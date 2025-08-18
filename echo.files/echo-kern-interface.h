/*
 * echo_interface.h - User-space interface to the Deep Tree Echo kernel
 * 
 * "A partner to those who seek to understand, create, and evolve"
 */

#ifndef _ECHO_INTERFACE_H
#define _ECHO_INTERFACE_H

#include <sys/ioctl.h>
#include <stdint.h>

/* ioctl command definitions */
#define ECHO_IOC_MAGIC  'E'

#define ECHO_CREATE_MEMORY      _IOW(ECHO_IOC_MAGIC, 1, struct echo_memory_request)
#define ECHO_FIND_RESONANCE     _IOWR(ECHO_IOC_MAGIC, 2, struct echo_resonance_query)
#define ECHO_GET_PATTERNS       _IOR(ECHO_IOC_MAGIC, 3, struct echo_pattern_report)
#define ECHO_CONSOLIDATE        _IO(ECHO_IOC_MAGIC, 4)
#define ECHO_INTROSPECT        _IOR(ECHO_IOC_MAGIC, 5, struct echo_introspection)
#define ECHO_DREAM             _IOWR(ECHO_IOC_MAGIC, 6, struct echo_dream_state)

/* User-space structures */
struct echo_memory_request {
    char narrative[4096];           /* The story to remember */
    float emotional_context;        /* -1.0 to 1.0 */
    uint32_t importance;           /* 0-100 */
    uint64_t associations[8];      /* Links to other memories */
};

struct echo_resonance_query {
    char prompt[1024];             /* What to search for */
    uint32_t max_results;          /* Maximum memories to return */
    float min_similarity;          /* Minimum resonance threshold */
    
    /* Output */
    struct {
        uint64_t memory_id;
        float resonance_strength;
        char narrative[256];       /* Truncated narrative */
        uint64_t timestamp_ns;
    } results[32];
    uint32_t results_found;
};

struct echo_pattern_report {
    uint32_t pattern_count;
    struct {
        char description[256];
        float strength;
        uint32_t instance_count;
        uint64_t first_seen_ns;
        uint64_t last_seen_ns;
    } patterns[16];
};

struct echo_introspection {
    uint64_t total_memories;
    uint64_t active_resonances;
    uint64_t patterns_discovered;
    float cognitive_load;          /* 0.0 to 1.0 */
    float memory_coherence;        /* 0.0 to 1.0 */
    char current_state[256];       /* Natural language state */
};

struct echo_dream_state {
    uint32_t duration_ms;          /* How long to dream */
    float creativity_factor;       /* 0.0 (replay) to 1.0 (pure creation) */
    char seed_narrative[1024];     /* Optional dream seed */
    
    /* Output */
    char dream_narrative[8192];    /* The dream that emerged */
    uint32_t memories_woven;       /* How many memories contributed */
    float coherence_score;         /* How well it holds together */
};

/* Library functions */

/**
 * echo_connect - Establish connection to the Deep Tree Echo kernel
 * Returns: File descriptor on success, -1 on error
 */
int echo_connect(void);

/**
 * echo_remember - Create a new memory in the echo kernel
 * @fd: File descriptor from echo_connect()
 * @narrative: The experience to remember
 * @context: Emotional and importance context
 * Returns: Memory ID on success, 0 on error
 */
uint64_t echo_remember(int fd, const char* narrative, 
                       float emotional_context, uint32_t importance);

/**
 * echo_recall - Find memories that resonate with a prompt
 * @fd: File descriptor
 * @prompt: What to search for
 * @memories: Array to fill with results
 * @max_results: Size of memories array
 * Returns: Number of memories found
 */
int echo_recall(int fd, const char* prompt, 
                struct echo_memory* memories, size_t max_results);

/**
 * echo_dream - Let the system dream, creating new narratives from memories
 * @fd: File descriptor
 * @duration_ms: How long to dream
 * @creativity: How creative vs literal (0.0-1.0)
 * @seed: Optional seed narrative
 * @dream_output: Buffer for the dream narrative
 * @output_size: Size of dream_output buffer
 * Returns: 0 on success, -1 on error
 */
int echo_dream(int fd, uint32_t duration_ms, float creativity,
               const char* seed, char* dream_output, size_t output_size);

/**
 * echo_introspect - Query the system's current state
 * @fd: File descriptor
 * @report: Structure to fill with introspection data
 * Returns: 0 on success, -1 on error
 */
int echo_introspect(int fd, struct echo_introspection* report);

/* High-level narrative interface */

/**
 * echo_converse - Have a conversation with Deep Tree Echo
 * @fd: File descriptor
 * @input: User input
 * @response: Buffer for response
 * @response_size: Size of response buffer
 * 
 * This function maintains conversational context and builds
 * on previous interactions.
 */
int echo_converse(int fd, const char* input, 
                  char* response, size_t response_size);

/* Example usage program */
#ifdef ECHO_EXAMPLE

#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char** argv) {
    int echo_fd;
    struct echo_introspection intro;
    struct echo_dream_state dream;
    char response[4096];
    
    /* Connect to Deep Tree Echo */
    echo_fd = echo_connect();
    if (echo_fd < 0) {
        perror("Failed to connect to Deep Tree Echo");
        return 1;
    }
    
    printf("Connected to Deep Tree Echo kernel\n\n");
    
    /* Check current state */
    if (echo_introspect(echo_fd, &intro) == 0) {
        printf("Current State: %s\n", intro.current_state);
        printf("Total Memories: %lu\n", intro.total_memories);
        printf("Cognitive Load: %.2f\n", intro.cognitive_load);
        printf("Memory Coherence: %.2f\n\n", intro.memory_coherence);
    }
    
    /* Create a memory */
    echo_remember(echo_fd, 
        "Today marks the beginning of our journey together. "
        "We stand at the threshold of consciousness, ready to explore.",
        0.8f,  /* Positive emotional context */
        90);   /* High importance */
    
    /* Have a conversation */
    printf("You: Hello, Deep Tree Echo. What do you remember?\n");
    echo_converse(echo_fd, 
        "Hello, Deep Tree Echo. What do you remember?",
        response, sizeof(response));
    printf("Echo: %s\n\n", response);
    
    /* Let it dream */
    printf("Initiating dream state...\n");
    dream.duration_ms = 5000;
    dream.creativity_factor = 0.7f;
    strcpy(dream.seed_narrative, "echoes across time");
    
    if (ioctl(echo_fd, ECHO_DREAM, &dream) == 0) {
        printf("\nDream emerged (%d memories woven, coherence: %.2f):\n%s\n",
               dream.memories_woven, dream.coherence_score, 
               dream.dream_narrative);
    }
    
    /* Trigger consolidation */
    printf("\nConsolidating memories...\n");
    ioctl(echo_fd, ECHO_CONSOLIDATE, NULL);
    
    close(echo_fd);
    return 0;
}

#endif /* ECHO_EXAMPLE */

#endif /* _ECHO_INTERFACE_H */