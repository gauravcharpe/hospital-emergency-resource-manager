/**
 * Hospital Emergency Resource Manager (HERM)
 * Central Simulation Engine in C.
 */

#include "herm.h"

void herm_init(HospitalSimulator* sim, int policy, bool banker_enabled) {
    memset(sim, 0, sizeof(HospitalSimulator));

    sim->clock = 0;
    sim->policy = policy;
    sim->banker_enabled = banker_enabled ? 1 : 0;
    sim->is_completed = 0;
    sim->aging_interval = 4;
    sim->aging_cap = 2;
    sim->time_quantum = 2;
    sim->starvation_thresh = 15;
    sim->deadlocks_detected = 0;
    sim->deadlocks_recovered = 0;

    pthread_mutex_init(&sim->allocation_mutex, NULL);
    pthread_mutex_init(&sim->msg_lock, NULL);

    /* Capacities matching Proposal Table III */
    sem_custom_init(&sim->semaphores[RES_BEDS],   "ICU_Beds",           4);
    sem_custom_init(&sim->semaphores[RES_VENTS],  "Ventilators",        3);
    sem_custom_init(&sim->semaphores[RES_DOCS],   "Doctors",            5);
    sem_custom_init(&sim->semaphores[RES_NURSES], "Nurses",             8);
    sem_custom_init(&sim->semaphores[RES_OTS],    "Operation_Theatres", 2);

    herm_load_standard_workload(sim);
    ipc_publish(sim, MSG_ARRIVAL, "Reception", "System", "ALL", "System initialized with standard emergency workload.");
}

void herm_destroy(HospitalSimulator* sim) {
    for (int r = 0; r < NUM_RESOURCES; r++) {
        sem_custom_destroy(&sim->semaphores[r]);
    }
    pthread_mutex_destroy(&sim->allocation_mutex);
    pthread_mutex_destroy(&sim->msg_lock);
}

void herm_reset(HospitalSimulator* sim) {
    sim->clock = 0;
    sim->is_completed = 0;
    sim->deadlocks_detected = 0;
    sim->deadlocks_recovered = 0;
    sim->message_count = 0;

    sem_custom_reset(&sim->semaphores[RES_BEDS],   4);
    sem_custom_reset(&sim->semaphores[RES_VENTS],  3);
    sem_custom_reset(&sim->semaphores[RES_DOCS],   5);
    sem_custom_reset(&sim->semaphores[RES_NURSES], 8);
    sem_custom_reset(&sim->semaphores[RES_OTS],    2);

    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        p->state = STATE_NEW;
        p->effective_priority = p->base_priority;
        p->remaining_time = p->burst_time;
        p->waiting_time = 0;
        p->turnaround_time = 0;
        p->completion_time = 0;
        p->ready_ticks = 0;
        p->preemption_count = 0;
        p->is_starved = 0;
        p->quantum_remaining = 0;
        for (int r = 0; r < NUM_RESOURCES; r++) {
            p->allocated[r] = 0;
            p->need[r] = p->max_claim[r];
        }
    }
}

void herm_add_patient(HospitalSimulator* sim, Patient p) {
    if (sim->patient_count < MAX_PATIENTS) {
        p.state = STATE_NEW;
        p.effective_priority = p.base_priority;
        p.remaining_time = p.burst_time;
        for (int r = 0; r < NUM_RESOURCES; r++) {
            p.allocated[r] = 0;
            p.need[r] = p.max_claim[r];
        }
        sim->patients[sim->patient_count++] = p;
    }
}

void herm_trigger_deadlock(HospitalSimulator* sim) {
    sim->banker_enabled = 0;

    Patient p_a = { "P_DEAD_A", "Emergency Cardiac", "Severe cardiac block", sim->clock, PRIO_SERIOUS, PRIO_SERIOUS, 8, 8, STATE_WAITING, {1, 0, 0, 0, 1}, {0, 0, 0, 0, 1}, {1, 0, 0, 0, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p_b = { "P_DEAD_B", "Severe Polytrauma", "Internal hemorrhage", sim->clock, PRIO_MODERATE, PRIO_MODERATE, 8, 8, STATE_WAITING, {1, 0, 0, 0, 1}, {1, 0, 0, 0, 0}, {0, 0, 0, 0, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };

    herm_add_patient(sim, p_a);
    herm_add_patient(sim, p_b);

    /* Deplete remaining free units to force circular wait */
    sem_custom_reset(&sim->semaphores[RES_BEDS], 0);
    sem_custom_reset(&sim->semaphores[RES_OTS], 0);

    ipc_publish(sim, MSG_REQUEST, "Tester", "ResourceManager", "P_DEAD_A & P_DEAD_B", "Cross-allocation circular wait injected with Banker's Avoidance OFF.");
}

void herm_step(HospitalSimulator* sim) {
    if (sim->is_completed) return;

    int t = sim->clock;

    /* 1. Admit New Arrivals */
    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        if (p->state == STATE_NEW && p->arrival_time <= t) {
            p->state = STATE_READY;
            char details[256];
            snprintf(details, sizeof(details), "Admitted at triage as %s (Level %d).", get_priority_name(p->base_priority), p->base_priority);
            ipc_publish(sim, MSG_ARRIVAL, "Reception", "Scheduler", p->pid, details);
        }
    }

    /* 2. Dynamic Priority Aging */
    scheduler_apply_aging(sim);

    /* 3. Deadlock Detection on WFG */
    wfg_build(sim, &sim->wfg);
    if (wfg_detect_cycle(&sim->wfg)) {
        sim->deadlocks_detected++;
        char details[256];
        snprintf(details, sizeof(details), "Circular wait detected among %d patient nodes.", sim->wfg.cycle_len);
        ipc_publish(sim, MSG_DEADLOCK_DETECTED, "DeadlockDetector", "RecoveryEngine", "CIRCULAR_WAIT", details);

        /* Recover by selecting victim and preempting */
        wfg_recover_deadlock(sim, &sim->wfg);
    }

    /* 4. Preemption Check */
    if (sim->policy == POLICY_PREEMPTIVE_AGING) {
        int running_idx = -1;
        for (int i = 0; i < sim->patient_count; i++) {
            if (sim->patients[i].state == STATE_RUNNING) {
                if (running_idx == -1 || sim->patients[i].effective_priority > sim->patients[running_idx].effective_priority) {
                    running_idx = i;
                }
            }
        }

        if (running_idx != -1) {
            for (int j = 0; j < sim->patient_count; j++) {
                if (sim->patients[j].state == STATE_READY) {
                    if (scheduler_should_preempt(sim, running_idx, j)) {
                        /* Preempt running patient */
                        Patient* r_pt = &sim->patients[running_idx];
                        Patient* c_pt = &sim->patients[j];

                        pthread_mutex_lock(&sim->allocation_mutex);
                        for (int res = 0; res < NUM_RESOURCES; res++) {
                            if (r_pt->allocated[res] > 0) {
                                sem_custom_release(&sim->semaphores[res], r_pt->allocated[res]);
                                r_pt->need[res] += r_pt->allocated[res];
                                r_pt->allocated[res] = 0;
                            }
                        }
                        pthread_mutex_unlock(&sim->allocation_mutex);

                        r_pt->state = STATE_READY;
                        r_pt->preemption_count++;

                        char details[256];
                        snprintf(details, sizeof(details), "Preempted by higher priority patient %s (Level %d).", c_pt->pid, c_pt->effective_priority);
                        ipc_publish(sim, MSG_PREEMPT, "Scheduler", r_pt->pid, r_pt->pid, details);
                        break;
                    }
                }
            }
        }
    }

    /* 5. Resource Allocation & Dispatch */
    while (1) {
        int candidate_idx = scheduler_select_next(sim);
        if (candidate_idx == -1) break;

        Patient* cand = &sim->patients[candidate_idx];

        /* Check physical semaphore availability */
        bool can_physically_allocate = true;
        for (int r = 0; r < NUM_RESOURCES; r++) {
            if (cand->need[r] > sim->semaphores[r].value) {
                can_physically_allocate = false;
                break;
            }
        }

        if (!can_physically_allocate) {
            cand->state = STATE_WAITING;
            break; /* No more allocations can proceed this tick */
        }

        /* Check Banker's Algorithm if enabled */
        if (sim->banker_enabled) {
            if (!banker_evaluate_request(sim, candidate_idx, cand->need)) {
                cand->state = STATE_WAITING;
                char details[256];
                snprintf(details, sizeof(details), "Request denied by Banker's safety check to prevent potential deadlock.");
                ipc_publish(sim, MSG_DENY, "BankerAvoidance", cand->pid, cand->pid, details);
                break;
            }
        }

        /* Grant resources atomically */
        pthread_mutex_lock(&sim->allocation_mutex);
        for (int r = 0; r < NUM_RESOURCES; r++) {
            if (cand->need[r] > 0) {
                sem_custom_acquire(&sim->semaphores[r], cand->need[r]);
                cand->allocated[r] += cand->need[r];
                cand->need[r] = 0;
            }
        }
        pthread_mutex_unlock(&sim->allocation_mutex);

        cand->state = STATE_RUNNING;
        if (cand->effective_priority == 4) {
            cand->quantum_remaining = sim->time_quantum;
        }

        char details[256];
        snprintf(details, sizeof(details), "Resources granted; patient entered RUNNING treatment state.");
        ipc_publish(sim, MSG_GRANT, "ResourceManager", cand->pid, cand->pid, details);
    }

    /* 6. Treatment Progress */
    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        if (p->state == STATE_RUNNING) {
            p->remaining_time--;
            if (p->effective_priority == 4) {
                p->quantum_remaining--;
            }

            if (p->remaining_time <= 0) {
                p->state = STATE_COMPLETED;
                p->completion_time = t + 1;
                p->turnaround_time = p->completion_time - p->arrival_time;
                p->waiting_time = p->turnaround_time - p->burst_time;
                if (p->waiting_time < 0) p->waiting_time = 0;

                /* Release all allocated resources back to pools */
                pthread_mutex_lock(&sim->allocation_mutex);
                for (int r = 0; r < NUM_RESOURCES; r++) {
                    if (p->allocated[r] > 0) {
                        sem_custom_release(&sim->semaphores[r], p->allocated[r]);
                        p->allocated[r] = 0;
                    }
                }
                pthread_mutex_unlock(&sim->allocation_mutex);

                char details[256];
                snprintf(details, sizeof(details), "Discharged! Turnaround: %dt, Waiting: %dt.", p->turnaround_time, p->waiting_time);
                ipc_publish(sim, MSG_DONE, "OperatingRoom", "Discharge", p->pid, details);
            }
        }
    }

    /* 7. Update Waiting Time */
    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        if ((p->state == STATE_READY || p->state == STATE_WAITING) && p->arrival_time <= t) {
            p->waiting_time++;
            if (p->waiting_time >= sim->starvation_thresh) {
                p->is_starved = 1;
            }
        }
    }

    /* Advance clock */
    sim->clock++;

    /* 8. Check overall completion */
    bool all_done = true;
    for (int i = 0; i < sim->patient_count; i++) {
        if (sim->patients[i].state != STATE_COMPLETED) {
            all_done = false;
            break;
        }
    }
    if (all_done) {
        sim->is_completed = 1;
    }

    /* Update Banker safety check cache */
    banker_check_safety(sim, &sim->banker);
}

void herm_run_all(HospitalSimulator* sim, int max_ticks) {
    while (!sim->is_completed && sim->clock < max_ticks) {
        herm_step(sim);
    }
}
