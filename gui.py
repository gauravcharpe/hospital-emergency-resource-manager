"""
Hospital Emergency Resource Manager (HERM)
Tkinter Native Desktop GUI Dashboard.
Provides a local graphical window displaying resource pools,
patient queues, and simulation controls without needing a web browser.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from herm.core.simulator import HospitalSimulator, get_standard_test_workload, get_surge_workload
from herm.core.scheduler import SchedulingPolicy
from herm.core.benchmark import BenchmarkEngine

class HermTkinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HERM - Hospital Emergency Resource Manager (BCSE303L)")
        self.root.geometry("1100x700")
        self.root.configure(bg="#111827")

        self.simulator = HospitalSimulator()
        self.is_auto_running = False

        self._create_widgets()
        self._refresh_ui()

    def _create_widgets(self):
        # Header Frame
        header = tk.Frame(self.root, bg="#1F2937", pady=10, padx=15)
        header.pack(fill=tk.X)

        title_lbl = tk.Label(
            header,
            text="🏥 HERM: Hospital Emergency Resource Manager",
            font=("Helvetica", 16, "bold"),
            fg="#F3F4F6",
            bg="#1F2937"
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = tk.Label(
            header,
            text="BCSE303L OS | Faculty: Dr. V. Ezhil Arasi",
            font=("Helvetica", 10),
            fg="#9CA3AF",
            bg="#1F2937"
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=15)

        self.clock_lbl = tk.Label(
            header,
            text="Clock: T=0",
            font=("Courier", 12, "bold"),
            fg="#06B6D4",
            bg="#1F2937"
        )
        self.clock_lbl.pack(side=tk.RIGHT)

        # Controls Bar
        ctrl_frame = tk.Frame(self.root, bg="#111827", pady=10, padx=15)
        ctrl_frame.pack(fill=tk.X)

        tk.Label(ctrl_frame, text="Policy:", fg="#F3F4F6", bg="#111827", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.policy_var = tk.StringVar(value="PREEMPTIVE_PRIORITY_AGING")
        policy_menu = ttk.Combobox(
            ctrl_frame,
            textvariable=self.policy_var,
            values=["PREEMPTIVE_PRIORITY_AGING", "NON_PREEMPTIVE_PRIORITY", "FCFS"],
            state="readonly",
            width=26
        )
        policy_menu.pack(side=tk.LEFT, padx=5)
        policy_menu.bind("<<ComboboxSelected>>", self._on_policy_change)

        self.btn_step = tk.Button(ctrl_frame, text="Step (+1)", command=self._step, bg="#3B82F6", fg="black", padx=10)
        self.btn_step.pack(side=tk.LEFT, padx=5)

        self.btn_run = tk.Button(ctrl_frame, text="Run All", command=self._run_all, bg="#10B981", fg="black", padx=10)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_reset = tk.Button(ctrl_frame, text="Reset", command=self._reset, bg="#6B7280", fg="black", padx=10)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        self.btn_deadlock = tk.Button(ctrl_frame, text="Inject Deadlock", command=self._inject_deadlock, bg="#EF4444", fg="black", padx=10)
        self.btn_deadlock.pack(side=tk.LEFT, padx=5)

        self.btn_bench = tk.Button(ctrl_frame, text="Run Benchmark", command=self._run_benchmark, bg="#8B5CF6", fg="black", padx=10)
        self.btn_bench.pack(side=tk.LEFT, padx=5)

        # Resource Display Frame
        self.res_frame = tk.Frame(self.root, bg="#1F2937", pady=10, padx=15)
        self.res_frame.pack(fill=tk.X, padx=15, pady=5)
        self.res_labels = {}

        # Content Panes: Left = Patient Table, Right = Logs / Details
        body_panes = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#111827")
        body_panes.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Patient Table
        table_frame = tk.Frame(body_panes, bg="#1F2937", padx=10, pady=10)
        body_panes.add(table_frame, width=650)

        cols = ("PID", "Name", "Priority", "State", "Burst", "Remaining", "Wait")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80 if col not in ("Name", "Priority") else 140)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Log & WFG Frame
        right_frame = tk.Frame(body_panes, bg="#1F2937", padx=10, pady=10)
        body_panes.add(right_frame, width=450)

        tk.Label(right_frame, text="Live IPC Event Stream & Deadlock Status", font=("Helvetica", 10, "bold"), fg="#F3F4F6", bg="#1F2937").pack(anchor=tk.W)
        self.log_text = tk.Text(right_frame, bg="#090D16", fg="#9CA3AF", font=("Courier", 9), height=18)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def _step(self):
        state = self.simulator.step()
        self._refresh_ui(state)

    def _run_all(self):
        state = self.simulator.run_all()
        self._refresh_ui(state)

    def _reset(self):
        policy = SchedulingPolicy[self.policy_var.get()]
        self.simulator.reset(policy=policy)
        self._refresh_ui()

    def _on_policy_change(self, event=None):
        self._reset()

    def _inject_deadlock(self):
        self.simulator.trigger_deadlock_scenario()
        state = self.simulator.step()
        self._refresh_ui(state)
        messagebox.showwarning("Deadlock Demo", f"Circular wait injected!\nCycles detected: {self.simulator.deadlocks_detected_count}\nRecovered via preemption: {self.simulator.deadlocks_recovered_count}")

    def _run_benchmark(self):
        results = BenchmarkEngine.run_comparative_study(get_surge_workload())
        summary = "Comparative Benchmark Results (Surge Workload):\n\n"
        for k, v in results.items():
            summary += f"• {v['display_name']}:\n"
            summary += f"   - Critical Wait: {v['critical_avg_waiting_time']}s | Overall Wait: {v['avg_waiting_time']}s | Deadlocks: {v['deadlocks_detected']}\n"
        messagebox.showinfo("Benchmark Results", summary)

    def _refresh_ui(self, state=None):
        if state is None:
            state = self.simulator.get_state_snapshot()

        self.clock_lbl.config(text=f"Clock: T={state['sim_time']}")

        # Clear and repopulate resource labels
        for widget in self.res_frame.winfo_children():
            widget.destroy()

        for res, info in state["resources"].items():
            f = tk.Frame(self.res_frame, bg="#111827", padx=8, pady=5)
            f.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
            tk.Label(f, text=res.replace("_", " "), font=("Helvetica", 8, "bold"), fg="#9CA3AF", bg="#111827").pack()
            tk.Label(f, text=f"{info['available']} / {info['total']}", font=("Courier", 11, "bold"), fg="#10B981" if info['available']>0 else "#EF4444", bg="#111827").pack()

        # Update Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in state["patients"]:
            self.tree.insert("", tk.END, values=(
                p["pid"],
                p["name"],
                f"L{p['effective_priority']} ({p['effective_priority_name']})",
                p["state"],
                p["burst_time"],
                p["remaining_time"],
                p["waiting_time"]
            ))

        # Update logs
        self.log_text.delete("1.0", tk.END)
        for msg in state["ipc_messages"]:
            self.log_text.insert(tk.END, f"[T={msg['timestamp']}] [{msg['msg_type']}] {msg['patient_id']}: {msg['payload']}\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = HermTkinterApp(root)
    root.mainloop()
