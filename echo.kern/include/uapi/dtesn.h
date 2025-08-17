/*
 * DTESN User-Space API Definitions
 * ===============================
 * 
 * User-space interface for Deep Tree Echo State Networks (DTESN) system calls.
 * Provides comprehensive API for creating and managing DTESN instances, membrane
 * operations, B-series computations, and ESN reservoir state management.
 * 
 * Performance Targets:
 * - syscall overhead: ≤ 100ns
 * - parameter validation: ≤ 50ns  
 * - data copy: ≥ 8GB/s
 * - error path: ≤ 200ns
 * 
 * OEIS A000081 Compliance: All tree structures follow unlabeled rooted tree
 * enumeration sequence: 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, ...
 */

#ifndef _UAPI_DTESN_H
#define _UAPI_DTESN_H

#include <linux/types.h>
#include <linux/ioctl.h>

#ifdef __cplusplus
extern "C" {
#endif

/* DTESN system call numbers - will be assigned by kernel */
#define __NR_sys_dtesn_create       600
#define __NR_sys_dtesn_evolve       601  
#define __NR_sys_dtesn_get_state    602
#define __NR_sys_dtesn_destroy      603
#define __NR_sys_membrane_op        604
#define __NR_sys_bseries_compute    605
#define __NR_sys_esn_update         606

/* DTESN configuration constants */
#define DTESN_MAX_DEPTH             16      /* Maximum tree depth */
#define DTESN_MAX_ORDER             10      /* Maximum B-series order */
#define DTESN_MAX_NEURONS           10000   /* Maximum ESN neurons */
#define DTESN_MAX_MEMBRANES         1024    /* Maximum P-system membranes */
#define DTESN_MAX_INPUT_SIZE        1000    /* Maximum input dimension */
#define DTESN_MAX_OUTPUT_SIZE       1000    /* Maximum output dimension */
#define DTESN_MAX_LABEL_LEN         64      /* Maximum label string length */

/* DTESN creation flags */
#define DTESN_CREATE_DEFAULT        0x0000  /* Default configuration */
#define DTESN_CREATE_HARDWARE_ACCEL 0x0001  /* Enable hardware acceleration */
#define DTESN_CREATE_HIGH_PRECISION 0x0002  /* Use double precision floats */
#define DTESN_CREATE_SPARSE_MODE    0x0004  /* Optimize for sparse operations */
#define DTESN_CREATE_REAL_TIME      0x0008  /* Enable real-time constraints */
#define DTESN_CREATE_VALIDATE_OEIS  0x0010  /* Validate OEIS A000081 compliance */

/* DTESN evolution modes */
#define DTESN_EVOLVE_SYNCHRONOUS    0x0000  /* Synchronous evolution */
#define DTESN_EVOLVE_ASYNCHRONOUS   0x0001  /* Asynchronous evolution */
#define DTESN_EVOLVE_CONTINUOUS     0x0002  /* Continuous evolution mode */
#define DTESN_EVOLVE_STEP_BY_STEP   0x0004  /* Single-step evolution */

/* Membrane operation types */
#define DTESN_MEMBRANE_CREATE       1       /* Create new membrane */
#define DTESN_MEMBRANE_EVOLVE       2       /* Evolve membrane state */
#define DTESN_MEMBRANE_COMMUNICATE  3       /* Inter-membrane communication */
#define DTESN_MEMBRANE_DISSOLVE     4       /* Dissolve membrane */
#define DTESN_MEMBRANE_DIVIDE       5       /* Divide membrane */

/* Error codes specific to DTESN operations */
#define DTESN_SUCCESS               0       /* Operation successful */
#define DTESN_ERROR_INVALID_DEPTH   -1001   /* Invalid tree depth */
#define DTESN_ERROR_INVALID_ORDER   -1002   /* Invalid B-series order */
#define DTESN_ERROR_OEIS_VIOLATION  -1003   /* OEIS A000081 violation */
#define DTESN_ERROR_PERFORMANCE     -1004   /* Performance target missed */
#define DTESN_ERROR_HARDWARE        -1005   /* Hardware acceleration error */
#define DTESN_ERROR_MEMBRANE        -1006   /* Membrane operation error */
#define DTESN_ERROR_ESN             -1007   /* ESN operation error */
#define DTESN_ERROR_BSERIES         -1008   /* B-series computation error */

/* DTESN instance creation parameters */
struct dtesn_create_params {
    __u32 depth;                    /* Tree depth (1-16) */
    __u32 max_order;                /* Maximum B-series order (1-10) */
    __u32 neuron_count;             /* ESN reservoir neurons */
    __u32 membrane_count;           /* P-system membranes */
    __u32 input_dim;                /* Input dimension */
    __u32 output_dim;               /* Output dimension */
    __u32 flags;                    /* Creation flags */
    char label[DTESN_MAX_LABEL_LEN]; /* Human-readable label */
};

/* DTESN evolution parameters */
struct dtesn_evolve_params {
    __s32 fd;                       /* DTESN instance file descriptor */
    const float *input;             /* Input vector */
    __u32 input_size;               /* Input vector size */
    __u32 steps;                    /* Number of evolution steps */
    __u32 mode;                     /* Evolution mode flags */
    __u64 timeout_ns;               /* Maximum execution time (ns) */
};

/* DTESN state information */
struct dtesn_state_info {
    __u32 depth;                    /* Current tree depth */
    __u32 active_membranes;         /* Active membrane count */
    __u32 total_neurons;            /* Total ESN neurons */
    __u32 evolution_steps;          /* Total evolution steps */
    __u64 creation_time_ns;         /* Instance creation time */
    __u64 last_update_ns;           /* Last state update time */
    double spectral_radius;         /* Current ESN spectral radius */
    double membrane_activity;       /* Membrane activity level */
    __u32 oeis_compliance;          /* OEIS A000081 compliance flag */
    __u32 performance_violations;   /* Performance constraint violations */
};

/* Membrane operation parameters */
struct dtesn_membrane_op_params {
    __s32 fd;                       /* DTESN instance file descriptor */
    __u32 operation;                /* Operation type */
    __u32 membrane_id;              /* Target membrane ID */
    __u32 parent_id;                /* Parent membrane ID (for create) */
    __u32 steps;                    /* Evolution steps (for evolve) */
    const void *data;               /* Operation-specific data */
    __u32 data_size;                /* Data size */
};

/* Membrane operation parameters */
struct dtesn_membrane_params {
    __s32 fd;                       /* DTESN instance file descriptor */
    __u32 operation;                /* Membrane operation type */
    __u32 membrane_id;              /* Target membrane ID */
    __u32 parent_id;                /* Parent membrane ID (for create) */
    __u32 steps;                    /* Evolution steps (for evolve) */
    const void *data;               /* Operation-specific data */
    __u32 data_size;                /* Data size */
};

/* B-series computation parameters */
struct dtesn_bseries_params {
    __s32 fd;                       /* DTESN instance file descriptor */
    __u32 order;                    /* Computation order (1-10) */
    const double *coefficients;     /* Input coefficients */
    __u32 coeff_count;              /* Number of coefficients */
    double *result;                 /* Output buffer */
    __u32 result_size;              /* Output buffer size */
    __u32 tree_count;               /* Number of trees to compute */
};

/* ESN update parameters */
struct dtesn_esn_params {
    __s32 fd;                       /* DTESN instance file descriptor */
    const float *input;             /* Input vector */
    __u32 input_size;               /* Input vector size */
    float *state;                   /* Current state vector */
    __u32 state_size;               /* State vector size */
    float *output;                  /* Output vector */
    __u32 output_size;              /* Output vector size */
    float learning_rate;            /* Learning rate for training */
    float regularization;           /* Regularization parameter */
};

/* Hardware device information */
struct dtesn_device_info {
    __u32 device_id;                /* Unique device identifier */
    __u32 device_type;              /* Device type (GPU, FPGA, etc.) */
    __u32 compute_units;            /* Number of compute units */
    __u64 memory_size_bytes;        /* Available memory in bytes */
    __u32 max_frequency_mhz;        /* Maximum operating frequency */
    __u32 capabilities;             /* Device capability flags */
    char name[64];                  /* Human-readable device name */
    char vendor[32];                /* Vendor name */
};

/* Performance metrics structure */
struct dtesn_performance_metrics {
    __u64 syscall_overhead_ns;      /* Average syscall overhead */
    __u64 validation_time_ns;       /* Parameter validation time */
    __u64 copy_bandwidth_bps;       /* Data copy bandwidth */
    __u64 error_path_time_ns;       /* Error handling time */
    __u64 evolution_time_ns;        /* Average evolution time */
    __u64 membrane_op_time_ns;      /* Average membrane operation time */
    __u64 bseries_comp_time_ns;     /* Average B-series computation time */
    __u64 esn_update_time_ns;       /* Average ESN update time */
    __u32 cache_hits;               /* Cache hit count */
    __u32 cache_misses;             /* Cache miss count */
    __u32 hw_accelerations;         /* Hardware acceleration usage */
};

/* IOCTL commands for advanced operations */
#define DTESN_IOC_MAGIC             'D'
#define DTESN_IOC_GET_METRICS       _IOR(DTESN_IOC_MAGIC, 1, struct dtesn_performance_metrics)
#define DTESN_IOC_SET_DEBUG         _IOW(DTESN_IOC_MAGIC, 2, __u32)
#define DTESN_IOC_VALIDATE_OEIS     _IO(DTESN_IOC_MAGIC, 3)
#define DTESN_IOC_RESET_STATS       _IO(DTESN_IOC_MAGIC, 4)
#define DTESN_IOC_GET_VERSION       _IOR(DTESN_IOC_MAGIC, 5, __u32)

/* DTESN API version information */
#define DTESN_API_VERSION_MAJOR     1
#define DTESN_API_VERSION_MINOR     0
#define DTESN_API_VERSION_PATCH     0
#define DTESN_API_VERSION           ((DTESN_API_VERSION_MAJOR << 16) | \
                                    (DTESN_API_VERSION_MINOR << 8) | \
                                    DTESN_API_VERSION_PATCH)

/* Utility macros for parameter validation */
#define DTESN_VALID_DEPTH(d)        ((d) >= 1 && (d) <= DTESN_MAX_DEPTH)
#define DTESN_VALID_ORDER(o)        ((o) >= 1 && (o) <= DTESN_MAX_ORDER) 
#define DTESN_VALID_NEURONS(n)      ((n) >= 1 && (n) <= DTESN_MAX_NEURONS)
#define DTESN_VALID_MEMBRANES(m)    ((m) >= 1 && (m) <= DTESN_MAX_MEMBRANES)
#define DTESN_VALID_INPUT_SIZE(s)   ((s) >= 1 && (s) <= DTESN_MAX_INPUT_SIZE)
#define DTESN_VALID_OUTPUT_SIZE(s)  ((s) >= 1 && (s) <= DTESN_MAX_OUTPUT_SIZE)

/* OEIS A000081 validation macro */
#define DTESN_OEIS_A000081_SEQUENCE_INIT \
    { 0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973, 86810 }

#ifdef __cplusplus
}
#endif

#endif /* _UAPI_DTESN_H */