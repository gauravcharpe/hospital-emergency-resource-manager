"""
Hospital Emergency Resource Manager (HERM)
Deadlock Detection & Recovery: Wait-For Graph (WFG) & Preemption Engine.
Builds resource dependency graphs, detects circular wait cycles, and selects victims for preemption.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from herm.core.models import Patient, RESOURCE_NAMES, ProcessState

class DeadlockDetector:
    """
    Constructs the Wait-For Graph and executes DFS cycle detection.
    Performs preemption-based recovery according to priority and treatment progress.
    """
    def __init__(self):
        self.wfg_nodes: List[str] = []
        self.wfg_edges: List[Dict[str, Any]] = []
        self.detected_cycles: List[List[str]] = []
        self.incidents_history: List[Dict[str, Any]] = []

    def build_wait_for_graph(
        self,
        patients: List[Patient],
        available: Dict[str, int]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Builds the Wait-For Graph (WFG).
        Node: Patient PID
        Edge: Pi -> Pj if Pi is WAITING for resource R, and Pj is holding resource R.
        """
        active = [p for p in patients if p.state != ProcessState.COMPLETED]
        self.wfg_nodes = [p.pid for p in active]
        self.wfg_edges = []

        waiting_patients = [p for p in active if p.state == ProcessState.WAITING]
        holding_patients = [p for p in active if any(units > 0 for units in p.allocated_resources.values())]

        for waiter in waiting_patients:
            needed = waiter.need_resources
            for res_name in RESOURCE_NAMES:
                needed_units = needed.get(res_name, 0)
                # If resource is currently in deficit in Available pool
                if needed_units > available.get(res_name, 0):
                    for holder in holding_patients:
                        if holder.pid != waiter.pid and holder.allocated_resources.get(res_name, 0) > 0:
                            # Add dependency edge waiter -> holder
                            edge = {
                                "from": waiter.pid,
                                "to": holder.pid,
                                "resource": res_name,
                                "units_held": holder.allocated_resources[res_name]
                            }
                            # Avoid duplicate directed edges for the same resource
                            if not any(
                                e["from"] == edge["from"] and e["to"] == edge["to"] and e["resource"] == edge["resource"]
                                for e in self.wfg_edges
                            ):
                                self.wfg_edges.append(edge)

        return self.wfg_nodes, self.wfg_edges

    def detect_cycles(self) -> List[List[str]]:
        """
        Executes Depth-First Search (DFS) on the Wait-For Graph to identify cycles.
        """
        adj: Dict[str, List[str]] = {node: [] for node in self.wfg_nodes}
        for edge in self.wfg_edges:
            adj[edge["from"]].append(edge["to"])

        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        cycles: List[List[str]] = []

        def dfs(u: str):
            visited.add(u)
            rec_stack.add(u)
            path.append(u)

            for v in adj.get(u, []):
                if v not in visited:
                    dfs(v)
                elif v in rec_stack:
                    # Found a cycle: trace from first occurrence of v in path
                    cycle_start_idx = path.index(v)
                    detected_cycle = path[cycle_start_idx:] + [v]
                    # Normalize cycle representation to avoid reporting duplicates
                    node_set = frozenset(detected_cycle[:-1])
                    if not any(frozenset(c[:-1]) == node_set for c in cycles):
                        cycles.append(detected_cycle)

            rec_stack.remove(u)
            path.pop()

        for node in self.wfg_nodes:
            if node not in visited:
                dfs(node)

        self.detected_cycles = cycles
        return cycles

    def select_victim(
        self,
        cycle: List[str],
        patient_map: Dict[str, Patient]
    ) -> Optional[Patient]:
        """
        Selects a victim patient from the cycle for preemption.
        Rules:
        1. Lowest Priority (Highest numerical level: 4 > 3 > 2 > 1).
        2. Tie Breaker: Least treatment completed (burst - remaining is minimum).
        3. Tie Breaker: Most recent arrival time.
        """
        cycle_pids = set(cycle[:-1])  # Exclude loop closure duplicate
        cycle_patients = [patient_map[pid] for pid in cycle_pids if pid in patient_map]
        if not cycle_patients:
            return None

        # Sort key:
        # 1. -effective_priority (higher number means lower clinical priority, e.g. Stable=4)
        # 2. progress (burst - remaining, ascending: less work done chosen first)
        # 3. -arrival_time (later arrival chosen first)
        def victim_score(p: Patient):
            progress = p.burst_time - p.remaining_time
            return (
                -p.effective_priority,  # Lower clinical urgency gets preempted first
                progress,               # Least work completed
                -p.arrival_time
            )

        victim = min(cycle_patients, key=victim_score)
        return victim

    def recover(
        self,
        cycles: List[List[str]],
        patient_map: Dict[str, Patient],
        available: Dict[str, int],
        current_time: int
    ) -> List[Dict[str, Any]]:
        """
        Executes recovery on all detected cycles by preempting selected victim processes.
        Returns details of recovery actions taken.
        """
        recovery_actions: List[Dict[str, Any]] = []
        handled_victims: Set[str] = set()

        for cycle in cycles:
            victim = self.select_victim(cycle, patient_map)
            if victim and victim.pid not in handled_victims:
                handled_victims.add(victim.pid)
                
                # Reclaim resources from the victim
                released_resources = dict(victim.allocated_resources)
                for res_name, count in released_resources.items():
                    available[res_name] += count
                    victim.allocated_resources[res_name] = 0

                # Transition victim to READY state
                victim.state = ProcessState.READY
                victim.preemption_count += 1

                action = {
                    "timestamp": current_time,
                    "cycle": cycle,
                    "victim_pid": victim.pid,
                    "victim_name": victim.name,
                    "victim_priority": victim.effective_priority,
                    "released_resources": released_resources,
                    "reason": f"Deadlock circular wait resolved by preempting lowest-urgency patient {victim.pid}."
                }
                recovery_actions.append(action)
                self.incidents_history.append(action)

        return recovery_actions
