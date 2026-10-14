/**
 * Hospital Emergency Resource Manager (HERM)
 * Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi
 * School of Computer Science and Engineering, Vellore Institute of Technology
 * 
 * Header Definitions: Models, POSIX Semaphores, Mutexes,
 * Banker's Avoidance, Wait-For Graph Deadlock Detection, and Scheduler.
 */

#ifndef HERM_H
#define HERM_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_PATIENTS 32
#define NUM_RESOURCES 5
#define MAX_LOG_MESSAGES 512

/* Resource Types */
#define RES_BEDS    0  /* ICU Beds: Capacity 4 */
#define RES_VENTS   1  /* Ventilators: Capacity 3 */
#define RES_DOCS    2  /* Doctors: Capacity 5 */
#define RES_NURSES  3  /* Nurses: Capacity 8 */
#define RES_OTS     4  /* Operation Theatres: Capacity 2 */

/* Acuity Priority Levels */
#define PRIO_CRITICAL 1 /* Trauma, Cardiac arrest - Preempts lower priorities */
#define PRIO_SERIOUS  2 /* Respiratory distress, Open fracture - Subject to aging */
#define PRIO_MODERATE 3 /* Controlled bleeding, Fever - Subject to aging */
#define PRIO_STABLE   4 /* Routine observation - Round Robin allowed */

/* Process States */
#define STATE_NEW       0
#define STATE_READY     1
#define STATE_RUNNING   2
#define STATE_WAITING   3
#define STATE_COMPLETED 4

/* Scheduling Policies */
#define POLICY_PREEMPTIVE_AGING 0
#define POLICY_NON_PREEMPTIVE   1
#define POLICY_FCFS             2

/* IPC Message Types */
typedef enum {
    MSG_ARRIVAL,
    MSG_REQUEST,
    MSG_GRANT,
    MSG_DENY,
    MSG_RELEASE,
    MSG_PREEMPT,
    MSG_AGING,
    MSG_DEADLOCK_DETECTED,
    MSG_DEADLOCK_RECOVERED,
    MSG_DONE
} MessageType;

/* IPC Event Message Struct */
typedef struct {
    int timestamp;
    MessageType type;
    char sender[32];
    char recipient[32];
    char pid[16];
    char details[256];
} IPCMessage;

/* Patient Process Control Block (PCB) */
typedef struct {
    char pid[16];
    char name[64];
    char condition[128];
    int arrival_time;
    int base_priority;
    int effective_priority;
    int burst_time;
    int remaining_time;
    int state;
    
    int max_claim[NUM_RESOURCES];
    int allocated[NUM_RESOURCES];
    int need[NUM_RESOURCES];

    int waiting_time;
    int turnaround_time;
    int completion_time;
    int ready_ticks;
    int preemption_count;
    int is_starved;
    int quantum_remaining;
    pthread_t thread_id;
} Patient;

/* POSIX Counting Semaphore */
typedef struct {
    char name[32];
    int capacity;
    int value;
    pthread_mutex_t lock;
    pthread_cond_t cond;
} CountingSemaphore;

/* Banker's Safety State */
typedef struct {
    int available[NUM_RESOURCES];
    int safe_sequence[MAX_PATIENTS];
    int safe_seq_len;
    int is_safe;
} BankerState;

/* Wait-For Graph (WFG) */
typedef struct {
    int adj[MAX_PATIENTS][MAX_PATIENTS];
    int num_nodes;
    int has_deadlock;
    int cycle_nodes[MAX_PATIENTS];
    int cycle_len;
} WaitForGraph;

/* Central Hospital Simulation Context */
typedef struct {
    int clock;
    int policy;
    int banker_enabled;
    int is_completed;
    int aging_interval;      /* Ta default = 4 */
    int aging_cap;           /* Cap at Level 2 */
    int time_quantum;        /* q default = 2 */
    int starvation_thresh;   /* 15 ticks */
    
    int deadlocks_detected;
    int deadlocks_recovered;

    Patient patients[MAX_PATIENTS];
    int patient_count;

    CountingSemaphore semaphores[NUM_RESOURCES];
    pthread_mutex_t allocation_mutex;

    IPCMessage messages[MAX_LOG_MESSAGES];
    int message_count;
    pthread_mutex_t msg_lock;

    BankerState banker;
    WaitForGraph wfg;
} HospitalSimulator;

/* Function Prototypes */
void herm_init(HospitalSimulator* sim, int policy, bool banker_enabled);
void herm_destroy(HospitalSimulator* sim);
void herm_reset(HospitalSimulator* sim);
void herm_load_standard_workload(HospitalSimulator* sim);
void herm_load_surge_workload(HospitalSimulator* sim);
void herm_add_patient(HospitalSimulator* sim, Patient p);

/* Synchronization Prototypes */
void sem_custom_init(CountingSemaphore* sem, const char* name, int capacity);
void sem_custom_destroy(CountingSemaphore* sem);
void sem_custom_acquire(CountingSemaphore* sem, int units);
void sem_custom_release(CountingSemaphore* sem, int units);
void sem_custom_reset(CountingSemaphore* sem, int capacity);

/* Banker's Algorithm */
bool banker_check_safety(HospitalSimulator* sim, BankerState* state);
bool banker_evaluate_request(HospitalSimulator* sim, int patient_idx, const int request[NUM_RESOURCES]);

/* Deadlock Detection & Recovery */
void wfg_build(HospitalSimulator* sim, WaitForGraph* wfg);
bool wfg_detect_cycle(WaitForGraph* wfg);
int wfg_select_victim(HospitalSimulator* sim, const int cycle_nodes[], int cycle_len);
void wfg_recover_deadlock(HospitalSimulator* sim, WaitForGraph* wfg);

/* Scheduler */
void scheduler_apply_aging(HospitalSimulator* sim);
int scheduler_select_next(HospitalSimulator* sim);
bool scheduler_should_preempt(HospitalSimulator* sim, int running_idx, int candidate_idx);

/* IPC Bus */
void ipc_publish(HospitalSimulator* sim, MessageType type, const char* sender, const char* recipient, const char* pid, const char* details);

/* Simulation Step */
void herm_step(HospitalSimulator* sim);
void herm_run_all(HospitalSimulator* sim, int max_ticks);
void herm_trigger_deadlock(HospitalSimulator* sim);

/* Analytics & Serialization */
void herm_export_json_state(HospitalSimulator* sim, char* buffer, size_t max_len);
void herm_run_comparative_benchmarks(void);

/* Helper Utilities */
const char* get_priority_name(int prio);
const char* get_state_name(int state);
const char* get_resource_name(int res_idx);
const char* get_policy_name(int policy);
const char* get_msg_type_name(MessageType type);

#endif /* HERM_H */
