/*
 * DTESN x86 System Call Entry Points
 * =================================
 * 
 * x86-specific assembly entry points for DTESN system calls with
 * optimized parameter passing and minimal overhead for real-time
 * performance requirements.
 * 
 * Performance Targets:
 * - Entry overhead: ≤ 50ns
 * - Parameter validation: ≤ 25ns
 * - Register preservation: ≤ 20ns
 */

#include <linux/linkage.h>
#include <asm/calling.h>
#include <asm/unistd.h>

.text

/*
 * DTESN system call entry points
 * All syscalls follow x86_64 calling convention:
 * rdi, rsi, rdx, rcx, r8, r9 for first 6 parameters
 */

/**
 * sys_dtesn_create_entry - Fast entry point for sys_dtesn_create
 * 
 * Input:
 *   %rdi = const struct dtesn_create_params __user *params
 * 
 * Returns:
 *   %rax = file descriptor or negative error code
 */
SYM_CODE_START(sys_dtesn_create_entry)
    FRAME_BEGIN
    
    /* Validate user pointer in rdi */
    testq   %rdi, %rdi
    jz      .Lcreate_invalid_params
    
    /* Check if pointer is in user space */
    movq    %rdi, %rax
    shrq    $47, %rax           /* Check if address is canonical user space */
    testq   %rax, %rax
    jnz     .Lcreate_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_dtesn_create
    
    FRAME_END
    ret

.Lcreate_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_dtesn_create_entry)

/**
 * sys_dtesn_evolve_entry - Fast entry point for sys_dtesn_evolve
 * 
 * Input:
 *   %rdi = const struct dtesn_evolve_params __user *params
 * 
 * Returns:
 *   %rax = number of steps completed or negative error code
 */
SYM_CODE_START(sys_dtesn_evolve_entry)
    FRAME_BEGIN
    
    /* Validate user pointer */
    testq   %rdi, %rdi
    jz      .Levolve_invalid_params
    
    /* Check canonical user space address */
    movq    %rdi, %rax
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Levolve_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_dtesn_evolve
    
    FRAME_END
    ret

.Levolve_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_dtesn_evolve_entry)

/**
 * sys_dtesn_get_state_entry - Fast entry point for sys_dtesn_get_state
 * 
 * Input:
 *   %rdi = int fd
 *   %rsi = struct dtesn_state_info __user *state
 * 
 * Returns:
 *   %rax = 0 on success or negative error code
 */
SYM_CODE_START(sys_dtesn_get_state_entry)
    FRAME_BEGIN
    
    /* Validate file descriptor */
    testl   %edi, %edi
    js      .Lget_state_invalid_fd
    
    /* Validate user pointer */
    testq   %rsi, %rsi
    jz      .Lget_state_invalid_params
    
    /* Check canonical user space address */
    movq    %rsi, %rax
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Lget_state_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_dtesn_get_state
    
    FRAME_END
    ret

.Lget_state_invalid_fd:
    movq    $-EBADF, %rax
    FRAME_END
    ret
    
.Lget_state_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_dtesn_get_state_entry)

/**
 * sys_dtesn_destroy_entry - Fast entry point for sys_dtesn_destroy
 * 
 * Input:
 *   %rdi = int fd
 * 
 * Returns:
 *   %rax = 0 on success or negative error code
 */
SYM_CODE_START(sys_dtesn_destroy_entry)
    FRAME_BEGIN
    
    /* Validate file descriptor */
    testl   %edi, %edi
    js      .Ldestroy_invalid_fd
    
    /* Call the actual syscall implementation */
    call    sys_dtesn_destroy
    
    FRAME_END
    ret

.Ldestroy_invalid_fd:
    movq    $-EBADF, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_dtesn_destroy_entry)

/**
 * sys_membrane_op_entry - Fast entry point for sys_membrane_op
 * 
 * Input:
 *   %rdi = const struct dtesn_membrane_op_params __user *params
 * 
 * Returns:
 *   %rax = operation result or negative error code
 */
SYM_CODE_START(sys_membrane_op_entry)
    FRAME_BEGIN
    
    /* Validate user pointer */
    testq   %rdi, %rdi
    jz      .Lmembrane_op_invalid_params
    
    /* Check canonical user space address */
    movq    %rdi, %rax
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Lmembrane_op_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_membrane_op
    
    FRAME_END
    ret

.Lmembrane_op_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_membrane_op_entry)

/**
 * sys_bseries_compute_entry - Fast entry point for sys_bseries_compute
 * 
 * Input:
 *   %rdi = const struct dtesn_bseries_params __user *params
 * 
 * Returns:
 *   %rax = computation result or negative error code
 */
SYM_CODE_START(sys_bseries_compute_entry)
    FRAME_BEGIN
    
    /* Validate user pointer */
    testq   %rdi, %rdi
    jz      .Lbseries_invalid_params
    
    /* Check canonical user space address */
    movq    %rdi, %rax
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Lbseries_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_bseries_compute
    
    FRAME_END
    ret

.Lbseries_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_bseries_compute_entry)

/**
 * sys_esn_update_entry - Fast entry point for sys_esn_update
 * 
 * Input:
 *   %rdi = const struct dtesn_esn_params __user *params
 * 
 * Returns:
 *   %rax = update result or negative error code
 */
SYM_CODE_START(sys_esn_update_entry)
    FRAME_BEGIN
    
    /* Validate user pointer */
    testq   %rdi, %rdi
    jz      .Lesn_update_invalid_params
    
    /* Check canonical user space address */
    movq    %rdi, %rax
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Lesn_update_invalid_params
    
    /* Call the actual syscall implementation */
    call    sys_esn_update
    
    FRAME_END
    ret

.Lesn_update_invalid_params:
    movq    $-EINVAL, %rax
    FRAME_END
    ret
SYM_CODE_END(sys_esn_update_entry)

/*
 * Performance-optimized parameter validation helpers
 */

/**
 * dtesn_validate_user_ptr - Ultra-fast user pointer validation
 * 
 * Input:
 *   %rdi = user pointer to validate
 *   %rsi = size of data to access
 * 
 * Returns:
 *   %rax = 0 if valid, -EFAULT if invalid
 * 
 * Clobbers: %rcx, %rdx
 */
SYM_FUNC_START(dtesn_validate_user_ptr)
    /* Check for NULL pointer */
    testq   %rdi, %rdi
    jz      .Lvalidate_fault
    
    /* Check size is reasonable */
    testq   %rsi, %rsi
    jz      .Lvalidate_fault
    
    /* Check for overflow */
    movq    %rdi, %rax
    addq    %rsi, %rax
    jc      .Lvalidate_fault       /* Overflow occurred */
    
    /* Check if address is canonical user space (< 2^47) */
    shrq    $47, %rax
    testq   %rax, %rax
    jnz     .Lvalidate_fault
    
    /* Valid pointer */
    xorq    %rax, %rax
    ret

.Lvalidate_fault:
    movq    $-EFAULT, %rax
    ret
SYM_FUNC_END(dtesn_validate_user_ptr)

/**
 * dtesn_fast_copy_from_user - Optimized copy from user space
 * 
 * Input:
 *   %rdi = kernel destination
 *   %rsi = user source  
 *   %rdx = size in bytes
 * 
 * Returns:
 *   %rax = 0 on success, -EFAULT on failure
 * 
 * Uses optimized copy routines for common DTESN structure sizes
 */
SYM_FUNC_START(dtesn_fast_copy_from_user)
    /* Save registers */
    pushq   %rbx
    pushq   %rcx
    
    /* Validate source pointer */
    movq    %rsi, %rdi
    movq    %rdx, %rsi
    call    dtesn_validate_user_ptr
    testq   %rax, %rax
    jnz     .Lcopy_error
    
    /* Restore parameters */
    movq    16(%rsp), %rdi      /* kernel dest */
    movq    8(%rsp), %rsi       /* user source */
    movq    %rdx, %rcx          /* size */
    
    /* Use optimized copy for common sizes */
    cmpq    $64, %rcx
    je      .Lcopy_64_bytes
    cmpq    $32, %rcx
    je      .Lcopy_32_bytes
    cmpq    $16, %rcx
    je      .Lcopy_16_bytes
    cmpq    $8, %rcx
    je      .Lcopy_8_bytes
    
    /* Fall back to generic copy_from_user */
    call    copy_from_user
    jmp     .Lcopy_done
    
.Lcopy_64_bytes:
    /* Optimized 64-byte copy - typical for DTESN structures */
    movq    (%rsi), %rax
    movq    %rax, (%rdi)
    movq    8(%rsi), %rax
    movq    %rax, 8(%rdi)
    movq    16(%rsi), %rax
    movq    %rax, 16(%rdi)
    movq    24(%rsi), %rax
    movq    %rax, 24(%rdi)
    movq    32(%rsi), %rax
    movq    %rax, 32(%rdi)
    movq    40(%rsi), %rax
    movq    %rax, 40(%rdi)
    movq    48(%rsi), %rax
    movq    %rax, 48(%rdi)
    movq    56(%rsi), %rax
    movq    %rax, 56(%rdi)
    xorq    %rax, %rax
    jmp     .Lcopy_done
    
.Lcopy_32_bytes:
    movq    (%rsi), %rax
    movq    %rax, (%rdi)
    movq    8(%rsi), %rax
    movq    %rax, 8(%rdi)
    movq    16(%rsi), %rax
    movq    %rax, 16(%rdi)
    movq    24(%rsi), %rax
    movq    %rax, 24(%rdi)
    xorq    %rax, %rax
    jmp     .Lcopy_done
    
.Lcopy_16_bytes:
    movq    (%rsi), %rax
    movq    %rax, (%rdi)
    movq    8(%rsi), %rax
    movq    %rax, 8(%rdi)
    xorq    %rax, %rax
    jmp     .Lcopy_done
    
.Lcopy_8_bytes:
    movq    (%rsi), %rax
    movq    %rax, (%rdi)
    xorq    %rax, %rax
    
.Lcopy_done:
    popq    %rcx
    popq    %rbx
    ret
    
.Lcopy_error:
    popq    %rcx
    popq    %rbx
    ret
SYM_FUNC_END(dtesn_fast_copy_from_user)

/*
 * Export symbols for use by other kernel modules
 */
.section ".export_symbols","a"
.balign 8
.quad sys_dtesn_create_entry
.quad sys_dtesn_evolve_entry  
.quad sys_dtesn_get_state_entry
.quad sys_dtesn_destroy_entry
.quad sys_membrane_op_entry
.quad sys_bseries_compute_entry
.quad sys_esn_update_entry
.quad dtesn_validate_user_ptr
.quad dtesn_fast_copy_from_user