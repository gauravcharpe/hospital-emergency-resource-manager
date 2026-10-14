/**
 * Hospital Emergency Resource Manager (HERM)
 * Models implementation: Workloads, string helpers, and PCB initialization.
 */

#include "herm.h"

const char* get_priority_name(int prio) {
    switch (prio) {
        case PRIO_CRITICAL: return "Critical";
        case PRIO_SERIOUS:  return "Serious";
        case PRIO_MODERATE: return "Moderate";
        case PRIO_STABLE:   return "Stable";
        default:            return "Unknown";
    }
}

const char* get_state_name(int state) {
    switch (state) {
        case STATE_NEW:       return "NEW";
        case STATE_READY:     return "READY";
        case STATE_RUNNING:   return "RUNNING";
        case STATE_WAITING:   return "WAITING";
        case STATE_COMPLETED: return "COMPLETED";
        default:              return "UNKNOWN";
    }
}

const char* get_resource_name(int res_idx) {
    switch (res_idx) {
        case RES_BEDS:   return "ICU_Beds";
        case RES_VENTS:  return "Ventilators";
        case RES_DOCS:   return "Doctors";
        case RES_NURSES: return "Nurses";
        case RES_OTS:    return "Operation_Theatres";
        default:         return "Resource";
    }
}

const char* get_policy_name(int policy) {
    switch (policy) {
        case POLICY_PREEMPTIVE_AGING: return "Preemptive Priority with Aging";
        case POLICY_NON_PREEMPTIVE:   return "Non-Preemptive Priority";
        case POLICY_FCFS:             return "First-Come, First-Served (FCFS)";
        default:                      return "Unknown Policy";
    }
}

const char* get_msg_type_name(MessageType type) {
    switch (type) {
        case MSG_ARRIVAL:            return "ARRIVAL";
        case MSG_REQUEST:            return "REQUEST";
        case MSG_GRANT:              return "GRANT";
        case MSG_DENY:               return "DENY";
        case MSG_RELEASE:            return "RELEASE";
        case MSG_PREEMPT:            return "PREEMPT";
        case MSG_AGING:              return "AGING";
        case MSG_DEADLOCK_DETECTED:  return "DEADLOCK_DETECTED";
        case MSG_DEADLOCK_RECOVERED: return "DEADLOCK_RECOVERED";
        case MSG_DONE:               return "DONE";
        default:                     return "EVENT";
    }
}

void herm_load_standard_workload(HospitalSimulator* sim) {
    sim->patient_count = 0;

    Patient p1 = { "P1", "John Doe", "Controlled bleeding", 0, PRIO_MODERATE, PRIO_MODERATE, 8, 8, STATE_NEW, {1, 0, 1, 2, 0}, {0}, {1, 0, 1, 2, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p2 = { "P2", "Sarah Smith", "Respiratory distress", 1, PRIO_SERIOUS, PRIO_SERIOUS, 6, 6, STATE_NEW, {1, 1, 1, 0, 0}, {0}, {1, 1, 1, 0, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p3 = { "P3", "David Clark", "Routine sprain observation", 2, PRIO_STABLE, PRIO_STABLE, 4, 4, STATE_NEW, {0, 0, 1, 1, 0}, {0}, {0, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p4 = { "P4", "Emma Watson", "Cardiac arrest (Critical)", 3, PRIO_CRITICAL, PRIO_CRITICAL, 5, 5, STATE_NEW, {1, 1, 2, 2, 1}, {0}, {1, 1, 2, 2, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p5 = { "P5", "Robert Miller", "High fever, dehydration", 4, PRIO_MODERATE, PRIO_MODERATE, 7, 7, STATE_NEW, {1, 0, 1, 1, 0}, {0}, {1, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p6 = { "P6", "Lisa Ray", "Aortic aneurysm (Critical)", 6, PRIO_CRITICAL, PRIO_CRITICAL, 4, 4, STATE_NEW, {1, 1, 1, 0, 1}, {0}, {1, 1, 1, 0, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p7 = { "P7", "Alex Turner", "Stable laceration sutures", 8, PRIO_STABLE, PRIO_STABLE, 5, 5, STATE_NEW, {0, 0, 1, 1, 0}, {0}, {0, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient p8 = { "P8", "Elena Gilbert", "Acute asthma exacerbation", 9, PRIO_SERIOUS, PRIO_SERIOUS, 5, 5, STATE_NEW, {1, 1, 1, 1, 0}, {0}, {1, 1, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };

    sim->patients[sim->patient_count++] = p1;
    sim->patients[sim->patient_count++] = p2;
    sim->patients[sim->patient_count++] = p3;
    sim->patients[sim->patient_count++] = p4;
    sim->patients[sim->patient_count++] = p5;
    sim->patients[sim->patient_count++] = p6;
    sim->patients[sim->patient_count++] = p7;
    sim->patients[sim->patient_count++] = p8;
}

void herm_load_surge_workload(HospitalSimulator* sim) {
    sim->patient_count = 0;

    Patient s1  = { "P1", "Alpha", "Severe sepsis", 0, PRIO_STABLE, PRIO_STABLE, 10, 10, STATE_NEW, {1, 1, 1, 1, 1}, {0}, {1, 1, 1, 1, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s2  = { "P2", "Beta", "Moderate trauma", 1, PRIO_MODERATE, PRIO_MODERATE, 8, 8, STATE_NEW, {1, 1, 1, 1, 1}, {0}, {1, 1, 1, 1, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s3  = { "P3", "Gamma", "Critical cardiac arrest", 1, PRIO_CRITICAL, PRIO_CRITICAL, 6, 6, STATE_NEW, {1, 1, 2, 2, 1}, {0}, {1, 1, 2, 2, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s4  = { "P4", "Delta", "Ankle sprain", 2, PRIO_STABLE, PRIO_STABLE, 12, 12, STATE_NEW, {1, 0, 1, 1, 0}, {0}, {1, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s5  = { "P5", "Epsilon", "Ruptured aortic trauma", 2, PRIO_CRITICAL, PRIO_CRITICAL, 5, 5, STATE_NEW, {1, 1, 2, 2, 1}, {0}, {1, 1, 2, 2, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s6  = { "P6", "Zeta", "Serious head injury", 3, PRIO_SERIOUS, PRIO_SERIOUS, 7, 7, STATE_NEW, {1, 1, 1, 1, 0}, {0}, {1, 1, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s7  = { "P7", "Eta", "Routine observation", 4, PRIO_STABLE, PRIO_STABLE, 9, 9, STATE_NEW, {0, 0, 1, 1, 0}, {0}, {0, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s8  = { "P8", "Theta", "Severe gunshot trauma", 5, PRIO_CRITICAL, PRIO_CRITICAL, 4, 4, STATE_NEW, {1, 1, 1, 1, 1}, {0}, {1, 1, 1, 1, 1}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s9  = { "P9", "Iota", "Acute appendicitis", 6, PRIO_MODERATE, PRIO_MODERATE, 6, 6, STATE_NEW, {1, 0, 1, 1, 0}, {0}, {1, 0, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };
    Patient s10 = { "P10", "Kappa", "Pulmonary embolism", 7, PRIO_SERIOUS, PRIO_SERIOUS, 5, 5, STATE_NEW, {1, 1, 1, 1, 0}, {0}, {1, 1, 1, 1, 0}, 0, 0, 0, 0, 0, 0, 0, 0 };

    sim->patients[sim->patient_count++] = s1;
    sim->patients[sim->patient_count++] = s2;
    sim->patients[sim->patient_count++] = s3;
    sim->patients[sim->patient_count++] = s4;
    sim->patients[sim->patient_count++] = s5;
    sim->patients[sim->patient_count++] = s6;
    sim->patients[sim->patient_count++] = s7;
    sim->patients[sim->patient_count++] = s8;
    sim->patients[sim->patient_count++] = s9;
    sim->patients[sim->patient_count++] = s10;
}
