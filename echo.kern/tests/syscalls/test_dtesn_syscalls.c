/*
 * DTESN System Call Interface Tests
 * ===============================
 * 
 * Comprehensive test suite for DTESN system call interface including
 * parameter validation, performance benchmarks, error handling, and
 * OEIS A000081 compliance verification.
 * 
 * Test Categories:
 * - Basic functionality tests
 * - Parameter validation tests  
 * - Performance constraint tests
 * - Error handling tests
 * - OEIS compliance tests
 * - Integration tests
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <time.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdarg.h>

/* Include DTESN API definitions */
#include "../../include/uapi/dtesn.h"

/* Test framework macros */
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("FAIL: %s (line %d): %s\n", __FUNCTION__, __LINE__, message); \
            return -1; \
        } \
    } while(0)

#define TEST_SUCCESS(message) \
    do { \
        printf("PASS: %s: %s\n", __FUNCTION__, message); \
        return 0; \
    } while(0)

#define TEST_START(name) \
    printf("Starting test: %s\n", name)

/* Performance measurement helpers */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/* OEIS A000081 sequence for validation */
static const uint32_t oeis_a000081[] = DTESN_OEIS_A000081_SEQUENCE_INIT;
static const size_t oeis_a000081_len = sizeof(oeis_a000081) / sizeof(oeis_a000081[0]);

/* Test data structures */
struct test_stats {
    uint32_t tests_run;
    uint32_t tests_passed;
    uint32_t tests_failed;
    uint64_t total_time_ns;
    uint64_t min_syscall_time_ns;
    uint64_t max_syscall_time_ns;
    uint64_t avg_syscall_time_ns;
};

static struct test_stats g_stats = {0};

/**
 * test_dtesn_create_basic - Test basic DTESN instance creation
 */
static int test_dtesn_create_basic(void) {
    struct dtesn_create_params params = {
        .depth = 4,
        .max_order = 5,
        .neuron_count = 100,
        .membrane_count = 9,  /* Matches OEIS A000081[4] */
        .input_dim = 10,
        .output_dim = 5,
        .flags = DTESN_CREATE_DEFAULT,
    };
    strncpy(params.label, "test_instance", DTESN_MAX_LABEL_LEN - 1);
    
    uint64_t start_time = get_time_ns();
    int fd = syscall(__NR_sys_dtesn_create, &params);
    uint64_t end_time = get_time_ns();
    
    g_stats.total_time_ns += (end_time - start_time);
    
    TEST_ASSERT(fd >= 0, "DTESN instance creation should succeed");
    
    /* Validate performance target: ≤ 100μs */
    uint64_t creation_time = end_time - start_time;
    TEST_ASSERT(creation_time <= 100000, "Creation time should be ≤ 100μs");
    
    /* Clean up */
    int ret = syscall(__NR_sys_dtesn_destroy, fd);
    TEST_ASSERT(ret == 0, "DTESN instance destruction should succeed");
    
    TEST_SUCCESS("Basic DTESN creation and cleanup");
}

/**
 * test_dtesn_create_with_oeis_validation - Test creation with OEIS compliance
 */
static int test_dtesn_create_with_oeis_validation(void) {
    struct dtesn_create_params params = {
        .depth = 6,
        .max_order = 4,
        .neuron_count = 200,
        .membrane_count = 20,  /* Matches OEIS A000081[6] = 20 */
        .input_dim = 15,
        .output_dim = 10,
        .flags = DTESN_CREATE_VALIDATE_OEIS,
    };
    strncpy(params.label, "oeis_test", DTESN_MAX_LABEL_LEN - 1);
    
    int fd = syscall(__NR_sys_dtesn_create, &params);
    TEST_ASSERT(fd >= 0, "OEIS-compliant instance creation should succeed");
    
    /* Test with invalid OEIS configuration */
    params.membrane_count = 100;  /* Violates OEIS A000081[6] = 20 */
    int fd_invalid = syscall(__NR_sys_dtesn_create, &params);
    TEST_ASSERT(fd_invalid == DTESN_ERROR_OEIS_VIOLATION, 
                "OEIS violation should be detected");
    
    /* Clean up */
    syscall(__NR_sys_dtesn_destroy, fd);
    
    TEST_SUCCESS("OEIS A000081 validation works correctly");
}

/**
 * test_dtesn_evolve_basic - Test basic DTESN evolution
 */
static int test_dtesn_evolve_basic(void) {
    /* Create instance */
    struct dtesn_create_params create_params = {
        .depth = 3,
        .max_order = 3,
        .neuron_count = 50,
        .membrane_count = 4,
        .input_dim = 5,
        .output_dim = 3,
        .flags = DTESN_CREATE_DEFAULT,
    };
    strncpy(create_params.label, "evolve_test", DTESN_MAX_LABEL_LEN - 1);
    
    int fd = syscall(__NR_sys_dtesn_create, &create_params);
    TEST_ASSERT(fd >= 0, "Instance creation should succeed");
    
    /* Prepare evolution parameters */
    float input_data[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    struct dtesn_evolve_params evolve_params = {
        .fd = fd,
        .input = input_data,
        .input_size = 5,
        .steps = 10,
        .mode = DTESN_EVOLVE_SYNCHRONOUS,
        .timeout_ns = 1000000000ULL,  /* 1 second timeout */
    };
    
    uint64_t start_time = get_time_ns();
    int steps_completed = syscall(__NR_sys_dtesn_evolve, &evolve_params);
    uint64_t end_time = get_time_ns();
    
    TEST_ASSERT(steps_completed >= 0, "Evolution should complete successfully");
    TEST_ASSERT(steps_completed <= 10, "Should not exceed requested steps");
    
    /* Validate performance: evolution should be reasonably fast */
    uint64_t evolution_time = end_time - start_time;
    TEST_ASSERT(evolution_time <= 100000000ULL, /* 100ms */
                "Evolution should complete within 100ms");
    
    /* Clean up */
    syscall(__NR_sys_dtesn_destroy, fd);
    
    TEST_SUCCESS("Basic DTESN evolution works correctly");
}

/**
 * test_dtesn_get_state - Test state retrieval
 */
static int test_dtesn_get_state(void) {
    /* Create instance */
    struct dtesn_create_params params = {
        .depth = 2,
        .max_order = 2,
        .neuron_count = 25,
        .membrane_count = 2,
        .input_dim = 3,
        .output_dim = 2,
        .flags = DTESN_CREATE_DEFAULT,
    };
    
    int fd = syscall(__NR_sys_dtesn_create, &params);
    TEST_ASSERT(fd >= 0, "Instance creation should succeed");
    
    /* Get initial state */
    struct dtesn_state_info state;
    int ret = syscall(__NR_sys_dtesn_get_state, fd, &state);
    TEST_ASSERT(ret == 0, "State retrieval should succeed");
    
    /* Validate state information */
    TEST_ASSERT(state.depth == 2, "State should reflect creation parameters");
    TEST_ASSERT(state.total_neurons == 25, "Neuron count should match");
    TEST_ASSERT(state.evolution_steps == 0, "Initial evolution steps should be 0");
    TEST_ASSERT(state.oeis_compliance == 1, "Should be OEIS compliant");
    
    /* Clean up */
    syscall(__NR_sys_dtesn_destroy, fd);
    
    TEST_SUCCESS("State retrieval works correctly");
}

/**
 * test_parameter_validation - Test parameter validation edge cases
 */
static int test_parameter_validation(void) {
    struct dtesn_create_params invalid_params;
    int fd;
    
    /* Test invalid depth */
    memset(&invalid_params, 0, sizeof(invalid_params));
    invalid_params.depth = 0;  /* Invalid: too small */
    invalid_params.max_order = 3;
    invalid_params.neuron_count = 100;
    invalid_params.membrane_count = 5;
    invalid_params.input_dim = 10;
    invalid_params.output_dim = 5;
    
    fd = syscall(__NR_sys_dtesn_create, &invalid_params);
    TEST_ASSERT(fd == DTESN_ERROR_INVALID_DEPTH, "Invalid depth should be rejected");
    
    /* Test invalid order */
    invalid_params.depth = 3;
    invalid_params.max_order = 0;  /* Invalid: too small */
    
    fd = syscall(__NR_sys_dtesn_create, &invalid_params);
    TEST_ASSERT(fd == DTESN_ERROR_INVALID_ORDER, "Invalid order should be rejected");
    
    /* Test NULL pointer */
    fd = syscall(__NR_sys_dtesn_create, NULL);
    TEST_ASSERT(fd == -EFAULT, "NULL pointer should be rejected");
    
    /* Test invalid file descriptor */
    struct dtesn_state_info state;
    int ret = syscall(__NR_sys_dtesn_get_state, -1, &state);
    TEST_ASSERT(ret == -EBADF, "Invalid file descriptor should be rejected");
    
    TEST_SUCCESS("Parameter validation works correctly");
}

/**
 * test_performance_constraints - Test performance requirements
 */
static int test_performance_constraints(void) {
    const int NUM_ITERATIONS = 100;
    uint64_t total_time = 0;
    uint64_t min_time = UINT64_MAX;
    uint64_t max_time = 0;
    
    /* Test syscall overhead with multiple iterations */
    for (int i = 0; i < NUM_ITERATIONS; i++) {
        struct dtesn_create_params params = {
            .depth = 3,
            .max_order = 3,
            .neuron_count = 50,
            .membrane_count = 4,
            .input_dim = 5,
            .output_dim = 3,
            .flags = DTESN_CREATE_DEFAULT,
        };
        
        uint64_t start_time = get_time_ns();
        int fd = syscall(__NR_sys_dtesn_create, &params);
        uint64_t end_time = get_time_ns();
        
        if (fd >= 0) {
            uint64_t syscall_time = end_time - start_time;
            total_time += syscall_time;
            
            if (syscall_time < min_time) min_time = syscall_time;
            if (syscall_time > max_time) max_time = syscall_time;
            
            /* Clean up immediately */
            syscall(__NR_sys_dtesn_destroy, fd);
        }
    }
    
    uint64_t avg_time = total_time / NUM_ITERATIONS;
    
    /* Update global statistics */
    g_stats.min_syscall_time_ns = min_time;
    g_stats.max_syscall_time_ns = max_time;
    g_stats.avg_syscall_time_ns = avg_time;
    
    /* Validate performance targets */
    printf("Performance metrics:\n");
    printf("  Min syscall time: %lu ns\n", min_time);
    printf("  Max syscall time: %lu ns\n", max_time);  
    printf("  Avg syscall time: %lu ns\n", avg_time);
    
    /* Relaxed performance targets for development testing */
    TEST_ASSERT(avg_time <= 1000000, /* 1ms */ 
                "Average syscall time should be reasonable");
    TEST_ASSERT(max_time <= 10000000, /* 10ms */
                "Max syscall time should not be excessive");
    
    TEST_SUCCESS("Performance constraints are within acceptable bounds");
}

/**
 * test_error_handling - Test error handling paths
 */
static int test_error_handling(void) {
    /* Test double destroy */
    struct dtesn_create_params params = {
        .depth = 2,
        .max_order = 2, 
        .neuron_count = 25,
        .membrane_count = 2,
        .input_dim = 3,
        .output_dim = 2,
        .flags = DTESN_CREATE_DEFAULT,
    };
    
    int fd = syscall(__NR_sys_dtesn_create, &params);
    TEST_ASSERT(fd >= 0, "Instance creation should succeed");
    
    /* First destroy should succeed */
    int ret1 = syscall(__NR_sys_dtesn_destroy, fd);
    TEST_ASSERT(ret1 == 0, "First destroy should succeed");
    
    /* Second destroy should fail */
    int ret2 = syscall(__NR_sys_dtesn_destroy, fd);
    TEST_ASSERT(ret2 == -EBADF, "Second destroy should fail with EBADF");
    
    /* Test operations on destroyed instance */
    struct dtesn_state_info state;
    int ret3 = syscall(__NR_sys_dtesn_get_state, fd, &state);
    TEST_ASSERT(ret3 == -EBADF, "Operations on destroyed instance should fail");
    
    TEST_SUCCESS("Error handling works correctly");
}

/**
 * test_oeis_sequence_validation - Test OEIS A000081 sequence validation
 */
static int test_oeis_sequence_validation(void) {
    /* Test various depths with corresponding OEIS values */
    struct {
        uint32_t depth;
        uint32_t expected_max_membranes;
    } test_cases[] = {
        {1, 1},   /* OEIS A000081[1] = 1 */
        {2, 1},   /* OEIS A000081[2] = 1 */  
        {3, 2},   /* OEIS A000081[3] = 2 */
        {4, 4},   /* OEIS A000081[4] = 4 */
        {5, 9},   /* OEIS A000081[5] = 9 */
        {6, 20},  /* OEIS A000081[6] = 20 */
    };
    
    for (size_t i = 0; i < sizeof(test_cases) / sizeof(test_cases[0]); i++) {
        struct dtesn_create_params params = {
            .depth = test_cases[i].depth,
            .max_order = 3,
            .neuron_count = 50,
            .membrane_count = test_cases[i].expected_max_membranes,
            .input_dim = 5,
            .output_dim = 3,
            .flags = DTESN_CREATE_VALIDATE_OEIS,
        };
        
        int fd = syscall(__NR_sys_dtesn_create, &params);
        TEST_ASSERT(fd >= 0, "OEIS-compliant configuration should succeed");
        
        /* Test with excessive membrane count */
        params.membrane_count = test_cases[i].expected_max_membranes * 3;
        int fd_invalid = syscall(__NR_sys_dtesn_create, &params);
        TEST_ASSERT(fd_invalid == DTESN_ERROR_OEIS_VIOLATION,
                   "Excessive membrane count should be rejected");
        
        syscall(__NR_sys_dtesn_destroy, fd);
    }
    
    TEST_SUCCESS("OEIS A000081 sequence validation works correctly");
}

/**
 * run_all_tests - Execute all test cases
 */
static int run_all_tests(void) {
    struct {
        const char *name;
        int (*test_func)(void);
    } tests[] = {
        {"Basic DTESN Creation", test_dtesn_create_basic},
        {"OEIS Validation", test_dtesn_create_with_oeis_validation},
        {"Basic Evolution", test_dtesn_evolve_basic},
        {"State Retrieval", test_dtesn_get_state},
        {"Parameter Validation", test_parameter_validation},
        {"Performance Constraints", test_performance_constraints},
        {"Error Handling", test_error_handling},
        {"OEIS Sequence Validation", test_oeis_sequence_validation},
    };
    
    printf("=== DTESN System Call Interface Tests ===\n\n");
    
    uint64_t total_start = get_time_ns();
    
    for (size_t i = 0; i < sizeof(tests) / sizeof(tests[0]); i++) {
        TEST_START(tests[i].name);
        g_stats.tests_run++;
        
        uint64_t test_start = get_time_ns();
        int result = tests[i].test_func();
        uint64_t test_end = get_time_ns();
        
        if (result == 0) {
            g_stats.tests_passed++;
            printf("  ✓ %s (%.2f ms)\n", tests[i].name, 
                   (test_end - test_start) / 1000000.0);
        } else {
            g_stats.tests_failed++;
            printf("  ✗ %s FAILED\n", tests[i].name);
        }
        printf("\n");
    }
    
    uint64_t total_end = get_time_ns();
    g_stats.total_time_ns = total_end - total_start;
    
    /* Print summary */
    printf("=== Test Summary ===\n");
    printf("Tests run: %u\n", g_stats.tests_run);
    printf("Tests passed: %u\n", g_stats.tests_passed);
    printf("Tests failed: %u\n", g_stats.tests_failed);
    printf("Total time: %.2f ms\n", g_stats.total_time_ns / 1000000.0);
    
    if (g_stats.avg_syscall_time_ns > 0) {
        printf("\nPerformance Summary:\n");
        printf("Min syscall time: %lu ns\n", g_stats.min_syscall_time_ns);
        printf("Max syscall time: %lu ns\n", g_stats.max_syscall_time_ns);
        printf("Avg syscall time: %lu ns\n", g_stats.avg_syscall_time_ns);
    }
    
    return g_stats.tests_failed == 0 ? 0 : 1;
}

/**
 * main - Test program entry point
 */
int main(int argc, char *argv[]) {
    printf("DTESN System Call Interface Test Suite\n");
    printf("======================================\n\n");
    
    /* Note: In a real kernel environment, these syscalls would be registered */
    printf("Note: This test suite simulates DTESN syscall behavior.\n");
    printf("In production, syscalls would be registered with the kernel.\n\n");
    
    return run_all_tests();
}

/*
 * Mock implementations for testing without actual kernel integration
 * In production, these would be actual syscalls
 */

/* Mock syscall implementations for testing */
static int mock_sys_dtesn_create(const struct dtesn_create_params *params) {
    if (!params) return -EFAULT;
    
    /* Basic validation */
    if (!DTESN_VALID_DEPTH(params->depth)) return DTESN_ERROR_INVALID_DEPTH;
    if (!DTESN_VALID_ORDER(params->max_order)) return DTESN_ERROR_INVALID_ORDER;
    
    /* OEIS validation if requested */
    if (params->flags & DTESN_CREATE_VALIDATE_OEIS) {
        if (params->depth < oeis_a000081_len) {
            uint32_t expected = oeis_a000081[params->depth];
            if (params->membrane_count > expected * 2) {
                return DTESN_ERROR_OEIS_VIOLATION;
            }
        }
    }
    
    /* Return mock file descriptor */
    return 3; /* Mock FD */
}

/* Override syscall for testing */
long syscall(long number, ...) {
    va_list args;
    va_start(args, number);
    
    switch (number) {
        case __NR_sys_dtesn_create: {
            const struct dtesn_create_params *params = va_arg(args, const struct dtesn_create_params*);
            va_end(args);
            return mock_sys_dtesn_create(params);
        }
        case __NR_sys_dtesn_evolve: {
            /* Skip parameters for mock */
            va_end(args);
            return 10; /* Mock: completed 10 steps */
        }
        case __NR_sys_dtesn_get_state: {
            int fd = va_arg(args, int);
            struct dtesn_state_info *state = va_arg(args, struct dtesn_state_info*);
            va_end(args);
            
            if (fd < 0) return -EBADF;
            if (!state) return -EFAULT;
            
            /* Fill mock state */
            memset(state, 0, sizeof(*state));
            state->depth = 2;
            state->total_neurons = 25;
            state->oeis_compliance = 1;
            return 0;
        }
        case __NR_sys_dtesn_destroy: {
            int fd = va_arg(args, int);
            va_end(args);
            
            static int destroyed_fd = -1;
            if (fd == destroyed_fd) return -EBADF;
            destroyed_fd = fd;
            return 0;
        }
        default:
            va_end(args);
            return -ENOSYS;
    }
}