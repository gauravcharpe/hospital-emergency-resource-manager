"""
Hospital Emergency Resource Manager (HERM)
Comparative Benchmarking Engine:
Evaluates FCFS, Non-Preemptive Priority, and Preemptive Priority with Aging
across identical workloads and computes waiting time, turnaround time,
starvation counts, resource utilization, and deadlock incidents.
"""

from typing import Dict, List, Any
import copy
from herm.core.simulator import HospitalSimulator, get_standard_test_workload
from herm.core.scheduler import SchedulingPolicy

class BenchmarkEngine:
    @staticmethod
    def run_comparative_study(workload=None) -> Dict[str, Any]:
        """
        Executes a controlled comparative benchmark of the 3 algorithms
        on identical workload inputs.
        """
        if workload is None:
            workload = get_standard_test_workload()

        policies = [
            ("FCFS", SchedulingPolicy.FCFS, True),
            ("NON_PREEMPTIVE", SchedulingPolicy.NON_PREEMPTIVE_PRIORITY, True),
            ("PREEMPTIVE_AGING", SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING, True),
            ("PREEMPTIVE_NO_BANKER", SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING, False)
        ]

        results = {}

        for name, policy, banker in policies:
            sim = HospitalSimulator(
                scheduling_policy=policy,
                banker_avoidance_enabled=banker
            )
            sim.load_workload([copy.deepcopy(p) for p in workload])
            sim.run_all(max_ticks=200)
            
            completed = [p for p in sim.all_patients if p.state.value == "COMPLETED"]
            avg_wait = round(sum(p.waiting_time for p in completed) / len(completed), 2) if completed else 0.0
            avg_tat = round(sum(p.turnaround_time for p in completed) / len(completed), 2) if completed else 0.0
            
            # Critical patients metrics (Level 1)
            critical = [p for p in completed if p.base_priority == 1]
            crit_wait = round(sum(p.waiting_time for p in critical) / len(critical), 2) if critical else 0.0
            crit_tat = round(sum(p.turnaround_time for p in critical) / len(critical), 2) if critical else 0.0

            # Serious patients (Level 2)
            serious = [p for p in completed if p.base_priority == 2]
            ser_wait = round(sum(p.waiting_time for p in serious) / len(serious), 2) if serious else 0.0

            # Moderate patients (Level 3)
            mod = [p for p in completed if p.base_priority == 3]
            mod_wait = round(sum(p.waiting_time for p in mod) / len(mod), 2) if mod else 0.0

            # Stable patients (Level 4)
            stable = [p for p in completed if p.base_priority == 4]
            stab_wait = round(sum(p.waiting_time for p in stable) / len(stable), 2) if stable else 0.0

            starved = sum(1 for p in sim.all_patients if p.is_starved)

            results[name] = {
                "policy_name": name,
                "display_name": {
                    "FCFS": "First-Come, First-Served (FCFS)",
                    "NON_PREEMPTIVE": "Non-Preemptive Priority",
                    "PREEMPTIVE_AGING": "Preemptive Priority with Aging",
                    "PREEMPTIVE_NO_BANKER": "Preemptive + Aging (No Banker's Check)"
                }.get(name, name),
                "banker_enabled": banker,
                "total_duration": sim.current_time,
                "completed_patients": len(completed),
                "avg_waiting_time": avg_wait,
                "avg_turnaround_time": avg_tat,
                "critical_avg_waiting_time": crit_wait,
                "critical_avg_turnaround_time": crit_tat,
                "serious_avg_waiting_time": ser_wait,
                "moderate_avg_waiting_time": mod_wait,
                "stable_avg_waiting_time": stab_wait,
                "starved_patients_count": starved,
                "deadlocks_detected": sim.deadlocks_detected_count,
                "deadlocks_recovered": sim.deadlocks_recovered_count,
                "patient_details": [p.to_dict() for p in sim.all_patients]
            }

        return results
