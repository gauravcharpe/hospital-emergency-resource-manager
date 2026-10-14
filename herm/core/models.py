"""
Hospital Emergency Resource Manager (HERM)
Core Models: Patients, Resources, Enums, and State Definitions.
"""

from enum import Enum
from typing import Dict, Any, Optional

class PriorityLevel(Enum):
    CRITICAL = 1   # Cardiac arrest, severe trauma (Preemptive, highest priority)
    SERIOUS = 2    # Breathing difficulty, major fracture (Subject to aging)
    MODERATE = 3   # Controlled bleeding, high fever (Subject to aging)
    STABLE = 4     # Minor injury, routine check (Round Robin allowed)

    @classmethod
    def get_name(cls, level: int) -> str:
        mapping = {
            1: "Critical",
            2: "Serious",
            3: "Moderate",
            4: "Stable"
        }
        return mapping.get(level, "Unknown")

class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"

RESOURCE_NAMES = [
    "ICU_Beds",
    "Ventilators",
    "Doctors",
    "Nurses",
    "Operation_Theatres"
]

DEFAULT_RESOURCE_CAPACITY: Dict[str, int] = {
    "ICU_Beds": 4,
    "Ventilators": 3,
    "Doctors": 5,
    "Nurses": 8,
    "Operation_Theatres": 2
}

class Patient:
    """
    Represents an emergency patient modelled as an Operating System Process.
    """
    def __init__(
        self,
        pid: str,
        name: str,
        arrival_time: int,
        base_priority: int,
        burst_time: int,
        max_resources: Dict[str, int],
        condition_description: str = ""
    ):
        self.pid: str = pid
        self.name: str = name
        self.arrival_time: int = arrival_time
        self.base_priority: int = base_priority
        self.effective_priority: int = base_priority
        self.burst_time: int = burst_time
        self.remaining_time: int = burst_time
        
        # Max claim vector
        self.max_resources: Dict[str, int] = {
            res: max_resources.get(res, 0) for res in RESOURCE_NAMES
        }
        # Currently allocated vector
        self.allocated_resources: Dict[str, int] = {res: 0 for res in RESOURCE_NAMES}
        
        self.state: ProcessState = ProcessState.NEW
        self.condition_description: str = condition_description or f"Priority {base_priority} Case"
        
        # Timing and metrics
        self.first_response_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.waiting_time: int = 0
        self.turnaround_time: int = 0
        self.ready_time_counter: int = 0  # For aging calculation
        self.preemption_count: int = 0
        self.is_starved: bool = False
        
        # Round Robin tracking for level 4
        self.quantum_remaining: int = 0

    @property
    def need_resources(self) -> Dict[str, int]:
        return {
            res: max(0, self.max_resources[res] - self.allocated_resources[res])
            for res in RESOURCE_NAMES
        }

    def reset_for_simulation(self):
        self.effective_priority = self.base_priority
        self.remaining_time = self.burst_time
        self.allocated_resources = {res: 0 for res in RESOURCE_NAMES}
        self.state = ProcessState.NEW
        self.first_response_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.ready_time_counter = 0
        self.preemption_count = 0
        self.is_starved = False
        self.quantum_remaining = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "arrival_time": self.arrival_time,
            "base_priority": self.base_priority,
            "base_priority_name": PriorityLevel.get_name(self.base_priority),
            "effective_priority": self.effective_priority,
            "effective_priority_name": PriorityLevel.get_name(self.effective_priority),
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "progress_percent": round(((self.burst_time - self.remaining_time) / self.burst_time) * 100, 1) if self.burst_time > 0 else 100,
            "max_resources": self.max_resources,
            "allocated_resources": self.allocated_resources,
            "need_resources": self.need_resources,
            "state": self.state.value,
            "condition_description": self.condition_description,
            "first_response_time": self.first_response_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "preemption_count": self.preemption_count,
            "is_starved": self.is_starved
        }
