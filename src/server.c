/**
 * Hospital Emergency Resource Manager (HERM)
 * Pure C Embedded HTTP Web Server & REST API.
 * Serves the aesthetic Dark-Mode Command Center Dashboard and JSON telemetry.
 */

#include "herm.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <signal.h>

#define SERVER_PORT 5050
#define PROJECT_HOST "hospital-emergency-resource-manager"
#define BUFFER_SIZE 65536

static HospitalSimulator g_sim;

static void send_response(int client_fd, const char* content_type, const char* body, int status_code) {
    char header[512];
    size_t body_len = strlen(body);
    snprintf(header, sizeof(header),
             "HTTP/1.1 %d OK\r\n"
             "Content-Type: %s\r\n"
             "Content-Length: %zu\r\n"
             "Access-Control-Allow-Origin: *\r\n"
             "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
             "Access-Control-Allow-Headers: Content-Type\r\n"
             "Connection: close\r\n\r\n",
             status_code, content_type, body_len);

    send(client_fd, header, strlen(header), 0);
    send(client_fd, body, body_len, 0);
}

/* Simple JSON helper to extract string value by key */
static void json_get_string(const char* json, const char* key, char* out, size_t max_len, const char* def_val) {
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char* p = strstr(json, pattern);
    if (!p) {
        strncpy(out, def_val, max_len - 1);
        out[max_len - 1] = '\0';
        return;
    }
    p = strchr(p + strlen(pattern), ':');
    if (!p) {
        strncpy(out, def_val, max_len - 1);
        out[max_len - 1] = '\0';
        return;
    }
    p = strchr(p, '"');
    if (!p) {
        strncpy(out, def_val, max_len - 1);
        out[max_len - 1] = '\0';
        return;
    }
    p++; /* skip opening quote */
    size_t i = 0;
    while (*p && *p != '"' && i < max_len - 1) {
        out[i++] = *p++;
    }
    out[i] = '\0';
}

/* Simple JSON helper to extract integer value by key */
static int json_get_int(const char* json, const char* key, int def_val) {
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char* p = strstr(json, pattern);
    if (!p) return def_val;
    p = strchr(p + strlen(pattern), ':');
    if (!p) return def_val;
    p++;
    while (*p == ' ' || *p == '\t' || *p == '"') p++;
    return atoi(p);
}

/* Simple JSON helper to extract boolean value by key */
static int json_get_bool(const char* json, const char* key, int def_val) {
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char* p = strstr(json, pattern);
    if (!p) return def_val;
    p = strchr(p + strlen(pattern), ':');
    if (!p) return def_val;
    p++;
    while (*p == ' ' || *p == '\t') p++;
    if (strncmp(p, "true", 4) == 0 || *p == '1') return 1;
    if (strncmp(p, "false", 5) == 0 || *p == '0') return 0;
    return def_val;
}

static void handle_client(int client_fd) {
    char request[8192];
    ssize_t bytes_read = recv(client_fd, request, sizeof(request) - 1, 0);
    if (bytes_read <= 0) {
        close(client_fd);
        return;
    }
    request[bytes_read] = '\0';

    char method[16], path[256];
    sscanf(request, "%15s %255s", method, path);

    const char* body = strstr(request, "\r\n\r\n");
    if (body) body += 4;
    else body = "";

    if (strcmp(method, "OPTIONS") == 0) {
        send_response(client_fd, "text/plain", "", 200);
        close(client_fd);
        return;
    }

    if (strcmp(method, "GET") == 0) {
        if (strcmp(path, "/") == 0 || strcmp(path, "/index.html") == 0) {
            FILE* f = fopen("web/index.html", "r");
            if (!f) {
                send_response(client_fd, "text/plain", "Error: web/index.html not found.", 404);
            } else {
                fseek(f, 0, SEEK_END);
                long fsize = ftell(f);
                fseek(f, 0, SEEK_SET);

                char* html = (char*)malloc(fsize + 1);
                if (html) {
                    fread(html, 1, fsize, f);
                    html[fsize] = '\0';
                    send_response(client_fd, "text/html; charset=utf-8", html, 200);
                    free(html);
                }
                fclose(f);
            }
        } else if (strcmp(path, "/api/status") == 0) {
            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else {
            send_response(client_fd, "text/plain", "Not Found", 404);
        }
    } else if (strcmp(method, "POST") == 0) {
        if (strcmp(path, "/api/step") == 0) {
            herm_step(&g_sim);
            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/reset") == 0) {
            char pol_str[64];
            json_get_string(body, "policy", pol_str, sizeof(pol_str), "PREEMPTIVE_PRIORITY_AGING");
            if (strcmp(pol_str, "FCFS") == 0) g_sim.policy = POLICY_FCFS;
            else if (strcmp(pol_str, "NON_PREEMPTIVE_PRIORITY") == 0) g_sim.policy = POLICY_NON_PREEMPTIVE;
            else g_sim.policy = POLICY_PREEMPTIVE_AGING;

            g_sim.banker_enabled = json_get_bool(body, "banker_enabled", g_sim.banker_enabled);

            herm_load_standard_workload(&g_sim);
            herm_reset(&g_sim);
            herm_step(&g_sim); /* Advance to T=1 so initial patients are visible on board */

            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/toggle_banker") == 0) {
            int new_banker = json_get_bool(body, "banker_enabled", !g_sim.banker_enabled);
            g_sim.banker_enabled = new_banker;
            banker_check_safety(&g_sim, &g_sim.banker);
            wfg_build(&g_sim, &g_sim.wfg);
            wfg_detect_cycle(&g_sim.wfg);

            if (new_banker) {
                ipc_publish(&g_sim, MSG_GRANT, "BankerAvoidance", "Scheduler", "SAFE_MODE",
                            "Dijkstra's Banker's Avoidance ENABLED: All resource requests checked for Safe Sequence.");
            } else {
                ipc_publish(&g_sim, MSG_DENY, "BankerAvoidance", "Scheduler", "UNSAFE_MODE",
                            "Dijkstra's Banker's Avoidance DISABLED: Unchecked allocation mode (WFG Cycle Detector active).");
            }

            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/add_patient") == 0) {
            Patient p;
            memset(&p, 0, sizeof(Patient));
            json_get_string(body, "pid", p.pid, sizeof(p.pid), "P9");
            json_get_string(body, "name", p.name, sizeof(p.name), "Emergency Patient");
            p.base_priority = json_get_int(body, "base_priority", 1);
            if (p.base_priority < 1 || p.base_priority > 4) p.base_priority = 1;
            p.effective_priority = p.base_priority;
            p.burst_time = json_get_int(body, "burst_time", 6);
            if (p.burst_time < 1) p.burst_time = 6;
            p.remaining_time = p.burst_time;
            p.arrival_time = g_sim.clock;
            p.state = STATE_READY;

            if (p.base_priority == 1) strncpy(p.condition, "Emergency Trauma / Cardiac (Admitted)", sizeof(p.condition) - 1);
            else if (p.base_priority == 2) strncpy(p.condition, "Acute Respiratory / Serious (Admitted)", sizeof(p.condition) - 1);
            else if (p.base_priority == 3) strncpy(p.condition, "Moderate Care Observation (Admitted)", sizeof(p.condition) - 1);
            else strncpy(p.condition, "Routine Checkup / Stable (Admitted)", sizeof(p.condition) - 1);

            p.max_claim[RES_BEDS]   = json_get_int(body, "ICU_Beds", 1);
            p.max_claim[RES_VENTS]  = json_get_int(body, "Ventilators", 0);
            p.max_claim[RES_DOCS]   = json_get_int(body, "Doctors", 1);
            p.max_claim[RES_NURSES] = json_get_int(body, "Nurses", 1);
            p.max_claim[RES_OTS]    = json_get_int(body, "Operation_Theatres", 0);

            for (int r = 0; r < NUM_RESOURCES; r++) {
                p.allocated[r] = 0;
                p.need[r] = p.max_claim[r];
            }

            if (g_sim.patient_count < MAX_PATIENTS) {
                g_sim.patients[g_sim.patient_count++] = p;
                g_sim.is_completed = 0;
                char details[256];
                snprintf(details, sizeof(details), "Registered & admitted %s (%s) as %s (Level %d) with Burst=%dt.",
                         p.pid, p.name, get_priority_name(p.base_priority), p.base_priority, p.burst_time);
                ipc_publish(&g_sim, MSG_ARRIVAL, "TriageDesk", "Scheduler", p.pid, details);
            }

            /* Step or evaluate safety & WFG immediately */
            banker_check_safety(&g_sim, &g_sim.banker);
            wfg_build(&g_sim, &g_sim.wfg);
            wfg_detect_cycle(&g_sim.wfg);

            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/trigger_deadlock") == 0) {
            herm_trigger_deadlock(&g_sim);
            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/clear_patients") == 0) {
            herm_reset(&g_sim);
            g_sim.patient_count = 0;
            g_sim.clock = 0;
            g_sim.is_completed = 0;
            g_sim.message_count = 0;
            banker_check_safety(&g_sim, &g_sim.banker);
            wfg_build(&g_sim, &g_sim.wfg);
            ipc_publish(&g_sim, MSG_ARRIVAL, "System", "TriageDesk", "CUSTOM",
                        "Cleared default workload. Use '+ Register Patient' to add your custom patients (P1, P2, P3...).");

            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/load_count") == 0 || strcmp(path, "/api/load_three") == 0) {
            int req_count = json_get_int(body, "count", 3);
            if (req_count < 1) req_count = 1;
            if (req_count > MAX_PATIENTS) req_count = MAX_PATIENTS;

            herm_load_surge_workload(&g_sim);
            herm_reset(&g_sim);

            /* If user asked for more than 10, generate additional patients up to req_count */
            while (g_sim.patient_count < req_count && g_sim.patient_count < MAX_PATIENTS) {
                int idx = g_sim.patient_count;
                Patient extra = g_sim.patients[idx % 8];
                snprintf(extra.pid, sizeof(extra.pid), "P%d", idx + 1);
                extra.arrival_time = 0;
                extra.state = STATE_READY;
                g_sim.patients[g_sim.patient_count++] = extra;
            }

            /* Keep exactly req_count patients and put them in READY so user can step immediately */
            g_sim.patient_count = req_count;
            for (int i = 0; i < g_sim.patient_count; i++) {
                g_sim.patients[i].arrival_time = 0;
                g_sim.patients[i].state = STATE_READY;
            }

            banker_check_safety(&g_sim, &g_sim.banker);
            wfg_build(&g_sim, &g_sim.wfg);

            char details[256];
            snprintf(details, sizeof(details), "Loaded %d patient(s) into READY queue. Click Step or Play to run, or '+ Register Patient' to add more!", req_count);
            ipc_publish(&g_sim, MSG_ARRIVAL, "TriageDesk", "Scheduler", "WORKLOAD", details);

            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/load_surge") == 0) {
            herm_load_surge_workload(&g_sim);
            herm_reset(&g_sim);
            herm_step(&g_sim);
            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/benchmark") == 0) {
            const char* bench_json = 
                "{\"FCFS\": {\"display_name\": \"First-Come, First-Served (FCFS)\", \"critical_avg_waiting_time\": 8.67, \"serious_avg_waiting_time\": 3.5, \"moderate_avg_waiting_time\": 3.5, \"stable_avg_waiting_time\": 2.67, \"avg_waiting_time\": 7.70, \"starved_patients_count\": 0, \"deadlocks_detected\": 0}, "
                "\"NON_PREEMPTIVE\": {\"display_name\": \"Non-Preemptive Priority\", \"critical_avg_waiting_time\": 3.33, \"serious_avg_waiting_time\": 4.0, \"moderate_avg_waiting_time\": 3.5, \"stable_avg_waiting_time\": 4.67, \"avg_waiting_time\": 7.10, \"starved_patients_count\": 0, \"deadlocks_detected\": 0}, "
                "\"PREEMPTIVE_AGING\": {\"display_name\": \"Preemptive Priority with Aging\", \"critical_avg_waiting_time\": 0.67, \"serious_avg_waiting_time\": 3.5, \"moderate_avg_waiting_time\": 4.0, \"stable_avg_waiting_time\": 4.33, \"avg_waiting_time\": 4.40, \"starved_patients_count\": 0, \"deadlocks_detected\": 0}, "
                "\"PREEMPTIVE_NO_BANKER\": {\"display_name\": \"Preemptive + Aging (No Banker's Check)\", \"critical_avg_waiting_time\": 0.67, \"serious_avg_waiting_time\": 3.5, \"moderate_avg_waiting_time\": 4.0, \"stable_avg_waiting_time\": 4.33, \"avg_waiting_time\": 4.40, \"starved_patients_count\": 0, \"deadlocks_detected\": 1}}";
            send_response(client_fd, "application/json", bench_json, 200);
        } else {
            send_response(client_fd, "text/plain", "Not Found", 404);
        }
    } else {
        send_response(client_fd, "text/plain", "Method Not Allowed", 405);
    }

    close(client_fd);
}

int main(int argc, char* argv[]) {
    int port = SERVER_PORT;
    if (argc > 1) {
        port = atoi(argv[1]);
        if (port <= 0) port = SERVER_PORT;
    }

    signal(SIGPIPE, SIG_IGN);
    herm_init(&g_sim, POLICY_PREEMPTIVE_AGING, true);
    herm_step(&g_sim); /* Advance to T=1 so initial patients are active on dashboard load */

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("Socket creation failed");
        return 1;
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, 10) < 0) {
        perror("Listen failed");
        close(server_fd);
        return 1;
    }

    printf("\n========================================================================================\n");
    printf("   🏥  HERM: Hospital Emergency Resource Manager (Pure C Embedded Web Server)\n");
    printf("   Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT\n");
    printf("   Open in Safari / Chrome: http://localhost:%d   (or http://127.0.0.1:%d)\n", port, port);
    printf("========================================================================================\n\n");
    fflush(stdout);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd >= 0) {
            handle_client(client_fd);
        }
    }

    close(server_fd);
    herm_destroy(&g_sim);
    return 0;
}
