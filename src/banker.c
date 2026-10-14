/**
 * Hospital Emergency Resource Manager (HERM)
 * Dijkstra's Banker's Algorithm for Deadlock Avoidance in C.
 */

#include "herm.h"

bool banker_check_safety(HospitalSimulator* sim, BankerState* state) {
    int work[NUM_RESOURCES];
    bool finish[MAX_PATIENTS];
    int active_count = 0;

    /* Initialize work vector from current available semaphore values */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        work[r] = sim->semaphores[r].value;
        state->available[r] = work[r];
    }

    state->safe_seq_len = 0;

    for (int i = 0; i < sim->patient_count; i++) {
        if (sim->patients[i].state == STATE_COMPLETED) {
            finish[i] = true;
        } else {
            finish[i] = false;
            active_count++;
        }
    }

    if (active_count == 0) {
        state->is_safe = 1;
        return true;
    }

    while (state->safe_seq_len < active_count) {
        bool found = false;
        for (int i = 0; i < sim->patient_count; i++) {
            if (!finish[i]) {
                bool can_satisfy = true;
                for (int r = 0; r < NUM_RESOURCES; r++) {
                    if (sim->patients[i].need[r] > work[r]) {
                        can_satisfy = false;
                        break;
                    }
                }

                if (can_satisfy) {
                    for (int r = 0; r < NUM_RESOURCES; r++) {
                        work[r] += sim->patients[i].allocated[r];
                    }
                    finish[i] = true;
                    state->safe_sequence[state->safe_seq_len++] = i;
                    found = true;
                    break;
                }
            }
        }

        if (!found) {
            state->is_safe = 0;
            return false;
        }
    }

    state->is_safe = 1;
    return true;
}

bool banker_evaluate_request(HospitalSimulator* sim, int patient_idx, const int request[NUM_RESOURCES]) {
    Patient* p = &sim->patients[patient_idx];

    /* Step 1: Check Request <= Need */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        if (request[r] > p->need[r]) {
            return false;
        }
    }

    /* Step 2: Check Request <= Available */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        if (request[r] > sim->semaphores[r].value) {
            return false;
        }
    }

    /* Step 3: Hypothetical State Allocation */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        sim->semaphores[r].value -= request[r];
        p->allocated[r] += request[r];
        p->need[r] -= request[r];
    }

    BankerState test_state;
    bool is_safe = banker_check_safety(sim, &test_state);

    /* Step 4: Revert Hypothetical Allocation */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        sim->semaphores[r].value += request[r];
        p->allocated[r] -= request[r];
        p->need[r] += request[r];
    }

    return is_safe;
}
