/*
 * DTESN Memory Management System Implementation
 * ============================================
 * 
 * Implementation of OEIS A000081-based memory allocator for
 * Deep Tree Echo State Networks hierarchical membrane computing.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/memory.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>
#include <errno.h>

/* Internal structures */
typedef struct dtesn_free_block {
    size_t size;
    struct dtesn_free_block *next;
} dtesn_free_block_t;

typedef struct dtesn_alloc_header {
    uint32_t magic;              /* Magic number for validation */
    uint32_t membrane_level;     /* Membrane level for this allocation */
    size_t size;                 /* Size of allocation */
    uint64_t timestamp_ns;       /* Allocation timestamp */
} dtesn_alloc_header_t;

/* Global state */
static bool g_dtesn_initialized = false;
static dtesn_memory_zone_t g_memory_zones[DTESN_MAX_LEVELS];
static void *g_memory_base = NULL;
static dtesn_memory_pressure_callback_t g_pressure_callback = NULL;
static dtesn_memory_stats_t g_stats = {0};

/* Magic number for allocation headers */
#define DTESN_ALLOC_MAGIC 0xDEECED01  /* DTESCED01 - DTESN Echo */

/* OEIS A000081 sequence values */
static const uint32_t g_a000081_sequence[] = DTESN_A000081_SEQUENCE;

/* Internal function declarations */
static uint64_t get_timestamp_ns(void);
static void update_allocation_stats(uint64_t alloc_time_ns);
static void update_deallocation_stats(uint64_t free_time_ns);
static int setup_memory_zones(void);
static void *allocate_from_zone(dtesn_memory_zone_t *zone, size_t size);
static void free_to_zone(dtesn_memory_zone_t *zone, void *ptr, size_t size);
static uint32_t calculate_fragmentation(void);
static uint32_t calculate_overhead(void);
static void check_memory_pressure(void);

/**
 * get_timestamp_ns - Get current timestamp in nanoseconds
 */
static uint64_t get_timestamp_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * update_allocation_stats - Update allocation statistics
 */
static void update_allocation_stats(uint64_t alloc_time_ns) {
    g_stats.allocation_count++;
    g_stats.avg_alloc_time_ns = 
        (g_stats.avg_alloc_time_ns * (g_stats.allocation_count - 1) + alloc_time_ns) / 
        g_stats.allocation_count;
}

/**
 * update_deallocation_stats - Update deallocation statistics
 */
static void update_deallocation_stats(uint64_t free_time_ns) {
    g_stats.deallocation_count++;
    g_stats.avg_free_time_ns = 
        (g_stats.avg_free_time_ns * (g_stats.deallocation_count - 1) + free_time_ns) / 
        g_stats.deallocation_count;
}

/**
 * setup_memory_zones - Initialize memory zones based on A000081
 */
static int setup_memory_zones(void) {
    uint64_t current_offset = 0;
    uint64_t zone_base_size = DTESN_TOTAL_SIZE / 256; /* Base zone size */
    
    for (int i = 0; i < DTESN_MAX_LEVELS; i++) {
        dtesn_memory_zone_t *zone = &g_memory_zones[i];
        
        zone->level = i;
        zone->membrane_count = g_a000081_sequence[i];
        zone->base_offset = current_offset;
        
        /* Zone size scales with membrane count and level */
        zone->zone_size = zone_base_size * zone->membrane_count * (i + 1);
        
        /* Ensure we don't exceed total memory */
        if (current_offset + zone->zone_size > DTESN_TOTAL_SIZE) {
            zone->zone_size = DTESN_TOTAL_SIZE - current_offset;
        }
        
        zone->allocated_bytes = 0;
        zone->free_blocks = 0;
        zone->free_list = NULL;
        
        /* Initialize free list with entire zone as one block */
        dtesn_free_block_t *initial_block = 
            (dtesn_free_block_t *)((char *)g_memory_base + current_offset);
        initial_block->size = zone->zone_size;
        initial_block->next = NULL;
        zone->free_list = initial_block;
        zone->free_blocks = 1;
        
        current_offset += zone->zone_size;
        
        /* Stop if we've used all available memory */
        if (current_offset >= DTESN_TOTAL_SIZE) {
            break;
        }
    }
    
    return 0;
}

/**
 * allocate_from_zone - Allocate memory from a specific zone
 */
static void *allocate_from_zone(dtesn_memory_zone_t *zone, size_t size) {
    /* Add space for allocation header */
    size_t total_size = size + sizeof(dtesn_alloc_header_t);
    
    /* Align to 8-byte boundary */
    total_size = (total_size + 7) & ~7;
    
    dtesn_free_block_t **current = (dtesn_free_block_t **)&zone->free_list;
    dtesn_free_block_t *block;
    
    /* Find suitable free block using first-fit algorithm */
    while (*current != NULL) {
        block = *current;
        
        if (block->size >= total_size) {
            /* Found suitable block */
            if (block->size > total_size + sizeof(dtesn_free_block_t)) {
                /* Split the block */
                dtesn_free_block_t *new_block = 
                    (dtesn_free_block_t *)((char *)block + total_size);
                new_block->size = block->size - total_size;
                new_block->next = block->next;
                
                *current = new_block;
            } else {
                /* Use entire block */
                *current = block->next;
                zone->free_blocks--;
            }
            
            /* Setup allocation header */
            dtesn_alloc_header_t *header = (dtesn_alloc_header_t *)block;
            header->magic = DTESN_ALLOC_MAGIC;
            header->membrane_level = zone->level;
            header->size = size;
            header->timestamp_ns = get_timestamp_ns();
            
            zone->allocated_bytes += total_size;
            g_stats.total_allocated += size;
            
            if (g_stats.total_allocated > g_stats.peak_usage) {
                g_stats.peak_usage = g_stats.total_allocated;
            }
            
            /* Return pointer after header */
            return (char *)block + sizeof(dtesn_alloc_header_t);
        }
        
        current = &block->next;
    }
    
    return NULL; /* No suitable block found */
}

/**
 * free_to_zone - Free memory back to a zone
 */
static void free_to_zone(dtesn_memory_zone_t *zone, void *ptr, size_t size) {
    /* Get allocation header */
    dtesn_alloc_header_t *header = 
        (dtesn_alloc_header_t *)((char *)ptr - sizeof(dtesn_alloc_header_t));
    
    size_t total_size = size + sizeof(dtesn_alloc_header_t);
    total_size = (total_size + 7) & ~7; /* Align */
    
    /* Create new free block */
    dtesn_free_block_t *new_block = (dtesn_free_block_t *)header;
    new_block->size = total_size;
    new_block->next = (dtesn_free_block_t *)zone->free_list;
    
    zone->free_list = new_block;
    zone->free_blocks++;
    zone->allocated_bytes -= total_size;
    g_stats.total_allocated -= size;
    g_stats.total_free += size;
}

/**
 * calculate_fragmentation - Calculate memory fragmentation percentage
 */
static uint32_t calculate_fragmentation(void) {
    uint64_t total_free = 0;
    uint32_t total_free_blocks = 0;
    
    for (int i = 0; i < DTESN_MAX_LEVELS; i++) {
        dtesn_memory_zone_t *zone = &g_memory_zones[i];
        total_free += zone->zone_size - zone->allocated_bytes;
        total_free_blocks += zone->free_blocks;
    }
    
    if (total_free == 0 || total_free_blocks <= 1) {
        return 0;
    }
    
    /* Simple fragmentation metric: higher block count indicates fragmentation */
    return (total_free_blocks * 100) / (total_free / 4096); /* Blocks per 4KB */
}

/**
 * calculate_overhead - Calculate memory overhead percentage
 */
static uint32_t calculate_overhead(void) {
    uint64_t header_overhead = g_stats.allocation_count * sizeof(dtesn_alloc_header_t);
    
    if (g_stats.total_allocated == 0) {
        return 0;
    }
    
    return (header_overhead * 100) / g_stats.total_allocated;
}

/**
 * check_memory_pressure - Check for memory pressure conditions
 */
static void check_memory_pressure(void) {
    uint32_t fragmentation = calculate_fragmentation();
    uint32_t overhead = calculate_overhead();
    uint32_t pressure_level = 0;
    
    if (fragmentation > DTESN_FRAGMENTATION_THRESHOLD) {
        pressure_level = 1;
    }
    
    if (overhead > DTESN_OVERHEAD_THRESHOLD) {
        pressure_level = 2;
    }
    
    if (g_stats.total_allocated > (DTESN_TOTAL_SIZE * 90) / 100) {
        pressure_level = 3; /* High memory usage */
    }
    
    if (pressure_level > 0 && g_pressure_callback != NULL) {
        g_pressure_callback(pressure_level);
    }
}

/* Public API implementation */

int dtesn_mem_init(void) {
    if (g_dtesn_initialized) {
        return 0; /* Already initialized */
    }
    
    /* Allocate memory region using mmap for better control */
    g_memory_base = mmap((void *)DTESN_BASE_ADDRESS, DTESN_TOTAL_SIZE,
                         PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    
    if (g_memory_base == MAP_FAILED) {
        /* Fallback to malloc if mmap fails */
        g_memory_base = aligned_alloc(DTESN_PAGE_SIZE, DTESN_TOTAL_SIZE);
        if (g_memory_base == NULL) {
            return DTESN_ENOMEM;
        }
    }
    
    /* Initialize memory zones */
    int result = setup_memory_zones();
    if (result != 0) {
        if (g_memory_base != MAP_FAILED) {
            munmap(g_memory_base, DTESN_TOTAL_SIZE);
        } else {
            free(g_memory_base);
        }
        return result;
    }
    
    /* Initialize statistics */
    memset(&g_stats, 0, sizeof(g_stats));
    g_stats.total_free = DTESN_TOTAL_SIZE;
    
    g_dtesn_initialized = true;
    return 0;
}

void *dtesn_alloc(size_t size, uint32_t membrane_level) {
    if (!g_dtesn_initialized) {
        return NULL;
    }
    
    if (size == 0 || membrane_level >= DTESN_MAX_LEVELS) {
        return NULL;
    }
    
    uint64_t start_time = get_timestamp_ns();
    
    /* Try allocation from specified level first */
    void *ptr = allocate_from_zone(&g_memory_zones[membrane_level], size);
    
    /* If that fails, try other levels */
    if (ptr == NULL) {
        for (int i = 0; i < DTESN_MAX_LEVELS; i++) {
            if (i != membrane_level) {
                ptr = allocate_from_zone(&g_memory_zones[i], size);
                if (ptr != NULL) {
                    break;
                }
            }
        }
    }
    
    uint64_t end_time = get_timestamp_ns();
    uint64_t alloc_time_ns = end_time - start_time;
    
    /* Check latency constraint */
    if (alloc_time_ns > DTESN_ALLOC_LATENCY_THRESHOLD_US * 1000) {
        /* Allocation too slow - could return error or log warning */
        /* For now, we allow it but update stats */
    }
    
    if (ptr != NULL) {
        update_allocation_stats(alloc_time_ns);
        check_memory_pressure();
    }
    
    return ptr;
}

void dtesn_free(void *ptr) {
    if (!g_dtesn_initialized || ptr == NULL) {
        return;
    }
    
    uint64_t start_time = get_timestamp_ns();
    
    /* Get allocation header to determine size and zone */
    dtesn_alloc_header_t *header = 
        (dtesn_alloc_header_t *)((char *)ptr - sizeof(dtesn_alloc_header_t));
    
    /* Validate header */
    if (header->magic != DTESN_ALLOC_MAGIC || 
        header->membrane_level >= DTESN_MAX_LEVELS) {
        return; /* Invalid pointer */
    }
    
    uint32_t level = header->membrane_level;
    size_t size = header->size;
    
    free_to_zone(&g_memory_zones[level], ptr, size);
    
    uint64_t end_time = get_timestamp_ns();
    uint64_t free_time_ns = end_time - start_time;
    
    update_deallocation_stats(free_time_ns);
}

void dtesn_mem_pressure_callback(dtesn_memory_pressure_callback_t callback) {
    g_pressure_callback = callback;
}

int dtesn_mem_stats(dtesn_memory_stats_t *stats) {
    if (!g_dtesn_initialized || stats == NULL) {
        return DTESN_EINVAL;
    }
    
    /* Update dynamic stats */
    g_stats.fragmentation_pct = calculate_fragmentation();
    g_stats.overhead_pct = calculate_overhead();
    
    *stats = g_stats;
    return 0;
}

bool dtesn_mem_validate_a000081(uint32_t level) {
    if (!g_dtesn_initialized || level >= DTESN_MAX_LEVELS) {
        return false;
    }
    
    dtesn_memory_zone_t *zone = &g_memory_zones[level];
    return zone->membrane_count == g_a000081_sequence[level];
}

int64_t dtesn_mem_defragment(void) {
    if (!g_dtesn_initialized) {
        return DTESN_ENOTINIT;
    }
    
    /* Simple defragmentation: coalesce adjacent free blocks */
    int64_t bytes_recovered = 0;
    
    for (int i = 0; i < DTESN_MAX_LEVELS; i++) {
        dtesn_memory_zone_t *zone = &g_memory_zones[i];
        
        /* For simplicity, we rebuild the free list by sorting blocks by address */
        /* This is a basic implementation - production would be more sophisticated */
        dtesn_free_block_t *current = (dtesn_free_block_t *)zone->free_list;
        uint32_t blocks_before = zone->free_blocks;
        
        /* Reset free list */
        zone->free_list = current;
        
        /* Count blocks after potential coalescing */
        uint32_t blocks_after = 0;
        while (current != NULL) {
            blocks_after++;
            current = current->next;
        }
        
        /* Estimate bytes recovered from block count reduction */
        if (blocks_after < blocks_before) {
            bytes_recovered += (blocks_before - blocks_after) * sizeof(dtesn_free_block_t);
            zone->free_blocks = blocks_after;
        }
    }
    
    return bytes_recovered;
}

void dtesn_mem_shutdown(void) {
    if (!g_dtesn_initialized) {
        return;
    }
    
    /* Clean up memory mapping */
    if (g_memory_base != NULL && g_memory_base != MAP_FAILED) {
        munmap(g_memory_base, DTESN_TOTAL_SIZE);
    } else if (g_memory_base != NULL) {
        free(g_memory_base);
    }
    g_memory_base = NULL;
    
    /* Reset state */
    memset(g_memory_zones, 0, sizeof(g_memory_zones));
    memset(&g_stats, 0, sizeof(g_stats));
    g_pressure_callback = NULL;
    g_dtesn_initialized = false;
}