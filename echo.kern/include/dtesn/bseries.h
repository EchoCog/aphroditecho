/*
 * DTESN B-Series Tree Computation Engine
 * =====================================
 * 
 * Deep Tree Echo State Networks (DTESN) B-Series implementation providing
 * real-time differential tree computation with OEIS A000081 compliance.
 * 
 * Performance Requirements:
 * - Tree computation: ≤ 100μs
 * - Coefficient calculation: ≤ 50μs
 * - Vector operations: ≥ 1000 trees/ms
 * - Numerical precision: double precision (64-bit)
 * 
 * Mathematical Foundation:
 * y(h) = y₀ + h ∑ α(τ) F(τ)(y₀)
 * where τ represents rooted trees from OEIS A000081 enumeration
 */

#ifndef DTESN_BSERIES_H
#define DTESN_BSERIES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <math.h>

#ifdef __cplusplus
extern "C" {
#endif

/* B-Series configuration constants */
#define DTESN_BSERIES_MAX_ORDER         10      /* Maximum tree order */
#define DTESN_BSERIES_MAX_TREES         1024    /* Maximum trees per order */
#define DTESN_BSERIES_MAX_NODES         64      /* Maximum nodes per tree */
#define DTESN_BSERIES_MAX_CHILDREN      8       /* Maximum children per node */
#define DTESN_BSERIES_MAX_SYMBOL_LEN    128     /* Maximum symbol length */

/* Performance thresholds (microseconds) */
#define DTESN_BSERIES_TREE_THRESHOLD_US       100   /* ≤ 100μs tree computation */
#define DTESN_BSERIES_COEFF_THRESHOLD_US      50    /* ≤ 50μs coefficient calculation */
#define DTESN_BSERIES_VECTOR_THRESHOLD_MS     1     /* ≥ 1000 trees/ms vector ops */

/* OEIS A000081 sequence for tree enumeration validation */
#define DTESN_BSERIES_A000081_MAX_ORDER 15
#define DTESN_BSERIES_A000081_SEQUENCE \
    { 0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973 }

/* B-Series tree structure types */
typedef enum {
    DTESN_BSERIES_SINGLE_NODE = 0,    /* • Single node tree */
    DTESN_BSERIES_LINEAR_CHAIN = 1,   /* •—•—• Linear chain */
    DTESN_BSERIES_STAR_GRAPH = 2,     /* • with multiple children */
    DTESN_BSERIES_BINARY_TREE = 3,    /* Binary branching tree */
    DTESN_BSERIES_GENERAL_TREE = 4    /* General rooted tree */
} dtesn_bseries_tree_type_t;

/* Elementary differential types */
typedef enum {
    DTESN_BSERIES_DIFF_F = 0,         /* f(y) */
    DTESN_BSERIES_DIFF_FP = 1,        /* f'(y) */
    DTESN_BSERIES_DIFF_FPP = 2,       /* f''(y) */
    DTESN_BSERIES_DIFF_FPPP = 3,      /* f'''(y) */
    DTESN_BSERIES_DIFF_COMPLEX = 4    /* Complex differential */
} dtesn_bseries_diff_type_t;

/* Tree node structure for B-Series computation */
typedef struct dtesn_bseries_node {
    uint32_t node_id;                          /* Unique node identifier */
    uint32_t parent_id;                        /* Parent node ID (0 for root) */
    uint32_t *children_ids;                    /* Array of child node IDs */
    uint32_t children_count;                   /* Number of children */
    uint32_t subtree_size;                     /* Size of subtree rooted here */
    uint32_t depth;                            /* Depth from root */
    
    /* B-Series properties */
    double coefficient_contribution;            /* Node contribution to α(τ) */
    dtesn_bseries_diff_type_t diff_type;       /* Associated differential type */
    uint32_t symmetry_factor;                  /* Symmetry factor for node */
    
} dtesn_bseries_node_t;

/* B-Series tree structure */
typedef struct dtesn_bseries_tree {
    uint32_t tree_id;                          /* Unique tree identifier */
    uint32_t order;                            /* Tree order (number of nodes) */
    dtesn_bseries_tree_type_t tree_type;       /* Structure classification */
    
    /* Tree topology */
    dtesn_bseries_node_t *nodes;               /* Array of tree nodes */
    uint32_t node_count;                       /* Number of nodes */
    uint32_t root_id;                          /* Root node ID */
    uint32_t max_depth;                        /* Maximum depth */
    
    /* B-Series coefficients */
    double bseries_coefficient;                /* α(τ) coefficient */
    double gamma_factor;                       /* Γ(τ) = |Aut(τ)| */
    uint32_t factorial_order;                  /* order! for normalization */
    
    /* Elementary differential */
    char differential_expression[DTESN_BSERIES_MAX_SYMBOL_LEN];
    dtesn_bseries_diff_type_t primary_diff_type;
    double computational_cost;                 /* Estimated computation cost */
    
    /* Validation and performance */
    bool is_validated;                         /* OEIS A000081 validated */
    uint64_t creation_time_ns;                 /* Tree creation timestamp */
    uint64_t last_computed_ns;                 /* Last computation timestamp */
    
} dtesn_bseries_tree_t;

/* B-Series tree collection for an order */
typedef struct dtesn_bseries_order {
    uint32_t order;                            /* Tree order */
    uint32_t tree_count;                       /* Number of trees */
    uint32_t expected_count;                   /* OEIS A000081 expected count */
    dtesn_bseries_tree_t *trees;               /* Array of trees */
    bool is_complete;                          /* All trees enumerated */
    bool is_validated;                         /* OEIS compliance validated */
    
} dtesn_bseries_order_t;

/* B-Series computation system */
typedef struct dtesn_bseries_system {
    char system_name[64];                      /* System identifier */
    uint32_t max_order;                        /* Maximum supported order */
    
    /* Tree management */
    dtesn_bseries_order_t *orders;             /* Array of tree orders */
    uint32_t total_trees;                      /* Total trees in system */
    uint32_t validated_orders;                 /* Orders with OEIS validation */
    
    /* Performance monitoring */
    uint64_t total_computations;               /* Total tree computations */
    uint64_t total_computation_time_ns;        /* Total computation time */
    uint64_t avg_computation_time_ns;          /* Average computation time */
    uint64_t max_computation_time_ns;          /* Maximum computation time */
    bool meets_performance_targets;            /* All targets satisfied */
    
    /* Memory management */
    void *memory_pool;                         /* Dedicated memory pool */
    size_t memory_pool_size;                   /* Pool size */
    size_t memory_used;                        /* Currently used memory */
    
} dtesn_bseries_system_t;

/* Vector operation structure for bulk processing */
typedef struct dtesn_bseries_vector_op {
    dtesn_bseries_tree_t **trees;             /* Array of tree pointers */
    uint32_t tree_count;                       /* Number of trees */
    double *coefficients;                      /* Output coefficients */
    double *computational_costs;               /* Output costs */
    uint64_t operation_time_ns;                /* Time taken for operation */
    bool success;                              /* Operation success flag */
    
} dtesn_bseries_vector_op_t;

/* Performance statistics structure */
typedef struct dtesn_bseries_stats {
    uint64_t total_tree_computations;          /* Total tree computations */
    uint64_t total_coefficient_computations;   /* Total coefficient computations */
    uint64_t total_vector_operations;          /* Total vector operations */
    
    uint64_t avg_tree_time_ns;                 /* Average tree computation time */
    uint64_t max_tree_time_ns;                 /* Maximum tree computation time */
    uint64_t avg_coeff_time_ns;                /* Average coefficient time */
    uint64_t max_coeff_time_ns;                /* Maximum coefficient time */
    
    uint32_t vector_throughput_per_ms;         /* Vector operation throughput */
    uint32_t cache_hit_rate_pct;               /* Coefficient cache hit rate */
    
    bool tree_threshold_met;                   /* ≤100μs tree computation */
    bool coeff_threshold_met;                  /* ≤50μs coefficient calculation */
    bool vector_threshold_met;                 /* ≥1000 trees/ms vector ops */
    
} dtesn_bseries_stats_t;

/* Core B-Series management functions */

/**
 * dtesn_bseries_init - Initialize B-Series computation system
 * 
 * Initializes the B-Series tree computation engine with memory pools,
 * OEIS A000081 validation, and performance monitoring.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_bseries_init(void);

/**
 * dtesn_bseries_system_create - Create B-Series computation system
 * @system_name: Human-readable system identifier
 * @max_order: Maximum tree order to support
 * 
 * Creates a new B-Series computation system with specified constraints.
 * Pre-computes trees up to max_order following OEIS A000081 enumeration.
 * 
 * Returns: Pointer to system structure, NULL on failure
 */
dtesn_bseries_system_t *dtesn_bseries_system_create(const char *system_name, 
                                                     uint32_t max_order);

/**
 * dtesn_bseries_system_destroy - Destroy B-Series system and free resources
 * @system: B-Series system to destroy
 * 
 * Cleanly shuts down the system and releases all associated resources.
 */
void dtesn_bseries_system_destroy(dtesn_bseries_system_t *system);

/* Tree management functions */

/**
 * bseries_tree_init - Initialize B-Series tree structure
 * @tree: Tree structure to initialize
 * @order: Tree order (number of nodes)
 * @tree_type: Type of tree structure
 * 
 * Initializes a B-Series tree with the specified properties and
 * allocates memory for nodes and coefficients.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int bseries_tree_init(dtesn_bseries_tree_t *tree, 
                      uint32_t order, 
                      dtesn_bseries_tree_type_t tree_type);

/**
 * bseries_compute_coefficient - Compute B-Series coefficient α(τ)
 * @tree: Target B-Series tree
 * @coefficient: Output coefficient value
 * 
 * Computes the B-Series coefficient α(τ) for the given tree using
 * Butcher's formula: α(τ) = 1/γ(τ) where γ(τ) = σ(τ) * order!
 * Enforces ≤50μs timing constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int bseries_compute_coefficient(dtesn_bseries_tree_t *tree, double *coefficient);

/**
 * bseries_tree_classify - Classify tree structure type
 * @tree: Tree to classify
 * @tree_type: Output classification
 * 
 * Analyzes tree topology and classifies it as single node, linear chain,
 * star graph, binary tree, or general tree structure.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int bseries_tree_classify(dtesn_bseries_tree_t *tree, 
                          dtesn_bseries_tree_type_t *tree_type);

/**
 * bseries_validate_stability - Validate numerical stability
 * @tree: Tree to validate
 * @tolerance: Numerical tolerance threshold
 * 
 * Validates that B-Series coefficient computation is numerically stable
 * and within specified tolerance bounds.
 * 
 * Returns: true if stable, false otherwise
 */
bool bseries_validate_stability(dtesn_bseries_tree_t *tree, double tolerance);

/* Vector operations for performance */

/**
 * bseries_vector_op - Perform vectorized B-Series operations
 * @vector_op: Vector operation structure
 * 
 * Performs bulk B-Series coefficient computation on multiple trees
 * with optimized vectorized operations. Enforces ≥1000 trees/ms constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int bseries_vector_op(dtesn_bseries_vector_op_t *vector_op);

/**
 * dtesn_bseries_generate_order - Generate all trees for given order
 * @system: B-Series system
 * @order: Target order
 * 
 * Generates all rooted trees of the specified order following
 * OEIS A000081 enumeration and computes their B-Series coefficients.
 * 
 * Returns: Number of trees generated, negative on error
 */
int dtesn_bseries_generate_order(dtesn_bseries_system_t *system, uint32_t order);

/* Utility and validation functions */

/**
 * dtesn_bseries_validate_a000081 - Validate OEIS A000081 compliance
 * @system: B-Series system to validate
 * 
 * Validates that the generated trees follow the OEIS A000081
 * unlabeled rooted tree enumeration sequence.
 * 
 * Returns: true if compliant, false otherwise
 */
bool dtesn_bseries_validate_a000081(dtesn_bseries_system_t *system);

/**
 * dtesn_bseries_get_stats - Get comprehensive performance statistics
 * @system: B-Series system to analyze
 * @stats: Statistics structure to fill
 * 
 * Retrieves detailed performance metrics including timing analysis,
 * computation counts, and throughput measurements.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_bseries_get_stats(dtesn_bseries_system_t *system, 
                            dtesn_bseries_stats_t *stats);

/**
 * dtesn_bseries_get_tree - Retrieve tree by order and index
 * @system: B-Series system
 * @order: Tree order
 * @index: Tree index within order
 * 
 * Retrieves a specific tree from the system by order and index.
 * 
 * Returns: Pointer to tree structure, NULL if not found
 */
dtesn_bseries_tree_t *dtesn_bseries_get_tree(dtesn_bseries_system_t *system,
                                              uint32_t order, 
                                              uint32_t index);

/**
 * dtesn_bseries_tree_isomorphic - Check if two trees are isomorphic
 * @tree1: First tree
 * @tree2: Second tree
 * 
 * Determines if two trees are isomorphic using canonical form comparison.
 * 
 * Returns: true if isomorphic, false otherwise
 */
bool dtesn_bseries_tree_isomorphic(dtesn_bseries_tree_t *tree1,
                                   dtesn_bseries_tree_t *tree2);

/**
 * dtesn_bseries_shutdown - Shutdown B-Series computation system
 * 
 * Cleanly shuts down the B-Series subsystem and releases system resources.
 */
void dtesn_bseries_shutdown(void);

/* Error codes specific to B-Series operations */
#define DTESN_BSERIES_ENOMEM         -20   /* Out of memory */
#define DTESN_BSERIES_EINVAL         -21   /* Invalid parameters */
#define DTESN_BSERIES_ENOTFOUND      -22   /* Tree not found */
#define DTESN_BSERIES_ELATENCY       -23   /* Timing constraint violated */
#define DTESN_BSERIES_EVALIDATION    -24   /* OEIS A000081 validation failed */
#define DTESN_BSERIES_ESTABILITY     -25   /* Numerical stability failed */
#define DTESN_BSERIES_ECOMPUTATION   -26   /* Computation failed */
#define DTESN_BSERIES_EVECTOR        -27   /* Vector operation failed */

#ifdef __cplusplus
}
#endif

#endif /* DTESN_BSERIES_H */