/*
 * DTESN Multi-Modal Fusion Implementation
 * ======================================
 * 
 * Multi-modal sensory input processing and fusion strategies including
 * early, late, hierarchical, and adaptive fusion with cross-modal
 * learning and attention-weighted integration.
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
#define DTESN_FUSION_CONFIDENCE_THRESHOLD       0.5f    /* Minimum confidence for fusion */
#define DTESN_FUSION_TEMPORAL_WINDOW_MS         100     /* Temporal alignment window */
#define DTESN_FUSION_CORRELATION_THRESHOLD      0.3f    /* Cross-modal correlation threshold */
#define DTESN_FUSION_DEFAULT_OUTPUT_SIZE        512     /* Default fused representation size */
#define DTESN_FUSION_ATTENTION_WEIGHT           0.8f    /* Attention modulation weight */

/* Cross-modal correlation matrix */
typedef struct cross_modal_correlation {
    uint32_t modality_a;
    uint32_t modality_b;
    float correlation_strength;
    uint64_t last_update_ns;
} cross_modal_correlation_t;

/* Forward declarations */
static uint64_t get_time_ns(void);
static int validate_system(const dtesn_cognitive_system_t *system);
static int validate_modality_data(const dtesn_cognitive_modality_data_t *data, uint32_t count);
static int perform_early_fusion(dtesn_cognitive_system_t *system,
                               const dtesn_cognitive_modality_data_t *input_data,
                               uint32_t num_modalities, float *output, uint32_t output_size);
static int perform_late_fusion(dtesn_cognitive_system_t *system,
                              const dtesn_cognitive_modality_data_t *input_data,
                              uint32_t num_modalities, float *output, uint32_t output_size);
static int perform_hierarchical_fusion(dtesn_cognitive_system_t *system,
                                      const dtesn_cognitive_modality_data_t *input_data,
                                      uint32_t num_modalities, float *output, uint32_t output_size);
static int perform_adaptive_fusion(dtesn_cognitive_system_t *system,
                                  const dtesn_cognitive_modality_data_t *input_data,
                                  uint32_t num_modalities, float *output, uint32_t output_size);
static float compute_modality_reliability(const dtesn_cognitive_modality_data_t *modality);
static float compute_cross_modal_correlation(const dtesn_cognitive_modality_data_t *mod_a,
                                           const dtesn_cognitive_modality_data_t *mod_b);
static int apply_attention_modulation(dtesn_cognitive_system_t *system,
                                     const dtesn_cognitive_modality_data_t *input_data,
                                     uint32_t num_modalities, float *attention_weights);
static int normalize_fusion_output(float *output, uint32_t size);
static int temporal_alignment(const dtesn_cognitive_modality_data_t *input_data,
                             uint32_t num_modalities, uint64_t *reference_time);
static float compute_fusion_confidence(const dtesn_cognitive_modality_data_t *input_data,
                                      uint32_t num_modalities, const float *fusion_weights);

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
    
    return 0;
}

/**
 * Validate modality data array
 */
static int validate_modality_data(const dtesn_cognitive_modality_data_t *data, uint32_t count) {
    if (!data || count == 0) {
        return -EINVAL;
    }
    
    for (uint32_t i = 0; i < count; i++) {
        if (!data[i].data || data[i].data_size == 0) {
            return -EINVAL;
        }
        
        if (!data[i].valid) {
            return -EINVAL;
        }
        
        if (data[i].confidence < 0.0f || data[i].confidence > 1.0f) {
            return -EINVAL;
        }
    }
    
    return 0;
}

/**
 * Perform early fusion (feature-level integration)
 */
static int perform_early_fusion(dtesn_cognitive_system_t *system,
                               const dtesn_cognitive_modality_data_t *input_data,
                               uint32_t num_modalities, float *output, uint32_t output_size) {
    /* Early fusion concatenates features from all modalities */
    uint32_t total_input_size = 0;
    uint32_t output_idx = 0;
    
    /* Calculate total input size */
    for (uint32_t i = 0; i < num_modalities; i++) {
        total_input_size += input_data[i].data_size;
    }
    
    if (total_input_size > output_size) {
        /* Need to compress features */
        float compression_ratio = (float)output_size / total_input_size;
        
        for (uint32_t i = 0; i < num_modalities && output_idx < output_size; i++) {
            uint32_t modality_output_size = (uint32_t)(input_data[i].data_size * compression_ratio);
            
            /* Simple downsampling */
            for (uint32_t j = 0; j < modality_output_size && output_idx < output_size; j++) {
                uint32_t input_idx = (j * input_data[i].data_size) / modality_output_size;
                output[output_idx++] = input_data[i].data[input_idx] * input_data[i].confidence;
            }
        }
    } else {
        /* Direct concatenation */
        for (uint32_t i = 0; i < num_modalities && output_idx < output_size; i++) {
            for (uint32_t j = 0; j < input_data[i].data_size && output_idx < output_size; j++) {
                output[output_idx++] = input_data[i].data[j] * input_data[i].confidence;
            }
        }
    }
    
    /* Zero-pad remaining output */
    while (output_idx < output_size) {
        output[output_idx++] = 0.0f;
    }
    
    return normalize_fusion_output(output, output_size);
}

/**
 * Perform late fusion (decision-level integration)
 */
static int perform_late_fusion(dtesn_cognitive_system_t *system,
                              const dtesn_cognitive_modality_data_t *input_data,
                              uint32_t num_modalities, float *output, uint32_t output_size) {
    /* Late fusion processes each modality separately, then combines decisions */
    float *modality_outputs = malloc(num_modalities * output_size * sizeof(float));
    float *fusion_weights = malloc(num_modalities * sizeof(float));
    
    if (!modality_outputs || !fusion_weights) {
        free(modality_outputs);
        free(fusion_weights);
        return -ENOMEM;
    }
    
    /* Process each modality independently */
    for (uint32_t i = 0; i < num_modalities; i++) {
        float *mod_output = &modality_outputs[i * output_size];
        
        /* Simple processing: normalize and pad/truncate to output size */
        uint32_t copy_size = (input_data[i].data_size < output_size) ? 
                            input_data[i].data_size : output_size;
        
        for (uint32_t j = 0; j < copy_size; j++) {
            mod_output[j] = input_data[i].data[j];
        }
        
        /* Zero-pad if needed */
        for (uint32_t j = copy_size; j < output_size; j++) {
            mod_output[j] = 0.0f;
        }
        
        /* Normalize modality output */
        normalize_fusion_output(mod_output, output_size);
        
        /* Compute fusion weight based on reliability */
        fusion_weights[i] = compute_modality_reliability(&input_data[i]);
    }
    
    /* Normalize fusion weights */
    float weight_sum = 0.0f;
    for (uint32_t i = 0; i < num_modalities; i++) {
        weight_sum += fusion_weights[i];
    }
    
    if (weight_sum > 0.0f) {
        for (uint32_t i = 0; i < num_modalities; i++) {
            fusion_weights[i] /= weight_sum;
        }
    } else {
        /* Equal weighting if all weights are zero */
        for (uint32_t i = 0; i < num_modalities; i++) {
            fusion_weights[i] = 1.0f / num_modalities;
        }
    }
    
    /* Weighted combination of modality outputs */
    memset(output, 0, output_size * sizeof(float));
    for (uint32_t i = 0; i < num_modalities; i++) {
        float *mod_output = &modality_outputs[i * output_size];
        for (uint32_t j = 0; j < output_size; j++) {
            output[j] += fusion_weights[i] * mod_output[j];
        }
    }
    
    free(modality_outputs);
    free(fusion_weights);
    
    return 0;
}

/**
 * Perform hierarchical fusion (multi-stage integration)
 */
static int perform_hierarchical_fusion(dtesn_cognitive_system_t *system,
                                      const dtesn_cognitive_modality_data_t *input_data,
                                      uint32_t num_modalities, float *output, uint32_t output_size) {
    /* Hierarchical fusion combines modalities in stages */
    if (num_modalities < 2) {
        /* Fall back to early fusion for single modality */
        return perform_early_fusion(system, input_data, num_modalities, output, output_size);
    }
    
    /* Stage 1: Combine pairs of modalities */
    uint32_t stage1_size = (num_modalities + 1) / 2;
    dtesn_cognitive_modality_data_t *stage1_data = malloc(stage1_size * sizeof(dtesn_cognitive_modality_data_t));
    
    if (!stage1_data) {
        return -ENOMEM;
    }
    
    for (uint32_t i = 0; i < stage1_size; i++) {
        uint32_t mod_a = i * 2;
        uint32_t mod_b = (i * 2 + 1 < num_modalities) ? i * 2 + 1 : mod_a;
        
        /* Combine pair of modalities */
        uint32_t combined_size = input_data[mod_a].data_size + 
                               (mod_b != mod_a ? input_data[mod_b].data_size : 0);
        
        stage1_data[i].modality_id = i;
        stage1_data[i].data = malloc(combined_size * sizeof(float));
        stage1_data[i].data_size = combined_size;
        
        if (!stage1_data[i].data) {
            /* Cleanup and return error */
            for (uint32_t j = 0; j < i; j++) {
                free(stage1_data[j].data);
            }
            free(stage1_data);
            return -ENOMEM;
        }
        
        /* Copy data from both modalities */
        memcpy(stage1_data[i].data, input_data[mod_a].data, 
               input_data[mod_a].data_size * sizeof(float));
        
        if (mod_b != mod_a) {
            memcpy(&stage1_data[i].data[input_data[mod_a].data_size],
                   input_data[mod_b].data, 
                   input_data[mod_b].data_size * sizeof(float));
        }
        
        /* Combine confidence scores */
        stage1_data[i].confidence = (input_data[mod_a].confidence + 
                                   (mod_b != mod_a ? input_data[mod_b].confidence : 0.0f)) / 
                                   (mod_b != mod_a ? 2.0f : 1.0f);
        
        stage1_data[i].valid = true;
        stage1_data[i].timestamp_ns = fmaxf(input_data[mod_a].timestamp_ns,
                                          mod_b != mod_a ? input_data[mod_b].timestamp_ns : 0);
    }
    
    /* Stage 2: Perform late fusion on combined modalities */
    int result = perform_late_fusion(system, stage1_data, stage1_size, output, output_size);
    
    /* Cleanup stage 1 data */
    for (uint32_t i = 0; i < stage1_size; i++) {
        free(stage1_data[i].data);
    }
    free(stage1_data);
    
    return result;
}

/**
 * Perform adaptive fusion (strategy selection based on context)
 */
static int perform_adaptive_fusion(dtesn_cognitive_system_t *system,
                                  const dtesn_cognitive_modality_data_t *input_data,
                                  uint32_t num_modalities, float *output, uint32_t output_size) {
    /* Adaptive fusion selects strategy based on modality characteristics */
    float avg_confidence = 0.0f;
    float confidence_variance = 0.0f;
    bool temporal_coherence = true;
    uint64_t reference_time = input_data[0].timestamp_ns;
    
    /* Analyze modality characteristics */
    for (uint32_t i = 0; i < num_modalities; i++) {
        avg_confidence += input_data[i].confidence;
        
        /* Check temporal coherence */
        uint64_t time_diff = (input_data[i].timestamp_ns > reference_time) ?
                           input_data[i].timestamp_ns - reference_time :
                           reference_time - input_data[i].timestamp_ns;
        
        if (time_diff > DTESN_FUSION_TEMPORAL_WINDOW_MS * 1000000ULL) {
            temporal_coherence = false;
        }
    }
    
    avg_confidence /= num_modalities;
    
    /* Compute confidence variance */
    for (uint32_t i = 0; i < num_modalities; i++) {
        float diff = input_data[i].confidence - avg_confidence;
        confidence_variance += diff * diff;
    }
    confidence_variance /= num_modalities;
    
    /* Select fusion strategy based on analysis */
    if (avg_confidence > 0.8f && confidence_variance < 0.1f && temporal_coherence) {
        /* High confidence, low variance, good temporal alignment -> Early fusion */
        printf("Adaptive fusion: Selected early fusion (high confidence, coherent)\n");
        return perform_early_fusion(system, input_data, num_modalities, output, output_size);
    } else if (confidence_variance > 0.3f) {
        /* High variance in confidence -> Late fusion */
        printf("Adaptive fusion: Selected late fusion (high confidence variance)\n");
        return perform_late_fusion(system, input_data, num_modalities, output, output_size);
    } else if (num_modalities > 2 && !temporal_coherence) {
        /* Multiple modalities with poor temporal alignment -> Hierarchical fusion */
        printf("Adaptive fusion: Selected hierarchical fusion (multiple modalities, poor alignment)\n");
        return perform_hierarchical_fusion(system, input_data, num_modalities, output, output_size);
    } else {
        /* Default to early fusion */
        printf("Adaptive fusion: Selected early fusion (default)\n");
        return perform_early_fusion(system, input_data, num_modalities, output, output_size);
    }
}

/**
 * Compute modality reliability score
 */
static float compute_modality_reliability(const dtesn_cognitive_modality_data_t *modality) {
    if (!modality || !modality->valid) {
        return 0.0f;
    }
    
    /* Reliability based on confidence and data characteristics */
    float confidence_factor = modality->confidence;
    
    /* Data quality factor based on signal characteristics */
    float signal_energy = 0.0f;
    float signal_variance = 0.0f;
    float signal_mean = 0.0f;
    
    for (uint32_t i = 0; i < modality->data_size; i++) {
        signal_mean += modality->data[i];
        signal_energy += modality->data[i] * modality->data[i];
    }
    
    signal_mean /= modality->data_size;
    signal_energy /= modality->data_size;
    
    for (uint32_t i = 0; i < modality->data_size; i++) {
        float diff = modality->data[i] - signal_mean;
        signal_variance += diff * diff;
    }
    signal_variance /= modality->data_size;
    
    /* Higher variance and energy indicate more informative signal */
    float quality_factor = sqrtf(signal_variance) * sqrtf(signal_energy);
    quality_factor = fmaxf(0.0f, fminf(1.0f, quality_factor));
    
    /* Temporal freshness factor */
    uint64_t current_time = get_time_ns();
    uint64_t age_ns = current_time - modality->timestamp_ns;
    float age_seconds = age_ns / 1000000000.0f;
    float freshness_factor = expf(-age_seconds / 10.0f); /* Decay over 10 seconds */
    
    /* Combined reliability score */
    float reliability = confidence_factor * 0.5f + quality_factor * 0.3f + freshness_factor * 0.2f;
    
    return fmaxf(0.0f, fminf(1.0f, reliability));
}

/**
 * Compute cross-modal correlation
 */
static float compute_cross_modal_correlation(const dtesn_cognitive_modality_data_t *mod_a,
                                           const dtesn_cognitive_modality_data_t *mod_b) {
    if (!mod_a || !mod_b || !mod_a->valid || !mod_b->valid) {
        return 0.0f;
    }
    
    /* Compute correlation between modality signals */
    uint32_t min_size = (mod_a->data_size < mod_b->data_size) ? 
                       mod_a->data_size : mod_b->data_size;
    
    if (min_size == 0) {
        return 0.0f;
    }
    
    float mean_a = 0.0f, mean_b = 0.0f;
    for (uint32_t i = 0; i < min_size; i++) {
        mean_a += mod_a->data[i];
        mean_b += mod_b->data[i];
    }
    mean_a /= min_size;
    mean_b /= min_size;
    
    float covariance = 0.0f;
    float var_a = 0.0f, var_b = 0.0f;
    
    for (uint32_t i = 0; i < min_size; i++) {
        float diff_a = mod_a->data[i] - mean_a;
        float diff_b = mod_b->data[i] - mean_b;
        covariance += diff_a * diff_b;
        var_a += diff_a * diff_a;
        var_b += diff_b * diff_b;
    }
    
    float denom = sqrtf(var_a * var_b);
    if (denom > 0.0f) {
        return covariance / denom;
    }
    
    return 0.0f;
}

/**
 * Apply attention modulation to fusion
 */
static int apply_attention_modulation(dtesn_cognitive_system_t *system,
                                     const dtesn_cognitive_modality_data_t *input_data,
                                     uint32_t num_modalities, float *attention_weights) {
    /* Use attention system to weight modalities */
    if (system->attention_channels && system->num_attention_channels > 0) {
        uint32_t active_channel = system->active_channel_id;
        
        if (active_channel < system->num_attention_channels) {
            float attention_boost = system->attention_channels[active_channel].weight;
            
            /* Modulate fusion weights based on attention */
            for (uint32_t i = 0; i < num_modalities; i++) {
                if (i < system->num_attention_channels) {
                    attention_weights[i] *= (1.0f + DTESN_FUSION_ATTENTION_WEIGHT * 
                                           system->attention_channels[i].weight);
                }
            }
        }
    }
    
    return 0;
}

/**
 * Normalize fusion output
 */
static int normalize_fusion_output(float *output, uint32_t size) {
    if (!output || size == 0) {
        return -EINVAL;
    }
    
    /* Compute output statistics */
    float mean = 0.0f;
    float max_val = fabsf(output[0]);
    
    for (uint32_t i = 0; i < size; i++) {
        mean += output[i];
        if (fabsf(output[i]) > max_val) {
            max_val = fabsf(output[i]);
        }
    }
    mean /= size;
    
    /* Normalize to [-1, 1] range */
    if (max_val > 0.0f) {
        for (uint32_t i = 0; i < size; i++) {
            output[i] /= max_val;
        }
    }
    
    return 0;
}

/**
 * Temporal alignment check
 */
static int temporal_alignment(const dtesn_cognitive_modality_data_t *input_data,
                             uint32_t num_modalities, uint64_t *reference_time) {
    if (!input_data || num_modalities == 0 || !reference_time) {
        return -EINVAL;
    }
    
    *reference_time = input_data[0].timestamp_ns;
    
    /* Check if all modalities are within temporal window */
    for (uint32_t i = 1; i < num_modalities; i++) {
        uint64_t time_diff = (input_data[i].timestamp_ns > *reference_time) ?
                           input_data[i].timestamp_ns - *reference_time :
                           *reference_time - input_data[i].timestamp_ns;
        
        if (time_diff > DTESN_FUSION_TEMPORAL_WINDOW_MS * 1000000ULL) {
            return -ETIME; /* Temporal misalignment */
        }
    }
    
    return 0;
}

/**
 * Compute fusion confidence
 */
static float compute_fusion_confidence(const dtesn_cognitive_modality_data_t *input_data,
                                      uint32_t num_modalities, const float *fusion_weights) {
    if (!input_data || num_modalities == 0) {
        return 0.0f;
    }
    
    float weighted_confidence = 0.0f;
    float weight_sum = 0.0f;
    
    for (uint32_t i = 0; i < num_modalities; i++) {
        float weight = fusion_weights ? fusion_weights[i] : (1.0f / num_modalities);
        weighted_confidence += weight * input_data[i].confidence;
        weight_sum += weight;
    }
    
    if (weight_sum > 0.0f) {
        weighted_confidence /= weight_sum;
    }
    
    /* Boost confidence for multi-modal agreement */
    if (num_modalities > 1) {
        weighted_confidence *= (1.0f + 0.1f * (num_modalities - 1));
        weighted_confidence = fminf(1.0f, weighted_confidence);
    }
    
    return weighted_confidence;
}

/**
 * Fuse multi-modal sensory input
 */
int dtesn_multimodal_fuse(dtesn_cognitive_system_t *system,
                         const dtesn_cognitive_modality_data_t *input_data,
                         uint32_t num_modalities,
                         dtesn_cognitive_fusion_type_t fusion_type,
                         float *output,
                         uint32_t output_size) {
    int result;
    uint64_t start_time, end_time;
    uint64_t reference_time;
    
    result = validate_system(system);
    if (result != 0) {
        return result;
    }
    
    result = validate_modality_data(input_data, num_modalities);
    if (result != 0) {
        return result;
    }
    
    if (!output || output_size == 0) {
        return -EINVAL;
    }
    
    start_time = get_time_ns();
    
    /* Check temporal alignment */
    result = temporal_alignment(input_data, num_modalities, &reference_time);
    if (result == -ETIME) {
        printf("Warning: Temporal misalignment detected in modalities\n");
        /* Continue with fusion despite misalignment */
    }
    
    /* Apply selected fusion strategy */
    switch (fusion_type) {
        case DTESN_COGNITIVE_FUSION_EARLY:
            result = perform_early_fusion(system, input_data, num_modalities, output, output_size);
            break;
        case DTESN_COGNITIVE_FUSION_LATE:
            result = perform_late_fusion(system, input_data, num_modalities, output, output_size);
            break;
        case DTESN_COGNITIVE_FUSION_HIERARCHICAL:
            result = perform_hierarchical_fusion(system, input_data, num_modalities, output, output_size);
            break;
        case DTESN_COGNITIVE_FUSION_ADAPTIVE:
            result = perform_adaptive_fusion(system, input_data, num_modalities, output, output_size);
            break;
        default:
            result = -EINVAL;
            break;
    }
    
    end_time = get_time_ns();
    
    if (result == 0) {
        /* Compute and store fusion confidence */
        float fusion_confidence = compute_fusion_confidence(input_data, num_modalities, NULL);
        
        /* Update system's fused representation if successful */
        if (system->fused_representation && system->fused_size >= output_size) {
            memcpy(system->fused_representation, output, output_size * sizeof(float));
        }
        
        printf("Multi-modal fusion completed: %u modalities, confidence %.2f (%.2f ms)\n",
               num_modalities, fusion_confidence, (end_time - start_time) / 1000000.0);
    }
    
    return result;
}