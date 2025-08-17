/*
 * DTESN Memory Consolidation Implementation
 * ========================================
 * 
 * Memory consolidation mechanisms for cognitive state persistence and recovery
 * including immediate, delayed, replay-based, and adaptive consolidation
 * strategies with ≤100ms performance target compliance.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/dtesn_cognitive.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <math.h>
#include <float.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

/* Internal constants */
#define DTESN_CONSOLIDATION_MEMORY_THRESHOLD    0.7f    /* Memory usage threshold */
#define DTESN_CONSOLIDATION_IMPORTANCE_DECAY    0.95f   /* Importance decay factor */
#define DTESN_CONSOLIDATION_REPLAY_RATIO        0.1f    /* Replay sample ratio */
#define DTESN_CONSOLIDATION_MAX_CHUNKS          1024    /* Maximum memory chunks */
#define DTESN_CONSOLIDATION_CHUNK_SIZE          4096    /* Chunk size in bytes */

/* Consolidation data structures */
typedef struct consolidation_chunk {
    uint32_t chunk_id;
    float importance_score;
    uint32_t access_count;
    uint64_t timestamp_ns;
    void *data;
    size_t size;
    struct consolidation_chunk *next;
} consolidation_chunk_t;

/* Forward declarations */
static uint64_t get_time_ns(void);
static int validate_system(const dtesn_cognitive_system_t *system);
static float compute_importance_score(const dtesn_cognitive_memory_node_t *node);
static int perform_immediate_consolidation(dtesn_cognitive_system_t *system);
static int perform_delayed_consolidation(dtesn_cognitive_system_t *system);
static int perform_replay_consolidation(dtesn_cognitive_system_t *system);
static int perform_adaptive_consolidation(dtesn_cognitive_system_t *system);
static int consolidate_memory_node(dtesn_cognitive_system_t *system, 
                                  dtesn_cognitive_memory_node_t *node);
static int save_memory_to_storage(const dtesn_cognitive_memory_node_t *node, 
                                 const char *storage_path);
static int load_memory_from_storage(dtesn_cognitive_memory_node_t *node, 
                                   const char *storage_path);
static int cleanup_working_memory(dtesn_cognitive_system_t *system, float threshold);
static int replay_important_memories(dtesn_cognitive_system_t *system, uint32_t replay_count);

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
 * Validate system pointer and state
 */
static int validate_system(const dtesn_cognitive_system_t *system) {
    if (!system) {
        return -EINVAL;
    }
    
    if (!system->initialized) {
        return -ENODEV;
    }
    
    return 0;
}

/**
 * Compute importance score for memory node
 */
static float compute_importance_score(const dtesn_cognitive_memory_node_t *node) {
    if (!node) {
        return 0.0f;
    }
    
    /* Factors contributing to importance:
     * 1. Activation level (current relevance)
     * 2. Access frequency (historical relevance)
     * 3. Temporal recency (how recent the memory is)
     * 4. Persistence flag (explicit importance marking)
     */
    
    float activation_factor = node->activation;
    float frequency_factor = log1pf((float)node->access_count) / log1pf(100.0f); /* Normalized */
    
    /* Temporal decay based on age */
    uint64_t current_time = get_time_ns();
    uint64_t age_ns = current_time - node->timestamp_ns;
    float age_hours = age_ns / (3600.0f * 1000000000.0f);
    float recency_factor = expf(-age_hours / 24.0f); /* Decay over 24 hours */
    
    float persistence_factor = node->persistent ? 2.0f : 1.0f;
    
    /* Weighted combination of factors */
    float importance = (0.4f * activation_factor + 
                       0.3f * frequency_factor + 
                       0.2f * recency_factor + 
                       0.1f) * persistence_factor;
    
    return fmaxf(0.0f, fminf(1.0f, importance));
}

/**
 * Perform immediate consolidation
 */
static int perform_immediate_consolidation(dtesn_cognitive_system_t *system) {
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    uint32_t consolidated_count = 0;
    
    /* Consolidate all memory nodes immediately */
    while (current) {
        int result = consolidate_memory_node(system, current);
        if (result == 0) {
            consolidated_count++;
        }
        current = current->next;
    }
    
    printf("Immediate consolidation: %u memory nodes processed\n", consolidated_count);
    return 0;
}

/**
 * Perform delayed consolidation
 */
static int perform_delayed_consolidation(dtesn_cognitive_system_t *system) {
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    uint32_t consolidated_count = 0;
    uint64_t current_time = get_time_ns();
    const uint64_t delay_threshold = 3600ULL * 1000000000ULL; /* 1 hour delay */
    
    /* Only consolidate memories older than threshold */
    while (current) {
        if ((current_time - current->timestamp_ns) > delay_threshold) {
            int result = consolidate_memory_node(system, current);
            if (result == 0) {
                consolidated_count++;
            }
        }
        current = current->next;
    }
    
    printf("Delayed consolidation: %u memory nodes processed\n", consolidated_count);
    return 0;
}

/**
 * Perform replay-based consolidation
 */
static int perform_replay_consolidation(dtesn_cognitive_system_t *system) {
    /* Count total memory nodes */
    uint32_t total_nodes = system->memory_node_count;
    uint32_t replay_count = (uint32_t)(total_nodes * DTESN_CONSOLIDATION_REPLAY_RATIO);
    
    if (replay_count == 0 && total_nodes > 0) {
        replay_count = 1; /* Ensure at least one replay */
    }
    
    /* Replay important memories to reinforce them */
    int result = replay_important_memories(system, replay_count);
    if (result != 0) {
        return result;
    }
    
    /* Then perform standard consolidation */
    return perform_immediate_consolidation(system);
}

/**
 * Perform adaptive consolidation
 */
static int perform_adaptive_consolidation(dtesn_cognitive_system_t *system) {
    /* Compute current memory usage */
    float memory_utilization = (float)system->memory_node_count / DTESN_COGNITIVE_MAX_MEMORY_NODES;
    
    /* Adaptive strategy based on memory pressure */
    if (memory_utilization > DTESN_CONSOLIDATION_MEMORY_THRESHOLD) {
        /* High memory usage - aggressive consolidation */
        printf("High memory usage (%.1f%%) - performing aggressive consolidation\n", 
               memory_utilization * 100.0f);
        
        /* First, cleanup low-importance memories */
        int result = cleanup_working_memory(system, 0.3f);
        if (result != 0) {
            return result;
        }
        
        /* Then consolidate remaining memories */
        return perform_immediate_consolidation(system);
    } else if (memory_utilization > 0.5f) {
        /* Medium memory usage - selective consolidation */
        return perform_delayed_consolidation(system);
    } else {
        /* Low memory usage - replay-based consolidation */
        return perform_replay_consolidation(system);
    }
}

/**
 * Consolidate individual memory node
 */
static int consolidate_memory_node(dtesn_cognitive_system_t *system, 
                                  dtesn_cognitive_memory_node_t *node) {
    if (!node || !node->data) {
        return -EINVAL;
    }
    
    /* Create storage path based on system and node identifiers */
    char storage_path[256];
    snprintf(storage_path, sizeof(storage_path), 
             "/tmp/dtesn_memory_system_%u_node_%u.dat", 
             system->system_id, node->node_id);
    
    /* Save memory node to persistent storage */
    int result = save_memory_to_storage(node, storage_path);
    if (result != 0) {
        return result;
    }
    
    /* Update node metadata */
    node->access_count++;
    node->timestamp_ns = get_time_ns();
    
    return 0;
}

/**
 * Save memory node to storage
 */
static int save_memory_to_storage(const dtesn_cognitive_memory_node_t *node, 
                                 const char *storage_path) {
    int fd;
    ssize_t bytes_written;
    
    fd = open(storage_path, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) {
        return -errno;
    }
    
    /* Write node metadata */
    bytes_written = write(fd, node, sizeof(dtesn_cognitive_memory_node_t));
    if (bytes_written != sizeof(dtesn_cognitive_memory_node_t)) {
        close(fd);
        return -EIO;
    }
    
    /* Write node data */
    size_t data_size = node->data_size * sizeof(float);
    bytes_written = write(fd, node->data, data_size);
    if (bytes_written != (ssize_t)data_size) {
        close(fd);
        return -EIO;
    }
    
    /* Ensure data is written to disk */
    fsync(fd);
    close(fd);
    
    return 0;
}

/**
 * Load memory node from storage
 */
static int load_memory_from_storage(dtesn_cognitive_memory_node_t *node, 
                                   const char *storage_path) {
    int fd;
    ssize_t bytes_read;
    struct stat file_stats;
    
    fd = open(storage_path, O_RDONLY);
    if (fd < 0) {
        return -errno;
    }
    
    /* Get file size */
    if (fstat(fd, &file_stats) != 0) {
        close(fd);
        return -errno;
    }
    
    /* Read node metadata */
    bytes_read = read(fd, node, sizeof(dtesn_cognitive_memory_node_t));
    if (bytes_read != sizeof(dtesn_cognitive_memory_node_t)) {
        close(fd);
        return -EIO;
    }
    
    /* Allocate and read node data */
    size_t data_size = node->data_size * sizeof(float);
    node->data = malloc(data_size);
    if (!node->data) {
        close(fd);
        return -ENOMEM;
    }
    
    bytes_read = read(fd, node->data, data_size);
    if (bytes_read != (ssize_t)data_size) {
        free(node->data);
        node->data = NULL;
        close(fd);
        return -EIO;
    }
    
    close(fd);
    return 0;
}

/**
 * Cleanup working memory based on importance threshold
 */
static int cleanup_working_memory(dtesn_cognitive_system_t *system, float threshold) {
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    dtesn_cognitive_memory_node_t *prev = NULL;
    uint32_t removed_count = 0;
    
    while (current) {
        float importance = compute_importance_score(current);
        
        if (importance < threshold && !current->persistent) {
            /* Remove low-importance, non-persistent memory node */
            dtesn_cognitive_memory_node_t *to_remove = current;
            
            if (prev) {
                prev->next = current->next;
            } else {
                system->memory_head = current->next;
            }
            
            current = current->next;
            
            /* Free memory */
            if (to_remove->data) {
                free(to_remove->data);
            }
            free(to_remove);
            
            system->memory_node_count--;
            removed_count++;
        } else {
            prev = current;
            current = current->next;
        }
    }
    
    printf("Cleaned up %u low-importance memory nodes (threshold: %.2f)\n", 
           removed_count, threshold);
    return 0;
}

/**
 * Replay important memories for reinforcement
 */
static int replay_important_memories(dtesn_cognitive_system_t *system, uint32_t replay_count) {
    if (replay_count == 0 || !system->memory_head) {
        return 0;
    }
    
    /* Build array of memory nodes with importance scores */
    dtesn_cognitive_memory_node_t **nodes = malloc(system->memory_node_count * sizeof(void*));
    float *importance_scores = malloc(system->memory_node_count * sizeof(float));
    
    if (!nodes || !importance_scores) {
        free(nodes);
        free(importance_scores);
        return -ENOMEM;
    }
    
    /* Collect nodes and compute importance scores */
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    uint32_t node_count = 0;
    
    while (current && node_count < system->memory_node_count) {
        nodes[node_count] = current;
        importance_scores[node_count] = compute_importance_score(current);
        current = current->next;
        node_count++;
    }
    
    /* Simple selection of most important nodes (could be optimized) */
    for (uint32_t i = 0; i < replay_count && i < node_count; i++) {
        uint32_t max_idx = i;
        
        /* Find most important remaining node */
        for (uint32_t j = i + 1; j < node_count; j++) {
            if (importance_scores[j] > importance_scores[max_idx]) {
                max_idx = j;
            }
        }
        
        /* Swap to front */
        if (max_idx != i) {
            dtesn_cognitive_memory_node_t *temp_node = nodes[i];
            float temp_score = importance_scores[i];
            nodes[i] = nodes[max_idx];
            importance_scores[i] = importance_scores[max_idx];
            nodes[max_idx] = temp_node;
            importance_scores[max_idx] = temp_score;
        }
        
        /* Replay (reinforce) this memory */
        nodes[i]->activation = fminf(1.0f, nodes[i]->activation * 1.1f);
        nodes[i]->access_count++;
        nodes[i]->timestamp_ns = get_time_ns();
    }
    
    free(nodes);
    free(importance_scores);
    
    printf("Replayed %u important memories\n", 
           replay_count < node_count ? replay_count : node_count);
    return 0;
}

/**
 * Consolidate working memory to long-term storage
 */
int dtesn_memory_consolidate(dtesn_cognitive_system_t *system,
                            dtesn_cognitive_consolidate_type_t consolidate_type) {
    int result;
    uint64_t start_time, end_time;
    
    result = validate_system(system);
    if (result != 0) {
        return result;
    }
    
    start_time = get_time_ns();
    
    pthread_mutex_lock(&system->memory_lock);
    
    /* Apply selected consolidation strategy */
    switch (consolidate_type) {
        case DTESN_COGNITIVE_CONSOLIDATE_IMMEDIATE:
            result = perform_immediate_consolidation(system);
            break;
        case DTESN_COGNITIVE_CONSOLIDATE_DELAYED:
            result = perform_delayed_consolidation(system);
            break;
        case DTESN_COGNITIVE_CONSOLIDATE_REPLAY:
            result = perform_replay_consolidation(system);
            break;
        case DTESN_COGNITIVE_CONSOLIDATE_ADAPTIVE:
            result = perform_adaptive_consolidation(system);
            break;
        default:
            result = -EINVAL;
            break;
    }
    
    end_time = get_time_ns();
    
    /* Update performance statistics */
    if (result == 0) {
        system->total_consolidations++;
        system->total_consolidation_time_ns += (end_time - start_time);
        
        /* Check performance target: ≤100ms */
        uint64_t consolidation_time_us = (end_time - start_time) / 1000;
        if (consolidation_time_us > DTESN_COGNITIVE_MEMORY_CONSOLIDATION_US) {
            printf("Warning: Consolidation took %lu μs (target: ≤%u μs)\n",
                   (unsigned long)consolidation_time_us, 
                   DTESN_COGNITIVE_MEMORY_CONSOLIDATION_US);
        }
    }
    
    pthread_mutex_unlock(&system->memory_lock);
    
    if (result == 0) {
        printf("Memory consolidation completed in %.2f ms\n",
               (end_time - start_time) / 1000000.0);
    }
    
    return result;
}

/**
 * Selective memory consolidation
 */
int dtesn_memory_consolidate_selective(dtesn_cognitive_system_t *system,
                                      float threshold,
                                      dtesn_cognitive_consolidate_type_t consolidate_type) {
    int result;
    uint64_t start_time, end_time;
    uint32_t consolidated_count = 0;
    
    result = validate_system(system);
    if (result != 0) {
        return result;
    }
    
    if (threshold < 0.0f || threshold > 1.0f) {
        return -EINVAL;
    }
    
    start_time = get_time_ns();
    
    pthread_mutex_lock(&system->memory_lock);
    
    /* Process only memories above importance threshold */
    dtesn_cognitive_memory_node_t *current = system->memory_head;
    
    while (current) {
        float importance = compute_importance_score(current);
        
        if (importance >= threshold) {
            result = consolidate_memory_node(system, current);
            if (result == 0) {
                consolidated_count++;
            }
        }
        
        current = current->next;
    }
    
    end_time = get_time_ns();
    
    /* Update performance statistics */
    system->total_consolidations++;
    system->total_consolidation_time_ns += (end_time - start_time);
    
    pthread_mutex_unlock(&system->memory_lock);
    
    printf("Selective consolidation: %u nodes above threshold %.2f (%.2f ms)\n",
           consolidated_count, threshold, (end_time - start_time) / 1000000.0);
    
    return 0;
}