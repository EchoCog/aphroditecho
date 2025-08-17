/*
 * DTESN Integration Testing Framework
 * ==================================
 * 
 * Comprehensive integration testing framework for Deep Tree Echo State Networks (DTESN)
 * kernel components, providing cross-component validation, OEIS A000081 compliance
 * testing, and performance regression analysis.
 * 
 * This framework validates integration between all 8 DTESN kernel components:
 * 1. Memory Management     5. Scheduler
 * 2. P-System Membranes    6. System Calls  
 * 3. B-Series Computation  7. Hardware Abstraction
 * 4. ESN Reservoir         8. Profiler
 */

#ifndef DTESN_INTEGRATION_TEST_H
#define DTESN_INTEGRATION_TEST_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Test framework configuration */
#define DTESN_INTEGRATION_MAX_COMPONENTS    8       /* 8 kernel components */
#define DTESN_INTEGRATION_MAX_TESTS         256     /* Maximum test cases */
#define DTESN_INTEGRATION_MAX_METRICS       64      /* Performance metrics */
#define DTESN_INTEGRATION_TIMEOUT_MS        5000    /* 5 second test timeout */

/* Performance targets from specification */
#define DTESN_PERF_MEMBRANE_EVOLUTION_US    10      /* ≤ 10μs membrane evolution */
#define DTESN_PERF_BSERIES_COMPUTATION_US   100     /* ≤ 100μs B-series computation */
#define DTESN_PERF_ESN_STATE_UPDATE_US      1000    /* ≤ 1ms ESN state update */
#define DTESN_PERF_CONTEXT_SWITCH_US        5       /* ≤ 5μs context switch */
#define DTESN_PERF_SCHEDULING_LATENCY_US    10      /* ≤ 10μs scheduling latency */

/* Test coverage requirements */
#define DTESN_COVERAGE_TARGET_PCT           95      /* ≥ 95% code coverage */
#define DTESN_INTEGRATION_POINTS            8       /* All component integrations */

/* OEIS A000081 compliance constants */
#define DTESN_OEIS_MAX_DEPTH                12      /* Maximum tree depth to test */
extern const int dtesn_oeis_a000081_sequence[DTESN_OEIS_MAX_DEPTH];

/**
 * Component identifiers for integration testing
 */
typedef enum {
    DTESN_COMPONENT_MEMORY = 0,
    DTESN_COMPONENT_PSYSTEM,
    DTESN_COMPONENT_BSERIES,
    DTESN_COMPONENT_ESN,
    DTESN_COMPONENT_SCHEDULER,
    DTESN_COMPONENT_SYSCALLS,
    DTESN_COMPONENT_HAL,
    DTESN_COMPONENT_PROFILER,
    DTESN_COMPONENT_COUNT
} dtesn_component_id_t;

/**
 * Test result status codes
 */
typedef enum {
    DTESN_TEST_PASS = 0,
    DTESN_TEST_FAIL,
    DTESN_TEST_TIMEOUT,
    DTESN_TEST_SKIP,
    DTESN_TEST_ERROR
} dtesn_test_result_t;

/**
 * Performance metric types
 */
typedef enum {
    DTESN_METRIC_LATENCY = 0,
    DTESN_METRIC_THROUGHPUT,
    DTESN_METRIC_JITTER,
    DTESN_METRIC_CPU_USAGE,
    DTESN_METRIC_MEMORY_USAGE,
    DTESN_METRIC_COUNT
} dtesn_metric_type_t;

/**
 * Integration test context
 */
typedef struct {
    uint32_t test_id;
    const char *test_name;
    dtesn_component_id_t primary_component;
    dtesn_component_id_t secondary_component;
    uint64_t start_time_ns;
    uint64_t end_time_ns;
    dtesn_test_result_t result;
    char error_message[256];
} dtesn_test_context_t;

/**
 * Performance measurement structure
 */
typedef struct {
    dtesn_metric_type_t type;
    uint64_t value_ns;          /* Value in nanoseconds */
    uint64_t threshold_ns;      /* Performance threshold */
    bool meets_requirement;     /* Whether requirement is met */
    const char *description;
} dtesn_performance_metric_t;

/**
 * Integration test suite state
 */
typedef struct {
    uint32_t total_tests;
    uint32_t tests_passed;
    uint32_t tests_failed;
    uint32_t tests_skipped;
    uint64_t total_runtime_ns;
    dtesn_performance_metric_t metrics[DTESN_INTEGRATION_MAX_METRICS];
    uint32_t metric_count;
    bool oeis_compliance_validated;
    double code_coverage_pct;
} dtesn_integration_state_t;

/**
 * Test report structure
 */
typedef struct {
    dtesn_integration_state_t state;
    uint64_t timestamp_ns;
    char version[32];
    char build_info[256];
    bool regression_detected;
    char report_filename[256];
} dtesn_integration_report_t;

/* Core Integration Test Functions */

/**
 * dtesn_integration_test_init - Initialize integration testing framework
 * @config: Optional configuration parameters (NULL for defaults)
 * 
 * Initializes the DTESN integration testing framework, sets up component
 * interfaces, and prepares performance monitoring infrastructure.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_integration_test_init(const void *config);

/**
 * dtesn_integration_test_cleanup - Clean up integration testing framework
 * 
 * Releases resources, finalizes reports, and shuts down the integration
 * testing framework.
 */
void dtesn_integration_test_cleanup(void);

/**
 * dtesn_test_cross_component - Test cross-component communication
 * @comp1: Primary component to test
 * @comp2: Secondary component to test
 * @test_data: Test-specific data payload
 * @test_size: Size of test data
 * 
 * Validates communication and data exchange between two DTESN components,
 * ensuring proper interface compliance and data integrity.
 * 
 * Returns: DTESN_TEST_PASS on success, error code on failure
 */
dtesn_test_result_t dtesn_test_cross_component(
    dtesn_component_id_t comp1,
    dtesn_component_id_t comp2,
    const void *test_data,
    size_t test_size);

/**
 * dtesn_test_performance_regression - Run performance regression tests
 * @baseline_file: Path to baseline performance data (NULL for new baseline)
 * @regression_threshold_pct: Acceptable performance degradation percentage
 * 
 * Executes comprehensive performance tests across all components and
 * compares results against historical baselines to detect regressions.
 * 
 * Returns: 0 if no regressions detected, positive count of regressions found
 */
int dtesn_test_performance_regression(const char *baseline_file, double regression_threshold_pct);

/**
 * dtesn_validate_oeis_compliance - Validate OEIS A000081 compliance
 * @max_depth: Maximum tree depth to validate
 * 
 * Validates that all membrane hierarchies and tree structures across
 * integrated components comply with OEIS A000081 enumeration.
 * 
 * Returns: true if all components are OEIS compliant, false otherwise
 */
bool dtesn_validate_oeis_compliance(int max_depth);

/**
 * dtesn_test_report_generate - Generate comprehensive test report
 * @report: Output report structure
 * @output_file: Optional file path for report output
 * 
 * Generates detailed integration test report with performance metrics,
 * coverage analysis, and compliance validation results.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_test_report_generate(dtesn_integration_report_t *report, const char *output_file);

/* Component-Specific Integration Tests */

/**
 * dtesn_test_memory_integration - Test memory subsystem integration
 * 
 * Validates memory management integration with all other components,
 * including allocation/deallocation patterns and memory layout compliance.
 */
dtesn_test_result_t dtesn_test_memory_integration(void);

/**
 * dtesn_test_psystem_integration - Test P-System membrane integration
 * 
 * Validates P-System membrane integration with ESN reservoirs, B-Series
 * computation, and scheduler components.
 */
dtesn_test_result_t dtesn_test_psystem_integration(void);

/**
 * dtesn_test_esn_integration - Test ESN reservoir integration
 * 
 * Validates ESN reservoir integration with membrane systems, B-Series
 * computation, and hardware abstraction layer.
 */
dtesn_test_result_t dtesn_test_esn_integration(void);

/**
 * dtesn_test_scheduler_integration - Test scheduler integration
 * 
 * Validates real-time scheduler integration with all components,
 * including task priorities, deadlines, and load balancing.
 */
dtesn_test_result_t dtesn_test_scheduler_integration(void);

/* Performance and Stress Testing */

/**
 * dtesn_test_realistic_workload - Test under realistic workload scenarios
 * @workload_type: Type of workload to simulate
 * @duration_ms: Duration of test in milliseconds
 * 
 * Executes integration tests under realistic workload conditions to
 * validate system behavior under operational stress.
 */
dtesn_test_result_t dtesn_test_realistic_workload(int workload_type, uint32_t duration_ms);

/**
 * dtesn_test_stress_integration - Stress test integrated system
 * @max_load_pct: Maximum load percentage to apply
 * @duration_ms: Duration of stress test
 * 
 * Applies high load conditions to test system stability and performance
 * degradation patterns under stress.
 */
dtesn_test_result_t dtesn_test_stress_integration(int max_load_pct, uint32_t duration_ms);

/* Utility Functions */

/**
 * dtesn_get_component_name - Get human-readable component name
 * @component: Component identifier
 * 
 * Returns: String name of component, or "Unknown" for invalid IDs
 */
const char *dtesn_get_component_name(dtesn_component_id_t component);

/**
 * dtesn_measure_performance - Measure component performance
 * @component: Component to measure
 * @metric_type: Type of metric to measure
 * @duration_ms: Measurement duration
 * 
 * Returns: Performance measurement result
 */
dtesn_performance_metric_t dtesn_measure_performance(
    dtesn_component_id_t component,
    dtesn_metric_type_t metric_type,
    uint32_t duration_ms);

/**
 * dtesn_get_integration_state - Get current integration test state
 * 
 * Returns: Pointer to current integration test state structure
 */
const dtesn_integration_state_t *dtesn_get_integration_state(void);

/**
 * dtesn_reset_integration_state - Reset integration test state
 * 
 * Resets all test counters and metrics for a fresh test run.
 */
void dtesn_reset_integration_state(void);

/* Timing Utilities */
static inline uint64_t dtesn_get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static inline double dtesn_ns_to_us(uint64_t ns) {
    return (double)ns / 1000.0;
}

static inline double dtesn_ns_to_ms(uint64_t ns) {
    return (double)ns / 1000000.0;
}

#ifdef __cplusplus
}
#endif

#endif /* DTESN_INTEGRATION_TEST_H */