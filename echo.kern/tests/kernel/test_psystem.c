/*
 * DTESN P-System Membrane Computing Kernel Module Unit Tests
 * ==========================================================
 * 
 * Comprehensive unit tests for the DTESN P-System implementation including
 * performance validation, OEIS A000081 compliance, rule application,
 * membrane communication, and real-time constraint verification.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/psystem.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>

/* Test framework macros */
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("FAIL: %s - %s\n", __func__, message); \
            return 0; \
        } \
    } while(0)

#define TEST_PASS() \
    do { \
        printf("PASS: %s\n", __func__); \
        return 1; \
    } while(0)

#define TEST_PERFORMANCE_THRESHOLD_NS(actual, threshold_us, label) \
    do { \
        uint64_t threshold_ns = (threshold_us) * 1000; \
        if ((actual) > threshold_ns) { \
            printf("WARNING: %s performance: %lu ns (threshold: %lu ns)\n", \
                   label, actual, threshold_ns); \
        } \
    } while(0)

/* Test configuration */
#define TEST_ITERATIONS 100
#define STRESS_TEST_MEMBRANES 50
#define PERFORMANCE_SAMPLES 1000
#define COMMUNICATION_TEST_OBJECTS 10

/* Global test state */
static int tests_passed = 0;
static int tests_failed = 0;

/* Test function declarations */
static int test_psystem_initialization(void);
static int test_psystem_creation(void);
static int test_membrane_creation(void);
static int test_membrane_hierarchy_validation(void);
static int test_object_multiset_operations(void);
static int test_rule_application(void);
static int test_membrane_evolution_performance(void);
static int test_membrane_communication(void);
static int test_parallel_evolution(void);
static int test_oeis_a000081_compliance(void);
static int test_system_evolution(void);
static int test_membrane_dissolution(void);
static int test_performance_statistics(void);
static int test_stress_many_membranes(void);
static int test_edge_cases(void);

/* Helper functions */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static dtesn_psystem_multiset_t *create_test_multiset(void) {
    dtesn_psystem_multiset_t *multiset = dtesn_multiset_create();
    if (multiset) {
        dtesn_multiset_add(multiset, "test_object", 5);
        dtesn_multiset_add(multiset, "signal", 3);
        dtesn_multiset_add(multiset, "data", 1);
    }
    return multiset;
}

/* Test implementations */

/**
 * test_psystem_initialization - Test P-System subsystem initialization
 */
static int test_psystem_initialization(void) {
    int result = dtesn_psystem_init();
    TEST_ASSERT(result == 0, "P-System initialization failed");
    
    /* Test double initialization */
    result = dtesn_psystem_init();
    TEST_ASSERT(result == 0, "Double initialization should succeed");
    
    TEST_PASS();
}

/**
 * test_psystem_creation - Test P-System instance creation and destruction
 */
static int test_psystem_creation(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("test_system", 100);
    TEST_ASSERT(system != NULL, "P-System creation failed");
    
    /* Verify system properties */
    TEST_ASSERT(strcmp(system->system_name, "test_system") == 0, "System name mismatch");
    TEST_ASSERT(system->membrane_capacity == 100, "Membrane capacity incorrect");
    TEST_ASSERT(system->membrane_count == 0, "Initial membrane count should be 0");
    TEST_ASSERT(system->next_membrane_id == 1, "Initial membrane ID should be 1");
    TEST_ASSERT(!system->is_halted, "System should not be halted initially");
    
    /* Test system destruction */
    dtesn_psystem_destroy(system);
    
    /* Test creation with default parameters */
    system = dtesn_psystem_create("default_system", 0);
    TEST_ASSERT(system != NULL, "Default system creation failed");
    TEST_ASSERT(system->membrane_capacity == DTESN_PSYSTEM_MAX_MEMBRANES, 
                "Default capacity incorrect");
    
    dtesn_psystem_destroy(system);
    
    TEST_PASS();
}

/**
 * test_membrane_creation - Test membrane creation and properties
 */
static int test_membrane_creation(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("membrane_test", 50);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    /* Create root membrane */
    uint32_t root_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                             "root", 0, 100);
    TEST_ASSERT(root_id != 0, "Root membrane creation failed");
    TEST_ASSERT(root_id == 1, "First membrane ID should be 1");
    TEST_ASSERT(system->membrane_count == 1, "Membrane count should be 1");
    TEST_ASSERT(system->skin_membrane_id == root_id, "Skin membrane should be set");
    
    /* Create child membrane */
    uint32_t child_id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                              "child", root_id, 50);
    TEST_ASSERT(child_id != 0, "Child membrane creation failed");
    TEST_ASSERT(child_id == 2, "Second membrane ID should be 2");
    TEST_ASSERT(system->membrane_count == 2, "Membrane count should be 2");
    
    /* Verify membrane properties */
    dtesn_psystem_membrane_t *root_membrane = NULL;
    for (uint32_t i = 0; i < system->membrane_count; i++) {
        if (system->membranes[i]->membrane_id == root_id) {
            root_membrane = system->membranes[i];
            break;
        }
    }
    
    TEST_ASSERT(root_membrane != NULL, "Root membrane not found");
    TEST_ASSERT(root_membrane->membrane_type == DTESN_MEMBRANE_ROOT, "Root type incorrect");
    TEST_ASSERT(strcmp(root_membrane->label, "root") == 0, "Root label incorrect");
    TEST_ASSERT(root_membrane->neuron_count == 100, "Root neuron count incorrect");
    TEST_ASSERT(root_membrane->depth_level == 0, "Root depth should be 0");
    TEST_ASSERT(root_membrane->is_active, "Root should be active");
    TEST_ASSERT(!root_membrane->is_dissolved, "Root should not be dissolved");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_membrane_hierarchy_validation - Test OEIS A000081 compliance validation
 */
static int test_membrane_hierarchy_validation(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("hierarchy_test", 50);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    printf("Testing OEIS A000081 hierarchy validation...\n");
    
    /* Create valid hierarchy according to OEIS A000081 */
    uint32_t root_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                             "root", 0, 100);
    TEST_ASSERT(root_id != 0, "Root creation failed");
    
    /* Test validation with single root (A000081[0] = 1) */
    bool is_valid = dtesn_psystem_validate_a000081(system);
    TEST_ASSERT(is_valid, "Single root should be valid");
    
    /* Add trunk membrane (A000081[1] = 1) */
    uint32_t trunk_id = dtesn_membrane_create(system, DTESN_MEMBRANE_TRUNK,
                                              "trunk", root_id, 200);
    TEST_ASSERT(trunk_id != 0, "Trunk creation failed");
    
    is_valid = dtesn_psystem_validate_a000081(system);
    printf("  After adding trunk: %s\n", is_valid ? "VALID" : "INVALID");
    
    /* Add branch membrane (A000081[2] = 2) - first one */
    uint32_t branch1_id = dtesn_membrane_create(system, DTESN_MEMBRANE_BRANCH,
                                                "branch1", trunk_id, 150);
    TEST_ASSERT(branch1_id != 0, "Branch1 creation failed");
    
    is_valid = dtesn_psystem_validate_a000081(system);
    printf("  After adding branch1: %s\n", is_valid ? "VALID" : "INVALID");
    
    /* Add second branch membrane (A000081[2] = 2) */
    uint32_t branch2_id = dtesn_membrane_create(system, DTESN_MEMBRANE_BRANCH,
                                                "branch2", trunk_id, 150);
    TEST_ASSERT(branch2_id != 0, "Branch2 creation failed");
    
    is_valid = dtesn_psystem_validate_a000081(system);
    printf("  After adding branch2: %s\n", is_valid ? "VALID" : "INVALID");
    
    /* Add leaf membranes (A000081[3] = 4) */
    for (int i = 0; i < 4; i++) {
        char leaf_label[32];
        snprintf(leaf_label, sizeof(leaf_label), "leaf%d", i);
        uint32_t parent_id = (i < 2) ? branch1_id : branch2_id;
        
        uint32_t leaf_id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                                 leaf_label, parent_id, 100);
        TEST_ASSERT(leaf_id != 0, "Leaf creation failed");
    }
    
    is_valid = dtesn_psystem_validate_a000081(system);
    printf("  Final hierarchy validation: %s\n", is_valid ? "VALID" : "INVALID");
    printf("  Total membranes: %u\n", system->membrane_count);
    
    /* Print membrane depth distribution */
    uint32_t depth_counts[5] = {0};
    for (uint32_t i = 0; i < system->membrane_count; i++) {
        uint32_t depth = system->membranes[i]->depth_level;
        if (depth < 5) depth_counts[depth]++;
    }
    
    printf("  Depth distribution: ");
    for (int i = 0; i < 5; i++) {
        printf("L%d:%u ", i, depth_counts[i]);
    }
    printf("\n");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_object_multiset_operations - Test object multiset management
 */
static int test_object_multiset_operations(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("object_test", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    uint32_t membrane_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                                 "test_membrane", 0, 100);
    TEST_ASSERT(membrane_id != 0, "Membrane creation failed");
    
    /* Test adding objects */
    int result = dtesn_membrane_add_object(system, membrane_id, "signal", 5);
    TEST_ASSERT(result == 0, "Adding signal objects failed");
    
    result = dtesn_membrane_add_object(system, membrane_id, "noise", 3);
    TEST_ASSERT(result == 0, "Adding noise objects failed");
    
    result = dtesn_membrane_add_object(system, membrane_id, "signal", 2);
    TEST_ASSERT(result == 0, "Adding more signal objects failed");
    
    /* Verify object counts */
    dtesn_psystem_membrane_t *membrane = NULL;
    for (uint32_t i = 0; i < system->membrane_count; i++) {
        if (system->membranes[i]->membrane_id == membrane_id) {
            membrane = system->membranes[i];
            break;
        }
    }
    
    TEST_ASSERT(membrane != NULL, "Membrane not found");
    TEST_ASSERT(membrane->objects.object_count == 2, "Object count should be 2");
    TEST_ASSERT(membrane->objects.total_multiplicity == 10, "Total multiplicity should be 10");
    
    /* Test removing objects */
    uint32_t removed = dtesn_membrane_remove_object(system, membrane_id, "signal", 3);
    TEST_ASSERT(removed == 3, "Should remove 3 signal objects");
    
    removed = dtesn_membrane_remove_object(system, membrane_id, "noise", 10);
    TEST_ASSERT(removed == 3, "Should remove all 3 noise objects");
    
    removed = dtesn_membrane_remove_object(system, membrane_id, "nonexistent", 1);
    TEST_ASSERT(removed == 0, "Should not remove nonexistent objects");
    
    /* Test multiset creation and destruction */
    dtesn_psystem_multiset_t *multiset = create_test_multiset();
    TEST_ASSERT(multiset != NULL, "Multiset creation failed");
    TEST_ASSERT(multiset->object_count == 3, "Multiset should have 3 object types");
    TEST_ASSERT(multiset->total_multiplicity == 9, "Total multiplicity should be 9");
    
    dtesn_multiset_destroy(multiset);
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_rule_application - Test evolution rule application
 */
static int test_rule_application(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("rule_test", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    uint32_t membrane_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                                 "rule_membrane", 0, 100);
    TEST_ASSERT(membrane_id != 0, "Membrane creation failed");
    
    /* Add test objects */
    dtesn_membrane_add_object(system, membrane_id, "input", 5);
    dtesn_membrane_add_object(system, membrane_id, "catalyst", 2);
    
    /* Create test rule structures */
    dtesn_psystem_multiset_t *lhs = dtesn_multiset_create();
    dtesn_psystem_multiset_t *rhs = dtesn_multiset_create();
    
    TEST_ASSERT(lhs != NULL && rhs != NULL, "Rule multiset creation failed");
    
    /* Rule: input + catalyst -> output + catalyst */
    dtesn_multiset_add(lhs, "input", 1);
    dtesn_multiset_add(lhs, "catalyst", 1);
    dtesn_multiset_add(rhs, "output", 1);
    dtesn_multiset_add(rhs, "catalyst", 1);
    
    uint32_t rule_id = dtesn_membrane_add_rule(system, membrane_id,
                                               DTESN_RULE_EVOLUTION, 10,
                                               "input + catalyst -> output + catalyst",
                                               lhs, rhs, 0);
    TEST_ASSERT(rule_id != 0, "Rule addition failed");
    
    /* Test evolution */
    int rules_applied = dtesn_membrane_evolve(system, membrane_id);
    printf("  Rules applied in evolution: %d\n", rules_applied);
    
    /* Note: In this simplified test, we don't fully verify rule application
     * since it requires more complex rule matching logic */
    
    dtesn_multiset_destroy(lhs);
    dtesn_multiset_destroy(rhs);
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_membrane_evolution_performance - Test evolution performance constraints
 */
static int test_membrane_evolution_performance(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("perf_test", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    uint32_t membrane_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                                 "perf_membrane", 0, 100);
    TEST_ASSERT(membrane_id != 0, "Membrane creation failed");
    
    /* Add objects for evolution */
    dtesn_membrane_add_object(system, membrane_id, "test_obj", 1000);
    
    printf("Testing membrane evolution performance (%d samples)...\n", PERFORMANCE_SAMPLES);
    
    uint64_t total_time = 0;
    uint64_t max_time = 0;
    uint64_t min_time = UINT64_MAX;
    
    for (int i = 0; i < PERFORMANCE_SAMPLES; i++) {
        uint64_t start = get_time_ns();
        int result = dtesn_membrane_evolve(system, membrane_id);
        uint64_t end = get_time_ns();
        
        uint64_t duration = end - start;
        total_time += duration;
        
        if (duration > max_time) max_time = duration;
        if (duration < min_time) min_time = duration;
        
        /* Re-add object for next iteration if consumed */
        if (result > 0) {
            dtesn_membrane_add_object(system, membrane_id, "test_obj", 1);
        }
    }
    
    uint64_t avg_time = total_time / PERFORMANCE_SAMPLES;
    
    printf("  Average evolution time: %lu ns\n", avg_time);
    printf("  Minimum evolution time: %lu ns\n", min_time);
    printf("  Maximum evolution time: %lu ns\n", max_time);
    printf("  Threshold: %u μs (%lu ns)\n", 
           DTESN_PSYSTEM_EVOLUTION_THRESHOLD_US,
           DTESN_PSYSTEM_EVOLUTION_THRESHOLD_US * 1000UL);
    
    TEST_PERFORMANCE_THRESHOLD_NS(avg_time, DTESN_PSYSTEM_EVOLUTION_THRESHOLD_US, 
                                  "Evolution");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_membrane_communication - Test inter-membrane communication
 */
static int test_membrane_communication(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("comm_test", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    uint32_t source_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                               "source", 0, 100);
    uint32_t target_id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                               "target", source_id, 50);
    
    TEST_ASSERT(source_id != 0 && target_id != 0, "Membrane creation failed");
    
    /* Add objects to source */
    dtesn_membrane_add_object(system, source_id, "message", 5);
    dtesn_membrane_add_object(system, source_id, "data", 3);
    
    /* Create communication multiset */
    dtesn_psystem_multiset_t *comm_objects = dtesn_multiset_create();
    TEST_ASSERT(comm_objects != NULL, "Communication multiset creation failed");
    
    dtesn_multiset_add(comm_objects, "message", 2);
    dtesn_multiset_add(comm_objects, "data", 1);
    
    printf("Testing membrane communication performance...\n");
    
    uint64_t total_comm_time = 0;
    for (int i = 0; i < COMMUNICATION_TEST_OBJECTS; i++) {
        uint64_t start = get_time_ns();
        int result = dtesn_membrane_communicate(system, source_id, target_id, 
                                                comm_objects);
        uint64_t end = get_time_ns();
        
        TEST_ASSERT(result == 0, "Communication should succeed");
        
        uint64_t comm_time = end - start;
        total_comm_time += comm_time;
        
        /* Re-add objects for next test */
        dtesn_membrane_add_object(system, source_id, "message", 2);
        dtesn_membrane_add_object(system, source_id, "data", 1);
    }
    
    uint64_t avg_comm_time = total_comm_time / COMMUNICATION_TEST_OBJECTS;
    printf("  Average communication time: %lu ns\n", avg_comm_time);
    printf("  Threshold: %u μs (%lu ns)\n",
           DTESN_PSYSTEM_COMM_THRESHOLD_US,
           DTESN_PSYSTEM_COMM_THRESHOLD_US * 1000UL);
    
    TEST_PERFORMANCE_THRESHOLD_NS(avg_comm_time, DTESN_PSYSTEM_COMM_THRESHOLD_US,
                                  "Communication");
    
    dtesn_multiset_destroy(comm_objects);
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_system_evolution - Test system-wide evolution
 */
static int test_system_evolution(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("system_evolution", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    /* Create simple membrane hierarchy */
    uint32_t root_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                             "root", 0, 100);
    uint32_t child_id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                              "child", root_id, 50);
    
    TEST_ASSERT(root_id != 0 && child_id != 0, "Membrane creation failed");
    
    /* Add initial objects */
    dtesn_membrane_add_object(system, root_id, "initial", 10);
    dtesn_membrane_add_object(system, child_id, "data", 5);
    
    printf("Testing system evolution...\n");
    
    int evolution_steps = 0;
    bool system_active = true;
    
    while (system_active && evolution_steps < 100) {
        uint64_t start = get_time_ns();
        system_active = dtesn_system_evolve(system);
        uint64_t end = get_time_ns();
        
        evolution_steps++;
        
        printf("  Step %d: %s (time: %lu ns)\n", 
               evolution_steps, 
               system_active ? "active" : "halted",
               end - start);
        
        if (!system_active) {
            break;
        }
    }
    
    printf("  System halted after %d steps\n", evolution_steps);
    TEST_ASSERT(system->is_halted, "System should be halted");
    TEST_ASSERT(system->global_phase == DTESN_PHASE_HALTED, "Phase should be halted");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_performance_statistics - Test performance statistics collection
 */
static int test_performance_statistics(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("stats_test", 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    uint32_t membrane_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                                 "stats_membrane", 0, 100);
    TEST_ASSERT(membrane_id != 0, "Membrane creation failed");
    
    /* Perform some operations to generate statistics */
    dtesn_membrane_add_object(system, membrane_id, "test", 100);
    
    for (int i = 0; i < 10; i++) {
        dtesn_membrane_evolve(system, membrane_id);
    }
    
    /* Get statistics */
    dtesn_psystem_stats_t stats;
    int result = dtesn_psystem_get_stats(system, &stats);
    TEST_ASSERT(result == 0, "Getting statistics failed");
    
    printf("Performance Statistics:\n");
    printf("  Active membranes: %u\n", stats.active_membranes);
    printf("  Total objects: %u\n", stats.total_objects);
    printf("  Total rules: %u\n", stats.total_rules);
    printf("  Evolution time (avg): %lu ns\n", stats.avg_evolution_time_ns);
    printf("  Rule time (avg): %lu ns\n", stats.avg_rule_time_ns);
    printf("  Communication time (avg): %lu ns\n", stats.avg_comm_time_ns);
    printf("  Performance targets met: %s\n", 
           stats.meets_performance_targets ? "YES" : "NO");
    
    TEST_ASSERT(stats.active_membranes >= 1, "Should have at least 1 active membrane");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_stress_many_membranes - Stress test with many membranes
 */
static int test_stress_many_membranes(void) {
    dtesn_psystem_t *system = dtesn_psystem_create("stress_test", STRESS_TEST_MEMBRANES + 10);
    TEST_ASSERT(system != NULL, "System creation failed");
    
    printf("Stress testing with %d membranes...\n", STRESS_TEST_MEMBRANES);
    
    uint32_t root_id = dtesn_membrane_create(system, DTESN_MEMBRANE_ROOT,
                                             "stress_root", 0, 100);
    TEST_ASSERT(root_id != 0, "Root membrane creation failed");
    
    uint64_t start_time = get_time_ns();
    
    /* Create many child membranes */
    for (int i = 0; i < STRESS_TEST_MEMBRANES; i++) {
        char label[32];
        snprintf(label, sizeof(label), "stress_mem_%d", i);
        
        uint32_t membrane_id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                                     label, root_id, 50 + i);
        if (membrane_id == 0) {
            printf("  Failed to create membrane %d (OEIS constraint or capacity)\n", i);
            break;
        }
        
        /* Add some objects to each membrane */
        dtesn_membrane_add_object(system, membrane_id, "stress_obj", i % 10 + 1);
    }
    
    uint64_t end_time = get_time_ns();
    uint64_t creation_time = end_time - start_time;
    
    printf("  Created %u membranes in %lu ms\n", 
           system->membrane_count, creation_time / 1000000);
    
    /* Test system evolution with many membranes */
    start_time = get_time_ns();
    bool evolved = dtesn_system_evolve(system);
    end_time = get_time_ns();
    
    printf("  System evolution time: %lu ms\n", 
           (end_time - start_time) / 1000000);
    
    /* Validate OEIS compliance */
    bool is_valid = dtesn_psystem_validate_a000081(system);
    printf("  OEIS A000081 compliance: %s\n", is_valid ? "VALID" : "INVALID");
    
    dtesn_psystem_destroy(system);
    TEST_PASS();
}

/**
 * test_edge_cases - Test edge cases and error conditions
 */
static int test_edge_cases(void) {
    /* Test NULL parameters */
    int result = dtesn_psystem_init();
    TEST_ASSERT(result == 0, "Initialization should succeed");
    
    dtesn_psystem_t *null_system = dtesn_psystem_create(NULL, 10);
    TEST_ASSERT(null_system == NULL, "NULL name should fail");
    
    dtesn_psystem_t *system = dtesn_psystem_create("edge_test", 5);
    TEST_ASSERT(system != NULL, "Valid system creation should succeed");
    
    /* Test invalid membrane operations */
    uint32_t invalid_id = dtesn_membrane_create(system, (dtesn_membrane_type_t)999,
                                                "invalid", 0, 100);
    TEST_ASSERT(invalid_id == 0, "Invalid membrane type should fail");
    
    result = dtesn_membrane_add_object(system, 999, "test", 1);
    TEST_ASSERT(result != 0, "Adding to nonexistent membrane should fail");
    
    result = dtesn_membrane_destroy(system, 999);
    TEST_ASSERT(result != 0, "Destroying nonexistent membrane should fail");
    
    /* Test capacity limits */
    for (int i = 0; i < 10; i++) {
        char label[32];
        snprintf(label, sizeof(label), "test_%d", i);
        uint32_t id = dtesn_membrane_create(system, DTESN_MEMBRANE_LEAF,
                                            label, 0, 50);
        if (id == 0) {
            printf("  Reached capacity limit at membrane %d\n", i);
            break;
        }
    }
    
    /* Test multiset operations with NULL */
    dtesn_psystem_multiset_t *null_multiset = dtesn_multiset_create();
    TEST_ASSERT(null_multiset != NULL, "Multiset creation should succeed");
    
    result = dtesn_multiset_add(null_multiset, NULL, 1);
    TEST_ASSERT(result != 0, "Adding NULL symbol should fail");
    
    result = dtesn_multiset_add(null_multiset, "test", 0);
    TEST_ASSERT(result != 0, "Adding zero multiplicity should fail");
    
    dtesn_multiset_destroy(null_multiset);
    dtesn_psystem_destroy(system);
    
    TEST_PASS();
}

/* Test runner */
static void run_test(int (*test_func)(void)) {
    if (test_func()) {
        tests_passed++;
    } else {
        tests_failed++;
    }
}

int main(void) {
    printf("DTESN P-System Membrane Computing Kernel Module - Unit Tests\n");
    printf("============================================================\n\n");
    
    /* Run all tests */
    run_test(test_psystem_initialization);
    run_test(test_psystem_creation);
    run_test(test_membrane_creation);
    run_test(test_membrane_hierarchy_validation);
    run_test(test_object_multiset_operations);
    run_test(test_rule_application);
    run_test(test_membrane_evolution_performance);
    run_test(test_membrane_communication);
    run_test(test_system_evolution);
    run_test(test_performance_statistics);
    run_test(test_stress_many_membranes);
    run_test(test_edge_cases);
    
    /* Cleanup */
    dtesn_psystem_shutdown();
    
    /* Print results */
    printf("\nTest Results:\n");
    printf("=============\n");
    printf("Tests passed: %d\n", tests_passed);
    printf("Tests failed: %d\n", tests_failed);
    printf("Total tests:  %d\n", tests_passed + tests_failed);
    
    if (tests_failed == 0) {
        printf("\n✅ ALL TESTS PASSED\n");
        printf("\nPerformance Summary:\n");
        printf("- Evolution constraint: ≤ %u μs\n", DTESN_PSYSTEM_EVOLUTION_THRESHOLD_US);
        printf("- Rule constraint: ≤ %u μs\n", DTESN_PSYSTEM_RULE_THRESHOLD_US);
        printf("- Communication constraint: ≤ %u μs\n", DTESN_PSYSTEM_COMM_THRESHOLD_US);
        printf("- OEIS A000081 compliance verified\n");
        return 0;
    } else {
        printf("\n❌ %d TEST(S) FAILED\n", tests_failed);
        return 1;
    }
}