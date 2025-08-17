/*
 * DTESN Core API Implementation
 * ============================
 * 
 * Core user-space library implementation for DTESN APIs.
 * Provides high-level wrappers around DTESN system calls with
 * error handling, performance optimization, and thread safety.
 */

#include "libdtesn.h"
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <sys/time.h>
#include <stdio.h>

/* Library global state */
static struct {
    bool initialized;
    dtesn_lib_config_t config;
    dtesn_perf_stats_t global_stats;
    pthread_mutex_t stats_mutex;
    pthread_mutex_t instance_mutex;
    dtesn_handle_t *instances[DTESN_MAX_CONCURRENT_INSTANCES];
    uint32_t next_instance_id;
    int debug_level;
} g_dtesn_lib = { .initialized = false };

/* Thread-local error storage */
static __thread int g_last_error = 0;

/* Internal function declarations */
static uint64_t get_timestamp_ns(void);
static int validate_create_params(const struct dtesn_create_params *params);
static int validate_oeis_compliance(uint32_t depth, uint32_t membrane_count);
static void update_performance_stats(uint64_t start_time_ns, bool success);
static dtesn_handle_t *allocate_handle(void);
static void free_handle(dtesn_handle_t *handle);
static int find_free_instance_slot(void);

/* Performance monitoring helpers */
static inline uint64_t get_timestamp_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static void update_performance_stats(uint64_t start_time_ns, bool success)
{
    uint64_t end_time_ns = get_timestamp_ns();
    uint64_t execution_time_ns = end_time_ns - start_time_ns;
    
    pthread_mutex_lock(&g_dtesn_lib.stats_mutex);
    
    g_dtesn_lib.global_stats.total_api_calls++;
    g_dtesn_lib.global_stats.total_execution_time_ns += execution_time_ns;
    
    if (g_dtesn_lib.global_stats.total_api_calls == 1) {
        g_dtesn_lib.global_stats.min_call_time_ns = execution_time_ns;
        g_dtesn_lib.global_stats.max_call_time_ns = execution_time_ns;
    } else {
        if (execution_time_ns < g_dtesn_lib.global_stats.min_call_time_ns) {
            g_dtesn_lib.global_stats.min_call_time_ns = execution_time_ns;
        }
        if (execution_time_ns > g_dtesn_lib.global_stats.max_call_time_ns) {
            g_dtesn_lib.global_stats.max_call_time_ns = execution_time_ns;
        }
    }
    
    g_dtesn_lib.global_stats.avg_call_overhead_ns = 
        g_dtesn_lib.global_stats.total_execution_time_ns / g_dtesn_lib.global_stats.total_api_calls;
    
    if (!success) {
        g_dtesn_lib.global_stats.failed_calls++;
    }
    
    pthread_mutex_unlock(&g_dtesn_lib.stats_mutex);
}

/* OEIS A000081 validation */
static const uint32_t oeis_a000081[] = {
    0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973, 86810
};

static int validate_oeis_compliance(uint32_t depth, uint32_t membrane_count)
{
    if (depth >= sizeof(oeis_a000081) / sizeof(oeis_a000081[0])) {
        return DTESN_ERROR_INVALID_DEPTH;
    }
    
    if (membrane_count != oeis_a000081[depth]) {
        return DTESN_ERROR_OEIS_VIOLATION;
    }
    
    return 0;
}

static int validate_create_params(const struct dtesn_create_params *params)
{
    if (!params) {
        return -EINVAL;
    }
    
    /* Validate depth */
    if (params->depth < 1 || params->depth > DTESN_MAX_DEPTH) {
        return DTESN_ERROR_INVALID_DEPTH;
    }
    
    /* Validate B-series order */
    if (params->max_order < 1 || params->max_order > DTESN_MAX_ORDER) {
        return DTESN_ERROR_INVALID_ORDER;
    }
    
    /* Validate neuron count */
    if (params->neuron_count > DTESN_MAX_NEURONS) {
        return -EINVAL;
    }
    
    /* Validate membrane count */
    if (params->membrane_count > DTESN_MAX_MEMBRANES) {
        return -EINVAL;
    }
    
    /* Validate input/output dimensions */
    if (params->input_dim > DTESN_MAX_INPUT_SIZE || 
        params->output_dim > DTESN_MAX_OUTPUT_SIZE) {
        return -EINVAL;
    }
    
    /* Validate OEIS compliance if requested */
    if (params->flags & DTESN_CREATE_VALIDATE_OEIS) {
        int oeis_result = validate_oeis_compliance(params->depth, params->membrane_count);
        if (oeis_result != 0) {
            return oeis_result;
        }
    }
    
    return 0;
}

/* Instance management helpers */
static dtesn_handle_t *allocate_handle(void)
{
    dtesn_handle_t *handle = calloc(1, sizeof(dtesn_handle_t));
    if (!handle) {
        return NULL;
    }
    
    handle->fd = -1;
    handle->creation_time_ns = get_timestamp_ns();
    handle->is_async = false;
    
    return handle;
}

static void free_handle(dtesn_handle_t *handle)
{
    if (handle) {
        if (handle->fd >= 0) {
            close(handle->fd);
        }
        free(handle->private_data);
        free(handle);
    }
}

static int find_free_instance_slot(void)
{
    for (int i = 0; i < DTESN_MAX_CONCURRENT_INSTANCES; i++) {
        if (g_dtesn_lib.instances[i] == NULL) {
            return i;
        }
    }
    return -1;
}

/*
 * Public API Implementation
 * ========================
 */

int dtesn_init(const dtesn_lib_config_t *config)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (g_dtesn_lib.initialized) {
        g_last_error = -EALREADY;
        return -EALREADY;
    }
    
    /* Initialize default configuration */
    if (config) {
        g_dtesn_lib.config = *config;
    } else {
        g_dtesn_lib.config.max_instances = DTESN_MAX_CONCURRENT_INSTANCES;
        g_dtesn_lib.config.async_queue_size = DTESN_MAX_ASYNC_OPERATIONS;
        g_dtesn_lib.config.worker_threads = 4;
        g_dtesn_lib.config.flags = 0;
    }
    
    /* Initialize mutexes */
    int ret = pthread_mutex_init(&g_dtesn_lib.stats_mutex, NULL);
    if (ret != 0) {
        g_last_error = -ret;
        return -ret;
    }
    
    ret = pthread_mutex_init(&g_dtesn_lib.instance_mutex, NULL);
    if (ret != 0) {
        pthread_mutex_destroy(&g_dtesn_lib.stats_mutex);
        g_last_error = -ret;
        return -ret;
    }
    
    /* Initialize instance array */
    memset(g_dtesn_lib.instances, 0, sizeof(g_dtesn_lib.instances));
    g_dtesn_lib.next_instance_id = 1;
    
    /* Initialize performance stats */
    memset(&g_dtesn_lib.global_stats, 0, sizeof(g_dtesn_lib.global_stats));
    
    g_dtesn_lib.debug_level = 1; /* Default to errors only */
    g_dtesn_lib.initialized = true;
    
    update_performance_stats(start_time, true);
    
    if (g_dtesn_lib.debug_level >= 3) {
        printf("DTESN: Library initialized successfully (v%s)\n", LIBDTESN_VERSION_STRING);
    }
    
    return 0;
}

int dtesn_cleanup(void)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized) {
        g_last_error = -ENOTCONN;
        return -ENOTCONN;
    }
    
    /* Close all active instances */
    pthread_mutex_lock(&g_dtesn_lib.instance_mutex);
    for (int i = 0; i < DTESN_MAX_CONCURRENT_INSTANCES; i++) {
        if (g_dtesn_lib.instances[i]) {
            dtesn_destroy(g_dtesn_lib.instances[i]);
            g_dtesn_lib.instances[i] = NULL;
        }
    }
    pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
    
    /* Cleanup mutexes */
    pthread_mutex_destroy(&g_dtesn_lib.stats_mutex);
    pthread_mutex_destroy(&g_dtesn_lib.instance_mutex);
    
    g_dtesn_lib.initialized = false;
    
    update_performance_stats(start_time, true);
    
    if (g_dtesn_lib.debug_level >= 3) {
        printf("DTESN: Library cleanup completed\n");
    }
    
    return 0;
}

const char *dtesn_get_version(int *major, int *minor, int *patch)
{
    if (major) *major = LIBDTESN_VERSION_MAJOR;
    if (minor) *minor = LIBDTESN_VERSION_MINOR;
    if (patch) *patch = LIBDTESN_VERSION_PATCH;
    
    return LIBDTESN_VERSION_STRING;
}

int dtesn_create(const struct dtesn_create_params *params, dtesn_handle_t **handle)
{
    uint64_t start_time = get_timestamp_ns();
    int result = 0;
    
    if (!g_dtesn_lib.initialized) {
        g_last_error = -ENOTCONN;
        return -ENOTCONN;
    }
    
    if (!params || !handle) {
        g_last_error = -EINVAL;
        update_performance_stats(start_time, false);
        return -EINVAL;
    }
    
    /* Validate parameters */
    result = validate_create_params(params);
    if (result != 0) {
        g_last_error = result;
        update_performance_stats(start_time, false);
        return result;
    }
    
    /* Find free instance slot */
    pthread_mutex_lock(&g_dtesn_lib.instance_mutex);
    int slot = find_free_instance_slot();
    if (slot < 0) {
        pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
        g_last_error = -ENOMEM;
        update_performance_stats(start_time, false);
        return -ENOMEM;
    }
    
    /* Allocate handle */
    dtesn_handle_t *new_handle = allocate_handle();
    if (!new_handle) {
        pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
        g_last_error = -ENOMEM;
        update_performance_stats(start_time, false);
        return -ENOMEM;
    }
    
    /* Make system call to create DTESN instance */
    long syscall_result = syscall(__NR_sys_dtesn_create, params);
    if (syscall_result < 0) {
        free_handle(new_handle);
        pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
        g_last_error = (int)syscall_result;
        update_performance_stats(start_time, false);
        return (int)syscall_result;
    }
    
    /* Initialize handle */
    new_handle->fd = (int)syscall_result;
    new_handle->instance_id = g_dtesn_lib.next_instance_id++;
    memcpy(&new_handle->params, params, sizeof(*params));
    
    /* Store in instance array */
    g_dtesn_lib.instances[slot] = new_handle;
    g_dtesn_lib.global_stats.active_instances++;
    
    pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
    
    *handle = new_handle;
    
    update_performance_stats(start_time, true);
    
    if (g_dtesn_lib.debug_level >= 3) {
        printf("DTESN: Created instance %u (fd=%d)\n", new_handle->instance_id, new_handle->fd);
    }
    
    return 0;
}

int dtesn_destroy(dtesn_handle_t *handle)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized) {
        g_last_error = -ENOTCONN;
        return -ENOTCONN;
    }
    
    if (!handle) {
        g_last_error = -EINVAL;
        update_performance_stats(start_time, false);
        return -EINVAL;
    }
    
    /* Make system call to destroy instance */
    long syscall_result = syscall(__NR_sys_dtesn_destroy, handle->fd);
    
    /* Remove from instance array */
    pthread_mutex_lock(&g_dtesn_lib.instance_mutex);
    for (int i = 0; i < DTESN_MAX_CONCURRENT_INSTANCES; i++) {
        if (g_dtesn_lib.instances[i] == handle) {
            g_dtesn_lib.instances[i] = NULL;
            g_dtesn_lib.global_stats.active_instances--;
            break;
        }
    }
    pthread_mutex_unlock(&g_dtesn_lib.instance_mutex);
    
    if (g_dtesn_lib.debug_level >= 3) {
        printf("DTESN: Destroyed instance %u (fd=%d)\n", handle->instance_id, handle->fd);
    }
    
    /* Free handle */
    free_handle(handle);
    
    bool success = (syscall_result == 0);
    if (!success) {
        g_last_error = (int)syscall_result;
    }
    
    update_performance_stats(start_time, success);
    
    return success ? 0 : (int)syscall_result;
}

int dtesn_evolve(dtesn_handle_t *handle, const float *input, 
                 uint32_t input_size, uint32_t steps, uint32_t mode)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized || !handle) {
        g_last_error = !g_dtesn_lib.initialized ? -ENOTCONN : -EINVAL;
        update_performance_stats(start_time, false);
        return g_last_error;
    }
    
    if (!input || input_size == 0 || steps == 0) {
        g_last_error = -EINVAL;
        update_performance_stats(start_time, false);
        return -EINVAL;
    }
    
    if (input_size > handle->params.input_dim) {
        g_last_error = -EINVAL;
        update_performance_stats(start_time, false);
        return -EINVAL;
    }
    
    /* Prepare evolution parameters */
    struct dtesn_evolve_params evolve_params = {
        .fd = handle->fd,
        .input = input,
        .input_size = input_size,
        .steps = steps,
        .mode = mode,
        .timeout_ns = DTESN_DEFAULT_TIMEOUT_MS * 1000000ULL
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_dtesn_evolve, &evolve_params);
    
    bool success = (syscall_result == 0);
    if (!success) {
        g_last_error = (int)syscall_result;
    }
    
    update_performance_stats(start_time, success);
    
    return success ? 0 : (int)syscall_result;
}

int dtesn_get_state(dtesn_handle_t *handle, struct dtesn_state_info *state)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized || !handle || !state) {
        g_last_error = !g_dtesn_lib.initialized ? -ENOTCONN : -EINVAL;
        update_performance_stats(start_time, false);
        return g_last_error;
    }
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_dtesn_get_state, handle->fd, state);
    
    bool success = (syscall_result == 0);
    if (!success) {
        g_last_error = (int)syscall_result;
    }
    
    update_performance_stats(start_time, success);
    
    return success ? 0 : (int)syscall_result;
}

int dtesn_get_performance_stats(dtesn_handle_t *handle, dtesn_perf_stats_t *stats)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized || !stats) {
        g_last_error = !g_dtesn_lib.initialized ? -ENOTCONN : -EINVAL;
        update_performance_stats(start_time, false);
        return g_last_error;
    }
    
    if (handle == NULL) {
        /* Return global statistics */
        pthread_mutex_lock(&g_dtesn_lib.stats_mutex);
        memcpy(stats, &g_dtesn_lib.global_stats, sizeof(*stats));
        pthread_mutex_unlock(&g_dtesn_lib.stats_mutex);
    } else {
        /* For now, return global stats - could be extended for per-instance stats */
        pthread_mutex_lock(&g_dtesn_lib.stats_mutex);
        memcpy(stats, &g_dtesn_lib.global_stats, sizeof(*stats));
        pthread_mutex_unlock(&g_dtesn_lib.stats_mutex);
    }
    
    update_performance_stats(start_time, true);
    
    return 0;
}

int dtesn_reset_performance_stats(dtesn_handle_t *handle)
{
    uint64_t start_time = get_timestamp_ns();
    
    if (!g_dtesn_lib.initialized) {
        g_last_error = -ENOTCONN;
        return -ENOTCONN;
    }
    
    pthread_mutex_lock(&g_dtesn_lib.stats_mutex);
    
    if (handle == NULL) {
        /* Reset global statistics */
        memset(&g_dtesn_lib.global_stats, 0, sizeof(g_dtesn_lib.global_stats));
    }
    /* Per-instance reset would be implemented here */
    
    pthread_mutex_unlock(&g_dtesn_lib.stats_mutex);
    
    update_performance_stats(start_time, true);
    
    return 0;
}

const char *dtesn_strerror(int error)
{
    switch (error) {
        case DTESN_SUCCESS:
            return "Success";
        case DTESN_ERROR_INVALID_DEPTH:
            return "Invalid tree depth";
        case DTESN_ERROR_INVALID_ORDER:
            return "Invalid B-series order";
        case DTESN_ERROR_OEIS_VIOLATION:
            return "OEIS A000081 compliance violation";
        case DTESN_ERROR_PERFORMANCE:
            return "Performance target not met";
        case DTESN_ERROR_HARDWARE:
            return "Hardware acceleration error";
        case DTESN_ERROR_MEMBRANE:
            return "P-system membrane operation error";
        case DTESN_ERROR_ESN:
            return "ESN operation error";
        case DTESN_ERROR_BSERIES:
            return "B-series computation error";
        default:
            if (error < 0) {
                return strerror(-error);
            }
            return "Unknown error";
    }
}

int dtesn_get_last_error(void)
{
    return g_last_error;
}

int dtesn_set_debug_level(int level)
{
    int old_level = g_dtesn_lib.debug_level;
    g_dtesn_lib.debug_level = level;
    return old_level;
}