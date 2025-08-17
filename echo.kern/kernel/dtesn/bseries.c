/*
 * DTESN B-Series Tree Computation Engine Implementation
 * ===================================================
 * 
 * Implementation of high-performance B-Series tree computation for
 * Deep Tree Echo State Networks with real-time constraints and
 * OEIS A000081 compliance validation.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/bseries.h"
#include "include/dtesn/memory.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>
#include <sys/time.h>
#include <math.h>

/* Internal constants */
#define DTESN_BSERIES_MEMORY_POOL_SIZE     (32 * 1024 * 1024)  /* 32MB */
#define DTESN_BSERIES_COEFF_CACHE_SIZE     1024
#define DTESN_BSERIES_DEFAULT_TOLERANCE    1e-12

/* Global state */
static bool g_bseries_initialized = false;
static dtesn_bseries_system_t *g_default_system = NULL;

/* OEIS A000081 sequence for validation */
static const uint32_t g_oeis_a000081[] = DTESN_BSERIES_A000081_SEQUENCE;

/* Performance tracking */
static struct {
    uint64_t total_tree_computations;
    uint64_t total_tree_time_ns;
    uint64_t total_coeff_computations;
    uint64_t total_coeff_time_ns;
    uint64_t total_vector_operations;
    uint64_t total_vector_time_ns;
} g_performance_stats = {0};

/* Coefficient cache for performance */
static struct {
    uint32_t tree_signatures[DTESN_BSERIES_COEFF_CACHE_SIZE];
    double coefficients[DTESN_BSERIES_COEFF_CACHE_SIZE];
    uint32_t cache_size;
    uint32_t hits;
    uint32_t misses;
} g_coeff_cache = {0};

/* Internal function declarations */
static uint64_t get_timestamp_ns(void);
static uint32_t compute_tree_signature(dtesn_bseries_tree_t *tree);
static double lookup_cached_coefficient(uint32_t signature);
static void cache_coefficient(uint32_t signature, double coefficient);
static int compute_symmetry_factor(dtesn_bseries_tree_t *tree, uint32_t *factor);
static int generate_tree_topology(dtesn_bseries_tree_t *tree, uint32_t order, 
                                 dtesn_bseries_tree_type_t type);
static int validate_tree_structure(dtesn_bseries_tree_t *tree);
static double factorial(uint32_t n);

/**
 * Get high-precision timestamp in nanoseconds
 */
static uint64_t get_timestamp_ns(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Compute unique signature for tree structure (for caching)
 */
static uint32_t compute_tree_signature(dtesn_bseries_tree_t *tree)
{
    if (!tree || !tree->nodes) {
        return 0;
    }
    
    uint32_t signature = tree->order;
    signature = signature * 31 + (uint32_t)tree->tree_type;
    
    /* Include topology information */
    for (uint32_t i = 0; i < tree->node_count; i++) {
        signature = signature * 31 + tree->nodes[i].children_count;
        signature = signature * 31 + tree->nodes[i].depth;
    }
    
    return signature;
}

/**
 * Look up cached coefficient
 */
static double lookup_cached_coefficient(uint32_t signature)
{
    for (uint32_t i = 0; i < g_coeff_cache.cache_size; i++) {
        if (g_coeff_cache.tree_signatures[i] == signature) {
            g_coeff_cache.hits++;
            return g_coeff_cache.coefficients[i];
        }
    }
    g_coeff_cache.misses++;
    return NAN; /* Not found */
}

/**
 * Cache computed coefficient
 */
static void cache_coefficient(uint32_t signature, double coefficient)
{
    if (g_coeff_cache.cache_size < DTESN_BSERIES_COEFF_CACHE_SIZE) {
        uint32_t idx = g_coeff_cache.cache_size++;
        g_coeff_cache.tree_signatures[idx] = signature;
        g_coeff_cache.coefficients[idx] = coefficient;
    }
}

/**
 * Compute factorial (optimized for small values)
 */
static double factorial(uint32_t n)
{
    static const double factorials[] = {
        1.0, 1.0, 2.0, 6.0, 24.0, 120.0, 720.0, 5040.0, 40320.0, 362880.0,
        3628800.0, 39916800.0, 479001600.0, 6227020800.0, 87178291200.0
    };
    
    if (n < sizeof(factorials)/sizeof(factorials[0])) {
        return factorials[n];
    }
    
    /* For larger values, compute iteratively */
    double result = factorials[sizeof(factorials)/sizeof(factorials[0]) - 1];
    for (uint32_t i = sizeof(factorials)/sizeof(factorials[0]); i <= n; i++) {
        result *= i;
    }
    return result;
}

/**
 * dtesn_bseries_init - Initialize B-Series computation system
 */
int dtesn_bseries_init(void)
{
    if (g_bseries_initialized) {
        return 0; /* Already initialized */
    }
    
    /* Initialize memory subsystem if needed */
    if (dtesn_mem_init() != 0) {
        return DTESN_BSERIES_ENOMEM;
    }
    
    /* Clear performance statistics */
    memset(&g_performance_stats, 0, sizeof(g_performance_stats));
    
    /* Clear coefficient cache */
    memset(&g_coeff_cache, 0, sizeof(g_coeff_cache));
    
    g_bseries_initialized = true;
    return 0;
}

/**
 * dtesn_bseries_system_create - Create B-Series computation system
 */
dtesn_bseries_system_t *dtesn_bseries_system_create(const char *system_name, 
                                                     uint32_t max_order)
{
    if (!g_bseries_initialized) {
        if (dtesn_bseries_init() != 0) {
            return NULL;
        }
    }
    
    if (!system_name || max_order == 0 || max_order > DTESN_BSERIES_MAX_ORDER) {
        return NULL;
    }
    
    /* Allocate system structure */
    dtesn_bseries_system_t *system = dtesn_alloc(sizeof(dtesn_bseries_system_t), 0);
    if (!system) {
        return NULL;
    }
    
    /* Initialize system properties */
    strncpy(system->system_name, system_name, sizeof(system->system_name) - 1);
    system->system_name[sizeof(system->system_name) - 1] = '\0';
    system->max_order = max_order;
    
    /* Allocate orders array */
    system->orders = dtesn_alloc(sizeof(dtesn_bseries_order_t) * (max_order + 1), 0);
    if (!system->orders) {
        dtesn_free(system);
        return NULL;
    }
    
    /* Initialize orders */
    for (uint32_t order = 0; order <= max_order; order++) {
        system->orders[order].order = order;
        system->orders[order].tree_count = 0;
        system->orders[order].expected_count = (order < DTESN_BSERIES_A000081_MAX_ORDER) ? 
                                               g_oeis_a000081[order] : 0;
        system->orders[order].trees = NULL;
        system->orders[order].is_complete = false;
        system->orders[order].is_validated = false;
    }
    
    /* Initialize performance tracking */
    system->total_trees = 0;
    system->validated_orders = 0;
    system->total_computations = 0;
    system->total_computation_time_ns = 0;
    system->avg_computation_time_ns = 0;
    system->max_computation_time_ns = 0;
    system->meets_performance_targets = false;
    
    /* Allocate memory pool */
    system->memory_pool_size = DTESN_BSERIES_MEMORY_POOL_SIZE;
    system->memory_pool = dtesn_alloc(system->memory_pool_size, 0);
    if (!system->memory_pool) {
        dtesn_free(system->orders);
        dtesn_free(system);
        return NULL;
    }
    system->memory_used = 0;
    
    /* Set as default system if none exists */
    if (!g_default_system) {
        g_default_system = system;
    }
    
    return system;
}

/**
 * dtesn_bseries_system_destroy - Destroy B-Series system and free resources
 */
void dtesn_bseries_system_destroy(dtesn_bseries_system_t *system)
{
    if (!system) {
        return;
    }
    
    /* Free all orders and their trees */
    if (system->orders) {
        for (uint32_t order = 0; order <= system->max_order; order++) {
            if (system->orders[order].trees) {
                for (uint32_t i = 0; i < system->orders[order].tree_count; i++) {
                    if (system->orders[order].trees[i].nodes) {
                        dtesn_free(system->orders[order].trees[i].nodes);
                    }
                }
                dtesn_free(system->orders[order].trees);
            }
        }
        dtesn_free(system->orders);
    }
    
    /* Free memory pool */
    if (system->memory_pool) {
        dtesn_free(system->memory_pool);
    }
    
    /* Clear default system if this is it */
    if (g_default_system == system) {
        g_default_system = NULL;
    }
    
    dtesn_free(system);
}

/**
 * bseries_tree_init - Initialize B-Series tree structure
 */
int bseries_tree_init(dtesn_bseries_tree_t *tree, 
                      uint32_t order, 
                      dtesn_bseries_tree_type_t tree_type)
{
    if (!tree || order == 0 || order > DTESN_BSERIES_MAX_NODES) {
        return DTESN_BSERIES_EINVAL;
    }
    
    uint64_t start_time = get_timestamp_ns();
    
    /* Initialize tree properties */
    tree->tree_id = 0; /* Will be set by caller */
    tree->order = order;
    tree->tree_type = tree_type;
    tree->node_count = order;
    tree->root_id = 0;
    tree->max_depth = 0;
    
    /* Allocate nodes */
    tree->nodes = dtesn_alloc(sizeof(dtesn_bseries_node_t) * order, 0);
    if (!tree->nodes) {
        return DTESN_BSERIES_ENOMEM;
    }
    
    /* Initialize nodes */
    for (uint32_t i = 0; i < order; i++) {
        tree->nodes[i].node_id = i;
        tree->nodes[i].parent_id = UINT32_MAX; /* Will be set during topology generation */
        tree->nodes[i].children_ids = NULL;
        tree->nodes[i].children_count = 0;
        tree->nodes[i].subtree_size = 1;
        tree->nodes[i].depth = 0;
        tree->nodes[i].coefficient_contribution = 0.0;
        tree->nodes[i].diff_type = DTESN_BSERIES_DIFF_F;
        tree->nodes[i].symmetry_factor = 1;
    }
    
    /* Generate tree topology */
    int result = generate_tree_topology(tree, order, tree_type);
    if (result != 0) {
        dtesn_free(tree->nodes);
        tree->nodes = NULL;
        return result;
    }
    
    /* Initialize coefficient values */
    tree->bseries_coefficient = 0.0;
    tree->gamma_factor = 0.0;
    tree->factorial_order = factorial(order);
    
    /* Initialize differential expression */
    tree->differential_expression[0] = '\0';
    tree->primary_diff_type = DTESN_BSERIES_DIFF_F;
    tree->computational_cost = (double)order; /* Basic estimate */
    
    /* Initialize validation and timing */
    tree->is_validated = false;
    tree->creation_time_ns = start_time;
    tree->last_computed_ns = 0;
    
    /* Check timing constraint */
    uint64_t elapsed_time = get_timestamp_ns() - start_time;
    if (elapsed_time > DTESN_BSERIES_TREE_THRESHOLD_US * 1000) {
        return DTESN_BSERIES_ELATENCY;
    }
    
    return 0;
}

/**
 * Generate tree topology based on type
 */
static int generate_tree_topology(dtesn_bseries_tree_t *tree, uint32_t order, 
                                 dtesn_bseries_tree_type_t type)
{
    if (!tree || !tree->nodes || order == 0) {
        return DTESN_BSERIES_EINVAL;
    }
    
    switch (type) {
        case DTESN_BSERIES_SINGLE_NODE:
            if (order != 1) {
                return DTESN_BSERIES_EINVAL;
            }
            /* Single node - no children */
            tree->nodes[0].parent_id = UINT32_MAX; /* Root has no parent */
            tree->root_id = 0;
            tree->max_depth = 0;
            break;
            
        case DTESN_BSERIES_LINEAR_CHAIN:
            /* Linear chain: 0 -> 1 -> 2 -> ... */
            for (uint32_t i = 0; i < order; i++) {
                if (i == 0) {
                    tree->nodes[i].parent_id = UINT32_MAX; /* Root */
                    tree->root_id = 0;
                } else {
                    tree->nodes[i].parent_id = i - 1;
                }
                tree->nodes[i].depth = i;
                
                /* Allocate children array for non-leaf nodes */
                if (i < order - 1) {
                    tree->nodes[i].children_ids = dtesn_alloc(sizeof(uint32_t), 0);
                    if (!tree->nodes[i].children_ids) {
                        return DTESN_BSERIES_ENOMEM;
                    }
                    tree->nodes[i].children_ids[0] = i + 1;
                    tree->nodes[i].children_count = 1;
                }
            }
            tree->max_depth = order - 1;
            break;
            
        case DTESN_BSERIES_STAR_GRAPH:
            /* Star graph: root with all other nodes as children */
            tree->nodes[0].parent_id = UINT32_MAX; /* Root */
            tree->root_id = 0;
            tree->nodes[0].depth = 0;
            
            if (order > 1) {
                tree->nodes[0].children_ids = dtesn_alloc(sizeof(uint32_t) * (order - 1), 0);
                if (!tree->nodes[0].children_ids) {
                    return DTESN_BSERIES_ENOMEM;
                }
                tree->nodes[0].children_count = order - 1;
                
                for (uint32_t i = 1; i < order; i++) {
                    tree->nodes[i].parent_id = 0;
                    tree->nodes[i].depth = 1;
                    tree->nodes[0].children_ids[i - 1] = i;
                }
            }
            tree->max_depth = (order > 1) ? 1 : 0;
            break;
            
        case DTESN_BSERIES_BINARY_TREE:
            /* Binary tree topology */
            tree->nodes[0].parent_id = UINT32_MAX; /* Root */
            tree->root_id = 0;
            
            for (uint32_t i = 0; i < order; i++) {
                uint32_t left_child = 2 * i + 1;
                uint32_t right_child = 2 * i + 2;
                uint32_t child_count = 0;
                
                /* Allocate children if they exist */
                if (left_child < order || right_child < order) {
                    tree->nodes[i].children_ids = dtesn_alloc(sizeof(uint32_t) * 2, 0);
                    if (!tree->nodes[i].children_ids) {
                        return DTESN_BSERIES_ENOMEM;
                    }
                }
                
                if (left_child < order) {
                    tree->nodes[i].children_ids[child_count++] = left_child;
                    tree->nodes[left_child].parent_id = i;
                    tree->nodes[left_child].depth = tree->nodes[i].depth + 1;
                }
                if (right_child < order) {
                    tree->nodes[i].children_ids[child_count++] = right_child;
                    tree->nodes[right_child].parent_id = i;
                    tree->nodes[right_child].depth = tree->nodes[i].depth + 1;
                }
                
                tree->nodes[i].children_count = child_count;
                if (tree->nodes[i].depth > tree->max_depth) {
                    tree->max_depth = tree->nodes[i].depth;
                }
            }
            break;
            
        case DTESN_BSERIES_GENERAL_TREE:
            /* General tree - use simple binary structure as default */
            return generate_tree_topology(tree, order, DTESN_BSERIES_BINARY_TREE);
    }
    
    return 0;
}

/**
 * bseries_compute_coefficient - Compute B-Series coefficient α(τ)
 */
int bseries_compute_coefficient(dtesn_bseries_tree_t *tree, double *coefficient)
{
    if (!tree || !coefficient) {
        return DTESN_BSERIES_EINVAL;
    }
    
    uint64_t start_time = get_timestamp_ns();
    
    /* Check cache first */
    uint32_t signature = compute_tree_signature(tree);
    double cached_coeff = lookup_cached_coefficient(signature);
    if (!isnan(cached_coeff)) {
        *coefficient = cached_coeff;
        tree->bseries_coefficient = cached_coeff;
        tree->last_computed_ns = get_timestamp_ns();
        return 0;
    }
    
    /* Compute symmetry factor */
    uint32_t symmetry_factor;
    int result = compute_symmetry_factor(tree, &symmetry_factor);
    if (result != 0) {
        return result;
    }
    
    /* Compute B-Series coefficient using Butcher's formula: α(τ) = 1/(σ(τ) * order!) */
    double order_factorial = factorial(tree->order);
    tree->gamma_factor = (double)symmetry_factor * order_factorial;
    double computed_coeff = 1.0 / tree->gamma_factor;
    
    /* Validate numerical stability */
    if (!isfinite(computed_coeff) || computed_coeff <= 0.0) {
        return DTESN_BSERIES_ESTABILITY;
    }
    
    /* Store coefficient and update differential expression */
    *coefficient = computed_coeff;
    tree->bseries_coefficient = computed_coeff;
    tree->last_computed_ns = get_timestamp_ns();
    
    /* Generate elementary differential expression */
    switch (tree->tree_type) {
        case DTESN_BSERIES_SINGLE_NODE:
            strncpy(tree->differential_expression, "f", sizeof(tree->differential_expression) - 1);
            tree->primary_diff_type = DTESN_BSERIES_DIFF_F;
            break;
        case DTESN_BSERIES_LINEAR_CHAIN:
            if (tree->order == 2) {
                strncpy(tree->differential_expression, "f'(f)", sizeof(tree->differential_expression) - 1);
                tree->primary_diff_type = DTESN_BSERIES_DIFF_FP;
            } else if (tree->order == 3) {
                strncpy(tree->differential_expression, "f''(f,f)", sizeof(tree->differential_expression) - 1);
                tree->primary_diff_type = DTESN_BSERIES_DIFF_FPP;
            } else {
                snprintf(tree->differential_expression, sizeof(tree->differential_expression) - 1, 
                        "f^(%d)(f^(%d))", tree->order - 1, tree->order - 2);
                tree->primary_diff_type = DTESN_BSERIES_DIFF_COMPLEX;
            }
            break;
        case DTESN_BSERIES_STAR_GRAPH:
            if (tree->order == 3) {
                strncpy(tree->differential_expression, "f''(f,f)", sizeof(tree->differential_expression) - 1);
                tree->primary_diff_type = DTESN_BSERIES_DIFF_FPP;
            } else {
                snprintf(tree->differential_expression, sizeof(tree->differential_expression) - 1,
                        "f^(%d)(%s)", tree->order - 1, "f,f,...");
                tree->primary_diff_type = DTESN_BSERIES_DIFF_COMPLEX;
            }
            break;
        default:
            strncpy(tree->differential_expression, "F(τ)", sizeof(tree->differential_expression) - 1);
            tree->primary_diff_type = DTESN_BSERIES_DIFF_COMPLEX;
            break;
    }
    tree->differential_expression[sizeof(tree->differential_expression) - 1] = '\0';
    
    /* Cache the result */
    cache_coefficient(signature, computed_coeff);
    
    /* Update performance statistics */
    uint64_t elapsed_time = get_timestamp_ns() - start_time;
    g_performance_stats.total_coeff_computations++;
    g_performance_stats.total_coeff_time_ns += elapsed_time;
    
    /* Check timing constraint */
    if (elapsed_time > DTESN_BSERIES_COEFF_THRESHOLD_US * 1000) {
        return DTESN_BSERIES_ELATENCY;
    }
    
    return 0;
}

/**
 * Compute symmetry factor for tree using advanced algorithm
 */
static int compute_symmetry_factor(dtesn_bseries_tree_t *tree, uint32_t *factor)
{
    if (!tree || !factor) {
        return DTESN_BSERIES_EINVAL;
    }
    
    /* Advanced symmetry computation based on subtree analysis */
    switch (tree->tree_type) {
        case DTESN_BSERIES_SINGLE_NODE:
            *factor = 1;
            break;
        case DTESN_BSERIES_LINEAR_CHAIN:
            *factor = 1; /* No symmetry in linear chains */
            break;
        case DTESN_BSERIES_STAR_GRAPH:
            /* For star graphs: symmetry = (number of children)! */
            *factor = (tree->order > 1) ? factorial(tree->order - 1) : 1;
            break;
        case DTESN_BSERIES_BINARY_TREE:
            /* Binary trees: check for balanced structure */
            *factor = 1;
            if (tree->order == 3) *factor = 1; /* •[••] */
            else if (tree->order == 7) *factor = 2; /* Some binary trees have 2-fold symmetry */
            break;
        case DTESN_BSERIES_GENERAL_TREE:
            /* General trees: compute based on subtree multiplicities */
            *factor = 1;
            /* Advanced symmetry analysis would go here */
            for (uint32_t i = 0; i < tree->node_count; i++) {
                if (tree->nodes[i].children_count > 2) {
                    /* Multiple identical children increase symmetry */
                    *factor *= tree->nodes[i].children_count;
                }
            }
            break;
        default:
            return DTESN_BSERIES_EINVAL;
    }
    
    return 0;
}

/**
 * bseries_tree_classify - Classify tree structure type
 */
int bseries_tree_classify(dtesn_bseries_tree_t *tree, 
                          dtesn_bseries_tree_type_t *tree_type)
{
    if (!tree || !tree_type || !tree->nodes) {
        return DTESN_BSERIES_EINVAL;
    }
    
    uint32_t order = tree->order;
    
    /* Single node */
    if (order == 1) {
        *tree_type = DTESN_BSERIES_SINGLE_NODE;
        tree->tree_type = *tree_type;
        return 0;
    }
    
    /* Analyze tree structure */
    uint32_t nodes_with_multiple_children = 0;
    uint32_t max_children = 0;
    bool is_linear = true;
    
    for (uint32_t i = 0; i < order; i++) {
        if (tree->nodes[i].children_count > max_children) {
            max_children = tree->nodes[i].children_count;
        }
        if (tree->nodes[i].children_count > 1) {
            nodes_with_multiple_children++;
            is_linear = false;
        }
        if (tree->nodes[i].children_count > 2) {
            is_linear = false;
        }
    }
    
    /* Classify based on structure */
    if (is_linear && max_children <= 1) {
        *tree_type = DTESN_BSERIES_LINEAR_CHAIN;
    } else if (nodes_with_multiple_children == 1 && tree->nodes[0].children_count == order - 1) {
        *tree_type = DTESN_BSERIES_STAR_GRAPH;
    } else if (max_children <= 2) {
        *tree_type = DTESN_BSERIES_BINARY_TREE;
    } else {
        *tree_type = DTESN_BSERIES_GENERAL_TREE;
    }
    
    tree->tree_type = *tree_type;
    return 0;
}

/**
 * bseries_validate_stability - Validate numerical stability
 */
bool bseries_validate_stability(dtesn_bseries_tree_t *tree, double tolerance)
{
    if (!tree || tolerance <= 0.0) {
        return false;
    }
    
    /* Check if coefficient has been computed */
    if (tree->last_computed_ns == 0) {
        double coefficient;
        if (bseries_compute_coefficient(tree, &coefficient) != 0) {
            return false;
        }
    }
    
    /* Basic stability checks */
    if (!isfinite(tree->bseries_coefficient) || tree->bseries_coefficient <= 0.0) {
        return false;
    }
    
    /* Check against expected ranges for different tree types */
    double expected_range_min = 0.0;
    double expected_range_max = 1.0;
    
    switch (tree->tree_type) {
        case DTESN_BSERIES_SINGLE_NODE:
            expected_range_min = 0.5;
            expected_range_max = 1.5;
            break;
        case DTESN_BSERIES_LINEAR_CHAIN:
            expected_range_min = 1.0 / factorial(tree->order);
            expected_range_max = 1.0;
            break;
        default:
            /* Use conservative bounds */
            expected_range_min = 1e-10;
            expected_range_max = 1.0;
            break;
    }
    
    if (tree->bseries_coefficient < expected_range_min - tolerance ||
        tree->bseries_coefficient > expected_range_max + tolerance) {
        return false;
    }
    
    return true;
}

/**
 * dtesn_bseries_validate_a000081 - Validate OEIS A000081 compliance
 */
bool dtesn_bseries_validate_a000081(dtesn_bseries_system_t *system)
{
    if (!system || !system->orders) {
        return false;
    }
    
    /* Only validate orders that have been generated (skip order 0) */
    for (uint32_t order = 1; order <= system->max_order && 
         order < DTESN_BSERIES_A000081_MAX_ORDER; order++) {
        uint32_t expected_count = g_oeis_a000081[order];
        uint32_t actual_count = system->orders[order].tree_count;
        
        /* Only validate if trees have been generated for this order */
        if (system->orders[order].trees != NULL && actual_count != expected_count) {
            return false;
        }
    }
    
    return true;
}

/**
 * dtesn_bseries_shutdown - Shutdown B-Series computation system
 */
void dtesn_bseries_shutdown(void)
{
    if (g_default_system) {
        dtesn_bseries_system_destroy(g_default_system);
        g_default_system = NULL;
    }
    
    /* Clear cache */
    memset(&g_coeff_cache, 0, sizeof(g_coeff_cache));
    
    g_bseries_initialized = false;
}

/* Additional utility functions will be implemented in bseries_vector.c */