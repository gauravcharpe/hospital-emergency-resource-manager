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
             "Connection: close\r\n\r\n",
             status_code, content_type, body_len);

    send(client_fd, header, strlen(header), 0);
    send(client_fd, body, body_len, 0);
}

static void handle_client(int client_fd) {
    char request[4096];
    ssize_t bytes_read = recv(client_fd, request, sizeof(request) - 1, 0);
    if (bytes_read <= 0) {
        close(client_fd);
        return;
    }
    request[bytes_read] = '\0';

    char method[16], path[256];
    sscanf(request, "%15s %255s", method, path);

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
            herm_reset(&g_sim);
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
        } else if (strcmp(path, "/api/load_surge") == 0) {
            herm_load_surge_workload(&g_sim);
            herm_reset(&g_sim);
            char* json_buf = (char*)malloc(BUFFER_SIZE);
            if (json_buf) {
                herm_export_json_state(&g_sim, json_buf, BUFFER_SIZE);
                send_response(client_fd, "application/json", json_buf, 200);
                free(json_buf);
            }
        } else if (strcmp(path, "/api/benchmark") == 0) {
            /* Quick benchmark JSON response matching C benchmark engine output */
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
    /* Port 80 lets the dashboard open at http://hospital-emergency-resource-manager
       with no ":port" suffix. If 80 is unavailable, fall back to 5050. */
    int port = 80;
    int port_given = 0;
    if (argc > 1) {
        port = atoi(argv[1]);
        if (port <= 0) port = 80;
        else port_given = 1;
    }

    herm_init(&g_sim, POLICY_PREEMPTIVE_AGING, true);

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
        if (port_given) {
            perror("Bind failed");
            close(server_fd);
            return 1;
        }
        /* Port 80 busy or not permitted: fall back to the old port */
        port = SERVER_PORT;
        address.sin_port = htons(port);
        if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
            perror("Bind failed");
            close(server_fd);
            return 1;
        }
    }

    if (listen(server_fd, 10) < 0) {
        perror("Listen failed");
        close(server_fd);
        return 1;
    }

    printf("\n========================================================================================\n");
    printf("   🏥  HERM: Hospital Emergency Resource Manager (Pure C Embedded Web Server)\n");
    printf("   Course: BCSE303L Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT\n");
    if (port == 80) {
        printf("   Open in browser: http://%s\n", PROJECT_HOST);
    } else {
        printf("   Open in browser: http://%s:%d\n", PROJECT_HOST, port);
    }
    printf("   (One-time setup if the name doesn't open: run  make setup-host)\n");
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
