/*
 * DTESN ESN Reservoir Management
 * =============================
 * 
 * Implementation of Echo State Network (ESN) reservoir management APIs
 * for the DTESN user-space library. Provides high-level interfaces for
 * ESN state updates, training, and prediction operations.
 */

#include "libdtesn.h"
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

/* Internal thread-local error storage */
static __thread int g_last_esn_error = 0;

/* Internal helper functions */
static int validate_esn_dimensions(dtesn_handle_t *handle, uint32_t input_size, 
                                   uint32_t state_size, uint32_t output_size);
static int validate_training_data(const float *input_data, const float *target_data,
                                  uint32_t samples, uint32_t input_dim, uint32_t output_dim);
static float compute_spectral_radius(const float *weights, uint32_t size);
static void normalize_reservoir_weights(float *weights, uint32_t size, float target_radius);

static int validate_esn_dimensions(dtesn_handle_t *handle, uint32_t input_size,
                                   uint32_t state_size, uint32_t output_size)
{
    if (!handle) {
        return -EINVAL;
    }
    
    /* Validate input dimension against instance configuration */
    if (input_size > handle->params.input_dim) {
        return -EINVAL;
    }
    
    /* Validate output dimension against instance configuration */
    if (output_size > handle->params.output_dim) {
        return -EINVAL;
    }
    
    /* Validate reservoir size against instance configuration */
    if (state_size > handle->params.neuron_count) {
        return -EINVAL;
    }
    
    /* Check reasonable bounds */
    if (input_size == 0 || state_size == 0) {
        return -EINVAL;
    }
    
    return 0;
}

static int validate_training_data(const float *input_data, const float *target_data,
                                  uint32_t samples, uint32_t input_dim, uint32_t output_dim)
{
    if (!input_data || !target_data) {
        return -EINVAL;
    }
    
    if (samples == 0 || input_dim == 0 || output_dim == 0) {
        return -EINVAL;
    }
    
    /* Check for reasonable sample count (avoid excessive memory usage) */
    if (samples > 100000) {
        return -EINVAL;
    }
    
    /* Check for NaN or infinite values in a sample of the data */
    for (uint32_t i = 0; i < 10 && i < samples; i++) {
        for (uint32_t j = 0; j < input_dim; j++) {
            float val = input_data[i * input_dim + j];
            if (isnan(val) || isinf(val)) {
                return -EINVAL;
            }
        }
        
        for (uint32_t j = 0; j < output_dim; j++) {
            float val = target_data[i * output_dim + j];
            if (isnan(val) || isinf(val)) {
                return -EINVAL;
            }
        }
    }
    
    return 0;
}

static float compute_spectral_radius(const float *weights, uint32_t size)
{
    /* Simplified spectral radius computation
     * Real implementation would use proper eigenvalue computation */
    
    float max_abs = 0.0f;
    for (uint32_t i = 0; i < size; i++) {
        float abs_val = fabsf(weights[i]);
        if (abs_val > max_abs) {
            max_abs = abs_val;
        }
    }
    
    /* Rough approximation - real spectral radius would be computed differently */
    return max_abs * sqrtf((float)size);
}

static void normalize_reservoir_weights(float *weights, uint32_t size, float target_radius)
{
    if (target_radius <= 0.0f || !weights) {
        return;
    }
    
    float current_radius = compute_spectral_radius(weights, size);
    if (current_radius > 0.0f) {
        float scale_factor = target_radius / current_radius;
        for (uint32_t i = 0; i < size; i++) {
            weights[i] *= scale_factor;
        }
    }
}

/*
 * ESN Reservoir Management API Implementation
 */

int dtesn_esn_update(dtesn_handle_t *handle, const float *input, uint32_t input_size,
                     float *state, uint32_t state_size)
{
    if (!handle || !input || !state) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate dimensions */
    int validation_result = validate_esn_dimensions(handle, input_size, state_size, 0);
    if (validation_result != 0) {
        g_last_esn_error = validation_result;
        return validation_result;
    }
    
    /* Prepare ESN update parameters */
    struct dtesn_esn_params esn_params = {
        .fd = handle->fd,
        .input = input,
        .input_size = input_size,
        .state = state,
        .state_size = state_size,
        .output = NULL,  /* Not used for update */
        .output_size = 0,
        .learning_rate = 0.0f,  /* Not used for update */
        .regularization = 0.0f   /* Not used for update */
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_esn_update, &esn_params);
    
    if (syscall_result < 0) {
        g_last_esn_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

int dtesn_esn_train(dtesn_handle_t *handle, const float *input_data,
                    const float *target_data, uint32_t samples,
                    uint32_t input_dim, uint32_t output_dim)
{
    if (!handle) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate training data */
    int validation_result = validate_training_data(input_data, target_data, samples, input_dim, output_dim);
    if (validation_result != 0) {
        g_last_esn_error = validation_result;
        return validation_result;
    }
    
    /* Validate dimensions against handle configuration */
    int dimension_result = validate_esn_dimensions(handle, input_dim, handle->params.neuron_count, output_dim);
    if (dimension_result != 0) {
        g_last_esn_error = dimension_result;
        return dimension_result;
    }
    
    /* For training, we need to iterate through samples and accumulate states
     * This is a simplified implementation - real ESN training would be more complex */
    
    float *accumulated_states = calloc(samples * handle->params.neuron_count, sizeof(float));
    if (!accumulated_states) {
        g_last_esn_error = -ENOMEM;
        return -ENOMEM;
    }
    
    float *current_state = calloc(handle->params.neuron_count, sizeof(float));
    if (!current_state) {
        free(accumulated_states);
        g_last_esn_error = -ENOMEM;
        return -ENOMEM;
    }
    
    /* Run reservoir through all training samples to collect states */
    for (uint32_t sample = 0; sample < samples; sample++) {
        const float *current_input = &input_data[sample * input_dim];
        
        /* Update reservoir state */
        int update_result = dtesn_esn_update(handle, current_input, input_dim,
                                             current_state, handle->params.neuron_count);
        if (update_result != 0) {
            free(accumulated_states);
            free(current_state);
            g_last_esn_error = update_result;
            return update_result;
        }
        
        /* Store state for this sample */
        memcpy(&accumulated_states[sample * handle->params.neuron_count],
               current_state, handle->params.neuron_count * sizeof(float));
    }
    
    /* Prepare training parameters */
    struct {
        uint32_t samples;
        uint32_t input_dim;
        uint32_t output_dim;
        uint32_t reservoir_size;
        const float *states;
        const float *targets;
    } training_data = {
        .samples = samples,
        .input_dim = input_dim,
        .output_dim = output_dim,
        .reservoir_size = handle->params.neuron_count,
        .states = accumulated_states,
        .targets = target_data
    };
    
    /* Prepare ESN parameters for training syscall */
    struct dtesn_esn_params esn_params = {
        .fd = handle->fd,
        .input = (const float *)&training_data,  /* Pass training data structure */
        .input_size = sizeof(training_data),
        .state = NULL,
        .state_size = 0,
        .output = NULL,
        .output_size = 0,
        .learning_rate = 0.01f,       /* Default learning rate */
        .regularization = 0.001f      /* Default regularization */
    };
    
    /* Make system call for training */
    long syscall_result = syscall(__NR_sys_esn_update, &esn_params);
    
    /* Cleanup */
    free(accumulated_states);
    free(current_state);
    
    if (syscall_result < 0) {
        g_last_esn_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

int dtesn_esn_predict(dtesn_handle_t *handle, const float *input, uint32_t input_size,
                      float *output, uint32_t output_size)
{
    if (!handle || !input || !output) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate dimensions */
    int validation_result = validate_esn_dimensions(handle, input_size, handle->params.neuron_count, output_size);
    if (validation_result != 0) {
        g_last_esn_error = validation_result;
        return validation_result;
    }
    
    /* Allocate temporary state vector */
    float *temp_state = calloc(handle->params.neuron_count, sizeof(float));
    if (!temp_state) {
        g_last_esn_error = -ENOMEM;
        return -ENOMEM;
    }
    
    /* First, update reservoir state with input */
    int update_result = dtesn_esn_update(handle, input, input_size, temp_state, handle->params.neuron_count);
    if (update_result != 0) {
        free(temp_state);
        g_last_esn_error = update_result;
        return update_result;
    }
    
    /* Prepare ESN parameters for prediction */
    struct dtesn_esn_params esn_params = {
        .fd = handle->fd,
        .input = input,
        .input_size = input_size,
        .state = temp_state,
        .state_size = handle->params.neuron_count,
        .output = output,
        .output_size = output_size,
        .learning_rate = 0.0f,    /* Not used for prediction */
        .regularization = 0.0f    /* Not used for prediction */
    };
    
    /* Make system call for prediction */
    long syscall_result = syscall(__NR_sys_esn_update, &esn_params);
    
    free(temp_state);
    
    if (syscall_result < 0) {
        g_last_esn_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

/* Extended ESN management functions */

int dtesn_esn_reset_state(dtesn_handle_t *handle)
{
    if (!handle) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Prepare zero state vector */
    float *zero_state = calloc(handle->params.neuron_count, sizeof(float));
    if (!zero_state) {
        g_last_esn_error = -ENOMEM;
        return -ENOMEM;
    }
    
    /* Zero input vector */
    float *zero_input = calloc(handle->params.input_dim, sizeof(float));
    if (!zero_input) {
        free(zero_state);
        g_last_esn_error = -ENOMEM;
        return -ENOMEM;
    }
    
    /* Update with zero input to reset state */
    int update_result = dtesn_esn_update(handle, zero_input, handle->params.input_dim,
                                         zero_state, handle->params.neuron_count);
    
    free(zero_state);
    free(zero_input);
    
    if (update_result != 0) {
        g_last_esn_error = update_result;
        return update_result;
    }
    
    return 0;
}

int dtesn_esn_get_reservoir_info(dtesn_handle_t *handle, uint32_t *neuron_count,
                                 float *spectral_radius, float *connectivity)
{
    if (!handle) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    if (neuron_count) {
        *neuron_count = handle->params.neuron_count;
    }
    
    if (spectral_radius) {
        /* In a real implementation, this would query the kernel for actual spectral radius */
        *spectral_radius = 0.95f;  /* Typical ESN spectral radius */
    }
    
    if (connectivity) {
        /* In a real implementation, this would query the kernel for actual connectivity */
        *connectivity = 0.1f;  /* Typical sparse connectivity */
    }
    
    return 0;
}

int dtesn_esn_set_parameters(dtesn_handle_t *handle, float spectral_radius,
                             float input_scaling, float leak_rate)
{
    if (!handle) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate parameter ranges */
    if (spectral_radius <= 0.0f || spectral_radius >= 2.0f) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    if (input_scaling <= 0.0f || input_scaling > 10.0f) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    if (leak_rate <= 0.0f || leak_rate > 1.0f) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Prepare parameter structure */
    struct {
        float spectral_radius;
        float input_scaling;
        float leak_rate;
    } esn_config = {
        .spectral_radius = spectral_radius,
        .input_scaling = input_scaling,
        .leak_rate = leak_rate
    };
    
    /* Prepare ESN parameters */
    struct dtesn_esn_params esn_params = {
        .fd = handle->fd,
        .input = (const float *)&esn_config,
        .input_size = sizeof(esn_config),
        .state = NULL,
        .state_size = 0,
        .output = NULL,
        .output_size = 0,
        .learning_rate = 0.0f,
        .regularization = 0.0f
    };
    
    /* Make system call to update ESN parameters */
    long syscall_result = syscall(__NR_sys_esn_update, &esn_params);
    
    if (syscall_result < 0) {
        g_last_esn_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

/* Batch processing functions */

int dtesn_esn_batch_predict(dtesn_handle_t *handle, const float *input_batch,
                            uint32_t batch_size, uint32_t input_dim,
                            float *output_batch, uint32_t output_dim)
{
    if (!handle || !input_batch || !output_batch) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    if (batch_size == 0 || batch_size > 10000) {  /* Reasonable batch size limit */
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate dimensions */
    int validation_result = validate_esn_dimensions(handle, input_dim, handle->params.neuron_count, output_dim);
    if (validation_result != 0) {
        g_last_esn_error = validation_result;
        return validation_result;
    }
    
    /* Process each sample in the batch */
    for (uint32_t i = 0; i < batch_size; i++) {
        const float *current_input = &input_batch[i * input_dim];
        float *current_output = &output_batch[i * output_dim];
        
        int predict_result = dtesn_esn_predict(handle, current_input, input_dim,
                                               current_output, output_dim);
        if (predict_result != 0) {
            g_last_esn_error = predict_result;
            return predict_result;
        }
    }
    
    return 0;
}

/* Memory and resource management */

int dtesn_esn_get_memory_usage(dtesn_handle_t *handle, size_t *bytes_used)
{
    if (!handle || !bytes_used) {
        g_last_esn_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Estimate memory usage based on ESN parameters */
    size_t reservoir_weights = handle->params.neuron_count * handle->params.neuron_count * sizeof(float);
    size_t input_weights = handle->params.input_dim * handle->params.neuron_count * sizeof(float);
    size_t output_weights = handle->params.neuron_count * handle->params.output_dim * sizeof(float);
    size_t state_vectors = handle->params.neuron_count * sizeof(float);
    size_t misc_overhead = 1024;  /* Approximate overhead for bookkeeping */
    
    *bytes_used = reservoir_weights + input_weights + output_weights + state_vectors + misc_overhead;
    
    return 0;
}