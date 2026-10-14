# REVIEW 2 DOCUMENTATION: METHODOLOGY, ALGORITHMS & IMPLEMENTATION
**Course:** BCSE303L – Operating Systems  
**Faculty:** Dr. V. Ezhil Arasi  
**School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India**  
**Academic Year:** 2026–2027  

---

### Project Title
**Hospital Emergency Resource Manager (HERM) Using Operating System Concepts**

### Team Members
1. **Nitin Sunil Holkar** (Reg. No: 24BCE2819)
2. **Team Member 2** (Reg. No: 24BCEXXXX)
3. **Team Member 3** (Reg. No: 24BCEYYYY)

---

## 1. System Methodology & Working Principle
The Hospital Emergency Resource Manager (HERM) operates as an event-driven concurrent system. The emergency department is initialized with a pool of five distinct critical medical resource types:
- **ICU Beds:** 4 units
- **Mechanical Ventilators:** 3 units
- **Emergency Physicians / Doctors:** 5 units
- **Trauma Nurses:** 8 units
- **Operation Theatres (OT):** 2 units

Each incoming patient is represented as a process descriptor holding static medical parameters (Arrival Time, Base Urgency, Burst Treatment Time, and Declared Maximum Resource Claim Vector) and dynamic runtime telemetry (Effective Priority, Allocated Vector, Need Vector, State, Waiting Time, Turnaround Time, and Preemption Count).

---

## 2. Process State Machine & Lifecycle Transitions
Every patient process traverses five discrete states modeled after the classical five-state process execution model:

```
               ┌───────────┐
               │    NEW    │
               └─────┬─────┘
                     │ (Admit / Classify)
                     ▼
  ┌─────────────────────────────────────┐
  │                READY                │◄──────────────┐
  └───┬─────────────────────────────▲───┘               │
      │                             │                   │
      │ (Dispatch)                  │ (Preempt)         │ (Resource Granted /
      ▼                             │                   │  Deadlock Recovered)
  ┌─────────────────────────────────┴───┐               │
  │               RUNNING               │               │
  └───┬─────────────────────────────┬───┘               │
      │ (Complete)                  │ (Resource Busy /  │
      │                             │  Unsafe Banker)   │
      ▼                             ▼                   │
┌───────────┐             ┌───────────────────┐         │
│ COMPLETED │             │      WAITING      ├─────────┘
└───────────┘             └───────────────────┘
```

1. **`NEW`:** Patient is admitted at triage. Priority is classified into Levels 1–4, and process control parameters are initialized.
2. **`READY`:** Patient is queued in the scheduler waiting for clinical dispatch. Aging increments every $T_a$ ticks spent in this state.
3. **`RUNNING`:** Resources have been granted, and medical intervention is actively executing. Remaining burst time decrements each clock tick.
4. **`WAITING`:** Patient requires additional resources that are either physically exhausted or denied by Banker's safety check to prevent deadlock.
5. **`COMPLETED`:** Treatment burst finishes. All held resources are atomically reclaimed and returned to the semaphore pools. Turnaround and waiting times are committed to the audit log.

---

## 3. Algorithmic Formulations

### 3.1 Preemptive Priority Scheduling with Dynamic Aging
Patients are assigned a Base Priority $P_{base} \in \{1, 2, 3, 4\}$, where Level 1 represents the highest urgency:
- **Level 1 (Critical):** Cardiac arrest, severe hemorrhage, major polytrauma. Immediate preemption of lower-urgency running processes.
- **Level 2 (Serious):** Acute respiratory distress, open compound fracture. High priority, eligible for aging.
- **Level 3 (Moderate):** Controlled bleeding, severe fever, dehydration. Medium priority, eligible for aging.
- **Level 4 (Stable):** Minor lacerations, routine clinical checks. Lowest priority; served via Round Robin with time quantum $q = 2$.

#### Dynamic Aging Formula
To prevent lower-priority patients from starving when critical cases arrive continuously, the effective priority $P_{eff}$ dynamically upgrades as a function of continuous residence time in the `READY` queue ($t_{ready}$):

$$P_{eff}(t) = \max \left( P_{cap}, \; P_{base} - \left\lfloor \frac{t_{ready}}{T_a} \right\rfloor \right)$$

Where:
- $T_a = 4$ simulation clock ticks (aging threshold interval).
- $P_{cap} = 2$ (aging cap). A moderate (Level 3) or stable (Level 4) patient can age up to Level 2 (Serious), elevating them above standard waiting patients, but **never bypassing a genuine Level 1 Critical emergency**.
- Upon dispatch to `RUNNING`, $P_{eff}$ resets to $P_{base}$.

---

### 3.2 Concurrency Control & Synchronization Architecture
Resource contention and double allocation are prevented via two cooperating synchronization primitives:
1. **Counting Semaphores:** For each resource pool $R_j$ ($j \in \{1, \dots, 5\}$), a counting semaphore $S_j$ is initialized to its maximum capacity $C_j$:
   - $P(S_j, k)$: Atomically checks if $S_j \ge k$. If true, decrements $S_j \leftarrow S_j - k$; otherwise blocks the requesting thread until resources are freed.
   - $V(S_j, k)$: Atomically increments $S_j \leftarrow S_j + k$ and awakens blocked threads via condition variable broadcasts.
2. **Mutual Exclusion Allocation Mutex ($M_{alloc}$):** All queries and mutations to the system allocation tables, semaphore counters, and Banker safety checks are encapsulated within an uninterruptible critical section protected by $M_{alloc}$. This eliminates race conditions where two threads attempt to seize the last available ventilator simultaneously.

---

### 3.3 Deadlock Avoidance: Banker's Algorithm
The system tracks $m = 5$ resource types and $n$ active processes using four standard data structures:
- $\vec{Available} = [A_1, A_2, \dots, A_m]$
- $[Max]_{n \times m}$
- $[Allocation]_{n \times m}$
- $[Need]_{n \times m} = [Max] - [Allocation]$

#### Banker's Safety Algorithm
1. Initialize $\vec{Work} = \vec{Available}$ and $Finish[i] = \text{False}$ for all $i \in \{1, \dots, n\}$.
2. Search for an uncompleted process index $i$ satisfying:
   $$Finish[i] == \text{False} \quad \land \quad \vec{Need}_i \le \vec{Work}$$
3. If such an $i$ exists:
   $$\vec{Work} \leftarrow \vec{Work} + \vec{Allocation}_i, \quad Finish[i] \leftarrow \text{True}$$
   Append $P_i$ to the safe sequence $\vec{\sigma}_{safe}$, and return to Step 2.
4. If $Finish[i] == \text{True}$ for all $i \in \{1, \dots, n\}$, the system state is **SAFE**, and sequence $\vec{\sigma}_{safe}$ is returned. Otherwise, the state is **UNSAFE**.

#### Resource-Request Decision Logic
When patient $P_i$ issues a resource request vector $\vec{Req}_i$:
1. If $\vec{Req}_i \le \vec{Need}_i$ and $\vec{Req}_i \le \vec{Available}$:
   Hypothetically grant:
   $$\vec{Available}' = \vec{Available} - \vec{Req}_i$$
   $$\vec{Alloc}_i' = \vec{Alloc}_i + \vec{Req}_i$$
   $$\vec{Need}_i' = \vec{Need}_i - \vec{Req}_i$$
2. Execute Safety Algorithm on hypothetical state. If safe, commit changes; if unsafe, rollback to prior state and transition $P_i$ to `WAITING`.

---

### 3.4 Deadlock Detection (WFG) & Preemption Recovery
When Banker's avoidance is intentionally bypassed (or in environments where maximum claims are undeclared), deadlocks can form through circular waits.
1. **Wait-For Graph (WFG) Construction:**
   A directed graph $G = (V, E)$ is built where $V$ contains all active patients. A directed edge $(P_i \to P_j) \in E$ is drawn if $P_i$ is in `WAITING` state needing resource $R_k$, and $P_j$ holds allocated units of $R_k$ while $\vec{Available}[R_k] == 0$.
2. **Cycle Detection via Depth-First Search (DFS):**
   A recursive DFS traversal maintains an active recursion stack. Encountering a back-edge immediately identifies a circular wait set:
   $$P_a \to P_b \to \dots \to P_z \to P_a$$
3. **Victim Selection & Preemption:**
   For each detected cycle, a victim process $P_{victim}$ is selected using a three-tier deterministic scoring metric:
   - **Primary Criterion:** Lowest urgency priority (highest numerical level: Level 4 Stable chosen before Level 1 Critical).
   - **Secondary Criterion (Tie Breaker):** Least clinical progress completed ($\text{Progress} = BT - RT$ is minimal).
   - **Tertiary Criterion (Tie Breaker):** Most recent arrival time.
   
   The victim's allocated resources are immediately preempted and returned to the semaphore pool. The victim process is transitioned to `READY`, retaining its accrued waiting time and aging status to prevent repeated victim selection (starvation avoidance).

---

## 4. Technology Stack & Configuration
| Component | Technology / Library | Architectural Role |
| :--- | :--- | :--- |
| **Language** | Python 3.13 | High-precision concurrency, standard library primitives |
| **Synchronization** | `threading`, `Lock`, `Condition` | Counting semaphores, allocation mutex, thread safety |
| **Database** | SQLite 3 (`sqlite3`) | Persistent audit trails, event telemetry, deadlock logging |
| **Data Structures** | `numpy`, `queue`, `collections` | Fast matrix manipulation, FIFO and priority queues |
| **Web Server** | `http.server`, `socketserver` | High-performance zero-dependency RESTful HTTP API |
| **Web Dashboard** | HTML5, CSS3 Variables, ES6 JS | Glassmorphic dark-mode emergency room command center |
| **Visualizations** | SVG Vector Canvas | Interactive dynamic Wait-For Graph and cycle visualizer |
| **Desktop GUI** | Python Tkinter (`tkinter.ttk`) | Native local graphical window fallback |
| **CLI Dashboard** | Python Shell Utility | Terminal-based step-by-step runner and benchmark suite |

---

## 5. Module-Wise Implementation Breakdown
The codebase is structured into clear, decoupled modules under `herm/`:
1. `herm/core/models.py`: Defines `Patient`, `PriorityLevel`, `ProcessState`, and resource vector schemas.
2. `herm/core/synchronization.py`: Implements `CountingSemaphore` and `SynchronizationManager` with `allocation_mutex`.
3. `herm/core/banker.py`: Encapsulates Banker's safety evaluation and resource-request testing.
4. `herm/core/deadlock_detector.py`: Implements Wait-For Graph construction, DFS cycle search, and preemption recovery.
5. `herm/core/scheduler.py`: Houses the multi-policy scheduler (Preemptive Priority with Aging, Non-Preemptive, FCFS).
6. `herm/core/ipc_bus.py`: Event bus managing discrete message passing (`ARRIVAL`, `GRANT`, `DENY`, `PREEMPT`, `DONE`).
7. `herm/core/database.py`: Schema definitions and queries for simulation runs, patient telemetry, and deadlock audit logs.
8. `herm/core/simulator.py`: Central simulation engine executing discrete clock progression and state coordination.
9. `herm/core/benchmark.py`: Automated batch evaluator testing identical workloads across all algorithms.
10. `app.py`: Web server exposing REST API endpoints on port 5050.
11. `gui.py` & `cli.py`: Native Tkinter desktop GUI and terminal dashboard.

---

## 6. Preliminary Validation on Standard Workload
The simulation engine was validated using the standard benchmark workload from Table IV of the research proposal:

### Initial Workload Specification
| PID | Arrival | Base Priority | Burst Time | Maximum Resource Requirements |
| :--- | :--- | :--- | :--- | :--- |
| **P1** | 0 | 3 (Moderate) | 8 | 1 Bed, 1 Doctor, 2 Nurses |
| **P2** | 1 | 2 (Serious) | 6 | 1 Bed, 1 Ventilator, 1 Doctor |
| **P3** | 2 | 4 (Stable) | 4 | 1 Doctor, 1 Nurse |
| **P4** | 3 | 1 (Critical) | 5 | 1 Bed, 1 Ventilator, 2 Doctors, 2 Nurses, 1 Theatre |
| **P5** | 4 | 3 (Moderate) | 7 | 1 Bed, 1 Doctor, 1 Nurse |
| **P6** | 6 | 1 (Critical) | 4 | 1 Bed, 1 Ventilator, 1 Doctor, 1 Theatre |

### Preliminary Results
- **Preemption Verification:** When P4 arrives at $T=3$ as a Level 1 Critical emergency, it successfully preempts running lower-priority tasks, seizing the Operation Theatre immediately.
- **Aging Verification:** P3 (Level 4 Stable) waiting in the ready queue has its priority aged up to Level 3 at $T=6$ and Level 2 at $T=10$, preventing indefinite starvation.
- **Deadlock Recovery:** Injecting cross-dependencies with Banker's avoidance disabled successfully produces a 2-node cycle ($P_A \rightleftharpoons P_B$) detected by the WFG DFS module, which resolves the cycle within 1 clock tick by preempting the lower-priority victim.
