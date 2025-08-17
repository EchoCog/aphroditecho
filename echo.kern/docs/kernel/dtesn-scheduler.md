# DTESN Real-Time Scheduler

## Overview

The DTESN (Deep Tree Echo State Networks) Real-Time Scheduler is a high-performance, deterministic task scheduler designed specifically for neuromorphic computing workloads. It provides strict timing guarantees while optimizing for the unique characteristics of membrane computing, Echo State Networks, and B-Series computations.

## Architecture

### Core Components

1. **Scheduler Core** (`kernel/dtesn/scheduler.c`)
   - Main scheduling logic and task management
   - Per-CPU run queues with lock-free operations where possible
   - Performance monitoring and metrics collection

2. **Scheduling Policies** (`kernel/dtesn/sched_policy.c`)
   - DTESN_REALTIME: Custom policy optimized for neuromorphic workloads
   - EDF (Earliest Deadline First): Classic real-time scheduling
   - Rate Monotonic: Fixed-priority periodic task scheduling
   - CFS (Completely Fair Scheduler): Fair scheduling for general tasks

3. **Header Interface** (`include/dtesn/scheduler.h`)
   - Data structures and function prototypes
   - Configuration constants and performance thresholds
   - OEIS A000081 compliance definitions

## Performance Requirements

The scheduler meets strict real-time performance requirements:

| Metric | Requirement | Implementation |
|--------|-------------|----------------|
| Context Switch | ≤ 5μs | Lock-free run queues, optimized data structures |
| Scheduling Latency | ≤ 10μs | Fast policy selection, bitmap-based queue management |
| Jitter | ≤ 1μs | Deterministic algorithms, minimal variance |
| CPU Overhead | ≤ 5% | Efficient algorithms, lazy load balancing |

## DTESN Workload Types

The scheduler recognizes and optimizes for different DTESN workload types:

### 1. Membrane Computing (`DTESN_WORKLOAD_MEMBRANE`)
- **Priority**: Highest (0-9)
- **Characteristics**: Time-critical P-system operations
- **Optimizations**: 
  - Larger time slices (2ms)
  - CPU affinity to reduce migration
  - Memory zone assignment based on membrane hierarchy

### 2. Echo State Networks (`DTESN_WORKLOAD_ESN`)
- **Priority**: High (10-19)
- **Characteristics**: Reservoir state updates, vector operations
- **Optimizations**:
  - FPU and vector unit requirements
  - Consistent scheduling for state coherence
  - 1.5ms time slices

### 3. B-Series Computations (`DTESN_WORKLOAD_BSERIES`)
- **Priority**: Medium-High (20-29)
- **Characteristics**: Mathematical tree computations
- **Optimizations**:
  - FPU requirements
  - Order-based priority adjustment
  - Budget-aware scheduling

### 4. Memory Operations (`DTESN_WORKLOAD_MEMORY`)
- **Priority**: Medium (30-39)
- **Characteristics**: Memory management operations
- **Optimizations**: Standard scheduling with memory locality

### 5. I/O Operations (`DTESN_WORKLOAD_IO`)
- **Priority**: Lower (40-49)
- **Characteristics**: I/O bound operations
- **Optimizations**: Fair scheduling with I/O wait handling

### 6. General Tasks (`DTESN_WORKLOAD_GENERAL`)
- **Priority**: Lowest (50+)
- **Characteristics**: Non-DTESN workloads
- **Optimizations**: Standard CFS scheduling

## Scheduling Policies

### DTESN_REALTIME Policy

Custom real-time policy optimized for DTESN workloads:

```c
// Priority calculation
effective_priority = base_priority + workload_boost + deadline_boost + membrane_boost
```

**Features:**
- Workload-aware priority boosting
- Membrane hierarchy consideration
- Deadline urgency handling
- Vector operation affinity

### EDF (Earliest Deadline First)

Classic deadline-driven scheduling:

```c
// Task selection
selected_task = task_with_earliest_deadline()
```

**Features:**
- Optimal for deadline-sensitive tasks
- Dynamic priority based on deadline proximity
- Missed deadline tracking and reporting

### Rate Monotonic

Fixed-priority scheduling based on task periods:

```c
// Priority assignment
priority = inverse(task_period)
```

**Features:**
- Predictable behavior for periodic tasks
- Budget enforcement per period
- Utilization-based admission control

### CFS (Completely Fair Scheduler)

Fair scheduling for general-purpose tasks:

```c
// Virtual runtime calculation
vruntime = actual_runtime * nice_weight
```

**Features:**
- Fair CPU time distribution
- Nice value support (-20 to +19)
- Interactive task boosting

## Priority Inheritance

The scheduler implements a priority inheritance protocol to prevent priority inversion:

```c
int dtesn_priority_inherit(dtesn_task_t *blocked_task, dtesn_task_t *blocking_task)
{
    if (blocked_task->priority < blocking_task->priority) {
        blocking_task->effective_priority = blocked_task->priority;
        blocking_task->pi_state = DTESN_PI_STATE_INHERITED;
    }
}
```

**Features:**
- Automatic priority boosting
- Deadlock detection (boost limit)
- Chain inheritance support
- Original priority restoration

## Load Balancing

Multi-core load balancing optimizes system utilization:

### Load Metrics
- **Load Weight**: Based on workload type and task count
- **Balance Interval**: 10ms default (configurable)
- **Migration Threshold**: Minimum load difference for migration

### Migration Strategy
1. Identify most and least loaded CPUs
2. Select migratable tasks (respecting CPU affinity)
3. Prefer non-membrane tasks for migration
4. Limit migrations per balance cycle (max 2)

```c
// Load weight calculation by workload type
switch (workload_type) {
    case DTESN_WORKLOAD_MEMBRANE: weight = 100; break;
    case DTESN_WORKLOAD_ESN:      weight = 80;  break;
    case DTESN_WORKLOAD_BSERIES:  weight = 60;  break;
    default:                      weight = 20;  break;
}
```

## OEIS A000081 Compliance

The scheduler maintains compliance with OEIS A000081 (rooted tree enumeration):

### Sequence Values
```
A000081: 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, ...
```

### Implementation
- **Memory Zones**: Organized according to OEIS hierarchy
- **Task Placement**: Memory zone assignment based on workload depth
- **Validation**: Optional compliance checking for data structures

```c
bool dtesn_sched_validate_oeis(void *structure_data, uint32_t depth)
{
    if (depth >= DTESN_SCHED_A000081_MAX_DEPTH) {
        return true; // Skip validation for large depths
    }
    
    uint32_t expected_count = oeis_sequence[depth];
    // Validate structure follows expected enumeration
    return validate_structure_count(structure_data, expected_count);
}
```

## Performance Monitoring

### Metrics Collected

#### Per-CPU Metrics
- Context switches count
- Scheduling latency (min/avg/max)
- Jitter measurement
- Missed deadlines count
- CPU utilization

#### Global Metrics
- Total context switches
- System-wide latency statistics
- Load balancing efficiency
- Policy distribution

### Usage Example

```c
// Get global performance metrics
dtesn_sched_perf_t *global_perf = dtesn_sched_get_performance(-1);
printf("Average latency: %.2f μs\n", global_perf->scheduling_latency_ns / 1000.0);

// Get per-CPU metrics
dtesn_sched_perf_t *cpu_perf = dtesn_sched_get_performance(0);
printf("CPU 0 context switches: %lu\n", cpu_perf->context_switches);
```

## API Reference

### Initialization

```c
// Initialize scheduler with specified CPU count
int dtesn_sched_init(uint32_t nr_cpus);

// Cleanup all scheduler resources
int dtesn_sched_cleanup(void);
```

### Task Management

```c
// Create new DTESN task
dtesn_task_t *dtesn_task_create(uint32_t pid, 
                                dtesn_workload_type_t workload_type,
                                dtesn_sched_policy_t policy, 
                                uint32_t priority);

// Destroy task and free resources
int dtesn_task_destroy(dtesn_task_t *task);

// Set scheduling policy and priority
int dtesn_sched_set_policy(dtesn_task_t *task, 
                           dtesn_sched_policy_t policy, 
                           uint32_t priority);
```

### Scheduling Operations

```c
// Schedule next task on specified CPU
dtesn_task_t *dtesn_task_schedule(uint32_t cpu_id);

// Check task deadline compliance
bool dtesn_deadline_check(dtesn_task_t *task, uint64_t current_time_ns);

// Trigger load balancing
int dtesn_load_balance(uint32_t trigger_cpu);

// Handle priority inheritance
int dtesn_priority_inherit(dtesn_task_t *blocked_task, 
                           dtesn_task_t *blocking_task);
```

### Performance Monitoring

```c
// Get performance metrics (cpu_id = -1 for global)
dtesn_sched_perf_t *dtesn_sched_get_performance(int cpu_id);

// Validate OEIS A000081 compliance
bool dtesn_sched_validate_oeis(void *structure_data, uint32_t depth);
```

## Configuration

### Compile-Time Constants

```c
#define DTESN_SCHED_MAX_TASKS           4096    // Maximum tasks
#define DTESN_SCHED_MAX_CPUS            64      // Maximum CPUs
#define DTESN_SCHED_MAX_PRIORITIES      256     // Priority levels
#define DTESN_SCHED_QUANTUM_NS          1000000 // 1ms quantum

// Performance thresholds
#define DTESN_SCHED_CONTEXT_SWITCH_THRESHOLD_US    5
#define DTESN_SCHED_LATENCY_THRESHOLD_US          10
#define DTESN_SCHED_JITTER_THRESHOLD_US            1
#define DTESN_SCHED_CPU_OVERHEAD_THRESHOLD_PCT     5
```

### Runtime Configuration

```c
// Enable/disable load balancing
scheduler.load_balancing_enabled = true;

// Set load balance interval (nanoseconds)
scheduler.balance_interval_ns = 10000000; // 10ms

// Set migration threshold
scheduler.migration_threshold = 4;

// Enable/disable priority inheritance
scheduler.priority_inheritance_enabled = true;

// Set PI boost limit
scheduler.pi_boost_limit = 3;

// Enable/disable OEIS validation
scheduler.oeis_validation_enabled = true;
```

## Integration Example

### Creating and Scheduling DTESN Tasks

```c
#include <dtesn/scheduler.h>

int main() {
    // Initialize scheduler for 4 CPUs
    if (dtesn_sched_init(4) != 0) {
        fprintf(stderr, "Failed to initialize DTESN scheduler\n");
        return -1;
    }
    
    // Create membrane computing task
    dtesn_task_t *membrane_task = dtesn_task_create(
        1001,                           // PID
        DTESN_WORKLOAD_MEMBRANE,       // Workload type
        DTESN_SCHED_POLICY_REALTIME,   // Policy
        5                              // Priority
    );
    
    // Create ESN task with deadline
    dtesn_task_t *esn_task = dtesn_task_create(
        1002,
        DTESN_WORKLOAD_ESN,
        DTESN_SCHED_POLICY_EDF,
        10
    );
    
    // Set 10ms deadline for ESN task
    uint64_t current_time = get_current_time_ns();
    esn_task->deadline_ns = current_time + 10000000;
    
    // Schedule tasks
    for (int i = 0; i < 100; i++) {
        for (uint32_t cpu = 0; cpu < 4; cpu++) {
            dtesn_task_t *scheduled = dtesn_task_schedule(cpu);
            if (scheduled) {
                // Task selected for execution
                printf("CPU %u: Running task %u (workload: %d)\n",
                       cpu, scheduled->task_id, scheduled->workload_type);
            }
        }
        
        // Periodic load balancing
        if (i % 10 == 0) {
            dtesn_load_balance(0);
        }
        
        usleep(1000); // 1ms delay
    }
    
    // Get performance statistics
    dtesn_sched_perf_t *perf = dtesn_sched_get_performance(-1);
    printf("Context switches: %lu\n", perf->context_switches);
    printf("Average latency: %.2f μs\n", perf->scheduling_latency_ns / 1000.0);
    printf("Jitter: %.2f μs\n", perf->jitter_ns / 1000.0);
    
    // Cleanup
    dtesn_task_destroy(membrane_task);
    dtesn_task_destroy(esn_task);
    dtesn_sched_cleanup();
    
    return 0;
}
```

## Testing

The scheduler includes comprehensive test suite (`tests/kernel/test_scheduler.c`):

### Test Categories

1. **Initialization Tests**: Scheduler setup and configuration
2. **Task Management Tests**: Creation, destruction, and attributes
3. **Scheduling Tests**: Policy selection and task ordering
4. **Deadline Tests**: EDF and Rate Monotonic deadline handling
5. **Load Balancing Tests**: Multi-core load distribution
6. **Priority Inheritance Tests**: Priority inversion prevention
7. **Performance Tests**: Latency, jitter, and overhead measurement
8. **OEIS Compliance Tests**: Mathematical correctness validation
9. **Stress Tests**: High-load performance validation
10. **Integration Tests**: DTESN component interaction

### Running Tests

```bash
# Compile and run scheduler tests
cd /path/to/echo.kern
make test-scheduler

# Or run directly
gcc -I include tests/kernel/test_scheduler.c kernel/dtesn/scheduler.c kernel/dtesn/sched_policy.c -o test_scheduler -lpthread
./test_scheduler
```

### Expected Results

```
DTESN Real-Time Scheduler Test Suite
====================================

=== Scheduler Initialization Tests ===
✅ Scheduler initialization with valid CPU count
✅ Scheduler initialization with zero CPUs (should fail)
...

Test Summary:
=============
Total tests: 45
Passed: 45
Failed: 0
Success rate: 100.0%
🎉 All tests passed!
```

## Performance Optimization

### Lock-Free Optimizations
- Atomic operations for counters
- RCU for read-heavy data structures
- Per-CPU data to minimize cache bouncing

### Cache Optimization
- Data structure alignment
- Hot/cold data separation
- NUMA-aware task placement

### Real-Time Optimizations
- Preemption-safe critical sections
- Bounded execution time algorithms
- Priority inheritance for lock holders

## Troubleshooting

### Common Issues

1. **High Scheduling Latency**
   - Check CPU utilization
   - Verify lock contention
   - Review task priorities

2. **Missed Deadlines**
   - Analyze workload characteristics
   - Adjust task priorities
   - Consider task migration

3. **Load Imbalance**
   - Check CPU affinity settings
   - Verify migration thresholds
   - Review workload distribution

### Debug Information

```c
// Enable verbose debugging
#define DTESN_SCHED_DEBUG 1

// Monitor specific CPU
dtesn_sched_perf_t *perf = dtesn_sched_get_performance(cpu_id);
// Check metrics...
```

## Future Enhancements

1. **Hardware Acceleration**: Integration with neuromorphic processors
2. **Energy Management**: Power-aware scheduling policies
3. **Thermal Management**: Temperature-based task migration
4. **Security**: Isolation and secure scheduling
5. **Machine Learning**: Adaptive policy selection

## References

1. OEIS A000081: Number of rooted trees with n nodes
2. Liu, C.L. and Layland, J.W. "Scheduling algorithms for multiprogramming in a hard-real-time environment"
3. Buttazzo, G.C. "Hard Real-Time Computing Systems"
4. Love, R. "Linux Kernel Development"
5. DTESN Echo.Kern Architecture Specification