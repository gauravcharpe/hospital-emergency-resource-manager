/**
 * Hospital Emergency Resource Manager (HERM)
 * Comparative Benchmarking and JSON State Serialization in C.
 */

#include "herm.h"

void herm_export_json_state(HospitalSimulator* sim, char* buffer, size_t max_len) {
    size_t offset = 0;

    offset += snprintf(buffer + offset, max_len - offset,
        "{\"sim_time\": %d, \"policy\": \"%s\", \"banker_enabled\": %s, \"is_completed\": %s, ",
        sim->clock, get_policy_name(sim->policy),
        sim->banker_enabled ? "true" : "false",
        sim->is_completed ? "true" : "false");

    /* Resources */
    offset += snprintf(buffer + offset, max_len - offset, "\"resources\": {");
    int caps[NUM_RESOURCES] = {4, 3, 5, 8, 2};
    for (int r = 0; r < NUM_RESOURCES; r++) {
        int avail = sim->semaphores[r].value;
        int alloc = caps[r] - avail;
        float util = (caps[r] > 0) ? ((float)alloc / caps[r]) * 100.0f : 0.0f;
        offset += snprintf(buffer + offset, max_len - offset,
            "\"%s\": {\"total\": %d, \"available\": %d, \"allocated\": %d, \"utilization_percent\": %.1f}%s",
            get_resource_name(r), caps[r], avail, alloc, util,
            (r < NUM_RESOURCES - 1) ? ", " : "");
    }
    offset += snprintf(buffer + offset, max_len - offset, "}, ");

    /* Patients */
    offset += snprintf(buffer + offset, max_len - offset, "\"patients\": [");
    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        float prog = (p->burst_time > 0) ? ((float)(p->burst_time - p->remaining_time) / p->burst_time) * 100.0f : 100.0f;
        offset += snprintf(buffer + offset, max_len - offset,
            "{\"pid\": \"%s\", \"name\": \"%s\", \"arrival_time\": %d, \"base_priority\": %d, \"base_priority_name\": \"%s\", \"effective_priority\": %d, \"effective_priority_name\": \"%s\", \"burst_time\": %d, \"remaining_time\": %d, \"progress_percent\": %.1f, \"state\": \"%s\", \"waiting_time\": %d, \"turnaround_time\": %d, \"completion_time\": %d, \"preemption_count\": %d, \"is_starved\": %s, \"condition_description\": \"%s\", "
            "\"allocated_resources\": {\"ICU_Beds\": %d, \"Ventilators\": %d, \"Doctors\": %d, \"Nurses\": %d, \"Operation_Theatres\": %d}, "
            "\"max_resources\": {\"ICU_Beds\": %d, \"Ventilators\": %d, \"Doctors\": %d, \"Nurses\": %d, \"Operation_Theatres\": %d}, "
            "\"need_resources\": {\"ICU_Beds\": %d, \"Ventilators\": %d, \"Doctors\": %d, \"Nurses\": %d, \"Operation_Theatres\": %d}}%s",
            p->pid, p->name, p->arrival_time, p->base_priority, get_priority_name(p->base_priority),
            p->effective_priority, get_priority_name(p->effective_priority), p->burst_time, p->remaining_time,
            prog, get_state_name(p->state), p->waiting_time, p->turnaround_time, p->completion_time, p->preemption_count,
            p->is_starved ? "true" : "false", p->condition,
            p->allocated[0], p->allocated[1], p->allocated[2], p->allocated[3], p->allocated[4],
            p->max_claim[0], p->max_claim[1], p->max_claim[2], p->max_claim[3], p->max_claim[4],
            p->need[0], p->need[1], p->need[2], p->need[3], p->need[4],
            (i < sim->patient_count - 1) ? ", " : "");
    }
    offset += snprintf(buffer + offset, max_len - offset, "], ");

    /* Banker state */
    offset += snprintf(buffer + offset, max_len - offset,
        "\"banker_state\": {\"is_safe\": %s, \"safe_sequence\": [",
        sim->banker.is_safe ? "true" : "false");
    for (int k = 0; k < sim->banker.safe_seq_len; k++) {
        int p_idx = sim->banker.safe_sequence[k];
        offset += snprintf(buffer + offset, max_len - offset, "\"%s\"%s",
            sim->patients[p_idx].pid, (k < sim->banker.safe_seq_len - 1) ? ", " : "");
    }
    offset += snprintf(buffer + offset, max_len - offset, "]}, ");

    /* Wait-For Graph */
    offset += snprintf(buffer + offset, max_len - offset,
        "\"wait_for_graph\": {\"has_deadlock\": %s, \"nodes\": [",
        sim->wfg.has_deadlock ? "true" : "false");
    for (int i = 0; i < sim->patient_count; i++) {
        if (sim->patients[i].state != STATE_COMPLETED) {
            offset += snprintf(buffer + offset, max_len - offset, "\"%s\", ", sim->patients[i].pid);
        }
    }
    if (offset > 2 && buffer[offset - 2] == ',') offset -= 2; /* Remove trailing comma */

    offset += snprintf(buffer + offset, max_len - offset, "], \"edges\": [");
    bool first_edge = true;
    for (int i = 0; i < sim->patient_count; i++) {
        for (int j = 0; j < sim->patient_count; j++) {
            if (sim->wfg.adj[i][j]) {
                offset += snprintf(buffer + offset, max_len - offset,
                    "%s{\"from\": \"%s\", \"to\": \"%s\"}",
                    first_edge ? "" : ", ", sim->patients[i].pid, sim->patients[j].pid);
                first_edge = false;
            }
        }
    }
    offset += snprintf(buffer + offset, max_len - offset, "], \"detected_cycles\": [");
    if (sim->wfg.has_deadlock && sim->wfg.cycle_len > 0) {
        offset += snprintf(buffer + offset, max_len - offset, "[");
        for (int c = 0; c < sim->wfg.cycle_len; c++) {
            int p_idx = sim->wfg.cycle_nodes[c];
            offset += snprintf(buffer + offset, max_len - offset, "\"%s\"%s",
                sim->patients[p_idx].pid, (c < sim->wfg.cycle_len - 1) ? ", " : "");
        }
        offset += snprintf(buffer + offset, max_len - offset, "]");
    }
    offset += snprintf(buffer + offset, max_len - offset, "]}, ");

    /* Recent IPC Messages */
    offset += snprintf(buffer + offset, max_len - offset, "\"ipc_messages\": [");
    int start_m = (sim->message_count > 30) ? sim->message_count - 30 : 0;
    for (int m = start_m; m < sim->message_count; m++) {
        IPCMessage* msg = &sim->messages[m % MAX_LOG_MESSAGES];
        offset += snprintf(buffer + offset, max_len - offset,
            "{\"timestamp\": %d, \"msg_type\": \"%s\", \"patient_id\": \"%s\", \"payload\": {\"details\": \"%s\"}}%s",
            msg->timestamp, get_msg_type_name(msg->type), msg->pid, msg->details,
            (m < sim->message_count - 1) ? ", " : "");
    }
    offset += snprintf(buffer + offset, max_len - offset, "]}");
}

void herm_run_comparative_benchmarks(void) {
    printf("\n========================================================================================\n");
    printf("   HERM COMPARATIVE BENCHMARK EVALUATION (C ENGINE - POSIX THREADS & SYNCHRONIZATION)\n");
    printf("   Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT\n");
    printf("========================================================================================\n");

    int policies[4] = { POLICY_FCFS, POLICY_NON_PREEMPTIVE, POLICY_PREEMPTIVE_AGING, POLICY_PREEMPTIVE_AGING };
    bool banker_flags[4] = { true, true, true, false };
    const char* names[4] = {
        "First-Come, First-Served (FCFS)",
        "Non-Preemptive Priority",
        "Preemptive Priority with Aging",
        "Preemptive + Aging (No Banker's)"
    };

    printf("%-35s | %-10s | %-10s | %-10s | %-10s\n", "Policy", "Crit Wait", "Avg Wait", "Avg TAT", "Deadlocks");
    printf("------------------------------------+------------+------------+------------+------------\n");

    for (int p = 0; p < 4; p++) {
        HospitalSimulator sim;
        herm_init(&sim, policies[p], banker_flags[p]);
        herm_load_surge_workload(&sim);
        herm_run_all(&sim, 200);

        int comp_count = 0;
        int total_wait = 0, total_tat = 0;
        int crit_wait = 0, crit_count = 0;

        for (int i = 0; i < sim.patient_count; i++) {
            if (sim.patients[i].state == STATE_COMPLETED) {
                comp_count++;
                total_wait += sim.patients[i].waiting_time;
                total_tat += sim.patients[i].turnaround_time;
                if (sim.patients[i].base_priority == PRIO_CRITICAL) {
                    crit_wait += sim.patients[i].waiting_time;
                    crit_count++;
                }
            }
        }

        float avg_w = comp_count ? (float)total_wait / comp_count : 0.0f;
        float avg_t = comp_count ? (float)total_tat / comp_count : 0.0f;
        float crit_w = crit_count ? (float)crit_wait / crit_count : 0.0f;

        printf("%-35s | %-10.2fs | %-10.2fs | %-10.2fs | %-10d\n",
               names[p], crit_w, avg_w, avg_t, sim.deadlocks_detected);

        herm_destroy(&sim);
    }
    printf("========================================================================================\n\n");
}
