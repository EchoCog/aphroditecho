/*
 * DTESN Real-Time Scheduler Test Suite
 * ===================================
 * 
 * Comprehensive test suite for DTESN real-time scheduler implementation
 * validating performance requirements, scheduling policies, and OEIS compliance.
 */

#include <dtesn/scheduler.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <sys/time.h>

/* Test configuration */
#define TEST_MAX_CPUS           4
#define TEST_MAX_TASKS          100
#define TEST_STRESS_DURATION    5   /* seconds */
#define TEST_TOLERANCE_PERCENT  10  /* 10% tolerance for timing tests */

/* Test result tracking */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

/* Forward declarations */
static void test_scheduler_init(void);
static void test_task_creation(void);
static void test_task_scheduling(void);
static void test_deadline_checking(void);
static void test_load_balancing(void);
static void test_priority_inheritance(void);
static void test_scheduling_policies(void);
static void test_performance_requirements(void);
static void test_oeis_compliance(void);
static void test_stress_testing(void);
static void test_integration(void);

static uint64_t get_time_ns(void);
static void print_test_result(const char *test_name, int result);
static void print_test_summary(void);

/**
 * get_time_ns - Get current time in nanoseconds
 */
static uint64_t get_time_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/**
 * print_test_result - Print test result
 */
static void print_test_result(const char *test_name, int result)
{
    tests_run++;
    if (result) {
        tests_passed++;
        printf("✅ %s\n", test_name);
    } else {
        tests_failed++;
        printf("❌ %s\n", test_name);
    }
}

/**
 * print_test_summary - Print test summary
 */
static void print_test_summary(void)
{
    printf("\nTest Summary:\n");
    printf("=============\n");
    printf("Total tests: %d\n", tests_run);
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Success rate: %.1f%%\n", (float)tests_passed / tests_run * 100.0);
    
    if (tests_failed == 0) {
        printf("🎉 All tests passed!\n");
    } else {
        printf("⚠️  %d test(s) failed\n", tests_failed);
    }
}

/**
 * test_scheduler_init - Test scheduler initialization
 */
static void test_scheduler_init(void)
{
    printf("\n=== Scheduler Initialization Tests ===\n");
    
    /* Test valid initialization */
    int result = dtesn_sched_init(TEST_MAX_CPUS);
    print_test_result("Scheduler initialization with valid CPU count", result == 0);
    
    /* Test invalid CPU count */
    result = dtesn_sched_init(0);
    print_test_result("Scheduler initialization with zero CPUs (should fail)", result != 0);
    
    result = dtesn_sched_init(DTESN_SCHED_MAX_CPUS + 1);
    print_test_result("Scheduler initialization with too many CPUs (should fail)", result != 0);
    
    /* Test double initialization */
    result = dtesn_sched_init(TEST_MAX_CPUS);
    print_test_result("Double initialization (should fail)", result != 0);
    
    /* Get performance metrics */
    dtesn_sched_perf_t *perf = dtesn_sched_get_performance(-1);
    print_test_result("Get global performance metrics", perf != NULL);
    
    perf = dtesn_sched_get_performance(0);
    print_test_result("Get per-CPU performance metrics", perf != NULL);
    
    perf = dtesn_sched_get_performance(TEST_MAX_CPUS);
    print_test_result("Get invalid CPU performance metrics (should fail)", perf == NULL);
}

/**
 * test_task_creation - Test task creation and destruction
 */
static void test_task_creation(void)
{
    printf("\n=== Task Creation Tests ===\n");
    
    /* Test valid task creation */
    dtesn_task_t *task = dtesn_task_create(1234, DTESN_WORKLOAD_MEMBRANE, 
                                           DTESN_SCHED_POLICY_REALTIME, 10);
    print_test_result("Create membrane computing task", task != NULL);
    
    if (task) {
        print_test_result("Task has correct PID", task->pid == 1234);
        print_test_result("Task has correct workload type", 
                         task->workload_type == DTESN_WORKLOAD_MEMBRANE);
        print_test_result("Task has correct policy", 
                         task->policy == DTESN_SCHED_POLICY_REALTIME);
        print_test_result("Task has correct priority", task->priority == 10);
        print_test_result("Task is OEIS compliant", task->oeis_compliant);
        
        /* Test task destruction */
        int result = dtesn_task_destroy(task);
        print_test_result("Destroy task", result == 0);
    }
    
    /* Test ESN task creation */
    task = dtesn_task_create(5678, DTESN_WORKLOAD_ESN, 
                            DTESN_SCHED_POLICY_EDF, 20);
    print_test_result("Create ESN task", task != NULL);
    
    if (task) {
        print_test_result("ESN task requires FPU", task->requires_fpu);
        print_test_result("ESN task requires vector", task->requires_vector);
        dtesn_task_destroy(task);
    }
    
    /* Test B-Series task creation */
    task = dtesn_task_create(9012, DTESN_WORKLOAD_BSERIES, 
                            DTESN_SCHED_POLICY_RM, 30);
    print_test_result("Create B-Series task", task != NULL);
    
    if (task) {
        print_test_result("B-Series task has correct order", task->bseries_order == 4);
        dtesn_task_destroy(task);
    }
    
    /* Test invalid task creation */
    task = dtesn_task_create(1111, DTESN_WORKLOAD_GENERAL, 
                            DTESN_SCHED_POLICY_CFS, DTESN_SCHED_MAX_PRIORITIES);
    print_test_result("Create task with invalid priority (should fail)", task == NULL);
}

/**
 * test_task_scheduling - Test basic task scheduling
 */
static void test_task_scheduling(void)
{
    printf("\n=== Task Scheduling Tests ===\n");
    
    /* Create test tasks */
    dtesn_task_t *task1 = dtesn_task_create(1001, DTESN_WORKLOAD_MEMBRANE,
                                           DTESN_SCHED_POLICY_REALTIME, 10);
    dtesn_task_t *task2 = dtesn_task_create(1002, DTESN_WORKLOAD_ESN,
                                           DTESN_SCHED_POLICY_REALTIME, 20);
    dtesn_task_t *task3 = dtesn_task_create(1003, DTESN_WORKLOAD_GENERAL,
                                           DTESN_SCHED_POLICY_CFS, 50);
    
    print_test_result("Create test tasks for scheduling", 
                     task1 != NULL && task2 != NULL && task3 != NULL);
    
    if (task1 && task2 && task3) {
        /* Add tasks to run queue */
        dtesn_sched_add_task(task1, 0);
        dtesn_sched_add_task(task2, 0);
        dtesn_sched_add_task(task3, 0);
        
        /* Schedule tasks on CPU 0 */
        dtesn_task_t *scheduled = dtesn_task_schedule(0);
        print_test_result("Schedule task on CPU 0", scheduled != NULL);
        
        if (scheduled) {
            print_test_result("Membrane task scheduled first (highest priority)",
                             scheduled->workload_type == DTESN_WORKLOAD_MEMBRANE);
        }
        
        /* Test scheduling on invalid CPU */
        scheduled = dtesn_task_schedule(TEST_MAX_CPUS);
        print_test_result("Schedule on invalid CPU (should fail)", scheduled == NULL);
        
        /* Cleanup */
        dtesn_task_destroy(task1);
        dtesn_task_destroy(task2);
        dtesn_task_destroy(task3);
    }
}

/**
 * test_deadline_checking - Test deadline enforcement
 */
static void test_deadline_checking(void)
{
    printf("\n=== Deadline Checking Tests ===\n");
    
    uint64_t current_time = get_time_ns();
    
    /* Create EDF task with future deadline */
    dtesn_task_t *task = dtesn_task_create(2001, DTESN_WORKLOAD_ESN,
                                          DTESN_SCHED_POLICY_EDF, 10);
    
    if (task) {
        /* Set deadline in the future */
        task->deadline_ns = current_time + 10000000; /* 10ms from now */
        
        bool deadline_met = dtesn_deadline_check(task, current_time);
        print_test_result("Deadline check for future deadline", deadline_met);
        
        /* Set deadline in the past */
        task->deadline_ns = current_time - 1000000; /* 1ms ago */
        
        deadline_met = dtesn_deadline_check(task, current_time);
        print_test_result("Deadline check for past deadline (should fail)", !deadline_met);
        
        /* Test Rate Monotonic budget checking */
        task->policy = DTESN_SCHED_POLICY_RM;
        task->budget_ns = 5000000; /* 5ms budget */
        task->runtime_ns = 6000000; /* 6ms runtime - over budget */
        
        deadline_met = dtesn_deadline_check(task, current_time);
        print_test_result("Budget check for over-budget task (should fail)", !deadline_met);
        
        dtesn_task_destroy(task);
    }
    
    /* Test deadline checking for non-RT task */
    task = dtesn_task_create(2002, DTESN_WORKLOAD_GENERAL,
                            DTESN_SCHED_POLICY_CFS, 50);
    
    if (task) {
        bool deadline_met = dtesn_deadline_check(task, current_time);
        print_test_result("Deadline check for non-RT task (should pass)", deadline_met);
        
        dtesn_task_destroy(task);
    }
}

/**
 * test_load_balancing - Test load balancing functionality
 */
static void test_load_balancing(void)
{
    printf("\n=== Load Balancing Tests ===\n");
    
    /* Create multiple tasks to trigger load balancing */
    dtesn_task_t *tasks[10];
    int num_tasks = 0;
    
    for (int i = 0; i < 10; i++) {
        tasks[i] = dtesn_task_create(3000 + i, DTESN_WORKLOAD_GENERAL,
                                    DTESN_SCHED_POLICY_CFS, 50);
        if (tasks[i]) {
            num_tasks++;
        }
    }
    
    print_test_result("Create multiple tasks for load balancing", num_tasks == 10);
    
    /* Trigger load balancing */
    int migrated = dtesn_load_balance(0);
    print_test_result("Load balancing execution", migrated >= 0);
    
    /* Test load balancing on invalid CPU */
    migrated = dtesn_load_balance(TEST_MAX_CPUS);
    print_test_result("Load balancing on invalid CPU (should fail)", migrated < 0);
    
    /* Cleanup */
    for (int i = 0; i < num_tasks; i++) {
        if (tasks[i]) {
            dtesn_task_destroy(tasks[i]);
        }
    }
}

/**
 * test_priority_inheritance - Test priority inheritance protocol
 */
static void test_priority_inheritance(void)
{
    printf("\n=== Priority Inheritance Tests ===\n");
    
    /* Create high and low priority tasks */
    dtesn_task_t *high_prio = dtesn_task_create(4001, DTESN_WORKLOAD_MEMBRANE,
                                               DTESN_SCHED_POLICY_REALTIME, 5);
    dtesn_task_t *low_prio = dtesn_task_create(4002, DTESN_WORKLOAD_GENERAL,
                                              DTESN_SCHED_POLICY_CFS, 50);
    
    if (high_prio && low_prio) {
        print_test_result("Create tasks for priority inheritance test", 1);
        
        uint32_t original_priority = low_prio->effective_priority;
        
        /* Simulate priority inheritance */
        int result = dtesn_priority_inherit(high_prio, low_prio);
        print_test_result("Priority inheritance execution", result == 0);
        
        if (result == 0) {
            print_test_result("Low priority task inherits high priority",
                             low_prio->effective_priority == high_prio->effective_priority);
            print_test_result("Original priority preserved",
                             low_prio->original_priority == original_priority);
            print_test_result("PI state updated",
                             low_prio->pi_state == DTESN_PI_STATE_INHERITED);
        }
        
        dtesn_task_destroy(high_prio);
        dtesn_task_destroy(low_prio);
    }
    
    /* Test invalid priority inheritance */
    int result = dtesn_priority_inherit(NULL, NULL);
    print_test_result("Priority inheritance with NULL tasks (should fail)", result != 0);
}

/**
 * test_scheduling_policies - Test different scheduling policies
 */
static void test_scheduling_policies(void)
{
    printf("\n=== Scheduling Policy Tests ===\n");
    
    uint64_t current_time = get_time_ns();
    
    /* Test EDF policy */
    dtesn_task_t *edf_task = dtesn_task_create(5001, DTESN_WORKLOAD_ESN,
                                              DTESN_SCHED_POLICY_EDF, 20);
    if (edf_task) {
        edf_task->deadline_ns = current_time + 5000000; /* 5ms deadline */
        
        int result = dtesn_sched_set_policy(edf_task, DTESN_SCHED_POLICY_EDF, 20);
        print_test_result("Set EDF policy", result == 0);
        
        dtesn_task_destroy(edf_task);
    }
    
    /* Test Rate Monotonic policy */
    dtesn_task_t *rm_task = dtesn_task_create(5002, DTESN_WORKLOAD_BSERIES,
                                             DTESN_SCHED_POLICY_RM, 15);
    if (rm_task) {
        rm_task->period_ns = 10000000;  /* 10ms period */
        rm_task->budget_ns = 5000000;   /* 5ms budget */
        
        int result = dtesn_sched_set_policy(rm_task, DTESN_SCHED_POLICY_RM, 15);
        print_test_result("Set Rate Monotonic policy", result == 0);
        
        dtesn_task_destroy(rm_task);
    }
    
    /* Test CFS policy */
    dtesn_task_t *cfs_task = dtesn_task_create(5003, DTESN_WORKLOAD_GENERAL,
                                              DTESN_SCHED_POLICY_CFS, 30);
    if (cfs_task) {
        cfs_task->nice = -5; /* Higher priority */
        
        int result = dtesn_sched_set_policy(cfs_task, DTESN_SCHED_POLICY_CFS, 30);
        print_test_result("Set CFS policy", result == 0);
        
        dtesn_task_destroy(cfs_task);
    }
    
    /* Test DTESN real-time policy */
    dtesn_task_t *rt_task = dtesn_task_create(5004, DTESN_WORKLOAD_MEMBRANE,
                                             DTESN_SCHED_POLICY_REALTIME, 5);
    if (rt_task) {
        rt_task->membrane_level = 2;
        
        int result = dtesn_sched_set_policy(rt_task, DTESN_SCHED_POLICY_REALTIME, 5);
        print_test_result("Set DTESN real-time policy", result == 0);
        
        dtesn_task_destroy(rt_task);
    }
}

/**
 * test_performance_requirements - Test performance requirements
 */
static void test_performance_requirements(void)
{
    printf("\n=== Performance Requirements Tests ===\n");
    
    /* Test context switch latency */
    dtesn_task_t *task = dtesn_task_create(6001, DTESN_WORKLOAD_MEMBRANE,
                                          DTESN_SCHED_POLICY_REALTIME, 10);
    
    if (task) {
        uint64_t start_time = get_time_ns();
        dtesn_task_t *scheduled = dtesn_task_schedule(0);
        uint64_t end_time = get_time_ns();
        
        uint64_t latency_ns = end_time - start_time;
        uint64_t threshold_ns = DTESN_SCHED_LATENCY_THRESHOLD_US * 1000;
        
        print_test_result("Context switch latency meets requirement (≤10μs)",
                         latency_ns <= threshold_ns);
        
        printf("   Measured latency: %lu ns (%.2f μs)\n", latency_ns, latency_ns / 1000.0);
        
        dtesn_task_destroy(task);
    }
    
    /* Test scheduling overhead */
    const int num_iterations = 1000;
    uint64_t total_latency = 0;
    
    for (int i = 0; i < num_iterations; i++) {
        uint64_t start = get_time_ns();
        dtesn_task_schedule(0);
        uint64_t end = get_time_ns();
        total_latency += (end - start);
    }
    
    uint64_t avg_latency = total_latency / num_iterations;
    uint64_t threshold_ns = DTESN_SCHED_LATENCY_THRESHOLD_US * 1000;
    
    print_test_result("Average scheduling latency meets requirement",
                     avg_latency <= threshold_ns);
    
    printf("   Average latency: %lu ns (%.2f μs)\n", avg_latency, avg_latency / 1000.0);
    
    /* Get performance statistics */
    dtesn_sched_perf_t *perf = dtesn_sched_get_performance(-1);
    if (perf) {
        printf("   Context switches: %lu\n", perf->context_switches);
        printf("   Max latency: %lu ns (%.2f μs)\n", 
               perf->max_latency_ns, perf->max_latency_ns / 1000.0);
        printf("   Min latency: %lu ns (%.2f μs)\n", 
               perf->min_latency_ns, perf->min_latency_ns / 1000.0);
        printf("   Avg latency: %lu ns (%.2f μs)\n", 
               perf->scheduling_latency_ns, perf->scheduling_latency_ns / 1000.0);
        printf("   Jitter: %lu ns (%.2f μs)\n", 
               perf->jitter_ns, perf->jitter_ns / 1000.0);
        
        print_test_result("Jitter meets requirement (≤1μs)",
                         perf->jitter_ns <= DTESN_SCHED_JITTER_THRESHOLD_US * 1000);
    }
}

/**
 * test_oeis_compliance - Test OEIS A000081 compliance
 */
static void test_oeis_compliance(void)
{
    printf("\n=== OEIS A000081 Compliance Tests ===\n");
    
    /* Test OEIS validation function */
    bool result = dtesn_sched_validate_oeis(NULL, 0);
    print_test_result("OEIS validation with valid depth 0", result);
    
    result = dtesn_sched_validate_oeis(NULL, 1);
    print_test_result("OEIS validation with valid depth 1", result);
    
    result = dtesn_sched_validate_oeis(NULL, DTESN_SCHED_A000081_MAX_DEPTH);
    print_test_result("OEIS validation with max depth (should pass)", result);
    
    result = dtesn_sched_validate_oeis(NULL, DTESN_SCHED_A000081_MAX_DEPTH + 1);
    print_test_result("OEIS validation with invalid depth (should pass - skip validation)", result);
    
    /* Test task OEIS compliance */
    dtesn_task_t *task = dtesn_task_create(7001, DTESN_WORKLOAD_MEMBRANE,
                                          DTESN_SCHED_POLICY_REALTIME, 10);
    if (task) {
        print_test_result("Task is OEIS compliant", task->oeis_compliant);
        print_test_result("Task has valid memory zone", task->memory_zone < DTESN_SCHED_A000081_MAX_DEPTH);
        
        dtesn_task_destroy(task);
    }
}

/**
 * test_stress_testing - Stress test the scheduler
 */
static void test_stress_testing(void)
{
    printf("\n=== Stress Testing ===\n");
    
    printf("Running stress test for %d seconds...\n", TEST_STRESS_DURATION);
    
    uint64_t start_time = get_time_ns();
    uint64_t end_time = start_time + (TEST_STRESS_DURATION * 1000000000ULL);
    
    dtesn_task_t *stress_tasks[50];
    int num_stress_tasks = 0;
    
    /* Create stress test tasks */
    for (int i = 0; i < 50; i++) {
        dtesn_workload_type_t workload = i % 6; /* Cycle through workload types */
        dtesn_sched_policy_t policy = i % 4;    /* Cycle through policies */
        uint32_t priority = i % DTESN_SCHED_MAX_PRIORITIES;
        
        stress_tasks[i] = dtesn_task_create(8000 + i, workload, policy, priority);
        if (stress_tasks[i]) {
            num_stress_tasks++;
            
            /* Set random deadline for EDF tasks */
            if (policy == DTESN_SCHED_POLICY_EDF) {
                stress_tasks[i]->deadline_ns = get_time_ns() + (rand() % 100000000);
            }
            
            /* Set random period for RM tasks */
            if (policy == DTESN_SCHED_POLICY_RM) {
                stress_tasks[i]->period_ns = 10000000 + (rand() % 90000000);
                stress_tasks[i]->budget_ns = stress_tasks[i]->period_ns / 2;
            }
        }
    }
    
    print_test_result("Create stress test tasks", num_stress_tasks >= 40);
    
    /* Run stress test */
    uint64_t iterations = 0;
    uint64_t total_latency = 0;
    uint64_t max_latency = 0;
    
    while (get_time_ns() < end_time) {
        for (uint32_t cpu = 0; cpu < TEST_MAX_CPUS; cpu++) {
            uint64_t sched_start = get_time_ns();
            dtesn_task_schedule(cpu);
            uint64_t sched_end = get_time_ns();
            
            uint64_t latency = sched_end - sched_start;
            total_latency += latency;
            if (latency > max_latency) {
                max_latency = latency;
            }
            iterations++;
        }
        
        /* Periodically trigger load balancing */
        if (iterations % 100 == 0) {
            dtesn_load_balance(0);
        }
        
        /* Small delay to prevent busy loop */
        usleep(1000); /* 1ms */
    }
    
    uint64_t avg_latency = iterations > 0 ? total_latency / iterations : 0;
    
    printf("   Iterations: %lu\n", iterations);
    printf("   Average latency: %lu ns (%.2f μs)\n", avg_latency, avg_latency / 1000.0);
    printf("   Maximum latency: %lu ns (%.2f μs)\n", max_latency, max_latency / 1000.0);
    
    print_test_result("Stress test completed", iterations > 1000);
    print_test_result("Average latency under stress meets requirement",
                     avg_latency <= DTESN_SCHED_LATENCY_THRESHOLD_US * 1000);
    print_test_result("Maximum latency under stress reasonable",
                     max_latency <= DTESN_SCHED_LATENCY_THRESHOLD_US * 1000 * 10);
    
    /* Cleanup stress test tasks */
    for (int i = 0; i < num_stress_tasks; i++) {
        if (stress_tasks[i]) {
            dtesn_task_destroy(stress_tasks[i]);
        }
    }
}

/**
 * test_integration - Test integration with existing DTESN components
 */
static void test_integration(void)
{
    printf("\n=== Integration Tests ===\n");
    
    /* Test integration with different DTESN workload types */
    dtesn_task_t *membrane_task = dtesn_task_create(9001, DTESN_WORKLOAD_MEMBRANE,
                                                   DTESN_SCHED_POLICY_REALTIME, 5);
    dtesn_task_t *esn_task = dtesn_task_create(9002, DTESN_WORKLOAD_ESN,
                                              DTESN_SCHED_POLICY_EDF, 10);
    dtesn_task_t *bseries_task = dtesn_task_create(9003, DTESN_WORKLOAD_BSERIES,
                                                  DTESN_SCHED_POLICY_RM, 15);
    
    print_test_result("Create DTESN workload tasks", 
                     membrane_task && esn_task && bseries_task);
    
    if (membrane_task && esn_task && bseries_task) {
        /* Set appropriate parameters for each task type */
        esn_task->deadline_ns = get_time_ns() + 10000000; /* 10ms deadline */
        bseries_task->period_ns = 20000000; /* 20ms period */
        bseries_task->budget_ns = 10000000; /* 10ms budget */
        
        /* Add all tasks to run queue */
        dtesn_sched_add_task(membrane_task, 0);
        dtesn_sched_add_task(esn_task, 0);
        dtesn_sched_add_task(bseries_task, 0);
        
        /* Schedule tasks and verify DTESN priority ordering */
        dtesn_task_t *scheduled = dtesn_task_schedule(0);
        print_test_result("Membrane task scheduled first (highest DTESN priority)",
                         scheduled && scheduled->workload_type == DTESN_WORKLOAD_MEMBRANE);
        
        /* Test workload-specific attributes */
        print_test_result("Membrane task has correct attributes",
                         membrane_task->requires_fpu && 
                         membrane_task->membrane_level > 0 &&
                         membrane_task->memory_zone > 0);
        
        print_test_result("ESN task has correct attributes",
                         esn_task->requires_fpu && 
                         esn_task->requires_vector &&
                         esn_task->deadline_ns > 0);
        
        print_test_result("B-Series task has correct attributes",
                         bseries_task->requires_fpu && 
                         bseries_task->bseries_order > 0 &&
                         bseries_task->period_ns > 0);
        
        /* Cleanup */
        dtesn_task_destroy(membrane_task);
        dtesn_task_destroy(esn_task);
        dtesn_task_destroy(bseries_task);
    }
    
    /* Test scheduler cleanup */
    int result = dtesn_sched_cleanup();
    print_test_result("Scheduler cleanup", result == 0);
}

/**
 * main - Run all scheduler tests
 */
int main(void)
{
    printf("DTESN Real-Time Scheduler Test Suite\n");
    printf("====================================\n");
    
    /* Initialize random seed for stress testing */
    srand(time(NULL));
    
    /* Run all test suites */
    test_scheduler_init();
    test_task_creation();
    test_task_scheduling();
    test_deadline_checking();
    test_load_balancing();
    test_priority_inheritance();
    test_scheduling_policies();
    test_performance_requirements();
    test_oeis_compliance();
    test_stress_testing();
    test_integration();
    
    /* Print final summary */
    print_test_summary();
    
    return (tests_failed == 0) ? 0 : 1;
}