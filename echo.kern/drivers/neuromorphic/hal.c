/*
 * DTESN Neuromorphic Hardware Abstraction Layer Implementation
 * ===========================================================
 * 
 * Core implementation of the neuromorphic HAL providing unified API
 * for spike-based processing across multiple neuromorphic platforms.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/neuro_hal.h"
/* #include "include/dtesn/memory.h" */
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/time.h>

/* HAL version information */
#define DTESN_NEURO_HAL_VERSION_MAJOR    1
#define DTESN_NEURO_HAL_VERSION_MINOR    0
#define DTESN_NEURO_HAL_VERSION_PATCH    0

/* Global HAL state */
static struct {
    bool initialized;
    uint32_t num_devices;
    uint32_t num_drivers;
    dtesn_neuro_device_t devices[DTESN_NEURO_MAX_DEVICES];
    dtesn_neuro_driver_t drivers[8]; /* Support up to 8 driver types */
    pthread_mutex_t hal_lock;
    pthread_t monitor_thread;
    bool monitor_running;
    uint64_t start_time_ns;
} g_neuro_hal = {0};

/* OEIS A000081 sequence for validation */
static const uint32_t g_oeis_a000081[] = DTESN_NEURO_A000081_SEQUENCE;

/* Forward declarations */
static uint64_t get_timestamp_ns(void);
static int validate_device_config(const dtesn_neuro_config_t *config);
static int update_device_stats(dtesn_neuro_device_t *device);
static void *event_monitor_thread(void *arg);
static void *device_monitor_thread(void *arg);
static int ensure_event_queue(dtesn_neuro_device_t *device);
static int process_event_queue(dtesn_neuro_device_t *device);

/**
 * Get current timestamp in nanoseconds
 */
static uint64_t get_timestamp_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Validate device configuration
 */
static int validate_device_config(const dtesn_neuro_config_t *config) {
    if (!config) {
        return DTESN_NEURO_EINVAL;
    }
    
    /* Basic validation */
    if (config->num_neurons == 0 || config->num_cores == 0) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (config->spike_threshold_mv < 10 || config->spike_threshold_mv > 1000) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (config->learning_rate < 0.0f || config->learning_rate > 1.0f) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (config->timestep_us == 0 || config->timestep_us > 10000) {
        return DTESN_NEURO_EINVAL;
    }
    
    return 0;
}

/**
 * Update device performance statistics
 */
static int update_device_stats(dtesn_neuro_device_t *device) {
    if (!device) {
        return DTESN_NEURO_EINVAL;
    }
    
    uint64_t current_time = get_timestamp_ns();
    device->last_activity_ns = current_time;
    
    /* Update performance threshold flags */
    device->stats.event_latency_threshold_met = 
        (device->stats.avg_event_latency_ns <= DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US * 1000);
    
    device->stats.throughput_threshold_met = 
        (device->stats.throughput_events_per_sec >= DTESN_NEURO_THROUGHPUT_THRESHOLD_HZ);
    
    device->stats.power_efficiency_threshold_met = 
        (device->stats.power_efficiency_mw_gops <= DTESN_NEURO_POWER_EFFICIENCY_MW_GOPS);
    
    device->stats.context_switch_threshold_met = 
        (device->stats.avg_context_switch_time_ns <= DTESN_NEURO_CONTEXT_SWITCH_THRESHOLD_US * 1000);
    
    return 0;
}

/**
 * Ensure event queue is allocated and ready
 */
static int ensure_event_queue(dtesn_neuro_device_t *device) {
    if (!device) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (!device->event_queue) {
        device->event_queue_size = DTESN_NEURO_EVENT_QUEUE_SIZE;
        device->event_queue = malloc(
            device->event_queue_size * sizeof(dtesn_neuro_event_t));
        
        if (!device->event_queue) {
            return DTESN_NEURO_ENOMEM;
        }
        
        device->event_queue_head = 0;
        device->event_queue_tail = 0;
    }
    
    return 0;
}

/**
 * Process events in device queue
 */
static int process_event_queue(dtesn_neuro_device_t *device) {
    if (!device || !device->event_queue) {
        return DTESN_NEURO_EINVAL;
    }
    
    int events_processed = 0;
    uint64_t start_time = get_timestamp_ns();
    
    pthread_mutex_lock(&device->device_lock);
    
    while (device->event_queue_head != device->event_queue_tail) {
        dtesn_neuro_event_t *event = &device->event_queue[device->event_queue_head];
        
        /* Process event based on type */
        switch (event->type) {
            case DTESN_NEURO_EVENT_SPIKE:
                device->stats.total_spikes_generated++;
                break;
                
            case DTESN_NEURO_EVENT_LEARNING:
                device->stats.total_learning_updates++;
                break;
                
            default:
                break;
        }
        
        device->event_queue_head = (device->event_queue_head + 1) % device->event_queue_size;
        events_processed++;
        device->stats.total_events_processed++;
        
        /* Check latency constraint */
        uint64_t processing_time = get_timestamp_ns() - event->timestamp_ns;
        if (processing_time > device->stats.max_event_latency_ns) {
            device->stats.max_event_latency_ns = processing_time;
        }
        
        if (device->stats.min_event_latency_ns == 0 || 
            processing_time < device->stats.min_event_latency_ns) {
            device->stats.min_event_latency_ns = processing_time;
        }
        
        /* Update average latency */
        if (device->stats.total_events_processed > 0) {
            device->stats.avg_event_latency_ns = 
                (device->stats.avg_event_latency_ns * (device->stats.total_events_processed - 1) + 
                 processing_time) / device->stats.total_events_processed;
        }
    }
    
    pthread_mutex_unlock(&device->device_lock);
    
    /* Update throughput */
    uint64_t total_time = get_timestamp_ns() - start_time;
    if (total_time > 0 && events_processed > 0) {
        uint32_t current_throughput = (uint32_t)((uint64_t)events_processed * 1000000000ULL / total_time);
        
        if (current_throughput > device->stats.peak_throughput_events_per_sec) {
            device->stats.peak_throughput_events_per_sec = current_throughput;
        }
        
        device->stats.throughput_events_per_sec = current_throughput;
    }
    
    return events_processed;
}

/**
 * Device monitoring thread
 */
static void *device_monitor_thread(void *arg) {
    (void)arg; /* Unused */
    
    while (g_neuro_hal.monitor_running) {
        pthread_mutex_lock(&g_neuro_hal.hal_lock);
        
        for (uint32_t i = 0; i < g_neuro_hal.num_devices; i++) {
            dtesn_neuro_device_t *device = &g_neuro_hal.devices[i];
            
            if (device->state == DTESN_NEURO_STATE_ACTIVE) {
                /* Process events for active devices */
                process_event_queue(device);
                update_device_stats(device);
            }
        }
        
        pthread_mutex_unlock(&g_neuro_hal.hal_lock);
        
        /* Sleep for 1ms to maintain real-time performance */
        usleep(1000);
    }
    
    return NULL;
}

/* Public API Implementation */

int neuro_hal_init(void) {
    if (g_neuro_hal.initialized) {
        return 0; /* Already initialized */
    }
    
    /* Initialize HAL state */
    memset(&g_neuro_hal, 0, sizeof(g_neuro_hal));
    
    /* Initialize memory management if not already done */
    /* int result = dtesn_mem_init();
    if (result != 0) {
        return result;
    } */
    
    /* Initialize synchronization */
    if (pthread_mutex_init(&g_neuro_hal.hal_lock, NULL) != 0) {
        return DTESN_NEURO_EHARDWARE;
    }
    
    /* Start monitoring thread */
    g_neuro_hal.monitor_running = true;
    if (pthread_create(&g_neuro_hal.monitor_thread, NULL, device_monitor_thread, NULL) != 0) {
        pthread_mutex_destroy(&g_neuro_hal.hal_lock);
        return DTESN_NEURO_EHARDWARE;
    }
    
    g_neuro_hal.start_time_ns = get_timestamp_ns();
    g_neuro_hal.initialized = true;
    
    return 0;
}

void neuro_hal_shutdown(void) {
    if (!g_neuro_hal.initialized) {
        return;
    }
    
    /* Stop monitoring thread */
    g_neuro_hal.monitor_running = false;
    pthread_join(g_neuro_hal.monitor_thread, NULL);
    
    /* Close all devices */
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    for (uint32_t i = 0; i < g_neuro_hal.num_devices; i++) {
        dtesn_neuro_device_t *device = &g_neuro_hal.devices[i];
        if (device->state != DTESN_NEURO_STATE_UNINITIALIZED) {
            neuro_device_close(device);
        }
    }
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    /* Cleanup */
    pthread_mutex_destroy(&g_neuro_hal.hal_lock);
    memset(&g_neuro_hal, 0, sizeof(g_neuro_hal));
}

int neuro_device_register(const dtesn_neuro_driver_t *driver) {
    if (!driver || !g_neuro_hal.initialized) {
        return DTESN_NEURO_EINVAL;
    }
    
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    if (g_neuro_hal.num_drivers >= sizeof(g_neuro_hal.drivers) / sizeof(g_neuro_hal.drivers[0])) {
        pthread_mutex_unlock(&g_neuro_hal.hal_lock);
        return DTESN_NEURO_ENOMEM;
    }
    
    /* Check for duplicate driver type */
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == driver->type) {
            pthread_mutex_unlock(&g_neuro_hal.hal_lock);
            return DTESN_NEURO_EBUSY;
        }
    }
    
    /* Register driver */
    memcpy(&g_neuro_hal.drivers[g_neuro_hal.num_drivers], driver, sizeof(dtesn_neuro_driver_t));
    g_neuro_hal.num_drivers++;
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    return 0;
}

int neuro_device_unregister(dtesn_neuro_device_type_t type) {
    if (!g_neuro_hal.initialized) {
        return DTESN_NEURO_EINVAL;
    }
    
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    /* Find and remove driver */
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == type) {
            /* Move remaining drivers down */
            memmove(&g_neuro_hal.drivers[i], &g_neuro_hal.drivers[i + 1],
                   (g_neuro_hal.num_drivers - i - 1) * sizeof(dtesn_neuro_driver_t));
            g_neuro_hal.num_drivers--;
            
            pthread_mutex_unlock(&g_neuro_hal.hal_lock);
            return 0;
        }
    }
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    return DTESN_NEURO_ENOTFOUND;
}

int neuro_device_discover(dtesn_neuro_device_t *devices, uint32_t max_devices) {
    if (!devices || max_devices == 0 || !g_neuro_hal.initialized) {
        return DTESN_NEURO_EINVAL;
    }
    
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    uint32_t devices_found = 0;
    
    /* Try each registered driver for device discovery */
    for (uint32_t driver_idx = 0; driver_idx < g_neuro_hal.num_drivers && devices_found < max_devices; driver_idx++) {
        dtesn_neuro_driver_t *driver = &g_neuro_hal.drivers[driver_idx];
        
        /* Create a device structure for probing */
        dtesn_neuro_device_t probe_device;
        memset(&probe_device, 0, sizeof(probe_device));
        probe_device.type = driver->type;
        probe_device.device_id = devices_found; /* Temporary ID */
        
        /* Probe for device */
        if (driver->probe && driver->probe(&probe_device) == 0) {
            /* Device found, add to discovered list */
            if (devices_found < g_neuro_hal.num_devices) {
                memcpy(&devices[devices_found], &probe_device, sizeof(dtesn_neuro_device_t));
            } else {
                /* Add to global device list */
                if (g_neuro_hal.num_devices < DTESN_NEURO_MAX_DEVICES) {
                    memcpy(&g_neuro_hal.devices[g_neuro_hal.num_devices], &probe_device, sizeof(dtesn_neuro_device_t));
                    g_neuro_hal.devices[g_neuro_hal.num_devices].device_id = g_neuro_hal.num_devices;
                    g_neuro_hal.num_devices++;
                    
                    memcpy(&devices[devices_found], &probe_device, sizeof(dtesn_neuro_device_t));
                }
            }
            
            devices_found++;
        }
    }
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    return devices_found;
}

dtesn_neuro_device_t *neuro_device_get_by_id(uint32_t device_id) {
    if (!g_neuro_hal.initialized) {
        return NULL;
    }
    
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    for (uint32_t i = 0; i < g_neuro_hal.num_devices; i++) {
        if (g_neuro_hal.devices[i].device_id == device_id) {
            pthread_mutex_unlock(&g_neuro_hal.hal_lock);
            return &g_neuro_hal.devices[i];
        }
    }
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    return NULL;
}

dtesn_neuro_device_t *neuro_device_get_by_type(dtesn_neuro_device_type_t type) {
    if (!g_neuro_hal.initialized) {
        return NULL;
    }
    
    pthread_mutex_lock(&g_neuro_hal.hal_lock);
    
    for (uint32_t i = 0; i < g_neuro_hal.num_devices; i++) {
        if (g_neuro_hal.devices[i].type == type) {
            pthread_mutex_unlock(&g_neuro_hal.hal_lock);
            return &g_neuro_hal.devices[i];
        }
    }
    
    pthread_mutex_unlock(&g_neuro_hal.hal_lock);
    
    return NULL;
}

int neuro_device_open(dtesn_neuro_device_t *device, const dtesn_neuro_config_t *config) {
    if (!device || !config || !g_neuro_hal.initialized) {
        return DTESN_NEURO_EINVAL;
    }
    
    uint64_t start_time = get_timestamp_ns();
    
    /* Validate configuration */
    int result = validate_device_config(config);
    if (result != 0) {
        return result;
    }
    
    pthread_mutex_lock(&device->device_lock);
    
    if (device->state != DTESN_NEURO_STATE_READY) {
        pthread_mutex_unlock(&device->device_lock);
        return DTESN_NEURO_EBUSY;
    }
    
    /* Apply configuration */
    memcpy(&device->config, config, sizeof(dtesn_neuro_config_t));
    
    /* Initialize event queue */
    result = ensure_event_queue(device);
    if (result != 0) {
        pthread_mutex_unlock(&device->device_lock);
        return result;
    }
    
    /* Find and initialize driver */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    if (!driver) {
        pthread_mutex_unlock(&device->device_lock);
        return DTESN_NEURO_EDRIVER;
    }
    
    /* Initialize device through driver */
    if (driver->init) {
        result = driver->init(device);
        if (result != 0) {
            pthread_mutex_unlock(&device->device_lock);
            return result;
        }
    }
    
    /* Configure device through driver */
    if (driver->configure) {
        result = driver->configure(device, config);
        if (result != 0) {
            pthread_mutex_unlock(&device->device_lock);
            return result;
        }
    }
    
    /* Start device */
    if (driver->start) {
        result = driver->start(device);
        if (result != 0) {
            pthread_mutex_unlock(&device->device_lock);
            return result;
        }
    }
    
    device->state = DTESN_NEURO_STATE_ACTIVE;
    device->creation_time_ns = get_timestamp_ns();
    
    /* Check context switch time */
    uint64_t context_switch_time = get_timestamp_ns() - start_time;
    device->stats.context_switch_count++;
    device->stats.avg_context_switch_time_ns = 
        (device->stats.avg_context_switch_time_ns * (device->stats.context_switch_count - 1) + 
         context_switch_time) / device->stats.context_switch_count;
    
    pthread_mutex_unlock(&device->device_lock);
    
    return 0;
}

int neuro_device_close(dtesn_neuro_device_t *device) {
    if (!device || !g_neuro_hal.initialized) {
        return DTESN_NEURO_EINVAL;
    }
    
    pthread_mutex_lock(&device->device_lock);
    
    if (device->state == DTESN_NEURO_STATE_UNINITIALIZED) {
        pthread_mutex_unlock(&device->device_lock);
        return 0; /* Already closed */
    }
    
    /* Find driver for shutdown */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    /* Stop device through driver */
    if (driver && driver->stop) {
        driver->stop(device);
    }
    
    /* Cleanup resources */
    if (device->event_queue) {
        free(device->event_queue);
        device->event_queue = NULL;
    }
    
    if (device->dma_buffer) {
        free(device->dma_buffer);
        device->dma_buffer = NULL;
    }
    
    device->state = DTESN_NEURO_STATE_UNINITIALIZED;
    
    pthread_mutex_unlock(&device->device_lock);
    
    return 0;
}

int neuro_event_process(dtesn_neuro_device_t *device, 
                       const dtesn_neuro_event_t *events, 
                       uint32_t num_events) {
    if (!device || !events || num_events == 0) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (device->state != DTESN_NEURO_STATE_ACTIVE) {
        return DTESN_NEURO_EBUSY;
    }
    
    uint64_t start_time = get_timestamp_ns();
    int events_processed = 0;
    
    pthread_mutex_lock(&device->device_lock);
    
    /* Ensure event queue is ready */
    int result = ensure_event_queue(device);
    if (result != 0) {
        pthread_mutex_unlock(&device->device_lock);
        return result;
    }
    
    /* Process each event */
    for (uint32_t i = 0; i < num_events; i++) {
        /* Check if queue has space */
        uint32_t next_tail = (device->event_queue_tail + 1) % device->event_queue_size;
        if (next_tail == device->event_queue_head) {
            /* Queue full, process some events first */
            pthread_mutex_unlock(&device->device_lock);
            process_event_queue(device);
            pthread_mutex_lock(&device->device_lock);
        }
        
        /* Add event to queue */
        memcpy(&device->event_queue[device->event_queue_tail], &events[i], sizeof(dtesn_neuro_event_t));
        device->event_queue[device->event_queue_tail].timestamp_ns = get_timestamp_ns();
        device->event_queue_tail = next_tail;
        
        events_processed++;
    }
    
    pthread_mutex_unlock(&device->device_lock);
    
    /* Check processing latency */
    uint64_t processing_time = get_timestamp_ns() - start_time;
    uint64_t avg_event_latency = num_events > 0 ? processing_time / num_events : 0;
    
    if (avg_event_latency > DTESN_NEURO_EVENT_LATENCY_THRESHOLD_US * 1000) {
        return DTESN_NEURO_ELATENCY;
    }
    
    return events_processed;
}

int neuro_event_send(dtesn_neuro_device_t *device, const dtesn_neuro_event_t *event) {
    if (!device || !event) {
        return DTESN_NEURO_EINVAL;
    }
    
    return neuro_event_process(device, event, 1);
}

int neuro_event_receive(dtesn_neuro_device_t *device, 
                       dtesn_neuro_event_t *event, 
                       uint32_t timeout_us) {
    if (!device || !event) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (device->state != DTESN_NEURO_STATE_ACTIVE) {
        return DTESN_NEURO_EBUSY;
    }
    
    uint64_t start_time = get_timestamp_ns();
    uint64_t timeout_ns = (uint64_t)timeout_us * 1000;
    
    while (true) {
        pthread_mutex_lock(&device->device_lock);
        
        /* Check if event available */
        if (device->event_queue_head != device->event_queue_tail) {
            memcpy(event, &device->event_queue[device->event_queue_head], sizeof(dtesn_neuro_event_t));
            device->event_queue_head = (device->event_queue_head + 1) % device->event_queue_size;
            
            pthread_mutex_unlock(&device->device_lock);
            return 1; /* Event received */
        }
        
        pthread_mutex_unlock(&device->device_lock);
        
        /* Check timeout */
        if (timeout_us > 0) {
            uint64_t elapsed = get_timestamp_ns() - start_time;
            if (elapsed >= timeout_ns) {
                return 0; /* Timeout */
            }
        } else {
            return 0; /* Non-blocking, no event */
        }
        
        /* Small delay before retry */
        usleep(10);
    }
}

int neuro_power_manage(dtesn_neuro_device_t *device, dtesn_neuro_power_mode_t mode) {
    if (!device) {
        return DTESN_NEURO_EINVAL;
    }
    
    if (device->state == DTESN_NEURO_STATE_UNINITIALIZED) {
        return DTESN_NEURO_EBUSY;
    }
    
    /* Find driver for power management */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    if (!driver || !driver->set_power_mode) {
        return DTESN_NEURO_ENOTSUPPORTED;
    }
    
    dtesn_neuro_power_mode_t old_mode = device->config.power_mode;
    
    int result = driver->set_power_mode(device, mode);
    if (result == 0) {
        device->config.power_mode = mode;
        
        /* Update device state based on power mode */
        switch (mode) {
            case DTESN_NEURO_POWER_FULL:
                if (device->state == DTESN_NEURO_STATE_SUSPENDED) {
                    device->state = DTESN_NEURO_STATE_ACTIVE;
                }
                break;
                
            case DTESN_NEURO_POWER_SLEEP:
            case DTESN_NEURO_POWER_SUSPEND:
                device->state = DTESN_NEURO_STATE_SUSPENDED;
                break;
                
            case DTESN_NEURO_POWER_OFF:
                device->state = DTESN_NEURO_STATE_UNINITIALIZED;
                break;
                
            default:
                break;
        }
    }
    
    return result;
}

int neuro_power_get_stats(dtesn_neuro_device_t *device, 
                         float *power_mw, 
                         float *efficiency_mw_gops) {
    if (!device || !power_mw || !efficiency_mw_gops) {
        return DTESN_NEURO_EINVAL;
    }
    
    /* Find driver for power statistics */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    if (!driver || !driver->get_power_stats) {
        /* Use cached values */
        *power_mw = device->stats.power_consumption_mw;
        *efficiency_mw_gops = device->stats.power_efficiency_mw_gops;
        return 0;
    }
    
    int result = driver->get_power_stats(device, power_mw, efficiency_mw_gops);
    if (result == 0) {
        device->stats.power_consumption_mw = *power_mw;
        device->stats.power_efficiency_mw_gops = *efficiency_mw_gops;
    }
    
    return result;
}

bool neuro_device_validate_a000081(const dtesn_neuro_device_t *devices, uint32_t num_devices) {
    if (!devices || num_devices == 0) {
        return false;
    }
    
    /* OEIS A000081 validation for device enumeration */
    if (num_devices > DTESN_NEURO_A000081_MAX_DEPTH) {
        return false;
    }
    
    /* Check if device count matches OEIS sequence */
    if (num_devices <= sizeof(g_oeis_a000081) / sizeof(g_oeis_a000081[0])) {
        return (num_devices <= g_oeis_a000081[num_devices - 1]);
    }
    
    return true;
}

int neuro_device_get_stats(dtesn_neuro_device_t *device, dtesn_neuro_stats_t *stats) {
    if (!device || !stats) {
        return DTESN_NEURO_EINVAL;
    }
    
    pthread_mutex_lock(&device->device_lock);
    
    /* Update statistics */
    update_device_stats(device);
    
    /* Copy statistics */
    memcpy(stats, &device->stats, sizeof(dtesn_neuro_stats_t));
    
    pthread_mutex_unlock(&device->device_lock);
    
    return 0;
}

bool neuro_hal_check_thresholds(dtesn_neuro_device_t *device) {
    if (!device) {
        return false;
    }
    
    update_device_stats(device);
    
    return (device->stats.event_latency_threshold_met &&
            device->stats.throughput_threshold_met &&
            device->stats.power_efficiency_threshold_met &&
            device->stats.context_switch_threshold_met);
}

int neuro_config_default(dtesn_neuro_config_t *config, dtesn_neuro_device_type_t type) {
    if (!config) {
        return DTESN_NEURO_EINVAL;
    }
    
    memset(config, 0, sizeof(dtesn_neuro_config_t));
    
    /* Set common defaults */
    config->num_neurons = 256;
    config->num_cores = 1;
    config->spike_threshold_mv = 50;
    config->refractory_period_us = 1000;
    config->learning_rate = 0.01f;
    config->timestep_us = 1000;
    config->power_mode = DTESN_NEURO_POWER_FULL;
    config->enable_learning = true;
    config->enable_monitoring = true;
    
    /* Device-specific defaults */
    switch (type) {
        case DTESN_NEURO_DEVICE_LOIHI:
            config->num_neurons = 1024;
            config->num_cores = 128;
            break;
            
        case DTESN_NEURO_DEVICE_SPINNAKER:
            config->num_neurons = 256;
            config->num_cores = 18;
            break;
            
        case DTESN_NEURO_DEVICE_AKIDA:
            config->num_neurons = 1200;
            config->num_cores = 80;
            break;
            
        default:
            break;
    }
    
    return 0;
}

dtesn_neuro_event_t neuro_event_create(dtesn_neuro_event_type_t type,
                                      uint32_t source_id,
                                      uint32_t target_id, 
                                      float weight) {
    dtesn_neuro_event_t event;
    memset(&event, 0, sizeof(event));
    
    event.type = type;
    event.timestamp_ns = get_timestamp_ns();
    event.source_id = source_id;
    event.target_id = target_id;
    event.weight = weight;
    
    return event;
}

const char *neuro_device_type_name(dtesn_neuro_device_type_t type) {
    switch (type) {
        case DTESN_NEURO_DEVICE_LOIHI:      return "Intel Loihi";
        case DTESN_NEURO_DEVICE_SPINNAKER:  return "SpiNNaker";
        case DTESN_NEURO_DEVICE_AKIDA:      return "BrainChip Akida";
        case DTESN_NEURO_DEVICE_DYNAP:      return "SynSense DYNAP";
        case DTESN_NEURO_DEVICE_TRUENORTH:  return "IBM TrueNorth";
        case DTESN_NEURO_DEVICE_GENERIC:    return "Generic Neuromorphic";
        default:                            return "Unknown";
    }
}

void neuro_hal_get_version(uint32_t *major, uint32_t *minor, uint32_t *patch) {
    if (major) *major = DTESN_NEURO_HAL_VERSION_MAJOR;
    if (minor) *minor = DTESN_NEURO_HAL_VERSION_MINOR;
    if (patch) *patch = DTESN_NEURO_HAL_VERSION_PATCH;
}

/* Stub implementations for DMA functions */
int neuro_dma_transfer(dtesn_neuro_device_t *device, const dtesn_neuro_dma_desc_t *desc) {
    if (!device || !desc) {
        return DTESN_NEURO_EINVAL;
    }
    
    /* Find driver for DMA operations */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    if (!driver || !driver->dma_transfer) {
        return DTESN_NEURO_ENOTSUPPORTED;
    }
    
    return driver->dma_transfer(device, desc->src_addr, desc->dst_addr, desc->size, desc->mode);
}

int neuro_dma_status(dtesn_neuro_device_t *device, bool *complete, size_t *bytes_transferred) {
    if (!device || !complete || !bytes_transferred) {
        return DTESN_NEURO_EINVAL;
    }
    
    /* Find driver for DMA status */
    dtesn_neuro_driver_t *driver = NULL;
    for (uint32_t i = 0; i < g_neuro_hal.num_drivers; i++) {
        if (g_neuro_hal.drivers[i].type == device->type) {
            driver = &g_neuro_hal.drivers[i];
            break;
        }
    }
    
    if (!driver || !driver->dma_status) {
        *complete = true;
        *bytes_transferred = 0;
        return 0;
    }
    
    return driver->dma_status(device, complete, bytes_transferred);
}

int neuro_dma_wait(dtesn_neuro_device_t *device, uint32_t timeout_us) {
    if (!device) {
        return DTESN_NEURO_EINVAL;
    }
    
    uint64_t start_time = get_timestamp_ns();
    uint64_t timeout_ns = (uint64_t)timeout_us * 1000;
    
    while (true) {
        bool complete;
        size_t bytes_transferred;
        
        int result = neuro_dma_status(device, &complete, &bytes_transferred);
        if (result != 0) {
            return result;
        }
        
        if (complete) {
            return 0;
        }
        
        /* Check timeout */
        if (timeout_us > 0) {
            uint64_t elapsed = get_timestamp_ns() - start_time;
            if (elapsed >= timeout_ns) {
                return DTESN_NEURO_ETIMEDOUT;
            }
        }
        
        usleep(100); /* 100μs delay */
    }
}