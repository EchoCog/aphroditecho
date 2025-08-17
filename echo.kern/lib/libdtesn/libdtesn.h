/*
 * libdtesn - User-Space DTESN Programming Library
 * ==============================================
 * 
 * Comprehensive user-space library providing high-level APIs for
 * Deep Tree Echo State Networks (DTESN) application development.
 * 
 * This library provides C/C++ APIs that wrap the DTESN kernel system calls
 * with user-friendly interfaces, error handling, and performance optimization.
 * 
 * Performance Targets:
 * - API call overhead: ≤ 1μs
 * - Library load time: ≤ 100ms  
 * - Memory footprint: ≤ 10MB
 * - Concurrent clients: ≥ 1000
 * 
 * OEIS A000081 Compliance: All tree structures follow unlabeled rooted tree
 * enumeration sequence: 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, ...
 * 
 * Copyright (c) 2024 Echo.Kern Development Team
 * Licensed under GPL-2.0
 */

#ifndef _LIBDTESN_H
#define _LIBDTESN_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Include kernel UAPI definitions */
#include "../../include/uapi/dtesn.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Library version information */
#define LIBDTESN_VERSION_MAJOR    1
#define LIBDTESN_VERSION_MINOR    0
#define LIBDTESN_VERSION_PATCH    0
#define LIBDTESN_VERSION_STRING   "1.0.0"

/* Library configuration constants */
#define DTESN_MAX_CONCURRENT_INSTANCES  1000
#define DTESN_DEFAULT_TIMEOUT_MS        5000
#define DTESN_MAX_ASYNC_OPERATIONS      256

/*
 * DTESN Library Data Types
 * =======================
 */

/* Forward declarations */
typedef struct dtesn_handle dtesn_handle_t;
typedef struct dtesn_async_context dtesn_async_context_t;

/* Library initialization parameters */
typedef struct {
    uint32_t max_instances;      /* Maximum concurrent DTESN instances */
    uint32_t async_queue_size;   /* Asynchronous operation queue size */
    uint32_t worker_threads;     /* Number of worker threads */
    uint32_t flags;              /* Library initialization flags */
} dtesn_lib_config_t;

/* DTESN instance handle (opaque) */
struct dtesn_handle {
    int fd;                      /* Kernel file descriptor */
    uint32_t instance_id;        /* Unique instance identifier */
    struct dtesn_create_params params;  /* Creation parameters */
    uint64_t creation_time_ns;   /* Instance creation timestamp */
    bool is_async;              /* Asynchronous operation mode */
    void *private_data;         /* Private library data */
};

/* Asynchronous operation context */
struct dtesn_async_context {
    uint32_t operation_id;       /* Unique operation identifier */
    uint32_t operation_type;     /* Type of operation */
    bool completed;              /* Operation completion status */
    int result;                  /* Operation result code */
    void *result_data;          /* Result data buffer */
    size_t result_size;         /* Result data size */
    void (*callback)(struct dtesn_async_context *ctx, void *user_data);
    void *user_data;            /* User callback data */
};

/* Performance statistics */
typedef struct {
    uint64_t total_api_calls;           /* Total API calls made */
    uint64_t total_execution_time_ns;   /* Total execution time */
    uint64_t avg_call_overhead_ns;      /* Average call overhead */
    uint64_t min_call_time_ns;          /* Minimum call time */
    uint64_t max_call_time_ns;          /* Maximum call time */
    uint32_t active_instances;          /* Currently active instances */
    uint32_t failed_calls;              /* Number of failed calls */
    uint64_t memory_usage_bytes;        /* Current memory usage */
} dtesn_perf_stats_t;

/*
 * Core Library Functions
 * =====================
 */

/**
 * dtesn_init - Initialize the DTESN user-space library
 * @config: Library configuration parameters (NULL for defaults)
 * 
 * Initializes the DTESN user-space library with specified configuration.
 * Must be called before any other library functions.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_init(const dtesn_lib_config_t *config);

/**
 * dtesn_cleanup - Cleanup and shutdown the DTESN library
 * 
 * Shuts down the library, closes all instances, and frees resources.
 * Should be called before application exit.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_cleanup(void);

/**
 * dtesn_get_version - Get library version information
 * @major: Pointer to store major version number
 * @minor: Pointer to store minor version number
 * @patch: Pointer to store patch version number
 * 
 * Return: Version string
 */
const char *dtesn_get_version(int *major, int *minor, int *patch);

/*
 * Instance Management APIs
 * =======================
 */

/**
 * dtesn_create - Create a new DTESN instance
 * @params: Instance creation parameters
 * @handle: Pointer to store instance handle
 * 
 * Creates a new DTESN instance with specified parameters.
 * The handle must be used for all subsequent operations.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_create(const struct dtesn_create_params *params, dtesn_handle_t **handle);

/**
 * dtesn_destroy - Destroy a DTESN instance
 * @handle: Instance handle to destroy
 * 
 * Destroys the specified DTESN instance and frees all resources.
 * The handle becomes invalid after this call.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_destroy(dtesn_handle_t *handle);

/**
 * dtesn_evolve - Evolve DTESN instance state
 * @handle: Instance handle
 * @input: Input vector
 * @input_size: Input vector size
 * @steps: Number of evolution steps
 * @mode: Evolution mode flags
 * 
 * Evolves the DTESN instance state with given input for specified steps.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_evolve(dtesn_handle_t *handle, const float *input, 
                 uint32_t input_size, uint32_t steps, uint32_t mode);

/**
 * dtesn_get_state - Get current DTESN instance state
 * @handle: Instance handle
 * @state: State structure to fill
 * 
 * Retrieves the current state information of the DTESN instance.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_get_state(dtesn_handle_t *handle, struct dtesn_state_info *state);

/*
 * P-System Membrane Operations APIs
 * ================================
 */

/**
 * dtesn_membrane_create - Create a new P-system membrane
 * @handle: Instance handle
 * @parent_id: Parent membrane ID (0 for root)
 * @membrane_id: Pointer to store new membrane ID
 * 
 * Creates a new P-system membrane within the specified instance.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_membrane_create(dtesn_handle_t *handle, uint32_t parent_id, uint32_t *membrane_id);

/**
 * dtesn_membrane_evolve - Evolve P-system membrane state
 * @handle: Instance handle
 * @membrane_id: Target membrane ID
 * @steps: Number of evolution steps
 * @data: Evolution data buffer
 * @data_size: Data buffer size
 * 
 * Evolves the specified P-system membrane for given number of steps.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_membrane_evolve(dtesn_handle_t *handle, uint32_t membrane_id,
                          uint32_t steps, const void *data, uint32_t data_size);

/**
 * dtesn_membrane_communicate - Inter-membrane communication
 * @handle: Instance handle
 * @source_id: Source membrane ID
 * @target_id: Target membrane ID
 * @message: Message data
 * @message_size: Message size
 * 
 * Facilitates communication between two membranes in the P-system.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_membrane_communicate(dtesn_handle_t *handle, uint32_t source_id,
                               uint32_t target_id, const void *message, uint32_t message_size);

/**
 * dtesn_membrane_validate_oeis - Validate OEIS A000081 compliance for membranes
 * @handle: Instance handle
 * @is_compliant: Pointer to store compliance result
 * 
 * Validates that the current membrane structure follows OEIS A000081.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_membrane_validate_oeis(dtesn_handle_t *handle, bool *is_compliant);

/*
 * B-Series Computation Interface APIs
 * ===================================
 */

/**
 * dtesn_bseries_compute - Compute B-series coefficients
 * @handle: Instance handle
 * @order: Computation order (1-10)
 * @coefficients: Input coefficients array
 * @coeff_count: Number of coefficients
 * @result: Output buffer for results
 * @result_size: Output buffer size
 * 
 * Computes B-series coefficients for rooted trees up to specified order.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_bseries_compute(dtesn_handle_t *handle, uint32_t order,
                          const double *coefficients, uint32_t coeff_count,
                          double *result, uint32_t result_size);

/**
 * dtesn_bseries_validate_oeis - Validate OEIS A000081 compliance
 * @handle: Instance handle
 * @order: Order to validate
 * @is_compliant: Pointer to store compliance result
 * 
 * Validates that the current B-series computation follows OEIS A000081.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_bseries_validate_oeis(dtesn_handle_t *handle, uint32_t order, bool *is_compliant);

/**
 * dtesn_bseries_get_tree_count - Get number of trees for given order
 * @order: B-series order
 * @tree_count: Pointer to store tree count
 * 
 * Gets the expected number of rooted trees for the given order from OEIS A000081.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_bseries_get_tree_count(uint32_t order, uint32_t *tree_count);

/*
 * ESN Reservoir Management APIs
 * =============================
 */

/**
 * dtesn_esn_update - Update ESN reservoir state
 * @handle: Instance handle
 * @input: Input vector
 * @input_size: Input vector size
 * @state: Current state vector (modified)
 * @state_size: State vector size
 * 
 * Updates the Echo State Network reservoir state with new input.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_esn_update(dtesn_handle_t *handle, const float *input, uint32_t input_size,
                     float *state, uint32_t state_size);

/**
 * dtesn_esn_train - Train ESN output weights
 * @handle: Instance handle
 * @input_data: Training input data matrix
 * @target_data: Training target data matrix
 * @samples: Number of training samples
 * @input_dim: Input dimension
 * @output_dim: Output dimension
 * 
 * Trains the ESN readout weights using ridge regression.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_esn_train(dtesn_handle_t *handle, const float *input_data,
                    const float *target_data, uint32_t samples,
                    uint32_t input_dim, uint32_t output_dim);

/**
 * dtesn_esn_predict - Generate ESN predictions
 * @handle: Instance handle
 * @input: Input vector
 * @input_size: Input vector size
 * @output: Output buffer
 * @output_size: Output buffer size
 * 
 * Generates predictions using the trained ESN.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_esn_predict(dtesn_handle_t *handle, const float *input, uint32_t input_size,
                      float *output, uint32_t output_size);

/**
 * dtesn_esn_get_reservoir_info - Get ESN reservoir information
 * @handle: Instance handle
 * @neuron_count: Pointer to store neuron count
 * @spectral_radius: Pointer to store spectral radius
 * @connectivity: Pointer to store connectivity
 * 
 * Retrieves information about the ESN reservoir configuration.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_esn_get_reservoir_info(dtesn_handle_t *handle, uint32_t *neuron_count,
                                 float *spectral_radius, float *connectivity);

/**
 * dtesn_esn_get_memory_usage - Get ESN memory usage
 * @handle: Instance handle
 * @bytes_used: Pointer to store memory usage in bytes
 * 
 * Retrieves the current memory usage of the ESN.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_esn_get_memory_usage(dtesn_handle_t *handle, size_t *bytes_used);

/*
 * Hardware Acceleration APIs
 * ==========================
 */

/**
 * dtesn_hardware_accel - Enable hardware acceleration
 * @handle: Instance handle
 * @accel_type: Acceleration type flags
 * @device_id: Hardware device ID (optional)
 * 
 * Enables hardware acceleration for DTESN operations.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_hardware_accel(dtesn_handle_t *handle, uint32_t accel_type, uint32_t device_id);

/**
 * dtesn_hardware_get_devices - Get available hardware devices
 * @devices: Buffer to store device information
 * @max_devices: Maximum number of devices to return
 * @device_count: Pointer to store actual device count
 * 
 * Retrieves information about available hardware acceleration devices.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_hardware_get_devices(struct dtesn_device_info *devices, 
                               uint32_t max_devices, uint32_t *device_count);

/*
 * Performance Monitoring APIs
 * ===========================
 */

/**
 * dtesn_get_performance_stats - Get performance statistics
 * @handle: Instance handle (NULL for global stats)
 * @stats: Structure to store performance statistics
 * 
 * Retrieves performance statistics for the specified instance or globally.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_get_performance_stats(dtesn_handle_t *handle, dtesn_perf_stats_t *stats);

/**
 * dtesn_reset_performance_stats - Reset performance counters
 * @handle: Instance handle (NULL for global reset)
 * 
 * Resets performance counters for the specified instance or globally.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_reset_performance_stats(dtesn_handle_t *handle);

/*
 * Asynchronous Operation APIs
 * ===========================
 */

/**
 * dtesn_async_evolve - Asynchronous evolution operation
 * @handle: Instance handle
 * @input: Input vector
 * @input_size: Input vector size
 * @steps: Number of evolution steps
 * @callback: Completion callback function
 * @user_data: User callback data
 * @ctx: Pointer to store async context
 * 
 * Initiates asynchronous evolution operation.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_async_evolve(dtesn_handle_t *handle, const float *input, uint32_t input_size,
                       uint32_t steps, void (*callback)(dtesn_async_context_t *, void *),
                       void *user_data, dtesn_async_context_t **ctx);

/**
 * dtesn_async_wait - Wait for asynchronous operation completion
 * @ctx: Async context
 * @timeout_ms: Timeout in milliseconds (0 for infinite)
 * 
 * Waits for the specified asynchronous operation to complete.
 * 
 * Return: 0 on success, negative error code on failure/timeout
 */
int dtesn_async_wait(dtesn_async_context_t *ctx, uint32_t timeout_ms);

/**
 * dtesn_async_cancel - Cancel asynchronous operation
 * @ctx: Async context
 * 
 * Attempts to cancel the specified asynchronous operation.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_async_cancel(dtesn_async_context_t *ctx);

/*
 * Error Handling and Utilities
 * ============================
 */

/**
 * dtesn_strerror - Get error string for DTESN error code
 * @error: Error code
 * 
 * Returns human-readable error message for the given error code.
 * 
 * Return: Error message string
 */
const char *dtesn_strerror(int error);

/**
 * dtesn_get_last_error - Get last error code for current thread
 * 
 * Returns the last error code that occurred in the current thread.
 * 
 * Return: Last error code
 */
int dtesn_get_last_error(void);

/**
 * dtesn_set_debug_level - Set debug output level
 * @level: Debug level (0=none, 1=errors, 2=warnings, 3=info, 4=debug)
 * 
 * Sets the debug output level for library diagnostics.
 * 
 * Return: Previous debug level
 */
int dtesn_set_debug_level(int level);

#ifdef __cplusplus
}
#endif

#endif /* _LIBDTESN_H */