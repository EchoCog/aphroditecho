/*
 * DTESN Performance Profiling Framework
 * =====================================
 * 
 * Low-overhead performance profiling system for Deep Tree Echo State Networks
 * kernel components with hardware performance counter integration.
 * 
 * Performance Requirements:
 * - Profiling overhead: ≤ 2%
 * - Counter accuracy: 1ns resolution
 * - Data collection: real-time
 * - Analysis latency: ≤ 1ms
 * 
 * Profiling Points:
 * - Memory allocation/deallocation
 * - Membrane evolution cycles
 * - B-Series computations
 * - ESN state updates
 * - System call overhead
 */

#ifndef DTESN_PROFILER_H
#define DTESN_PROFILER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Performance counter types based on DTESN component operations */
typedef enum dtesn_profile_type {
    DTESN_PROFILE_MEMORY_ALLOC = 0,
    DTESN_PROFILE_MEMORY_FREE,
    DTESN_PROFILE_MEMBRANE_EVOLUTION,
    DTESN_PROFILE_BSERIES_COMPUTE,
    DTESN_PROFILE_ESN_UPDATE,
    DTESN_PROFILE_SYSCALL,
    DTESN_PROFILE_SCHEDULER,
    DTESN_PROFILE_TYPE_COUNT
} dtesn_profile_type_t;

/* Hardware performance counter types */
typedef enum dtesn_hw_counter_type {
    DTESN_HW_CPU_CYCLES = 0,
    DTESN_HW_INSTRUCTIONS,
    DTESN_HW_CACHE_MISSES,
    DTESN_HW_BRANCH_MISSES,
    DTESN_HW_PAGE_FAULTS,
    DTESN_HW_CONTEXT_SWITCHES,
    DTESN_HW_COUNTER_TYPE_COUNT
} dtesn_hw_counter_type_t;

/* Performance measurement data */
typedef struct dtesn_profile_measurement {
    uint64_t start_time_ns;      /* Start timestamp (nanoseconds) */
    uint64_t end_time_ns;        /* End timestamp (nanoseconds) */
    uint64_t duration_ns;        /* Operation duration */
    dtesn_profile_type_t type;   /* Operation type */
    uint32_t membrane_level;     /* Membrane hierarchy level (OEIS A000081) */
    uint64_t hw_counters[DTESN_HW_COUNTER_TYPE_COUNT]; /* Hardware counters */
} dtesn_profile_measurement_t;

/* Performance statistics for each operation type */
typedef struct dtesn_profile_stats {
    uint64_t total_count;        /* Total number of operations */
    uint64_t total_time_ns;      /* Total time spent */
    uint64_t min_time_ns;        /* Minimum operation time */
    uint64_t max_time_ns;        /* Maximum operation time */
    uint64_t avg_time_ns;        /* Average operation time */
    uint64_t violations;         /* Performance target violations */
    uint64_t last_measurement_ns; /* Last measurement timestamp */
} dtesn_profile_stats_t;

/* Profiling context for tracking active measurements */
typedef struct dtesn_profile_context {
    dtesn_profile_measurement_t measurement;
    bool active;                 /* Context currently in use */
    uint32_t thread_id;         /* Thread ID for context isolation */
} dtesn_profile_context_t;

/* Main profiling system state */
typedef struct dtesn_profiler {
    bool initialized;            /* Profiler initialization state */
    bool enabled;                /* Global profiling enable/disable */
    uint64_t overhead_ns;        /* Measured profiling overhead */
    dtesn_profile_stats_t stats[DTESN_PROFILE_TYPE_COUNT];
    dtesn_profile_context_t *contexts; /* Per-CPU contexts */
    uint32_t max_contexts;       /* Maximum number of contexts */
    uint64_t dropped_measurements; /* Counter for dropped measurements */
} dtesn_profiler_t;

/* Performance targets for violation detection */
#define DTESN_PROFILE_MEMORY_ALLOC_TARGET_NS   10000   /* ≤ 10μs */
#define DTESN_PROFILE_MEMORY_FREE_TARGET_NS     5000   /* ≤ 5μs */
#define DTESN_PROFILE_MEMBRANE_EVOLUTION_TARGET_NS  10000  /* ≤ 10μs */
#define DTESN_PROFILE_BSERIES_COMPUTE_TARGET_NS 100000 /* ≤ 100μs */
#define DTESN_PROFILE_ESN_UPDATE_TARGET_NS     1000000 /* ≤ 1ms */
#define DTESN_PROFILE_SYSCALL_TARGET_NS         5000   /* ≤ 5μs */

/* Maximum profiling overhead threshold */
#define DTESN_PROFILE_OVERHEAD_THRESHOLD        2.0    /* ≤ 2% */

/* Default maximum contexts (typically number of CPU cores) */
#define DTESN_PROFILE_DEFAULT_MAX_CONTEXTS      32

/*
 * Core profiling functions
 */

/**
 * dtesn_profile_init - Initialize the DTESN profiling framework
 * @max_contexts: Maximum number of concurrent profiling contexts
 *
 * Initializes low-overhead performance profiling system with hardware
 * counter support and per-CPU context isolation.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_profile_init(uint32_t max_contexts);

/**
 * dtesn_profile_start - Begin profiling an operation
 * @type: Type of operation being profiled
 * @membrane_level: Membrane hierarchy level (0-7, OEIS A000081)
 *
 * Starts timing measurement with hardware counter collection.
 * Must be called before the operation to be profiled.
 *
 * Return: Profile context pointer on success, NULL on failure
 */
dtesn_profile_context_t *dtesn_profile_start(dtesn_profile_type_t type,
                                             uint32_t membrane_level);

/**
 * dtesn_profile_end - Complete profiling an operation
 * @context: Profile context from dtesn_profile_start()
 *
 * Completes timing measurement and updates statistics.
 * Must be called after the operation being profiled.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_profile_end(dtesn_profile_context_t *context);

/**
 * dtesn_profile_report - Generate performance report
 * @buffer: Output buffer for report
 * @buffer_size: Size of output buffer
 *
 * Generates comprehensive performance statistics report including
 * violation detection and overhead analysis.
 *
 * Return: Number of bytes written on success, negative error code on failure
 */
int dtesn_profile_report(char *buffer, size_t buffer_size);

/**
 * dtesn_hw_counters - Read hardware performance counters
 * @counters: Array to store counter values
 *
 * Reads current hardware performance counter values for
 * low-level performance analysis.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_hw_counters(uint64_t counters[DTESN_HW_COUNTER_TYPE_COUNT]);

/**
 * dtesn_profile_enable - Enable/disable profiling
 * @enabled: true to enable, false to disable
 *
 * Dynamically control profiling overhead by enabling/disabling
 * measurement collection.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_profile_enable(bool enabled);

/**
 * dtesn_profile_reset - Reset profiling statistics
 *
 * Clears all accumulated statistics and resets counters.
 * Useful for benchmark runs and regression testing.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_profile_reset(void);

/**
 * dtesn_profile_overhead - Measure profiling overhead
 *
 * Calibrates profiling system overhead by performing
 * empty measurement cycles.
 *
 * Return: Overhead in nanoseconds
 */
uint64_t dtesn_profile_overhead(void);

/**
 * dtesn_profile_cleanup - Shutdown profiling framework
 *
 * Releases resources and generates final performance report.
 *
 * Return: 0 on success, negative error code on failure
 */
int dtesn_profile_cleanup(void);

/*
 * Convenience macros for common profiling patterns
 */

/* Profile a code block automatically */
#define DTESN_PROFILE_BLOCK(type, level) \
    dtesn_profile_context_t *__prof_ctx = dtesn_profile_start(type, level); \
    do

#define DTESN_PROFILE_END() \
    while (0); \
    if (__prof_ctx) dtesn_profile_end(__prof_ctx)

/* Profile function entry/exit */
#define DTESN_PROFILE_FUNCTION(type, level) \
    dtesn_profile_context_t *__prof_ctx = dtesn_profile_start(type, level)

#define DTESN_PROFILE_FUNCTION_END() \
    if (__prof_ctx) dtesn_profile_end(__prof_ctx)

/* Quick profiling for performance-critical sections */
#define DTESN_PROFILE_QUICK(type) \
    dtesn_profile_context_t *__prof_ctx = dtesn_profile_start(type, 0)

#ifdef __cplusplus
}
#endif

#endif /* DTESN_PROFILER_H */