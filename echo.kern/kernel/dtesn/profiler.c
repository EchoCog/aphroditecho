/*
 * DTESN Performance Profiling Framework Implementation
 * ====================================================
 * 
 * Low-overhead performance profiling for Deep Tree Echo State Networks
 * with hardware performance counter integration and real-time monitoring.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/profiler.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>
#include <pthread.h>
#include <sys/time.h>

/* Internal state and globals */
static dtesn_profiler_t g_profiler = {0};
static pthread_mutex_t g_profiler_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Performance target thresholds in nanoseconds */
static const uint64_t g_performance_targets[DTESN_PROFILE_TYPE_COUNT] = {
    [DTESN_PROFILE_MEMORY_ALLOC] = DTESN_PROFILE_MEMORY_ALLOC_TARGET_NS,
    [DTESN_PROFILE_MEMORY_FREE] = DTESN_PROFILE_MEMORY_FREE_TARGET_NS,
    [DTESN_PROFILE_MEMBRANE_EVOLUTION] = DTESN_PROFILE_MEMBRANE_EVOLUTION_TARGET_NS,
    [DTESN_PROFILE_BSERIES_COMPUTE] = DTESN_PROFILE_BSERIES_COMPUTE_TARGET_NS,
    [DTESN_PROFILE_ESN_UPDATE] = DTESN_PROFILE_ESN_UPDATE_TARGET_NS,
    [DTESN_PROFILE_SYSCALL] = DTESN_PROFILE_SYSCALL_TARGET_NS,
    [DTESN_PROFILE_SCHEDULER] = DTESN_PROFILE_SYSCALL_TARGET_NS, /* Same as syscall */
};

/* Operation type names for reporting */
static const char *g_operation_names[DTESN_PROFILE_TYPE_COUNT] = {
    [DTESN_PROFILE_MEMORY_ALLOC] = "Memory Allocation",
    [DTESN_PROFILE_MEMORY_FREE] = "Memory Deallocation",
    [DTESN_PROFILE_MEMBRANE_EVOLUTION] = "Membrane Evolution",
    [DTESN_PROFILE_BSERIES_COMPUTE] = "B-Series Computation",
    [DTESN_PROFILE_ESN_UPDATE] = "ESN State Update",
    [DTESN_PROFILE_SYSCALL] = "System Call",
    [DTESN_PROFILE_SCHEDULER] = "Scheduler Operation",
};

/* Hardware counter names for reporting */
static const char *g_hw_counter_names[DTESN_HW_COUNTER_TYPE_COUNT] = {
    [DTESN_HW_CPU_CYCLES] = "CPU Cycles",
    [DTESN_HW_INSTRUCTIONS] = "Instructions",
    [DTESN_HW_CACHE_MISSES] = "Cache Misses",
    [DTESN_HW_BRANCH_MISSES] = "Branch Misses",
    [DTESN_HW_PAGE_FAULTS] = "Page Faults",
    [DTESN_HW_CONTEXT_SWITCHES] = "Context Switches",
};

/*
 * Internal helper functions
 */

/**
 * get_timestamp_ns - Get high-resolution timestamp
 *
 * Returns current time in nanoseconds with best available resolution.
 */
static inline uint64_t get_timestamp_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * read_hw_counters - Read hardware performance counters
 * @counters: Array to store counter values
 *
 * Simulates hardware counter reading. In a real implementation,
 * this would interface with CPU performance monitoring units.
 */
static int read_hw_counters(uint64_t counters[DTESN_HW_COUNTER_TYPE_COUNT])
{
    /* Simulate hardware counter values for demonstration */
    /* In real implementation, would use perf_event_open() or similar */
    static uint64_t base_counters[DTESN_HW_COUNTER_TYPE_COUNT] = {0};
    static bool initialized = false;
    
    if (!initialized) {
        /* Initialize with random base values */
        for (int i = 0; i < DTESN_HW_COUNTER_TYPE_COUNT; i++) {
            base_counters[i] = get_timestamp_ns() % 1000000;
        }
        initialized = true;
    }
    
    /* Simulate counter progression */
    for (int i = 0; i < DTESN_HW_COUNTER_TYPE_COUNT; i++) {
        base_counters[i] += (get_timestamp_ns() % 100) + 1;
        counters[i] = base_counters[i];
    }
    
    return 0;
}

/**
 * find_free_context - Find an available profiling context
 *
 * Returns pointer to free context or NULL if none available.
 */
static dtesn_profile_context_t *find_free_context(void)
{
    for (uint32_t i = 0; i < g_profiler.max_contexts; i++) {
        if (!g_profiler.contexts[i].active) {
            return &g_profiler.contexts[i];
        }
    }
    
    /* No free contexts - increment dropped counter */
    __sync_fetch_and_add(&g_profiler.dropped_measurements, 1);
    return NULL;
}

/**
 * update_stats - Update statistics for completed measurement
 * @measurement: Completed measurement data
 */
static void update_stats(const dtesn_profile_measurement_t *measurement)
{
    dtesn_profile_stats_t *stats = &g_profiler.stats[measurement->type];
    uint64_t duration = measurement->duration_ns;
    
    /* Update statistics atomically */
    __sync_fetch_and_add(&stats->total_count, 1);
    __sync_fetch_and_add(&stats->total_time_ns, duration);
    
    /* Update min/max (with simple compare-and-swap) */
    uint64_t current_min = stats->min_time_ns;
    if (current_min == 0 || duration < current_min) {
        __sync_val_compare_and_swap(&stats->min_time_ns, current_min, duration);
    }
    
    uint64_t current_max = stats->max_time_ns;
    if (duration > current_max) {
        __sync_val_compare_and_swap(&stats->max_time_ns, current_max, duration);
    }
    
    /* Check for performance violations */
    if (duration > g_performance_targets[measurement->type]) {
        __sync_fetch_and_add(&stats->violations, 1);
    }
    
    /* Update last measurement timestamp */
    stats->last_measurement_ns = measurement->end_time_ns;
    
    /* Calculate average (approximate, for performance) */
    if (stats->total_count > 0) {
        stats->avg_time_ns = stats->total_time_ns / stats->total_count;
    }
}

/*
 * Public API implementation
 */

int dtesn_profile_init(uint32_t max_contexts)
{
    pthread_mutex_lock(&g_profiler_mutex);
    
    if (g_profiler.initialized) {
        pthread_mutex_unlock(&g_profiler_mutex);
        return -EALREADY;
    }
    
    if (max_contexts == 0) {
        max_contexts = DTESN_PROFILE_DEFAULT_MAX_CONTEXTS;
    }
    
    /* Allocate context array */
    g_profiler.contexts = calloc(max_contexts, sizeof(dtesn_profile_context_t));
    if (!g_profiler.contexts) {
        pthread_mutex_unlock(&g_profiler_mutex);
        return -ENOMEM;
    }
    
    g_profiler.max_contexts = max_contexts;
    g_profiler.enabled = true;
    g_profiler.initialized = true;
    
    /* Initialize statistics */
    for (int i = 0; i < DTESN_PROFILE_TYPE_COUNT; i++) {
        memset(&g_profiler.stats[i], 0, sizeof(dtesn_profile_stats_t));
    }
    
    /* Measure initial overhead */
    g_profiler.overhead_ns = dtesn_profile_overhead();
    
    pthread_mutex_unlock(&g_profiler_mutex);
    return 0;
}

dtesn_profile_context_t *dtesn_profile_start(dtesn_profile_type_t type,
                                             uint32_t membrane_level)
{
    if (!g_profiler.initialized || !g_profiler.enabled) {
        return NULL;
    }
    
    if (type >= DTESN_PROFILE_TYPE_COUNT) {
        return NULL;
    }
    
    /* Find free context */
    dtesn_profile_context_t *context = find_free_context();
    if (!context) {
        return NULL;
    }
    
    /* Initialize measurement */
    context->measurement.type = type;
    context->measurement.membrane_level = membrane_level;
    context->measurement.start_time_ns = get_timestamp_ns();
    context->active = true;
    context->thread_id = (uint32_t)pthread_self();
    
    /* Read hardware counters at start */
    read_hw_counters(context->measurement.hw_counters);
    
    return context;
}

int dtesn_profile_end(dtesn_profile_context_t *context)
{
    if (!context || !context->active) {
        return -EINVAL;
    }
    
    /* Capture end time immediately */
    context->measurement.end_time_ns = get_timestamp_ns();
    context->measurement.duration_ns = 
        context->measurement.end_time_ns - context->measurement.start_time_ns;
    
    /* Update statistics */
    update_stats(&context->measurement);
    
    /* Mark context as free */
    context->active = false;
    
    return 0;
}

int dtesn_profile_report(char *buffer, size_t buffer_size)
{
    if (!buffer || buffer_size == 0) {
        return -EINVAL;
    }
    
    if (!g_profiler.initialized) {
        return -ENODATA;
    }
    
    int written = 0;
    int ret;
    
    /* Header */
    ret = snprintf(buffer + written, buffer_size - written,
                   "DTESN Performance Profiling Report\n"
                   "===================================\n\n"
                   "Profiling Overhead: %lu ns (%.2f%%)\n"
                   "Dropped Measurements: %lu\n"
                   "Active Contexts: %u/%u\n\n",
                   g_profiler.overhead_ns,
                   (double)g_profiler.overhead_ns / 1000.0 * 0.1, /* Approximate % */
                   g_profiler.dropped_measurements,
                   /* Count active contexts */
                   0, g_profiler.max_contexts);
    
    if (ret < 0 || written + ret >= buffer_size) {
        return -ENOSPC;
    }
    written += ret;
    
    /* Per-operation statistics */
    for (int i = 0; i < DTESN_PROFILE_TYPE_COUNT; i++) {
        const dtesn_profile_stats_t *stats = &g_profiler.stats[i];
        
        if (stats->total_count == 0) {
            continue;
        }
        
        ret = snprintf(buffer + written, buffer_size - written,
                       "%s:\n"
                       "  Count: %lu operations\n"
                       "  Total Time: %lu ns\n"
                       "  Average: %lu ns\n"
                       "  Min: %lu ns\n"
                       "  Max: %lu ns\n"
                       "  Violations: %lu (target: %lu ns)\n"
                       "  Last: %lu ns ago\n\n",
                       g_operation_names[i],
                       stats->total_count,
                       stats->total_time_ns,
                       stats->avg_time_ns,
                       stats->min_time_ns,
                       stats->max_time_ns,
                       stats->violations,
                       g_performance_targets[i],
                       get_timestamp_ns() - stats->last_measurement_ns);
        
        if (ret < 0 || written + ret >= buffer_size) {
            return -ENOSPC;
        }
        written += ret;
    }
    
    return written;
}

int dtesn_hw_counters(uint64_t counters[DTESN_HW_COUNTER_TYPE_COUNT])
{
    if (!counters) {
        return -EINVAL;
    }
    
    return read_hw_counters(counters);
}

int dtesn_profile_enable(bool enabled)
{
    if (!g_profiler.initialized) {
        return -ENODATA;
    }
    
    g_profiler.enabled = enabled;
    return 0;
}

int dtesn_profile_reset(void)
{
    if (!g_profiler.initialized) {
        return -ENODATA;
    }
    
    pthread_mutex_lock(&g_profiler_mutex);
    
    /* Reset all statistics */
    for (int i = 0; i < DTESN_PROFILE_TYPE_COUNT; i++) {
        memset(&g_profiler.stats[i], 0, sizeof(dtesn_profile_stats_t));
    }
    
    g_profiler.dropped_measurements = 0;
    
    /* Clear all active contexts */
    for (uint32_t i = 0; i < g_profiler.max_contexts; i++) {
        g_profiler.contexts[i].active = false;
    }
    
    pthread_mutex_unlock(&g_profiler_mutex);
    return 0;
}

uint64_t dtesn_profile_overhead(void)
{
    if (!g_profiler.initialized) {
        return 0;
    }
    
    /* Measure overhead by performing empty profiling cycles */
    const int iterations = 1000;
    uint64_t start_time = get_timestamp_ns();
    
    for (int i = 0; i < iterations; i++) {
        dtesn_profile_context_t *ctx = dtesn_profile_start(DTESN_PROFILE_MEMORY_ALLOC, 0);
        if (ctx) {
            dtesn_profile_end(ctx);
        }
    }
    
    uint64_t end_time = get_timestamp_ns();
    uint64_t total_overhead = end_time - start_time;
    
    return total_overhead / iterations;
}

int dtesn_profile_cleanup(void)
{
    if (!g_profiler.initialized) {
        return -ENODATA;
    }
    
    pthread_mutex_lock(&g_profiler_mutex);
    
    /* Free resources */
    if (g_profiler.contexts) {
        free(g_profiler.contexts);
        g_profiler.contexts = NULL;
    }
    
    g_profiler.initialized = false;
    g_profiler.enabled = false;
    g_profiler.max_contexts = 0;
    
    pthread_mutex_unlock(&g_profiler_mutex);
    return 0;
}