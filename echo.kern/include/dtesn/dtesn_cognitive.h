/*
 * DTESN Advanced Cognitive Computing Module
 * =========================================
 * 
 * Deep Tree Echo State Networks (DTESN) cognitive computing implementation
 * providing adaptive learning, memory consolidation, attention mechanisms,
 * multi-modal fusion, and distributed processing for neuromorphic systems.
 * 
 * Performance Requirements:
 * - Learning convergence: ≤ 1000 iterations
 * - Memory consolidation: ≤ 100ms
 * - Attention switching: ≤ 10ms
 * - State persistence: ≤ 50ms
 * 
 * Cognitive Architecture:
 * - Online learning and adaptation for ESN reservoirs
 * - Working memory management with temporal dynamics
 * - Attention and focus mechanisms with priority queuing
 * - Memory consolidation algorithms for long-term storage
 * - Multi-modal sensor fusion with cross-modal learning
 * - Distributed cognition protocols for node coordination
 * - OEIS A000081 compliant cognitive topology
 */

#ifndef DTESN_COGNITIVE_H
#define DTESN_COGNITIVE_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>
#include "esn.h"
#include "memory.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Cognitive configuration constants */
#define DTESN_COGNITIVE_MAX_LEARNING_ITERATIONS     1000    /* ≤ 1000 iterations */
#define DTESN_COGNITIVE_MAX_MEMORY_NODES           10000    /* Maximum working memory nodes */
#define DTESN_COGNITIVE_MAX_ATTENTION_CHANNELS        64    /* Maximum attention channels */
#define DTESN_COGNITIVE_MAX_MODALITIES                 8    /* Maximum sensory modalities */
#define DTESN_COGNITIVE_MAX_DISTRIBUTED_NODES         32    /* Maximum distributed nodes */

/* Performance thresholds (microseconds) */
#define DTESN_COGNITIVE_LEARNING_CONVERGENCE_MAX    1000000 /* ≤ 1000 iterations */
#define DTESN_COGNITIVE_MEMORY_CONSOLIDATION_US      100000 /* ≤ 100ms */
#define DTESN_COGNITIVE_ATTENTION_SWITCH_US           10000 /* ≤ 10ms */
#define DTESN_COGNITIVE_STATE_PERSISTENCE_US          50000 /* ≤ 50ms */

/* OEIS A000081 sequence for cognitive topology validation */
#define DTESN_COGNITIVE_A000081_MAX_DEPTH 12
#define DTESN_COGNITIVE_A000081_SEQUENCE \
    { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766 }

/* Cognitive learning algorithms */
typedef enum {
    DTESN_COGNITIVE_LEARN_HEBBIAN = 0,      /* Hebbian learning rule */
    DTESN_COGNITIVE_LEARN_STDP = 1,         /* Spike-timing dependent plasticity */
    DTESN_COGNITIVE_LEARN_BCM = 2,          /* BCM (Bienenstock-Cooper-Munro) rule */
    DTESN_COGNITIVE_LEARN_RLRL = 3,         /* Reward-based reinforcement learning */
    DTESN_COGNITIVE_LEARN_ADAPTIVE = 4      /* Adaptive meta-learning */
} dtesn_cognitive_learn_type_t;

/* Memory consolidation types */
typedef enum {
    DTESN_COGNITIVE_CONSOLIDATE_IMMEDIATE = 0,  /* Immediate consolidation */
    DTESN_COGNITIVE_CONSOLIDATE_DELAYED = 1,    /* Delayed consolidation */
    DTESN_COGNITIVE_CONSOLIDATE_REPLAY = 2,     /* Experience replay */
    DTESN_COGNITIVE_CONSOLIDATE_ADAPTIVE = 3    /* Adaptive consolidation */
} dtesn_cognitive_consolidate_type_t;

/* Attention mechanism types */
typedef enum {
    DTESN_COGNITIVE_ATTENTION_BOTTOM_UP = 0,    /* Bottom-up attention */
    DTESN_COGNITIVE_ATTENTION_TOP_DOWN = 1,     /* Top-down attention */
    DTESN_COGNITIVE_ATTENTION_COMPETITIVE = 2,  /* Competitive attention */
    DTESN_COGNITIVE_ATTENTION_COOPERATIVE = 3   /* Cooperative attention */
} dtesn_cognitive_attention_type_t;

/* Multi-modal fusion strategies */
typedef enum {
    DTESN_COGNITIVE_FUSION_EARLY = 0,          /* Early fusion */
    DTESN_COGNITIVE_FUSION_LATE = 1,           /* Late fusion */
    DTESN_COGNITIVE_FUSION_HIERARCHICAL = 2,   /* Hierarchical fusion */
    DTESN_COGNITIVE_FUSION_ADAPTIVE = 3        /* Adaptive fusion */
} dtesn_cognitive_fusion_type_t;

/* Cognitive learning parameters */
typedef struct dtesn_cognitive_learn_params {
    dtesn_cognitive_learn_type_t learn_type;   /* Learning algorithm type */
    float learning_rate;                       /* Base learning rate (0.0-1.0) */
    float adaptation_rate;                     /* Adaptation rate (0.0-1.0) */
    uint32_t max_iterations;                   /* Maximum learning iterations */
    float convergence_threshold;               /* Convergence threshold */
    bool enable_plasticity;                    /* Enable synaptic plasticity */
    bool enable_homeostasis;                   /* Enable homeostatic regulation */
    uint32_t batch_size;                       /* Mini-batch size */
} dtesn_cognitive_learn_params_t;

/* Working memory node structure */
typedef struct dtesn_cognitive_memory_node {
    uint32_t node_id;                         /* Unique node identifier */
    char label[64];                           /* Human-readable label */
    float *data;                              /* Node data vector */
    uint32_t data_size;                       /* Data vector size */
    float activation;                         /* Current activation level */
    float decay_rate;                         /* Temporal decay rate */
    uint64_t timestamp_ns;                    /* Last update timestamp */
    uint32_t access_count;                    /* Access frequency counter */
    bool persistent;                          /* Persistence flag */
    struct dtesn_cognitive_memory_node *next; /* Linked list pointer */
} dtesn_cognitive_memory_node_t;

/* Attention channel structure */
typedef struct dtesn_cognitive_attention_channel {
    uint32_t channel_id;                      /* Channel identifier */
    dtesn_cognitive_attention_type_t type;    /* Attention type */
    float weight;                             /* Attention weight (0.0-1.0) */
    float *focus_vector;                      /* Focus vector */
    uint32_t focus_size;                      /* Focus vector size */
    uint64_t switch_time_ns;                  /* Last switch timestamp */
    bool active;                              /* Channel active flag */
} dtesn_cognitive_attention_channel_t;

/* Multi-modal sensor data */
typedef struct dtesn_cognitive_modality_data {
    uint32_t modality_id;                     /* Modality identifier */
    char name[32];                            /* Modality name */
    float *data;                              /* Sensor data vector */
    uint32_t data_size;                       /* Data vector size */
    float confidence;                         /* Data confidence (0.0-1.0) */
    uint64_t timestamp_ns;                    /* Data timestamp */
    bool valid;                               /* Data validity flag */
} dtesn_cognitive_modality_data_t;

/* Distributed node information */
typedef struct dtesn_cognitive_distributed_node {
    uint32_t node_id;                         /* Node identifier */
    uint32_t ip_address;                      /* Node IP address */
    uint16_t port;                            /* Node port */
    float computational_load;                 /* Current load (0.0-1.0) */
    float network_latency_ms;                 /* Network latency */
    bool online;                              /* Node online status */
    uint64_t last_sync_ns;                    /* Last synchronization time */
} dtesn_cognitive_distributed_node_t;

/* Main cognitive system structure */
typedef struct dtesn_cognitive_system {
    uint32_t system_id;                       /* System identifier */
    char name[64];                            /* Human-readable name */
    
    /* ESN reservoir integration */
    dtesn_esn_reservoir_t *reservoir;         /* Associated ESN reservoir */
    
    /* Working memory */
    dtesn_cognitive_memory_node_t *memory_head;  /* Working memory linked list */
    uint32_t memory_node_count;               /* Current memory nodes */
    pthread_mutex_t memory_lock;              /* Memory access lock */
    
    /* Attention system */
    dtesn_cognitive_attention_channel_t *attention_channels;  /* Attention channels */
    uint32_t num_attention_channels;          /* Number of channels */
    uint32_t active_channel_id;               /* Currently active channel */
    pthread_mutex_t attention_lock;           /* Attention access lock */
    
    /* Multi-modal fusion */
    dtesn_cognitive_modality_data_t *modalities;  /* Sensor modalities */
    uint32_t num_modalities;                  /* Number of modalities */
    dtesn_cognitive_fusion_type_t fusion_type;    /* Fusion strategy */
    float *fused_representation;              /* Fused multimodal data */
    uint32_t fused_size;                      /* Fused data size */
    
    /* Distributed processing */
    dtesn_cognitive_distributed_node_t *nodes;    /* Distributed nodes */
    uint32_t num_nodes;                       /* Number of nodes */
    pthread_mutex_t distributed_lock;         /* Distributed access lock */
    
    /* Performance monitoring */
    uint64_t total_learning_iterations;       /* Total learning iterations */
    uint64_t total_learning_time_ns;          /* Total learning time */
    uint64_t total_consolidations;            /* Total consolidations */
    uint64_t total_consolidation_time_ns;     /* Total consolidation time */
    uint64_t total_attention_switches;        /* Total attention switches */
    uint64_t total_attention_switch_time_ns;  /* Total switch time */
    uint64_t total_state_saves;               /* Total state saves */
    uint64_t total_state_save_time_ns;        /* Total save time */
    
    /* System state */
    bool initialized;                         /* Initialization flag */
    pthread_mutex_t system_lock;              /* System-wide lock */
    
} dtesn_cognitive_system_t;

/* Core cognitive functions */

/**
 * dtesn_cognitive_init - Initialize cognitive computing subsystem
 * 
 * Initializes the DTESN cognitive computing subsystem with default
 * configuration and allocates required resources.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_cognitive_init(void);

/**
 * dtesn_cognitive_cleanup - Cleanup cognitive computing subsystem
 * 
 * Cleans up the cognitive computing subsystem and frees all allocated
 * resources. Should be called during system shutdown.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_cognitive_cleanup(void);

/**
 * dtesn_cognitive_system_create - Create a new cognitive system
 * @name: Human-readable system name
 * @reservoir: Associated ESN reservoir
 * 
 * Creates a new cognitive system instance with the specified name
 * and associates it with an ESN reservoir for neural processing.
 * 
 * Returns: Pointer to cognitive system on success, NULL on failure
 */
dtesn_cognitive_system_t *dtesn_cognitive_system_create(const char *name,
                                                       dtesn_esn_reservoir_t *reservoir);

/**
 * dtesn_cognitive_system_destroy - Destroy a cognitive system
 * @system: Target cognitive system
 * 
 * Destroys a cognitive system and frees all associated resources.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_cognitive_system_destroy(dtesn_cognitive_system_t *system);

/* Adaptive learning functions */

/**
 * dtesn_adaptive_learn - Perform adaptive learning on ESN reservoir
 * @system: Target cognitive system
 * @input_data: Training input data
 * @target_data: Training target data
 * @num_samples: Number of training samples
 * @params: Learning parameters
 * 
 * Performs adaptive learning on the associated ESN reservoir using
 * the specified learning algorithm and parameters.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_adaptive_learn(dtesn_cognitive_system_t *system,
                        const float **input_data,
                        const float **target_data,
                        uint32_t num_samples,
                        const dtesn_cognitive_learn_params_t *params);

/**
 * dtesn_adaptive_learn_online - Perform online adaptive learning
 * @system: Target cognitive system
 * @input: Single input sample
 * @target: Single target sample
 * @params: Learning parameters
 * 
 * Performs online (incremental) adaptive learning with a single
 * input-target pair for real-time learning scenarios.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_adaptive_learn_online(dtesn_cognitive_system_t *system,
                               const float *input,
                               const float *target,
                               const dtesn_cognitive_learn_params_t *params);

/* Memory consolidation functions */

/**
 * dtesn_memory_consolidate - Consolidate working memory to long-term storage
 * @system: Target cognitive system
 * @consolidate_type: Type of consolidation to perform
 * 
 * Consolidates working memory contents to long-term storage using
 * the specified consolidation strategy.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_memory_consolidate(dtesn_cognitive_system_t *system,
                            dtesn_cognitive_consolidate_type_t consolidate_type);

/**
 * dtesn_memory_consolidate_selective - Selective memory consolidation
 * @system: Target cognitive system
 * @threshold: Importance threshold for consolidation
 * @consolidate_type: Type of consolidation to perform
 * 
 * Performs selective memory consolidation based on importance threshold,
 * consolidating only memory nodes above the specified threshold.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_memory_consolidate_selective(dtesn_cognitive_system_t *system,
                                      float threshold,
                                      dtesn_cognitive_consolidate_type_t consolidate_type);

/* Attention mechanism functions */

/**
 * dtesn_attention_focus - Focus attention on specific input channel
 * @system: Target cognitive system
 * @channel_id: Target attention channel ID
 * @focus_vector: Focus vector (optional, can be NULL)
 * @focus_size: Focus vector size
 * 
 * Switches attention focus to the specified channel, optionally
 * using a custom focus vector for targeted attention.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_attention_focus(dtesn_cognitive_system_t *system,
                         uint32_t channel_id,
                         const float *focus_vector,
                         uint32_t focus_size);

/**
 * dtesn_attention_distribute - Distribute attention across channels
 * @system: Target cognitive system
 * @weights: Attention weight distribution
 * @num_weights: Number of weights (must match number of channels)
 * 
 * Distributes attention across multiple channels using the specified
 * weight distribution (weights must sum to 1.0).
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_attention_distribute(dtesn_cognitive_system_t *system,
                              const float *weights,
                              uint32_t num_weights);

/* Multi-modal fusion functions */

/**
 * dtesn_multimodal_fuse - Fuse multi-modal sensory input
 * @system: Target cognitive system
 * @input_data: Array of modality data
 * @num_modalities: Number of input modalities
 * @fusion_type: Fusion strategy to use
 * @output: Output buffer for fused representation
 * @output_size: Output buffer size
 * 
 * Fuses multi-modal sensory input using the specified fusion strategy
 * and stores the result in the output buffer.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_multimodal_fuse(dtesn_cognitive_system_t *system,
                         const dtesn_cognitive_modality_data_t *input_data,
                         uint32_t num_modalities,
                         dtesn_cognitive_fusion_type_t fusion_type,
                         float *output,
                         uint32_t output_size);

/* Distributed processing functions */

/**
 * dtesn_distributed_sync - Synchronize state across distributed nodes
 * @system: Target cognitive system
 * @sync_timeout_ms: Synchronization timeout in milliseconds
 * 
 * Synchronizes cognitive system state across all registered
 * distributed nodes with the specified timeout.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_distributed_sync(dtesn_cognitive_system_t *system,
                          uint32_t sync_timeout_ms);

/**
 * dtesn_distributed_add_node - Add a node to distributed processing
 * @system: Target cognitive system
 * @node_id: Unique node identifier
 * @ip_address: Node IP address
 * @port: Node port number
 * 
 * Adds a new node to the distributed processing network.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_distributed_add_node(dtesn_cognitive_system_t *system,
                              uint32_t node_id,
                              uint32_t ip_address,
                              uint16_t port);

/* Utility and validation functions */

/**
 * dtesn_cognitive_validate_a000081 - Validate OEIS A000081 compliance
 * @system: Target cognitive system
 * 
 * Validates that the cognitive system topology follows OEIS A000081
 * rooted tree enumeration constraints.
 * 
 * Returns: true if compliant, false otherwise
 */
bool dtesn_cognitive_validate_a000081(const dtesn_cognitive_system_t *system);

/**
 * dtesn_cognitive_get_performance_stats - Get performance statistics
 * @system: Target cognitive system
 * @stats_buffer: Buffer to store performance statistics
 * @buffer_size: Size of statistics buffer
 * 
 * Retrieves current performance statistics for the cognitive system.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_cognitive_get_performance_stats(const dtesn_cognitive_system_t *system,
                                         void *stats_buffer,
                                         size_t buffer_size);

/**
 * dtesn_cognitive_reset_stats - Reset performance statistics
 * @system: Target cognitive system
 * 
 * Resets all performance counters and statistics for the cognitive system.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_cognitive_reset_stats(dtesn_cognitive_system_t *system);

#ifdef __cplusplus
}
#endif

#endif /* DTESN_COGNITIVE_H */