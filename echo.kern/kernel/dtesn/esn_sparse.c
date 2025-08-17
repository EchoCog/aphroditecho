/*
 * DTESN ESN Sparse Matrix Operations
 * =================================
 * 
 * High-performance sparse matrix operations for ESN reservoir computing
 * with optimized memory layout and vectorized operations.
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include "include/dtesn/esn.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

/* Internal performance tracking */
static struct {
    uint64_t total_multiplies;
    uint64_t total_mult_time_ns;
} g_sparse_stats = {0};

/* Forward declarations */
static int dtesn_esn_sparse_matrix_validate(const dtesn_esn_sparse_matrix_t *matrix);
static uint64_t dtesn_esn_sparse_get_time_ns(void);

/**
 * Get current time in nanoseconds
 */
static uint64_t dtesn_esn_sparse_get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/**
 * Validate sparse matrix structure
 */
static int dtesn_esn_sparse_matrix_validate(const dtesn_esn_sparse_matrix_t *matrix) {
    if (!matrix) {
        return DTESN_ESN_EINVAL;
    }
    
    if (matrix->rows == 0 || matrix->cols == 0) {
        return DTESN_ESN_EINVAL;
    }
    
    if (matrix->nnz == 0) {
        return 0; /* Empty matrix is valid */
    }
    
    if (!matrix->row_ptr || !matrix->col_idx || !matrix->values) {
        return DTESN_ESN_EINVAL;
    }
    
    /* Validate CSR format */
    if (matrix->row_ptr[0] != 0) {
        return DTESN_ESN_EINVAL;
    }
    
    if (matrix->row_ptr[matrix->rows] != matrix->nnz) {
        return DTESN_ESN_EINVAL;
    }
    
    /* Check row pointers are non-decreasing */
    for (uint32_t i = 0; i < matrix->rows; i++) {
        if (matrix->row_ptr[i] > matrix->row_ptr[i + 1]) {
            return DTESN_ESN_EINVAL;
        }
    }
    
    /* Check column indices are within bounds and sorted within each row */
    for (uint32_t i = 0; i < matrix->rows; i++) {
        uint32_t start = matrix->row_ptr[i];
        uint32_t end = matrix->row_ptr[i + 1];
        
        for (uint32_t j = start; j < end; j++) {
            if (matrix->col_idx[j] >= matrix->cols) {
                return DTESN_ESN_EINVAL;
            }
            
            if (j > start && matrix->col_idx[j] <= matrix->col_idx[j - 1]) {
                return DTESN_ESN_EINVAL; /* Not sorted or duplicate */
            }
        }
    }
    
    return 0;
}

dtesn_esn_sparse_matrix_t *dtesn_esn_sparse_matrix_create(uint32_t rows, uint32_t cols, float sparsity) {
    if (rows == 0 || cols == 0 || sparsity <= 0.0f || sparsity > 1.0f) {
        return NULL;
    }
    
    dtesn_esn_sparse_matrix_t *matrix = calloc(1, sizeof(dtesn_esn_sparse_matrix_t));
    if (!matrix) {
        return NULL;
    }
    
    matrix->rows = rows;
    matrix->cols = cols;
    matrix->sparsity = sparsity;
    matrix->is_symmetric = false;
    
    /* Estimate number of non-zeros */
    uint64_t total_elements = (uint64_t)rows * cols;
    matrix->nnz = (uint32_t)(total_elements * sparsity);
    
    /* Ensure minimum connectivity for small matrices */
    if (matrix->nnz < rows && sparsity > 0.0f) {
        matrix->nnz = rows;
    }
    
    /* Allocate CSR arrays */
    matrix->row_ptr = calloc(rows + 1, sizeof(uint32_t));
    matrix->col_idx = calloc(matrix->nnz, sizeof(uint32_t));
    matrix->values = calloc(matrix->nnz, sizeof(float));
    
    if (!matrix->row_ptr || !matrix->col_idx || !matrix->values) {
        dtesn_esn_sparse_matrix_destroy(matrix);
        return NULL;
    }
    
    /* Generate random sparse structure */
    srand((unsigned int)time(NULL));
    
    uint32_t current_nnz = 0;
    matrix->row_ptr[0] = 0;
    
    for (uint32_t i = 0; i < rows && current_nnz < matrix->nnz; i++) {
        /* Determine number of connections for this row */
        uint32_t row_connections = (uint32_t)(cols * sparsity);
        if (row_connections == 0 && sparsity > 0.0f) {
            row_connections = 1;
        }
        
        /* Ensure we don't exceed total nnz budget */
        if (current_nnz + row_connections > matrix->nnz) {
            row_connections = matrix->nnz - current_nnz;
        }
        
        /* Generate random column indices for this row */
        bool *selected = calloc(cols, sizeof(bool));
        if (!selected) {
            dtesn_esn_sparse_matrix_destroy(matrix);
            return NULL;
        }
        
        uint32_t connections_added = 0;
        while (connections_added < row_connections) {
            uint32_t col = rand() % cols;
            if (!selected[col]) {
                selected[col] = true;
                matrix->col_idx[current_nnz + connections_added] = col;
                connections_added++;
            }
        }
        
        /* Sort column indices for this row */
        for (uint32_t j = 0; j < connections_added - 1; j++) {
            for (uint32_t k = j + 1; k < connections_added; k++) {
                uint32_t j_idx = current_nnz + j;
                uint32_t k_idx = current_nnz + k;
                if (matrix->col_idx[j_idx] > matrix->col_idx[k_idx]) {
                    uint32_t temp = matrix->col_idx[j_idx];
                    matrix->col_idx[j_idx] = matrix->col_idx[k_idx];
                    matrix->col_idx[k_idx] = temp;
                }
            }
        }
        
        current_nnz += connections_added;
        matrix->row_ptr[i + 1] = current_nnz;
        
        free(selected);
    }
    
    /* Update actual nnz */
    matrix->nnz = current_nnz;
    
    /* Validate the created matrix */
    if (dtesn_esn_sparse_matrix_validate(matrix) != 0) {
        dtesn_esn_sparse_matrix_destroy(matrix);
        return NULL;
    }
    
    return matrix;
}

void dtesn_esn_sparse_matrix_destroy(dtesn_esn_sparse_matrix_t *matrix) {
    if (!matrix) {
        return;
    }
    
    free(matrix->row_ptr);
    free(matrix->col_idx);
    free(matrix->values);
    free(matrix);
}

int esn_sparse_multiply(const dtesn_esn_sparse_matrix_t *matrix, const float *input, float *output) {
    if (!matrix || !input || !output) {
        return DTESN_ESN_EINVAL;
    }
    
    uint64_t start_time = dtesn_esn_sparse_get_time_ns();
    
    /* Validate matrix */
    int validation_result = dtesn_esn_sparse_matrix_validate(matrix);
    if (validation_result != 0) {
        return validation_result;
    }
    
    /* Initialize output vector */
    memset(output, 0, matrix->rows * sizeof(float));
    
    /* Sparse matrix-vector multiplication using CSR format */
    for (uint32_t i = 0; i < matrix->rows; i++) {
        uint32_t start = matrix->row_ptr[i];
        uint32_t end = matrix->row_ptr[i + 1];
        
        float sum = 0.0f;
        
        /* Unroll loop for better performance when possible */
        uint32_t j = start;
        for (; j + 3 < end; j += 4) {
            sum += matrix->values[j] * input[matrix->col_idx[j]];
            sum += matrix->values[j + 1] * input[matrix->col_idx[j + 1]];
            sum += matrix->values[j + 2] * input[matrix->col_idx[j + 2]];
            sum += matrix->values[j + 3] * input[matrix->col_idx[j + 3]];
        }
        
        /* Handle remaining elements */
        for (; j < end; j++) {
            sum += matrix->values[j] * input[matrix->col_idx[j]];
        }
        
        output[i] = sum;
    }
    
    /* Update performance statistics */
    uint64_t mult_time = dtesn_esn_sparse_get_time_ns() - start_time;
    
    g_sparse_stats.total_multiplies++;
    g_sparse_stats.total_mult_time_ns += mult_time;
    
    /* Check timing constraint */
    if (mult_time > DTESN_ESN_MATRIX_MULT_THRESHOLD_US * 1000) {
        return DTESN_ESN_ELATENCY;
    }
    
    return 0;
}

int dtesn_esn_sparse_transpose(const dtesn_esn_sparse_matrix_t *matrix, dtesn_esn_sparse_matrix_t **transposed) {
    if (!matrix || !transposed) {
        return DTESN_ESN_EINVAL;
    }
    
    int validation_result = dtesn_esn_sparse_matrix_validate(matrix);
    if (validation_result != 0) {
        return validation_result;
    }
    
    /* Create transposed matrix structure */
    dtesn_esn_sparse_matrix_t *trans = calloc(1, sizeof(dtesn_esn_sparse_matrix_t));
    if (!trans) {
        return DTESN_ESN_ENOMEM;
    }
    
    trans->rows = matrix->cols;
    trans->cols = matrix->rows;
    trans->nnz = matrix->nnz;
    trans->sparsity = matrix->sparsity;
    trans->is_symmetric = matrix->is_symmetric;
    
    /* Allocate arrays */
    trans->row_ptr = calloc(trans->rows + 1, sizeof(uint32_t));
    trans->col_idx = calloc(trans->nnz, sizeof(uint32_t));
    trans->values = calloc(trans->nnz, sizeof(float));
    
    if (!trans->row_ptr || !trans->col_idx || !trans->values) {
        dtesn_esn_sparse_matrix_destroy(trans);
        return DTESN_ESN_ENOMEM;
    }
    
    /* Count elements per column in original matrix */
    uint32_t *col_counts = calloc(trans->rows, sizeof(uint32_t));
    if (!col_counts) {
        dtesn_esn_sparse_matrix_destroy(trans);
        return DTESN_ESN_ENOMEM;
    }
    
    for (uint32_t i = 0; i < matrix->nnz; i++) {
        col_counts[matrix->col_idx[i]]++;
    }
    
    /* Build row pointers for transposed matrix */
    trans->row_ptr[0] = 0;
    for (uint32_t i = 0; i < trans->rows; i++) {
        trans->row_ptr[i + 1] = trans->row_ptr[i] + col_counts[i];
    }
    
    /* Reset col_counts to use as insertion pointers */
    memset(col_counts, 0, trans->rows * sizeof(uint32_t));
    
    /* Fill transposed matrix */
    for (uint32_t i = 0; i < matrix->rows; i++) {
        for (uint32_t j = matrix->row_ptr[i]; j < matrix->row_ptr[i + 1]; j++) {
            uint32_t col = matrix->col_idx[j];
            uint32_t insert_pos = trans->row_ptr[col] + col_counts[col];
            
            trans->col_idx[insert_pos] = i;
            trans->values[insert_pos] = matrix->values[j];
            col_counts[col]++;
        }
    }
    
    free(col_counts);
    
    /* Sort column indices within each row of transposed matrix */
    for (uint32_t i = 0; i < trans->rows; i++) {
        uint32_t start = trans->row_ptr[i];
        uint32_t end = trans->row_ptr[i + 1];
        
        /* Simple insertion sort for small rows */
        for (uint32_t j = start + 1; j < end; j++) {
            uint32_t col_key = trans->col_idx[j];
            float val_key = trans->values[j];
            uint32_t k = j;
            
            while (k > start && trans->col_idx[k - 1] > col_key) {
                trans->col_idx[k] = trans->col_idx[k - 1];
                trans->values[k] = trans->values[k - 1];
                k--;
            }
            
            trans->col_idx[k] = col_key;
            trans->values[k] = val_key;
        }
    }
    
    *transposed = trans;
    return 0;
}

int dtesn_esn_sparse_add(const dtesn_esn_sparse_matrix_t *A, const dtesn_esn_sparse_matrix_t *B, 
                        dtesn_esn_sparse_matrix_t **result) {
    if (!A || !B || !result) {
        return DTESN_ESN_EINVAL;
    }
    
    if (A->rows != B->rows || A->cols != B->cols) {
        return DTESN_ESN_EINVAL;
    }
    
    /* For simplicity, this is a basic implementation */
    /* A more optimized version would merge the sparse structures directly */
    
    dtesn_esn_sparse_matrix_t *C = calloc(1, sizeof(dtesn_esn_sparse_matrix_t));
    if (!C) {
        return DTESN_ESN_ENOMEM;
    }
    
    C->rows = A->rows;
    C->cols = A->cols;
    C->nnz = A->nnz + B->nnz; /* Upper bound, will be adjusted */
    C->sparsity = (A->sparsity + B->sparsity) / 2.0f; /* Approximation */
    C->is_symmetric = A->is_symmetric && B->is_symmetric;
    
    /* Allocate temporary arrays with upper bound size */
    C->row_ptr = calloc(C->rows + 1, sizeof(uint32_t));
    C->col_idx = calloc(C->nnz, sizeof(uint32_t));
    C->values = calloc(C->nnz, sizeof(float));
    
    if (!C->row_ptr || !C->col_idx || !C->values) {
        dtesn_esn_sparse_matrix_destroy(C);
        return DTESN_ESN_ENOMEM;
    }
    
    uint32_t current_nnz = 0;
    C->row_ptr[0] = 0;
    
    /* Merge rows */
    for (uint32_t i = 0; i < A->rows; i++) {
        uint32_t a_start = A->row_ptr[i];
        uint32_t a_end = A->row_ptr[i + 1];
        uint32_t b_start = B->row_ptr[i];
        uint32_t b_end = B->row_ptr[i + 1];
        
        uint32_t a_idx = a_start;
        uint32_t b_idx = b_start;
        
        /* Merge sorted lists */
        while (a_idx < a_end || b_idx < b_end) {
            if (a_idx >= a_end) {
                /* Only B elements remain */
                C->col_idx[current_nnz] = B->col_idx[b_idx];
                C->values[current_nnz] = B->values[b_idx];
                b_idx++;
                current_nnz++;
            } else if (b_idx >= b_end) {
                /* Only A elements remain */
                C->col_idx[current_nnz] = A->col_idx[a_idx];
                C->values[current_nnz] = A->values[a_idx];
                a_idx++;
                current_nnz++;
            } else if (A->col_idx[a_idx] < B->col_idx[b_idx]) {
                /* A element is smaller */
                C->col_idx[current_nnz] = A->col_idx[a_idx];
                C->values[current_nnz] = A->values[a_idx];
                a_idx++;
                current_nnz++;
            } else if (A->col_idx[a_idx] > B->col_idx[b_idx]) {
                /* B element is smaller */
                C->col_idx[current_nnz] = B->col_idx[b_idx];
                C->values[current_nnz] = B->values[b_idx];
                b_idx++;
                current_nnz++;
            } else {
                /* Same column index - add values */
                C->col_idx[current_nnz] = A->col_idx[a_idx];
                C->values[current_nnz] = A->values[a_idx] + B->values[b_idx];
                a_idx++;
                b_idx++;
                current_nnz++;
            }
        }
        
        C->row_ptr[i + 1] = current_nnz;
    }
    
    /* Update actual nnz */
    C->nnz = current_nnz;
    
    /* Reallocate arrays to exact size if significantly smaller */
    if (current_nnz < (A->nnz + B->nnz) / 2) {
        uint32_t *new_col_idx = realloc(C->col_idx, current_nnz * sizeof(uint32_t));
        float *new_values = realloc(C->values, current_nnz * sizeof(float));
        
        if (new_col_idx && new_values) {
            C->col_idx = new_col_idx;
            C->values = new_values;
        }
    }
    
    *result = C;
    return 0;
}

int dtesn_esn_sparse_get_stats(uint64_t *total_operations, uint64_t *avg_time_ns) {
    if (!total_operations || !avg_time_ns) {
        return DTESN_ESN_EINVAL;
    }
    
    *total_operations = g_sparse_stats.total_multiplies;
    
    if (g_sparse_stats.total_multiplies > 0) {
        *avg_time_ns = g_sparse_stats.total_mult_time_ns / g_sparse_stats.total_multiplies;
    } else {
        *avg_time_ns = 0;
    }
    
    return 0;
}