/*
 * DTESN Attention Mechanism Implementation
 * =======================================
 * 
 * Attention and focus mechanisms for cognitive processing including
 * bottom-up, top-down, competitive, and cooperative attention strategies
 * with ≤10ms attention switching performance target compliance.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/dtesn_cognitive.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <math.h>
#include <float.h>

/* Internal constants */
#define DTESN_ATTENTION_DEFAULT_FOCUS_SIZE      256     /* Default focus vector size */
#define DTESN_ATTENTION_COMPETITIVE_THRESHOLD   0.1f    /* Competition threshold */
#define DTESN_ATTENTION_COOPERATIVE_WEIGHT      0.8f    /* Cooperation weight */
#define DTESN_ATTENTION_DECAY_RATE             0.95f    /* Attention decay rate */
#define DTESN_ATTENTION_MIN_WEIGHT             0.001f   /* Minimum attention weight */
#define DTESN_ATTENTION_MAX_FOCUS_HISTORY      10       /* Focus history length */

/* Attention focus history for tracking */
typedef struct attention_focus_history {
    uint32_t channel_id;
    uint64_t timestamp_ns;
    float duration_ns;
    float weight;
} attention_focus_history_t;

/* Forward declarations */
static uint64_t get_time_ns(void);
static int validate_system(const dtesn_cognitive_system_t *system);
static int validate_channel_id(const dtesn_cognitive_system_t *system, uint32_t channel_id);
static float compute_saliency_score(const float *input_data, uint32_t size);
static int apply_bottom_up_attention(dtesn_cognitive_system_t *system, uint32_t channel_id);
static int apply_top_down_attention(dtesn_cognitive_system_t *system, uint32_t channel_id, 
                                   const float *focus_vector, uint32_t focus_size);
static int apply_competitive_attention(dtesn_cognitive_system_t *system);
static int apply_cooperative_attention(dtesn_cognitive_system_t *system);
static int normalize_attention_weights(dtesn_cognitive_system_t *system);
static int update_focus_history(dtesn_cognitive_system_t *system, uint32_t prev_channel_id, 
                               uint64_t switch_time);
static float compute_attention_efficiency(const dtesn_cognitive_system_t *system);
static int apply_attention_decay(dtesn_cognitive_system_t *system);

/**
 * Get current time in nanoseconds
 */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Validate system pointer and state
 */
static int validate_system(const dtesn_cognitive_system_t *system) {
    if (!system) {
        return -EINVAL;
    }
    
    if (!system->initialized) {
        return -ENODEV;
    }
    
    if (!system->attention_channels || system->num_attention_channels == 0) {
        return -EINVAL;
    }
    
    return 0;
}

/**
 * Validate channel ID
 */
static int validate_channel_id(const dtesn_cognitive_system_t *system, uint32_t channel_id) {
    if (channel_id >= system->num_attention_channels) {
        return -EINVAL;
    }
    
    return 0;
}

/**
 * Compute saliency score for attention focus
 */
static float compute_saliency_score(const float *input_data, uint32_t size) {
    if (!input_data || size == 0) {
        return 0.0f;
    }
    
    float mean = 0.0f;
    float variance = 0.0f;
    float max_val = input_data[0];
    
    /* Compute statistics */
    for (uint32_t i = 0; i < size; i++) {
        mean += input_data[i];
        if (input_data[i] > max_val) {
            max_val = input_data[i];
        }
    }
    mean /= size;
    
    for (uint32_t i = 0; i < size; i++) {
        float diff = input_data[i] - mean;
        variance += diff * diff;
    }
    variance /= size;
    
    /* Saliency based on variance (novelty) and maximum activation */
    float saliency = (0.6f * sqrtf(variance) + 0.4f * max_val);
    
    return fmaxf(0.0f, fminf(1.0f, saliency));
}

/**
 * Apply bottom-up attention mechanism
 */
static int apply_bottom_up_attention(dtesn_cognitive_system_t *system, uint32_t channel_id) {
    dtesn_cognitive_attention_channel_t *channel = &system->attention_channels[channel_id];
    
    /* Bottom-up attention is stimulus-driven */
    if (system->reservoir && system->reservoir->u_current) {
        uint32_t input_size = system->reservoir->config.input_size;
        float saliency = compute_saliency_score(system->reservoir->u_current, input_size);
        
        /* Increase channel weight based on input saliency */
        channel->weight = fminf(1.0f, channel->weight + 0.1f * saliency);
    }
    
    channel->type = DTESN_COGNITIVE_ATTENTION_BOTTOM_UP;
    return 0;
}

/**
 * Apply top-down attention mechanism
 */
static int apply_top_down_attention(dtesn_cognitive_system_t *system, uint32_t channel_id,
                                   const float *focus_vector, uint32_t focus_size) {
    dtesn_cognitive_attention_channel_t *channel = &system->attention_channels[channel_id];
    
    /* Allocate or reallocate focus vector */
    if (channel->focus_vector && channel->focus_size != focus_size) {
        free(channel->focus_vector);
        channel->focus_vector = NULL;
    }
    
    if (!channel->focus_vector) {
        channel->focus_vector = malloc(focus_size * sizeof(float));
        if (!channel->focus_vector) {
            return -ENOMEM;
        }
        channel->focus_size = focus_size;
    }
    
    /* Copy focus vector if provided, otherwise use default pattern */
    if (focus_vector) {
        memcpy(channel->focus_vector, focus_vector, focus_size * sizeof(float));
    } else {
        /* Default top-down pattern - gaussian-like distribution */
        float center = focus_size / 2.0f;
        float sigma = focus_size / 6.0f;
        
        for (uint32_t i = 0; i < focus_size; i++) {
            float x = (float)i - center;
            channel->focus_vector[i] = expf(-x * x / (2.0f * sigma * sigma));
        }
    }
    
    /* Top-down attention uses goal-driven focus */
    channel->weight = fminf(1.0f, channel->weight + 0.2f);
    channel->type = DTESN_COGNITIVE_ATTENTION_TOP_DOWN;
    
    return 0;
}

/**
 * Apply competitive attention mechanism
 */
static int apply_competitive_attention(dtesn_cognitive_system_t *system) {
    uint32_t winner_channel = 0;
    float max_weight = 0.0f;
    
    /* Find channel with maximum weight (winner-take-all) */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        if (system->attention_channels[i].weight > max_weight) {
            max_weight = system->attention_channels[i].weight;
            winner_channel = i;
        }
    }
    
    /* Suppress non-winning channels */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        if (i == winner_channel) {
            system->attention_channels[i].weight = 1.0f;
            system->attention_channels[i].active = true;
            system->attention_channels[i].type = DTESN_COGNITIVE_ATTENTION_COMPETITIVE;
        } else {
            /* Competitive suppression */
            system->attention_channels[i].weight *= (1.0f - DTESN_ATTENTION_COMPETITIVE_THRESHOLD);
            system->attention_channels[i].active = false;
        }
    }
    
    system->active_channel_id = winner_channel;
    
    return 0;
}

/**
 * Apply cooperative attention mechanism
 */
static int apply_cooperative_attention(dtesn_cognitive_system_t *system) {
    float total_weight = 0.0f;
    
    /* Compute total weight */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        total_weight += system->attention_channels[i].weight;
    }
    
    if (total_weight <= 0.0f) {
        return -EINVAL;
    }
    
    /* Normalize weights cooperatively */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        float normalized_weight = system->attention_channels[i].weight / total_weight;
        
        /* Cooperative boost for active channels */
        if (normalized_weight > DTESN_ATTENTION_MIN_WEIGHT) {
            system->attention_channels[i].weight = normalized_weight * DTESN_ATTENTION_COOPERATIVE_WEIGHT;
            system->attention_channels[i].active = true;
        } else {
            system->attention_channels[i].weight = DTESN_ATTENTION_MIN_WEIGHT;
            system->attention_channels[i].active = false;
        }
        
        system->attention_channels[i].type = DTESN_COGNITIVE_ATTENTION_COOPERATIVE;
    }
    
    /* Set active channel to the one with highest cooperative weight */
    uint32_t active_channel = 0;
    float max_weight = system->attention_channels[0].weight;
    
    for (uint32_t i = 1; i < system->num_attention_channels; i++) {
        if (system->attention_channels[i].weight > max_weight) {
            max_weight = system->attention_channels[i].weight;
            active_channel = i;
        }
    }
    
    system->active_channel_id = active_channel;
    
    return 0;
}

/**
 * Normalize attention weights to sum to 1.0
 */
static int normalize_attention_weights(dtesn_cognitive_system_t *system) {
    float total_weight = 0.0f;
    
    /* Compute total weight */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        total_weight += system->attention_channels[i].weight;
    }
    
    if (total_weight <= 0.0f) {
        /* Equal distribution if all weights are zero */
        float equal_weight = 1.0f / system->num_attention_channels;
        for (uint32_t i = 0; i < system->num_attention_channels; i++) {
            system->attention_channels[i].weight = equal_weight;
        }
    } else {
        /* Normalize to sum to 1.0 */
        for (uint32_t i = 0; i < system->num_attention_channels; i++) {
            system->attention_channels[i].weight /= total_weight;
        }
    }
    
    return 0;
}

/**
 * Update focus history tracking
 */
static int update_focus_history(dtesn_cognitive_system_t *system, uint32_t prev_channel_id,
                               uint64_t switch_time) {
    /* This would maintain a history of attention focus changes */
    /* For now, we just update the switch timestamp */
    if (prev_channel_id < system->num_attention_channels) {
        system->attention_channels[prev_channel_id].switch_time_ns = switch_time;
    }
    
    return 0;
}

/**
 * Compute attention efficiency metric
 */
static float compute_attention_efficiency(const dtesn_cognitive_system_t *system) {
    float entropy = 0.0f;
    
    /* Compute attention entropy (lower entropy = more focused) */
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        float weight = system->attention_channels[i].weight;
        if (weight > DTESN_ATTENTION_MIN_WEIGHT) {
            entropy -= weight * log2f(weight);
        }
    }
    
    /* Efficiency is inverse of entropy (more focused = higher efficiency) */
    float max_entropy = log2f((float)system->num_attention_channels);
    float efficiency = 1.0f - (entropy / max_entropy);
    
    return fmaxf(0.0f, fminf(1.0f, efficiency));
}

/**
 * Apply temporal decay to attention weights
 */
static int apply_attention_decay(dtesn_cognitive_system_t *system) {
    uint64_t current_time = get_time_ns();
    
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        dtesn_cognitive_attention_channel_t *channel = &system->attention_channels[i];
        
        /* Apply exponential decay based on time since last update */
        uint64_t time_since_update = current_time - channel->switch_time_ns;
        float decay_seconds = time_since_update / 1000000000.0f;
        float decay_factor = expf(-decay_seconds * (1.0f - DTESN_ATTENTION_DECAY_RATE));
        
        channel->weight *= decay_factor;
        
        /* Ensure minimum weight */
        if (channel->weight < DTESN_ATTENTION_MIN_WEIGHT) {
            channel->weight = DTESN_ATTENTION_MIN_WEIGHT;
        }
    }
    
    return 0;
}

/**
 * Focus attention on specific input channel
 */
int dtesn_attention_focus(dtesn_cognitive_system_t *system,
                         uint32_t channel_id,
                         const float *focus_vector,
                         uint32_t focus_size) {
    int result;
    uint64_t start_time, end_time;
    uint32_t prev_channel_id;
    
    result = validate_system(system);
    if (result != 0) {
        return result;
    }
    
    result = validate_channel_id(system, channel_id);
    if (result != 0) {
        return result;
    }
    
    start_time = get_time_ns();
    
    pthread_mutex_lock(&system->attention_lock);
    
    prev_channel_id = system->active_channel_id;
    
    /* Apply temporal decay to existing attention weights */
    apply_attention_decay(system);
    
    /* Determine attention strategy based on channel type */
    dtesn_cognitive_attention_channel_t *channel = &system->attention_channels[channel_id];
    
    switch (channel->type) {
        case DTESN_COGNITIVE_ATTENTION_BOTTOM_UP:
            result = apply_bottom_up_attention(system, channel_id);
            break;
        case DTESN_COGNITIVE_ATTENTION_TOP_DOWN:
            result = apply_top_down_attention(system, channel_id, focus_vector, focus_size);
            break;
        case DTESN_COGNITIVE_ATTENTION_COMPETITIVE:
            result = apply_competitive_attention(system);
            break;
        case DTESN_COGNITIVE_ATTENTION_COOPERATIVE:
            result = apply_cooperative_attention(system);
            break;
        default:
            /* Default to top-down attention */
            result = apply_top_down_attention(system, channel_id, focus_vector, focus_size);
            break;
    }
    
    if (result == 0) {
        /* Update active channel */
        system->active_channel_id = channel_id;
        channel->active = true;
        channel->switch_time_ns = get_time_ns();
        
        /* Update focus history */
        update_focus_history(system, prev_channel_id, channel->switch_time_ns);
    }
    
    end_time = get_time_ns();
    
    /* Update performance statistics */
    if (result == 0) {
        system->total_attention_switches++;
        system->total_attention_switch_time_ns += (end_time - start_time);
        
        /* Check performance target: ≤10ms */
        uint64_t switch_time_us = (end_time - start_time) / 1000;
        if (switch_time_us > DTESN_COGNITIVE_ATTENTION_SWITCH_US) {
            printf("Warning: Attention switch took %lu μs (target: ≤%u μs)\n",
                   (unsigned long)switch_time_us, DTESN_COGNITIVE_ATTENTION_SWITCH_US);
        }
    }
    
    pthread_mutex_unlock(&system->attention_lock);
    
    if (result == 0) {
        printf("Attention focused on channel %u (%.2f μs, efficiency: %.2f)\n",
               channel_id, (end_time - start_time) / 1000.0,
               compute_attention_efficiency(system));
    }
    
    return result;
}

/**
 * Distribute attention across channels
 */
int dtesn_attention_distribute(dtesn_cognitive_system_t *system,
                              const float *weights,
                              uint32_t num_weights) {
    int result;
    uint64_t start_time, end_time;
    float weight_sum = 0.0f;
    
    result = validate_system(system);
    if (result != 0) {
        return result;
    }
    
    if (!weights || num_weights != system->num_attention_channels) {
        return -EINVAL;
    }
    
    /* Validate weight sum (should be close to 1.0) */
    for (uint32_t i = 0; i < num_weights; i++) {
        if (weights[i] < 0.0f || weights[i] > 1.0f) {
            return -EINVAL;
        }
        weight_sum += weights[i];
    }
    
    if (fabsf(weight_sum - 1.0f) > 0.01f) {
        return -EINVAL; /* Weights must sum to approximately 1.0 */
    }
    
    start_time = get_time_ns();
    
    pthread_mutex_lock(&system->attention_lock);
    
    /* Apply temporal decay first */
    apply_attention_decay(system);
    
    /* Distribute attention weights */
    uint32_t active_channel = 0;
    float max_weight = 0.0f;
    
    for (uint32_t i = 0; i < system->num_attention_channels; i++) {
        system->attention_channels[i].weight = weights[i];
        system->attention_channels[i].active = (weights[i] > DTESN_ATTENTION_MIN_WEIGHT);
        system->attention_channels[i].switch_time_ns = get_time_ns();
        
        /* Find channel with maximum weight for primary focus */
        if (weights[i] > max_weight) {
            max_weight = weights[i];
            active_channel = i;
        }
    }
    
    /* Set primary active channel */
    system->active_channel_id = active_channel;
    
    /* Apply cooperative attention mechanism */
    result = apply_cooperative_attention(system);
    
    end_time = get_time_ns();
    
    /* Update performance statistics */
    if (result == 0) {
        system->total_attention_switches++;
        system->total_attention_switch_time_ns += (end_time - start_time);
    }
    
    pthread_mutex_unlock(&system->attention_lock);
    
    if (result == 0) {
        printf("Attention distributed across %u channels (primary: %u, %.2f μs)\n",
               system->num_attention_channels, active_channel,
               (end_time - start_time) / 1000.0);
    }
    
    return result;
}