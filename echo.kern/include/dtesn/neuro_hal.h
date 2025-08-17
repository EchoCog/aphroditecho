/*
 * DTESN Neuromorphic Hardware Abstraction Layer
 * =============================================
 * 
 * Deep Tree Echo State Networks (DTESN) neuromorphic hardware abstraction
 * providing unified API for spike-based processing across Intel Loihi,
 * SpiNNaker, BrainChip Akida, and other neuromorphic computing platforms.
 * 
 * Performance Requirements:
 * - Event latency: ≤ 1μs
 * - Throughput: ≥ 1M events/sec
 * - Power efficiency: ≤ 10mW/GOPS
 * - Context switch: ≤ 5μs
 * 
 * Architecture:
 * - Event-driven I/O for spike-based processing
 * - DMA support for high-throughput data transfer
 * - Power management for neuromorphic devices
 * - OEIS A000081 compliant device enumeration
 * - Real-time deterministic operation
 */

#ifndef DTESN_NEURO_HAL_H
#define DTESN_NEURO_HAL_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Neuromorphic HAL constants */
#define DTESN_NEURO_MAX_DEVICES         16      /* Maximum neuromorphic devices */
#define DTESN_NEURO_MAX_EVENTS          1000000 /* 1M events/sec target */
#define DTESN_NEURO_MAX_CHANNELS        256     /* Maximum I/O channels */
#define DTESN_NEURO_MAX_CORES           1024    /* Maximum cores per device */
#define DTESN_NEURO_MAX_SPIKE_RATE      100000  /* 100kHz max spike rate per neuron */
#define DTESN_NEURO_EVENT_QUEUE_SIZE    4096    /* Event queue depth */

/* Performance thresholds */
#define DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US   1    /* ≤ 1μs event latency */
#define DTESN_NEURO_THROUGHPUT_THRESHOLD_HZ      1000000  /* ≥ 1M events/sec */
#define DTESN_NEURO_POWER_EFFICIENCY_MW_GOPS     10   /* ≤ 10mW/GOPS */
#define DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US  5    /* ≤ 5μs context switch */

/* OEIS A000081 sequence for device enumeration compliance */
#define DTESN_NEURO_A000081_MAX_DEPTH    12
#define DTESN_NEURO_A000081_SEQUENCE \
    { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766 }

/* Neuromorphic device types */
typedef enum {
    DTESN_NEURO_DEVICE_UNKNOWN = 0,        /* Unknown device */
    DTESN_NEURO_DEVICE_LOIHI = 1,          /* Intel Loihi */
    DTESN_NEURO_DEVICE_SPINNAKER = 2,      /* SpiNNaker */
    DTESN_NEURO_DEVICE_AKIDA = 3,          /* BrainChip Akida */
    DTESN_NEURO_DEVICE_DYNAP = 4,          /* SynSense DYNAP */
    DTESN_NEURO_DEVICE_TRUENORTH = 5,      /* IBM TrueNorth */
    DTESN_NEURO_DEVICE_GENERIC = 6         /* Generic neuromorphic */
} dtesn_neuro_device_type_t;

/* Device states */
typedef enum {
    DTESN_NEURO_STATE_UNINITIALIZED = 0,   /* Not initialized */
    DTESN_NEURO_STATE_INITIALIZING = 1,    /* Initialization in progress */
    DTESN_NEURO_STATE_READY = 2,           /* Ready for operation */
    DTESN_NEURO_STATE_ACTIVE = 3,          /* Active processing */
    DTESN_NEURO_STATE_SUSPENDED = 4,       /* Suspended/sleep mode */
    DTESN_NEURO_STATE_ERROR = 5            /* Error state */
} dtesn_neuro_state_t;

/* Event types for spike-based processing */
typedef enum {
    DTESN_NEURO_EVENT_SPIKE = 0,           /* Spike event */
    DTESN_NEURO_EVENT_SYNAPSE = 1,         /* Synaptic weight update */
    DTESN_NEURO_EVENT_LEARNING = 2,        /* Learning rule application */
    DTESN_NEURO_EVENT_RESET = 3,           /* Neuron reset */
    DTESN_NEURO_EVENT_CONFIG = 4,          /* Configuration change */
    DTESN_NEURO_EVENT_TIMER = 5            /* Timer/clock event */
} dtesn_neuro_event_type_t;

/* Power management modes */
typedef enum {
    DTESN_NEURO_POWER_FULL = 0,            /* Full power operation */
    DTESN_NEURO_POWER_REDUCED = 1,         /* Reduced power mode */
    DTESN_NEURO_POWER_SLEEP = 2,           /* Sleep mode */
    DTESN_NEURO_POWER_SUSPEND = 3,         /* Deep suspend */
    DTESN_NEURO_POWER_OFF = 4              /* Power off */
} dtesn_neuro_power_mode_t;

/* DMA transfer modes */
typedef enum {
    DTESN_NEURO_DMA_SYNCHRONOUS = 0,       /* Blocking transfer */
    DTESN_NEURO_DMA_ASYNCHRONOUS = 1,      /* Non-blocking transfer */
    DTESN_NEURO_DMA_SCATTER_GATHER = 2     /* Scatter-gather transfer */
} dtesn_neuro_dma_mode_t;

/* Neuromorphic event structure */
typedef struct dtesn_neuro_event {
    dtesn_neuro_event_type_t type;         /* Event type */
    uint64_t timestamp_ns;                 /* Timestamp in nanoseconds */
    uint32_t source_id;                    /* Source neuron/core ID */
    uint32_t target_id;                    /* Target neuron/core ID */
    uint32_t channel;                      /* I/O channel */
    float weight;                          /* Synaptic weight or data */
    uint32_t flags;                        /* Event flags */
    void *data;                            /* Additional event data */
} dtesn_neuro_event_t;

/* Device capability structure */
typedef struct dtesn_neuro_capabilities {
    uint32_t max_neurons;                  /* Maximum neurons */
    uint32_t max_synapses;                 /* Maximum synapses */
    uint32_t max_cores;                    /* Maximum processing cores */
    uint32_t max_spike_rate_hz;            /* Maximum spike rate */
    bool supports_stdp;                    /* STDP learning support */
    bool supports_dma;                     /* DMA support */
    bool supports_power_mgmt;              /* Power management support */
    bool supports_realtime;                /* Real-time guarantees */
    uint32_t memory_size_bytes;            /* On-device memory */
    float power_consumption_mw;            /* Power consumption (mW) */
    float gops_rating;                     /* GOPS performance rating */
} dtesn_neuro_capabilities_t;

/* Device configuration structure */
typedef struct dtesn_neuro_config {
    uint32_t num_neurons;                  /* Number of active neurons */
    uint32_t num_cores;                    /* Number of active cores */
    uint32_t spike_threshold_mv;           /* Spike threshold (mV) */
    uint32_t refractory_period_us;         /* Refractory period (μs) */
    float learning_rate;                   /* Learning rate */
    uint32_t timestep_us;                  /* Simulation timestep (μs) */
    dtesn_neuro_power_mode_t power_mode;   /* Power management mode */
    bool enable_learning;                  /* Enable learning */
    bool enable_monitoring;                /* Enable event monitoring */
} dtesn_neuro_config_t;

/* Performance statistics */
typedef struct dtesn_neuro_stats {
    uint64_t total_events_processed;       /* Total events processed */
    uint64_t total_spikes_generated;       /* Total spikes generated */
    uint64_t total_learning_updates;       /* Total learning updates */
    
    uint64_t avg_event_latency_ns;         /* Average event latency */
    uint64_t max_event_latency_ns;         /* Maximum event latency */
    uint64_t min_event_latency_ns;         /* Minimum event latency */
    
    uint32_t throughput_events_per_sec;    /* Current throughput */
    uint32_t peak_throughput_events_per_sec; /* Peak throughput */
    
    float power_consumption_mw;            /* Current power consumption */
    float power_efficiency_mw_gops;        /* Power efficiency */
    
    uint64_t context_switch_count;         /* Context switches */
    uint64_t avg_context_switch_time_ns;   /* Average context switch time */
    
    uint64_t dma_transfers_completed;      /* DMA transfers completed */
    uint64_t dma_bytes_transferred;        /* Total DMA bytes */
    
    bool event_latency_threshold_met;      /* ≤1μs latency constraint */
    bool throughput_threshold_met;         /* ≥1M events/sec constraint */
    bool power_efficiency_threshold_met;   /* ≤10mW/GOPS constraint */
    bool context_switch_threshold_met;     /* ≤5μs context switch constraint */
} dtesn_neuro_stats_t;

/* Device descriptor structure */
typedef struct dtesn_neuro_device {
    uint32_t device_id;                    /* Unique device identifier */
    char name[64];                         /* Device name */
    dtesn_neuro_device_type_t type;        /* Device type */
    dtesn_neuro_state_t state;             /* Current state */
    
    dtesn_neuro_capabilities_t caps;       /* Device capabilities */
    dtesn_neuro_config_t config;           /* Current configuration */
    dtesn_neuro_stats_t stats;             /* Performance statistics */
    
    /* Hardware-specific context */
    void *hw_context;                      /* Hardware-specific data */
    void *driver_context;                  /* Driver-specific data */
    
    /* Event processing */
    dtesn_neuro_event_t *event_queue;      /* Event queue */
    uint32_t event_queue_head;             /* Queue head index */
    uint32_t event_queue_tail;             /* Queue tail index */
    uint32_t event_queue_size;             /* Queue size */
    
    /* DMA state */
    void *dma_buffer;                      /* DMA transfer buffer */
    size_t dma_buffer_size;                /* DMA buffer size */
    bool dma_in_progress;                  /* DMA transfer active */
    
    /* Synchronization */
    pthread_mutex_t device_lock;           /* Device access lock */
    pthread_cond_t event_cond;             /* Event processing condition */
    pthread_t event_thread;                /* Event processing thread */
    
    /* OEIS A000081 compliance */
    uint32_t tree_depth;                   /* Device enumeration tree depth */
    bool oeis_validated;                   /* OEIS compliance validated */
    
    /* Performance monitoring */
    uint64_t creation_time_ns;             /* Device creation timestamp */
    uint64_t last_activity_ns;             /* Last activity timestamp */
    
} dtesn_neuro_device_t;

/* Device driver interface structure */
typedef struct dtesn_neuro_driver {
    dtesn_neuro_device_type_t type;        /* Device type supported */
    char name[64];                         /* Driver name */
    
    /* Driver operations */
    int (*probe)(dtesn_neuro_device_t *device);
    int (*init)(dtesn_neuro_device_t *device);
    int (*start)(dtesn_neuro_device_t *device);
    int (*stop)(dtesn_neuro_device_t *device);
    int (*reset)(dtesn_neuro_device_t *device);
    int (*configure)(dtesn_neuro_device_t *device, const dtesn_neuro_config_t *config);
    
    /* Event operations */
    int (*send_event)(dtesn_neuro_device_t *device, const dtesn_neuro_event_t *event);
    int (*receive_event)(dtesn_neuro_device_t *device, dtesn_neuro_event_t *event);
    int (*process_events)(dtesn_neuro_device_t *device);
    
    /* DMA operations */
    int (*dma_transfer)(dtesn_neuro_device_t *device, void *src, void *dst, 
                       size_t size, dtesn_neuro_dma_mode_t mode);
    int (*dma_status)(dtesn_neuro_device_t *device, bool *complete, size_t *transferred);
    
    /* Power management */
    int (*set_power_mode)(dtesn_neuro_device_t *device, dtesn_neuro_power_mode_t mode);
    int (*get_power_stats)(dtesn_neuro_device_t *device, float *power_mw, float *efficiency);
    
    /* Statistics */
    int (*get_stats)(dtesn_neuro_device_t *device, dtesn_neuro_stats_t *stats);
    int (*reset_stats)(dtesn_neuro_device_t *device);
    
} dtesn_neuro_driver_t;

/* DMA transfer descriptor */
typedef struct dtesn_neuro_dma_desc {
    void *src_addr;                        /* Source address */
    void *dst_addr;                        /* Destination address */
    size_t size;                           /* Transfer size */
    dtesn_neuro_dma_mode_t mode;           /* Transfer mode */
    uint32_t flags;                        /* Transfer flags */
    void (*callback)(void *context);       /* Completion callback */
    void *callback_context;                /* Callback context */
} dtesn_neuro_dma_desc_t;

/* Event callback function type */
typedef void (*dtesn_neuro_event_callback_t)(dtesn_neuro_device_t *device, 
                                             const dtesn_neuro_event_t *event, 
                                             void *context);

/* Power management callback function type */
typedef void (*dtesn_neuro_power_callback_t)(dtesn_neuro_device_t *device, 
                                             dtesn_neuro_power_mode_t old_mode,
                                             dtesn_neuro_power_mode_t new_mode, 
                                             void *context);

/* Core HAL management functions */

/**
 * neuro_hal_init - Initialize neuromorphic hardware abstraction layer
 * 
 * Initializes the neuromorphic HAL subsystem, detects available devices,
 * loads appropriate drivers, and sets up event processing infrastructure.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_hal_init(void);

/**
 * neuro_hal_shutdown - Shutdown neuromorphic HAL
 * 
 * Cleanly shuts down all neuromorphic devices, unloads drivers,
 * and releases all HAL resources.
 */
void neuro_hal_shutdown(void);

/**
 * neuro_device_register - Register neuromorphic device driver
 * @driver: Device driver to register
 * 
 * Registers a neuromorphic device driver with the HAL for device
 * discovery and management.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_register(const dtesn_neuro_driver_t *driver);

/**
 * neuro_device_unregister - Unregister neuromorphic device driver
 * @type: Device type to unregister
 * 
 * Unregisters a neuromorphic device driver from the HAL.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_unregister(dtesn_neuro_device_type_t type);

/* Device discovery and management */

/**
 * neuro_device_discover - Discover available neuromorphic devices
 * @devices: Array to fill with discovered devices
 * @max_devices: Maximum number of devices to discover
 * 
 * Discovers and enumerates available neuromorphic devices according
 * to OEIS A000081 enumeration constraints.
 * 
 * Returns: Number of devices found, negative error code on failure
 */
int neuro_device_discover(dtesn_neuro_device_t *devices, uint32_t max_devices);

/**
 * neuro_device_get_by_id - Get device by ID
 * @device_id: Device identifier
 * 
 * Retrieves a device descriptor by its unique identifier.
 * 
 * Returns: Pointer to device, NULL if not found
 */
dtesn_neuro_device_t *neuro_device_get_by_id(uint32_t device_id);

/**
 * neuro_device_get_by_type - Get first device of specified type
 * @type: Device type to find
 * 
 * Retrieves the first available device of the specified type.
 * 
 * Returns: Pointer to device, NULL if not found
 */
dtesn_neuro_device_t *neuro_device_get_by_type(dtesn_neuro_device_type_t type);

/**
 * neuro_device_open - Open neuromorphic device for operation
 * @device: Device to open
 * @config: Initial device configuration
 * 
 * Opens a neuromorphic device and applies initial configuration.
 * Enforces ≤5μs context switch constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_open(dtesn_neuro_device_t *device, const dtesn_neuro_config_t *config);

/**
 * neuro_device_close - Close neuromorphic device
 * @device: Device to close
 * 
 * Closes a neuromorphic device and releases associated resources.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_close(dtesn_neuro_device_t *device);

/* Event processing functions */

/**
 * neuro_event_process - Process neuromorphic events
 * @device: Target device
 * @events: Array of events to process
 * @num_events: Number of events
 * 
 * Processes neuromorphic events on the specified device.
 * Enforces ≤1μs event latency constraint.
 * 
 * Returns: Number of events processed, negative error code on failure
 */
int neuro_event_process(dtesn_neuro_device_t *device, 
                       const dtesn_neuro_event_t *events, 
                       uint32_t num_events);

/**
 * neuro_event_send - Send single neuromorphic event
 * @device: Target device
 * @event: Event to send
 * 
 * Sends a single neuromorphic event to the specified device.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_event_send(dtesn_neuro_device_t *device, const dtesn_neuro_event_t *event);

/**
 * neuro_event_receive - Receive neuromorphic event
 * @device: Source device
 * @event: Buffer for received event
 * @timeout_us: Timeout in microseconds (0 = non-blocking)
 * 
 * Receives a neuromorphic event from the specified device.
 * 
 * Returns: 1 if event received, 0 if no event, negative error code on failure
 */
int neuro_event_receive(dtesn_neuro_device_t *device, 
                       dtesn_neuro_event_t *event, 
                       uint32_t timeout_us);

/**
 * neuro_event_register_callback - Register event callback
 * @device: Target device
 * @callback: Callback function
 * @context: Callback context
 * 
 * Registers a callback function for neuromorphic event notification.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_event_register_callback(dtesn_neuro_device_t *device,
                                 dtesn_neuro_event_callback_t callback,
                                 void *context);

/* DMA transfer functions */

/**
 * neuro_dma_transfer - Perform DMA transfer
 * @device: Target device
 * @desc: DMA transfer descriptor
 * 
 * Performs a DMA transfer between host memory and neuromorphic device.
 * Supports synchronous, asynchronous, and scatter-gather modes.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_dma_transfer(dtesn_neuro_device_t *device, const dtesn_neuro_dma_desc_t *desc);

/**
 * neuro_dma_status - Check DMA transfer status
 * @device: Target device
 * @complete: Output completion status
 * @bytes_transferred: Output bytes transferred
 * 
 * Checks the status of an ongoing DMA transfer.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_dma_status(dtesn_neuro_device_t *device, bool *complete, size_t *bytes_transferred);

/**
 * neuro_dma_wait - Wait for DMA transfer completion
 * @device: Target device
 * @timeout_us: Timeout in microseconds
 * 
 * Waits for a DMA transfer to complete with optional timeout.
 * 
 * Returns: 0 on completion, negative error code on timeout or failure
 */
int neuro_dma_wait(dtesn_neuro_device_t *device, uint32_t timeout_us);

/* Power management functions */

/**
 * neuro_power_manage - Set device power management mode
 * @device: Target device
 * @mode: Power management mode
 * 
 * Sets the power management mode for the neuromorphic device.
 * Maintains ≤10mW/GOPS power efficiency constraint.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_power_manage(dtesn_neuro_device_t *device, dtesn_neuro_power_mode_t mode);

/**
 * neuro_power_get_stats - Get power consumption statistics
 * @device: Target device
 * @power_mw: Output current power consumption (mW)
 * @efficiency_mw_gops: Output power efficiency (mW/GOPS)
 * 
 * Retrieves current power consumption and efficiency metrics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_power_get_stats(dtesn_neuro_device_t *device, 
                         float *power_mw, 
                         float *efficiency_mw_gops);

/**
 * neuro_power_register_callback - Register power state callback
 * @device: Target device
 * @callback: Callback function
 * @context: Callback context
 * 
 * Registers a callback for power state change notifications.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_power_register_callback(dtesn_neuro_device_t *device,
                                 dtesn_neuro_power_callback_t callback,
                                 void *context);

/* Validation and monitoring functions */

/**
 * neuro_device_validate_a000081 - Validate OEIS A000081 compliance
 * @devices: Array of devices to validate
 * @num_devices: Number of devices
 * 
 * Validates that device enumeration follows OEIS A000081 unlabeled
 * rooted tree enumeration for DTESN compliance.
 * 
 * Returns: true if compliant, false otherwise
 */
bool neuro_device_validate_a000081(const dtesn_neuro_device_t *devices, uint32_t num_devices);

/**
 * neuro_device_get_stats - Get comprehensive device statistics
 * @device: Target device
 * @stats: Statistics structure to fill
 * 
 * Retrieves comprehensive performance and operational statistics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_get_stats(dtesn_neuro_device_t *device, dtesn_neuro_stats_t *stats);

/**
 * neuro_device_reset_stats - Reset device statistics
 * @device: Target device
 * 
 * Resets performance and operational statistics counters.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_device_reset_stats(dtesn_neuro_device_t *device);

/**
 * neuro_hal_check_thresholds - Check performance thresholds
 * @device: Target device
 * 
 * Checks if device is meeting all performance thresholds:
 * - Event latency ≤ 1μs
 * - Throughput ≥ 1M events/sec
 * - Power efficiency ≤ 10mW/GOPS
 * - Context switch ≤ 5μs
 * 
 * Returns: true if all thresholds met, false otherwise
 */
bool neuro_hal_check_thresholds(dtesn_neuro_device_t *device);

/* Utility functions */

/**
 * neuro_config_default - Get default device configuration
 * @config: Configuration structure to fill
 * @type: Device type
 * 
 * Fills configuration structure with sensible defaults for
 * the specified device type.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int neuro_config_default(dtesn_neuro_config_t *config, dtesn_neuro_device_type_t type);

/**
 * neuro_event_create - Create neuromorphic event
 * @type: Event type
 * @source_id: Source neuron/core ID
 * @target_id: Target neuron/core ID
 * @weight: Synaptic weight or data
 * 
 * Creates a neuromorphic event with current timestamp.
 * 
 * Returns: Initialized event structure
 */
dtesn_neuro_event_t neuro_event_create(dtesn_neuro_event_type_t type,
                                      uint32_t source_id,
                                      uint32_t target_id, 
                                      float weight);

/**
 * neuro_device_type_name - Get device type name string
 * @type: Device type
 * 
 * Returns human-readable string for device type.
 * 
 * Returns: Device type name string
 */
const char *neuro_device_type_name(dtesn_neuro_device_type_t type);

/**
 * neuro_hal_get_version - Get HAL version information
 * @major: Output major version
 * @minor: Output minor version
 * @patch: Output patch version
 * 
 * Retrieves neuromorphic HAL version information.
 */
void neuro_hal_get_version(uint32_t *major, uint32_t *minor, uint32_t *patch);

/* Error codes specific to neuromorphic HAL */
#define DTESN_NEURO_ENOMEM           -50  /* Out of memory */
#define DTESN_NEURO_EINVAL           -51  /* Invalid parameters */
#define DTESN_NEURO_ENOTFOUND        -52  /* Device not found */
#define DTESN_NEURO_EBUSY            -53  /* Device busy */
#define DTESN_NEURO_ETIMEDOUT        -54  /* Operation timed out */
#define DTESN_NEURO_ELATENCY         -55  /* Latency constraint violated */
#define DTESN_NEURO_ETHROUGHPUT      -56  /* Throughput constraint violated */
#define DTESN_NEURO_EPOWER           -57  /* Power constraint violated */
#define DTESN_NEURO_EVALIDATION      -58  /* OEIS A000081 validation failed */
#define DTESN_NEURO_EHARDWARE        -59  /* Hardware failure */
#define DTESN_NEURO_EDRIVER          -60  /* Driver error */
#define DTESN_NEURO_EDMA             -61  /* DMA transfer failed */
#define DTESN_NEURO_EEVENT           -62  /* Event processing failed */
#define DTESN_NEURO_ENOTSUPPORTED    -63  /* Operation not supported */

#ifdef __cplusplus
}
#endif

#endif /* DTESN_NEURO_HAL_H */