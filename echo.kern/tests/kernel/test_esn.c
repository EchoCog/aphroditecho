/*
 * DTESN ESN Reservoir Test Suite
 * =============================
 * 
 * Comprehensive test suite for ESN reservoir implementation including
 * performance validation, OEIS A000081 compliance, and integration tests.
 */

#include "include/dtesn/esn.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include <math.h>

/* Test configuration */
#define TEST_MAX_RESERVOIR_SIZE 1000
#define TEST_MAX_INPUT_SIZE     100
#define TEST_NUM_ITERATIONS     100
#define TEST_TOLERANCE          1e-6f

/* Test statistics */
static struct {
    uint32_t tests_run;
    uint32_t tests_passed;
    uint32_t tests_failed;
    uint64_t total_test_time_ns;
} g_test_stats = {0};

/* Forward declarations */
static uint64_t get_time_ns(void);
static void print_test_result(const char *test_name, bool passed, uint64_t time_ns);
static bool test_esn_init(void);
static bool test_esn_config_validation(void);
static bool test_esn_reservoir_creation(void);
static bool test_esn_state_update_basic(void);
static bool test_esn_state_update_performance(void);
static bool test_esn_sparse_matrix_operations(void);
static bool test_esn_sparse_matrix_performance(void);
static bool test_esn_hardware_detection(void);
static bool test_esn_hardware_acceleration(void);
static bool test_esn_adaptive_scaling(void);
static bool test_esn_oeis_compliance(void);
static bool test_esn_memory_management(void);
static bool test_esn_error_handling(void);

/**
 * Get current time in nanoseconds
 */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Print test result
 */
static void print_test_result(const char *test_name, bool passed, uint64_t time_ns) {
    printf("%-40s: %s (%.3f ms)\n", 
           test_name, 
           passed ? "PASS" : "FAIL", 
           time_ns / 1e6);
    
    g_test_stats.tests_run++;
    if (passed) {
        g_test_stats.tests_passed++;
    } else {
        g_test_stats.tests_failed++;
    }
    g_test_stats.total_test_time_ns += time_ns;
}

/**
 * Test ESN subsystem initialization
 */
static bool test_esn_init(void) {
    uint64_t start_time = get_time_ns();
    
    int result = dtesn_esn_init();
    bool passed = (result == 0);
    
    if (passed) {
        /* Test double initialization should not fail */
        result = dtesn_esn_init();
        passed = (result == 0);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Subsystem Initialization", passed, test_time);
    
    return passed;
}

/**
 * Test ESN configuration validation
 */
static bool test_esn_config_validation(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    int result;
    
    /* Test default configuration */
    result = dtesn_esn_config_default(&config);
    passed = passed && (result == 0);
    
    /* Test valid configuration */
    config.reservoir_size = 100;
    config.input_size = 10;
    config.spectral_radius = 0.95f;
    config.leak_rate = 0.3f;
    config.connectivity = 0.1f;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "test_reservoir");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    /* Test invalid configurations */
    config.reservoir_size = 0; /* Invalid */
    reservoir = esn_reservoir_init(&config, "invalid_reservoir");
    passed = passed && (reservoir == NULL);
    
    config.reservoir_size = 100;
    config.spectral_radius = 1.5f; /* Invalid */
    reservoir = esn_reservoir_init(&config, "invalid_reservoir");
    passed = passed && (reservoir == NULL);
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Configuration Validation", passed, test_time);
    
    return passed;
}

/**
 * Test ESN reservoir creation and destruction
 */
static bool test_esn_reservoir_creation(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    
    /* Test basic creation */
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "test_reservoir");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        /* Verify basic properties */
        passed = passed && (reservoir->config.reservoir_size == config.reservoir_size);
        passed = passed && (reservoir->config.input_size == config.input_size);
        passed = passed && (reservoir->state == DTESN_ESN_STATE_INITIALIZED);
        passed = passed && (reservoir->x_current != NULL);
        passed = passed && (reservoir->x_previous != NULL);
        passed = passed && (reservoir->W_res != NULL);
        passed = passed && (reservoir->W_in != NULL);
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    /* Test creation with different sizes */
    for (uint32_t size = 10; size <= 500; size += 50) {
        config.reservoir_size = size;
        reservoir = esn_reservoir_init(&config, NULL);
        passed = passed && (reservoir != NULL);
        
        if (reservoir) {
            passed = passed && (reservoir->config.reservoir_size == size);
            dtesn_esn_reservoir_destroy(reservoir);
        }
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Reservoir Creation", passed, test_time);
    
    return passed;
}

/**
 * Test basic ESN state update functionality
 */
static bool test_esn_state_update_basic(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.reservoir_size = 50;
    config.input_size = 5;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "state_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        float input[5] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
        
        /* Test state update */
        int result = esn_state_update(reservoir, input, 5);
        passed = passed && (result == 0);
        
        /* Verify state has changed */
        bool state_changed = false;
        for (uint32_t i = 0; i < config.reservoir_size; i++) {
            if (fabsf(reservoir->x_current[i]) > TEST_TOLERANCE) {
                state_changed = true;
                break;
            }
        }
        passed = passed && state_changed;
        
        /* Test multiple updates */
        for (int i = 0; i < 10; i++) {
            input[0] = (float)i * 0.1f;
            result = esn_state_update(reservoir, input, 5);
            passed = passed && (result == 0);
        }
        
        /* Verify performance statistics */
        passed = passed && (reservoir->total_updates == 11);
        passed = passed && (reservoir->avg_update_time_ns > 0);
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN State Update Basic", passed, test_time);
    
    return passed;
}

/**
 * Test ESN state update performance constraints
 */
static bool test_esn_state_update_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.reservoir_size = TEST_MAX_RESERVOIR_SIZE;
    config.input_size = TEST_MAX_INPUT_SIZE;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "perf_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        float *input = malloc(config.input_size * sizeof(float));
        passed = passed && (input != NULL);
        
        if (input) {
            /* Initialize random input */
            for (uint32_t i = 0; i < config.input_size; i++) {
                input[i] = (float)(rand()) / RAND_MAX;
            }
            
            /* Perform multiple updates and measure timing */
            uint64_t total_update_time = 0;
            uint64_t max_update_time = 0;
            
            for (int i = 0; i < TEST_NUM_ITERATIONS; i++) {
                uint64_t update_start = get_time_ns();
                int result = esn_state_update(reservoir, input, config.input_size);
                uint64_t update_time = get_time_ns() - update_start;
                
                passed = passed && (result == 0);
                total_update_time += update_time;
                
                if (update_time > max_update_time) {
                    max_update_time = update_time;
                }
                
                /* Vary input slightly */
                input[i % config.input_size] += 0.01f;
            }
            
            uint64_t avg_update_time = total_update_time / TEST_NUM_ITERATIONS;
            
            /* Check performance constraints */
            passed = passed && (avg_update_time <= DTESN_ESN_STATE_UPDATE_THRESHOLD_US * 1000);
            passed = passed && (max_update_time <= DTESN_ESN_STATE_UPDATE_THRESHOLD_US * 1000 * 2);
            
            printf("    Average update time: %.3f μs (target: ≤ %d μs)\n", 
                   avg_update_time / 1000.0, DTESN_ESN_STATE_UPDATE_THRESHOLD_US);
            printf("    Maximum update time: %.3f μs\n", max_update_time / 1000.0);
            
            free(input);
        }
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN State Update Performance", passed, test_time);
    
    return passed;
}

/**
 * Test sparse matrix operations
 */
static bool test_esn_sparse_matrix_operations(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Test sparse matrix creation */
    dtesn_esn_sparse_matrix_t *matrix = dtesn_esn_sparse_matrix_create(100, 100, 0.1f);
    passed = passed && (matrix != NULL);
    
    if (matrix) {
        /* Verify matrix properties */
        passed = passed && (matrix->rows == 100);
        passed = passed && (matrix->cols == 100);
        passed = passed && (matrix->sparsity == 0.1f);
        passed = passed && (matrix->nnz > 0);
        passed = passed && (matrix->row_ptr != NULL);
        passed = passed && (matrix->col_idx != NULL);
        passed = passed && (matrix->values != NULL);
        
        /* Test sparse matrix-vector multiplication */
        float *input = malloc(100 * sizeof(float));
        float *output = malloc(100 * sizeof(float));
        
        if (input && output) {
            /* Initialize input vector */
            for (int i = 0; i < 100; i++) {
                input[i] = (float)i / 100.0f;
            }
            
            /* Fill matrix with test values */
            for (uint32_t i = 0; i < matrix->nnz; i++) {
                matrix->values[i] = 1.0f;
            }
            
            /* Perform multiplication */
            int result = esn_sparse_multiply(matrix, input, output);
            passed = passed && (result == 0);
            
            /* Verify output is reasonable */
            bool output_valid = true;
            for (int i = 0; i < 100; i++) {
                if (isnan(output[i]) || isinf(output[i])) {
                    output_valid = false;
                    break;
                }
            }
            passed = passed && output_valid;
        }
        
        free(input);
        free(output);
        dtesn_esn_sparse_matrix_destroy(matrix);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Sparse Matrix Operations", passed, test_time);
    
    return passed;
}

/**
 * Test sparse matrix performance constraints
 */
static bool test_esn_sparse_matrix_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    uint32_t matrix_size = 1000;
    float sparsity = 0.1f;
    
    dtesn_esn_sparse_matrix_t *matrix = dtesn_esn_sparse_matrix_create(matrix_size, matrix_size, sparsity);
    passed = passed && (matrix != NULL);
    
    if (matrix) {
        float *input = malloc(matrix_size * sizeof(float));
        float *output = malloc(matrix_size * sizeof(float));
        
        if (input && output) {
            /* Initialize test data */
            for (uint32_t i = 0; i < matrix_size; i++) {
                input[i] = (float)(rand()) / RAND_MAX;
            }
            
            for (uint32_t i = 0; i < matrix->nnz; i++) {
                matrix->values[i] = (float)(rand()) / RAND_MAX;
            }
            
            /* Perform multiple multiplications and measure timing */
            uint64_t total_mult_time = 0;
            uint64_t max_mult_time = 0;
            
            for (int i = 0; i < 100; i++) {
                uint64_t mult_start = get_time_ns();
                int result = esn_sparse_multiply(matrix, input, output);
                uint64_t mult_time = get_time_ns() - mult_start;
                
                passed = passed && (result == 0);
                total_mult_time += mult_time;
                
                if (mult_time > max_mult_time) {
                    max_mult_time = mult_time;
                }
            }
            
            uint64_t avg_mult_time = total_mult_time / 100;
            
            /* Check performance constraints */
            passed = passed && (avg_mult_time <= DTESN_ESN_MATRIX_MULT_THRESHOLD_US * 1000);
            
            printf("    Average multiply time: %.3f μs (target: ≤ %d μs)\n", 
                   avg_mult_time / 1000.0, DTESN_ESN_MATRIX_MULT_THRESHOLD_US);
            printf("    Matrix size: %u x %u, sparsity: %.1f%%, nnz: %u\n",
                   matrix_size, matrix_size, sparsity * 100.0f, matrix->nnz);
        }
        
        free(input);
        free(output);
        dtesn_esn_sparse_matrix_destroy(matrix);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Sparse Matrix Performance", passed, test_time);
    
    return passed;
}

/**
 * Test hardware acceleration detection
 */
static bool test_esn_hardware_detection(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_accel_context_t contexts[16];
    int num_contexts = dtesn_esn_detect_hardware(contexts, 16);
    
    passed = passed && (num_contexts >= 0);
    
    if (num_contexts > 0) {
        printf("    Detected %d acceleration contexts:\n", num_contexts);
        for (int i = 0; i < num_contexts; i++) {
            printf("      %s: %s (factor: %.1fx)\n",
                   contexts[i].device_name,
                   contexts[i].is_available ? "Available" : "Not Available",
                   contexts[i].performance_factor);
        }
    } else {
        printf("    No hardware acceleration detected\n");
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Hardware Detection", passed, test_time);
    
    return passed;
}

/**
 * Test hardware acceleration functionality
 */
static bool test_esn_hardware_acceleration(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.accel_type = DTESN_ESN_ACCEL_SIMD;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "accel_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        /* Try to enable SIMD acceleration */
        int result = esn_hardware_accel(reservoir, DTESN_ESN_ACCEL_SIMD);
        
        if (result == 0) {
            passed = passed && (reservoir->accel_available == true);
            printf("    SIMD acceleration enabled\n");
        } else {
            printf("    SIMD acceleration not available\n");
        }
        
        /* Test with GPU (should fail for now) */
        result = esn_hardware_accel(reservoir, DTESN_ESN_ACCEL_GPU);
        passed = passed && (result != 0); /* Expected to fail */
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Hardware Acceleration", passed, test_time);
    
    return passed;
}

/**
 * Test OEIS A000081 compliance validation
 */
static bool test_esn_oeis_compliance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.oeis_compliance = true;
    config.tree_depth = 5;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "oeis_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        /* Test OEIS validation */
        bool is_compliant = dtesn_esn_validate_a000081(reservoir);
        passed = passed && is_compliant;
        
        printf("    OEIS A000081 compliance: %s\n", is_compliant ? "Valid" : "Invalid");
        printf("    Tree depth: %u, reservoir size: %u\n", 
               config.tree_depth, config.reservoir_size);
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN OEIS A000081 Compliance", passed, test_time);
    
    return passed;
}

/**
 * Test error handling
 */
static bool test_esn_error_handling(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Test NULL pointer handling */
    int result = esn_state_update(NULL, NULL, 0);
    passed = passed && (result == DTESN_ESN_EINVAL);
    
    /* Test invalid input size */
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.input_size = 5;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "error_test");
    if (reservoir) {
        float input[10] = {0};
        result = esn_state_update(reservoir, input, 10); /* Wrong size */
        passed = passed && (result == DTESN_ESN_EINVAL);
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Error Handling", passed, test_time);
    
    return passed;
}

/**
 * Test adaptive scaling functionality
 */
static bool test_esn_adaptive_scaling(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "adaptive_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        float initial_spectral_radius = reservoir->current_spectral_radius;
        
        /* Test adaptive scaling */
        int result = esn_adaptive_scale(reservoir, 0.5f, 0.8f);
        passed = passed && (result == 0);
        
        /* Verify spectral radius changed */
        passed = passed && (reservoir->current_spectral_radius != initial_spectral_radius);
        
        /* Test stability check */
        float stability_metric;
        result = dtesn_esn_check_stability(reservoir, &stability_metric);
        passed = passed && (result == 0);
        passed = passed && (stability_metric >= 0.0f);
        
        printf("    Initial spectral radius: %.3f\n", initial_spectral_radius);
        printf("    Adapted spectral radius: %.3f\n", reservoir->current_spectral_radius);
        printf("    Stability metric: %.3f\n", stability_metric);
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Adaptive Scaling", passed, test_time);
    
    return passed;
}

/**
 * Test memory management and state save/load
 */
static bool test_esn_memory_management(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_esn_config_t config;
    dtesn_esn_config_default(&config);
    config.reservoir_size = 50;
    config.input_size = 5;
    config.output_size = 3;
    
    dtesn_esn_reservoir_t *reservoir = esn_reservoir_init(&config, "memory_test");
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        /* Update state to create some data */
        float input[5] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
        esn_state_update(reservoir, input, 5);
        
        /* Test state save */
        size_t buffer_size = 4096;
        void *buffer = malloc(buffer_size);
        passed = passed && (buffer != NULL);
        
        if (buffer) {
            int saved_bytes = dtesn_esn_save_state(reservoir, buffer, buffer_size);
            passed = passed && (saved_bytes > 0);
            
            printf("    Saved state size: %d bytes\n", saved_bytes);
            
            /* Modify state */
            esn_state_update(reservoir, input, 5);
            
            /* Test state load */
            int result = dtesn_esn_load_state(reservoir, buffer, saved_bytes);
            passed = passed && (result == 0);
            
            free(buffer);
        }
        
        dtesn_esn_reservoir_destroy(reservoir);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("ESN Memory Management", passed, test_time);
    
    return passed;
}

/**
 * Main test runner
 */
int main(void) {
    printf("DTESN ESN Reservoir Test Suite\n");
    printf("==============================\n\n");
    
    srand((unsigned int)time(NULL));
    
    /* Run all tests */
    test_esn_init();
    test_esn_config_validation();
    test_esn_reservoir_creation();
    test_esn_state_update_basic();
    test_esn_state_update_performance();
    test_esn_sparse_matrix_operations();
    test_esn_sparse_matrix_performance();
    test_esn_hardware_detection();
    test_esn_hardware_acceleration();
    test_esn_adaptive_scaling();
    test_esn_oeis_compliance();
    test_esn_memory_management();
    test_esn_error_handling();
    
    /* Print summary */
    printf("\nTest Summary:\n");
    printf("=============\n");
    printf("Tests run:    %u\n", g_test_stats.tests_run);
    printf("Tests passed: %u\n", g_test_stats.tests_passed);
    printf("Tests failed: %u\n", g_test_stats.tests_failed);
    printf("Success rate: %.1f%%\n", 
           (float)g_test_stats.tests_passed / g_test_stats.tests_run * 100.0f);
    printf("Total time:   %.3f ms\n", g_test_stats.total_test_time_ns / 1e6);
    
    /* Cleanup */
    dtesn_esn_shutdown();
    
    return (g_test_stats.tests_failed == 0) ? 0 : 1;
}