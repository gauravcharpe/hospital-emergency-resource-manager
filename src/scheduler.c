/**
 * Hospital Emergency Resource Manager (HERM)
 * Process Scheduler: Preemptive Priority with Aging, Non-Preemptive, and FCFS in C.
 */

#include "herm.h"

void scheduler_apply_aging(HospitalSimulator* sim) {
    if (sim->policy != POLICY_PREEMPTIVE_AGING) return;

    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        if (p->state == STATE_READY) {
            p->ready_ticks++;
            if (p->waiting_time >= sim->starvation_thresh) {
                p->is_starved = 1;
            }

            if (p->base_priority > sim->aging_cap) {
                int intervals = p->ready_ticks / sim->aging_interval;
                int target_prio = p->base_priority - intervals;
                if (target_prio < sim->aging_cap) {
                    target_prio = sim->aging_cap;
                }

                if (target_prio < p->effective_priority) {
                    int old_prio = p->effective_priority;
                    p->effective_priority = target_prio;

                    char details[256];
                    snprintf(details, sizeof(details), "Priority boosted from Level %d to Level %d after %d ready ticks.",
                             old_prio, target_prio, p->ready_ticks);
                    ipc_publish(sim, MSG_AGING, "AgingEngine", "Scheduler", p->pid, details);
                }
            }
        }
    }
}

int scheduler_select_next(HospitalSimulator* sim) {
    int best_idx = -1;

    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        if (p->state != STATE_READY && p->state != STATE_WAITING) continue;

        if (best_idx == -1) {
            best_idx = i;
            continue;
        }

        Patient* best = &sim->patients[best_idx];

        if (sim->policy == POLICY_FCFS) {
            if (p->arrival_time < best->arrival_time) {
                best_idx = i;
            }
        } else if (sim->policy == POLICY_NON_PREEMPTIVE) {
            if (p->base_priority < best->base_priority) {
                best_idx = i;
            } else if (p->base_priority == best->base_priority && p->arrival_time < best->arrival_time) {
                best_idx = i;
            }
        } else { /* POLICY_PREEMPTIVE_AGING */
            if (p->effective_priority < best->effective_priority) {
                best_idx = i;
            } else if (p->effective_priority == best->effective_priority && p->arrival_time < best->arrival_time) {
                best_idx = i;
            }
        }
    }
    return best_idx;
}

bool scheduler_should_preempt(HospitalSimulator* sim, int running_idx, int candidate_idx) {
    if (sim->policy != POLICY_PREEMPTIVE_AGING) return false;

    Patient* running = &sim->patients[running_idx];
    Patient* candidate = &sim->patients[candidate_idx];

    /* Case 1: Candidate has strictly higher priority (e.g. Critical=1 preempts Serious=2) */
    if (candidate->effective_priority < running->effective_priority) {
        return true;
    }

    /* Case 2: Round Robin quantum expired for Level 4 */
    if (running->effective_priority == 4 && running->quantum_remaining <= 0) {
        if (candidate->effective_priority == 4 && candidate_idx != running_idx) {
            return true;
        }
    }

    return false;
}
