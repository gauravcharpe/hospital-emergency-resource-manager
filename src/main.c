/**
 * Hospital Emergency Resource Manager (HERM)
 * Interactive ANSI Terminal CLI & Main Program in C.
 * Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT
 */

#include "herm.h"

void print_banner(void) {
    printf("\033[1;36m");
    printf("========================================================================================\n");
    printf("   🏥  HOSPITAL EMERGENCY RESOURCE MANAGER (HERM) - C CORE ENGINE\n");
    printf("   Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi\n");
    printf("   School of Computer Science and Engineering, Vellore Institute of Technology\n");
    printf("========================================================================================\n");
    printf("\033[0m");
}

void print_state_tui(HospitalSimulator* sim) {
    printf("\n\033[1;34m--- [Clock Tick T=%d | Policy: %s | Banker's: %s] ---\033[0m\n",
           sim->clock, get_policy_name(sim->policy), sim->banker_enabled ? "ON (Safe)" : "OFF (Demo)");

    /* Resource availability bar */
    printf("Resources: ");
    for (int r = 0; r < NUM_RESOURCES; r++) {
        int avail = sim->semaphores[r].value;
        int cap = sim->semaphores[r].capacity;
        if (avail > 0) {
            printf("\033[1;32m%s: %d/%d\033[0m  ", get_resource_name(r), avail, cap);
        } else {
            printf("\033[1;31m%s: 0/%d (BUSY)\033[0m  ", get_resource_name(r), cap);
        }
    }
    printf("\n");

    /* Patient State Table */
    printf("+-------+----------------------+----------+-----------+-------+-------+------+------------+\n");
    printf("| PID   | Name                 | Priority | State     | Burst | Rem   | Wait | Starved?   |\n");
    printf("+-------+----------------------+----------+-----------+-------+-------+------+------------+\n");

    for (int i = 0; i < sim->patient_count; i++) {
        Patient* p = &sim->patients[i];
        const char* color = "\033[0m";
        if (p->base_priority == PRIO_CRITICAL) color = "\033[1;31m";
        else if (p->base_priority == PRIO_SERIOUS) color = "\033[1;33m";
        else if (p->base_priority == PRIO_MODERATE) color = "\033[1;34m";
        else if (p->base_priority == PRIO_STABLE) color = "\033[1;32m";

        printf("| %s%-5s\033[0m | %-20s | %sL%d (%-6s)\033[0m | %-9s | %-5d | %-5d | %-4d | %-10s |\n",
               color, p->pid, p->name, color, p->effective_priority, get_priority_name(p->effective_priority),
               get_state_name(p->state), p->burst_time, p->remaining_time, p->waiting_time,
               p->is_starved ? "\033[1;31mYES\033[0m" : "No");
    }
    printf("+-------+----------------------+----------+-----------+-------+-------+------+------------+\n");

    if (sim->wfg.has_deadlock) {
        printf("\033[1;31m⚠️  DEADLOCK DETECTED in WFG! Circular dependency among nodes. Preempting victim...\033[0m\n");
    }
}

int main(int argc, char* argv[]) {
    if (argc > 1 && strcmp(argv[1], "--benchmark") == 0) {
        herm_run_comparative_benchmarks();
        return 0;
    }

    print_banner();

    while (1) {
        printf("\nSelect Simulation Mode:\n");
        printf("  1. Interactive Step-by-Step Simulation (Preemptive Priority with Aging)\n");
        printf("  2. Run Full Comparative Benchmark Study (FCFS vs Priority vs Preemptive)\n");
        printf("  3. Deadlock Injection & Wait-For Graph Recovery Demo\n");
        printf("  4. High-Contention Surge Workload Test\n");
        printf("  5. Exit\n");
        printf("\nEnter choice [1-5]: ");

        int choice = 0;
        if (scanf("%d", &choice) != 1) {
            break;
        }

        if (choice == 1) {
            HospitalSimulator sim;
            herm_init(&sim, POLICY_PREEMPTIVE_AGING, true);

            printf("\nStarting step-by-step execution. Press Enter after each tick (or enter 'q' to stop):\n");
            char line[64];
            fgets(line, sizeof(line), stdin); /* consume leftover newline */

            while (!sim.is_completed) {
                herm_step(&sim);
                print_state_tui(&sim);

                printf("\nPress [Enter] for next tick (or 'r' to run to end, 'q' to quit): ");
                if (!fgets(line, sizeof(line), stdin)) break;
                if (line[0] == 'q' || line[0] == 'Q') break;
                if (line[0] == 'r' || line[0] == 'R') {
                    herm_run_all(&sim, 150);
                    print_state_tui(&sim);
                    break;
                }
            }
            printf("\n\033[1;32m✓ All patients successfully treated and discharged at T=%dt!\033[0m\n", sim.clock);
            herm_destroy(&sim);

        } else if (choice == 2) {
            herm_run_comparative_benchmarks();

        } else if (choice == 3) {
            printf("\n\033[1;33mInjecting cross-allocation deadlock with Banker's Avoidance switched OFF...\033[0m\n");
            HospitalSimulator sim;
            herm_init(&sim, POLICY_PREEMPTIVE_AGING, false);
            herm_trigger_deadlock(&sim);

            printf("Running clock tick to trigger WFG DFS cycle detection...\n");
            herm_step(&sim);
            print_state_tui(&sim);

            printf("\nDeadlocks Detected: %d | Deadlocks Recovered via Preemption: %d\n",
                   sim.deadlocks_detected, sim.deadlocks_recovered);
            herm_destroy(&sim);

        } else if (choice == 4) {
            HospitalSimulator sim;
            herm_init(&sim, POLICY_PREEMPTIVE_AGING, true);
            herm_load_surge_workload(&sim);
            herm_run_all(&sim, 200);
            print_state_tui(&sim);
            printf("\n\033[1;32mSurge completed in %d ticks!\033[0m\n", sim.clock);
            herm_destroy(&sim);

        } else if (choice == 5) {
            printf("Exiting HERM. Good luck with your Operating Systems review!\n");
            break;
        }
    }

    return 0;
}
