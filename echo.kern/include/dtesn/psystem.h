/*
 * DTESN P-System Membrane Computing Kernel Module
 * ===============================================
 * 
 * Deep Tree Echo State Networks (DTESN) P-System implementation providing
 * real-time membrane computing with hierarchical organization based on
 * OEIS A000081 rooted tree enumeration.
 * 
 * Performance Requirements:
 * - Membrane evolution: ≤ 10μs
 * - Rule application: ≤ 1μs
 * - Communication latency: ≤ 5μs
 * - Parallel efficiency: ≥ 85%
 * 
 * System Architecture:
 * - Hierarchical membrane organization
 * - Object multisets with multiplicity tracking
 * - Evolution rules with priority-based execution
 * - Inter-membrane communication protocols
 * - Real-time constraint enforcement
 */

#ifndef DTESN_PSYSTEM_H
#define DTESN_PSYSTEM_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>

#ifdef __cplusplus
extern "C" {
#endif

/* P-System configuration constants */
#define DTESN_PSYSTEM_MAX_MEMBRANES     1024    /* Maximum membranes in system */
#define DTESN_PSYSTEM_MAX_OBJECTS       4096    /* Maximum objects per membrane */
#define DTESN_PSYSTEM_MAX_RULES         256     /* Maximum rules per membrane */
#define DTESN_PSYSTEM_MAX_SYMBOL_LEN    64      /* Maximum object symbol length */
#define DTESN_PSYSTEM_MAX_RULE_LEN      512     /* Maximum rule string length */
#define DTESN_PSYSTEM_MAX_PRIORITY      255     /* Maximum rule priority */

/* Performance thresholds (microseconds) */
#define DTESN_PSYSTEM_EVOLUTION_THRESHOLD_US    10  /* ≤ 10μs membrane evolution */
#define DTESN_PSYSTEM_RULE_THRESHOLD_US         1   /* ≤ 1μs rule application */
#define DTESN_PSYSTEM_COMM_THRESHOLD_US         5   /* ≤ 5μs communication */
#define DTESN_PSYSTEM_PARALLEL_EFFICIENCY       85  /* ≥ 85% parallel efficiency */

/* OEIS A000081 sequence for membrane hierarchy validation */
#define DTESN_PSYSTEM_A000081_MAX_DEPTH 10
#define DTESN_PSYSTEM_A000081_SEQUENCE \
    { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719 }

/* Membrane types based on DTESN hierarchy */
typedef enum {
    DTESN_MEMBRANE_ROOT = 0,
    DTESN_MEMBRANE_TRUNK = 1,
    DTESN_MEMBRANE_BRANCH = 2,
    DTESN_MEMBRANE_LEAF = 3,
    DTESN_MEMBRANE_TERMINAL = 4,
    DTESN_MEMBRANE_SKIN = 5,
    DTESN_MEMBRANE_ELEMENTARY = 6
} dtesn_membrane_type_t;

/* Rule types for P-System operations */
typedef enum {
    DTESN_RULE_EVOLUTION = 0,      /* Object evolution within membrane */
    DTESN_RULE_COMMUNICATION = 1,  /* Inter-membrane object transfer */
    DTESN_RULE_DISSOLUTION = 2,    /* Membrane dissolution */
    DTESN_RULE_DIVISION = 3,       /* Membrane division */
    DTESN_RULE_CREATION = 4,       /* New membrane creation */
    DTESN_RULE_SYMPORT = 5,        /* Synchronized transport */
    DTESN_RULE_ANTIPORT = 6        /* Anti-synchronized transport */
} dtesn_rule_type_t;

/* Execution phases */
typedef enum {
    DTESN_PHASE_INPUT = 0,
    DTESN_PHASE_EVOLUTION = 1,
    DTESN_PHASE_COMMUNICATION = 2,
    DTESN_PHASE_OUTPUT = 3,
    DTESN_PHASE_HALTED = 4
} dtesn_execution_phase_t;

/* Object structure for P-System computations */
typedef struct dtesn_psystem_object {
    char symbol[DTESN_PSYSTEM_MAX_SYMBOL_LEN];  /* Object symbol identifier */
    uint32_t multiplicity;                       /* Object count/multiplicity */
    uint64_t creation_time_ns;                   /* Creation timestamp */
    uint32_t properties;                         /* Property flags/attributes */
    struct dtesn_psystem_object *next;           /* Next object in list */
} dtesn_psystem_object_t;

/* Multiset structure for object collections */
typedef struct dtesn_psystem_multiset {
    dtesn_psystem_object_t *objects;            /* Head of object list */
    uint32_t object_count;                      /* Number of distinct objects */
    uint32_t total_multiplicity;                /* Total object count */
    pthread_mutex_t lock;                       /* Thread synchronization */
} dtesn_psystem_multiset_t;

/* Evolution rule structure */
typedef struct dtesn_psystem_rule {
    uint32_t rule_id;                           /* Unique rule identifier */
    char rule_string[DTESN_PSYSTEM_MAX_RULE_LEN]; /* Human-readable rule */
    dtesn_rule_type_t rule_type;                /* Type of rule operation */
    uint8_t priority;                           /* Rule priority (0-255) */
    
    /* Rule components */
    dtesn_psystem_multiset_t lhs;               /* Left-hand side (consumed) */
    dtesn_psystem_multiset_t rhs;               /* Right-hand side (produced) */
    
    /* Communication targets */
    uint32_t target_membrane_id;                /* Target for communication rules */
    uint32_t source_membrane_id;                /* Source for communication rules */
    
    /* Execution state */
    uint64_t application_count;                 /* Number of applications */
    uint64_t last_applied_ns;                   /* Last application timestamp */
    bool is_applicable;                         /* Current applicability */
    
    struct dtesn_psystem_rule *next;            /* Next rule in list */
} dtesn_psystem_rule_t;

/* Membrane structure */
typedef struct dtesn_psystem_membrane {
    uint32_t membrane_id;                       /* Unique membrane identifier */
    dtesn_membrane_type_t membrane_type;        /* Type of membrane */
    char label[DTESN_PSYSTEM_MAX_SYMBOL_LEN];   /* Human-readable label */
    
    /* Hierarchy relationships */
    uint32_t parent_id;                         /* Parent membrane ID */
    uint32_t *children_ids;                     /* Array of child membrane IDs */
    uint32_t children_count;                    /* Number of children */
    uint32_t children_capacity;                 /* Allocated capacity for children */
    uint32_t depth_level;                       /* Depth in hierarchy tree */
    
    /* P-System computational state */
    dtesn_psystem_multiset_t objects;           /* Current object multiset */
    dtesn_psystem_rule_t *rules;                /* Evolution rules list */
    uint32_t rule_count;                        /* Number of rules */
    
    /* DTESN neuromorphic properties */
    uint32_t neuron_count;                      /* ESN reservoir neurons */
    float spectral_radius;                      /* Network stability parameter */
    float leak_rate;                            /* Temporal dynamics rate */
    float connectivity;                         /* Network sparsity factor */
    
    /* Execution state */
    dtesn_execution_phase_t current_phase;      /* Current execution phase */
    uint64_t evolution_step;                    /* Current evolution step */
    bool is_dissolved;                          /* Dissolution state */
    bool is_active;                             /* Activity state */
    
    /* Performance metrics */
    uint64_t total_evolution_time_ns;           /* Cumulative evolution time */
    uint64_t total_rule_applications;           /* Total rule applications */
    uint64_t total_communications;              /* Total communications */
    
    /* Thread synchronization */
    pthread_mutex_t lock;                       /* Membrane state lock */
    pthread_cond_t evolution_cond;              /* Evolution synchronization */
    
} dtesn_psystem_membrane_t;

/* P-System hierarchy structure */
typedef struct dtesn_psystem {
    char system_name[DTESN_PSYSTEM_MAX_SYMBOL_LEN]; /* System identifier */
    uint32_t system_id;                             /* Unique system ID */
    
    /* Membrane management */
    dtesn_psystem_membrane_t **membranes;           /* Membrane array */
    uint32_t membrane_count;                        /* Number of membranes */
    uint32_t membrane_capacity;                     /* Allocated capacity */
    uint32_t next_membrane_id;                      /* Next available ID */
    uint32_t skin_membrane_id;                      /* Skin membrane ID */
    
    /* Evolution state */
    uint64_t global_evolution_step;                 /* Global step counter */
    dtesn_execution_phase_t global_phase;           /* Global execution phase */
    bool is_halted;                                 /* System halted state */
    
    /* Performance monitoring */
    uint64_t total_system_evolution_time_ns;        /* Total evolution time */
    uint64_t parallel_efficiency_pct;               /* Parallel efficiency */
    
    /* Thread management */
    pthread_mutex_t system_lock;                    /* System-wide lock */
    pthread_t *evolution_threads;                   /* Evolution thread pool */
    uint32_t thread_count;                          /* Number of threads */
    
    /* Memory management */
    void *memory_pool;                              /* Dedicated memory pool */
    size_t memory_pool_size;                        /* Pool size */
    size_t memory_used;                             /* Currently used memory */
    
} dtesn_psystem_t;

/* Performance statistics structure */
typedef struct dtesn_psystem_stats {
    uint64_t total_evolution_time_ns;               /* Total evolution time */
    uint64_t avg_evolution_time_ns;                 /* Average evolution time */
    uint64_t max_evolution_time_ns;                 /* Maximum evolution time */
    uint64_t total_rule_applications;               /* Total rule applications */
    uint64_t avg_rule_time_ns;                      /* Average rule application time */
    uint64_t max_rule_time_ns;                      /* Maximum rule application time */
    uint64_t total_communications;                  /* Total communications */
    uint64_t avg_comm_time_ns;                      /* Average communication time */
    uint64_t max_comm_time_ns;                      /* Maximum communication time */
    uint32_t parallel_efficiency_pct;               /* Parallel efficiency percentage */
    uint32_t active_membranes;                      /* Currently active membranes */
    uint32_t total_objects;                         /* Total objects in system */
    uint32_t total_rules;                           /* Total rules in system */
    bool meets_performance_targets;                 /* All targets satisfied */
} dtesn_psystem_stats_t;

/* Core P-System management functions */

/**
 * dtesn_psystem_init - Initialize P-System kernel module
 * 
 * Initializes the P-System membrane computing subsystem with memory pools,
 * thread management, and performance monitoring.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_psystem_init(void);

/**
 * dtesn_psystem_create - Create a new P-System instance
 * @system_name: Human-readable system identifier
 * @max_membranes: Maximum number of membranes (0 for default)
 * 
 * Creates a new P-System hierarchy with the specified constraints.
 * Allocates memory and initializes thread pools for parallel execution.
 * 
 * Returns: Pointer to system structure, NULL on failure
 */
dtesn_psystem_t *dtesn_psystem_create(const char *system_name, uint32_t max_membranes);

/**
 * dtesn_psystem_destroy - Destroy P-System and free resources
 * @system: P-System to destroy
 * 
 * Cleanly shuts down all evolution threads, frees memory pools,
 * and releases all associated resources.
 */
void dtesn_psystem_destroy(dtesn_psystem_t *system);

/* Membrane management functions */

/**
 * dtesn_membrane_create - Create a new membrane in the system
 * @system: Target P-System
 * @membrane_type: Type of membrane to create
 * @label: Human-readable membrane label
 * @parent_id: Parent membrane ID (0 for root)
 * @neuron_count: Number of ESN neurons
 * 
 * Creates a new membrane with specified properties and adds it to
 * the system hierarchy. Validates OEIS A000081 compliance.
 * 
 * Returns: New membrane ID on success, 0 on failure
 */
uint32_t dtesn_membrane_create(dtesn_psystem_t *system,
                               dtesn_membrane_type_t membrane_type,
                               const char *label,
                               uint32_t parent_id,
                               uint32_t neuron_count);

/**
 * dtesn_membrane_destroy - Destroy membrane and redistribute contents
 * @system: P-System containing the membrane
 * @membrane_id: ID of membrane to destroy
 * 
 * Dissolves the membrane and redistributes its objects to the parent
 * membrane according to P-System dissolution rules.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_membrane_destroy(dtesn_psystem_t *system, uint32_t membrane_id);

/* Object multiset management */

/**
 * dtesn_membrane_add_object - Add object to membrane multiset
 * @system: P-System containing the membrane
 * @membrane_id: Target membrane ID
 * @symbol: Object symbol identifier
 * @multiplicity: Number of objects to add
 * 
 * Adds objects to the membrane's multiset with thread-safe operations.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_membrane_add_object(dtesn_psystem_t *system,
                              uint32_t membrane_id,
                              const char *symbol,
                              uint32_t multiplicity);

/**
 * dtesn_membrane_remove_object - Remove object from membrane multiset
 * @system: P-System containing the membrane
 * @membrane_id: Target membrane ID
 * @symbol: Object symbol identifier
 * @multiplicity: Number of objects to remove
 * 
 * Removes objects from the membrane's multiset. If multiplicity exceeds
 * available objects, removes all available.
 * 
 * Returns: Number of objects actually removed
 */
uint32_t dtesn_membrane_remove_object(dtesn_psystem_t *system,
                                      uint32_t membrane_id,
                                      const char *symbol,
                                      uint32_t multiplicity);

/* Rule management functions */

/**
 * dtesn_membrane_add_rule - Add evolution rule to membrane
 * @system: P-System containing the membrane
 * @membrane_id: Target membrane ID
 * @rule_type: Type of evolution rule
 * @priority: Rule priority (0-255)
 * @rule_string: Human-readable rule representation
 * @lhs_objects: Left-hand side object multiset
 * @rhs_objects: Right-hand side object multiset
 * @target_membrane_id: Target for communication rules (0 if not applicable)
 * 
 * Adds an evolution rule to the specified membrane with validation
 * and compilation for efficient execution.
 * 
 * Returns: Rule ID on success, 0 on failure
 */
uint32_t dtesn_membrane_add_rule(dtesn_psystem_t *system,
                                 uint32_t membrane_id,
                                 dtesn_rule_type_t rule_type,
                                 uint8_t priority,
                                 const char *rule_string,
                                 dtesn_psystem_multiset_t *lhs_objects,
                                 dtesn_psystem_multiset_t *rhs_objects,
                                 uint32_t target_membrane_id);

/* Evolution and execution functions */

/**
 * dtesn_membrane_evolve - Evolve single membrane one step
 * @system: P-System containing the membrane
 * @membrane_id: Target membrane ID
 * 
 * Executes one evolution step for the specified membrane, applying
 * all applicable rules according to priority and maximum parallelism.
 * Enforces ≤10μs timing constraint.
 * 
 * Returns: Number of rules applied, negative on error
 */
int dtesn_membrane_evolve(dtesn_psystem_t *system, uint32_t membrane_id);

/**
 * dtesn_system_evolve - Evolve entire P-System one step
 * @system: P-System to evolve
 * 
 * Executes one global evolution step, evolving all active membranes
 * in parallel while maintaining synchronization and communication.
 * 
 * Returns: true if system is still active, false if halted
 */
bool dtesn_system_evolve(dtesn_psystem_t *system);

/**
 * dtesn_membrane_communicate - Transfer objects between membranes
 * @system: P-System containing the membranes
 * @source_id: Source membrane ID
 * @target_id: Target membrane ID
 * @objects: Objects to transfer
 * 
 * Transfers objects between membranes with atomic operations and
 * validation. Enforces ≤5μs timing constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_membrane_communicate(dtesn_psystem_t *system,
                               uint32_t source_id,
                               uint32_t target_id,
                               dtesn_psystem_multiset_t *objects);

/* Validation and monitoring functions */

/**
 * dtesn_psystem_validate_a000081 - Validate OEIS A000081 compliance
 * @system: P-System to validate
 * 
 * Validates that the membrane hierarchy follows the OEIS A000081
 * unlabeled rooted tree enumeration for correct DTESN structure.
 * 
 * Returns: true if compliant, false otherwise
 */
bool dtesn_psystem_validate_a000081(dtesn_psystem_t *system);

/**
 * dtesn_psystem_get_stats - Get comprehensive performance statistics
 * @system: P-System to analyze
 * @stats: Statistics structure to fill
 * 
 * Retrieves detailed performance metrics including timing analysis,
 * rule application counts, and parallel efficiency measurements.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_psystem_get_stats(dtesn_psystem_t *system, dtesn_psystem_stats_t *stats);

/**
 * dtesn_psystem_get_membrane_state - Get current membrane state
 * @system: P-System containing the membrane
 * @membrane_id: Target membrane ID
 * @buffer: Buffer to fill with state information
 * @buffer_size: Size of the buffer
 * 
 * Retrieves the current state of a membrane including objects,
 * rules, and execution state in a serialized format.
 * 
 * Returns: Number of bytes written, negative on error
 */
int dtesn_psystem_get_membrane_state(dtesn_psystem_t *system,
                                     uint32_t membrane_id,
                                     void *buffer,
                                     size_t buffer_size);

/* Utility functions */

/**
 * dtesn_multiset_create - Create empty multiset
 * 
 * Creates and initializes an empty object multiset with
 * proper thread synchronization.
 * 
 * Returns: Pointer to multiset, NULL on failure
 */
dtesn_psystem_multiset_t *dtesn_multiset_create(void);

/**
 * dtesn_multiset_destroy - Destroy multiset and free resources
 * @multiset: Multiset to destroy
 * 
 * Frees all objects and releases multiset resources.
 */
void dtesn_multiset_destroy(dtesn_psystem_multiset_t *multiset);

/**
 * dtesn_multiset_add - Add object to multiset
 * @multiset: Target multiset
 * @symbol: Object symbol
 * @multiplicity: Number to add
 * 
 * Thread-safe addition of objects to multiset.
 * 
 * Returns: 0 on success, negative on error
 */
int dtesn_multiset_add(dtesn_psystem_multiset_t *multiset,
                       const char *symbol,
                       uint32_t multiplicity);

/**
 * dtesn_psystem_shutdown - Shutdown P-System kernel module
 * 
 * Cleanly shuts down the P-System subsystem, stopping all threads
 * and releasing system resources.
 */
void dtesn_psystem_shutdown(void);

/* Error codes specific to P-System operations */
#define DTESN_PSYSTEM_ENOMEM         -10   /* Out of memory */
#define DTESN_PSYSTEM_EINVAL         -11   /* Invalid parameters */
#define DTESN_PSYSTEM_ENOTFOUND      -12   /* Membrane/object not found */
#define DTESN_PSYSTEM_ELATENCY       -13   /* Timing constraint violated */
#define DTESN_PSYSTEM_ETHREAD        -14   /* Thread operation failed */
#define DTESN_PSYSTEM_EVALIDATION    -15   /* OEIS A000081 validation failed */
#define DTESN_PSYSTEM_ECOMMUNICATION -16   /* Communication failed */
#define DTESN_PSYSTEM_EEVOLUTION     -17   /* Evolution failed */

#ifdef __cplusplus
}
#endif

#endif /* DTESN_PSYSTEM_H */