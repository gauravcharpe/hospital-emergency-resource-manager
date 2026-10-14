"""
Hospital Emergency Resource Manager (HERM)
Central Simulation Engine: Coordinates scheduling, synchronization,
Banker's deadlock avoidance, Wait-For Graph detection, recovery, and IPC events.
"""

import copy
import uuid
from typing import Dict, List, Optional, Any, Tuple
from herm.core.models import (
    Patient, ProcessState, PriorityLevel, RESOURCE_NAMES, DEFAULT_RESOURCE_CAPACITY
)
from herm.core.synchronization import SynchronizationManager
from herm.core.banker import BankersAlgorithm
from herm.core.deadlock_detector import DeadlockDetector
from herm.core.scheduler import Scheduler, SchedulingPolicy
from herm.core.ipc_bus import IPCBus, MessageType
from herm.core.database import DatabaseManager

def get_standard_test_workload() -> List[Patient]:
    """
    Returns the standard benchmark workload from the IEEE paper (Table IV)
    plus extended cases to rigorously test concurrency, aging, and deadlock recovery.
    """
    return [
        Patient(
            pid="P1",
            name="John Doe",
            arrival_time=0,
            base_priority=3,  # Moderate: Controlled bleeding
            burst_time=8,
            max_resources={"ICU_Beds": 1, "Ventilators": 0, "Doctors": 1, "Nurses": 2, "Operation_Theatres": 0},
            condition_description="Controlled bleeding, stable vitals"
        ),
        Patient(
            pid="P2",
            name="Sarah Smith",
            arrival_time=1,
            base_priority=2,  # Serious: Breathing difficulty
            burst_time=6,
            max_resources={"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 0, "Operation_Theatres": 0},
            condition_description="Acute respiratory distress, requires ventilator"
        ),
        Patient(
            pid="P3",
            name="David Clark",
            arrival_time=2,
            base_priority=4,  # Stable: Routine check/minor fracture
            burst_time=4,
            max_resources={"ICU_Beds": 0, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0},
            condition_description="Minor sprain, observation needed"
        ),
        Patient(
            pid="P4",
            name="Emma Watson",
            arrival_time=3,
            base_priority=1,  # Critical: Cardiac arrest / polytrauma
            burst_time=5,
            max_resources={"ICU_Beds": 1, "Ventilators": 1, "Doctors": 2, "Nurses": 2, "Operation_Theatres": 1},
            condition_description="Massive cardiac arrest, emergency surgery required"
        ),
        Patient(
            pid="P5",
            name="Robert Miller",
            arrival_time=4,
            base_priority=3,  # Moderate: High fever & dehydration
            burst_time=7,
            max_resources={"ICU_Beds": 1, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0},
            condition_description="High fever, IV antibiotics required"
        ),
        Patient(
            pid="P6",
            name="Lisa Ray",
            arrival_time=6,
            base_priority=1,  # Critical: Ruptured aortic aneurysm
            burst_time=4,
            max_resources={"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 0, "Operation_Theatres": 1},
            condition_description="Severe internal hemorrhage, urgent surgery"
        ),
        Patient(
            pid="P7",
            name="Alex Turner",
            arrival_time=8,
            base_priority=4,  # Stable
            burst_time=5,
            max_resources={"ICU_Beds": 0, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0},
            condition_description="Laceration requiring sutures"
        ),
        Patient(
            pid="P8",
            name="Elena Gilbert",
            arrival_time=9,
            base_priority=2,  # Serious
            burst_time=5,
            max_resources={"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0},
            condition_description="Severe asthma exacerbation"
        )
    ]

def get_surge_workload() -> List[Patient]:
    """
    High-contention surge workload: Many simultaneous arrivals competing
    for scarce Operation Theatres and Ventilators. Accentuates scheduling differences.
    """
    return [
        Patient("P1", "Patient Alpha", 0, 4, 10, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 1}, "Severe infection"),
        Patient("P2", "Patient Beta", 1, 3, 8, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 1}, "Moderate trauma"),
        Patient("P3", "Patient Gamma", 1, 1, 6, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 2, "Nurses": 2, "Operation_Theatres": 1}, "Critical cardiac arrest"),
        Patient("P4", "Patient Delta", 2, 4, 12, {"ICU_Beds": 1, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0}, "Non-urgent sprain"),
        Patient("P5", "Patient Epsilon", 2, 1, 5, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 2, "Nurses": 2, "Operation_Theatres": 1}, "Aortic rupture (Critical)"),
        Patient("P6", "Patient Zeta", 3, 2, 7, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0}, "Head injury (Serious)"),
        Patient("P7", "Patient Eta", 4, 4, 9, {"ICU_Beds": 0, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0}, "Stable observation"),
        Patient("P8", "Patient Theta", 5, 1, 4, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 1}, "Gunshot trauma (Critical)"),
        Patient("P9", "Patient Iota", 6, 3, 6, {"ICU_Beds": 1, "Ventilators": 0, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0}, "Appendicitis"),
        Patient("P10", "Patient Kappa", 7, 2, 5, {"ICU_Beds": 1, "Ventilators": 1, "Doctors": 1, "Nurses": 1, "Operation_Theatres": 0}, "Pulmonary embolism")
    ]


class HospitalSimulator:
    """
    Central simulation engine managing the emergency department lifecycle.
    """
    def __init__(
        self,
        scheduling_policy: SchedulingPolicy = SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING,
        banker_avoidance_enabled: bool = True,
        capacities: Optional[Dict[str, int]] = None
    ):
        self.run_id: str = f"HERM-{uuid.uuid4().hex[:8].upper()}"
        self.current_time: int = 0
        self.banker_enabled: bool = banker_avoidance_enabled
        self.is_running: bool = False
        self.is_completed: bool = False

        # Core subsystems
        self.sync_mgr = SynchronizationManager(capacities)
        self.scheduler = Scheduler(policy=scheduling_policy)
        self.deadlock_detector = DeadlockDetector()
        self.ipc_bus = IPCBus()
        self.db_mgr = DatabaseManager()

        # Patient storage
        self.all_patients: List[Patient] = []
        self.patient_map: Dict[str, Patient] = {}
        
        # Deadlock statistics
        self.deadlocks_detected_count: int = 0
        self.deadlocks_recovered_count: int = 0

        # Load standard initial workload
        self.load_workload(get_standard_test_workload())

    def load_workload(self, patients: List[Patient]):
        self.all_patients = [copy.deepcopy(p) for p in patients]
        for p in self.all_patients:
            p.reset_for_simulation()
        self.patient_map = {p.pid: p for p in self.all_patients}

    def reset(self, policy: Optional[SchedulingPolicy] = None, banker_enabled: Optional[bool] = None):
        self.current_time = 0
        self.run_id = f"HERM-{uuid.uuid4().hex[:8].upper()}"
        self.is_completed = False
        self.deadlocks_detected_count = 0
        self.deadlocks_recovered_count = 0
        
        if policy is not None:
            self.scheduler.policy = policy
        if banker_enabled is not None:
            self.banker_enabled = banker_enabled

        self.sync_mgr.reset()
        self.ipc_bus.clear()
        self.deadlock_detector = DeadlockDetector()
        
        for p in self.all_patients:
            p.reset_for_simulation()

    def add_patient(self, patient: Patient):
        patient.reset_for_simulation()
        self.all_patients.append(patient)
        self.patient_map[patient.pid] = patient
        if patient.arrival_time <= self.current_time:
            patient.state = ProcessState.READY
            self.ipc_bus.publish(
                self.current_time,
                MessageType.ARRIVAL,
                "Reception",
                "Scheduler",
                patient.pid,
                {"name": patient.name, "priority": patient.base_priority}
            )

    def trigger_deadlock_scenario(self):
        """
        Forces an intentional mutual dependency deadlock:
        Patient X holds the remaining Operation Theatres and waits for ICU Bed.
        Patient Y holds the remaining ICU Beds and waits for Operation Theatre.
        With Banker's Avoidance switched OFF, this produces a circular wait cycle in WFG.
        """
        self.banker_enabled = False
        p_a = Patient("P_DEADLOCK_A", "Emergency Cardiac", self.current_time, 2, 8, {"Operation_Theatres": 1, "ICU_Beds": 1})
        p_b = Patient("P_DEADLOCK_B", "Severe Trauma", self.current_time, 3, 8, {"Operation_Theatres": 1, "ICU_Beds": 1})
        self.add_patient(p_a)
        self.add_patient(p_b)
        
        # Deplete available units so Available is 0 for both resources
        # Allocate all available theatres to P_A and all beds to P_B
        avail = self.sync_mgr.get_available_vector()
        
        p_a.allocated_resources["Operation_Theatres"] = p_a.max_resources["Operation_Theatres"]
        p_b.allocated_resources["ICU_Beds"] = p_b.max_resources["ICU_Beds"]
        
        # Set semaphore and available to 0 for these contested pools
        self.sync_mgr.semaphores["Operation_Theatres"].reset(0)
        self.sync_mgr.semaphores["ICU_Beds"].reset(0)

        p_a.state = ProcessState.WAITING
        p_b.state = ProcessState.WAITING

        self.ipc_bus.publish(
            self.current_time,
            MessageType.REQUEST,
            "DeadlockTester",
            "ResourceManager",
            "P_DEADLOCK_A & P_DEADLOCK_B",
            {"details": "Circular wait intentionally induced: P_DEADLOCK_A holds Theatre, waits for Bed; P_DEADLOCK_B holds Bed, waits for Theatre."}
        )


    def step(self) -> Dict[str, Any]:
        """
        Advances the simulation by one discrete time unit (tick).
        Executes arrival triage, scheduling, synchronization, Banker's check,
        WFG cycle detection, treatment progress, preemption, and logging.
        """
        if self.is_completed:
            return self.get_state_snapshot()

        sim_time = self.current_time
        available = self.sync_mgr.get_available_vector()

        # Step 1: Process New Arrivals at current time
        for p in self.all_patients:
            if p.state == ProcessState.NEW and p.arrival_time <= sim_time:
                p.state = ProcessState.READY
                self.ipc_bus.publish(
                    sim_time,
                    MessageType.ARRIVAL,
                    "Reception",
                    "Scheduler",
                    p.pid,
                    {"priority": p.base_priority, "name": p.name}
                )

        # Step 2: Apply Priority Aging to READY patients
        ready_patients = [p for p in self.all_patients if p.state == ProcessState.READY]
        aging_events = self.scheduler.update_aging(ready_patients, sim_time)
        for age_ev in aging_events:
            self.ipc_bus.publish(
                sim_time,
                MessageType.AGING,
                "AgingEngine",
                "Scheduler",
                age_ev["pid"],
                age_ev
            )

        # Step 3: Check and Run Deadlock Detection on Wait-For Graph
        wfg_nodes, wfg_edges = self.deadlock_detector.build_wait_for_graph(self.all_patients, available)
        detected_cycles = self.deadlock_detector.detect_cycles()
        if detected_cycles:
            self.deadlocks_detected_count += len(detected_cycles)
            self.ipc_bus.publish(
                sim_time,
                MessageType.DEADLOCK_DETECTED,
                "DeadlockDetector",
                "RecoveryManager",
                ",".join(["->".join(c) for c in detected_cycles]),
                {"cycles": detected_cycles}
            )

            # Recover by selecting lowest priority victim in cycle
            recoveries = self.deadlock_detector.recover(detected_cycles, self.patient_map, available, sim_time)
            for rec in recoveries:
                self.deadlocks_recovered_count += 1
                # Sync semaphores after victim release
                for res, count in rec["released_resources"].items():
                    if count > 0:
                        self.sync_mgr.semaphores[res].release(count)
                
                self.ipc_bus.publish(
                    sim_time,
                    MessageType.DEADLOCK_RECOVERED,
                    "RecoveryManager",
                    "Scheduler",
                    rec["victim_pid"],
                    rec
                )
                self.db_mgr.log_deadlock(
                    self.run_id, sim_time, rec["cycle"], rec["victim_pid"], rec["released_resources"]
                )
            
            # Recompute available after recovery
            available = self.sync_mgr.get_available_vector()

        # Step 4: Check for Preemption of currently RUNNING patients
        running_patients = [p for p in self.all_patients if p.state == ProcessState.RUNNING]
        ready_patients = [p for p in self.all_patients if p.state == ProcessState.READY]

        if self.scheduler.policy == SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING and running_patients and ready_patients:
            # Check if any ready patient has higher priority than a running patient
            best_candidate = self.scheduler.select_next_patient(ready_patients)
            if best_candidate:
                # Find lowest priority running patient
                lowest_running = max(running_patients, key=lambda p: (p.effective_priority, -p.arrival_time))
                should_p, reason = self.scheduler.should_preempt(lowest_running, best_candidate)
                if should_p:
                    # Preempt lowest_running: release resources to available pool and move to READY
                    with self.sync_mgr.allocation_mutex:
                        for res_name, count in lowest_running.allocated_resources.items():
                            if count > 0:
                                self.sync_mgr.semaphores[res_name].release(count)
                                available[res_name] += count
                                lowest_running.allocated_resources[res_name] = 0

                    lowest_running.state = ProcessState.READY
                    lowest_running.preemption_count += 1
                    self.ipc_bus.publish(
                        sim_time,
                        MessageType.PREEMPT,
                        "Scheduler",
                        lowest_running.pid,
                        lowest_running.pid,
                        {"preempted_by": best_candidate.pid, "reason": reason}
                    )

        # Step 5: Allocate Resources and Dispatch Ready/Waiting Patients
        # Eligible candidates include READY and WAITING patients
        candidates = [p for p in self.all_patients if p.state in (ProcessState.READY, ProcessState.WAITING)]
        
        # Sort candidates according to scheduler policy
        if self.scheduler.policy == SchedulingPolicy.FCFS:
            candidates.sort(key=lambda p: (p.arrival_time, p.pid))
        elif self.scheduler.policy == SchedulingPolicy.NON_PREEMPTIVE_PRIORITY:
            candidates.sort(key=lambda p: (p.base_priority, p.arrival_time, p.pid))
        else: # Preemptive Priority with Aging
            candidates.sort(key=lambda p: (p.effective_priority, p.arrival_time, p.pid))

        for candidate in candidates:
            need = candidate.need_resources
            # If candidate already has all needed resources (e.g. was running or partially allocated)
            units_still_needed = {res: need[res] for res in RESOURCE_NAMES}
            
            # Check physical availability
            physically_available = all(available[res] >= units_still_needed[res] for res in RESOURCE_NAMES)
            
            if not physically_available:
                # Insufficient resources currently in the pool
                if candidate.state == ProcessState.READY:
                    candidate.state = ProcessState.WAITING
                    self.ipc_bus.publish(
                        sim_time,
                        MessageType.DENY,
                        "ResourceManager",
                        candidate.pid,
                        candidate.pid,
                        {"reason": "Resources busy, queued in WAITING state"}
                    )
                continue

            # Check Banker's Algorithm if enabled
            if self.banker_enabled:
                can_grant, reason, safe_seq = BankersAlgorithm.evaluate_request(
                    candidate, units_still_needed, available, self.all_patients
                )
                if not can_grant:
                    candidate.state = ProcessState.WAITING
                    self.ipc_bus.publish(
                        sim_time,
                        MessageType.DENY,
                        "BankerAvoidance",
                        candidate.pid,
                        candidate.pid,
                        {"reason": reason}
                    )
                    continue

            # Grant Resources atomically
            with self.sync_mgr.allocation_mutex:
                for res, count in units_still_needed.items():
                    if count > 0:
                        self.sync_mgr.semaphores[res].acquire(count)
                        available[res] -= count
                        candidate.allocated_resources[res] += count

            candidate.state = ProcessState.RUNNING
            if candidate.first_response_time is None:
                candidate.first_response_time = sim_time
            if candidate.effective_priority == 4:
                candidate.quantum_remaining = self.scheduler.time_quantum

            self.ipc_bus.publish(
                sim_time,
                MessageType.GRANT,
                "ResourceManager",
                candidate.pid,
                candidate.pid,
                {"allocated": candidate.allocated_resources}
            )

        # Step 6: Advance treatment for RUNNING patients
        currently_running = [p for p in self.all_patients if p.state == ProcessState.RUNNING]
        for p in currently_running:
            p.remaining_time -= 1
            if p.effective_priority == 4:
                p.quantum_remaining -= 1

            # Check if patient treatment completed
            if p.remaining_time <= 0:
                p.state = ProcessState.COMPLETED
                p.completion_time = sim_time + 1
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time = max(0, p.turnaround_time - p.burst_time)

                # Release all held resources
                with self.sync_mgr.allocation_mutex:
                    for res, count in p.allocated_resources.items():
                        if count > 0:
                            self.sync_mgr.semaphores[res].release(count)
                            available[res] += count
                            p.allocated_resources[res] = 0

                self.ipc_bus.publish(
                    sim_time,
                    MessageType.DONE,
                    "OperatingTheatre/ICU",
                    "Discharge",
                    p.pid,
                    {
                        "turnaround_time": p.turnaround_time,
                        "waiting_time": p.waiting_time,
                        "completion_time": p.completion_time
                    }
                )

        # Step 7: Update waiting times for READY and WAITING patients
        for p in self.all_patients:
            if p.state in (ProcessState.READY, ProcessState.WAITING) and p.arrival_time <= sim_time:
                p.waiting_time += 1
                if p.waiting_time >= self.scheduler.starvation_threshold:
                    p.is_starved = True

        # Advance simulation clock
        self.current_time += 1

        # Check overall completion
        if all(p.state == ProcessState.COMPLETED for p in self.all_patients):
            self.is_completed = True
            self._save_run_summary()

        return self.get_state_snapshot()

    def run_all(self, max_ticks: int = 150) -> Dict[str, Any]:
        """Runs the entire simulation until all patients complete."""
        while not self.is_completed and self.current_time < max_ticks:
            self.step()
        return self.get_state_snapshot()

    def _save_run_summary(self):
        completed = [p for p in self.all_patients if p.state == ProcessState.COMPLETED]
        if not completed:
            return
        avg_wait = sum(p.waiting_time for p in completed) / len(completed)
        avg_tat = sum(p.turnaround_time for p in completed) / len(completed)
        starved_count = sum(1 for p in self.all_patients if p.is_starved)

        run_data = {
            "run_id": self.run_id,
            "policy": self.scheduler.policy.value,
            "banker_enabled": self.banker_enabled,
            "total_patients": len(self.all_patients),
            "total_duration": self.current_time,
            "avg_waiting_time": round(avg_wait, 2),
            "avg_turnaround_time": round(avg_tat, 2),
            "starvation_count": starved_count,
            "deadlock_count": self.deadlocks_detected_count
        }
        self.db_mgr.record_run(run_data)
        self.db_mgr.record_patients(self.run_id, [p.to_dict() for p in self.all_patients])

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Provides a complete real-time JSON snapshot for the dashboard."""
        available = self.sync_mgr.get_available_vector()
        is_safe, safe_seq, _ = BankersAlgorithm.is_safe_state(available, self.all_patients)
        wfg_nodes, wfg_edges = self.deadlock_detector.build_wait_for_graph(self.all_patients, available)
        cycles = self.deadlock_detector.detect_cycles()

        completed_patients = [p for p in self.all_patients if p.state == ProcessState.COMPLETED]
        avg_wait = round(sum(p.waiting_time for p in completed_patients) / len(completed_patients), 2) if completed_patients else 0.0
        avg_tat = round(sum(p.turnaround_time for p in completed_patients) / len(completed_patients), 2) if completed_patients else 0.0

        # Breakdown by priority class
        priority_breakdown = {}
        for level in [1, 2, 3, 4]:
            pts = [p for p in completed_patients if p.base_priority == level]
            avg_w = round(sum(p.waiting_time for p in pts) / len(pts), 2) if pts else 0.0
            avg_t = round(sum(p.turnaround_time for p in pts) / len(pts), 2) if pts else 0.0
            priority_breakdown[PriorityLevel.get_name(level)] = {
                "level": level,
                "count": len(pts),
                "avg_waiting_time": avg_w,
                "avg_turnaround_time": avg_t
            }

        return {
            "run_id": self.run_id,
            "sim_time": self.current_time,
            "policy": self.scheduler.policy.value,
            "banker_enabled": self.banker_enabled,
            "is_completed": self.is_completed,
            "resources": {
                res: {
                    "total": self.sync_mgr.capacities[res],
                    "available": available[res],
                    "allocated": self.sync_mgr.capacities[res] - available[res],
                    "utilization_percent": round(((self.sync_mgr.capacities[res] - available[res]) / self.sync_mgr.capacities[res]) * 100, 1)
                } for res in RESOURCE_NAMES
            },
            "banker_state": {
                "is_safe": is_safe,
                "safe_sequence": safe_seq,
                "available_vector": available
            },
            "wait_for_graph": {
                "nodes": wfg_nodes,
                "edges": wfg_edges,
                "detected_cycles": cycles,
                "has_deadlock": len(cycles) > 0
            },
            "patients": [p.to_dict() for p in self.all_patients],
            "ipc_messages": self.ipc_bus.get_recent_messages(30),
            "metrics": {
                "total_patients": len(self.all_patients),
                "completed_count": len(completed_patients),
                "avg_waiting_time": avg_wait,
                "avg_turnaround_time": avg_tat,
                "starved_count": sum(1 for p in self.all_patients if p.is_starved),
                "deadlocks_detected": self.deadlocks_detected_count,
                "deadlocks_recovered": self.deadlocks_recovered_count,
                "priority_breakdown": priority_breakdown
            }
        }
