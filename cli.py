"""
Hospital Emergency Resource Manager (HERM)
CLI Simulation Runner & Terminal Dashboard.
Allows running and inspecting simulation cycles, benchmark comparisons,
and deadlock detection directly from the command line.
"""

import sys
import os
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from herm.core.simulator import HospitalSimulator, get_standard_test_workload, get_surge_workload
from herm.core.scheduler import SchedulingPolicy
from herm.core.benchmark import BenchmarkEngine

def print_banner():
    print("=" * 80)
    print("  HOSPITAL EMERGENCY RESOURCE MANAGER (HERM) - SIMULATION CLI")
    print("  Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi")
    print("  School of Computer Science and Engineering, Vellore Institute of Technology")
    print("=" * 80)

def run_cli_interactive():
    print_banner()
    print("\nSelect Simulation Mode:")
    print("  1. Run Step-by-Step Simulation (Preemptive Priority with Aging)")
    print("  2. Run Full Comparative Benchmark Study (FCFS vs Priority vs Preemptive)")
    print("  3. Run Deadlock Injection & Wait-For Graph Recovery Demo")
    print("  4. Run High-Contention Surge Workload")
    print("  5. Launch Web Command Center Dashboard")
    print("  6. Exit")

    choice = input("\nEnter choice [1-6]: ").strip()

    if choice == "1":
        sim = HospitalSimulator(SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING, banker_avoidance_enabled=True)
        print("\nStarting simulation... Press Enter after each step, or type 'run' to finish.")
        while not sim.is_completed:
            state = sim.step()
            print(f"\n--- [Clock Tick T={state['sim_time']}] ---")
            print(f"Resources: " + ", ".join([f"{k}: {v['available']}/{v['total']}" for k, v in state['resources'].items()]))
            running = [p['pid'] for p in state['patients'] if p['state'] == 'RUNNING']
            ready = [p['pid'] for p in state['patients'] if p['state'] == 'READY']
            waiting = [p['pid'] for p in state['patients'] if p['state'] == 'WAITING']
            completed = [p['pid'] for p in state['patients'] if p['state'] == 'COMPLETED']
            print(f"Active States -> RUNNING: {running} | READY: {ready} | WAITING: {waiting} | COMPLETED: {completed}")
            if state['wait_for_graph']['has_deadlock']:
                print(f"⚠️ DEADLOCK DETECTED! Cycles: {state['wait_for_graph']['detected_cycles']}")
            
            cmd = input("Press [Enter] for next tick (or 'run'): ")
            if cmd.strip().lower() == 'run':
                sim.run_all()
                break
        print(f"\nAll patients completed! Final duration: {sim.current_time} ticks.")

    elif choice == "2":
        print("\nExecuting multi-policy benchmark study on surge workload...")
        results = BenchmarkEngine.run_comparative_study(get_surge_workload())
        print("\n" + "=" * 90)
        print(f"{'Scheduling Policy':<36} | {'Crit Wait':<10} | {'Avg Wait':<10} | {'Avg TAT':<10} | {'Deadlocks':<10}")
        print("-" * 90)
        for k, v in results.items():
            print(f"{v['display_name']:<36} | {v['critical_avg_waiting_time']:<10.2f} | {v['avg_waiting_time']:<10.2f} | {v['avg_turnaround_time']:<10.2f} | {v['deadlocks_detected']:<10}")
        print("=" * 90)

    elif choice == "3":
        print("\nTriggering intentional cross-allocation deadlock with Banker's Avoidance OFF...")
        sim = HospitalSimulator(banker_avoidance_enabled=False)
        sim.trigger_deadlock_scenario()
        print("Advancing clock to trigger cycle detection...")
        state = sim.step()
        print(f"Deadlocks Detected: {sim.deadlocks_detected_count}")
        print(f"Deadlocks Recovered via Preemption: {sim.deadlocks_recovered_count}")
        print(f"WFG Edges: {state['wait_for_graph']['edges']}")

    elif choice == "4":
        sim = HospitalSimulator(SchedulingPolicy.PREEMPTIVE_PRIORITY_AGING)
        sim.load_workload(get_surge_workload())
        state = sim.run_all()
        print(f"\nSurge completed in {state['sim_time']} ticks.")
        print(f"Completed patients: {state['metrics']['completed_count']}/{state['metrics']['total_patients']}")
        print(f"Average Waiting Time: {state['metrics']['avg_waiting_time']} ticks")

    elif choice == "5":
        import app
        app.run_server(port=5050, auto_open=True)

if __name__ == "__main__":
    run_cli_interactive()
