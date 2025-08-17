/*
 * Hello DTESN - Basic DTESN Library Example
 * ========================================
 * 
 * A simple example demonstrating the basic usage of the libdtesn
 * user-space programming library. Shows instance creation, evolution,
 * membrane operations, and cleanup.
 */

#include "../lib/libdtesn/libdtesn.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>

/* Example parameters */
#define EXAMPLE_DEPTH           4
#define EXAMPLE_ORDER           5
#define EXAMPLE_NEURONS         100
#define EXAMPLE_MEMBRANES       9      /* OEIS A000081[4] = 9 */
#define EXAMPLE_INPUT_DIM       10
#define EXAMPLE_OUTPUT_DIM      5
#define EXAMPLE_EVOLUTION_STEPS 10

static void print_version_info(void)
{
    int major, minor, patch;
    const char *version = dtesn_get_version(&major, &minor, &patch);
    printf("Hello DTESN Example Application\n");
    printf("libdtesn version: %s (%d.%d.%d)\n", version, major, minor, patch);
    printf("Built with DTESN kernel interface support\n\n");
}

static void print_usage(const char *program_name)
{
    print_version_info();
    printf("Usage: %s [options]\n", program_name);
    printf("Options:\n");
    printf("  -h, --help     Show this help message\n");
    printf("  -v, --verbose  Enable verbose output\n");
    printf("  -d, --debug    Enable debug output\n");
    printf("  --membrane     Test membrane operations\n");
    printf("  --bseries      Test B-series computations\n");
    printf("  --esn          Test ESN operations\n");
    printf("  --all          Run all tests (default)\n");
}

static int test_basic_operations(bool verbose)
{
    printf("=== Basic DTESN Operations Test ===\n");
    
    /* Create DTESN instance */
    struct dtesn_create_params params = {
        .depth = EXAMPLE_DEPTH,
        .max_order = EXAMPLE_ORDER,
        .neuron_count = EXAMPLE_NEURONS,
        .membrane_count = EXAMPLE_MEMBRANES,
        .input_dim = EXAMPLE_INPUT_DIM,
        .output_dim = EXAMPLE_OUTPUT_DIM,
        .flags = DTESN_CREATE_VALIDATE_OEIS | DTESN_CREATE_REAL_TIME
    };
    strcpy(params.label, "hello_dtesn_example");
    
    dtesn_handle_t *handle = NULL;
    int result = dtesn_create(&params, &handle);
    if (result != 0) {
        printf("❌ Failed to create DTESN instance: %s\n", dtesn_strerror(result));
        return result;
    }
    
    if (verbose) {
        printf("✅ Created DTESN instance (depth=%u, neurons=%u, membranes=%u)\n",
               params.depth, params.neuron_count, params.membrane_count);
    }
    
    /* Prepare test input */
    float input[EXAMPLE_INPUT_DIM];
    for (int i = 0; i < EXAMPLE_INPUT_DIM; i++) {
        input[i] = 0.1f * (i + 1);  /* Simple test pattern */
    }
    
    /* Evolve the DTESN instance */
    result = dtesn_evolve(handle, input, EXAMPLE_INPUT_DIM, EXAMPLE_EVOLUTION_STEPS, DTESN_EVOLVE_SYNCHRONOUS);
    if (result != 0) {
        printf("❌ Failed to evolve DTESN instance: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Evolved DTESN instance for %u steps\n", EXAMPLE_EVOLUTION_STEPS);
    }
    
    /* Get instance state */
    struct dtesn_state_info state;
    result = dtesn_get_state(handle, &state);
    if (result != 0) {
        printf("❌ Failed to get DTESN state: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Retrieved DTESN state information\n");
    }
    
    /* Clean up */
    result = dtesn_destroy(handle);
    if (result != 0) {
        printf("❌ Failed to destroy DTESN instance: %s\n", dtesn_strerror(result));
        return result;
    }
    
    printf("✅ Basic operations test completed successfully\n\n");
    return 0;
}

static int test_membrane_operations(bool verbose)
{
    printf("=== P-System Membrane Operations Test ===\n");
    
    /* Create DTESN instance */
    struct dtesn_create_params params = {
        .depth = EXAMPLE_DEPTH,
        .max_order = EXAMPLE_ORDER,
        .neuron_count = EXAMPLE_NEURONS,
        .membrane_count = 1,  /* Start with just root membrane */
        .input_dim = EXAMPLE_INPUT_DIM,
        .output_dim = EXAMPLE_OUTPUT_DIM,
        .flags = DTESN_CREATE_VALIDATE_OEIS
    };
    strcpy(params.label, "membrane_test");
    
    dtesn_handle_t *handle = NULL;
    int result = dtesn_create(&params, &handle);
    if (result != 0) {
        printf("❌ Failed to create DTESN instance: %s\n", dtesn_strerror(result));
        return result;
    }
    
    /* Create child membranes */
    uint32_t membrane_ids[8];  /* OEIS[4] - 1 = 8 child membranes */
    for (int i = 0; i < 8; i++) {
        result = dtesn_membrane_create(handle, 1, &membrane_ids[i]);  /* Parent is root (ID 1) */
        if (result != 0) {
            printf("❌ Failed to create membrane %d: %s\n", i, dtesn_strerror(result));
            dtesn_destroy(handle);
            return result;
        }
        
        if (verbose) {
            printf("✅ Created membrane %u (child of root)\n", membrane_ids[i]);
        }
    }
    
    /* Test membrane evolution */
    char evolution_data[] = "test_evolution_data";
    result = dtesn_membrane_evolve(handle, membrane_ids[0], 5, evolution_data, sizeof(evolution_data));
    if (result != 0) {
        printf("❌ Failed to evolve membrane: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Evolved membrane %u for 5 steps\n", membrane_ids[0]);
    }
    
    /* Test membrane communication */
    char message[] = "Hello from membrane!";
    result = dtesn_membrane_communicate(handle, membrane_ids[0], membrane_ids[1], message, sizeof(message));
    if (result != 0) {
        printf("❌ Failed membrane communication: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Communication between membranes %u and %u\n", membrane_ids[0], membrane_ids[1]);
    }
    
    /* Test OEIS compliance validation */
    bool is_compliant;
    result = dtesn_membrane_validate_oeis(handle, &is_compliant);
    if (result != 0) {
        printf("❌ Failed OEIS validation check: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ OEIS A000081 compliance: %s\n", is_compliant ? "VALID" : "INVALID");
    }
    
    /* Clean up */
    dtesn_destroy(handle);
    printf("✅ Membrane operations test completed successfully\n\n");
    return 0;
}

static int test_bseries_computations(bool verbose)
{
    printf("=== B-Series Computations Test ===\n");
    
    /* Create DTESN instance */
    struct dtesn_create_params params = {
        .depth = EXAMPLE_DEPTH,
        .max_order = EXAMPLE_ORDER,
        .neuron_count = EXAMPLE_NEURONS,
        .membrane_count = EXAMPLE_MEMBRANES,
        .input_dim = EXAMPLE_INPUT_DIM,
        .output_dim = EXAMPLE_OUTPUT_DIM,
        .flags = DTESN_CREATE_VALIDATE_OEIS
    };
    strcpy(params.label, "bseries_test");
    
    dtesn_handle_t *handle = NULL;
    int result = dtesn_create(&params, &handle);
    if (result != 0) {
        printf("❌ Failed to create DTESN instance: %s\n", dtesn_strerror(result));
        return result;
    }
    
    /* Prepare coefficients for B-series computation */
    double coefficients[EXAMPLE_ORDER];
    for (int i = 0; i < EXAMPLE_ORDER; i++) {
        coefficients[i] = 1.0 / (i + 1.0);  /* Simple coefficient pattern */
    }
    
    /* Get expected tree count for the order */
    uint32_t tree_count;
    result = dtesn_bseries_get_tree_count(EXAMPLE_ORDER, &tree_count);
    if (result != 0) {
        printf("❌ Failed to get tree count: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ B-series order %u has %u rooted trees (OEIS A000081)\n", EXAMPLE_ORDER, tree_count);
    }
    
    /* Allocate result buffer */
    double *results = malloc(tree_count * sizeof(double));
    if (!results) {
        printf("❌ Failed to allocate memory for results\n");
        dtesn_destroy(handle);
        return -1;
    }
    
    /* Compute B-series coefficients */
    result = dtesn_bseries_compute(handle, EXAMPLE_ORDER, coefficients, EXAMPLE_ORDER, results, tree_count);
    if (result != 0) {
        printf("❌ Failed B-series computation: %s\n", dtesn_strerror(result));
        free(results);
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Computed B-series coefficients for %u trees\n", tree_count);
        printf("   First few results: ");
        for (uint32_t i = 0; i < 5 && i < tree_count; i++) {
            printf("%.4f ", results[i]);
        }
        printf("%s\n", (tree_count > 5) ? "..." : "");
    }
    
    /* Validate OEIS compliance */
    bool is_compliant;
    result = dtesn_bseries_validate_oeis(handle, EXAMPLE_ORDER, &is_compliant);
    if (result != 0) {
        printf("❌ Failed OEIS validation: %s\n", dtesn_strerror(result));
        free(results);
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ B-series OEIS A000081 compliance: %s\n", is_compliant ? "VALID" : "INVALID");
    }
    
    /* Clean up */
    free(results);
    dtesn_destroy(handle);
    printf("✅ B-series computations test completed successfully\n\n");
    return 0;
}

static int test_esn_operations(bool verbose)
{
    printf("=== ESN Reservoir Operations Test ===\n");
    
    /* Create DTESN instance */
    struct dtesn_create_params params = {
        .depth = EXAMPLE_DEPTH,
        .max_order = EXAMPLE_ORDER,
        .neuron_count = EXAMPLE_NEURONS,
        .membrane_count = EXAMPLE_MEMBRANES,
        .input_dim = EXAMPLE_INPUT_DIM,
        .output_dim = EXAMPLE_OUTPUT_DIM,
        .flags = DTESN_CREATE_DEFAULT
    };
    strcpy(params.label, "esn_test");
    
    dtesn_handle_t *handle = NULL;
    int result = dtesn_create(&params, &handle);
    if (result != 0) {
        printf("❌ Failed to create DTESN instance: %s\n", dtesn_strerror(result));
        return result;
    }
    
    /* Prepare test input and state vectors */
    float input[EXAMPLE_INPUT_DIM];
    float state[EXAMPLE_NEURONS];
    float output[EXAMPLE_OUTPUT_DIM];
    
    for (int i = 0; i < EXAMPLE_INPUT_DIM; i++) {
        input[i] = sinf(0.1f * i);  /* Sinusoidal test pattern */
    }
    
    /* Initialize state to zero */
    memset(state, 0, sizeof(state));
    
    /* Update ESN reservoir state */
    result = dtesn_esn_update(handle, input, EXAMPLE_INPUT_DIM, state, EXAMPLE_NEURONS);
    if (result != 0) {
        printf("❌ Failed ESN state update: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Updated ESN reservoir state\n");
        printf("   State sample: %.4f %.4f %.4f ... %.4f\n", 
               state[0], state[1], state[2], state[EXAMPLE_NEURONS-1]);
    }
    
    /* Test ESN prediction */
    result = dtesn_esn_predict(handle, input, EXAMPLE_INPUT_DIM, output, EXAMPLE_OUTPUT_DIM);
    if (result != 0) {
        printf("❌ Failed ESN prediction: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Generated ESN prediction\n");
        printf("   Output: ");
        for (int i = 0; i < EXAMPLE_OUTPUT_DIM; i++) {
            printf("%.4f ", output[i]);
        }
        printf("\n");
    }
    
    /* Get reservoir information */
    uint32_t neuron_count;
    float spectral_radius, connectivity;
    result = dtesn_esn_get_reservoir_info(handle, &neuron_count, &spectral_radius, &connectivity);
    if (result != 0) {
        printf("❌ Failed to get reservoir info: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ Reservoir info: %u neurons, spectral radius: %.3f, connectivity: %.3f\n",
               neuron_count, spectral_radius, connectivity);
    }
    
    /* Get memory usage */
    size_t memory_usage;
    result = dtesn_esn_get_memory_usage(handle, &memory_usage);
    if (result != 0) {
        printf("❌ Failed to get memory usage: %s\n", dtesn_strerror(result));
        dtesn_destroy(handle);
        return result;
    }
    
    if (verbose) {
        printf("✅ ESN memory usage: %zu bytes (%.2f KB)\n", memory_usage, memory_usage / 1024.0);
    }
    
    /* Clean up */
    dtesn_destroy(handle);
    printf("✅ ESN operations test completed successfully\n\n");
    return 0;
}

static int test_performance_monitoring(bool verbose)
{
    printf("=== Performance Monitoring Test ===\n");
    
    /* Get global performance statistics */
    dtesn_perf_stats_t stats;
    int result = dtesn_get_performance_stats(NULL, &stats);
    if (result != 0) {
        printf("❌ Failed to get performance stats: %s\n", dtesn_strerror(result));
        return result;
    }
    
    if (verbose) {
        printf("✅ Global performance statistics:\n");
        printf("   Total API calls: %lu\n", stats.total_api_calls);
        printf("   Average call overhead: %lu ns (%.2f μs)\n", 
               stats.avg_call_overhead_ns, stats.avg_call_overhead_ns / 1000.0);
        printf("   Min/Max call time: %lu ns / %lu ns\n", stats.min_call_time_ns, stats.max_call_time_ns);
        printf("   Active instances: %u\n", stats.active_instances);
        printf("   Failed calls: %u\n", stats.failed_calls);
        printf("   Memory usage: %lu bytes\n", stats.memory_usage_bytes);
    }
    
    /* Check if we're meeting performance targets */
    bool performance_ok = (stats.avg_call_overhead_ns <= 1000);  /* ≤ 1μs target */
    printf("%s Performance target (≤1μs avg overhead): %s (actual: %.2f μs)\n",
           performance_ok ? "✅" : "❌",
           performance_ok ? "MET" : "NOT MET",
           stats.avg_call_overhead_ns / 1000.0);
    
    return 0;
}

int main(int argc, char *argv[])
{
    bool verbose = false;
    bool test_membrane = false;
    bool test_bseries = false;
    bool test_esn = false;
    bool test_all = true;
    
    /* Parse command line arguments */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        } else if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--debug") == 0) {
            dtesn_set_debug_level(4);  /* Enable debug output */
            verbose = true;
        } else if (strcmp(argv[i], "--membrane") == 0) {
            test_membrane = true;
            test_all = false;
        } else if (strcmp(argv[i], "--bseries") == 0) {
            test_bseries = true;
            test_all = false;
        } else if (strcmp(argv[i], "--esn") == 0) {
            test_esn = true;
            test_all = false;
        } else if (strcmp(argv[i], "--all") == 0) {
            test_all = true;
        } else {
            printf("Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }
    
    print_version_info();
    
    /* Initialize the DTESN library */
    printf("Initializing DTESN library...\n");
    int result = dtesn_init(NULL);  /* Use default configuration */
    if (result != 0) {
        printf("❌ Failed to initialize DTESN library: %s\n", dtesn_strerror(result));
        return 1;
    }
    printf("✅ DTESN library initialized successfully\n\n");
    
    /* Run tests */
    bool all_tests_passed = true;
    
    if (test_all || (!test_membrane && !test_bseries && !test_esn)) {
        if (test_basic_operations(verbose) != 0) all_tests_passed = false;
        if (test_membrane_operations(verbose) != 0) all_tests_passed = false;
        if (test_bseries_computations(verbose) != 0) all_tests_passed = false;
        if (test_esn_operations(verbose) != 0) all_tests_passed = false;
    } else {
        if (test_basic_operations(verbose) != 0) all_tests_passed = false;
        if (test_membrane && test_membrane_operations(verbose) != 0) all_tests_passed = false;
        if (test_bseries && test_bseries_computations(verbose) != 0) all_tests_passed = false;
        if (test_esn && test_esn_operations(verbose) != 0) all_tests_passed = false;
    }
    
    /* Show performance monitoring */
    if (test_performance_monitoring(verbose) != 0) all_tests_passed = false;
    
    /* Cleanup */
    printf("Cleaning up DTESN library...\n");
    result = dtesn_cleanup();
    if (result != 0) {
        printf("❌ Failed to cleanup DTESN library: %s\n", dtesn_strerror(result));
        all_tests_passed = false;
    } else {
        printf("✅ DTESN library cleanup completed\n");
    }
    
    /* Final result */
    printf("\n=== Test Results Summary ===\n");
    printf("Overall result: %s\n", all_tests_passed ? "✅ ALL TESTS PASSED" : "❌ SOME TESTS FAILED");
    
    return all_tests_passed ? 0 : 1;
}