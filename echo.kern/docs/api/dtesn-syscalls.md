# DTESN System Call Interface API Documentation

## Overview

The DTESN (Deep Tree Echo State Networks) system call interface provides comprehensive access to neuromorphic computing primitives at the kernel level. This API enables user-space applications to create, manage, and operate DTESN instances with real-time performance guarantees.

## Performance Targets

| Operation | Target | Rationale |
|-----------|--------|-----------|
| Syscall overhead | ≤ 100ns | Minimal kernel entry/exit cost |
| Parameter validation | ≤ 50ns | Fast input validation |
| Data copy bandwidth | ≥ 8GB/s | High-throughput data transfer |
| Error path latency | ≤ 200ns | Quick error handling |

## OEIS A000081 Compliance

All DTESN operations maintain compliance with the OEIS A000081 sequence (unlabeled rooted trees): `1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, ...`

This mathematical foundation ensures correct topology for membrane hierarchies and B-series tree structures.

## System Calls

### sys_dtesn_create

Creates a new DTESN instance with specified parameters.

**Prototype:**
```c
long sys_dtesn_create(const struct dtesn_create_params *params);
```

**Parameters:**
- `params`: Pointer to creation parameters structure

**Returns:**
- File descriptor on success
- Negative error code on failure

**Usage Example:**
```c
#include <dtesn.h>

struct dtesn_create_params params = {
    .depth = 4,
    .max_order = 5,
    .neuron_count = 100,
    .membrane_count = 9,    // OEIS A000081[4] = 9
    .input_dim = 10,
    .output_dim = 5,
    .flags = DTESN_CREATE_VALIDATE_OEIS,
};
strcpy(params.label, "my_dtesn_instance");

int fd = syscall(__NR_sys_dtesn_create, &params);
if (fd < 0) {
    perror("Failed to create DTESN instance");
    return -1;
}
```

**Error Codes:**
- `DTESN_ERROR_INVALID_DEPTH`: Invalid tree depth
- `DTESN_ERROR_INVALID_ORDER`: Invalid B-series order
- `DTESN_ERROR_OEIS_VIOLATION`: Violates OEIS A000081 constraints
- `-EINVAL`: Invalid parameters
- `-ENOMEM`: Insufficient memory
- `-ENFILE`: Too many instances

### sys_dtesn_evolve

Evolves a DTESN instance through multiple computation steps.

**Prototype:**
```c
long sys_dtesn_evolve(const struct dtesn_evolve_params *params);
```

**Parameters:**
- `params`: Pointer to evolution parameters

**Returns:**
- Number of evolution steps completed
- Negative error code on failure

**Usage Example:**
```c
float input_vector[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

struct dtesn_evolve_params evolve_params = {
    .fd = dtesn_fd,
    .input = input_vector,
    .input_size = 5,
    .steps = 100,
    .mode = DTESN_EVOLVE_SYNCHRONOUS,
    .timeout_ns = 1000000000ULL,  // 1 second timeout
};

int steps_completed = syscall(__NR_sys_dtesn_evolve, &evolve_params);
if (steps_completed < 0) {
    fprintf(stderr, "Evolution failed: %s\n", strerror(-steps_completed));
    return -1;
}

printf("Completed %d evolution steps\n", steps_completed);
```

**Evolution Modes:**
- `DTESN_EVOLVE_SYNCHRONOUS`: Synchronous step-by-step evolution
- `DTESN_EVOLVE_ASYNCHRONOUS`: Asynchronous background evolution
- `DTESN_EVOLVE_CONTINUOUS`: Continuous evolution mode
- `DTESN_EVOLVE_STEP_BY_STEP`: Single-step debugging mode

### sys_dtesn_get_state

Retrieves current state information from a DTESN instance.

**Prototype:**
```c
long sys_dtesn_get_state(int fd, struct dtesn_state_info *state);
```

**Parameters:**
- `fd`: DTESN instance file descriptor
- `state`: Pointer to state information buffer

**Returns:**
- `0` on success
- Negative error code on failure

**Usage Example:**
```c
struct dtesn_state_info state;
int ret = syscall(__NR_sys_dtesn_get_state, dtesn_fd, &state);
if (ret < 0) {
    perror("Failed to get DTESN state");
    return -1;
}

printf("DTESN State:\n");
printf("  Depth: %u\n", state.depth);
printf("  Active membranes: %u\n", state.active_membranes);
printf("  Total neurons: %u\n", state.total_neurons);
printf("  Evolution steps: %u\n", state.evolution_steps);
printf("  Spectral radius: %.3f\n", state.spectral_radius);
printf("  OEIS compliance: %s\n", state.oeis_compliance ? "Yes" : "No");
printf("  Performance violations: %u\n", state.performance_violations);
```

### sys_dtesn_destroy

Destroys a DTESN instance and releases all resources.

**Prototype:**
```c
long sys_dtesn_destroy(int fd);
```

**Parameters:**
- `fd`: DTESN instance file descriptor

**Returns:**
- `0` on success
- Negative error code on failure

**Usage Example:**
```c
int ret = syscall(__NR_sys_dtesn_destroy, dtesn_fd);
if (ret < 0) {
    perror("Failed to destroy DTESN instance");
}
```

### sys_membrane_op

Performs operations on P-system membranes within a DTESN instance.

**Prototype:**
```c
long sys_membrane_op(const struct dtesn_membrane_op_params *params);
```

**Parameters:**
- `params`: Pointer to membrane operation parameters

**Returns:**
- Operation-specific result
- Negative error code on failure

**Membrane Operations:**
- `DTESN_MEMBRANE_CREATE`: Create new membrane
- `DTESN_MEMBRANE_EVOLVE`: Evolve membrane state  
- `DTESN_MEMBRANE_COMMUNICATE`: Inter-membrane communication
- `DTESN_MEMBRANE_DISSOLVE`: Dissolve membrane
- `DTESN_MEMBRANE_DIVIDE`: Divide membrane

**Usage Example:**
```c
struct dtesn_membrane_op_params membrane_params = {
    .fd = dtesn_fd,
    .operation = DTESN_MEMBRANE_CREATE,
    .parent_id = 1,             // Parent membrane ID
    .steps = 0,                 // Not used for creation
    .data = NULL,               // No additional data
    .data_size = 0,
};

int new_membrane_id = syscall(__NR_sys_membrane_op, &membrane_params);
if (new_membrane_id < 0) {
    fprintf(stderr, "Membrane creation failed: %s\n", strerror(-new_membrane_id));
    return -1;
}

printf("Created membrane with ID: %d\n", new_membrane_id);
```

### sys_bseries_compute

Performs B-series tree computations for differential equations.

**Prototype:**
```c
long sys_bseries_compute(const struct dtesn_bseries_params *params);
```

**Parameters:**
- `params`: Pointer to B-series computation parameters

**Returns:**
- Number of trees computed
- Negative error code on failure

**Usage Example:**
```c
double coefficients[] = {1.0, 0.5, 0.25, 0.125};
double results[100];

struct dtesn_bseries_params bseries_params = {
    .fd = dtesn_fd,
    .order = 4,
    .coefficients = coefficients,
    .coeff_count = 4,
    .result = results,
    .result_size = 100,
    .tree_count = 10,
};

int trees_computed = syscall(__NR_sys_bseries_compute, &bseries_params);
if (trees_computed < 0) {
    fprintf(stderr, "B-series computation failed: %s\n", strerror(-trees_computed));
    return -1;
}

printf("Computed %d B-series trees\n", trees_computed);
```

### sys_esn_update

Updates Echo State Network reservoir state.

**Prototype:**
```c
long sys_esn_update(const struct dtesn_esn_params *params);
```

**Parameters:**
- `params`: Pointer to ESN update parameters

**Returns:**
- `0` on success
- Negative error code on failure

**Usage Example:**
```c
float input[] = {1.0f, 2.0f, 3.0f};
float state[100];
float output[5];

struct dtesn_esn_params esn_params = {
    .fd = dtesn_fd,
    .input = input,
    .input_size = 3,
    .state = state,
    .state_size = 100,
    .output = output,
    .output_size = 5,
    .leak_rate = 0.1f,
    .spectral_radius = 0.9f,
};

int ret = syscall(__NR_sys_esn_update, &esn_params);
if (ret < 0) {
    fprintf(stderr, "ESN update failed: %s\n", strerror(-ret));
    return -1;
}

printf("ESN state updated successfully\n");
```

## Data Structures

### struct dtesn_create_params

Parameters for DTESN instance creation.

```c
struct dtesn_create_params {
    __u32 depth;                    // Tree depth (1-16)
    __u32 max_order;                // Maximum B-series order (1-10)
    __u32 neuron_count;             // ESN reservoir neurons
    __u32 membrane_count;           // P-system membranes
    __u32 input_dim;                // Input dimension
    __u32 output_dim;               // Output dimension
    __u32 flags;                    // Creation flags
    char label[DTESN_MAX_LABEL_LEN]; // Human-readable label
};
```

### struct dtesn_state_info

Current state information for a DTESN instance.

```c
struct dtesn_state_info {
    __u32 depth;                    // Current tree depth
    __u32 active_membranes;         // Active membrane count
    __u32 total_neurons;            // Total ESN neurons
    __u32 evolution_steps;          // Total evolution steps
    __u64 creation_time_ns;         // Instance creation time
    __u64 last_update_ns;           // Last state update time
    double spectral_radius;         // Current ESN spectral radius
    double membrane_activity;       // Membrane activity level
    __u32 oeis_compliance;          // OEIS A000081 compliance flag
    __u32 performance_violations;   // Performance constraint violations
};
```

## Error Handling

### DTESN-Specific Error Codes

| Code | Value | Description |
|------|-------|-------------|
| `DTESN_ERROR_INVALID_DEPTH` | -1001 | Invalid tree depth |
| `DTESN_ERROR_INVALID_ORDER` | -1002 | Invalid B-series order |
| `DTESN_ERROR_OEIS_VIOLATION` | -1003 | OEIS A000081 violation |
| `DTESN_ERROR_PERFORMANCE` | -1004 | Performance target missed |
| `DTESN_ERROR_HARDWARE` | -1005 | Hardware acceleration error |
| `DTESN_ERROR_MEMBRANE` | -1006 | Membrane operation error |
| `DTESN_ERROR_ESN` | -1007 | ESN operation error |
| `DTESN_ERROR_BSERIES` | -1008 | B-series computation error |

### Standard Linux Error Codes

Common standard error codes:
- `-EINVAL`: Invalid argument
- `-EFAULT`: Bad address (user pointer)
- `-ENOMEM`: Out of memory
- `-EBADF`: Bad file descriptor
- `-ENOSYS`: Function not implemented
- `-ENODEV`: No such device

## Performance Monitoring

### IOCTL Interface

Advanced operations using `ioctl()`:

```c
#include <sys/ioctl.h>

// Get performance metrics
struct dtesn_performance_metrics metrics;
int ret = ioctl(dtesn_fd, DTESN_IOC_GET_METRICS, &metrics);

// Enable debug mode
__u32 debug_level = 2;
ioctl(dtesn_fd, DTESN_IOC_SET_DEBUG, &debug_level);

// Validate OEIS compliance
ioctl(dtesn_fd, DTESN_IOC_VALIDATE_OEIS);

// Reset statistics
ioctl(dtesn_fd, DTESN_IOC_RESET_STATS);

// Get API version
__u32 version;
ioctl(dtesn_fd, DTESN_IOC_GET_VERSION, &version);
```

### Performance Metrics

```c
struct dtesn_performance_metrics {
    __u64 syscall_overhead_ns;      // Average syscall overhead
    __u64 validation_time_ns;       // Parameter validation time
    __u64 copy_bandwidth_bps;       // Data copy bandwidth
    __u64 error_path_time_ns;       // Error handling time
    __u64 evolution_time_ns;        // Average evolution time
    __u64 membrane_op_time_ns;      // Average membrane operation time
    __u64 bseries_comp_time_ns;     // Average B-series computation time
    __u64 esn_update_time_ns;       // Average ESN update time
    __u32 cache_hits;               // Cache hit count
    __u32 cache_misses;             // Cache miss count
    __u32 hw_accelerations;         // Hardware acceleration usage
};
```

## Best Practices

### 1. Instance Lifecycle Management

```c
// Create instance
int dtesn_fd = create_dtesn_instance(...);
if (dtesn_fd < 0) {
    handle_error();
    return -1;
}

// Use instance for computations
perform_dtesn_operations(dtesn_fd);

// Always destroy when finished
if (syscall(__NR_sys_dtesn_destroy, dtesn_fd) < 0) {
    log_warning("Failed to destroy DTESN instance");
}
```

### 2. Error Handling

```c
int result = syscall(__NR_sys_dtesn_evolve, &params);
if (result < 0) {
    switch (result) {
        case DTESN_ERROR_OEIS_VIOLATION:
            fprintf(stderr, "OEIS A000081 violation\n");
            break;
        case DTESN_ERROR_PERFORMANCE:
            fprintf(stderr, "Performance target missed\n");
            break;
        case -EINVAL:
            fprintf(stderr, "Invalid parameters\n");
            break;
        default:
            fprintf(stderr, "Unexpected error: %s\n", strerror(-result));
    }
    return -1;
}
```

### 3. Performance Monitoring

```c
// Monitor performance violations
struct dtesn_state_info state;
syscall(__NR_sys_dtesn_get_state, dtesn_fd, &state);

if (state.performance_violations > 0) {
    printf("Warning: %u performance violations detected\n", 
           state.performance_violations);
    
    // Consider adjusting parameters or system load
}
```

### 4. OEIS Compliance

```c
// Ensure membrane count follows OEIS A000081
const uint32_t oeis_a000081[] = {0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719};

struct dtesn_create_params params = {
    .depth = 5,
    .membrane_count = oeis_a000081[5], // Use exact OEIS value: 9
    .flags = DTESN_CREATE_VALIDATE_OEIS,
    // ... other parameters
};
```

## Integration Examples

### Complete Application Example

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <dtesn.h>

int main() {
    // Create DTESN instance
    struct dtesn_create_params create_params = {
        .depth = 4,
        .max_order = 5,
        .neuron_count = 100,
        .membrane_count = 9,        // OEIS A000081[4]
        .input_dim = 10,
        .output_dim = 5,
        .flags = DTESN_CREATE_VALIDATE_OEIS | DTESN_CREATE_REAL_TIME,
    };
    strcpy(create_params.label, "example_dtesn");
    
    int dtesn_fd = syscall(__NR_sys_dtesn_create, &create_params);
    if (dtesn_fd < 0) {
        fprintf(stderr, "Failed to create DTESN instance: %s\n", 
                strerror(-dtesn_fd));
        return 1;
    }
    
    // Prepare input data
    float input_data[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 
                         6.0f, 7.0f, 8.0f, 9.0f, 10.0f};
    
    // Evolve system
    struct dtesn_evolve_params evolve_params = {
        .fd = dtesn_fd,
        .input = input_data,
        .input_size = 10,
        .steps = 100,
        .mode = DTESN_EVOLVE_SYNCHRONOUS,
        .timeout_ns = 10000000000ULL,  // 10 second timeout
    };
    
    int steps = syscall(__NR_sys_dtesn_evolve, &evolve_params);
    if (steps < 0) {
        fprintf(stderr, "Evolution failed: %s\n", strerror(-steps));
        goto cleanup;
    }
    
    printf("Evolution completed: %d steps\n", steps);
    
    // Get final state
    struct dtesn_state_info state;
    if (syscall(__NR_sys_dtesn_get_state, dtesn_fd, &state) == 0) {
        printf("Final state:\n");
        printf("  Active membranes: %u\n", state.active_membranes);
        printf("  Evolution steps: %u\n", state.evolution_steps);
        printf("  Spectral radius: %.3f\n", state.spectral_radius);
        printf("  OEIS compliant: %s\n", state.oeis_compliance ? "Yes" : "No");
    }
    
cleanup:
    // Clean up
    syscall(__NR_sys_dtesn_destroy, dtesn_fd);
    return 0;
}
```

## Compilation

To compile applications using the DTESN API:

```bash
gcc -o example example.c -I/usr/include/dtesn
```

## Version Information

- **API Version**: 1.0.0
- **Kernel Module**: echo.kern
- **Compatible Architectures**: x86_64, ARM64
- **Performance Requirements**: Real-time neuromorphic computing

For more information, see the [Echo.Kern Implementation Specification](../Echo-Kernel%20Implementation%20Specification.md).