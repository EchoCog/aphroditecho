/*
 * DTESN Cognitive Computing Core Implementation
 * ===========================================
 * 
 * Core cognitive computing functionality for Deep Tree Echo State Networks
 * providing system initialization, cognitive system management, and
 * foundational cognitive operations with OEIS A000081 compliance.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/dtesn_cognitive.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>
#include <sys/time.h>
#include <math.h>
#include <float.h>

/* Internal constants */
#define DTESN_COGNITIVE_MEMORY_POOL_SIZE    (32 * 1024 * 1024)  /* 32MB */
#define DTESN_COGNITIVE_DEFAULT_TIMEOUT_MS  1000
#define DTESN_COGNITIVE_MAX_SYSTEMS         64

/* Global state */
static bool g_cognitive_initialized = false;
static pthread_mutex_t g_cognitive_lock = PTHREAD_MUTEX_INITIALIZER;
static uint32_t g_next_system_id = 1;

/* OEIS A000081 sequence for validation */
static const uint32_t g_oeis_a000081[] = DTESN_COGNITIVE_A000081_SEQUENCE;

/* System registry */
static dtesn_cognitive_system_t *g_systems[DTESN_COGNITIVE_MAX_SYSTEMS] = {NULL};
static uint32_t g_num_systems = 0;

/* Forward declarations */
static uint64_t get_time_ns(void);
static int validate_system_pointer(const dtesn_cognitive_system_t *system);
static int init_memory_subsystem(dtesn_cognitive_system_t *system);
static int init_attention_subsystem(dtesn_cognitive_system_t *system);
static int cleanup_memory_subsystem(dtesn_cognitive_system_t *system);
static int cleanup_attention_subsystem(dtesn_cognitive_system_t *system);

/**
 * Get current time in nanoseconds
 */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Validate system pointer and initialization
 */
static int validate_system_pointer(const dtesn_cognitive_system_t *system) {
    if (!system) {
        return -EINVAL;
    }
    
    if (!system->initialized) {
        return -ENODEV;
    }
    
    return 0;
}

/**
 * Initialize memory subsystem for cognitive system
 */
static int init_memory_subsystem(dtesn_cognitive_system_t *system) {
    int result;
    
    /* Initialize memory linked list */
    system->memory_head = NULL;
    system->memory_node_count = 0;
    
    /* Initialize memory mutex */
    result = pthread_mutex_init(&system->memory_lock, NULL);
    if (result != 0) {
        return -result;
    }
    
    return 0;
}

/**
 * Initialize attention subsystem for cognitive system
 */
static int init_attention_subsystem(dtesn_cognitive_system_t *system) {
    int result;
    
    /* Allocate attention channels based on OEIS A000081 */
    uint32_t num_channels = g_oeis_a000081[3]; /* Use 4 channels as default */
    system->attention_channels = calloc(num_channels, sizeof(dtesn_cognitive_attention_channel_t));
    if (!system->attention_channels) {
        return -ENOMEM;
    }
    
    system->num_attention_channels = num_channels;
    system->active_channel_id = 0;
    
    /* Initialize each attention channel */
    for (uint32_t i = 0; i < num_channels; i++) {
        dtesn_cognitive_attention_channel_t *channel = &system->attention_channels[i];
        channel->channel_id = i;
        channel->type = DTESN_COGNITIVE_ATTENTION_BOTTOM_UP;
        channel->weight = 1.0f / num_channels;
        channel->focus_vector = NULL;
        channel->focus_size = 0;
        channel->switch_time_ns = get_time_ns();
        channel->active = (i == 0); /* First channel active by default */
    }
    
    /* Initialize attention mutex */
    result = pthread_mutex_init(&system->attention_lock, NULL);
    if (result != 0) {
        free(system->attention_channels);
        return -result;
    }
    
    return 0;
}

/**
 * Cleanup memory subsystem
 */
static int cleanup_memory_subsystem(dtesn_cognitive_system_t *system) {
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    dtesn_cognitive_memory_node_t *next;
    
    /* Free all memory nodes */
    while (current) {
        next = current->next;
        if (current->data) {
            free(current->data);
        }
        free(current);
        current = next;
    }
    
    system->memory_head = NULL;
    system->memory_node_count = 0;
    
    /* Destroy mutex */
    pthread_mutex_destroy(&system->memory_lock);
    
    return 0;
}

/**
 * Cleanup attention subsystem
 */
static int cleanup_attention_subsystem(dtesn_cognitive_system_t *system) {
    if (system->attention_channels) {
        /* Free focus vectors */
        for (uint32_t i = 0; i < system->num_attention_channels; i++) {
            if (system->attention_channels[i].focus_vector) {
                free(system->attention_channels[i].focus_vector);
            }
        }
        
        free(system->attention_channels);
        system->attention_channels = NULL;
    }
    
    system->num_attention_channels = 0;
    
    /* Destroy mutex */
    pthread_mutex_destroy(&system->attention_lock);
    
    return 0;
}

/**
 * Initialize cognitive computing subsystem
 */
int dtesn_cognitive_init(void) {
    pthread_mutex_lock(&g_cognitive_lock);
    
    if (g_cognitive_initialized) {
        pthread_mutex_unlock(&g_cognitive_lock);
        return 0;
    }
    
    /* Initialize system registry */
    memset(g_systems, 0, sizeof(g_systems));
    g_num_systems = 0;
    g_next_system_id = 1;
    
    g_cognitive_initialized = true;
    
    pthread_mutex_unlock(&g_cognitive_lock);
    
    printf("DTESN Cognitive Computing initialized successfully\n");
    return 0;
}

/**
 * Cleanup cognitive computing subsystem
 */
int dtesn_cognitive_cleanup(void) {
    pthread_mutex_lock(&g_cognitive_lock);
    
    if (!g_cognitive_initialized) {
        pthread_mutex_unlock(&g_cognitive_lock);
        return 0;
    }
    
    /* Cleanup all active systems */
    for (uint32_t i = 0; i < DTESN_COGNITIVE_MAX_SYSTEMS; i++) {
        if (g_systems[i]) {
            dtesn_cognitive_system_destroy(g_systems[i]);
            g_systems[i] = NULL;
        }
    }
    
    g_num_systems = 0;
    g_cognitive_initialized = false;
    
    pthread_mutex_unlock(&g_cognitive_lock);
    
    printf("DTESN Cognitive Computing cleanup completed\n");
    return 0;
}

/**
 * Create a new cognitive system
 */
dtesn_cognitive_system_t *dtesn_cognitive_system_create(const char *name,
                                                       dtesn_esn_reservoir_t *reservoir) {
    int result;
    dtesn_cognitive_system_t *system;
    uint32_t system_slot = UINT32_MAX;
    
    if (!name || !reservoir) {
        return NULL;
    }
    
    if (!g_cognitive_initialized) {
        dtesn_cognitive_init();
    }
    
    /* Allocate system structure */
    system = calloc(1, sizeof(dtesn_cognitive_system_t));
    if (!system) {
        return NULL;
    }
    
    pthread_mutex_lock(&g_cognitive_lock);
    
    /* Find available system slot */
    for (uint32_t i = 0; i < DTESN_COGNITIVE_MAX_SYSTEMS; i++) {
        if (!g_systems[i]) {
            system_slot = i;
            break;
        }
    }
    
    if (system_slot == UINT32_MAX) {
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    /* Initialize basic system properties */
    system->system_id = g_next_system_id++;
    strncpy(system->name, name, sizeof(system->name) - 1);
    system->name[sizeof(system->name) - 1] = '\0';
    system->reservoir = reservoir;
    
    /* Initialize system mutex */
    result = pthread_mutex_init(&system->system_lock, NULL);
    if (result != 0) {
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    /* Initialize memory subsystem */
    result = init_memory_subsystem(system);
    if (result != 0) {
        pthread_mutex_destroy(&system->system_lock);
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    /* Initialize attention subsystem */
    result = init_attention_subsystem(system);
    if (result != 0) {
        cleanup_memory_subsystem(system);
        pthread_mutex_destroy(&system->system_lock);
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    /* Initialize multimodal fusion - use OEIS A000081 for modality count */
    system->num_modalities = g_oeis_a000081[2]; /* Use 2 modalities as default */
    system->modalities = calloc(system->num_modalities, sizeof(dtesn_cognitive_modality_data_t));
    if (!system->modalities) {
        cleanup_attention_subsystem(system);
        cleanup_memory_subsystem(system);
        pthread_mutex_destroy(&system->system_lock);
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    system->fusion_type = DTESN_COGNITIVE_FUSION_EARLY;
    system->fused_representation = NULL;
    system->fused_size = 0;
    
    /* Initialize distributed processing */
    system->num_nodes = 0;
    system->nodes = NULL;
    result = pthread_mutex_init(&system->distributed_lock, NULL);
    if (result != 0) {
        free(system->modalities);
        cleanup_attention_subsystem(system);
        cleanup_memory_subsystem(system);
        pthread_mutex_destroy(&system->system_lock);
        pthread_mutex_unlock(&g_cognitive_lock);
        free(system);
        return NULL;
    }
    
    /* Initialize performance counters */
    system->total_learning_iterations = 0;
    system->total_learning_time_ns = 0;
    system->total_consolidations = 0;
    system->total_consolidation_time_ns = 0;
    system->total_attention_switches = 0;
    system->total_attention_switch_time_ns = 0;
    system->total_state_saves = 0;
    system->total_state_save_time_ns = 0;
    
    /* Mark system as initialized */
    system->initialized = true;
    
    /* Register system */
    g_systems[system_slot] = system;
    g_num_systems++;
    
    pthread_mutex_unlock(&g_cognitive_lock);
    
    printf("Cognitive system '%s' created successfully (ID: %u)\n", 
           system->name, system->system_id);
    
    return system;
}

/**
 * Destroy a cognitive system
 */
int dtesn_cognitive_system_destroy(dtesn_cognitive_system_t *system) {
    uint32_t system_slot = UINT32_MAX;
    
    if (!system) {
        return -EINVAL;
    }
    
    pthread_mutex_lock(&g_cognitive_lock);
    
    /* Find system in registry */
    for (uint32_t i = 0; i < DTESN_COGNITIVE_MAX_SYSTEMS; i++) {
        if (g_systems[i] == system) {
            system_slot = i;
            break;
        }
    }
    
    if (system_slot != UINT32_MAX) {
        g_systems[system_slot] = NULL;
        g_num_systems--;
    }
    
    pthread_mutex_unlock(&g_cognitive_lock);
    
    /* Lock system for cleanup */
    pthread_mutex_lock(&system->system_lock);
    
    printf("Destroying cognitive system '%s' (ID: %u)\n", 
           system->name, system->system_id);
    
    /* Mark as uninitialized */
    system->initialized = false;
    
    /* Cleanup subsystems */
    cleanup_memory_subsystem(system);
    cleanup_attention_subsystem(system);
    
    /* Cleanup multimodal fusion */
    if (system->modalities) {
        for (uint32_t i = 0; i < system->num_modalities; i++) {
            if (system->modalities[i].data) {
                free(system->modalities[i].data);
            }
        }
        free(system->modalities);
    }
    
    if (system->fused_representation) {
        free(system->fused_representation);
    }
    
    /* Cleanup distributed processing */
    if (system->nodes) {
        free(system->nodes);
    }
    pthread_mutex_destroy(&system->distributed_lock);
    
    pthread_mutex_unlock(&system->system_lock);
    
    /* Destroy system mutex */
    pthread_mutex_destroy(&system->system_lock);
    
    /* Free system structure */
    free(system);
    
    return 0;
}

/**
 * Validate OEIS A000081 compliance
 */
bool dtesn_cognitive_validate_a000081(const dtesn_cognitive_system_t *system) {
    if (validate_system_pointer(system) != 0) {
        return false;
    }
    
    /* Check that attention channels follow A000081 enumeration */
    if (system->num_attention_channels > sizeof(g_oeis_a000081) / sizeof(g_oeis_a000081[0])) {
        return false;
    }
    
    /* Verify attention channel count matches OEIS sequence */
    bool found_match = false;
    for (size_t i = 0; i < sizeof(g_oeis_a000081) / sizeof(g_oeis_a000081[0]); i++) {
        if (system->num_attention_channels == g_oeis_a000081[i]) {
            found_match = true;
            break;
        }
    }
    
    if (!found_match) {
        return false;
    }
    
    /* Check modality count compliance */
    found_match = false;
    for (size_t i = 0; i < sizeof(g_oeis_a000081) / sizeof(g_oeis_a000081[0]); i++) {
        if (system->num_modalities == g_oeis_a000081[i]) {
            found_match = true;
            break;
        }
    }
    
    return found_match;
}

/**
 * Get performance statistics
 */
int dtesn_cognitive_get_performance_stats(const dtesn_cognitive_system_t *system,
                                         void *stats_buffer,
                                         size_t buffer_size) {
    int result = validate_system_pointer(system);
    if (result != 0) {
        return result;
    }
    
    if (!stats_buffer || buffer_size < sizeof(dtesn_cognitive_system_t)) {
        return -EINVAL;
    }
    
    /* Copy performance statistics */
    memcpy(stats_buffer, system, sizeof(dtesn_cognitive_system_t));
    
    return 0;
}

/**
 * Reset performance statistics
 */
int dtesn_cognitive_reset_stats(dtesn_cognitive_system_t *system) {
    int result = validate_system_pointer(system);
    if (result != 0) {
        return result;
    }
    
    pthread_mutex_lock(&system->system_lock);
    
    /* Reset all performance counters */
    system->total_learning_iterations = 0;
    system->total_learning_time_ns = 0;
    system->total_consolidations = 0;
    system->total_consolidation_time_ns = 0;
    system->total_attention_switches = 0;
    system->total_attention_switch_time_ns = 0;
    system->total_state_saves = 0;
    system->total_state_save_time_ns = 0;
    
    pthread_mutex_unlock(&system->system_lock);
    
    return 0;
}