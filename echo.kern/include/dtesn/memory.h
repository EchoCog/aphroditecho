/*
 * DTESN Memory Management System
 * ==============================
 * 
 * Deep Tree Echo State Networks (DTESN) memory allocator based on
 * OEIS A000081 rooted tree enumeration for hierarchical membrane computing.
 * 
 * Performance Requirements:
 * - Allocation latency: ≤ 10μs
 * - Deallocation latency: ≤ 5μs
 * - Fragmentation threshold: ≤ 15%
 * - Memory overhead: ≤ 8%
 * 
 * Memory Layout:
 * - Base address: 0x40000000
 * - Total size: 1GB
 * - Alignment: page-aligned (4KB)
 * - Zones organized by OEIS A000081 enumeration
 */

#ifndef DTESN_MEMORY_H
#define DTESN_MEMORY_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Memory layout constants */
#define DTESN_BASE_ADDRESS    0x40000000UL
#define DTESN_TOTAL_SIZE      (1UL << 30)  /* 1GB */
#define DTESN_PAGE_SIZE       4096         /* 4KB pages */
#define DTESN_MAX_LEVELS      8            /* Maximum membrane levels */

/* OEIS A000081 sequence values for memory layout */
#define DTESN_A000081_SEQUENCE { 1, 1, 2, 4, 9, 20, 48, 115, 286, 719 }

/* Performance thresholds */
#define DTESN_ALLOC_LATENCY_THRESHOLD_US   10   /* ≤ 10μs allocation */
#define DTESN_FREE_LATENCY_THRESHOLD_US     5   /* ≤ 5μs deallocation */
#define DTESN_FRAGMENTATION_THRESHOLD      15   /* ≤ 15% fragmentation */
#define DTESN_OVERHEAD_THRESHOLD            8   /* ≤ 8% memory overhead */

/* Memory zone structure for A000081-based layout */
typedef struct dtesn_memory_zone {
    uint32_t level;              /* Membrane hierarchy level */
    uint32_t membrane_count;     /* Number of membranes per A000081 */
    uint64_t base_offset;        /* Offset from DTESN_BASE_ADDRESS */
    uint64_t zone_size;          /* Size of this zone */
    uint64_t allocated_bytes;    /* Currently allocated bytes */
    uint32_t free_blocks;        /* Number of free blocks */
    void *free_list;             /* Free block list head */
} dtesn_memory_zone_t;

/* Memory statistics structure */
typedef struct dtesn_memory_stats {
    uint64_t total_allocated;    /* Total allocated bytes */
    uint64_t total_free;         /* Total free bytes */
    uint64_t peak_usage;         /* Peak memory usage */
    uint32_t allocation_count;   /* Number of allocations */
    uint32_t deallocation_count; /* Number of deallocations */
    uint32_t fragmentation_pct;  /* Fragmentation percentage */
    uint32_t overhead_pct;       /* Memory overhead percentage */
    uint64_t avg_alloc_time_ns;  /* Average allocation time (ns) */
    uint64_t avg_free_time_ns;   /* Average deallocation time (ns) */
} dtesn_memory_stats_t;

/* Memory pressure callback function type */
typedef void (*dtesn_memory_pressure_callback_t)(uint32_t pressure_level);

/* Core memory management functions */

/**
 * dtesn_mem_init - Initialize DTESN memory management system
 * 
 * Initializes the A000081-based memory zones and sets up the hierarchical
 * allocator for membrane computing structures.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_mem_init(void);

/**
 * dtesn_alloc - Allocate memory for DTESN membrane structures
 * @size: Size of memory to allocate in bytes
 * @membrane_level: Target membrane hierarchy level (0-7)
 * 
 * Allocates memory optimized for the specified membrane level according
 * to OEIS A000081 enumeration. Guarantees ≤10μs allocation latency.
 * 
 * Returns: Pointer to allocated memory, NULL on failure
 */
void *dtesn_alloc(size_t size, uint32_t membrane_level);

/**
 * dtesn_free - Free DTESN-allocated memory
 * @ptr: Pointer to memory to free
 * 
 * Frees memory previously allocated with dtesn_alloc().
 * Guarantees ≤5μs deallocation latency.
 */
void dtesn_free(void *ptr);

/**
 * dtesn_mem_pressure_callback - Set memory pressure callback
 * @callback: Function to call when memory pressure is detected
 * 
 * Registers a callback function to handle memory pressure situations
 * for neuromorphic workloads.
 */
void dtesn_mem_pressure_callback(dtesn_memory_pressure_callback_t callback);

/**
 * dtesn_mem_stats - Get current memory statistics
 * @stats: Pointer to statistics structure to fill
 * 
 * Retrieves comprehensive memory usage and performance statistics.
 * 
 * Returns: 0 on success, negative error code on failure
 */
int dtesn_mem_stats(dtesn_memory_stats_t *stats);

/* Advanced memory management functions */

/**
 * dtesn_mem_validate_a000081 - Validate A000081 compliance
 * @level: Membrane level to validate
 * 
 * Validates that the current memory layout conforms to OEIS A000081
 * enumeration for the specified membrane level.
 * 
 * Returns: true if valid, false otherwise
 */
bool dtesn_mem_validate_a000081(uint32_t level);

/**
 * dtesn_mem_defragment - Defragment memory zones
 * 
 * Performs memory defragmentation while maintaining real-time constraints.
 * 
 * Returns: Number of bytes recovered, negative on error
 */
int64_t dtesn_mem_defragment(void);

/**
 * dtesn_mem_shutdown - Shutdown memory management system
 * 
 * Cleans up and shuts down the DTESN memory management system.
 */
void dtesn_mem_shutdown(void);

/* Error codes */
#define DTESN_ENOMEM        -1  /* Out of memory */
#define DTESN_EINVAL        -2  /* Invalid parameters */
#define DTESN_ENOTINIT      -3  /* System not initialized */
#define DTESN_ELATENCY      -4  /* Latency threshold exceeded */
#define DTESN_EFRAGMENT     -5  /* Fragmentation threshold exceeded */

#ifdef __cplusplus
}
#endif

#endif /* DTESN_MEMORY_H */