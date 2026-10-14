"""
Hospital Emergency Resource Manager (HERM)
Inter-Process Communication (IPC) Bus:
Simulates message queues and pipes exchanging discrete event messages between modules:
- ARRIVAL, REQUEST, GRANT, DENY, RELEASE, PREEMPT, DONE, AGING, DEADLOCK_DETECTED, DEADLOCK_RECOVERED
"""

from enum import Enum
import threading
from typing import Dict, List, Any, Optional, Callable
import time

class MessageType(Enum):
    ARRIVAL = "ARRIVAL"
    REQUEST = "REQUEST"
    GRANT = "GRANT"
    DENY = "DENY"
    RELEASE = "RELEASE"
    PREEMPT = "PREEMPT"
    DONE = "DONE"
    AGING = "AGING"
    DEADLOCK_DETECTED = "DEADLOCK_DETECTED"
    DEADLOCK_RECOVERED = "DEADLOCK_RECOVERED"

class IPCMessage:
    def __init__(
        self,
        timestamp: int,
        msg_type: MessageType,
        sender: str,
        recipient: str,
        patient_id: str,
        payload: Dict[str, Any]
    ):
        self.timestamp = timestamp
        self.msg_type = msg_type
        self.sender = sender
        self.recipient = recipient
        self.patient_id = patient_id
        self.payload = payload
        self.wall_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "msg_type": self.msg_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "patient_id": self.patient_id,
            "payload": self.payload,
            "wall_time": self.wall_time
        }

class IPCBus:
    """
    Thread-safe Inter-Process Communication bus.
    Facilitates decoupled communication between the Emergency Reception,
    Process Scheduler, Resource Manager, and Deadlock Detector.
    """
    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self._history: List[IPCMessage] = []
        self._lock = threading.Lock()
        self._subscribers: List[Callable[[IPCMessage], None]] = []

    def subscribe(self, callback: Callable[[IPCMessage], None]):
        with self._lock:
            self._subscribers.append(callback)

    def publish(
        self,
        timestamp: int,
        msg_type: MessageType,
        sender: str,
        recipient: str,
        patient_id: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> IPCMessage:
        msg = IPCMessage(
            timestamp=timestamp,
            msg_type=msg_type,
            sender=sender,
            recipient=recipient,
            patient_id=patient_id,
            payload=payload or {}
        )
        with self._lock:
            self._history.append(msg)
            if len(self._history) > self.max_history:
                self._history.pop(0)
            subscribers_copy = list(self._subscribers)

        for callback in subscribers_copy:
            try:
                callback(msg)
            except Exception:
                pass
        return msg

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [m.to_dict() for m in self._history[-limit:]]

    def clear(self):
        with self._lock:
            self._history.clear()
