/*
 * DTESN Scheduling Policies Implementation
 * =======================================
 * 
 * Implementation of various scheduling policies optimized for
 * Deep Tree Echo State Networks (DTESN) workloads.
 */

#include <dtesn/scheduler.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>
#include <errno.h>

/* Forward declarations */
static int dtesn_policy_realtime_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected);
static int dtesn_policy_edf_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected);
static int dtesn_policy_rm_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected);
static int dtesn_policy_cfs_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected);
static uint64_t dtesn_get_time_ns(void);
static uint32_t dtesn_calculate_workload_priority(dtesn_workload_type_t workload_type);

/**
 * dtesn_get_time_ns - Get current time in nanoseconds
 * 
 * Return: Current system time in nanoseconds
 */
static uint64_t dtesn_get_time_ns(void)
{
    struct timespec ts;
    
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

/**
 * dtesn_calculate_workload_priority - Calculate priority boost for DTESN workloads
 * @workload_type: Type of DTESN workload
 * 
 * Return: Priority boost value (0 = highest boost)
 */
static uint32_t dtesn_calculate_workload_priority(dtesn_workload_type_t workload_type)
{
    switch (workload_type) {
        case DTESN_WORKLOAD_MEMBRANE:
            return 0;   /* Highest priority - membrane computing is critical */
        case DTESN_WORKLOAD_ESN:
            return 10;  /* High priority - reservoir state updates */
        case DTESN_WORKLOAD_BSERIES:
            return 20;  /* Medium-high priority - mathematical computations */
        case DTESN_WORKLOAD_MEMORY:
            return 30;  /* Medium priority - memory operations */
        case DTESN_WORKLOAD_IO:
            return 40;  /* Lower priority - I/O bound operations */
        case DTESN_WORKLOAD_GENERAL:
        default:
            return 50;  /* Lowest priority - general purpose tasks */
    }
}

/**
 * dtesn_policy_realtime_schedule - DTESN real-time scheduling policy
 * @rq: Run queue to schedule from
 * @selected: Output parameter for selected task
 * 
 * Custom DTESN real-time policy that prioritizes membrane computing
 * workloads and enforces strict timing constraints.
 * 
 * Return: 0 on success, negative error code on failure
 */
static int dtesn_policy_realtime_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected)
{
    if (!rq || !selected) {
        return -EINVAL;
    }
    
    *selected = NULL;
    
    dtesn_task_t *best_task = NULL;
    uint32_t best_priority = UINT32_MAX;
    uint64_t current_time = dtesn_get_time_ns();
    
    /* Search all priority levels for DTESN real-time tasks */
    for (int priority = 0; priority < DTESN_SCHED_MAX_PRIORITIES; priority++) {
        if (!(rq->queue_bitmap & (1U << priority))) {
            continue;
        }
        
        dtesn_task_t *task = rq->ready_queue[priority];
        
        while (task) {
            if (task->policy == DTESN_SCHED_POLICY_REALTIME) {
                /* Calculate effective priority based on DTESN workload */
                uint32_t workload_boost = dtesn_calculate_workload_priority(task->workload_type);
                uint32_t effective_prio = task->effective_priority + workload_boost;
                
                /* Additional priority boost for membrane computing */
                if (task->workload_type == DTESN_WORKLOAD_MEMBRANE) {
                    /* Check membrane level for additional boost */
                    if (task->membrane_level <= 3) {
                        effective_prio = (effective_prio > 5) ? effective_prio - 5 : 0;
                    }
                }
                
                /* Additional boost for tasks with tight deadlines */
                if (task->deadline_ns > 0 && task->deadline_ns < current_time + 1000000) {
                    /* Deadline within 1ms - urgent */
                    effective_prio = (effective_prio > 10) ? effective_prio - 10 : 0;
                }
                
                /* Additional boost for ESN reservoir tasks */
                if (task->workload_type == DTESN_WORKLOAD_ESN && task->requires_vector) {
                    /* Vector operations need consistent scheduling */
                    effective_prio = (effective_prio > 3) ? effective_prio - 3 : 0;
                }
                
                /* Select task with best (lowest) effective priority */
                if (effective_prio < best_priority) {
                    best_priority = effective_prio;
                    best_task = task;
                }
            }
            
            task = task->next;
        }
    }
    
    if (best_task) {
        *selected = best_task;
        return 0;
    }
    
    return -ENOENT;
}

/**
 * dtesn_policy_edf_schedule - Earliest Deadline First scheduling
 * @rq: Run queue to schedule from
 * @selected: Output parameter for selected task
 * 
 * Return: 0 on success, negative error code on failure
 */
static int dtesn_policy_edf_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected)
{
    if (!rq || !selected) {
        return -EINVAL;
    }
    
    *selected = NULL;
    
    dtesn_task_t *earliest_task = NULL;
    uint64_t earliest_deadline = UINT64_MAX;
    uint64_t current_time = dtesn_get_time_ns();
    
    /* Search all priority levels for EDF tasks */
    for (int priority = 0; priority < DTESN_SCHED_MAX_PRIORITIES; priority++) {
        if (!(rq->queue_bitmap & (1U << priority))) {
            continue;
        }
        
        dtesn_task_t *task = rq->ready_queue[priority];
        
        while (task) {
            if (task->policy == DTESN_SCHED_POLICY_EDF && task->deadline_ns > 0) {
                /* Check if deadline has already passed */
                if (task->deadline_ns < current_time) {
                    /* Deadline missed - highest priority */
                    earliest_deadline = 0;
                    earliest_task = task;
                    break;
                }
                
                /* Select task with earliest deadline */
                if (task->deadline_ns < earliest_deadline) {
                    earliest_deadline = task->deadline_ns;
                    earliest_task = task;
                }
            }
            
            task = task->next;
        }
        
        if (earliest_deadline == 0) {
            break; /* Found task with missed deadline */
        }
    }
    
    if (earliest_task) {
        *selected = earliest_task;
        return 0;
    }
    
    return -ENOENT;
}

/**
 * dtesn_policy_rm_schedule - Rate Monotonic scheduling
 * @rq: Run queue to schedule from
 * @selected: Output parameter for selected task
 * 
 * Return: 0 on success, negative error code on failure
 */
static int dtesn_policy_rm_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected)
{
    if (!rq || !selected) {
        return -EINVAL;
    }
    
    *selected = NULL;
    
    dtesn_task_t *shortest_period_task = NULL;
    uint64_t shortest_period = UINT64_MAX;
    uint64_t current_time = dtesn_get_time_ns();
    
    /* Search all priority levels for Rate Monotonic tasks */
    for (int priority = 0; priority < DTESN_SCHED_MAX_PRIORITIES; priority++) {
        if (!(rq->queue_bitmap & (1U << priority))) {
            continue;
        }
        
        dtesn_task_t *task = rq->ready_queue[priority];
        
        while (task) {
            if (task->policy == DTESN_SCHED_POLICY_RM && task->period_ns > 0) {
                /* Check if task has exceeded its budget for this period */
                if (task->budget_ns > 0 && task->runtime_ns >= task->budget_ns) {
                    /* Budget exhausted - skip this task */
                    task = task->next;
                    continue;
                }
                
                /* Check if we're still within the current period */
                uint64_t period_start = (current_time / task->period_ns) * task->period_ns;
                uint64_t time_in_period = current_time - period_start;
                
                if (time_in_period < task->period_ns) {
                    /* Select task with shortest period (highest frequency) */
                    if (task->period_ns < shortest_period) {
                        shortest_period = task->period_ns;
                        shortest_period_task = task;
                    }
                }
            }
            
            task = task->next;
        }
    }
    
    if (shortest_period_task) {
        *selected = shortest_period_task;
        return 0;
    }
    
    return -ENOENT;
}

/**
 * dtesn_policy_cfs_schedule - Completely Fair Scheduler
 * @rq: Run queue to schedule from
 * @selected: Output parameter for selected task
 * 
 * Return: 0 on success, negative error code on failure
 */
static int dtesn_policy_cfs_schedule(dtesn_runqueue_t *rq, dtesn_task_t **selected)
{
    if (!rq || !selected) {
        return -EINVAL;
    }
    
    *selected = NULL;
    
    dtesn_task_t *fairest_task = NULL;
    uint64_t min_runtime = UINT64_MAX;
    
    /* Search all priority levels for CFS tasks */
    for (int priority = 0; priority < DTESN_SCHED_MAX_PRIORITIES; priority++) {
        if (!(rq->queue_bitmap & (1U << priority))) {
            continue;
        }
        
        dtesn_task_t *task = rq->ready_queue[priority];
        
        while (task) {
            if (task->policy == DTESN_SCHED_POLICY_CFS) {
                /* Adjust runtime based on nice value */
                uint64_t weighted_runtime = task->total_runtime_ns;
                
                /* Apply nice value weighting */
                if (task->nice > 0) {
                    /* Lower priority - increase virtual runtime */
                    weighted_runtime = weighted_runtime * (100 + task->nice * 5) / 100;
                } else if (task->nice < 0) {
                    /* Higher priority - decrease virtual runtime */
                    weighted_runtime = weighted_runtime * 100 / (100 + (-task->nice) * 5);
                }
                
                /* Select task with minimum weighted runtime */
                if (weighted_runtime < min_runtime) {
                    min_runtime = weighted_runtime;
                    fairest_task = task;
                }
            }
            
            task = task->next;
        }
    }
    
    if (fairest_task) {
        *selected = fairest_task;
        return 0;
    }
    
    return -ENOENT;
}

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
int dtesn_sched_policy_select(dtesn_runqueue_t *rq, dtesn_task_t **selected_task)
{
    if (!rq || !selected_task) {
        return -EINVAL;
    }
    
    *selected_task = NULL;
    
    /* Policy selection order (highest to lowest priority):
     * 1. DTESN_REALTIME - Custom DTESN real-time policy
     * 2. EDF - Earliest Deadline First
     * 3. Rate Monotonic - Fixed priority based on period
     * 4. CFS - Completely Fair Scheduler
     * 5. FIFO/RR - Simple policies
     */
    
    dtesn_task_t *candidate_task = NULL;
    int result;
    
    /* Try DTESN real-time policy first */
    result = dtesn_policy_realtime_schedule(rq, &candidate_task);
    if (result == 0 && candidate_task) {
        *selected_task = candidate_task;
        return 0;
    }
    
    /* Try EDF policy */
    result = dtesn_policy_edf_schedule(rq, &candidate_task);
    if (result == 0 && candidate_task) {
        *selected_task = candidate_task;
        return 0;
    }
    
    /* Try Rate Monotonic policy */
    result = dtesn_policy_rm_schedule(rq, &candidate_task);
    if (result == 0 && candidate_task) {
        *selected_task = candidate_task;
        return 0;
    }
    
    /* Try CFS policy */
    result = dtesn_policy_cfs_schedule(rq, &candidate_task);
    if (result == 0 && candidate_task) {
        *selected_task = candidate_task;
        return 0;
    }
    
    /* Fall back to simple priority-based selection (FIFO/RR) */
    for (int priority = 0; priority < DTESN_SCHED_MAX_PRIORITIES; priority++) {
        if (!(rq->queue_bitmap & (1U << priority))) {
            continue;
        }
        
        dtesn_task_t *task = rq->ready_queue[priority];
        if (task) {
            *selected_task = task;
            return 0;
        }
    }
    
    return -ENOENT; /* No runnable tasks */
}

/**
 * dtesn_sched_policy_update_runtime - Update task runtime for policies
 * @task: Task to update
 * @runtime_ns: Runtime to add in nanoseconds
 * 
 * Updates task runtime statistics for scheduling policy decisions.
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_policy_update_runtime(dtesn_task_t *task, uint64_t runtime_ns)
{
    if (!task) {
        return -EINVAL;
    }
    
    pthread_mutex_lock(&task->task_lock);
    
    /* Update total runtime */
    task->total_runtime_ns += runtime_ns;
    
    /* Update runtime for current period (Rate Monotonic) */
    if (task->policy == DTESN_SCHED_POLICY_RM && task->period_ns > 0) {
        uint64_t current_time = dtesn_get_time_ns();
        uint64_t period_start = (current_time / task->period_ns) * task->period_ns;
        
        /* Reset runtime if we've entered a new period */
        if (task->last_ran_ns < period_start) {
            task->runtime_ns = 0;
        }
        
        task->runtime_ns += runtime_ns;
    }
    
    pthread_mutex_unlock(&task->task_lock);
    
    return 0;
}

/**
 * dtesn_sched_policy_check_preemption - Check if current task should be preempted
 * @current_task: Currently running task
 * @new_task: Newly arrived task
 * 
 * Determines if the current task should be preempted by a new task
 * based on scheduling policy requirements.
 * 
 * Return: true if preemption should occur, false otherwise
 */
bool dtesn_sched_policy_check_preemption(dtesn_task_t *current_task, dtesn_task_t *new_task)
{
    if (!current_task || !new_task) {
        return false;
    }
    
    uint64_t current_time = dtesn_get_time_ns();
    
    /* Real-time policies have preemption priority */
    if (new_task->policy == DTESN_SCHED_POLICY_REALTIME ||
        new_task->policy == DTESN_SCHED_POLICY_EDF ||
        new_task->policy == DTESN_SCHED_POLICY_RM) {
        
        /* Non-RT task should always be preempted by RT task */
        if (current_task->policy != DTESN_SCHED_POLICY_REALTIME &&
            current_task->policy != DTESN_SCHED_POLICY_EDF &&
            current_task->policy != DTESN_SCHED_POLICY_RM) {
            return true;
        }
        
        /* Check EDF preemption */
        if (new_task->policy == DTESN_SCHED_POLICY_EDF &&
            current_task->policy == DTESN_SCHED_POLICY_EDF) {
            return (new_task->deadline_ns < current_task->deadline_ns);
        }
        
        /* Check Rate Monotonic preemption */
        if (new_task->policy == DTESN_SCHED_POLICY_RM &&
            current_task->policy == DTESN_SCHED_POLICY_RM) {
            return (new_task->period_ns < current_task->period_ns);
        }
        
        /* Check DTESN real-time preemption */
        if (new_task->policy == DTESN_SCHED_POLICY_REALTIME) {
            uint32_t new_workload_boost = dtesn_calculate_workload_priority(new_task->workload_type);
            uint32_t current_workload_boost = dtesn_calculate_workload_priority(current_task->workload_type);
            
            uint32_t new_effective = new_task->effective_priority + new_workload_boost;
            uint32_t current_effective = current_task->effective_priority + current_workload_boost;
            
            return (new_effective < current_effective);
        }
        
        /* Check priority-based preemption */
        return (new_task->effective_priority < current_task->effective_priority);
    }
    
    /* For non-RT tasks, check time quantum expiration */
    if (current_task->policy == DTESN_SCHED_POLICY_CFS ||
        current_task->policy == DTESN_SCHED_POLICY_RR) {
        uint64_t time_slice = current_time - current_task->last_ran_ns;
        if (time_slice >= DTESN_SCHED_QUANTUM_NS) {
            return true; /* Time quantum expired */
        }
    }
    
    return false;
}

/**
 * dtesn_sched_policy_set_deadline - Set deadline for EDF tasks
 * @task: Task to set deadline for
 * @deadline_ns: Absolute deadline in nanoseconds
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_policy_set_deadline(dtesn_task_t *task, uint64_t deadline_ns)
{
    if (!task) {
        return -EINVAL;
    }
    
    pthread_mutex_lock(&task->task_lock);
    
    task->deadline_ns = deadline_ns;
    
    /* Automatically set policy to EDF if deadline is specified */
    if (deadline_ns > 0 && task->policy != DTESN_SCHED_POLICY_EDF) {
        task->policy = DTESN_SCHED_POLICY_EDF;
    }
    
    pthread_mutex_unlock(&task->task_lock);
    
    return 0;
}

/**
 * dtesn_sched_policy_set_period - Set period for Rate Monotonic tasks
 * @task: Task to set period for
 * @period_ns: Task period in nanoseconds
 * @budget_ns: Time budget per period in nanoseconds
 * 
 * Return: 0 on success, negative error code on failure
 */
int dtesn_sched_policy_set_period(dtesn_task_t *task, uint64_t period_ns, uint64_t budget_ns)
{
    if (!task || period_ns == 0 || budget_ns > period_ns) {
        return -EINVAL;
    }
    
    pthread_mutex_lock(&task->task_lock);
    
    task->period_ns = period_ns;
    task->budget_ns = budget_ns;
    task->runtime_ns = 0; /* Reset current period runtime */
    
    /* Calculate deadline based on period */
    uint64_t current_time = dtesn_get_time_ns();
    uint64_t next_period = ((current_time / period_ns) + 1) * period_ns;
    task->deadline_ns = next_period;
    
    /* Automatically set policy to Rate Monotonic */
    task->policy = DTESN_SCHED_POLICY_RM;
    
    pthread_mutex_unlock(&task->task_lock);
    
    return 0;
}

/**
 * dtesn_sched_policy_get_time_slice - Calculate time slice for task
 * @task: Task to calculate time slice for
 * 
 * Return: Time slice in nanoseconds
 */
uint64_t dtesn_sched_policy_get_time_slice(dtesn_task_t *task)
{
    if (!task) {
        return DTESN_SCHED_QUANTUM_NS;
    }
    
    switch (task->policy) {
        case DTESN_SCHED_POLICY_REALTIME:
            /* DTESN real-time tasks get larger time slices for efficiency */
            if (task->workload_type == DTESN_WORKLOAD_MEMBRANE) {
                return DTESN_SCHED_QUANTUM_NS * 2; /* 2ms for membrane computing */
            } else if (task->workload_type == DTESN_WORKLOAD_ESN) {
                return DTESN_SCHED_QUANTUM_NS * 1.5; /* 1.5ms for ESN */
            }
            return DTESN_SCHED_QUANTUM_NS;
            
        case DTESN_SCHED_POLICY_EDF:
            /* EDF tasks get time slice based on deadline urgency */
            if (task->deadline_ns > 0) {
                uint64_t current_time = dtesn_get_time_ns();
                uint64_t time_to_deadline = (task->deadline_ns > current_time) ?
                    (task->deadline_ns - current_time) : 0;
                
                if (time_to_deadline < DTESN_SCHED_QUANTUM_NS) {
                    return time_to_deadline; /* Run until deadline */
                }
            }
            return DTESN_SCHED_QUANTUM_NS;
            
        case DTESN_SCHED_POLICY_RM:
            /* Rate Monotonic tasks get budget-based time slices */
            if (task->budget_ns > 0 && task->runtime_ns < task->budget_ns) {
                uint64_t remaining_budget = task->budget_ns - task->runtime_ns;
                return (remaining_budget < DTESN_SCHED_QUANTUM_NS) ?
                    remaining_budget : DTESN_SCHED_QUANTUM_NS;
            }
            return DTESN_SCHED_QUANTUM_NS;
            
        case DTESN_SCHED_POLICY_CFS:
            /* CFS tasks get time slice based on nice value */
            if (task->nice > 0) {
                /* Lower priority - shorter time slice */
                return DTESN_SCHED_QUANTUM_NS / (1 + task->nice / 5);
            } else if (task->nice < 0) {
                /* Higher priority - longer time slice */
                return DTESN_SCHED_QUANTUM_NS * (1 + (-task->nice) / 5);
            }
            return DTESN_SCHED_QUANTUM_NS;
            
        default:
            return DTESN_SCHED_QUANTUM_NS;
    }
}