# REVIEW 1 DOCUMENTATION: PROBLEM, LITERATURE SURVEY & PROPOSED SYSTEM
**Course:** BCSE303L – Operating Systems  
**Faculty:** Dr. V. Ezhil Arasi  
**School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, India**  
**Academic Year:** 2026–2027  

---

### Project Title
**Hospital Emergency Resource Manager (HERM) Using Operating System Concepts**

### Team Members
1. **Nitin Sunil Holkar** (Reg. No: 24BCE2819)
2. **Gaurav Charpe** (Reg. No: 24BCT0326)
3. **Aditya Phogaat** (Reg. No: 24BCE/BCT)

---

## 1. Problem Statement
Hospital Emergency Departments (ED) routinely confront sudden, unpredictable surges of critically ill and injured patients requiring simultaneous access to strictly finite clinical infrastructure. Key bottleneck resources include intensive care unit (ICU) beds, mechanical ventilators, emergency triage physicians, trauma nurses, and operating theatres. 

In the absence of a synchronized, automated management system, contemporary emergency departments face three debilitating operational failures:
1. **Priority Inversion and Misordering:** Lower-urgency stable patients occupy specialized life-support equipment or operating theatres while acute, life-threatening cases wait in triage queues.
2. **Race Conditions and Double Allocation:** Concurrent unsynchronized requests originating from independent clinical departments attempt to claim the same critical resource (e.g., the last available ventilator or trauma bay) at the same physical instant, resulting in conflicting grants or uncoordinated overrides.
3. **Circular Wait Deadlocks and Starvation:** Critical patients hold a subset of necessary resources while waiting indefinitely for remaining equipment held by other patients (circular dependencies). Concurrently, low-priority patients suffer complete starvation under persistent arrival of higher-urgency cases.

This project designs, models, and implements a concurrent software solution that treats the emergency care environment as an operating system. Patients are abstracted as computational processes, and scarce medical assets are managed as lockable, preemptible system resources governed by rigorous OS scheduling, synchronization, and deadlock management principles.

---

## 2. Motivation
Operating systems have developed robust, mathematically proven mechanisms over decades to share scarce central processing units, memory banks, and I/O devices among competing concurrent tasks. The mathematical and architectural isomorphism between an OS kernel and a multi-resource emergency room provides a powerful opportunity:
- Triage protocols (such as the Emergency Severity Index) establish priority levels, directly analogous to priority scheduling queues.
- Finite beds and medical devices behave identically to counting semaphore resource pools.
- The risk of simultaneous assignment parallels critical-section race conditions, solvable via mutual exclusion (mutexes).
- Incomplete multi-resource allocations lead directly to Coffman deadlock conditions, resolvable via Dijkstra's Banker’s Algorithm and Wait-For Graph cycle detection.
- By translating these concepts into an interactive, visual software platform, the system demonstrates how OS theory solves tangible, life-critical logistical bottlenecks with total transparency.

---

## 3. Project Objectives
1. **Process Modeling:** Abstract each emergency patient as an independent process defined by unique Arrival Time ($AT$), Base Urgency Priority ($P_{base} \in [1,4]$), Treatment Burst Time ($BT$), and Maximum Resource Claim Vector ($\vec{Max}$).
2. **Preemptive Scheduling with Aging:** Implement a hybrid preemptive priority scheduler where Level 1 (Critical) patients immediately preempt running lower-priority tasks. To eliminate starvation, implement an aging mechanism where waiting time in the `READY` queue progressively elevates patient effective priority up to Level 2.
3. **Concurrency Control & Synchronization:** Guard multi-unit resource pools (ICU beds, ventilators, doctors, nurses, operating theatres) with counting semaphores, and encapsulate allocation state transitions inside atomic mutex locks to guarantee thread-safe operations.
4. **Deadlock Avoidance:** Integrate Dijkstra’s Banker’s Algorithm to evaluate the safety of prospective resource grants prior to allocation, preventing the system from transitioning into unsafe states.
5. **Deadlock Detection & Recovery:** Formulate a runtime Wait-For Graph (WFG) analyzed via Depth-First Search (DFS) cycle detection. Implement automated preemption-based recovery that identifies the lowest-priority, least-progressed patient in the cycle, reclaims contested assets, and reschedules the victim without losing accrued aging credits.
6. **Inter-Process Communication (IPC):** Construct a modular message-passing bus carrying structured discrete event messages (`ARRIVAL`, `REQUEST`, `GRANT`, `DENY`, `RELEASE`, `PREEMPT`, `DONE`) between clinical modules.
7. **Empirical Benchmarking & Real-Time Dashboard:** Provide an aesthetic, real-time command dashboard accompanied by comparative performance evaluations against First-Come, First-Served (FCFS) and Non-Preemptive Priority policies.

---

## 4. Literature Survey (Peer-Reviewed Google Scholar Citations)

Every citation included below represents authentic research indexed in Google Scholar from premier publishers (IEEE, ACM, Springer, Elsevier, INFORMS, Wiley):

1. **Gilboy et al. [1]** formulated the *Emergency Severity Index (ESI)*, a five-level triage framework standardizing urgency classification based on acute mortality risk and projected resource consumption. While ESI successfully categorizes clinical priority, it lacks concurrent resource scheduling and automated conflict resolution mechanisms.
2. **Jacobson, Argon, and Ziya [2]** investigated priority assignment during mass-casualty emergency events by modeling patient flows as queueing networks with impatient jobs. Their analytical queuing model demonstrated that static triage policies deteriorate during demand spikes, but their work did not address runtime resource locking or circular dependencies.
3. **Xiao, Osterweil, and Wang [3]** applied genetic algorithms to dynamically reschedule emergency department activities and clinical staff. Their work confirmed that resource contention significantly exacerbates treatment delays; however, optimization heuristics require intensive offline computation and do not enforce operating system synchronization primitives.
4. **Rosemarin, Rosenfeld, and Kraus [4]** proposed an online deep-reinforcement-learning approach to match emergency patients to specialized caregivers. While empirical throughput improved, the model relies on historical hospital datasets and functions as a black-box, lacking deterministic safety guarantees and deadlock prevention.
5. **Saghafian et al. [5]** introduced complexity-augmented triage incorporating patient physiological complexity into priority rankings. Their analytic models highlighted that ignoring multi-resource requirements causes downstream bed-blocking, reinforcing the necessity of multi-resource dependency tracking.
6. **Silberschatz, Galvin, and Gagne [6]** provided the authoritative foundational framework for process state lifecycles, counting semaphores, mutual exclusion, Banker's algorithm, and wait-for graph cycle detection, establishing the theoretical base for our implementation.
7. **Liu and Layland [7]** established classical theorems on priority-driven preemptive scheduling in multi-tasking systems, demonstrating that assigning immediate CPU preemption to hard-deadline tasks minimizes worst-case latency.
8. **Coffman, Elphick, and Shoshani [8]** identified the four necessary and sufficient conditions for system deadlock: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. This taxonomy directly underpins our two-layer defense combining Banker's avoidance and cycle preemption.
9. **Dijkstra [9]** originated the counting semaphore primitive $(P, V)$ and cooperating sequential processes, providing the exact mathematical synchronization abstraction required to track finite beds, ventilators, and surgical staff.
10. **Paul and Lin [10]** utilized discrete-event simulation to evaluate hospital emergency room bottlenecks, showing that bed and staff availability dictate total turnaround time more significantly than initial triage speed.
11. **Wiler et al. [11]** analyzed emergency department front-end operations across major trauma centers, reporting that misaligned bed allocation and uncoordinated admissions represent the primary cause of prolonged patient waiting times.
12. **Kolisch [12]** evaluated serial and parallel resource-constrained scheduling heuristics, establishing benchmarks for multi-resource allocation that parallel operating system Banker matrix structures.
13. **Habermann [13]** formalized mathematical proofs for deadlock avoidance in multi-resource environments, verifying that tracking available, maximum, and allocated vectors guarantees safe state maintenance.
14. **Holt [14]** developed graph-theoretic formulations of computer system deadlocks, proving that directed cycles in resource-allocation graphs with single-unit resources, and Wait-For Graphs among processes, are both necessary and sufficient indicators of system deadlock.
15. **Buttazzo [15]** examined real-time scheduling mechanisms, demonstrating that priority aging provides an optimal balance between prioritizing urgent arrivals and preventing prolonged starvation of lower-priority processes.
16. **Armony et al. [16]** conducted an extensive data-driven queuing study of hospital patient flows, concluding that holistic management of shared resources drastically cuts emergency department boarding time compared to isolated silo scheduling.

---

## 5. Research Gap
Existing hospital emergency management literature focuses predominantly on offline queuing theory, complex machine-learning predictors, or static workflow software. These systems exhibit several critical shortcomings:
- **No Concurrency Control:** They treat hospital beds and medical staff as static spreadsheet records, offering no runtime mutual exclusion or counting semaphore synchronization to prevent race conditions during simultaneous claims.
- **Neglect of Deadlock Dynamics:** Prior triage software completely ignores circular resource wait conditions (e.g., Patient A holding an Operation Theatre and waiting for an ICU Bed, while Patient B holds an ICU Bed and waits for an Operation Theatre).
- **Opaque Scheduling Logic:** AI and heuristic schedulers cannot provide formal safety guarantees, making them difficult to audit and explain in high-stakes environments.
- **Absence of Unified Preemption and Aging:** Real-time preemption for trauma arrivals has rarely been coupled with dynamic priority aging and Banker's safety verification within a single, unified concurrent engine.

---

## 6. Proposed System Architecture
The Hospital Emergency Resource Manager (HERM) structures the emergency department into a modular, layered concurrent architecture:

```
                  [ Emergency Patient Arrival ]
                               │
                               ▼
                    [ Priority Triage Engine ]
                 (Assigns Base Level 1, 2, 3, or 4)
                               │
                               ▼
                  [ Process Scheduler Module ]
     ┌─────────────────────────┼─────────────────────────┐
     ▼                         ▼                         ▼
 [Preemptive Priority]    [Priority Aging]      [Round Robin (L4)]
     │                         │                         │
     └─────────────────────────┬─────────────────────────┘
                               │
                               ▼
               [ Concurrency & Sync Manager ]
             (Counting Semaphores & Mutex Locks)
                               │
                               ▼
             [ Deadlock Avoidance (Banker's) ]
           ┌───────────────────┴───────────────────┐
           ▼                                       ▼
      [Safe State]                            [Unsafe State]
           │                                       │
           ▼                                       ▼
 [Grant Resources & Run]                   [Enqueue to WAITING]
           │                                       │
           └───────────────────┬───────────────────┘
                               │
                               ▼
                 [ Deadlock Detector (WFG) ]
             (DFS Cycle Detection & Preemption)
                               │
                               ▼
            [ SQLite Logger & Real-Time Dashboard ]
```

### Table 1: Mapping Operating System Concepts to Emergency Hospital Operations
| Operating System Concept | Hospital Emergency Department Implementation |
| :--- | :--- |
| **Process** | Incoming emergency patient request (Arrival Time, Priority, Burst Time, Resource Claims) |
| **Process State Machine** | Lifecycle transitions: `NEW`, `READY`, `RUNNING`, `WAITING`, `COMPLETED` |
| **Preemptive Priority Scheduling** | Level 1 Critical trauma patients immediately preempt running lower-urgency patients |
| **Priority Aging** | Elevates waiting patient effective priority by 1 level every $T_a$ ticks (capped at Level 2) |
| **Round Robin Scheduling** | Time-sliced sharing (quantum $q$) among stable Level 4 non-critical patients |
| **Counting Semaphore** | Tracks available quantities of ICU Beds (4), Ventilators (3), Doctors (5), Nurses (8), Theatres (2) |
| **Mutex Lock** | Guarantees atomic verification and allocation steps, eliminating double-booking race conditions |
| **Banker’s Algorithm** | Evaluates $\vec{Available}$, $[Max]$, $[Alloc]$, and $[Need]$ matrices to avoid unsafe states |
| **Wait-For Graph (WFG)** | Directed dependency graph ($P_i \to P_j$); DFS identifies circular wait deadlocks |
| **Deadlock Recovery** | Preempts lowest-urgency, least-progressed victim patient in cycle to free locked resources |
| **Inter-Process Comm (IPC)** | Structured message bus carrying typed events (`ARRIVAL`, `GRANT`, `DENY`, `PREEMPT`, `DONE`) |

---

## 7. References
```
[1]  N. Gilboy, P. Tanabe, D. Travers, and A. M. Rosenau, "Emergency Severity Index (ESI): A Triage Tool for Emergency Department Care, Version 4," Implementation Handbook, Agency for Healthcare Research and Quality (AHRQ), 2012.
[2]  E. Jacobson, N. T. Argon, and S. Ziya, "Priority assignment in emergency response," Operations Research, vol. 60, no. 4, pp. 813–832, 2012.
[3]  J. Xiao, L. J. Osterweil, and Q. Wang, "Dynamic scheduling of emergency department resources," in Proc. 1st ACM Int. Health Informatics Symp. (IHI '10), 2010, pp. 590–599.
[4]  H. Rosemarin, A. Rosenfeld, and S. Kraus, "Emergency department online patient-caregiver scheduling," in Proc. AAAI Conf. Artif. Intell., vol. 33, no. 1, pp. 695–701, 2019.
[5]  S. Saghafian, W. J. Hopp, M. P. Van Oyen, J. S. Desmond, and S. L. Kronick, "Complexity-augmented triage: A tool for improving patient safety and operational efficiency," Manuf. Serv. Oper. Manag., vol. 16, no. 3, pp. 327–345, 2014.
[6]  A. Silberschatz, P. B. Galvin, and G. Gagne, Operating System Concepts, 10th ed. Hoboken, NJ, USA: John Wiley & Sons, 2018.
[7]  C. L. Liu and J. W. Layland, "Scheduling algorithms for multiprogramming in a hard-real-time environment," J. ACM, vol. 20, no. 1, pp. 46–61, 1973.
[8]  E. G. Coffman, M. J. Elphick, and A. Shoshani, "System deadlocks," ACM Comput. Surv., vol. 3, no. 2, pp. 67–78, 1971.
[9]  E. W. Dijkstra, "Cooperating sequential processes," Technological Univ. Eindhoven, Eindhoven, The Netherlands, Tech. Rep. EWD-123, 1965.
[10] J. A. Paul and L. Lin, "Models for improving patient throughput and waiting time in an emergency department," OR Spectrum, vol. 34, no. 1, pp. 201–234, 2012.
[11] J. L. Wiler, C. Gentle, J. M. Halfpenny, et al., "Optimizing emergency department front-end operations," Ann. Emerg. Med., vol. 55, no. 2, pp. 142–160, 2010.
[12] R. Kolisch, "Serial and parallel resource-constrained project scheduling methods revisited: Theory and computation," Eur. J. Oper. Res., vol. 90, no. 2, pp. 320–333, 1996.
[13] A. N. Habermann, "Prevention of system deadlocks," Commun. ACM, vol. 12, no. 7, pp. 373–377, 1969.
[14] R. C. Holt, "Some deadlock properties of computer systems," ACM Comput. Surv., vol. 4, no. 3, pp. 179–196, 1972.
[15] G. C. Buttazzo, Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications, 3rd ed. New York, NY, USA: Springer, 2011.
[16] M. Armony, S. Israelit, A. Mandelbaum, et al., "On patient flow in hospitals: A data-based queueing-science perspective," Stoch. Syst., vol. 5, no. 1, pp. 146–194, 2015.
```
