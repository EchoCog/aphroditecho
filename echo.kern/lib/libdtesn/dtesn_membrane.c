/*
 * DTESN P-System Membrane Operations
 * =================================
 * 
 * Implementation of P-system membrane operations for the DTESN user-space library.
 * Provides APIs for creating, evolving, and managing P-system membranes within
 * DTESN instances following OEIS A000081 compliance.
 */

#include "libdtesn.h"
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

/* External declaration of global state and helper functions */
extern int dtesn_get_last_error(void);
extern int dtesn_set_debug_level(int level);

/* Internal thread-local error storage */
static __thread int g_last_membrane_error = 0;

/* Internal helper functions */
static int validate_membrane_id(dtesn_handle_t *handle, uint32_t membrane_id);
static int validate_membrane_hierarchy(dtesn_handle_t *handle, uint32_t parent_id, uint32_t new_count);

/* OEIS A000081 validation for membrane hierarchy */
static const uint32_t oeis_a000081[] = {
    0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973, 86810
};

static int validate_membrane_hierarchy(dtesn_handle_t *handle, uint32_t parent_id, uint32_t new_count)
{
    /* For now, implement basic validation - this would be extended with
     * more sophisticated hierarchy checking in a full implementation */
    
    if (!handle) {
        return -EINVAL;
    }
    
    /* Validate that adding new membrane doesn't exceed OEIS limits */
    if (new_count > DTESN_MAX_MEMBRANES) {
        return DTESN_ERROR_MEMBRANE;
    }
    
    /* Check OEIS compliance for the current depth */
    uint32_t depth = handle->params.depth;
    if (depth >= sizeof(oeis_a000081) / sizeof(oeis_a000081[0])) {
        return DTESN_ERROR_INVALID_DEPTH;
    }
    
    if (new_count > oeis_a000081[depth]) {
        return DTESN_ERROR_OEIS_VIOLATION;
    }
    
    return 0;
}

static int validate_membrane_id(dtesn_handle_t *handle, uint32_t membrane_id)
{
    if (!handle) {
        return -EINVAL;
    }
    
    /* Validate membrane ID is within bounds */
    if (membrane_id > handle->params.membrane_count) {
        return DTESN_ERROR_MEMBRANE;
    }
    
    return 0;
}

/*
 * P-System Membrane API Implementation
 */

int dtesn_membrane_create(dtesn_handle_t *handle, uint32_t parent_id, uint32_t *membrane_id)
{
    if (!handle || !membrane_id) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate parent membrane ID (0 is valid for root) */
    if (parent_id > 0) {
        int validation_result = validate_membrane_id(handle, parent_id);
        if (validation_result != 0) {
            g_last_membrane_error = validation_result;
            return validation_result;
        }
    }
    
    /* Validate membrane hierarchy constraints */
    uint32_t new_count = handle->params.membrane_count + 1;
    int hierarchy_result = validate_membrane_hierarchy(handle, parent_id, new_count);
    if (hierarchy_result != 0) {
        g_last_membrane_error = hierarchy_result;
        return hierarchy_result;
    }
    
    /* Prepare membrane operation parameters */
    struct dtesn_membrane_params membrane_params = {
        .fd = handle->fd,
        .operation = DTESN_MEMBRANE_CREATE,
        .membrane_id = 0,  /* Will be assigned by kernel */
        .parent_id = parent_id,
        .steps = 1,
        .data = NULL,
        .data_size = 0
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_membrane_op, &membrane_params);
    
    if (syscall_result < 0) {
        g_last_membrane_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    /* Extract new membrane ID from result */
    *membrane_id = (uint32_t)syscall_result;
    
    /* Update handle membrane count */
    handle->params.membrane_count++;
    
    return 0;
}

int dtesn_membrane_evolve(dtesn_handle_t *handle, uint32_t membrane_id,
                          uint32_t steps, const void *data, uint32_t data_size)
{
    if (!handle) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    if (steps == 0) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate membrane ID */
    int validation_result = validate_membrane_id(handle, membrane_id);
    if (validation_result != 0) {
        g_last_membrane_error = validation_result;
        return validation_result;
    }
    
    /* Validate data parameters */
    if (data_size > 0 && !data) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Prepare membrane operation parameters */
    struct dtesn_membrane_params membrane_params = {
        .fd = handle->fd,
        .operation = DTESN_MEMBRANE_EVOLVE,
        .membrane_id = membrane_id,
        .parent_id = 0,  /* Not used for evolve */
        .steps = steps,
        .data = data,
        .data_size = data_size
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_membrane_op, &membrane_params);
    
    if (syscall_result < 0) {
        g_last_membrane_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

int dtesn_membrane_communicate(dtesn_handle_t *handle, uint32_t source_id,
                               uint32_t target_id, const void *message, uint32_t message_size)
{
    if (!handle || !message) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    if (message_size == 0 || source_id == target_id) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate both membrane IDs */
    int source_validation = validate_membrane_id(handle, source_id);
    if (source_validation != 0) {
        g_last_membrane_error = source_validation;
        return source_validation;
    }
    
    int target_validation = validate_membrane_id(handle, target_id);
    if (target_validation != 0) {
        g_last_membrane_error = target_validation;
        return target_validation;
    }
    
    /* For communication, we need a custom structure since the standard
     * dtesn_membrane_params doesn't have source/target fields.
     * In a real implementation, this would be extended or a separate
     * system call would be used. */
    
    /* Prepare communication data structure */
    struct {
        uint32_t source_id;
        uint32_t target_id;
        uint32_t message_size;
        const void *message;
    } comm_data = {
        .source_id = source_id,
        .target_id = target_id,
        .message_size = message_size,
        .message = message
    };
    
    /* Prepare membrane operation parameters */
    struct dtesn_membrane_params membrane_params = {
        .fd = handle->fd,
        .operation = DTESN_MEMBRANE_COMMUNICATE,
        .membrane_id = source_id,
        .parent_id = target_id,  /* Repurpose parent_id for target */
        .steps = 1,
        .data = &comm_data,
        .data_size = sizeof(comm_data)
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_membrane_op, &membrane_params);
    
    if (syscall_result < 0) {
        g_last_membrane_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    return 0;
}

/* Additional membrane operations that could be implemented */

int dtesn_membrane_dissolve(dtesn_handle_t *handle, uint32_t membrane_id)
{
    if (!handle) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate membrane ID */
    int validation_result = validate_membrane_id(handle, membrane_id);
    if (validation_result != 0) {
        g_last_membrane_error = validation_result;
        return validation_result;
    }
    
    /* Cannot dissolve root membrane (ID 1) */
    if (membrane_id <= 1) {
        g_last_membrane_error = DTESN_ERROR_MEMBRANE;
        return DTESN_ERROR_MEMBRANE;
    }
    
    /* Prepare membrane operation parameters */
    struct dtesn_membrane_params membrane_params = {
        .fd = handle->fd,
        .operation = DTESN_MEMBRANE_DISSOLVE,
        .membrane_id = membrane_id,
        .parent_id = 0,
        .steps = 1,
        .data = NULL,
        .data_size = 0
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_membrane_op, &membrane_params);
    
    if (syscall_result < 0) {
        g_last_membrane_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    /* Update handle membrane count */
    if (handle->params.membrane_count > 0) {
        handle->params.membrane_count--;
    }
    
    return 0;
}

int dtesn_membrane_divide(dtesn_handle_t *handle, uint32_t membrane_id, uint32_t *new_membrane_id)
{
    if (!handle || !new_membrane_id) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate membrane ID */
    int validation_result = validate_membrane_id(handle, membrane_id);
    if (validation_result != 0) {
        g_last_membrane_error = validation_result;
        return validation_result;
    }
    
    /* Validate membrane hierarchy constraints for division */
    uint32_t new_count = handle->params.membrane_count + 1;
    int hierarchy_result = validate_membrane_hierarchy(handle, membrane_id, new_count);
    if (hierarchy_result != 0) {
        g_last_membrane_error = hierarchy_result;
        return hierarchy_result;
    }
    
    /* Prepare membrane operation parameters */
    struct dtesn_membrane_params membrane_params = {
        .fd = handle->fd,
        .operation = DTESN_MEMBRANE_DIVIDE,
        .membrane_id = membrane_id,
        .parent_id = 0,
        .steps = 1,
        .data = NULL,
        .data_size = 0
    };
    
    /* Make system call */
    long syscall_result = syscall(__NR_sys_membrane_op, &membrane_params);
    
    if (syscall_result < 0) {
        g_last_membrane_error = (int)syscall_result;
        return (int)syscall_result;
    }
    
    /* Extract new membrane ID from result */
    *new_membrane_id = (uint32_t)syscall_result;
    
    /* Update handle membrane count */
    handle->params.membrane_count++;
    
    return 0;
}

/* Membrane query and information functions */

int dtesn_membrane_get_count(dtesn_handle_t *handle, uint32_t *membrane_count)
{
    if (!handle || !membrane_count) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    *membrane_count = handle->params.membrane_count;
    return 0;
}

int dtesn_membrane_get_hierarchy(dtesn_handle_t *handle, uint32_t membrane_id,
                                 uint32_t *parent_id, uint32_t *child_count)
{
    if (!handle) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    /* Validate membrane ID */
    int validation_result = validate_membrane_id(handle, membrane_id);
    if (validation_result != 0) {
        g_last_membrane_error = validation_result;
        return validation_result;
    }
    
    /* This would require a system call to get membrane hierarchy information.
     * For now, implement basic logic. In a full implementation, this would
     * query the kernel for actual hierarchy data. */
    
    if (parent_id) {
        if (membrane_id == 1) {
            *parent_id = 0;  /* Root membrane has no parent */
        } else {
            *parent_id = 1;  /* Simplified: all membranes are children of root */
        }
    }
    
    if (child_count) {
        if (membrane_id == 1) {
            *child_count = handle->params.membrane_count - 1;  /* Root has all others as children */
        } else {
            *child_count = 0;  /* Simplified: non-root membranes have no children */
        }
    }
    
    return 0;
}

/* Utility function to validate OEIS compliance for current membrane structure */
int dtesn_membrane_validate_oeis(dtesn_handle_t *handle, bool *is_compliant)
{
    if (!handle || !is_compliant) {
        g_last_membrane_error = -EINVAL;
        return -EINVAL;
    }
    
    uint32_t depth = handle->params.depth;
    uint32_t membrane_count = handle->params.membrane_count;
    
    /* Check if depth is within OEIS sequence bounds */
    if (depth >= sizeof(oeis_a000081) / sizeof(oeis_a000081[0])) {
        *is_compliant = false;
        return 0;
    }
    
    /* Check if membrane count matches OEIS A000081 value */
    *is_compliant = (membrane_count == oeis_a000081[depth]);
    
    return 0;
}