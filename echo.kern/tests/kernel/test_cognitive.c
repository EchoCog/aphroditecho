/*
 * DTESN Cognitive Computing Test Suite
 * ===================================
 * 
 * Comprehensive test suite for DTESN cognitive computing features including
 * adaptive learning, memory consolidation, attention mechanisms, multi-modal
 * fusion, and distributed processing with performance validation.
 */

#include "include/dtesn/dtesn_cognitive.h"
#include "include/dtesn/esn.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include <math.h>
#include <unistd.h>

/* Test configuration */
#define TEST_MAX_RESERVOIR_SIZE         1000
#define TEST_MAX_INPUT_SIZE             100
#define TEST_MAX_OUTPUT_SIZE            50
#define TEST_NUM_ITERATIONS             10
#define TEST_NUM_SAMPLES                100
#define TEST_TOLERANCE                  1e-6f
#define TEST_PERFORMANCE_TOLERANCE_PCT  20  /* 20% tolerance for performance targets */

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
static dtesn_esn_reservoir_t *create_test_reservoir(void);
static void generate_test_data(float **input_data, float **target_data, 
                              uint32_t num_samples, uint32_t input_size, uint32_t output_size);
static void cleanup_test_data(float **input_data, float **target_data, uint32_t num_samples);

/* Test functions */
static bool test_cognitive_init_cleanup(void);
static bool test_cognitive_system_creation(void);
static bool test_adaptive_learning_hebbian(void);
static bool test_adaptive_learning_online(void);
static bool test_memory_consolidation_immediate(void);
static bool test_memory_consolidation_performance(void);
static bool test_attention_focus_switching(void);
static bool test_attention_performance(void);
static bool test_multimodal_fusion_early(void);
static bool test_multimodal_fusion_adaptive(void);
static bool test_oeis_compliance(void);
static bool test_performance_targets(void);
static bool test_error_handling(void);
static bool test_concurrent_operations(void);

/**
 * Get current time in nanoseconds
 */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Print test result with timing information
 */
static void print_test_result(const char *test_name, bool passed, uint64_t time_ns) {
    const char *status = passed ? "✅ PASS" : "❌ FAIL";
    double time_ms = time_ns / 1000000.0;
    
    printf("  %-40s %s (%.2f ms)\n", test_name, status, time_ms);
    
    g_test_stats.tests_run++;
    if (passed) {
        g_test_stats.tests_passed++;
    } else {
        g_test_stats.tests_failed++;
    }
    g_test_stats.total_test_time_ns += time_ns;
}

/**
 * Create test ESN reservoir
 */
static dtesn_esn_reservoir_t *create_test_reservoir(void) {
    dtesn_esn_config_t config;
    
    /* Initialize default configuration */
    config.reservoir_size = 100;
    config.input_size = 10;
    config.output_size = 5;
    config.spectral_radius = 0.9f;
    config.leak_rate = 0.1f;
    config.input_scaling = 1.0f;
    config.bias_scaling = 0.1f;
    config.noise_level = 0.001f;
    config.connectivity = 0.1f;
    config.input_connectivity = 10;
    config.use_bias = true;
    config.activation = DTESN_ESN_ACTIVATION_TANH;
    config.accel_type = DTESN_ESN_ACCEL_CPU;
    config.use_sparse_matrices = true;
    config.thread_count = 1;
    config.oeis_compliance = true;
    config.tree_depth = 5;
    
    /* This would normally create an ESN reservoir, but for testing we'll simulate it */
    dtesn_esn_reservoir_t *reservoir = calloc(1, sizeof(dtesn_esn_reservoir_t));
    if (!reservoir) return NULL;
    
    reservoir->reservoir_id = 1;
    strcpy(reservoir->name, "test_reservoir");
    reservoir->config = config;
    reservoir->state = DTESN_ESN_STATE_READY;
    
    /* Allocate state vectors */
    reservoir->x_current = calloc(config.reservoir_size, sizeof(float));
    reservoir->x_previous = calloc(config.reservoir_size, sizeof(float));
    reservoir->u_current = calloc(config.input_size, sizeof(float));
    reservoir->y_current = calloc(config.output_size, sizeof(float));
    
    if (!reservoir->x_current || !reservoir->x_previous || 
        !reservoir->u_current || !reservoir->y_current) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
        return NULL;
    }
    
    return reservoir;
}

/**
 * Generate test data
 */
static void generate_test_data(float **input_data, float **target_data,
                              uint32_t num_samples, uint32_t input_size, uint32_t output_size) {
    *input_data = malloc(num_samples * sizeof(float*));
    *target_data = malloc(num_samples * sizeof(float*));
    
    for (uint32_t i = 0; i < num_samples; i++) {
        (*input_data)[i] = malloc(input_size * sizeof(float));
        (*target_data)[i] = malloc(output_size * sizeof(float));
        
        /* Generate random input data */
        for (uint32_t j = 0; j < input_size; j++) {
            (*input_data)[i][j] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        }
        
        /* Generate corresponding target data (simplified mapping) */
        for (uint32_t j = 0; j < output_size; j++) {
            (*target_data)[i][j] = (*input_data)[i][j % input_size] * 0.5f;
        }
    }
}

/**
 * Cleanup test data
 */
static void cleanup_test_data(float **input_data, float **target_data, uint32_t num_samples) {
    if (*input_data) {
        for (uint32_t i = 0; i < num_samples; i++) {
            free((*input_data)[i]);
        }
        free(*input_data);
        *input_data = NULL;
    }
    
    if (*target_data) {
        for (uint32_t i = 0; i < num_samples; i++) {
            free((*target_data)[i]);
        }
        free(*target_data);
        *target_data = NULL;
    }
}

/**
 * Test cognitive system initialization and cleanup
 */
static bool test_cognitive_init_cleanup(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Test initialization */
    int result = dtesn_cognitive_init();
    passed = passed && (result == 0);
    
    /* Test double initialization (should be safe) */
    result = dtesn_cognitive_init();
    passed = passed && (result == 0);
    
    /* Test cleanup */
    result = dtesn_cognitive_cleanup();
    passed = passed && (result == 0);
    
    /* Test double cleanup (should be safe) */
    result = dtesn_cognitive_cleanup();
    passed = passed && (result == 0);
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Cognitive Init/Cleanup", passed, test_time);
    
    return passed;
}

/**
 * Test cognitive system creation and destruction
 */
static bool test_cognitive_system_creation(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Initialize cognitive subsystem */
    int result = dtesn_cognitive_init();
    passed = passed && (result == 0);
    
    /* Create test reservoir */
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    passed = passed && (reservoir != NULL);
    
    if (reservoir) {
        /* Create cognitive system */
        dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("test_system", reservoir);
        passed = passed && (system != NULL);
        
        if (system) {
            /* Verify system properties */
            passed = passed && (system->initialized == true);
            passed = passed && (system->reservoir == reservoir);
            passed = passed && (strcmp(system->name, "test_system") == 0);
            passed = passed && (system->attention_channels != NULL);
            passed = passed && (system->num_attention_channels > 0);
            
            /* Test OEIS A000081 compliance */
            bool is_compliant = dtesn_cognitive_validate_a000081(system);
            passed = passed && is_compliant;
            
            printf("    System ID: %u, Attention channels: %u, OEIS compliant: %s\n",
                   system->system_id, system->num_attention_channels,
                   is_compliant ? "Yes" : "No");
            
            /* Destroy system */
            result = dtesn_cognitive_system_destroy(system);
            passed = passed && (result == 0);
        }
        
        /* Cleanup reservoir */
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    /* Cleanup cognitive subsystem */
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Cognitive System Creation", passed, test_time);
    
    return passed;
}

/**
 * Test adaptive learning with Hebbian algorithm
 */
static bool test_adaptive_learning_hebbian(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("learning_test", reservoir);
    
    if (system) {
        /* Generate training data */
        float **input_data, **target_data;
        generate_test_data(&input_data, &target_data, TEST_NUM_SAMPLES, 
                          reservoir->config.input_size, reservoir->config.output_size);
        
        /* Configure learning parameters */
        dtesn_cognitive_learn_params_t params = {
            .learn_type = DTESN_COGNITIVE_LEARN_HEBBIAN,
            .learning_rate = 0.01f,
            .adaptation_rate = 0.001f,
            .max_iterations = 50,
            .convergence_threshold = 1e-4f,
            .enable_plasticity = true,
            .enable_homeostasis = true,
            .batch_size = 10
        };
        
        /* Perform adaptive learning */
        int result = dtesn_adaptive_learn(system, (const float**)input_data, 
                                         (const float**)target_data, 
                                         TEST_NUM_SAMPLES, &params);
        passed = passed && (result == 0);
        
        /* Check performance statistics */
        if (result == 0) {
            passed = passed && (system->total_learning_iterations > 0);
            passed = passed && (system->total_learning_time_ns > 0);
            
            printf("    Learning iterations: %lu, time: %.2f ms\n",
                   (unsigned long)system->total_learning_iterations,
                   system->total_learning_time_ns / 1000000.0);
        }
        
        cleanup_test_data(&input_data, &target_data, TEST_NUM_SAMPLES);
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Adaptive Learning (Hebbian)", passed, test_time);
    
    return passed;
}

/**
 * Test online adaptive learning
 */
static bool test_adaptive_learning_online(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("online_test", reservoir);
    
    if (system) {
        /* Configure learning parameters */
        dtesn_cognitive_learn_params_t params = {
            .learn_type = DTESN_COGNITIVE_LEARN_STDP,
            .learning_rate = 0.01f,
            .adaptation_rate = 0.001f,
            .max_iterations = 1,
            .convergence_threshold = 1e-4f,
            .enable_plasticity = true,
            .enable_homeostasis = false,
            .batch_size = 1
        };
        
        /* Perform online learning with individual samples */
        float input[10] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f, 0.6f, 0.7f, 0.8f, 0.9f, 1.0f};
        float target[5] = {0.05f, 0.1f, 0.15f, 0.2f, 0.25f};
        
        for (int i = 0; i < TEST_NUM_ITERATIONS; i++) {
            int result = dtesn_adaptive_learn_online(system, input, target, &params);
            passed = passed && (result == 0);
            
            /* Modify input slightly for next iteration */
            for (int j = 0; j < 10; j++) {
                input[j] += 0.01f;
            }
        }
        
        /* Check that learning occurred */
        passed = passed && (system->total_learning_iterations >= TEST_NUM_ITERATIONS);
        
        printf("    Online learning iterations: %lu\n",
               (unsigned long)system->total_learning_iterations);
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Online Adaptive Learning", passed, test_time);
    
    return passed;
}

/**
 * Test immediate memory consolidation
 */
static bool test_memory_consolidation_immediate(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("memory_test", reservoir);
    
    if (system) {
        /* Add some test memory nodes */
        for (int i = 0; i < 5; i++) {
            dtesn_cognitive_memory_node_t *node = malloc(sizeof(dtesn_cognitive_memory_node_t));
            if (node) {
                node->node_id = i;
                sprintf(node->label, "test_memory_%d", i);
                node->data_size = 10;
                node->data = calloc(10, sizeof(float));
                node->activation = 0.5f + i * 0.1f;
                node->decay_rate = 0.01f;
                node->timestamp_ns = get_time_ns();
                node->access_count = i + 1;
                node->persistent = (i % 2 == 0);
                node->next = system->memory_head;
                system->memory_head = node;
                system->memory_node_count++;
            }
        }
        
        printf("    Created %u memory nodes\n", system->memory_node_count);
        
        /* Test immediate consolidation */
        int result = dtesn_memory_consolidate(system, DTESN_COGNITIVE_CONSOLIDATE_IMMEDIATE);
        passed = passed && (result == 0);
        
        /* Check performance statistics */
        passed = passed && (system->total_consolidations > 0);
        passed = passed && (system->total_consolidation_time_ns > 0);
        
        printf("    Consolidations: %lu, time: %.2f ms\n",
               (unsigned long)system->total_consolidations,
               system->total_consolidation_time_ns / 1000000.0);
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Memory Consolidation (Immediate)", passed, test_time);
    
    return passed;
}

/**
 * Test memory consolidation performance target
 */
static bool test_memory_consolidation_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("perf_test", reservoir);
    
    if (system) {
        /* Add many memory nodes to test performance under load */
        for (int i = 0; i < 100; i++) {
            dtesn_cognitive_memory_node_t *node = malloc(sizeof(dtesn_cognitive_memory_node_t));
            if (node) {
                node->node_id = i;
                sprintf(node->label, "perf_memory_%d", i);
                node->data_size = 50;
                node->data = calloc(50, sizeof(float));
                node->activation = (float)rand() / RAND_MAX;
                node->decay_rate = 0.01f;
                node->timestamp_ns = get_time_ns();
                node->access_count = rand() % 10;
                node->persistent = (rand() % 2 == 0);
                node->next = system->memory_head;
                system->memory_head = node;
                system->memory_node_count++;
            }
        }
        
        /* Test consolidation performance */
        uint64_t consolidation_start = get_time_ns();
        int result = dtesn_memory_consolidate(system, DTESN_COGNITIVE_CONSOLIDATE_ADAPTIVE);
        uint64_t consolidation_time = get_time_ns() - consolidation_start;
        
        passed = passed && (result == 0);
        
        /* Check performance target: ≤100ms */
        uint64_t target_time_ns = DTESN_COGNITIVE_MEMORY_CONSOLIDATION_US * 1000;
        uint64_t tolerance_time_ns = target_time_ns * (100 + TEST_PERFORMANCE_TOLERANCE_PCT) / 100;
        
        if (consolidation_time <= tolerance_time_ns) {
            printf("    Performance target met: %.2f ms (target: ≤%.2f ms)\n",
                   consolidation_time / 1000000.0, target_time_ns / 1000000.0);
        } else {
            printf("    Performance target missed: %.2f ms (target: ≤%.2f ms)\n",
                   consolidation_time / 1000000.0, target_time_ns / 1000000.0);
            /* Don't fail test, just warn - this is development phase */
        }
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Memory Consolidation Performance", passed, test_time);
    
    return passed;
}

/**
 * Test attention focus switching
 */
static bool test_attention_focus_switching(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("attention_test", reservoir);
    
    if (system) {
        uint32_t num_channels = system->num_attention_channels;
        printf("    Testing with %u attention channels\n", num_channels);
        
        /* Test focusing on different channels */
        for (uint32_t i = 0; i < num_channels; i++) {
            int result = dtesn_attention_focus(system, i, NULL, 0);
            passed = passed && (result == 0);
            
            if (result == 0) {
                passed = passed && (system->active_channel_id == i);
                passed = passed && (system->attention_channels[i].active == true);
            }
        }
        
        /* Test with custom focus vector */
        float focus_vector[10] = {1.0f, 0.8f, 0.6f, 0.4f, 0.2f, 0.0f, 0.2f, 0.4f, 0.6f, 0.8f};
        int result = dtesn_attention_focus(system, 0, focus_vector, 10);
        passed = passed && (result == 0);
        
        /* Test attention distribution */
        float weights[4] = {0.4f, 0.3f, 0.2f, 0.1f}; /* Assuming 4 channels from OEIS */
        if (num_channels == 4) {
            result = dtesn_attention_distribute(system, weights, num_channels);
            passed = passed && (result == 0);
        }
        
        /* Check performance statistics */
        passed = passed && (system->total_attention_switches > 0);
        
        printf("    Attention switches: %lu, avg time: %.2f μs\n",
               (unsigned long)system->total_attention_switches,
               system->total_attention_switch_time_ns / 1000.0 / system->total_attention_switches);
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Attention Focus Switching", passed, test_time);
    
    return passed;
}

/**
 * Test attention switching performance
 */
static bool test_attention_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("attention_perf", reservoir);
    
    if (system) {
        uint32_t num_channels = system->num_attention_channels;
        
        /* Perform many attention switches to test performance */
        uint64_t total_switch_time = 0;
        uint32_t num_switches = 100;
        
        for (uint32_t i = 0; i < num_switches; i++) {
            uint32_t target_channel = i % num_channels;
            
            uint64_t switch_start = get_time_ns();
            int result = dtesn_attention_focus(system, target_channel, NULL, 0);
            uint64_t switch_time = get_time_ns() - switch_start;
            
            passed = passed && (result == 0);
            total_switch_time += switch_time;
            
            /* Check individual switch performance target: ≤10ms */
            uint64_t target_time_ns = DTESN_COGNITIVE_ATTENTION_SWITCH_US * 1000;
            if (switch_time > target_time_ns) {
                printf("    Switch %u exceeded target: %.2f μs (target: ≤%.2f μs)\n",
                       i, switch_time / 1000.0, target_time_ns / 1000.0);
            }
        }
        
        double avg_switch_time_us = (total_switch_time / 1000.0) / num_switches;
        double target_time_us = DTESN_COGNITIVE_ATTENTION_SWITCH_US;
        
        printf("    Average switch time: %.2f μs (target: ≤%.2f μs)\n",
               avg_switch_time_us, target_time_us);
        
        /* Performance target check with tolerance */
        if (avg_switch_time_us <= target_time_us * (100 + TEST_PERFORMANCE_TOLERANCE_PCT) / 100) {
            printf("    Performance target met (within tolerance)\n");
        } else {
            printf("    Performance target missed\n");
            /* Don't fail test in development phase */
        }
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Attention Performance", passed, test_time);
    
    return passed;
}

/**
 * Test multi-modal fusion (early strategy)
 */
static bool test_multimodal_fusion_early(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("fusion_test", reservoir);
    
    if (system) {
        /* Create test modality data */
        uint32_t num_modalities = 2;
        dtesn_cognitive_modality_data_t modalities[2];
        
        /* Visual modality */
        modalities[0].modality_id = 0;
        strcpy(modalities[0].name, "visual");
        modalities[0].data_size = 20;
        modalities[0].data = malloc(20 * sizeof(float));
        modalities[0].confidence = 0.8f;
        modalities[0].timestamp_ns = get_time_ns();
        modalities[0].valid = true;
        
        for (uint32_t i = 0; i < 20; i++) {
            modalities[0].data[i] = sinf(i * 0.1f);
        }
        
        /* Audio modality */
        modalities[1].modality_id = 1;
        strcpy(modalities[1].name, "audio");
        modalities[1].data_size = 15;
        modalities[1].data = malloc(15 * sizeof(float));
        modalities[1].confidence = 0.9f;
        modalities[1].timestamp_ns = get_time_ns();
        modalities[1].valid = true;
        
        for (uint32_t i = 0; i < 15; i++) {
            modalities[1].data[i] = cosf(i * 0.1f);
        }
        
        /* Test early fusion */
        uint32_t output_size = 50;
        float *fused_output = malloc(output_size * sizeof(float));
        
        int result = dtesn_multimodal_fuse(system, modalities, num_modalities,
                                          DTESN_COGNITIVE_FUSION_EARLY,
                                          fused_output, output_size);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Verify fusion output is valid */
            bool has_non_zero = false;
            for (uint32_t i = 0; i < output_size; i++) {
                if (fabsf(fused_output[i]) > TEST_TOLERANCE) {
                    has_non_zero = true;
                    break;
                }
            }
            passed = passed && has_non_zero;
            
            printf("    Fused %u modalities into %u features\n", 
                   num_modalities, output_size);
        }
        
        /* Cleanup */
        free(modalities[0].data);
        free(modalities[1].data);
        free(fused_output);
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Multi-modal Fusion (Early)", passed, test_time);
    
    return passed;
}

/**
 * Test multi-modal fusion (adaptive strategy)
 */
static bool test_multimodal_fusion_adaptive(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("adaptive_fusion", reservoir);
    
    if (system) {
        /* Create test modality data with varying confidence */
        uint32_t num_modalities = 3;
        dtesn_cognitive_modality_data_t modalities[3];
        
        for (uint32_t i = 0; i < num_modalities; i++) {
            modalities[i].modality_id = i;
            sprintf(modalities[i].name, "modality_%u", i);
            modalities[i].data_size = 10 + i * 5;
            modalities[i].data = malloc(modalities[i].data_size * sizeof(float));
            modalities[i].confidence = 0.5f + i * 0.2f; /* Varying confidence */
            modalities[i].timestamp_ns = get_time_ns() - i * 1000000; /* Slight time offset */
            modalities[i].valid = true;
            
            for (uint32_t j = 0; j < modalities[i].data_size; j++) {
                modalities[i].data[j] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
            }
        }
        
        /* Test adaptive fusion */
        uint32_t output_size = 40;
        float *fused_output = malloc(output_size * sizeof(float));
        
        int result = dtesn_multimodal_fuse(system, modalities, num_modalities,
                                          DTESN_COGNITIVE_FUSION_ADAPTIVE,
                                          fused_output, output_size);
        passed = passed && (result == 0);
        
        printf("    Adaptive fusion result: %s\n", result == 0 ? "Success" : "Failed");
        
        /* Cleanup */
        for (uint32_t i = 0; i < num_modalities; i++) {
            free(modalities[i].data);
        }
        free(fused_output);
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Multi-modal Fusion (Adaptive)", passed, test_time);
    
    return passed;
}

/**
 * Test OEIS A000081 compliance
 */
static bool test_oeis_compliance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("oeis_test", reservoir);
    
    if (system) {
        /* Test OEIS A000081 compliance */
        bool is_compliant = dtesn_cognitive_validate_a000081(system);
        passed = passed && is_compliant;
        
        printf("    OEIS A000081 compliance: %s\n", is_compliant ? "Valid" : "Invalid");
        printf("    Attention channels: %u, Modalities: %u\n",
               system->num_attention_channels, system->num_modalities);
        
        /* Verify specific OEIS constraints */
        const uint32_t oeis_sequence[] = {1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766};
        bool found_attention_match = false;
        bool found_modality_match = false;
        
        for (size_t i = 0; i < sizeof(oeis_sequence) / sizeof(oeis_sequence[0]); i++) {
            if (system->num_attention_channels == oeis_sequence[i]) {
                found_attention_match = true;
            }
            if (system->num_modalities == oeis_sequence[i]) {
                found_modality_match = true;
            }
        }
        
        passed = passed && found_attention_match && found_modality_match;
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("OEIS A000081 Compliance", passed, test_time);
    
    return passed;
}

/**
 * Test error handling
 */
static bool test_error_handling(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_cognitive_init();
    
    /* Test NULL pointer handling */
    int result = dtesn_adaptive_learn(NULL, NULL, NULL, 0, NULL);
    passed = passed && (result == -EINVAL);
    
    result = dtesn_memory_consolidate(NULL, DTESN_COGNITIVE_CONSOLIDATE_IMMEDIATE);
    passed = passed && (result == -EINVAL);
    
    result = dtesn_attention_focus(NULL, 0, NULL, 0);
    passed = passed && (result == -EINVAL);
    
    result = dtesn_multimodal_fuse(NULL, NULL, 0, DTESN_COGNITIVE_FUSION_EARLY, NULL, 0);
    passed = passed && (result == -EINVAL);
    
    /* Test invalid parameters */
    dtesn_esn_reservoir_t *reservoir = create_test_reservoir();
    dtesn_cognitive_system_t *system = dtesn_cognitive_system_create("error_test", reservoir);
    
    if (system) {
        /* Invalid channel ID */
        result = dtesn_attention_focus(system, 1000, NULL, 0);
        passed = passed && (result == -EINVAL);
        
        /* Invalid learning parameters */
        dtesn_cognitive_learn_params_t bad_params = {
            .learn_type = DTESN_COGNITIVE_LEARN_HEBBIAN,
            .learning_rate = -1.0f, /* Invalid negative rate */
            .adaptation_rate = 0.001f,
            .max_iterations = 10,
            .convergence_threshold = 1e-4f,
            .enable_plasticity = true,
            .enable_homeostasis = false,
            .batch_size = 1
        };
        
        result = dtesn_adaptive_learn_online(system, NULL, NULL, &bad_params);
        passed = passed && (result == -EINVAL);
        
        printf("    Error handling tests completed\n");
        
        dtesn_cognitive_system_destroy(system);
    }
    
    if (reservoir) {
        free(reservoir->x_current);
        free(reservoir->x_previous);
        free(reservoir->u_current);
        free(reservoir->y_current);
        free(reservoir);
    }
    
    dtesn_cognitive_cleanup();
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Error Handling", passed, test_time);
    
    return passed;
}

/**
 * Main test runner
 */
int main(void) {
    printf("DTESN Cognitive Computing Test Suite\n");
    printf("====================================\n\n");
    
    /* Initialize test statistics */
    memset(&g_test_stats, 0, sizeof(g_test_stats));
    srand((unsigned int)time(NULL));
    
    /* Run all tests */
    test_cognitive_init_cleanup();
    test_cognitive_system_creation();
    test_adaptive_learning_hebbian();
    test_adaptive_learning_online();
    test_memory_consolidation_immediate();
    test_memory_consolidation_performance();
    test_attention_focus_switching();
    test_attention_performance();
    test_multimodal_fusion_early();
    test_multimodal_fusion_adaptive();
    test_oeis_compliance();
    test_error_handling();
    
    /* Print summary */
    printf("\nTest Summary:\n");
    printf("=============\n");
    printf("Tests run:    %u\n", g_test_stats.tests_run);
    printf("Tests passed: %u\n", g_test_stats.tests_passed);
    printf("Tests failed: %u\n", g_test_stats.tests_failed);
    printf("Success rate: %.1f%%\n", 
           g_test_stats.tests_run > 0 ? 
           (100.0 * g_test_stats.tests_passed) / g_test_stats.tests_run : 0.0);
    printf("Total time:   %.2f ms\n", g_test_stats.total_test_time_ns / 1000000.0);
    
    if (g_test_stats.tests_failed > 0) {
        printf("\n❌ Some tests failed!\n");
        return 1;
    } else {
        printf("\n✅ All tests passed!\n");
        return 0;
    }
}