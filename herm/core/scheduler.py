"""
Hospital Emergency Resource Manager (HERM)
Process Scheduling Policies:
1. Preemptive Priority Scheduling with Aging & Round Robin for Stable cases
2. Non-Preemptive Priority Scheduling
3. First-Come, First-Served (FCFS)
"""

from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from herm.core.models import Patient, ProcessState, PriorityLevel

class SchedulingPolicy(Enum):
    PREEMPTIVE_PRIORITY_AGING = "PREEMPTIVE_PRIORITY_AGING"
    NON_PREEMPTIVE_PRIORITY = "NON_PREEMPTIVE_PRIORITY"
    FCFS = "FCFS"

class Scheduler:
    """
    Hospital CPU & Resource Scheduler implementing three distinct algorithms
    for comparative benchmarking and real-time clinical dispatching.
    """
    def __init__(
        self,
        policy: SchedulingPolicy = SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING,
        aging_interval: int = 4,   # Ta: Every 4 ticks in READY, boost priority
        aging_cap: int = 2,        # Aging can elevate up to Level 2 (Serious), not Level 1 (Critical)
        time_quantum: int = 2,     # q: Round Robin quantum for Level 4 (Stable)
        starvation_threshold: int = 15
    ):
        self.policy: SchedulingPolicy = policy
        self.aging_interval: int = aging_interval
        self.aging_cap: int = aging_cap
        self.time_quantum: int = time_quantum
        self.starvation_threshold: int = starvation_threshold

    def update_aging(self, ready_patients: List[Patient], current_time: int) -> List[Dict[str, Any]]:
        """
        Applies priority aging to patients waiting in the READY queue.
        Effective priority improves by 1 level per Ta ticks, capping at Level 2.
        """
        aging_events: List[Dict[str, Any]] = []
        if self.policy != SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING:
            return aging_events

        for patient in ready_patients:
            patient.ready_time_counter += 1
            # Check for starvation flag
            if patient.waiting_time >= self.starvation_threshold and not patient.is_starved:
                patient.is_starved = True

            # Calculate aging boost
            if patient.base_priority > self.aging_cap:
                num_intervals = patient.ready_time_counter // self.aging_interval
                target_priority = max(self.aging_cap, patient.base_priority - num_intervals)
                if target_priority < patient.effective_priority:
                    old_p = patient.effective_priority
                    patient.effective_priority = target_priority
                    aging_events.append({
                        "timestamp": current_time,
                        "pid": patient.pid,
                        "name": patient.name,
                        "old_priority": old_p,
                        "new_priority": target_priority,
                        "reason": f"Patient aged in READY queue for {patient.ready_time_counter} ticks."
                    })
        return aging_events

    def select_next_patient(
        self,
        ready_patients: List[Patient],
        currently_running: Optional[Patient] = None
    ) -> Optional[Patient]:
        """
        Selects the next patient to execute based on the active scheduling policy.
        """
        if not ready_patients:
            return None

        if self.policy == SchedulingPolicy.FCFS:
            # First Come First Served: earliest arrival time
            return min(ready_patients, key=lambda p: (p.arrival_time, p.pid))

        elif self.policy == SchedulingPolicy.NON_PREEMPTIVE_PRIORITY:
            # Strict base priority: Level 1 (Critical) < Level 2 < Level 3 < Level 4
            return min(ready_patients, key=lambda p: (p.base_priority, p.arrival_time, p.pid))

        elif self.policy == SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING:
            # Preemptive Priority with Aging:
            # Use effective priority (which incorporates aging boosts)
            # For Level 4 patients, tie-break by arrival to simulate Round Robin queue
            return min(ready_patients, key=lambda p: (p.effective_priority, p.arrival_time, p.pid))

        return ready_patients[0]

    def should_preempt(
        self,
        running_patient: Patient,
        candidate_patient: Patient
    ) -> Tuple[bool, str]:
        """
        Determines whether candidate_patient should preempt the currently running patient.
        Preemption is enabled only under PREEMPTIVE_PRIORITY_AGING.
        """
        if self.policy != SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING:
            return False, "Preemption disabled in current scheduling policy."

        # Case 1: Candidate is Critical (Level 1) and running patient is lower priority (> 1)
        if candidate_patient.effective_priority < running_patient.effective_priority:
            return True, f"Preemption triggered: Higher priority patient {candidate_patient.pid} (Level {candidate_patient.effective_priority}) preempts running patient {running_patient.pid} (Level {running_patient.effective_priority})."

        # Case 2: Round Robin quantum expiry for Level 4 (Stable)
        if running_patient.effective_priority == 4 and running_patient.quantum_remaining <= 0:
            if candidate_patient.effective_priority == 4 and candidate_patient.pid != running_patient.pid:
                return True, f"Round Robin quantum expired for stable patient {running_patient.pid}; yielding to next patient."

        return False, "No preemption condition met."
