/*
 * DTESN Neuromorphic Hardware Abstraction Layer Test Suite
 * ========================================================
 * 
 * Comprehensive test suite for neuromorphic HAL implementation including
 * device discovery, event processing, power management, and performance validation.
 */

#include "include/dtesn/neuro_hal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include <math.h>
#include <unistd.h>

/* Test configuration */
#define TEST_MAX_DEVICES         16
#define TEST_MAX_EVENTS          1000
#define TEST_PERFORMANCE_ITERATIONS 100
#define TEST_TOLERANCE           1e-6f

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
static bool test_neuro_hal_init(void);
static bool test_neuro_hal_version(void);
static bool test_neuro_device_driver_registration(void);
static bool test_neuro_device_discovery(void);
static bool test_neuro_device_open_close(void);
static bool test_neuro_event_processing(void);
static bool test_neuro_event_latency_performance(void);
static bool test_neuro_event_throughput_performance(void);
static bool test_neuro_power_management(void);
static bool test_neuro_power_efficiency(void);
static bool test_neuro_dma_operations(void);
static bool test_neuro_context_switch_performance(void);
static bool test_neuro_oeis_compliance(void);
static bool test_neuro_error_handling(void);
static bool test_neuro_concurrent_operations(void);
static bool test_neuro_device_statistics(void);

/* External driver registration functions */
extern int loihi_driver_register(void);
extern int loihi_driver_unregister(void);
extern int spinnaker_driver_register(void);
extern int spinnaker_driver_unregister(void);

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
    printf("%-50s: %s (%.3f ms)\n", 
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
 * Test neuromorphic HAL initialization
 */
static bool test_neuro_hal_init(void) {
    uint64_t start_time = get_time_ns();
    
    int result = neuro_hal_init();
    bool passed = (result == 0);
    
    if (passed) {
        /* Test double initialization should not fail */
        result = neuro_hal_init();
        passed = (result == 0);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Neuromorphic HAL Initialization", passed, test_time);
    
    return passed;
}

/**
 * Test HAL version information
 */
static bool test_neuro_hal_version(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    uint32_t major, minor, patch;
    neuro_hal_get_version(&major, &minor, &patch);
    
    /* Verify version numbers are reasonable */
    passed = passed && (major >= 1 && major <= 10);
    passed = passed && (minor >= 0 && minor <= 100);
    passed = passed && (patch >= 0 && patch <= 1000);
    
    printf("    HAL Version: %u.%u.%u\n", major, minor, patch);
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("HAL Version Information", passed, test_time);
    
    return passed;
}

/**
 * Test device driver registration
 */
static bool test_neuro_device_driver_registration(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Register Loihi driver */
    int result = loihi_driver_register();
    passed = passed && (result == 0);
    
    /* Register SpiNNaker driver */
    result = spinnaker_driver_register();
    passed = passed && (result == 0);
    
    /* Test duplicate registration should fail */
    result = loihi_driver_register();
    passed = passed && (result != 0);
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Device Driver Registration", passed, test_time);
    
    return passed;
}

/**
 * Test device discovery
 */
static bool test_neuro_device_discovery(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    dtesn_neuro_device_t devices[TEST_MAX_DEVICES];
    int num_devices = neuro_device_discover(devices, TEST_MAX_DEVICES);
    
    passed = passed && (num_devices >= 0);
    passed = passed && (num_devices <= TEST_MAX_DEVICES);
    
    printf("    Discovered devices: %d\n", num_devices);
    
    for (int i = 0; i < num_devices; i++) {
        printf("      Device %d: %s (%s)\n", 
               devices[i].device_id,
               devices[i].name,
               neuro_device_type_name(devices[i].type));
        
        /* Verify device properties */
        passed = passed && (devices[i].device_id < DTESN_NEURO_MAX_DEVICES);
        passed = passed && (devices[i].type != DTESN_NEURO_DEVICE_UNKNOWN);
        passed = passed && (devices[i].caps.max_neurons > 0);
        passed = passed && (devices[i].caps.max_cores > 0);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Device Discovery", passed, test_time);
    
    return passed;
}

/**
 * Test device open and close operations
 */
static bool test_neuro_device_open_close(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Get default configuration */
        dtesn_neuro_config_t config;
        int result = neuro_config_default(&config, device->type);
        passed = passed && (result == 0);
        
        /* Test device open */
        uint64_t open_start = get_time_ns();
        result = neuro_device_open(device, &config);
        uint64_t open_time = get_time_ns() - open_start;
        
        passed = passed && (result == 0);
        passed = passed && (device->state == DTESN_NEURO_STATE_ACTIVE);
        
        /* Check context switch time constraint (≤5μs) */
        passed = passed && (open_time <= DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US * 1000);
        
        printf("    Device open time: %.3f μs (target: ≤ %d μs)\n", 
               open_time / 1000.0, DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US);
        
        /* Test device close */
        result = neuro_device_close(device);
        passed = passed && (result == 0);
        passed = passed && (device->state == DTESN_NEURO_STATE_UNINITIALIZED);
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Device Open/Close Operations", passed, test_time);
    
    return passed;
}

/**
 * Test neuromorphic event processing
 */
static bool test_neuro_event_processing(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        config.num_neurons = 100;
        config.enable_monitoring = true;
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Test single event send */
            dtesn_neuro_event_t event = neuro_event_create(
                DTESN_NEURO_EVENT_SPIKE, 0, 1, 1.0f);
            
            result = neuro_event_send(device, &event);
            passed = passed && (result == 0);
            
            /* Test multiple event processing */
            dtesn_neuro_event_t events[10];
            for (int i = 0; i < 10; i++) {
                events[i] = neuro_event_create(
                    DTESN_NEURO_EVENT_SPIKE, i, (i + 1) % 10, 0.5f);
            }
            
            result = neuro_event_process(device, events, 10);
            passed = passed && (result == 10);
            
            /* Test event receive */
            dtesn_neuro_event_t received_event;
            result = neuro_event_receive(device, &received_event, 1000); /* 1ms timeout */
            /* Result can be 0 (no event) or 1 (event received) */
            passed = passed && (result >= 0);
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Neuromorphic Event Processing", passed, test_time);
    
    return passed;
}

/**
 * Test event processing latency performance
 */
static bool test_neuro_event_latency_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            uint64_t total_latency = 0;
            uint64_t max_latency = 0;
            
            /* Measure event processing latency */
            for (int i = 0; i < TEST_PERFORMANCE_ITERATIONS; i++) {
                dtesn_neuro_event_t event = neuro_event_create(
                    DTESN_NEURO_EVENT_SPIKE, i % 10, (i + 1) % 10, 1.0f);
                
                uint64_t event_start = get_time_ns();
                result = neuro_event_send(device, &event);
                uint64_t event_latency = get_time_ns() - event_start;
                
                passed = passed && (result == 0);
                total_latency += event_latency;
                
                if (event_latency > max_latency) {
                    max_latency = event_latency;
                }
            }
            
            uint64_t avg_latency = total_latency / TEST_PERFORMANCE_ITERATIONS;
            
            /* Check latency constraint (≤1μs) */
            passed = passed && (avg_latency <= DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US * 1000);
            passed = passed && (max_latency <= DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US * 1000 * 2);
            
            printf("    Average event latency: %.3f μs (target: ≤ %d μs)\n", 
                   avg_latency / 1000.0, DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US);
            printf("    Maximum event latency: %.3f μs\n", max_latency / 1000.0);
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Event Processing Latency Performance", passed, test_time);
    
    return passed;
}

/**
 * Test event processing throughput performance
 */
static bool test_neuro_event_throughput_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Create large batch of events */
            dtesn_neuro_event_t *events = malloc(TEST_MAX_EVENTS * sizeof(dtesn_neuro_event_t));
            passed = passed && (events != NULL);
            
            if (events) {
                for (int i = 0; i < TEST_MAX_EVENTS; i++) {
                    events[i] = neuro_event_create(
                        DTESN_NEURO_EVENT_SPIKE, i % 100, (i + 1) % 100, 1.0f);
                }
                
                /* Measure throughput */
                uint64_t throughput_start = get_time_ns();
                result = neuro_event_process(device, events, TEST_MAX_EVENTS);
                uint64_t throughput_time = get_time_ns() - throughput_start;
                
                passed = passed && (result == TEST_MAX_EVENTS);
                
                if (throughput_time > 0) {
                    uint32_t throughput_events_per_sec = 
                        (uint32_t)((uint64_t)TEST_MAX_EVENTS * 1000000000ULL / throughput_time);
                    
                    /* Check throughput constraint (≥1M events/sec) */
                    passed = passed && (throughput_events_per_sec >= DTESN_NEURO_THROUGHPUT_THRESHOLD_HZ);
                    
                    printf("    Event throughput: %u events/sec (target: ≥ %u events/sec)\n",
                           throughput_events_per_sec, DTESN_NEURO_THROUGHPUT_THRESHOLD_HZ);
                }
                
                free(events);
            }
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Event Processing Throughput Performance", passed, test_time);
    
    return passed;
}

/**
 * Test power management functionality
 */
static bool test_neuro_power_management(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Test power mode changes */
            dtesn_neuro_power_mode_t modes[] = {
                DTESN_NEURO_POWER_FULL,
                DTESN_NEURO_POWER_REDUCED,
                DTESN_NEURO_POWER_SLEEP,
                DTESN_NEURO_POWER_FULL
            };
            
            for (int i = 0; i < 4; i++) {
                result = neuro_power_manage(device, modes[i]);
                passed = passed && (result == 0);
                
                /* Get power statistics */
                float power_mw, efficiency_mw_gops;
                result = neuro_power_get_stats(device, &power_mw, &efficiency_mw_gops);
                passed = passed && (result == 0);
                passed = passed && (power_mw >= 0.0f);
                passed = passed && (efficiency_mw_gops >= 0.0f);
                
                printf("    Power mode %d: %.1f mW, %.3f mW/GOPS\n", 
                       modes[i], power_mw, efficiency_mw_gops);
            }
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Power Management Functionality", passed, test_time);
    
    return passed;
}

/**
 * Test power efficiency constraint
 */
static bool test_neuro_power_efficiency(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Get power statistics */
            float power_mw, efficiency_mw_gops;
            result = neuro_power_get_stats(device, &power_mw, &efficiency_mw_gops);
            passed = passed && (result == 0);
            
            /* Check power efficiency constraint (≤10mW/GOPS) */
            passed = passed && (efficiency_mw_gops <= DTESN_NEURO_POWER_EFFICIENCY_MW_GOPS);
            
            printf("    Power efficiency: %.3f mW/GOPS (target: ≤ %d mW/GOPS)\n",
                   efficiency_mw_gops, DTESN_NEURO_POWER_EFFICIENCY_MW_GOPS);
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Power Efficiency Constraint", passed, test_time);
    
    return passed;
}

/**
 * Test DMA operations
 */
static bool test_neuro_dma_operations(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device && device->caps.supports_dma) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Test DMA transfer */
            size_t buffer_size = 4096;
            void *src_buffer = malloc(buffer_size);
            void *dst_buffer = malloc(buffer_size);
            
            passed = passed && (src_buffer != NULL);
            passed = passed && (dst_buffer != NULL);
            
            if (src_buffer && dst_buffer) {
                /* Initialize source buffer */
                memset(src_buffer, 0xAA, buffer_size);
                memset(dst_buffer, 0x00, buffer_size);
                
                /* Create DMA descriptor */
                dtesn_neuro_dma_desc_t dma_desc = {
                    .src_addr = src_buffer,
                    .dst_addr = dst_buffer,
                    .size = buffer_size,
                    .mode = DTESN_NEURO_DMA_SYNCHRONOUS,
                    .flags = 0,
                    .callback = NULL,
                    .callback_context = NULL
                };
                
                /* Perform DMA transfer */
                result = neuro_dma_transfer(device, &dma_desc);
                passed = passed && (result == 0);
                
                /* Check transfer status */
                bool complete;
                size_t transferred;
                result = neuro_dma_status(device, &complete, &transferred);
                passed = passed && (result == 0);
                passed = passed && complete;
                passed = passed && (transferred >= buffer_size);
                
                printf("    DMA transfer: %zu bytes completed\n", transferred);
                
                free(src_buffer);
                free(dst_buffer);
            }
            
            neuro_device_close(device);
        }
    } else {
        printf("    No DMA-capable devices available for testing\n");
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("DMA Operations", passed, test_time);
    
    return passed;
}

/**
 * Test context switch performance
 */
static bool test_neuro_context_switch_performance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        uint64_t total_switch_time = 0;
        uint64_t max_switch_time = 0;
        
        /* Perform multiple open/close cycles */
        for (int i = 0; i < 10; i++) {
            uint64_t switch_start = get_time_ns();
            
            int result = neuro_device_open(device, &config);
            passed = passed && (result == 0);
            
            if (result == 0) {
                result = neuro_device_close(device);
                passed = passed && (result == 0);
            }
            
            uint64_t switch_time = get_time_ns() - switch_start;
            total_switch_time += switch_time;
            
            if (switch_time > max_switch_time) {
                max_switch_time = switch_time;
            }
        }
        
        uint64_t avg_switch_time = total_switch_time / 10;
        
        /* Check context switch constraint (≤5μs) */
        passed = passed && (avg_switch_time <= DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US * 1000);
        
        printf("    Average context switch time: %.3f μs (target: ≤ %d μs)\n",
               avg_switch_time / 1000.0, DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US);
        printf("    Maximum context switch time: %.3f μs\n", max_switch_time / 1000.0);
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Context Switch Performance", passed, test_time);
    
    return passed;
}

/**
 * Test OEIS A000081 compliance
 */
static bool test_neuro_oeis_compliance(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Discover devices */
    dtesn_neuro_device_t devices[TEST_MAX_DEVICES];
    int num_devices = neuro_device_discover(devices, TEST_MAX_DEVICES);
    
    passed = passed && (num_devices >= 0);
    
    if (num_devices > 0) {
        /* Test OEIS A000081 compliance */
        bool is_compliant = neuro_device_validate_a000081(devices, num_devices);
        passed = passed && is_compliant;
        
        printf("    Device enumeration OEIS A000081 compliance: %s\n", 
               is_compliant ? "Valid" : "Invalid");
        printf("    Number of devices: %d\n", num_devices);
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("OEIS A000081 Compliance", passed, test_time);
    
    return passed;
}

/**
 * Test error handling
 */
static bool test_neuro_error_handling(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Test NULL pointer handling */
    int result = neuro_event_send(NULL, NULL);
    passed = passed && (result == DTESN_NEURO_EINVAL);
    
    result = neuro_device_open(NULL, NULL);
    passed = passed && (result == DTESN_NEURO_EINVAL);
    
    result = neuro_power_manage(NULL, DTESN_NEURO_POWER_FULL);
    passed = passed && (result == DTESN_NEURO_EINVAL);
    
    /* Test invalid parameters */
    dtesn_neuro_config_t invalid_config = {0};
    invalid_config.num_neurons = 0; /* Invalid */
    
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (device) {
        result = neuro_device_open(device, &invalid_config);
        passed = passed && (result != 0); /* Should fail */
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Error Handling", passed, test_time);
    
    return passed;
}

/**
 * Test device statistics
 */
static bool test_neuro_device_statistics(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* Get a device for testing */
    dtesn_neuro_device_t *device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    if (!device) {
        device = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    }
    
    if (device) {
        /* Open device */
        dtesn_neuro_config_t config;
        neuro_config_default(&config, device->type);
        
        int result = neuro_device_open(device, &config);
        passed = passed && (result == 0);
        
        if (result == 0) {
            /* Send some events */
            for (int i = 0; i < 10; i++) {
                dtesn_neuro_event_t event = neuro_event_create(
                    DTESN_NEURO_EVENT_SPIKE, i % 5, (i + 1) % 5, 1.0f);
                neuro_event_send(device, &event);
            }
            
            /* Get statistics */
            dtesn_neuro_stats_t stats;
            result = neuro_device_get_stats(device, &stats);
            passed = passed && (result == 0);
            
            /* Verify statistics */
            passed = passed && (stats.total_events_processed >= 10);
            
            printf("    Events processed: %lu\n", stats.total_events_processed);
            printf("    Spikes generated: %lu\n", stats.total_spikes_generated);
            printf("    Average event latency: %lu ns\n", stats.avg_event_latency_ns);
            
            /* Check threshold compliance */
            bool thresholds_met = neuro_hal_check_thresholds(device);
            printf("    Performance thresholds met: %s\n", thresholds_met ? "Yes" : "No");
            
            /* Reset statistics */
            result = neuro_device_reset_stats(device);
            passed = passed && (result == 0);
            
            neuro_device_close(device);
        }
    } else {
        printf("    No devices available for testing\n");
        passed = false;
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Device Statistics", passed, test_time);
    
    return passed;
}

/**
 * Test concurrent operations (basic threading test)
 */
static bool test_neuro_concurrent_operations(void) {
    uint64_t start_time = get_time_ns();
    bool passed = true;
    
    /* This is a simplified concurrent test */
    /* In a real implementation, this would test multiple threads */
    
    /* Get multiple devices */
    dtesn_neuro_device_t *device1 = neuro_device_get_by_type(DTESN_NEURO_DEVICE_LOIHI);
    dtesn_neuro_device_t *device2 = neuro_device_get_by_type(DTESN_NEURO_DEVICE_SPINNAKER);
    
    if (device1 && device2) {
        /* Open both devices */
        dtesn_neuro_config_t config1, config2;
        neuro_config_default(&config1, device1->type);
        neuro_config_default(&config2, device2->type);
        
        int result1 = neuro_device_open(device1, &config1);
        int result2 = neuro_device_open(device2, &config2);
        
        passed = passed && (result1 == 0);
        passed = passed && (result2 == 0);
        
        if (result1 == 0 && result2 == 0) {
            /* Send events to both devices concurrently */
            for (int i = 0; i < 5; i++) {
                dtesn_neuro_event_t event1 = neuro_event_create(
                    DTESN_NEURO_EVENT_SPIKE, i, (i + 1) % 5, 1.0f);
                dtesn_neuro_event_t event2 = neuro_event_create(
                    DTESN_NEURO_EVENT_SPIKE, i, (i + 1) % 5, 1.0f);
                
                result1 = neuro_event_send(device1, &event1);
                result2 = neuro_event_send(device2, &event2);
                
                passed = passed && (result1 == 0);
                passed = passed && (result2 == 0);
            }
            
            printf("    Concurrent operations on multiple devices completed\n");
            
            neuro_device_close(device1);
            neuro_device_close(device2);
        }
    } else {
        printf("    Insufficient devices for concurrent testing\n");
    }
    
    uint64_t test_time = get_time_ns() - start_time;
    print_test_result("Concurrent Operations", passed, test_time);
    
    return passed;
}

/**
 * Main test runner
 */
int main(void) {
    printf("DTESN Neuromorphic Hardware Abstraction Layer Test Suite\n");
    printf("========================================================\n\n");
    
    srand((unsigned int)time(NULL));
    
    /* Run all tests */
    test_neuro_hal_init();
    test_neuro_hal_version();
    test_neuro_device_driver_registration();
    test_neuro_device_discovery();
    test_neuro_device_open_close();
    test_neuro_event_processing();
    test_neuro_event_latency_performance();
    test_neuro_event_throughput_performance();
    test_neuro_power_management();
    test_neuro_power_efficiency();
    test_neuro_dma_operations();
    test_neuro_context_switch_performance();
    test_neuro_oeis_compliance();
    test_neuro_device_statistics();
    test_neuro_concurrent_operations();
    test_neuro_error_handling();
    
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
    neuro_hal_shutdown();
    
    return (g_test_stats.tests_failed == 0) ? 0 : 1;
}