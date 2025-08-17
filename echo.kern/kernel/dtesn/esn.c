/*
 * DTESN Echo State Network Reservoir Computing Implementation
 * =========================================================
 * 
 * Implementation of high-performance ESN reservoir computing for
 * Deep Tree Echo State Networks with real-time constraints,
 * OEIS A000081 compliance, and hardware acceleration support.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/esn.h"
#include "include/dtesn/memory.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>
#include <sys/time.h>
#include <math.h>
#include <float.h>

/* Internal constants */
#define DTESN_ESN_MEMORY_POOL_SIZE      (64 * 1024 * 1024)  /* 64MB */
#define DTESN_ESN_DEFAULT_TOLERANCE     1e-6
#define DTESN_ESN_MAX_ADAPTATION_STEPS  1000
#define DTESN_ESN_SPECTRAL_RADIUS_MIN   0.1
#define DTESN_ESN_SPECTRAL_RADIUS_MAX   0.99

/* Global state */
static bool g_esn_initialized = false;
static pthread_mutex_t g_esn_lock = PTHREAD_MUTEX_INITIALIZER;
static uint32_t g_next_reservoir_id = 1;

/* OEIS A000081 sequence for validation */
static const uint32_t g_oeis_a000081[] = DTESN_ESN_A000081_SEQUENCE;

/* Performance tracking */
static struct {
    uint64_t total_state_updates;
    uint64_t total_state_update_time_ns;
    uint64_t total_matrix_multiplies;
    uint64_t total_matrix_mult_time_ns;
    uint64_t total_sparse_operations;
    uint64_t total_sparse_time_ns;
} g_performance_stats = {0};

/* Forward declarations for internal functions */
static int dtesn_esn_init_weights(dtesn_esn_reservoir_t *reservoir);
static int dtesn_esn_validate_config(const dtesn_esn_config_t *config);
static uint64_t dtesn_esn_get_time_ns(void);
static float dtesn_esn_activation_function(float x, dtesn_esn_activation_t type);
static int dtesn_esn_compute_spectral_radius(dtesn_esn_sparse_matrix_t *matrix, float *spectral_radius);

/**
 * Get current time in nanoseconds
 */
static uint64_t dtesn_esn_get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Apply activation function
 */
static float dtesn_esn_activation_function(float x, dtesn_esn_activation_t type) {
    switch (type) {
        case DTESN_ESN_ACTIVATION_TANH:
            return tanhf(x);
        case DTESN_ESN_ACTIVATION_SIGMOID:
            return 1.0f / (1.0f + expf(-x));
        case DTESN_ESN_ACTIVATION_RELU:
            return fmaxf(0.0f, x);
        case DTESN_ESN_ACTIVATION_LINEAR:
        default:
            return x;
    }
}

/**
 * Validate ESN configuration parameters
 */
static int dtesn_esn_validate_config(const dtesn_esn_config_t *config) {
    if (!config) {
        return DTESN_ESN_EINVAL;
    }
    
    if (config->reservoir_size == 0 || config->reservoir_size > DTESN_ESN_MAX_RESERVOIR_SIZE) {
        return DTESN_ESN_EINVAL;
    }
    
    if (config->input_size == 0 || config->input_size > DTESN_ESN_MAX_INPUT_SIZE) {
        return DTESN_ESN_EINVAL;
    }
    
    if (config->spectral_radius <= 0.0f || config->spectral_radius >= 1.0f) {
        return DTESN_ESN_EINVAL;
    }
    
    if (config->leak_rate <= 0.0f || config->leak_rate > 1.0f) {
        return DTESN_ESN_EINVAL;
    }
    
    if (config->connectivity <= 0.0f || config->connectivity > 1.0f) {
        return DTESN_ESN_EINVAL;
    }
    
    return 0;
}

/**
 * Initialize reservoir weight matrices
 */
static int dtesn_esn_init_weights(dtesn_esn_reservoir_t *reservoir) {
    if (!reservoir) {
        return DTESN_ESN_EINVAL;
    }
    
    const dtesn_esn_config_t *config = &reservoir->config;
    
    /* Initialize random number generator with time-based seed */
    srand((unsigned int)time(NULL) ^ reservoir->reservoir_id);
    
    /* Create reservoir weight matrix (sparse) */
    reservoir->W_res = dtesn_esn_sparse_matrix_create(
        config->reservoir_size, config->reservoir_size, config->connectivity);
    if (!reservoir->W_res) {
        return DTESN_ESN_ENOMEM;
    }
    
    /* Fill reservoir matrix with random weights */
    for (uint32_t i = 0; i < reservoir->W_res->nnz; i++) {
        reservoir->W_res->values[i] = (float)(rand()) / RAND_MAX * 2.0f - 1.0f;
    }
    
    /* Scale to achieve desired spectral radius */
    float current_spectral_radius;
    int result = dtesn_esn_compute_spectral_radius(reservoir->W_res, &current_spectral_radius);
    if (result == 0 && current_spectral_radius > 0.0f) {
        float scale_factor = config->spectral_radius / current_spectral_radius;
        for (uint32_t i = 0; i < reservoir->W_res->nnz; i++) {
            reservoir->W_res->values[i] *= scale_factor;
        }
        reservoir->current_spectral_radius = config->spectral_radius;
    } else {
        reservoir->current_spectral_radius = config->spectral_radius;
    }
    
    /* Create input weight matrix (sparse) */
    uint32_t input_connections = config->input_connectivity > 0 ? 
        config->input_connectivity : (uint32_t)(config->connectivity * config->input_size);
    float input_sparsity = (float)input_connections / (float)config->input_size;
    
    reservoir->W_in = dtesn_esn_sparse_matrix_create(
        config->reservoir_size, config->input_size, input_sparsity);
    if (!reservoir->W_in) {
        return DTESN_ESN_ENOMEM;
    }
    
    /* Fill input matrix with scaled random weights */
    for (uint32_t i = 0; i < reservoir->W_in->nnz; i++) {
        reservoir->W_in->values[i] = ((float)(rand()) / RAND_MAX * 2.0f - 1.0f) * config->input_scaling;
    }
    
    /* Initialize output weights (dense, will be trained) */
    reservoir->W_out = calloc(config->output_size * config->reservoir_size, sizeof(float));
    if (!reservoir->W_out) {
        return DTESN_ESN_ENOMEM;
    }
    
    /* Initialize bias vector if enabled */
    if (config->use_bias) {
        reservoir->bias = calloc(config->reservoir_size, sizeof(float));
        if (!reservoir->bias) {
            return DTESN_ESN_ENOMEM;
        }
        
        /* Fill bias with scaled random values */
        for (uint32_t i = 0; i < config->reservoir_size; i++) {
            reservoir->bias[i] = ((float)(rand()) / RAND_MAX * 2.0f - 1.0f) * config->bias_scaling;
        }
    }
    
    return 0;
}

/**
 * Compute spectral radius of sparse matrix (approximation)
 */
static int dtesn_esn_compute_spectral_radius(dtesn_esn_sparse_matrix_t *matrix, float *spectral_radius) {
    if (!matrix || !spectral_radius) {
        return DTESN_ESN_EINVAL;
    }
    
    /* Use power iteration method for approximation */
    const uint32_t max_iterations = 100;
    const float tolerance = 1e-6f;
    
    float *v = malloc(matrix->rows * sizeof(float));
    float *Av = malloc(matrix->rows * sizeof(float));
    if (!v || !Av) {
        free(v);
        free(Av);
        return DTESN_ESN_ENOMEM;
    }
    
    /* Initialize random vector */
    for (uint32_t i = 0; i < matrix->rows; i++) {
        v[i] = (float)(rand()) / RAND_MAX;
    }
    
    float lambda = 0.0f;
    for (uint32_t iter = 0; iter < max_iterations; iter++) {
        /* Compute Av = A * v */
        esn_sparse_multiply(matrix, v, Av);
        
        /* Compute eigenvalue estimate */
        float dot_Av_v = 0.0f;
        float dot_v_v = 0.0f;
        for (uint32_t i = 0; i < matrix->rows; i++) {
            dot_Av_v += Av[i] * v[i];
            dot_v_v += v[i] * v[i];
        }
        
        float new_lambda = (dot_v_v > 0.0f) ? dot_Av_v / dot_v_v : 0.0f;
        
        /* Check convergence */
        if (iter > 0 && fabsf(new_lambda - lambda) < tolerance) {
            break;
        }
        
        lambda = new_lambda;
        
        /* Normalize Av -> v for next iteration */
        float norm = 0.0f;
        for (uint32_t i = 0; i < matrix->rows; i++) {
            norm += Av[i] * Av[i];
        }
        norm = sqrtf(norm);
        
        if (norm > 0.0f) {
            for (uint32_t i = 0; i < matrix->rows; i++) {
                v[i] = Av[i] / norm;
            }
        }
    }
    
    *spectral_radius = fabsf(lambda);
    
    free(v);
    free(Av);
    return 0;
}

/* Public API Implementation */

int dtesn_esn_init(void) {
    pthread_mutex_lock(&g_esn_lock);
    
    if (g_esn_initialized) {
        pthread_mutex_unlock(&g_esn_lock);
        return 0;
    }
    
    /* Initialize performance tracking */
    memset(&g_performance_stats, 0, sizeof(g_performance_stats));
    
    g_esn_initialized = true;
    pthread_mutex_unlock(&g_esn_lock);
    
    return 0;
}

dtesn_esn_reservoir_t *esn_reservoir_init(const dtesn_esn_config_t *config, const char *name) {
    if (!g_esn_initialized) {
        return NULL;
    }
    
    if (dtesn_esn_validate_config(config) != 0) {
        return NULL;
    }
    
    dtesn_esn_reservoir_t *reservoir = calloc(1, sizeof(dtesn_esn_reservoir_t));
    if (!reservoir) {
        return NULL;
    }
    
    /* Assign unique ID */
    pthread_mutex_lock(&g_esn_lock);
    reservoir->reservoir_id = g_next_reservoir_id++;
    pthread_mutex_unlock(&g_esn_lock);
    
    /* Copy configuration */
    reservoir->config = *config;
    
    /* Set name */
    if (name) {
        strncpy(reservoir->name, name, sizeof(reservoir->name) - 1);
        reservoir->name[sizeof(reservoir->name) - 1] = '\0';
    } else {
        snprintf(reservoir->name, sizeof(reservoir->name), "ESN_%u", reservoir->reservoir_id);
    }
    
    /* Allocate state vectors */
    reservoir->x_current = calloc(config->reservoir_size, sizeof(float));
    reservoir->x_previous = calloc(config->reservoir_size, sizeof(float));
    reservoir->u_current = calloc(config->input_size, sizeof(float));
    reservoir->y_current = calloc(config->output_size, sizeof(float));
    
    if (!reservoir->x_current || !reservoir->x_previous || 
        !reservoir->u_current || !reservoir->y_current) {
        dtesn_esn_reservoir_destroy(reservoir);
        return NULL;
    }
    
    /* Initialize weight matrices */
    if (dtesn_esn_init_weights(reservoir) != 0) {
        dtesn_esn_reservoir_destroy(reservoir);
        return NULL;
    }
    
    /* Initialize synchronization */
    if (pthread_mutex_init(&reservoir->state_lock, NULL) != 0 ||
        pthread_cond_init(&reservoir->update_cond, NULL) != 0) {
        dtesn_esn_reservoir_destroy(reservoir);
        return NULL;
    }
    
    /* Set initial state */
    reservoir->state = DTESN_ESN_STATE_INITIALIZED;
    reservoir->adaptation_rate = 0.01f;
    reservoir->creation_time_ns = dtesn_esn_get_time_ns();
    reservoir->is_validated = false;
    
    /* Validate OEIS A000081 compliance if requested */
    if (config->oeis_compliance) {
        reservoir->is_validated = dtesn_esn_validate_a000081(reservoir);
    }
    
    return reservoir;
}

void dtesn_esn_reservoir_destroy(dtesn_esn_reservoir_t *reservoir) {
    if (!reservoir) {
        return;
    }
    
    /* Free sparse matrices */
    dtesn_esn_sparse_matrix_destroy(reservoir->W_res);
    dtesn_esn_sparse_matrix_destroy(reservoir->W_in);
    
    /* Free dense matrices and vectors */
    free(reservoir->W_out);
    free(reservoir->bias);
    free(reservoir->x_current);
    free(reservoir->x_previous);
    free(reservoir->u_current);
    free(reservoir->y_current);
    
    /* Free memory pool if allocated */
    free(reservoir->memory_pool);
    
    /* Destroy synchronization objects */
    pthread_mutex_destroy(&reservoir->state_lock);
    pthread_cond_destroy(&reservoir->update_cond);
    
    /* Free hardware acceleration context */
    free(reservoir->accel_context);
    
    free(reservoir);
}

int esn_state_update(dtesn_esn_reservoir_t *reservoir, const float *input, uint32_t input_size) {
    if (!reservoir || !input) {
        return DTESN_ESN_EINVAL;
    }
    
    if (input_size != reservoir->config.input_size) {
        return DTESN_ESN_EINVAL;
    }
    
    uint64_t start_time = dtesn_esn_get_time_ns();
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    reservoir->state = DTESN_ESN_STATE_RUNNING;
    
    /* Copy input vector */
    memcpy(reservoir->u_current, input, input_size * sizeof(float));
    
    /* Save previous state */
    memcpy(reservoir->x_previous, reservoir->x_current, 
           reservoir->config.reservoir_size * sizeof(float));
    
    /* Compute W_in * u(t) */
    float *input_contribution = calloc(reservoir->config.reservoir_size, sizeof(float));
    if (!input_contribution) {
        pthread_mutex_unlock(&reservoir->state_lock);
        return DTESN_ESN_ENOMEM;
    }
    
    int result = esn_sparse_multiply(reservoir->W_in, input, input_contribution);
    if (result != 0) {
        free(input_contribution);
        pthread_mutex_unlock(&reservoir->state_lock);
        return result;
    }
    
    /* Compute W_res * x(t-1) */
    float *recurrent_contribution = calloc(reservoir->config.reservoir_size, sizeof(float));
    if (!recurrent_contribution) {
        free(input_contribution);
        pthread_mutex_unlock(&reservoir->state_lock);
        return DTESN_ESN_ENOMEM;
    }
    
    result = esn_sparse_multiply(reservoir->W_res, reservoir->x_previous, recurrent_contribution);
    if (result != 0) {
        free(input_contribution);
        free(recurrent_contribution);
        pthread_mutex_unlock(&reservoir->state_lock);
        return result;
    }
    
    /* Update reservoir state: x(t) = (1-α)x(t-1) + α*tanh(W_in*u(t) + W_res*x(t-1) + bias) */
    float leak_rate = reservoir->config.leak_rate;
    float noise_level = reservoir->config.noise_level;
    
    for (uint32_t i = 0; i < reservoir->config.reservoir_size; i++) {
        float net_input = input_contribution[i] + recurrent_contribution[i];
        
        /* Add bias if enabled */
        if (reservoir->bias) {
            net_input += reservoir->bias[i];
        }
        
        /* Add noise if enabled */
        if (noise_level > 0.0f) {
            float noise = ((float)(rand()) / RAND_MAX * 2.0f - 1.0f) * noise_level;
            net_input += noise;
        }
        
        /* Apply activation function */
        float activation = dtesn_esn_activation_function(net_input, reservoir->config.activation);
        
        /* Apply leak rate */
        reservoir->x_current[i] = (1.0f - leak_rate) * reservoir->x_previous[i] + 
                                  leak_rate * activation;
    }
    
    free(input_contribution);
    free(recurrent_contribution);
    
    /* Update performance statistics */
    reservoir->total_updates++;
    uint64_t update_time = dtesn_esn_get_time_ns() - start_time;
    reservoir->total_update_time_ns += update_time;
    reservoir->avg_update_time_ns = reservoir->total_update_time_ns / reservoir->total_updates;
    
    if (update_time > reservoir->max_update_time_ns) {
        reservoir->max_update_time_ns = update_time;
    }
    
    reservoir->last_update_ns = dtesn_esn_get_time_ns();
    
    /* Update global statistics */
    pthread_mutex_lock(&g_esn_lock);
    g_performance_stats.total_state_updates++;
    g_performance_stats.total_state_update_time_ns += update_time;
    pthread_mutex_unlock(&g_esn_lock);
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    /* Check timing constraint */
    if (update_time > DTESN_ESN_STATE_UPDATE_THRESHOLD_US * 1000) {
        return DTESN_ESN_ELATENCY;
    }
    
    return 0;
}

int dtesn_esn_compute_output(dtesn_esn_reservoir_t *reservoir, float *output, uint32_t output_size) {
    if (!reservoir || !output) {
        return DTESN_ESN_EINVAL;
    }
    
    if (output_size != reservoir->config.output_size) {
        return DTESN_ESN_EINVAL;
    }
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    /* Compute y = W_out * x */
    for (uint32_t i = 0; i < output_size; i++) {
        output[i] = 0.0f;
        for (uint32_t j = 0; j < reservoir->config.reservoir_size; j++) {
            output[i] += reservoir->W_out[i * reservoir->config.reservoir_size + j] * 
                        reservoir->x_current[j];
        }
    }
    
    /* Copy to internal output vector */
    memcpy(reservoir->y_current, output, output_size * sizeof(float));
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    return 0;
}

int dtesn_esn_config_default(dtesn_esn_config_t *config) {
    if (!config) {
        return DTESN_ESN_EINVAL;
    }
    
    memset(config, 0, sizeof(dtesn_esn_config_t));
    
    config->reservoir_size = 100;
    config->input_size = 10;
    config->output_size = 1;
    config->spectral_radius = 0.95f;
    config->leak_rate = 0.3f;
    config->input_scaling = 1.0f;
    config->bias_scaling = 0.1f;
    config->noise_level = 0.001f;
    config->connectivity = 0.1f;
    config->input_connectivity = 10;
    config->use_bias = true;
    config->activation = DTESN_ESN_ACTIVATION_TANH;
    config->accel_type = DTESN_ESN_ACCEL_NONE;
    config->use_sparse_matrices = true;
    config->thread_count = 1;
    config->oeis_compliance = true;
    config->tree_depth = 4;
    
    return 0;
}

bool dtesn_esn_validate_a000081(dtesn_esn_reservoir_t *reservoir) {
    if (!reservoir) {
        return false;
    }
    
    /* For now, we implement basic topology validation */
    /* More sophisticated validation would analyze the actual network structure */
    uint32_t depth = reservoir->config.tree_depth;
    if (depth >= DTESN_ESN_A000081_MAX_DEPTH) {
        return false;
    }
    
    /* Check if reservoir size follows reasonable bounds for the tree depth */
    uint32_t expected_max_nodes = g_oeis_a000081[depth];
    if (reservoir->config.reservoir_size > expected_max_nodes * 100) {
        return false; /* Too large for given depth */
    }
    
    return true;
}

int dtesn_esn_get_stats(dtesn_esn_reservoir_t *reservoir, dtesn_esn_stats_t *stats) {
    if (!reservoir || !stats) {
        return DTESN_ESN_EINVAL;
    }
    
    memset(stats, 0, sizeof(dtesn_esn_stats_t));
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    stats->total_state_updates = reservoir->total_updates;
    stats->avg_state_update_time_ns = reservoir->avg_update_time_ns;
    stats->max_state_update_time_ns = reservoir->max_update_time_ns;
    
    /* Check performance thresholds */
    stats->state_threshold_met = 
        (reservoir->avg_update_time_ns <= DTESN_ESN_STATE_UPDATE_THRESHOLD_US * 1000);
    
    /* Estimate memory bandwidth (rough approximation) */
    if (reservoir->total_updates > 0) {
        size_t bytes_per_update = reservoir->config.reservoir_size * sizeof(float) * 3; /* x, u, y */
        float updates_per_second = 1e9f / reservoir->avg_update_time_ns;
        stats->avg_memory_bandwidth_gbps = (bytes_per_update * updates_per_second) / 1e9f;
        stats->bandwidth_threshold_met = 
            (stats->avg_memory_bandwidth_gbps >= DTESN_ESN_MEMORY_BANDWIDTH_GBPS);
    }
    
    /* Sparsity efficiency */
    if (reservoir->W_res) {
        stats->avg_sparsity_efficiency = reservoir->W_res->sparsity * 100.0f;
        stats->sparsity_threshold_met = 
            (stats->avg_sparsity_efficiency >= DTESN_ESN_SPARSITY_EFFICIENCY_PCT);
    }
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    return 0;
}

int esn_adaptive_scale(dtesn_esn_reservoir_t *reservoir, float performance_metric, float target_metric) {
    if (!reservoir) {
        return DTESN_ESN_EINVAL;
    }
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    /* Calculate performance error */
    float error = target_metric - performance_metric;
    float adaptation_step = reservoir->adaptation_rate * error;
    
    /* Adaptive spectral radius scaling */
    float new_spectral_radius = reservoir->current_spectral_radius + adaptation_step * 0.1f;
    
    /* Clamp to valid range */
    if (new_spectral_radius < DTESN_ESN_SPECTRAL_RADIUS_MIN) {
        new_spectral_radius = DTESN_ESN_SPECTRAL_RADIUS_MIN;
    } else if (new_spectral_radius > DTESN_ESN_SPECTRAL_RADIUS_MAX) {
        new_spectral_radius = DTESN_ESN_SPECTRAL_RADIUS_MAX;
    }
    
    /* Apply scaling if significant change */
    if (fabsf(new_spectral_radius - reservoir->current_spectral_radius) > 1e-4f) {
        float scale_factor = new_spectral_radius / reservoir->current_spectral_radius;
        
        /* Scale reservoir weights */
        if (reservoir->W_res) {
            for (uint32_t i = 0; i < reservoir->W_res->nnz; i++) {
                reservoir->W_res->values[i] *= scale_factor;
            }
        }
        
        reservoir->current_spectral_radius = new_spectral_radius;
        reservoir->adaptation_step++;
    }
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    return 0;
}

int dtesn_esn_auto_tune(dtesn_esn_reservoir_t *reservoir, const float **training_data, 
                       const float **target_data, uint32_t num_samples) {
    if (!reservoir || !training_data || !target_data) {
        return DTESN_ESN_EINVAL;
    }
    
    /* Basic auto-tuning implementation */
    /* In a full implementation, this would use more sophisticated optimization */
    
    float best_performance = FLT_MAX;
    float best_spectral_radius = reservoir->current_spectral_radius;
    float best_leak_rate = reservoir->config.leak_rate;
    
    /* Grid search over parameter space */
    for (float sr = 0.1f; sr < 1.0f; sr += 0.1f) {
        for (float lr = 0.1f; lr < 1.0f; lr += 0.1f) {
            /* Set parameters */
            reservoir->config.spectral_radius = sr;
            reservoir->config.leak_rate = lr;
            
            /* Reinitialize weights with new spectral radius */
            dtesn_esn_init_weights(reservoir);
            
            /* Test performance on training data */
            float total_error = 0.0f;
            for (uint32_t i = 0; i < num_samples && i < 100; i++) {
                esn_state_update(reservoir, training_data[i], reservoir->config.input_size);
                
                /* Compute simple error metric */
                for (uint32_t j = 0; j < reservoir->config.reservoir_size && j < 10; j++) {
                    float error = reservoir->x_current[j] - (target_data[i] ? target_data[i][j % reservoir->config.output_size] : 0.0f);
                    total_error += error * error;
                }
            }
            
            if (total_error < best_performance) {
                best_performance = total_error;
                best_spectral_radius = sr;
                best_leak_rate = lr;
            }
        }
    }
    
    /* Apply best parameters */
    reservoir->config.spectral_radius = best_spectral_radius;
    reservoir->config.leak_rate = best_leak_rate;
    reservoir->current_spectral_radius = best_spectral_radius;
    
    /* Reinitialize with optimal parameters */
    return dtesn_esn_init_weights(reservoir);
}

int dtesn_esn_check_stability(dtesn_esn_reservoir_t *reservoir, float *stability_metric) {
    if (!reservoir || !stability_metric) {
        return DTESN_ESN_EINVAL;
    }
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    /* Compute stability metric based on state variance */
    float mean = 0.0f;
    for (uint32_t i = 0; i < reservoir->config.reservoir_size; i++) {
        mean += reservoir->x_current[i];
    }
    mean /= reservoir->config.reservoir_size;
    
    float variance = 0.0f;
    for (uint32_t i = 0; i < reservoir->config.reservoir_size; i++) {
        float diff = reservoir->x_current[i] - mean;
        variance += diff * diff;
    }
    variance /= reservoir->config.reservoir_size;
    
    *stability_metric = sqrtf(variance);
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    /* Check if variance is within reasonable bounds */
    return (*stability_metric < 10.0f) ? 0 : DTESN_ESN_ESTABILITY;
}

int dtesn_esn_save_state(dtesn_esn_reservoir_t *reservoir, void *buffer, size_t buffer_size) {
    if (!reservoir || !buffer) {
        return DTESN_ESN_EINVAL;
    }
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    /* Calculate required size */
    size_t required_size = sizeof(dtesn_esn_config_t) + 
                          reservoir->config.reservoir_size * sizeof(float) * 2 + /* x_current, x_previous */
                          reservoir->config.input_size * sizeof(float) + /* u_current */
                          reservoir->config.output_size * sizeof(float) + /* y_current */
                          sizeof(uint64_t) * 3; /* timestamps and counters */
    
    if (buffer_size < required_size) {
        pthread_mutex_unlock(&reservoir->state_lock);
        return -1; /* Buffer too small */
    }
    
    uint8_t *ptr = (uint8_t *)buffer;
    
    /* Save configuration */
    memcpy(ptr, &reservoir->config, sizeof(dtesn_esn_config_t));
    ptr += sizeof(dtesn_esn_config_t);
    
    /* Save state vectors */
    memcpy(ptr, reservoir->x_current, reservoir->config.reservoir_size * sizeof(float));
    ptr += reservoir->config.reservoir_size * sizeof(float);
    
    memcpy(ptr, reservoir->x_previous, reservoir->config.reservoir_size * sizeof(float));
    ptr += reservoir->config.reservoir_size * sizeof(float);
    
    memcpy(ptr, reservoir->u_current, reservoir->config.input_size * sizeof(float));
    ptr += reservoir->config.input_size * sizeof(float);
    
    memcpy(ptr, reservoir->y_current, reservoir->config.output_size * sizeof(float));
    ptr += reservoir->config.output_size * sizeof(float);
    
    /* Save metadata */
    memcpy(ptr, &reservoir->total_updates, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    memcpy(ptr, &reservoir->adaptation_step, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    memcpy(ptr, &reservoir->creation_time_ns, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    return (int)(ptr - (uint8_t *)buffer);
}

int dtesn_esn_load_state(dtesn_esn_reservoir_t *reservoir, const void *buffer, size_t buffer_size) {
    if (!reservoir || !buffer) {
        return DTESN_ESN_EINVAL;
    }
    
    pthread_mutex_lock(&reservoir->state_lock);
    
    const uint8_t *ptr = (const uint8_t *)buffer;
    
    /* Load and validate configuration */
    if (buffer_size < sizeof(dtesn_esn_config_t)) {
        pthread_mutex_unlock(&reservoir->state_lock);
        return DTESN_ESN_EINVAL;
    }
    
    dtesn_esn_config_t saved_config;
    memcpy(&saved_config, ptr, sizeof(dtesn_esn_config_t));
    ptr += sizeof(dtesn_esn_config_t);
    
    /* Verify configuration compatibility */
    if (saved_config.reservoir_size != reservoir->config.reservoir_size ||
        saved_config.input_size != reservoir->config.input_size ||
        saved_config.output_size != reservoir->config.output_size) {
        pthread_mutex_unlock(&reservoir->state_lock);
        return DTESN_ESN_EINVAL;
    }
    
    /* Load state vectors */
    memcpy(reservoir->x_current, ptr, reservoir->config.reservoir_size * sizeof(float));
    ptr += reservoir->config.reservoir_size * sizeof(float);
    
    memcpy(reservoir->x_previous, ptr, reservoir->config.reservoir_size * sizeof(float));
    ptr += reservoir->config.reservoir_size * sizeof(float);
    
    memcpy(reservoir->u_current, ptr, reservoir->config.input_size * sizeof(float));
    ptr += reservoir->config.input_size * sizeof(float);
    
    memcpy(reservoir->y_current, ptr, reservoir->config.output_size * sizeof(float));
    ptr += reservoir->config.output_size * sizeof(float);
    
    /* Load metadata */
    memcpy(&reservoir->total_updates, ptr, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    memcpy(&reservoir->adaptation_step, ptr, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    uint64_t saved_creation_time;
    memcpy(&saved_creation_time, ptr, sizeof(uint64_t));
    ptr += sizeof(uint64_t);
    
    /* Update some configuration parameters */
    reservoir->config = saved_config;
    
    pthread_mutex_unlock(&reservoir->state_lock);
    
    return 0;
}

void dtesn_esn_shutdown(void) {
    pthread_mutex_lock(&g_esn_lock);
    
    if (!g_esn_initialized) {
        pthread_mutex_unlock(&g_esn_lock);
        return;
    }
    
    g_esn_initialized = false;
    pthread_mutex_unlock(&g_esn_lock);
}