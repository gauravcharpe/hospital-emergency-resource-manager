/**
 * Hospital Emergency Resource Manager (HERM)
 * Wait-For Graph (WFG) Construction, DFS Cycle Detection, and Preemption Recovery in C.
 */

#include "herm.h"

void wfg_build(HospitalSimulator* sim, WaitForGraph* wfg) {
    memset(wfg->adj, 0, sizeof(wfg->adj));
    wfg->num_nodes = sim->patient_count;
    wfg->has_deadlock = 0;
    wfg->cycle_len = 0;

    for (int i = 0; i < sim->patient_count; i++) {
        if (sim->patients[i].state != STATE_WAITING) continue;

        for (int r = 0; r < NUM_RESOURCES; r++) {
            int needed_units = sim->patients[i].need[r];
            /* If the resource is in deficit */
            if (needed_units > sim->semaphores[r].value) {
                for (int j = 0; j < sim->patient_count; j++) {
                    if (i != j && sim->patients[j].state != STATE_COMPLETED && sim->patients[j].allocated[r] > 0) {
                        wfg->adj[i][j] = 1; /* Directed dependency edge i -> j */
                    }
                }
            }
        }
    }
}

static bool dfs_cycle(WaitForGraph* wfg, int u, bool visited[], bool rec_stack[], int path[], int path_len) {
    visited[u] = true;
    rec_stack[u] = true;
    path[path_len] = u;

    for (int v = 0; v < wfg->num_nodes; v++) {
        if (wfg->adj[u][v]) {
            if (!visited[v]) {
                if (dfs_cycle(wfg, v, visited, rec_stack, path, path_len + 1)) {
                    return true;
                }
            } else if (rec_stack[v]) {
                /* Cycle found: extract cycle nodes */
                int start_idx = 0;
                for (int k = 0; k <= path_len; k++) {
                    if (path[k] == v) {
                        start_idx = k;
                        break;
                    }
                }
                wfg->cycle_len = 0;
                for (int k = start_idx; k <= path_len; k++) {
                    wfg->cycle_nodes[wfg->cycle_len++] = path[k];
                }
                wfg->has_deadlock = 1;
                return true;
            }
        }
    }

    rec_stack[u] = false;
    return false;
}

bool wfg_detect_cycle(WaitForGraph* wfg) {
    bool visited[MAX_PATIENTS] = { false };
    bool rec_stack[MAX_PATIENTS] = { false };
    int path[MAX_PATIENTS];

    for (int i = 0; i < wfg->num_nodes; i++) {
        if (!visited[i]) {
            if (dfs_cycle(wfg, i, visited, rec_stack, path, 0)) {
                return true;
            }
        }
    }
    return false;
}

int wfg_select_victim(HospitalSimulator* sim, const int cycle_nodes[], int cycle_len) {
    if (cycle_len == 0) return -1;

    int best_victim_idx = cycle_nodes[0];
    Patient* best = &sim->patients[best_victim_idx];

    for (int k = 1; k < cycle_len; k++) {
        int candidate_idx = cycle_nodes[k];
        Patient* cand = &sim->patients[candidate_idx];

        /* Criterion 1: Lowest priority (highest numerical level: 4 > 3 > 2 > 1) */
        if (cand->effective_priority > best->effective_priority) {
            best_victim_idx = candidate_idx;
            best = cand;
        } else if (cand->effective_priority == best->effective_priority) {
            /* Criterion 2: Least progress completed */
            int cand_prog = cand->burst_time - cand->remaining_time;
            int best_prog = best->burst_time - best->remaining_time;
            if (cand_prog < best_prog) {
                best_victim_idx = candidate_idx;
                best = cand;
            } else if (cand_prog == best_prog) {
                /* Criterion 3: Later arrival */
                if (cand->arrival_time > best->arrival_time) {
                    best_victim_idx = candidate_idx;
                    best = cand;
                }
            }
        }
    }
    return best_victim_idx;
}

void wfg_recover_deadlock(HospitalSimulator* sim, WaitForGraph* wfg) {
    if (!wfg->has_deadlock || wfg->cycle_len == 0) return;

    int victim_idx = wfg_select_victim(sim, wfg->cycle_nodes, wfg->cycle_len);
    if (victim_idx < 0) return;

    Patient* victim = &sim->patients[victim_idx];

    /* Reclaim all allocated resources from victim */
    for (int r = 0; r < NUM_RESOURCES; r++) {
        if (victim->allocated[r] > 0) {
            sem_custom_release(&sim->semaphores[r], victim->allocated[r]);
            victim->need[r] += victim->allocated[r];
            victim->allocated[r] = 0;
        }
    }

    victim->state = STATE_READY;
    victim->preemption_count++;
    sim->deadlocks_recovered++;

    char details[256];
    snprintf(details, sizeof(details), "Circular wait resolved. Preempted lowest-urgency patient %s (Level %d).",
             victim->pid, victim->effective_priority);
    ipc_publish(sim, MSG_DEADLOCK_RECOVERED, "RecoveryEngine", "Scheduler", victim->pid, details);
}
