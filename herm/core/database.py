"""
Hospital Emergency Resource Manager (HERM)
SQLite Database Manager: Persistent event logging, patient audit trails,
and simulation run benchmarks.
"""

import sqlite3
import json
import os
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "herm_simulation.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Simulation runs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id TEXT PRIMARY KEY,
                policy TEXT NOT NULL,
                banker_enabled INTEGER NOT NULL,
                total_patients INTEGER NOT NULL,
                total_duration INTEGER,
                avg_waiting_time REAL,
                avg_turnaround_time REAL,
                starvation_count INTEGER,
                deadlock_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Patient metrics per run
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                pid TEXT NOT NULL,
                name TEXT NOT NULL,
                arrival_time INTEGER NOT NULL,
                base_priority INTEGER NOT NULL,
                burst_time INTEGER NOT NULL,
                completion_time INTEGER,
                waiting_time INTEGER,
                turnaround_time INTEGER,
                preemption_count INTEGER,
                is_starved INTEGER,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
            """)

            # Event logging
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                sim_time INTEGER NOT NULL,
                msg_type TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                pid TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Deadlock incidents
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS deadlock_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                sim_time INTEGER NOT NULL,
                cycle_nodes TEXT NOT NULL,
                victim_pid TEXT NOT NULL,
                released_resources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def record_run(self, run_data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO simulation_runs (
                run_id, policy, banker_enabled, total_patients, total_duration,
                avg_waiting_time, avg_turnaround_time, starvation_count, deadlock_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_data["run_id"],
                run_data["policy"],
                1 if run_data.get("banker_enabled", True) else 0,
                run_data["total_patients"],
                run_data.get("total_duration", 0),
                run_data.get("avg_waiting_time", 0.0),
                run_data.get("avg_turnaround_time", 0.0),
                run_data.get("starvation_count", 0),
                run_data.get("deadlock_count", 0)
            ))
            conn.commit()

    def record_patients(self, run_id: str, patients: List[Dict[str, Any]]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for p in patients:
                cursor.execute("""
                INSERT INTO patient_audit (
                    run_id, pid, name, arrival_time, base_priority, burst_time,
                    completion_time, waiting_time, turnaround_time, preemption_count, is_starved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    p["pid"],
                    p["name"],
                    p["arrival_time"],
                    p["base_priority"],
                    p["burst_time"],
                    p.get("completion_time"),
                    p.get("waiting_time", 0),
                    p.get("turnaround_time", 0),
                    p.get("preemption_count", 0),
                    1 if p.get("is_starved") else 0
                ))
            conn.commit()

    def log_event(self, run_id: str, sim_time: int, msg_type: str, sender: str, recipient: str, pid: str, details: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO event_logs (run_id, sim_time, msg_type, sender, recipient, pid, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, sim_time, msg_type, sender, recipient, pid, details))
            conn.commit()

    def log_deadlock(self, run_id: str, sim_time: int, cycle: List[str], victim_pid: str, released: Dict[str, int]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO deadlock_incidents (run_id, sim_time, cycle_nodes, victim_pid, released_resources)
            VALUES (?, ?, ?, ?, ?)
            """, (run_id, sim_time, json.dumps(cycle), victim_pid, json.dumps(released)))
            conn.commit()
