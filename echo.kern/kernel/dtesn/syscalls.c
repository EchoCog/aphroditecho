/*
 * DTESN Comprehensive System Call Interface
 * =======================================
 * 
 * Main system call interface for Deep Tree Echo State Networks (DTESN) operations.
 * Provides unified coordination of P-system membranes, B-series computations, and
 * ESN reservoir computing with real-time performance guarantees.
 * 
 * This implements the high-level DTESN coordination layer that builds upon the
 * existing specialized modules (psystem_syscalls.c, bseries.c, esn.c).
 */

#define _GNU_SOURCE
#include "include/uapi/dtesn.h"
#include "include/dtesn/psystem.h"
#include "include/dtesn/bseries.h"
#include "include/dtesn/esn.h"
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/sched.h>
#include <linux/time.h>
#include <linux/file.h>
#include <linux/fs.h>
#include <linux/anon_inodes.h>
#include <linux/atomic.h>

/* DTESN instance management */
#define DTESN_MAX_INSTANCES         256
#define DTESN_INSTANCE_MAGIC        0xDEADBEEF

/* Performance tracking */
struct dtesn_perf_tracker {
    atomic64_t syscall_count;
    atomic64_t total_syscall_time_ns;
    atomic64_t validation_time_ns;
    atomic64_t copy_time_ns;
    atomic64_t error_count;
    atomic64_t cache_hits;
    atomic64_t cache_misses;
};

/* DTESN instance structure */
struct dtesn_instance {
    uint32_t magic;                         /* Magic number for validation */
    uint32_t instance_id;                   /* Unique instance identifier */
    struct dtesn_create_params params;      /* Creation parameters */
    dtesn_psystem_t *psystem;              /* P-system instance */
    dtesn_bseries_context_t *bseries;      /* B-series computation context */
    dtesn_esn_reservoir_t *esn;            /* ESN reservoir instance */
    struct dtesn_state_info state;         /* Current state information */
    struct dtesn_perf_tracker perf;        /* Performance metrics */
    struct mutex lock;                     /* Instance synchronization */
    atomic_t ref_count;                    /* Reference counting */
    bool is_destroyed;                     /* Destruction flag */
    uint64_t creation_time_ns;             /* Creation timestamp */
    uint64_t last_access_ns;               /* Last access timestamp */
};

/* Global DTESN state */
static struct dtesn_instance *g_dtesn_instances[DTESN_MAX_INSTANCES];
static DEFINE_MUTEX(g_dtesn_instances_mutex);
static atomic_t g_next_instance_id = ATOMIC_INIT(1);
static struct dtesn_perf_tracker g_global_perf;
static bool g_dtesn_initialized = false;

/* OEIS A000081 validation sequence */
static const uint32_t g_oeis_a000081[] = DTESN_OEIS_A000081_SEQUENCE_INIT;
static const size_t g_oeis_a000081_len = ARRAY_SIZE(g_oeis_a000081);

/* Forward declarations */
static int dtesn_validate_create_params(const struct dtesn_create_params *params);
static int dtesn_validate_oeis_compliance(struct dtesn_instance *instance);
static void dtesn_instance_get(struct dtesn_instance *instance);
static void dtesn_instance_put(struct dtesn_instance *instance);
static void dtesn_instance_destroy(struct dtesn_instance *instance);
static uint64_t dtesn_get_time_ns(void);

/**
 * dtesn_get_time_ns - Get current time in nanoseconds
 * 
 * Returns: Current time in nanoseconds since boot
 */
static uint64_t dtesn_get_time_ns(void) {
    struct timespec64 ts;
    ktime_get_boottime_ts64(&ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/**
 * dtesn_validate_create_params - Validate DTESN creation parameters
 * @params: Creation parameters to validate
 * 
 * Returns: 0 if valid, negative error code if invalid
 */
static int dtesn_validate_create_params(const struct dtesn_create_params *params) {
    uint64_t start_time = dtesn_get_time_ns();
    int ret = 0;
    
    if (!params) {
        ret = -EINVAL;
        goto out;
    }
    
    /* Validate depth against OEIS A000081 sequence */
    if (!DTESN_VALID_DEPTH(params->depth)) {
        ret = DTESN_ERROR_INVALID_DEPTH;
        goto out;
    }
    
    /* Validate B-series order */
    if (!DTESN_VALID_ORDER(params->max_order)) {
        ret = DTESN_ERROR_INVALID_ORDER;
        goto out;
    }
    
    /* Validate neuron count */
    if (!DTESN_VALID_NEURONS(params->neuron_count)) {
        ret = -EINVAL;
        goto out;
    }
    
    /* Validate membrane count */
    if (!DTESN_VALID_MEMBRANES(params->membrane_count)) {
        ret = -EINVAL;
        goto out;
    }
    
    /* Validate input/output dimensions */
    if (!DTESN_VALID_INPUT_SIZE(params->input_dim) || 
        !DTESN_VALID_OUTPUT_SIZE(params->output_dim)) {
        ret = -EINVAL;
        goto out;
    }
    
    /* Validate OEIS A000081 compliance if requested */
    if (params->flags & DTESN_CREATE_VALIDATE_OEIS) {
        if (params->depth >= g_oeis_a000081_len) {
            ret = DTESN_ERROR_OEIS_VIOLATION;
            goto out;
        }
        
        /* Check if membrane count matches expected OEIS sequence */
        uint32_t expected_membranes = g_oeis_a000081[params->depth];
        if (params->membrane_count > expected_membranes * 2) {
            /* Allow some flexibility but not excessive deviation */
            ret = DTESN_ERROR_OEIS_VIOLATION;
            goto out;
        }
    }
    
out:
    atomic64_add(dtesn_get_time_ns() - start_time, &g_global_perf.validation_time_ns);
    return ret;
}

/**
 * dtesn_validate_oeis_compliance - Validate OEIS A000081 compliance
 * @instance: DTESN instance to validate
 * 
 * Returns: 1 if compliant, 0 if not compliant, negative error code on failure
 */
static int dtesn_validate_oeis_compliance(struct dtesn_instance *instance) {
    if (!instance || !instance->psystem) {
        return -EINVAL;
    }
    
    /* Use existing P-system validation function */
    bool is_valid = dtesn_psystem_validate_a000081(instance->psystem);
    return is_valid ? 1 : 0;
}

/**
 * dtesn_instance_get - Increment instance reference count
 * @instance: DTESN instance
 */
static void dtesn_instance_get(struct dtesn_instance *instance) {
    if (instance) {
        atomic_inc(&instance->ref_count);
    }
}

/**
 * dtesn_instance_put - Decrement instance reference count
 * @instance: DTESN instance
 */
static void dtesn_instance_put(struct dtesn_instance *instance) {
    if (instance && atomic_dec_and_test(&instance->ref_count)) {
        dtesn_instance_destroy(instance);
    }
}

/**
 * dtesn_instance_destroy - Destroy DTESN instance
 * @instance: DTESN instance to destroy
 */
static void dtesn_instance_destroy(struct dtesn_instance *instance) {
    if (!instance) {
        return;
    }
    
    mutex_lock(&instance->lock);
    instance->is_destroyed = true;
    
    /* Destroy component instances */
    if (instance->psystem) {
        dtesn_psystem_destroy(instance->psystem);
        instance->psystem = NULL;
    }
    
    if (instance->bseries) {
        dtesn_bseries_context_destroy(instance->bseries);
        instance->bseries = NULL;
    }
    
    if (instance->esn) {
        dtesn_esn_reservoir_destroy(instance->esn);
        instance->esn = NULL;
    }
    
    mutex_unlock(&instance->lock);
    kfree(instance);
}

/**
 * sys_dtesn_create - Create a new DTESN instance
 * @params: Creation parameters (user space pointer)
 * 
 * Creates a new DTESN instance with the specified parameters and returns
 * a file descriptor for future operations.
 * 
 * Returns: File descriptor on success, negative error code on failure
 */
SYSCALL_DEFINE1(sys_dtesn_create, const struct dtesn_create_params __user *, params) {
    struct dtesn_create_params kernel_params;
    struct dtesn_instance *instance = NULL;
    uint64_t start_time = dtesn_get_time_ns();
    int fd = -1;
    int ret;
    int i;
    
    atomic64_inc(&g_global_perf.syscall_count);
    
    /* Copy parameters from user space */
    if (copy_from_user(&kernel_params, params, sizeof(kernel_params))) {
        ret = -EFAULT;
        goto error;
    }
    
    /* Validate parameters */
    ret = dtesn_validate_create_params(&kernel_params);
    if (ret < 0) {
        goto error;
    }
    
    /* Allocate new instance */
    instance = kzalloc(sizeof(struct dtesn_instance), GFP_KERNEL);
    if (!instance) {
        ret = -ENOMEM;
        goto error;
    }
    
    /* Initialize instance */
    instance->magic = DTESN_INSTANCE_MAGIC;
    instance->instance_id = atomic_inc_return(&g_next_instance_id);
    instance->params = kernel_params;
    instance->creation_time_ns = dtesn_get_time_ns();
    instance->last_access_ns = instance->creation_time_ns;
    mutex_init(&instance->lock);
    atomic_set(&instance->ref_count, 1);
    
    /* Initialize state information */
    instance->state.depth = kernel_params.depth;
    instance->state.active_membranes = 0;
    instance->state.total_neurons = kernel_params.neuron_count;
    instance->state.evolution_steps = 0;
    instance->state.creation_time_ns = instance->creation_time_ns;
    instance->state.last_update_ns = instance->creation_time_ns;
    instance->state.spectral_radius = 0.9; /* Default ESN spectral radius */
    instance->state.membrane_activity = 0.0;
    instance->state.oeis_compliance = 1;
    instance->state.performance_violations = 0;
    
    /* Create P-system instance */
    instance->psystem = dtesn_psystem_create(kernel_params.label, 
                                            kernel_params.membrane_count);
    if (!instance->psystem) {
        ret = -ENOMEM;
        goto error;
    }
    
    /* Create B-series context */
    instance->bseries = dtesn_bseries_context_create(kernel_params.max_order);
    if (!instance->bseries) {
        ret = -ENOMEM;
        goto error;
    }
    
    /* Create ESN reservoir */
    instance->esn = dtesn_esn_reservoir_create(kernel_params.neuron_count,
                                               kernel_params.input_dim,
                                               kernel_params.output_dim);
    if (!instance->esn) {
        ret = -ENOMEM;
        goto error;
    }
    
    /* Find available instance slot */
    mutex_lock(&g_dtesn_instances_mutex);
    for (i = 0; i < DTESN_MAX_INSTANCES; i++) {
        if (!g_dtesn_instances[i]) {
            g_dtesn_instances[i] = instance;
            break;
        }
    }
    mutex_unlock(&g_dtesn_instances_mutex);
    
    if (i >= DTESN_MAX_INSTANCES) {
        ret = -ENFILE;
        goto error;
    }
    
    /* Create anonymous file descriptor */
    fd = anon_inode_getfd("dtesn", NULL, instance, O_RDWR);
    if (fd < 0) {
        mutex_lock(&g_dtesn_instances_mutex);
        g_dtesn_instances[i] = NULL;
        mutex_unlock(&g_dtesn_instances_mutex);
        ret = fd;
        goto error;
    }
    
    /* Validate OEIS compliance if requested */
    if (kernel_params.flags & DTESN_CREATE_VALIDATE_OEIS) {
        ret = dtesn_validate_oeis_compliance(instance);
        if (ret <= 0) {
            close_fd(fd);
            ret = DTESN_ERROR_OEIS_VIOLATION;
            goto error;
        }
    }
    
    atomic64_add(dtesn_get_time_ns() - start_time, &g_global_perf.total_syscall_time_ns);
    return fd;
    
error:
    atomic64_inc(&g_global_perf.error_count);
    if (instance) {
        dtesn_instance_put(instance);
    }
    return ret;
}

/**
 * sys_dtesn_evolve - Evolve DTESN instance state
 * @params: Evolution parameters (user space pointer)
 * 
 * Evolves the DTESN instance through the specified number of steps,
 * coordinating P-system, B-series, and ESN computations.
 * 
 * Returns: Number of evolution steps completed, negative error code on failure
 */
SYSCALL_DEFINE1(sys_dtesn_evolve, const struct dtesn_evolve_params __user *, params) {
    struct dtesn_evolve_params kernel_params;
    struct dtesn_instance *instance;
    float *kernel_input = NULL;
    uint64_t start_time = dtesn_get_time_ns();
    uint64_t timeout_time;
    int steps_completed = 0;
    int ret;
    uint32_t step;
    
    atomic64_inc(&g_global_perf.syscall_count);
    
    /* Copy parameters from user space */
    if (copy_from_user(&kernel_params, params, sizeof(kernel_params))) {
        ret = -EFAULT;
        goto error;
    }
    
    /* Validate parameters */
    if (kernel_params.steps == 0 || kernel_params.steps > 1000000) {
        ret = -EINVAL;
        goto error;
    }
    
    /* Find instance by file descriptor */
    /* For simplicity, we'll use fd as array index - production would use proper fd lookup */
    if (kernel_params.fd < 0 || kernel_params.fd >= DTESN_MAX_INSTANCES) {
        ret = -EBADF;
        goto error;
    }
    
    mutex_lock(&g_dtesn_instances_mutex);
    instance = g_dtesn_instances[kernel_params.fd];
    if (instance) {
        dtesn_instance_get(instance);
    }
    mutex_unlock(&g_dtesn_instances_mutex);
    
    if (!instance || instance->magic != DTESN_INSTANCE_MAGIC || instance->is_destroyed) {
        ret = -EBADF;
        goto error;
    }
    
    /* Copy input vector if provided */
    if (kernel_params.input && kernel_params.input_size > 0) {
        if (kernel_params.input_size > DTESN_MAX_INPUT_SIZE) {
            ret = -EINVAL;
            goto cleanup;
        }
        
        kernel_input = kmalloc(kernel_params.input_size * sizeof(float), GFP_KERNEL);
        if (!kernel_input) {
            ret = -ENOMEM;
            goto cleanup;
        }
        
        if (copy_from_user(kernel_input, kernel_params.input, 
                          kernel_params.input_size * sizeof(float))) {
            ret = -EFAULT;
            goto cleanup;
        }
    }
    
    mutex_lock(&instance->lock);
    
    /* Calculate timeout */
    timeout_time = start_time + kernel_params.timeout_ns;
    
    /* Execute evolution steps */
    for (step = 0; step < kernel_params.steps; step++) {
        uint64_t step_start = dtesn_get_time_ns();
        
        /* Check timeout */
        if (kernel_params.timeout_ns > 0 && step_start >= timeout_time) {
            break;
        }
        
        /* Update ESN reservoir if input provided */
        if (kernel_input && instance->esn) {
            ret = dtesn_esn_update(instance->esn, kernel_input, 
                                  kernel_params.input_size);
            if (ret < 0) {
                break;
            }
        }
        
        /* Evolve P-system membranes */
        if (instance->psystem) {
            ret = dtesn_psystem_evolve_step(instance->psystem);
            if (ret < 0) {
                break;
            }
            instance->state.active_membranes = instance->psystem->membrane_count;
        }
        
        /* Perform B-series computation */
        if (instance->bseries) {
            ret = dtesn_bseries_compute_step(instance->bseries);
            if (ret < 0) {
                break;
            }
        }
        
        steps_completed++;
        instance->state.evolution_steps++;
        
        /* Check if we should yield CPU */
        if (step % 100 == 0) {
            cond_resched();
        }
        
        /* Performance monitoring */
        uint64_t step_time = dtesn_get_time_ns() - step_start;
        if (step_time > 10000) { /* 10μs threshold */
            instance->state.performance_violations++;
        }
    }
    
    instance->state.last_update_ns = dtesn_get_time_ns();
    instance->last_access_ns = instance->state.last_update_ns;
    
    mutex_unlock(&instance->lock);
    
cleanup:
    if (kernel_input) {
        kfree(kernel_input);
    }
    if (instance) {
        dtesn_instance_put(instance);
    }
    
    atomic64_add(dtesn_get_time_ns() - start_time, &g_global_perf.total_syscall_time_ns);
    return steps_completed;
    
error:
    atomic64_inc(&g_global_perf.error_count);
    return ret;
}

/**
 * sys_dtesn_get_state - Get current DTESN instance state
 * @fd: DTESN instance file descriptor
 * @state: State information buffer (user space pointer)
 * 
 * Retrieves the current state of the DTESN instance including
 * membrane activity, ESN state, and performance metrics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
SYSCALL_DEFINE2(sys_dtesn_get_state, int, fd, struct dtesn_state_info __user *, state) {
    struct dtesn_instance *instance;
    struct dtesn_state_info kernel_state;
    uint64_t start_time = dtesn_get_time_ns();
    int ret = 0;
    
    atomic64_inc(&g_global_perf.syscall_count);
    
    /* Validate parameters */
    if (!state) {
        ret = -EINVAL;
        goto error;
    }
    
    /* Find instance */
    if (fd < 0 || fd >= DTESN_MAX_INSTANCES) {
        ret = -EBADF;
        goto error;
    }
    
    mutex_lock(&g_dtesn_instances_mutex);
    instance = g_dtesn_instances[fd];
    if (instance) {
        dtesn_instance_get(instance);
    }
    mutex_unlock(&g_dtesn_instances_mutex);
    
    if (!instance || instance->magic != DTESN_INSTANCE_MAGIC || instance->is_destroyed) {
        ret = -EBADF;
        goto error;
    }
    
    mutex_lock(&instance->lock);
    
    /* Copy current state */
    kernel_state = instance->state;
    
    /* Update dynamic state information */
    if (instance->esn) {
        kernel_state.spectral_radius = dtesn_esn_get_spectral_radius(instance->esn);
    }
    
    if (instance->psystem) {
        kernel_state.membrane_activity = dtesn_psystem_get_activity(instance->psystem);
        kernel_state.oeis_compliance = dtesn_validate_oeis_compliance(instance) > 0 ? 1 : 0;
    }
    
    mutex_unlock(&instance->lock);
    
    /* Copy to user space */
    if (copy_to_user(state, &kernel_state, sizeof(kernel_state))) {
        ret = -EFAULT;
        goto cleanup;
    }
    
cleanup:
    if (instance) {
        dtesn_instance_put(instance);
    }
    
    atomic64_add(dtesn_get_time_ns() - start_time, &g_global_perf.total_syscall_time_ns);
    return ret;
    
error:
    atomic64_inc(&g_global_perf.error_count);
    return ret;
}

/**
 * sys_dtesn_destroy - Destroy DTESN instance
 * @fd: DTESN instance file descriptor
 * 
 * Destroys the DTESN instance and releases all associated resources.
 * 
 * Returns: 0 on success, negative error code on failure
 */
SYSCALL_DEFINE1(sys_dtesn_destroy, int, fd) {
    struct dtesn_instance *instance;
    uint64_t start_time = dtesn_get_time_ns();
    int ret = 0;
    
    atomic64_inc(&g_global_perf.syscall_count);
    
    /* Find and remove instance */
    if (fd < 0 || fd >= DTESN_MAX_INSTANCES) {
        ret = -EBADF;
        goto error;
    }
    
    mutex_lock(&g_dtesn_instances_mutex);
    instance = g_dtesn_instances[fd];
    if (instance) {
        g_dtesn_instances[fd] = NULL;
        dtesn_instance_get(instance);
    }
    mutex_unlock(&g_dtesn_instances_mutex);
    
    if (!instance || instance->magic != DTESN_INSTANCE_MAGIC) {
        ret = -EBADF;
        goto error;
    }
    
    /* Mark for destruction and release reference */
    instance->is_destroyed = true;
    dtesn_instance_put(instance); /* Remove our reference */
    dtesn_instance_put(instance); /* Remove the initial reference */
    
    atomic64_add(dtesn_get_time_ns() - start_time, &g_global_perf.total_syscall_time_ns);
    return 0;
    
error:
    atomic64_inc(&g_global_perf.error_count);
    return ret;
}

/* Additional syscalls for membrane operations, B-series, and ESN are implemented in their respective modules */

/**
 * dtesn_syscalls_init - Initialize DTESN syscalls module
 * 
 * Returns: 0 on success, negative error code on failure
 */
static int __init dtesn_syscalls_init(void) {
    int ret;
    
    printk(KERN_INFO "DTESN: Initializing comprehensive syscalls interface\n");
    
    /* Initialize global state */
    memset(g_dtesn_instances, 0, sizeof(g_dtesn_instances));
    memset(&g_global_perf, 0, sizeof(g_global_perf));
    
    /* Initialize subsystems */
    ret = dtesn_psystem_init();
    if (ret < 0) {
        printk(KERN_ERR "DTESN: Failed to initialize P-system subsystem\n");
        return ret;
    }
    
    ret = dtesn_bseries_init();
    if (ret < 0) {
        printk(KERN_ERR "DTESN: Failed to initialize B-series subsystem\n");
        goto cleanup_psystem;
    }
    
    ret = dtesn_esn_init();
    if (ret < 0) {
        printk(KERN_ERR "DTESN: Failed to initialize ESN subsystem\n");
        goto cleanup_bseries;
    }
    
    g_dtesn_initialized = true;
    
    printk(KERN_INFO "DTESN: Comprehensive syscalls interface initialized successfully\n");
    return 0;
    
cleanup_bseries:
    dtesn_bseries_shutdown();
cleanup_psystem:
    dtesn_psystem_shutdown();
    return ret;
}

/**
 * dtesn_syscalls_exit - Cleanup DTESN syscalls module
 */
static void __exit dtesn_syscalls_exit(void) {
    int i;
    
    printk(KERN_INFO "DTESN: Cleaning up comprehensive syscalls interface\n");
    
    g_dtesn_initialized = false;
    
    /* Destroy all remaining instances */
    mutex_lock(&g_dtesn_instances_mutex);
    for (i = 0; i < DTESN_MAX_INSTANCES; i++) {
        if (g_dtesn_instances[i]) {
            dtesn_instance_put(g_dtesn_instances[i]);
            g_dtesn_instances[i] = NULL;
        }
    }
    mutex_unlock(&g_dtesn_instances_mutex);
    
    /* Shutdown subsystems */
    dtesn_esn_shutdown();
    dtesn_bseries_shutdown();
    dtesn_psystem_shutdown();
    
    printk(KERN_INFO "DTESN: Comprehensive syscalls interface cleanup complete\n");
}

module_init(dtesn_syscalls_init);
module_exit(dtesn_syscalls_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Echo.Kern Development Team");
MODULE_DESCRIPTION("DTESN Comprehensive System Call Interface");
MODULE_VERSION("1.0");
MODULE_INFO(performance_targets, "syscall:100ns, validation:50ns, copy:8GB/s, error:200ns");
MODULE_INFO(oeis_compliance, "A000081 unlabeled rooted trees");
MODULE_INFO(api_version, "DTESN 1.0");