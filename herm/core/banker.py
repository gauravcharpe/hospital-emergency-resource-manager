"""
Hospital Emergency Resource Manager (HERM)
Deadlock Avoidance: Banker's Safety Algorithm.
Guarantees that resource allocations never lead to an unsafe state.
"""

from typing import Dict, List, Tuple, Optional, Any
from herm.core.models import Patient, RESOURCE_NAMES

class BankersAlgorithm:
    """
    Implements Dijkstra's Banker's Algorithm for multiple resource types.
    Maintains Available, Max, Allocation, and Need data structures.
    """
    @staticmethod
    def is_safe_state(
        available: Dict[str, int],
        patients: List[Patient]
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Banker's Safety Algorithm.
        Returns:
            (is_safe: bool, safe_sequence: List[str], debug_info: dict)
        """
        # Active patients that have not yet completed
        active_patients = [p for p in patients if p.state.value != "COMPLETED"]
        if not active_patients:
            return True, [], {"work_history": [], "finish": {}}

        work = dict(available)
        finish = {p.pid: False for p in active_patients}
        safe_sequence: List[str] = []
        work_history: List[Dict[str, int]] = [dict(work)]

        while len(safe_sequence) < len(active_patients):
            found_candidate = False
            for p in active_patients:
                if not finish[p.pid]:
                    # Check if Need <= Work for all resource types
                    need = p.need_resources
                    can_allocate = all(need[res] <= work[res] for res in RESOURCE_NAMES)
                    if can_allocate:
                        # Patient can complete; release its allocated resources to Work
                        for res in RESOURCE_NAMES:
                            work[res] += p.allocated_resources[res]
                        finish[p.pid] = True
                        safe_sequence.append(p.pid)
                        work_history.append(dict(work))
                        found_candidate = True
                        break
            
            if not found_candidate:
                # Deadlock avoidance: No process can finish; state is unsafe
                return False, [], {
                    "work": work,
                    "finish": finish,
                    "work_history": work_history,
                    "unresolved_patients": [pid for pid, done in finish.items() if not done]
                }

        return True, safe_sequence, {
            "work": work,
            "finish": finish,
            "work_history": work_history
        }

    @staticmethod
    def evaluate_request(
        patient: Patient,
        request: Dict[str, int],
        available: Dict[str, int],
        all_patients: List[Patient]
    ) -> Tuple[bool, str, List[str]]:
        """
        Banker's Resource-Request Algorithm.
        Tests whether granting the request keeps the system in a safe state.
        
        Returns:
            (can_grant: bool, reason: str, safe_sequence: List[str])
        """
        # Step 1: Check if Request <= Need
        need = patient.need_resources
        for res in RESOURCE_NAMES:
            req_units = request.get(res, 0)
            if req_units > need[res]:
                return False, f"Patient {patient.pid} requested {req_units} {res}, exceeding declared Need {need[res]}.", []

        # Step 2: Check if Request <= Available
        for res in RESOURCE_NAMES:
            req_units = request.get(res, 0)
            if req_units > available[res]:
                return False, f"Insufficient {res} available (Requested: {req_units}, Available: {available[res]}).", []

        # Step 3: Pretend allocation (Hypothetical state)
        simulated_available = dict(available)
        simulated_allocated = dict(patient.allocated_resources)

        for res in RESOURCE_NAMES:
            req_units = request.get(res, 0)
            simulated_available[res] -= req_units
            simulated_allocated[res] += req_units

        # Temporarily apply allocation to patient for safety check
        original_allocated = dict(patient.allocated_resources)
        patient.allocated_resources = simulated_allocated

        try:
            is_safe, safe_seq, _ = BankersAlgorithm.is_safe_state(
                simulated_available,
                all_patients
            )
        finally:
            # Revert to original state
            patient.allocated_resources = original_allocated

        if is_safe:
            return True, f"Request granted. System maintains safe state with sequence: {' -> '.join(safe_seq)}", safe_seq
        else:
            return False, "Request denied by Banker's Algorithm: Granting would cause an unsafe state (potential deadlock).", []
