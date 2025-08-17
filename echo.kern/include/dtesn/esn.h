/*
 * DTESN Echo State Network Reservoir Computing Module
 * ==================================================
 * 
 * Deep Tree Echo State Networks (DTESN) ESN implementation providing
 * real-time reservoir computing with hardware optimization and sparse
 * matrix operations for neuromorphic computing applications.
 * 
 * Performance Requirements:
 * - State update: ≤ 1ms
 * - Matrix multiply: ≤ 500μs
 * - Memory bandwidth: ≥ 10GB/s
 * - Sparsity efficiency: ≥ 90%
 * 
 * Reservoir Architecture:
 * - Recurrent neural network with fixed random weights
 * - Sparse connectivity for efficiency
 * - Adaptive spectral radius control
 * - Hardware acceleration hooks
 * - OEIS A000081 compliant topology
 */

#ifndef DTESN_ESN_H
#define DTESN_ESN_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ESN configuration constants */
#define DTESN_ESN_MAX_RESERVOIR_SIZE    10000   /* Maximum reservoir neurons */
#define DTESN_ESN_MAX_INPUT_SIZE        1000    /* Maximum input dimension */
#define DTESN_ESN_MAX_OUTPUT_SIZE       1000    /* Maximum output dimension */
#define DTESN_ESN_MAX_CONNECTIONS       1000000 /* Maximum sparse connections */
#define DTESN_ESN_DEFAULT_SPARSITY      0.1     /* Default connectivity (10%) */

/* Performance thresholds (microseconds) */
#define DTESN_ESN_STATE_UPDATE_THRESHOLD_US     1000    /* ≤ 1ms state update */
#define DTESN_ESN_MATRIX_MULT_THRESHOLD_US      500     /* ≤ 500μs matrix multiply */
#define DTESN_ESN_MEMORY_BANDWIDTH_GBPS         10      /* ≥ 10GB/s memory bandwidth */
#define DTESN_ESN_SPARSITY_EFFICIENCY_PCT       90      /* ≥ 90% sparsity efficiency */

/* OEIS A000081 sequence for reservoir topology validation */
#define DTESN_ESN_A000081_MAX_DEPTH 12
#define DTESN_ESN_A000081_SEQUENCE \
    { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766 }

/* ESN reservoir states */
typedef enum {
    DTESN_ESN_STATE_UNINITIALIZED = 0,  /* Not initialized */
    DTESN_ESN_STATE_INITIALIZED = 1,    /* Ready for use */
    DTESN_ESN_STATE_RUNNING = 2,        /* Active processing */
    DTESN_ESN_STATE_PAUSED = 3,         /* Temporarily paused */
    DTESN_ESN_STATE_ERROR = 4           /* Error state */
} dtesn_esn_state_t;

/* Hardware acceleration types */
typedef enum {
    DTESN_ESN_ACCEL_NONE = 0,          /* No acceleration */
    DTESN_ESN_ACCEL_SIMD = 1,          /* SIMD vectorization */
    DTESN_ESN_ACCEL_GPU = 2,           /* GPU acceleration */
    DTESN_ESN_ACCEL_FPGA = 3,          /* FPGA acceleration */
    DTESN_ESN_ACCEL_NEUROMORPHIC = 4   /* Neuromorphic hardware */
} dtesn_esn_accel_type_t;

/* Activation function types */
typedef enum {
    DTESN_ESN_ACTIVATION_TANH = 0,     /* Hyperbolic tangent */
    DTESN_ESN_ACTIVATION_SIGMOID = 1,  /* Sigmoid function */
    DTESN_ESN_ACTIVATION_RELU = 2,     /* Rectified linear unit */
    DTESN_ESN_ACTIVATION_LINEAR = 3    /* Linear activation */
} dtesn_esn_activation_t;

/* Sparse matrix structure for efficient storage */
typedef struct dtesn_esn_sparse_matrix {
    uint32_t rows;                     /* Number of rows */
    uint32_t cols;                     /* Number of columns */
    uint32_t nnz;                      /* Number of non-zero elements */
    uint32_t *row_ptr;                 /* Row pointers (CSR format) */
    uint32_t *col_idx;                 /* Column indices */
    float *values;                     /* Non-zero values */
    float sparsity;                    /* Sparsity ratio (0.0-1.0) */
    bool is_symmetric;                 /* Symmetry flag for optimization */
} dtesn_esn_sparse_matrix_t;

/* ESN reservoir configuration */
typedef struct dtesn_esn_config {
    uint32_t reservoir_size;           /* Number of reservoir neurons */
    uint32_t input_size;               /* Input vector dimension */
    uint32_t output_size;              /* Output vector dimension */
    
    /* Reservoir dynamics parameters */
    float spectral_radius;             /* Network stability (0.0-1.0) */
    float leak_rate;                   /* Temporal dynamics (0.0-1.0) */
    float input_scaling;               /* Input signal scaling */
    float bias_scaling;                /* Bias term scaling */
    float noise_level;                 /* Internal noise level */
    
    /* Network topology */
    float connectivity;                /* Connection probability (0.0-1.0) */
    uint32_t input_connectivity;       /* Input connections per neuron */
    bool use_bias;                     /* Enable bias terms */
    dtesn_esn_activation_t activation; /* Activation function */
    
    /* Performance settings */
    dtesn_esn_accel_type_t accel_type; /* Hardware acceleration */
    bool use_sparse_matrices;          /* Enable sparse storage */
    uint32_t thread_count;             /* Parallel processing threads */
    
    /* DTESN integration */
    bool oeis_compliance;              /* Enforce OEIS A000081 topology */
    uint32_t tree_depth;               /* Maximum tree depth */
    
} dtesn_esn_config_t;

/* ESN reservoir structure */
typedef struct dtesn_esn_reservoir {
    uint32_t reservoir_id;             /* Unique reservoir identifier */
    char name[64];                     /* Human-readable name */
    dtesn_esn_config_t config;         /* Configuration parameters */
    dtesn_esn_state_t state;           /* Current operational state */
    
    /* Network matrices */
    dtesn_esn_sparse_matrix_t *W_res;  /* Reservoir weight matrix */
    dtesn_esn_sparse_matrix_t *W_in;   /* Input weight matrix */
    float *W_out;                      /* Output weight matrix (dense) */
    float *bias;                       /* Bias vector */
    
    /* State vectors */
    float *x_current;                  /* Current reservoir state */
    float *x_previous;                 /* Previous reservoir state */
    float *u_current;                  /* Current input vector */
    float *y_current;                  /* Current output vector */
    
    /* Adaptation state */
    float current_spectral_radius;     /* Adaptive spectral radius */
    uint64_t adaptation_step;          /* Adaptation step counter */
    float adaptation_rate;             /* Adaptation learning rate */
    
    /* Performance monitoring */
    uint64_t total_updates;            /* Total state updates */
    uint64_t total_update_time_ns;     /* Total update time */
    uint64_t avg_update_time_ns;       /* Average update time */
    uint64_t max_update_time_ns;       /* Maximum update time */
    float memory_bandwidth_gbps;       /* Current memory bandwidth */
    float sparsity_efficiency;         /* Current sparsity efficiency */
    
    /* Hardware acceleration state */
    void *accel_context;               /* Hardware-specific context */
    bool accel_available;              /* Hardware acceleration available */
    
    /* Thread synchronization */
    pthread_mutex_t state_lock;        /* State vector lock */
    pthread_cond_t update_cond;        /* Update synchronization */
    
    /* Memory management */
    void *memory_pool;                 /* Dedicated memory pool */
    size_t memory_pool_size;           /* Pool size */
    size_t memory_used;                /* Currently used memory */
    
    /* Validation state */
    bool is_validated;                 /* OEIS A000081 validated */
    uint64_t creation_time_ns;         /* Creation timestamp */
    uint64_t last_update_ns;           /* Last update timestamp */
    
} dtesn_esn_reservoir_t;

/* Performance statistics structure */
typedef struct dtesn_esn_stats {
    uint64_t total_state_updates;      /* Total state updates */
    uint64_t total_matrix_multiplies;  /* Total matrix multiplications */
    uint64_t total_sparse_operations;  /* Total sparse operations */
    
    uint64_t avg_state_update_time_ns; /* Average state update time */
    uint64_t max_state_update_time_ns; /* Maximum state update time */
    uint64_t avg_matrix_mult_time_ns;  /* Average matrix multiply time */
    uint64_t max_matrix_mult_time_ns;  /* Maximum matrix multiply time */
    
    float avg_memory_bandwidth_gbps;   /* Average memory bandwidth */
    float peak_memory_bandwidth_gbps;  /* Peak memory bandwidth */
    float avg_sparsity_efficiency;     /* Average sparsity efficiency */
    
    uint32_t hardware_accel_usage_pct; /* Hardware acceleration usage */
    uint32_t cache_hit_rate_pct;       /* Memory cache hit rate */
    
    bool state_threshold_met;          /* ≤1ms state update constraint */
    bool matrix_threshold_met;         /* ≤500μs matrix multiply constraint */
    bool bandwidth_threshold_met;      /* ≥10GB/s bandwidth constraint */
    bool sparsity_threshold_met;       /* ≥90% sparsity efficiency constraint */
    
} dtesn_esn_stats_t;

/* Hardware acceleration context */
typedef struct dtesn_esn_accel_context {
    dtesn_esn_accel_type_t type;       /* Acceleration type */
    void *device_context;              /* Device-specific context */
    uint32_t device_id;                /* Device identifier */
    char device_name[64];              /* Device name */
    size_t device_memory_size;         /* Available device memory */
    bool is_available;                 /* Device availability */
    float performance_factor;          /* Performance multiplier */
} dtesn_esn_accel_context_t;

/* Core ESN management functions */

/**
 * dtesn_esn_init - Initialize ESN reservoir subsystem
 * 
 * Initializes the ESN reservoir computing subsystem with memory pools,
 * hardware acceleration detection, and performance monitoring.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_init(void);

/**
 * esn_reservoir_init - Create and initialize ESN reservoir
 * @config: Reservoir configuration parameters
 * @name: Human-readable reservoir name
 * 
 * Creates a new ESN reservoir with specified configuration, allocates
 * memory, initializes weight matrices, and validates OEIS A000081 compliance.
 * 
 * Returns: Pointer to reservoir structure, NULL on failure
 */
dtesn_esn_reservoir_t *esn_reservoir_init(const dtesn_esn_config_t *config, 
                                          const char *name);

/**
 * dtesn_esn_reservoir_destroy - Destroy reservoir and free resources
 * @reservoir: Reservoir to destroy
 * 
 * Cleanly shuts down the reservoir, releases hardware acceleration
 * resources, and frees all associated memory.
 */
void dtesn_esn_reservoir_destroy(dtesn_esn_reservoir_t *reservoir);

/* Core reservoir operations */

/**
 * esn_state_update - Update reservoir state with new input
 * @reservoir: Target reservoir
 * @input: Input vector
 * @input_size: Size of input vector
 * 
 * Updates the reservoir state using the recurrent dynamics equation:
 * x(t+1) = (1-α)x(t) + α·tanh(W_in·u(t+1) + W_res·x(t) + bias)
 * Enforces ≤1ms timing constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int esn_state_update(dtesn_esn_reservoir_t *reservoir, 
                     const float *input, 
                     uint32_t input_size);

/**
 * dtesn_esn_compute_output - Compute output from current reservoir state
 * @reservoir: Source reservoir
 * @output: Output vector buffer
 * @output_size: Size of output vector
 * 
 * Computes output using trained output weights: y(t) = W_out·x(t)
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_compute_output(dtesn_esn_reservoir_t *reservoir,
                            float *output,
                            uint32_t output_size);

/* Sparse matrix operations */

/**
 * esn_sparse_multiply - Sparse matrix-vector multiplication
 * @matrix: Sparse matrix in CSR format
 * @input: Input vector
 * @output: Output vector
 * 
 * Performs efficient sparse matrix-vector multiplication using
 * optimized CSR format. Enforces ≤500μs timing constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int esn_sparse_multiply(const dtesn_esn_sparse_matrix_t *matrix,
                       const float *input,
                       float *output);

/**
 * dtesn_esn_sparse_matrix_create - Create sparse matrix
 * @rows: Number of rows
 * @cols: Number of columns
 * @sparsity: Target sparsity ratio
 * 
 * Creates a sparse matrix structure with specified dimensions
 * and target sparsity for efficient storage and computation.
 * 
 * Returns: Pointer to sparse matrix, NULL on failure
 */
dtesn_esn_sparse_matrix_t *dtesn_esn_sparse_matrix_create(uint32_t rows,
                                                          uint32_t cols, 
                                                          float sparsity);

/**
 * dtesn_esn_sparse_matrix_destroy - Destroy sparse matrix
 * @matrix: Matrix to destroy
 * 
 * Frees all memory associated with the sparse matrix.
 */
void dtesn_esn_sparse_matrix_destroy(dtesn_esn_sparse_matrix_t *matrix);

/* Hardware acceleration functions */

/**
 * esn_hardware_accel - Enable hardware acceleration
 * @reservoir: Target reservoir
 * @accel_type: Type of acceleration to use
 * 
 * Initializes and enables hardware acceleration for reservoir
 * operations using available accelerators (SIMD, GPU, FPGA).
 * 
 * Returns: 0 on success, negative error code on failure
 */
int esn_hardware_accel(dtesn_esn_reservoir_t *reservoir,
                      dtesn_esn_accel_type_t accel_type);

/**
 * dtesn_esn_detect_hardware - Detect available acceleration hardware
 * @contexts: Array to fill with available contexts
 * @max_contexts: Maximum number of contexts to detect
 * 
 * Detects and catalogs available hardware acceleration devices.
 * 
 * Returns: Number of contexts found, negative on error
 */
int dtesn_esn_detect_hardware(dtesn_esn_accel_context_t *contexts,
                             uint32_t max_contexts);

/* Adaptive scaling functions */

/**
 * esn_adaptive_scale - Adaptive reservoir parameter scaling
 * @reservoir: Target reservoir
 * @performance_metric: Current performance metric
 * @target_metric: Target performance metric
 * 
 * Adaptively adjusts reservoir parameters (spectral radius, leak rate)
 * based on performance feedback to maintain optimal dynamics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int esn_adaptive_scale(dtesn_esn_reservoir_t *reservoir,
                      float performance_metric,
                      float target_metric);

/**
 * dtesn_esn_auto_tune - Automatic parameter tuning
 * @reservoir: Target reservoir
 * @training_data: Training input data
 * @target_data: Target output data
 * @num_samples: Number of training samples
 * 
 * Automatically tunes reservoir parameters using training data
 * to optimize performance metrics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_auto_tune(dtesn_esn_reservoir_t *reservoir,
                       const float **training_data,
                       const float **target_data,
                       uint32_t num_samples);

/* Validation and monitoring functions */

/**
 * dtesn_esn_validate_a000081 - Validate OEIS A000081 compliance
 * @reservoir: Reservoir to validate
 * 
 * Validates that the reservoir topology follows the OEIS A000081
 * unlabeled rooted tree enumeration for correct DTESN structure.
 * 
 * Returns: true if compliant, false otherwise
 */
bool dtesn_esn_validate_a000081(dtesn_esn_reservoir_t *reservoir);

/**
 * dtesn_esn_get_stats - Get comprehensive performance statistics
 * @reservoir: Reservoir to analyze
 * @stats: Statistics structure to fill
 * 
 * Retrieves detailed performance metrics including timing analysis,
 * memory bandwidth, sparsity efficiency, and hardware utilization.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_get_stats(dtesn_esn_reservoir_t *reservoir,
                       dtesn_esn_stats_t *stats);

/**
 * dtesn_esn_check_stability - Check reservoir stability
 * @reservoir: Reservoir to check
 * @stability_metric: Output stability metric
 * 
 * Analyzes reservoir dynamics to ensure stability and proper
 * echo state property maintenance.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_check_stability(dtesn_esn_reservoir_t *reservoir,
                             float *stability_metric);

/* Utility functions */

/**
 * dtesn_esn_config_default - Get default ESN configuration
 * @config: Configuration structure to fill
 * 
 * Fills configuration structure with sensible default values
 * for typical ESN applications.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_config_default(dtesn_esn_config_t *config);

/**
 * dtesn_esn_save_state - Save reservoir state to buffer
 * @reservoir: Source reservoir
 * @buffer: Buffer to save state
 * @buffer_size: Size of buffer
 * 
 * Serializes reservoir state for checkpointing or transfer.
 * 
 * Returns: Number of bytes written, negative on error
 */
int dtesn_esn_save_state(dtesn_esn_reservoir_t *reservoir,
                        void *buffer,
                        size_t buffer_size);

/**
 * dtesn_esn_load_state - Load reservoir state from buffer
 * @reservoir: Target reservoir
 * @buffer: Buffer containing state
 * @buffer_size: Size of buffer
 * 
 * Deserializes reservoir state from saved buffer.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_esn_load_state(dtesn_esn_reservoir_t *reservoir,
                        const void *buffer,
                        size_t buffer_size);

/**
 * dtesn_esn_shutdown - Shutdown ESN reservoir subsystem
 * 
 * Cleanly shuts down the ESN subsystem, releasing all resources
 * and stopping background threads.
 */
void dtesn_esn_shutdown(void);

/* Error codes specific to ESN operations */
#define DTESN_ESN_ENOMEM         -30   /* Out of memory */
#define DTESN_ESN_EINVAL         -31   /* Invalid parameters */
#define DTESN_ESN_ENOTFOUND      -32   /* Reservoir not found */
#define DTESN_ESN_ELATENCY       -33   /* Timing constraint violated */
#define DTESN_ESN_EVALIDATION    -34   /* OEIS A000081 validation failed */
#define DTESN_ESN_ESTABILITY     -35   /* Reservoir stability failed */
#define DTESN_ESN_ECOMPUTATION   -36   /* Computation failed */
#define DTESN_ESN_ESPARSE        -37   /* Sparse operation failed */
#define DTESN_ESN_EHARDWARE      -38   /* Hardware acceleration failed */
#define DTESN_ESN_EADAPTATION    -39   /* Adaptive scaling failed */

#ifdef __cplusplus
}
#endif

#endif /* DTESN_ESN_H */