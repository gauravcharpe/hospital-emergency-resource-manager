/**
 * Hospital Emergency Resource Manager (HERM)
 * POSIX Counting Semaphores and Mutex Synchronization implementation in C.
 */

#include "herm.h"

void sem_custom_init(CountingSemaphore* sem, const char* name, int capacity) {
    strncpy(sem->name, name, sizeof(sem->name) - 1);
    sem->name[sizeof(sem->name) - 1] = '\0';
    sem->capacity = capacity;
    sem->value = capacity;
    pthread_mutex_init(&sem->lock, NULL);
    pthread_cond_init(&sem->cond, NULL);
}

void sem_custom_destroy(CountingSemaphore* sem) {
    pthread_mutex_destroy(&sem->lock);
    pthread_cond_destroy(&sem->cond);
}

void sem_custom_acquire(CountingSemaphore* sem, int units) {
    pthread_mutex_lock(&sem->lock);
    while (sem->value < units) {
        pthread_cond_wait(&sem->cond, &sem->lock);
    }
    sem->value -= units;
    pthread_mutex_unlock(&sem->lock);
}

void sem_custom_release(CountingSemaphore* sem, int units) {
    pthread_mutex_lock(&sem->lock);
    sem->value += units;
    if (sem->value > sem->capacity) {
        sem->value = sem->capacity;
    }
    pthread_cond_broadcast(&sem->cond);
    pthread_mutex_unlock(&sem->lock);
}

void sem_custom_reset(CountingSemaphore* sem, int capacity) {
    pthread_mutex_lock(&sem->lock);
    sem->capacity = capacity;
    sem->value = capacity;
    pthread_cond_broadcast(&sem->cond);
    pthread_mutex_unlock(&sem->lock);
}
