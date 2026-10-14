/**
 * Hospital Emergency Resource Manager (HERM)
 * Thread-Safe Inter-Process Communication (IPC) Message Bus in C.
 */

#include "herm.h"

void ipc_publish(HospitalSimulator* sim, MessageType type, const char* sender, const char* recipient, const char* pid, const char* details) {
    pthread_mutex_lock(&sim->msg_lock);

    int idx = sim->message_count % MAX_LOG_MESSAGES;
    IPCMessage* msg = &sim->messages[idx];

    msg->timestamp = sim->clock;
    msg->type = type;
    strncpy(msg->sender, sender ? sender : "System", sizeof(msg->sender) - 1);
    msg->sender[sizeof(msg->sender) - 1] = '\0';

    strncpy(msg->recipient, recipient ? recipient : "Scheduler", sizeof(msg->recipient) - 1);
    msg->recipient[sizeof(msg->recipient) - 1] = '\0';

    strncpy(msg->pid, pid ? pid : "", sizeof(msg->pid) - 1);
    msg->pid[sizeof(msg->pid) - 1] = '\0';

    strncpy(msg->details, details ? details : "", sizeof(msg->details) - 1);
    msg->details[sizeof(msg->details) - 1] = '\0';

    sim->message_count++;

    pthread_mutex_unlock(&sim->msg_lock);
}
