# Hospital Emergency Resource Manager (HERM)
**Course:** BCSE303L - Operating Systems | **Faculty:** Dr. V. Ezhil Arasi  
**School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Vellore**

### Team Members
1. **Gaurav Charpe** (`24BCT0326`)
2. **Nitin Sunil Holkar** (`24BCE2819`)
3. **Aditya Phogaat** (`24BDS0349`)

---

## Live Interactive Web Dashboard (Open Directly from GitHub)

You can open and test the interactive Web Dashboard directly in your browser with **one click** (no installation required):

- **[Click Here to Open Live HERM Web Dashboard](https://htmlpreview.github.io/?https://github.com/gauravcharpe/hospital-emergency-resource-manager/blob/main/web/index.html)**

*(Alternatively, if you download or clone this repository, you can either double-click `web/index.html` to open it in any browser, or run `./herm_server` to run the C backend server at `http://localhost:5050`.)*

---

## Project Overview

Hospital emergency departments have a fixed number of ICU beds, mechanical ventilators, doctors, trauma nurses, and operating theatres. When multiple patients arrive at the same time with different medical urgencies, manual allocation or simple First-Come First-Served (FCFS) queues cause three major problems:
1. **Priority Inversion:** Critical trauma or cardiac arrest patients wait behind stable patients who arrived earlier.
2. **Race Conditions:** Uncoordinated requests try to assign the last remaining ICU bed or ventilator at the same time.
3. **Deadlocks and Starvation:** Two treatments hold resources while waiting on each other in a circular wait, or low-priority patients starve indefinitely.

**HERM** solves these problems in C by modeling the emergency room as an **Operating System Kernel**:
- **Patients as Processes:** Each patient is stored as a Process Control Block (`Patient` struct) moving through a 5-state lifecycle (`NEW`, `READY`, `RUNNING`, `WAITING`, `COMPLETED`).
- **Counting Semaphores & Mutex Locks:** Synchronizes 5 shared resource pools (`ICU Beds = 4`, `Ventilators = 3`, `Doctors = 5`, `Nurses = 8`, `Operating Theatres = 2`) using `pthread_mutex_t` and `pthread_cond_t`.
- **Preemptive Priority Scheduling with Dynamic Aging:** Schedules patients across 4 priority levels (`L1 Critical` to `L4 Stable`). Level 1 patients immediately preempt lower-priority running patients. Waiting patients age by +1 priority level every 4 clock ticks (capped at Level 2 so routine cases never block true Level 1 emergencies).
- **Dijkstra's Banker's Algorithm:** Checks whether a safe execution sequence exists before granting resources.
- **Wait-For Graph (WFG) & Cycle Recovery:** Uses Depth-First Search (DFS) to detect circular waits when avoidance is disabled and rolls back the lowest-priority victim process.

---

## Performance Benchmark Comparison (`make bench`)

Tested on an 8-patient high-contention emergency surge workload:

| Scheduling Policy | Critical (L1) Wait | Overall Avg Wait | Avg Turnaround | Deadlocks | Starved Patients |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. First-Come First-Served (FCFS)** | 8.67 sec | 7.70 sec | 14.90 sec | 0 | 0 |
| **2. Non-Preemptive Priority** | 3.33 sec | 7.10 sec | 14.30 sec | 0 | 0 |
| **3. Preemptive Priority + Aging (HERM)** | **0.67 sec** | **4.40 sec** | **11.60 sec** | **0 (Banker's Safe)** | **0** |
| **4. Preemptive + Aging (Banker's OFF)** | 0.67 sec | 4.40 sec | 11.60 sec | 1 Detected & Recovered | 0 |

- **92.3% Reduction in Critical Waiting Time:** Critical Level 1 trauma wait time drops from `8.67s` (FCFS) to `0.67s` (HERM).
- **42.9% Lower Overall Waiting Time:** Overall average wait time improves from `7.70s` to `4.40s`.
- **Zero Starvation & Zero Unhandled Deadlocks:** Capped dynamic aging bounds Level 4 wait times at `4.33s`.

---

## How to Compile and Run Locally (C Engine + Web Server)

### 1. Compile the C Code
```bash
make
```
This compiles two executables using `clang -Wall -Wextra -O2 -Iinclude -pthread`:
- `herm_cli`: Interactive terminal simulator and benchmark suite.
- `herm_server`: Embedded C HTTP server on port `5050`.

### 2. Run the Web Dashboard Locally
```bash
./herm_server
```
Then open **[http://localhost:5050](http://localhost:5050)** in Safari or Chrome (or simply double-click `web/index.html`).

### 3. Run the Terminal Simulator & Benchmark Suite
```bash
./herm_cli
```
Or run the automated benchmark comparison directly:
```bash
make bench
```

---

## Project Directory Structure

```text
hospital-emergency-resource-manager/
├── Makefile               # Build configuration for herm_cli and herm_server
├── README.md              # Project documentation and live dashboard link
├── include/
│   └── herm.h             # Header defining PCB struct, resource pools, and prototypes
├── src/
│   ├── main_cli.c         # Interactive terminal CLI and menu modes (1 to 5)
│   ├── server.c           # Embedded C HTTP socket server (port 5050)
│   ├── models.c           # Patient PCB initialization and workload presets
│   ├── sync.c             # Counting semaphores, pthread_mutex_t, and pthread_cond_t
│   ├── scheduler.c        # Preemptive priority scheduler and capped dynamic aging
│   ├── banker.c           # Dijkstra's Banker's Algorithm safety check
│   ├── deadlock.c         # Wait-For Graph (WFG) DFS cycle detection and victim rollback
│   ├── ipc.c              # Thread-safe IPC message log
│   ├── simulator.c        # Discrete-time simulation engine
│   └── benchmark.c        # Automated benchmark runner across scheduling policies
└── web/
    └── index.html         # Interactive Web Command Center UI
```
