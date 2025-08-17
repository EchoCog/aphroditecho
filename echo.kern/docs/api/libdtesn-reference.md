# libdtesn API Reference

## Overview

The libdtesn user-space library provides comprehensive APIs for Deep Tree Echo State Networks (DTESN) application development. This library wraps kernel system calls with user-friendly interfaces, error handling, and performance optimization.

## Version Information

- **Version**: 1.0.0
- **API Compatibility**: DTESN Kernel 1.0
- **OEIS Compliance**: A000081 (unlabeled rooted trees)
- **Performance Target**: ≤ 1μs API call overhead

## Library Initialization

### Core Functions

#### `int dtesn_init(const dtesn_lib_config_t *config)`

Initialize the DTESN user-space library.

**Parameters:**
- `config`: Library configuration parameters (NULL for defaults)

**Returns:** 0 on success, negative error code on failure

**Example:**
```c
dtesn_lib_config_t config = {
    .max_instances = 1000,
    .async_queue_size = 256,
    .worker_threads = 4,
    .flags = 0
};

int result = dtesn_init(&config);
if (result != 0) {
    fprintf(stderr, "Failed to initialize: %s\n", dtesn_strerror(result));
}
```

#### `int dtesn_cleanup(void)`

Cleanup and shutdown the DTESN library.

**Returns:** 0 on success, negative error code on failure

#### `const char *dtesn_get_version(int *major, int *minor, int *patch)`

Get library version information.

**Parameters:**
- `major`: Pointer to store major version number
- `minor`: Pointer to store minor version number  
- `patch`: Pointer to store patch version number

**Returns:** Version string

## Instance Management

### `int dtesn_create(const struct dtesn_create_params *params, dtesn_handle_t **handle)`

Create a new DTESN instance.

**Parameters:**
- `params`: Instance creation parameters
- `handle`: Pointer to store instance handle

**Returns:** 0 on success, negative error code on failure

**Example:**
```c
struct dtesn_create_params params = {
    .depth = 4,
    .max_order = 5,
    .neuron_count = 100,
    .membrane_count = 9,        // OEIS A000081[4] = 9
    .input_dim = 10,
    .output_dim = 5,
    .flags = DTESN_CREATE_VALIDATE_OEIS | DTESN_CREATE_REAL_TIME
};
strcpy(params.label, "my_dtesn_instance");

dtesn_handle_t *handle;
int result = dtesn_create(&params, &handle);
```

### `int dtesn_destroy(dtesn_handle_t *handle)`

Destroy a DTESN instance and free resources.

**Parameters:**
- `handle`: Instance handle to destroy

**Returns:** 0 on success, negative error code on failure

### `int dtesn_evolve(dtesn_handle_t *handle, const float *input, uint32_t input_size, uint32_t steps, uint32_t mode)`

Evolve DTESN instance state.

**Parameters:**
- `handle`: Instance handle
- `input`: Input vector
- `input_size`: Input vector size
- `steps`: Number of evolution steps
- `mode`: Evolution mode flags

**Returns:** 0 on success, negative error code on failure

**Evolution Modes:**
- `DTESN_EVOLVE_SYNCHRONOUS`: Synchronous evolution (default)
- `DTESN_EVOLVE_ASYNCHRONOUS`: Asynchronous evolution
- `DTESN_EVOLVE_CONTINUOUS`: Continuous evolution mode
- `DTESN_EVOLVE_STEP_BY_STEP`: Single-step evolution

## P-System Membrane Operations

### `int dtesn_membrane_create(dtesn_handle_t *handle, uint32_t parent_id, uint32_t *membrane_id)`

Create a new P-system membrane.

**Parameters:**
- `handle`: Instance handle
- `parent_id`: Parent membrane ID (0 for root)
- `membrane_id`: Pointer to store new membrane ID

**Returns:** 0 on success, negative error code on failure

### `int dtesn_membrane_evolve(dtesn_handle_t *handle, uint32_t membrane_id, uint32_t steps, const void *data, uint32_t data_size)`

Evolve P-system membrane state.

**Parameters:**
- `handle`: Instance handle
- `membrane_id`: Target membrane ID
- `steps`: Number of evolution steps
- `data`: Evolution data buffer
- `data_size`: Data buffer size

**Returns:** 0 on success, negative error code on failure

### `int dtesn_membrane_communicate(dtesn_handle_t *handle, uint32_t source_id, uint32_t target_id, const void *message, uint32_t message_size)`

Facilitate communication between two membranes.

**Parameters:**
- `handle`: Instance handle
- `source_id`: Source membrane ID
- `target_id`: Target membrane ID
- `message`: Message data
- `message_size`: Message size

**Returns:** 0 on success, negative error code on failure

## B-Series Computation Interface

### `int dtesn_bseries_compute(dtesn_handle_t *handle, uint32_t order, const double *coefficients, uint32_t coeff_count, double *result, uint32_t result_size)`

Compute B-series coefficients for rooted trees.

**Parameters:**
- `handle`: Instance handle
- `order`: Computation order (1-10)
- `coefficients`: Input coefficients array
- `coeff_count`: Number of coefficients
- `result`: Output buffer for results
- `result_size`: Output buffer size

**Returns:** 0 on success, negative error code on failure

**Example:**
```c
uint32_t order = 4;
double coefficients[] = {1.0, 0.5, 0.25, 0.125};
uint32_t tree_count;

// Get expected tree count
dtesn_bseries_get_tree_count(order, &tree_count);

double *results = malloc(tree_count * sizeof(double));
int result = dtesn_bseries_compute(handle, order, coefficients, 4, results, tree_count);
```

### `int dtesn_bseries_validate_oeis(dtesn_handle_t *handle, uint32_t order, bool *is_compliant)`

Validate OEIS A000081 compliance.

**Parameters:**
- `handle`: Instance handle
- `order`: Order to validate
- `is_compliant`: Pointer to store compliance result

**Returns:** 0 on success, negative error code on failure

## ESN Reservoir Management

### `int dtesn_esn_update(dtesn_handle_t *handle, const float *input, uint32_t input_size, float *state, uint32_t state_size)`

Update ESN reservoir state with new input.

**Parameters:**
- `handle`: Instance handle
- `input`: Input vector
- `input_size`: Input vector size
- `state`: Current state vector (modified)
- `state_size`: State vector size

**Returns:** 0 on success, negative error code on failure

### `int dtesn_esn_train(dtesn_handle_t *handle, const float *input_data, const float *target_data, uint32_t samples, uint32_t input_dim, uint32_t output_dim)`

Train ESN output weights using ridge regression.

**Parameters:**
- `handle`: Instance handle
- `input_data`: Training input data matrix
- `target_data`: Training target data matrix
- `samples`: Number of training samples
- `input_dim`: Input dimension
- `output_dim`: Output dimension

**Returns:** 0 on success, negative error code on failure

### `int dtesn_esn_predict(dtesn_handle_t *handle, const float *input, uint32_t input_size, float *output, uint32_t output_size)`

Generate predictions using the trained ESN.

**Parameters:**
- `handle`: Instance handle
- `input`: Input vector
- `input_size`: Input vector size
- `output`: Output buffer
- `output_size`: Output buffer size

**Returns:** 0 on success, negative error code on failure

## Performance Monitoring

### `int dtesn_get_performance_stats(dtesn_handle_t *handle, dtesn_perf_stats_t *stats)`

Get performance statistics.

**Parameters:**
- `handle`: Instance handle (NULL for global stats)
- `stats`: Structure to store performance statistics

**Returns:** 0 on success, negative error code on failure

**Performance Statistics:**
```c
typedef struct {
    uint64_t total_api_calls;           /* Total API calls made */
    uint64_t total_execution_time_ns;   /* Total execution time */
    uint64_t avg_call_overhead_ns;      /* Average call overhead */
    uint64_t min_call_time_ns;          /* Minimum call time */
    uint64_t max_call_time_ns;          /* Maximum call time */
    uint32_t active_instances;          /* Currently active instances */
    uint32_t failed_calls;              /* Number of failed calls */
    uint64_t memory_usage_bytes;        /* Current memory usage */
} dtesn_perf_stats_t;
```

## Error Handling

### `const char *dtesn_strerror(int error)`

Get human-readable error message for error code.

### `int dtesn_get_last_error(void)`

Get last error code for current thread.

### Error Codes

- `DTESN_SUCCESS` (0): Operation successful
- `DTESN_ERROR_INVALID_DEPTH` (-1001): Invalid tree depth
- `DTESN_ERROR_INVALID_ORDER` (-1002): Invalid B-series order
- `DTESN_ERROR_OEIS_VIOLATION` (-1003): OEIS A000081 violation
- `DTESN_ERROR_PERFORMANCE` (-1004): Performance target missed
- `DTESN_ERROR_HARDWARE` (-1005): Hardware acceleration error
- `DTESN_ERROR_MEMBRANE` (-1006): Membrane operation error
- `DTESN_ERROR_ESN` (-1007): ESN operation error
- `DTESN_ERROR_BSERIES` (-1008): B-series computation error

## Constants and Limits

### Configuration Constants

- `DTESN_MAX_DEPTH`: 16 (Maximum tree depth)
- `DTESN_MAX_ORDER`: 10 (Maximum B-series order)
- `DTESN_MAX_NEURONS`: 10000 (Maximum ESN neurons)
- `DTESN_MAX_MEMBRANES`: 1024 (Maximum P-system membranes)
- `DTESN_MAX_INPUT_SIZE`: 1000 (Maximum input dimension)
- `DTESN_MAX_OUTPUT_SIZE`: 1000 (Maximum output dimension)

### Creation Flags

- `DTESN_CREATE_DEFAULT`: Default configuration
- `DTESN_CREATE_HARDWARE_ACCEL`: Enable hardware acceleration
- `DTESN_CREATE_HIGH_PRECISION`: Use double precision floats
- `DTESN_CREATE_SPARSE_MODE`: Optimize for sparse operations
- `DTESN_CREATE_REAL_TIME`: Enable real-time constraints
- `DTESN_CREATE_VALIDATE_OEIS`: Validate OEIS A000081 compliance

## OEIS A000081 Compliance

The library enforces strict compliance with OEIS sequence A000081 (unlabeled rooted trees):
- **Sequence**: 0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, ...
- **Validation**: Automatic when `DTESN_CREATE_VALIDATE_OEIS` flag is used
- **Membrane Count**: Must match sequence value for given depth

## Building and Linking

### Static Library
```bash
make libdtesn-static
gcc myapp.c -Llib/libdtesn -ldtesn -lm -lpthread -o myapp
```

### Shared Library
```bash
make libdtesn-shared
gcc myapp.c -Lbuild/lib -ldtesn -lm -lpthread -o myapp
```

### Example Application
```bash
make examples
./build/examples/hello_dtesn --verbose
```

## Language Bindings

### Python Bindings
```bash
make python-bindings
# Creates build/bindings/python/pydtesn.so
```

```python
import pydtesn

# Initialize library
pydtesn.init()

# Create DTESN instance
dtesn = pydtesn.DTESN(depth=4, neuron_count=100, membrane_count=9)

# Evolve with input
input_data = [0.1, 0.2, 0.3, 0.4, 0.5]
dtesn.evolve(input_data, steps=10)

# Get performance stats
stats = pydtesn.get_performance_stats()
print(f"Average call overhead: {stats['avg_call_overhead_ns']} ns")

# Cleanup
pydtesn.cleanup()
```

### JavaScript/WebAssembly Bindings
```bash
make js-bindings
# Creates build/bindings/js/dtesn.js and dtesn.wasm
```

```javascript
import DTESNModule from './build/bindings/js/dtesn.js';

DTESNModule().then(Module => {
    // Initialize WASM DTESN
    const result = Module.ccall('wasm_dtesn_init', 'number', [], []);
    
    // Create instance
    const instanceId = Module.ccall('wasm_dtesn_create', 'number',
        ['number', 'number', 'number', 'number', 'number', 'number', 'number', 'string'],
        [4, 5, 100, 9, 10, 5, 0, 'js_instance']);
        
    console.log('Created DTESN instance:', instanceId);
    
    // Cleanup
    Module.ccall('wasm_dtesn_cleanup', 'number', [], []);
});
```

## Performance Considerations

### Performance Targets
- API call overhead: ≤ 1μs
- Library load time: ≤ 100ms
- Memory footprint: ≤ 10MB
- Concurrent clients: ≥ 1000

### Best Practices
1. **Initialize once**: Call `dtesn_init()` once per application
2. **Reuse instances**: Avoid frequent creation/destruction of instances
3. **Monitor performance**: Use `dtesn_get_performance_stats()` regularly
4. **Validate OEIS compliance**: Enable validation during development
5. **Use appropriate evolution modes**: Choose synchronous/asynchronous based on needs

## Thread Safety

- Library initialization/cleanup: **Not thread-safe**
- Instance operations: **Thread-safe** per instance
- Global statistics: **Thread-safe** with mutex protection
- Error handling: **Thread-local** error storage

## Integration Examples

See `examples/hello_dtesn.c` for comprehensive usage examples covering:
- Basic instance lifecycle management
- P-system membrane operations
- B-series computations with OEIS validation
- ESN reservoir management and prediction
- Performance monitoring and statistics

## Requirements

- **Minimum C Standard**: C99
- **Required Libraries**: libm, libpthread
- **Kernel Support**: DTESN kernel modules must be loaded
- **Python Bindings**: Python 3.6+ with development headers
- **WebAssembly**: Emscripten SDK for JavaScript bindings