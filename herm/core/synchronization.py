"""
Hospital Emergency Resource Manager (HERM)
Synchronization Primitives: Counting Semaphores and Mutex Locks.
Protects shared hospital resources and prevents race conditions.
"""

import threading
from typing import Dict, List, Optional
from herm.core.models import RESOURCE_NAMES, DEFAULT_RESOURCE_CAPACITY

class CountingSemaphore:
    """
    Simulates and implements a counting semaphore for tracking free units of a resource.
    Thread-safe implementation with acquire and release primitives.
    """
    def __init__(self, initial_count: int, name: str):
        self.name = name
        self.capacity = initial_count
        self._count = initial_count
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    @property
    def value(self) -> int:
        with self._lock:
            return self._count

    def acquire(self, units: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait (P operation) until 'units' are available.
        """
        with self._cond:
            if self._count < units:
                if timeout is not None:
                    success = self._cond.wait_for(lambda: self._count >= units, timeout=timeout)
                    if not success:
                        return False
                else:
                    self._cond.wait_for(lambda: self._count >= units)
            self._count -= units
            return True

    def release(self, units: int = 1):
        """
        Signal (V operation) to return 'units' to the semaphore.
        """
        with self._cond:
            self._count += units
            if self._count > self.capacity:
                self._count = self.capacity
            self._cond.notify_all()

    def reset(self, initial_count: Optional[int] = None):
        with self._cond:
            if initial_count is not None:
                self.capacity = initial_count
            self._count = self.capacity
            self._cond.notify_all()


class SynchronizationManager:
    """
    Coordinates counting semaphores for all resource pools and provides
    the allocation mutex to ensure atomic resource checks and grants.
    """
    def __init__(self, capacities: Optional[Dict[str, int]] = None):
        self.capacities = capacities or dict(DEFAULT_RESOURCE_CAPACITY)
        
        # Counting semaphores per resource pool
        self.semaphores: Dict[str, CountingSemaphore] = {
            res: CountingSemaphore(self.capacities[res], name=res)
            for res in RESOURCE_NAMES
        }
        
        # Single allocation mutex protecting allocation state transitions
        self.allocation_mutex = threading.Lock()

    def get_available_vector(self) -> Dict[str, int]:
        with self.allocation_mutex:
            return {res: self.semaphores[res].value for res in RESOURCE_NAMES}

    def reset(self):
        with self.allocation_mutex:
            for res in RESOURCE_NAMES:
                self.semaphores[res].reset(self.capacities.get(res))
