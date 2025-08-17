/*
 * DTESN Real-Time Scheduler for Neuromorphic Computing
 * ===================================================
 * 
 * Deep Tree Echo State Networks (DTESN) real-time scheduler providing
 * deterministic task scheduling optimized for membrane computing workloads
 * with strict timing constraints and OEIS A000081 compliance.
 * 
 * Performance Requirements:
 * - Context switch: ≤ 5μs
 * - Scheduling latency: ≤ 10μs
 * - Jitter: ≤ 1μs
 * - CPU overhead: ≤ 5%
 * 
 * Scheduling Architecture:
 * - DTESN-aware workload classification
 * - Deadline-sensitive task prioritization
 * - Membrane computing priority levels
 * - Multi-core load balancing
 * - Priority inheritance protocol
 */

#ifndef DTESN_SCHEDULER_H
#define DTESN_SCHEDULER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Scheduler configuration constants */
#define DTESN_SCHED_MAX_TASKS           4096    /* Maximum tasks in system */
#define DTESN_SCHED_MAX_CPUS            64      /* Maximum CPU cores */
#define DTESN_SCHED_MAX_PRIORITIES      256     /* Priority levels (0-255) */
#define DTESN_SCHED_MAX_RUNQUEUES       64      /* Per-CPU run queues */
#define DTESN_SCHED_QUANTUM_NS          1000000 /* 1ms default time quantum */

/* Performance thresholds (microseconds) */
#define DTESN_SCHED_CONTEXT_SWITCH_THRESHOLD_US    5    /* ≤ 5μs context switch */
#define DTESN_SCHED_LATENCY_THRESHOLD_US          10    /* ≤ 10μs scheduling latency */
#define DTESN_SCHED_JITTER_THRESHOLD_US            1    /* ≤ 1μs jitter */
#define DTESN_SCHED_CPU_OVERHEAD_THRESHOLD_PCT     5    /* ≤ 5% CPU overhead */

/* OEIS A000081 sequence for hierarchy validation */
#define DTESN_SCHED_A000081_MAX_DEPTH 10
#define DTESN_SCHED_A000081_SEQUENCE \
    { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719 }

/* DTESN scheduling policies */
typedef enum {
    DTESN_SCHED_POLICY_REALTIME = 0,    /* Custom DTESN real-time policy */
    DTESN_SCHED_POLICY_EDF = 1,         /* Earliest Deadline First */
    DTESN_SCHED_POLICY_RM = 2,          /* Rate Monotonic */
    DTESN_SCHED_POLICY_CFS = 3,         /* Completely Fair Scheduler */
    DTESN_SCHED_POLICY_FIFO = 4,        /* First-In-First-Out */
    DTESN_SCHED_POLICY_RR = 5           /* Round Robin */
} dtesn_sched_policy_t;

/* DTESN workload types for scheduling optimization */
typedef enum {
    DTESN_WORKLOAD_MEMBRANE = 0,        /* P-system membrane computing */
    DTESN_WORKLOAD_ESN = 1,             /* Echo State Network reservoir */
    DTESN_WORKLOAD_BSERIES = 2,         /* B-Series tree computation */
    DTESN_WORKLOAD_MEMORY = 3,          /* Memory management operations */
    DTESN_WORKLOAD_IO = 4,              /* I/O bound operations */
    DTESN_WORKLOAD_GENERAL = 5          /* General purpose tasks */
} dtesn_workload_type_t;

/* Task states */
typedef enum {
    DTESN_TASK_STATE_READY = 0,         /* Ready to run */
    DTESN_TASK_STATE_RUNNING = 1,       /* Currently executing */
    DTESN_TASK_STATE_WAITING = 2,       /* Waiting for resource */
    DTESN_TASK_STATE_BLOCKED = 3,       /* Blocked on I/O or event */
    DTESN_TASK_STATE_TERMINATED = 4     /* Task finished */
} dtesn_task_state_t;

/* Priority inheritance states */
typedef enum {
    DTESN_PI_STATE_NORMAL = 0,          /* Normal priority */
    DTESN_PI_STATE_INHERITED = 1,       /* Inherited higher priority */
    DTESN_PI_STATE_BOOSTED = 2          /* Temporarily boosted priority */
} dtesn_pi_state_t;

/* Performance measurement structure */
typedef struct dtesn_sched_perf {
    uint64_t context_switches;          /* Total context switches */
    uint64_t scheduling_latency_ns;     /* Average scheduling latency */
    uint64_t jitter_ns;                 /* Scheduling jitter */
    uint64_t cpu_overhead_ns;           /* Scheduler CPU overhead */
    uint64_t missed_deadlines;          /* Count of missed deadlines */
    
    /* Real-time metrics */
    uint64_t last_context_switch_ns;    /* Last context switch time */
    uint64_t max_latency_ns;            /* Maximum observed latency */
    uint64_t min_latency_ns;            /* Minimum observed latency */
    double cpu_utilization;             /* CPU utilization percentage */
} dtesn_sched_perf_t;

/* Task control block for DTESN tasks */
typedef struct dtesn_task {
    uint32_t task_id;                   /* Unique task identifier */
    uint32_t pid;                       /* Process ID */
    uint32_t tgid;                      /* Thread group ID */
    
    /* Scheduling attributes */
    dtesn_sched_policy_t policy;        /* Scheduling policy */
    dtesn_workload_type_t workload_type; /* DTESN workload classification */
    dtesn_task_state_t state;           /* Current task state */
    uint32_t priority;                  /* Task priority (0-255) */
    int32_t nice;                       /* Nice value (-20 to 19) */
    
    /* Real-time attributes */
    uint64_t deadline_ns;               /* Absolute deadline (EDF) */
    uint64_t period_ns;                 /* Task period (Rate Monotonic) */
    uint64_t runtime_ns;                /* Actual runtime this period */
    uint64_t budget_ns;                 /* Time budget for period */
    uint64_t wcet_ns;                   /* Worst-case execution time */
    
    /* Priority inheritance */
    dtesn_pi_state_t pi_state;          /* Priority inheritance state */
    uint32_t original_priority;         /* Original priority before PI */
    uint32_t effective_priority;        /* Current effective priority */
    struct dtesn_task *pi_blocked_on;   /* Task we're blocked on */
    
    /* CPU affinity and load balancing */
    uint32_t cpu_affinity_mask;         /* CPU affinity bit mask */
    uint32_t current_cpu;               /* Currently assigned CPU */
    uint32_t preferred_cpu;             /* Preferred CPU for locality */
    uint64_t last_ran_ns;               /* Last execution timestamp */
    
    /* Performance tracking */
    uint64_t total_runtime_ns;          /* Total execution time */
    uint64_t context_switches;          /* Number of context switches */
    uint64_t voluntary_switches;        /* Voluntary context switches */
    uint64_t involuntary_switches;      /* Involuntary context switches */
    
    /* DTESN-specific attributes */
    uint32_t membrane_level;            /* P-system membrane hierarchy level */
    uint32_t esn_reservoir_id;          /* Associated ESN reservoir */
    uint32_t bseries_order;             /* B-Series computation order */
    bool requires_fpu;                  /* Requires floating-point unit */
    bool requires_vector;               /* Requires vector operations */
    
    /* Memory layout compliance with OEIS A000081 */
    uint32_t memory_zone;               /* Memory zone based on A000081 */
    bool oeis_compliant;                /* OEIS A000081 compliance flag */
    
    /* Synchronization */
    pthread_mutex_t task_lock;          /* Task structure protection */
    
    /* Linked list pointers for run queues */
    struct dtesn_task *next;            /* Next task in queue */
    struct dtesn_task *prev;            /* Previous task in queue */
    
} dtesn_task_t;

/* Per-CPU run queue structure */
typedef struct dtesn_runqueue {
    uint32_t cpu_id;                    /* CPU identifier */
    uint32_t nr_running;                /* Number of runnable tasks */
    uint32_t nr_switches;               /* Context switches on this CPU */
    
    /* Task queues by priority */
    dtesn_task_t *ready_queue[DTESN_SCHED_MAX_PRIORITIES];
    uint32_t queue_bitmap;              /* Bitmap of non-empty queues */
    
    /* Current task */
    dtesn_task_t *current_task;         /* Currently running task */
    dtesn_task_t *idle_task;            /* Idle task for this CPU */
    
    /* Load balancing */
    uint64_t load_weight;               /* CPU load weight */
    uint64_t last_balance_ns;           /* Last load balance timestamp */
    
    /* Real-time scheduling */
    uint64_t next_deadline_ns;          /* Next task deadline */
    uint32_t rt_tasks;                  /* Number of real-time tasks */
    
    /* Performance tracking */
    dtesn_sched_perf_t perf;            /* Per-CPU performance metrics */
    
    /* Synchronization */
    pthread_spinlock_t rq_lock;         /* Run queue lock */
    
} dtesn_runqueue_t;

/* Global scheduler state */
typedef struct dtesn_scheduler {
    bool initialized;                   /* Scheduler initialization status */
    uint32_t nr_cpus;                   /* Number of available CPUs */
    uint32_t nr_tasks;                  /* Total number of tasks */
    
    /* Per-CPU run queues */
    dtesn_runqueue_t runqueues[DTESN_SCHED_MAX_CPUS];
    
    /* Global task management */
    dtesn_task_t *task_table[DTESN_SCHED_MAX_TASKS];
    uint32_t next_task_id;              /* Next available task ID */
    
    /* Load balancing configuration */
    bool load_balancing_enabled;        /* Enable/disable load balancing */
    uint64_t balance_interval_ns;       /* Load balance interval */
    uint32_t migration_threshold;       /* Task migration threshold */
    
    /* Priority inheritance configuration */
    bool priority_inheritance_enabled;  /* Enable/disable PI */
    uint32_t pi_boost_limit;            /* Maximum PI boost levels */
    
    /* Performance monitoring */
    dtesn_sched_perf_t global_perf;     /* Global performance metrics */
    uint64_t scheduler_start_time_ns;   /* Scheduler start timestamp */
    
    /* OEIS A000081 compliance tracking */
    uint32_t oeis_sequence[DTESN_SCHED_A000081_MAX_DEPTH];
    bool oeis_validation_enabled;       /* Enable OEIS compliance checking */
    
    /* Synchronization */
    pthread_mutex_t scheduler_lock;     /* Global scheduler lock */
    
} dtesn_scheduler_t;

/* Function prototypes */

/**
 * dtesn_sched_init - Initialize the DTESN scheduler
 * @nr_cpus: Number of CPU cores available
 * 
 * Initializes the DTESN real-time scheduler with specified number of CPUs.
 * Sets up per-CPU run queues, performance monitoring, and OEIS A000081
 * compliance validation.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_init(uint32_t nr_cpus);

/**
 * dtesn_task_schedule - Schedule tasks for execution
 * @cpu_id: Target CPU for scheduling
 * 
 * Core scheduling function that selects the next task to run on the
 * specified CPU. Considers DTESN workload types, real-time constraints,
 * and priority inheritance.
 * 
 * Return: Pointer to selected task, NULL if no runnable tasks
 */
dtesn_task_t *dtesn_task_schedule(uint32_t cpu_id);

/**
 * dtesn_deadline_check - Check and enforce task deadlines
 * @task: Task to check deadline for
 * @current_time_ns: Current system time in nanoseconds
 * 
 * Validates that the specified task meets its deadline constraints.
 * Updates performance metrics for missed deadlines and triggers
 * deadline enforcement actions.
 * 
 * Return: true if deadline met, false if deadline missed
 */
bool dtesn_deadline_check(dtesn_task_t *task, uint64_t current_time_ns);

/**
 * dtesn_load_balance - Balance load across CPU cores
 * @trigger_cpu: CPU that triggered load balancing
 * 
 * Performs load balancing across all available CPU cores to optimize
 * system throughput and meet real-time constraints. Considers CPU
 * affinity and DTESN workload characteristics.
 * 
 * Return: Number of tasks migrated, negative on error
 */
int dtesn_load_balance(uint32_t trigger_cpu);

/**
 * dtesn_priority_inherit - Handle priority inheritance
 * @blocked_task: Task that is blocked
 * @blocking_task: Task causing the block
 * 
 * Implements priority inheritance protocol to prevent priority inversion.
 * Temporarily boosts the priority of the blocking task to match the
 * highest priority blocked task.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_priority_inherit(dtesn_task_t *blocked_task, dtesn_task_t *blocking_task);

/**
 * dtesn_task_create - Create a new DTESN task
 * @pid: Process ID
 * @workload_type: DTESN workload classification
 * @policy: Scheduling policy
 * @priority: Task priority
 * 
 * Creates and initializes a new DTESN task with specified attributes.
 * Validates OEIS A000081 compliance and sets up performance tracking.
 * 
 * Return: Pointer to new task, NULL on failure
 */
dtesn_task_t *dtesn_task_create(uint32_t pid, dtesn_workload_type_t workload_type,
                                dtesn_sched_policy_t policy, uint32_t priority);

/**
 * dtesn_task_destroy - Destroy a DTESN task
 * @task: Task to destroy
 * 
 * Cleans up task resources and removes from scheduling queues.
 * Updates performance statistics and frees memory.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_task_destroy(dtesn_task_t *task);

/**
 * dtesn_sched_get_performance - Get scheduler performance metrics
 * @cpu_id: CPU ID for per-CPU metrics, -1 for global
 * 
 * Returns performance metrics for the specified CPU or global
 * scheduler performance if cpu_id is -1.
 * 
 * Return: Pointer to performance structure, NULL on error
 */
dtesn_sched_perf_t *dtesn_sched_get_performance(int cpu_id);

/**
 * dtesn_sched_set_policy - Set scheduling policy for task
 * @task: Target task
 * @policy: New scheduling policy
 * @priority: New priority (if applicable)
 * 
 * Changes the scheduling policy and priority for the specified task.
 * Validates policy parameters and updates run queue placement.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_set_policy(dtesn_task_t *task, dtesn_sched_policy_t policy, uint32_t priority);

/**
 * dtesn_sched_validate_oeis - Validate OEIS A000081 compliance
 * @structure_data: Data structure to validate
 * @depth: Hierarchy depth to check
 * 
 * Validates that the given structure follows OEIS A000081 enumeration
 * for rooted trees. Used to ensure scheduler data structures maintain
 * mathematical correctness.
 * 
 * Return: true if compliant, false otherwise
 */
bool dtesn_sched_validate_oeis(void *structure_data, uint32_t depth);

/**
 * dtesn_sched_cleanup - Cleanup scheduler resources
 * 
 * Performs complete cleanup of scheduler resources, including stopping
 * all tasks, freeing memory, and releasing locks.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_cleanup(void);

/**
 * dtesn_sched_policy_select - Select task based on scheduling policy
 * @rq: Run queue to select from
 * @selected_task: Output parameter for selected task
 * 
 * Main policy selection function that dispatches to specific policy
 * implementations based on task requirements.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_policy_select(dtesn_runqueue_t *rq, dtesn_task_t **selected_task);

/**
 * dtesn_sched_add_task - Add task to scheduler run queue
 * @task: Task to add to scheduler
 * @cpu_id: CPU to add task to (use -1 for automatic selection)
 * 
 * Adds the specified task to a CPU run queue for scheduling.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_add_task(dtesn_task_t *task, int cpu_id);

#ifdef __cplusplus
}
#endif

#endif /* DTESN_SCHEDULER_H */