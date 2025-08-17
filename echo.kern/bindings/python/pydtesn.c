/*
 * Python Bindings for DTESN Library (pydtesn)
 * ===========================================
 * 
 * Python C extension module providing Python bindings for the libdtesn
 * user-space programming library. Allows Python applications to access
 * DTESN functionality with Pythonic interfaces.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>
#include "libdtesn.h"

/* Python DTESN Handle Object */
typedef struct {
    PyObject_HEAD
    dtesn_handle_t *handle;
    int is_valid;
} PyDTESNObject;

/* Module state */
static int module_initialized = 0;

/* Forward declarations */
static PyTypeObject PyDTESNType;
static void PyDTESN_dealloc(PyDTESNObject *self);
static PyObject *PyDTESN_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static int PyDTESN_init(PyDTESNObject *self, PyObject *args, PyObject *kwds);

/* Utility functions */
static PyObject *dtesn_error_to_exception(int error_code)
{
    const char *error_msg = dtesn_strerror(error_code);
    return PyErr_Format(PyExc_RuntimeError, "DTESN Error: %s (code %d)", error_msg, error_code);
}

/* DTESN Object Methods */

static PyObject *PyDTESN_evolve(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"input", "steps", "mode", NULL};
    PyObject *input_list = NULL;
    unsigned int steps = 1;
    unsigned int mode = DTESN_EVOLVE_SYNCHRONOUS;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|II", kwlist, &input_list, &steps, &mode)) {
        return NULL;
    }
    
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    /* Convert Python list to C array */
    if (!PyList_Check(input_list)) {
        PyErr_SetString(PyExc_TypeError, "Input must be a list");
        return NULL;
    }
    
    Py_ssize_t input_size = PyList_Size(input_list);
    if (input_size <= 0 || input_size > 1000) {
        PyErr_SetString(PyExc_ValueError, "Invalid input size");
        return NULL;
    }
    
    float *input = malloc(input_size * sizeof(float));
    if (!input) {
        return PyErr_NoMemory();
    }
    
    for (Py_ssize_t i = 0; i < input_size; i++) {
        PyObject *item = PyList_GetItem(input_list, i);
        if (!PyFloat_Check(item) && !PyLong_Check(item)) {
            free(input);
            PyErr_SetString(PyExc_TypeError, "Input list must contain numbers");
            return NULL;
        }
        input[i] = (float)PyFloat_AsDouble(item);
    }
    
    /* Call DTESN evolve function */
    int result = dtesn_evolve(self->handle, input, (uint32_t)input_size, steps, mode);
    free(input);
    
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    Py_RETURN_NONE;
}

static PyObject *PyDTESN_get_state(PyDTESNObject *self, PyObject *Py_UNUSED(ignored))
{
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    struct dtesn_state_info state;
    int result = dtesn_get_state(self->handle, &state);
    
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    /* Convert C state structure to Python dictionary */
    PyObject *state_dict = PyDict_New();
    if (!state_dict) {
        return NULL;
    }
    
    PyDict_SetItemString(state_dict, "depth", PyLong_FromUnsignedLong(state.depth));
    PyDict_SetItemString(state_dict, "active_membranes", PyLong_FromUnsignedLong(state.active_membranes));
    PyDict_SetItemString(state_dict, "total_neurons", PyLong_FromUnsignedLong(state.total_neurons));
    PyDict_SetItemString(state_dict, "evolution_steps", PyLong_FromUnsignedLong(state.evolution_steps));
    PyDict_SetItemString(state_dict, "creation_time_ns", PyLong_FromUnsignedLongLong(state.creation_time_ns));
    PyDict_SetItemString(state_dict, "last_update_ns", PyLong_FromUnsignedLongLong(state.last_update_ns));
    PyDict_SetItemString(state_dict, "spectral_radius", PyFloat_FromDouble(state.spectral_radius));
    PyDict_SetItemString(state_dict, "membrane_activity", PyFloat_FromDouble(state.membrane_activity));
    PyDict_SetItemString(state_dict, "oeis_compliance", PyLong_FromUnsignedLong(state.oeis_compliance));
    PyDict_SetItemString(state_dict, "performance_violations", PyLong_FromUnsignedLong(state.performance_violations));
    
    return state_dict;
}

static PyObject *PyDTESN_membrane_create(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"parent_id", NULL};
    unsigned int parent_id = 0;  /* Default to root */
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|I", kwlist, &parent_id)) {
        return NULL;
    }
    
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    uint32_t membrane_id;
    int result = dtesn_membrane_create(self->handle, parent_id, &membrane_id);
    
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    return PyLong_FromUnsignedLong(membrane_id);
}

static PyObject *PyDTESN_membrane_evolve(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"membrane_id", "steps", "data", NULL};
    unsigned int membrane_id;
    unsigned int steps = 1;
    PyObject *data_obj = NULL;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "I|IO", kwlist, &membrane_id, &steps, &data_obj)) {
        return NULL;
    }
    
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    const void *data = NULL;
    uint32_t data_size = 0;
    
    if (data_obj && data_obj != Py_None) {
        if (PyBytes_Check(data_obj)) {
            data = PyBytes_AsString(data_obj);
            data_size = (uint32_t)PyBytes_Size(data_obj);
        } else if (PyUnicode_Check(data_obj)) {
            data = PyUnicode_AsUTF8(data_obj);
            data_size = (uint32_t)strlen((const char *)data);
        } else {
            PyErr_SetString(PyExc_TypeError, "Data must be bytes or string");
            return NULL;
        }
    }
    
    int result = dtesn_membrane_evolve(self->handle, membrane_id, steps, data, data_size);
    
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    Py_RETURN_NONE;
}

static PyObject *PyDTESN_bseries_compute(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"order", "coefficients", NULL};
    unsigned int order;
    PyObject *coeff_list;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "IO", kwlist, &order, &coeff_list)) {
        return NULL;
    }
    
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    if (!PyList_Check(coeff_list)) {
        PyErr_SetString(PyExc_TypeError, "Coefficients must be a list");
        return NULL;
    }
    
    Py_ssize_t coeff_count = PyList_Size(coeff_list);
    if (coeff_count <= 0) {
        PyErr_SetString(PyExc_ValueError, "Coefficients list cannot be empty");
        return NULL;
    }
    
    /* Convert coefficients to C array */
    double *coefficients = malloc(coeff_count * sizeof(double));
    if (!coefficients) {
        return PyErr_NoMemory();
    }
    
    for (Py_ssize_t i = 0; i < coeff_count; i++) {
        PyObject *item = PyList_GetItem(coeff_list, i);
        if (!PyFloat_Check(item) && !PyLong_Check(item)) {
            free(coefficients);
            PyErr_SetString(PyExc_TypeError, "Coefficients must be numbers");
            return NULL;
        }
        coefficients[i] = PyFloat_AsDouble(item);
    }
    
    /* Get expected result size */
    uint32_t tree_count;
    int result = dtesn_bseries_get_tree_count(order, &tree_count);
    if (result != 0) {
        free(coefficients);
        return dtesn_error_to_exception(result);
    }
    
    /* Allocate result buffer */
    double *results = malloc(tree_count * sizeof(double));
    if (!results) {
        free(coefficients);
        return PyErr_NoMemory();
    }
    
    /* Compute B-series */
    result = dtesn_bseries_compute(self->handle, order, coefficients, (uint32_t)coeff_count, results, tree_count);
    free(coefficients);
    
    if (result != 0) {
        free(results);
        return dtesn_error_to_exception(result);
    }
    
    /* Convert results to Python list */
    PyObject *result_list = PyList_New(tree_count);
    if (!result_list) {
        free(results);
        return NULL;
    }
    
    for (uint32_t i = 0; i < tree_count; i++) {
        PyList_SetItem(result_list, i, PyFloat_FromDouble(results[i]));
    }
    
    free(results);
    return result_list;
}

static PyObject *PyDTESN_esn_predict(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"input", "output_size", NULL};
    PyObject *input_list;
    unsigned int output_size;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OI", kwlist, &input_list, &output_size)) {
        return NULL;
    }
    
    if (!self->is_valid) {
        PyErr_SetString(PyExc_ValueError, "DTESN instance is not valid");
        return NULL;
    }
    
    if (!PyList_Check(input_list)) {
        PyErr_SetString(PyExc_TypeError, "Input must be a list");
        return NULL;
    }
    
    Py_ssize_t input_size = PyList_Size(input_list);
    if (input_size <= 0) {
        PyErr_SetString(PyExc_ValueError, "Input list cannot be empty");
        return NULL;
    }
    
    /* Convert input to C array */
    float *input = malloc(input_size * sizeof(float));
    if (!input) {
        return PyErr_NoMemory();
    }
    
    for (Py_ssize_t i = 0; i < input_size; i++) {
        PyObject *item = PyList_GetItem(input_list, i);
        if (!PyFloat_Check(item) && !PyLong_Check(item)) {
            free(input);
            PyErr_SetString(PyExc_TypeError, "Input must contain numbers");
            return NULL;
        }
        input[i] = (float)PyFloat_AsDouble(item);
    }
    
    /* Allocate output buffer */
    float *output = calloc(output_size, sizeof(float));
    if (!output) {
        free(input);
        return PyErr_NoMemory();
    }
    
    /* Make prediction */
    int result = dtesn_esn_predict(self->handle, input, (uint32_t)input_size, output, output_size);
    free(input);
    
    if (result != 0) {
        free(output);
        return dtesn_error_to_exception(result);
    }
    
    /* Convert output to Python list */
    PyObject *output_list = PyList_New(output_size);
    if (!output_list) {
        free(output);
        return NULL;
    }
    
    for (uint32_t i = 0; i < output_size; i++) {
        PyList_SetItem(output_list, i, PyFloat_FromDouble(output[i]));
    }
    
    free(output);
    return output_list;
}

/* DTESN Object Method Table */
static PyMethodDef PyDTESN_methods[] = {
    {"evolve", (PyCFunction)PyDTESN_evolve, METH_VARARGS | METH_KEYWORDS,
     "Evolve the DTESN instance with given input"},
    {"get_state", (PyCFunction)PyDTESN_get_state, METH_NOARGS,
     "Get current state information of the DTESN instance"},
    {"membrane_create", (PyCFunction)PyDTESN_membrane_create, METH_VARARGS | METH_KEYWORDS,
     "Create a new P-system membrane"},
    {"membrane_evolve", (PyCFunction)PyDTESN_membrane_evolve, METH_VARARGS | METH_KEYWORDS,
     "Evolve a P-system membrane"},
    {"bseries_compute", (PyCFunction)PyDTESN_bseries_compute, METH_VARARGS | METH_KEYWORDS,
     "Compute B-series coefficients"},
    {"esn_predict", (PyCFunction)PyDTESN_esn_predict, METH_VARARGS | METH_KEYWORDS,
     "Generate ESN prediction"},
    {NULL}  /* Sentinel */
};

/* DTESN Object Type Definition */
static PyTypeObject PyDTESNType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "pydtesn.DTESN",
    .tp_doc = "DTESN instance object",
    .tp_basicsize = sizeof(PyDTESNObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyDTESN_new,
    .tp_init = (initproc)PyDTESN_init,
    .tp_dealloc = (destructor)PyDTESN_dealloc,
    .tp_methods = PyDTESN_methods,
};

/* DTESN Object Implementation */
static PyObject *PyDTESN_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyDTESNObject *self = (PyDTESNObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->handle = NULL;
        self->is_valid = 0;
    }
    return (PyObject *)self;
}

static int PyDTESN_init(PyDTESNObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"depth", "max_order", "neuron_count", "membrane_count", 
                             "input_dim", "output_dim", "flags", "label", NULL};
    
    unsigned int depth = 4;
    unsigned int max_order = 5;
    unsigned int neuron_count = 100;
    unsigned int membrane_count = 9;
    unsigned int input_dim = 10;
    unsigned int output_dim = 5;
    unsigned int flags = DTESN_CREATE_DEFAULT;
    const char *label = "pydtesn_instance";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|IIIIIIIs", kwlist,
                                     &depth, &max_order, &neuron_count, &membrane_count,
                                     &input_dim, &output_dim, &flags, &label)) {
        return -1;
    }
    
    /* Create DTESN parameters */
    struct dtesn_create_params params = {
        .depth = depth,
        .max_order = max_order,
        .neuron_count = neuron_count,
        .membrane_count = membrane_count,
        .input_dim = input_dim,
        .output_dim = output_dim,
        .flags = flags
    };
    
    strncpy(params.label, label, DTESN_MAX_LABEL_LEN - 1);
    params.label[DTESN_MAX_LABEL_LEN - 1] = '\0';
    
    /* Create DTESN instance */
    int result = dtesn_create(&params, &self->handle);
    if (result != 0) {
        PyErr_Format(PyExc_RuntimeError, "Failed to create DTESN instance: %s", dtesn_strerror(result));
        return -1;
    }
    
    self->is_valid = 1;
    return 0;
}

static void PyDTESN_dealloc(PyDTESNObject *self)
{
    if (self->handle && self->is_valid) {
        dtesn_destroy(self->handle);
        self->handle = NULL;
        self->is_valid = 0;
    }
    Py_TYPE(self)->tp_free((PyObject *)self);
}

/* Module Functions */

static PyObject *pydtesn_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"max_instances", "async_queue_size", "worker_threads", "flags", NULL};
    unsigned int max_instances = 1000;
    unsigned int async_queue_size = 256;
    unsigned int worker_threads = 4;
    unsigned int flags = 0;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|IIII", kwlist,
                                     &max_instances, &async_queue_size, &worker_threads, &flags)) {
        return NULL;
    }
    
    if (module_initialized) {
        PyErr_SetString(PyExc_RuntimeError, "DTESN library already initialized");
        return NULL;
    }
    
    dtesn_lib_config_t config = {
        .max_instances = max_instances,
        .async_queue_size = async_queue_size,
        .worker_threads = worker_threads,
        .flags = flags
    };
    
    int result = dtesn_init(&config);
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    module_initialized = 1;
    Py_RETURN_NONE;
}

static PyObject *pydtesn_cleanup(PyObject *self, PyObject *Py_UNUSED(ignored))
{
    if (!module_initialized) {
        PyErr_SetString(PyExc_RuntimeError, "DTESN library not initialized");
        return NULL;
    }
    
    int result = dtesn_cleanup();
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    module_initialized = 0;
    Py_RETURN_NONE;
}

static PyObject *pydtesn_get_version(PyObject *self, PyObject *Py_UNUSED(ignored))
{
    int major, minor, patch;
    const char *version = dtesn_get_version(&major, &minor, &patch);
    
    PyObject *version_tuple = PyTuple_New(4);
    if (!version_tuple) {
        return NULL;
    }
    
    PyTuple_SetItem(version_tuple, 0, PyUnicode_FromString(version));
    PyTuple_SetItem(version_tuple, 1, PyLong_FromLong(major));
    PyTuple_SetItem(version_tuple, 2, PyLong_FromLong(minor));
    PyTuple_SetItem(version_tuple, 3, PyLong_FromLong(patch));
    
    return version_tuple;
}

static PyObject *pydtesn_get_performance_stats(PyObject *self, PyObject *Py_UNUSED(ignored))
{
    dtesn_perf_stats_t stats;
    int result = dtesn_get_performance_stats(NULL, &stats);
    
    if (result != 0) {
        return dtesn_error_to_exception(result);
    }
    
    PyObject *stats_dict = PyDict_New();
    if (!stats_dict) {
        return NULL;
    }
    
    PyDict_SetItemString(stats_dict, "total_api_calls", PyLong_FromUnsignedLongLong(stats.total_api_calls));
    PyDict_SetItemString(stats_dict, "total_execution_time_ns", PyLong_FromUnsignedLongLong(stats.total_execution_time_ns));
    PyDict_SetItemString(stats_dict, "avg_call_overhead_ns", PyLong_FromUnsignedLongLong(stats.avg_call_overhead_ns));
    PyDict_SetItemString(stats_dict, "min_call_time_ns", PyLong_FromUnsignedLongLong(stats.min_call_time_ns));
    PyDict_SetItemString(stats_dict, "max_call_time_ns", PyLong_FromUnsignedLongLong(stats.max_call_time_ns));
    PyDict_SetItemString(stats_dict, "active_instances", PyLong_FromUnsignedLong(stats.active_instances));
    PyDict_SetItemString(stats_dict, "failed_calls", PyLong_FromUnsignedLong(stats.failed_calls));
    PyDict_SetItemString(stats_dict, "memory_usage_bytes", PyLong_FromUnsignedLongLong(stats.memory_usage_bytes));
    
    return stats_dict;
}

/* Module Method Table */
static PyMethodDef pydtesn_methods[] = {
    {"init", (PyCFunction)pydtesn_init, METH_VARARGS | METH_KEYWORDS,
     "Initialize the DTESN library"},
    {"cleanup", pydtesn_cleanup, METH_NOARGS,
     "Cleanup and shutdown the DTESN library"},
    {"get_version", pydtesn_get_version, METH_NOARGS,
     "Get library version information"},
    {"get_performance_stats", pydtesn_get_performance_stats, METH_NOARGS,
     "Get global performance statistics"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

/* Module Definition */
static struct PyModuleDef pydtesn_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "pydtesn",
    .m_doc = "Python bindings for the DTESN user-space library",
    .m_size = -1,
    .m_methods = pydtesn_methods,
};

/* Module Initialization */
PyMODINIT_FUNC PyInit_pydtesn(void)
{
    PyObject *module;
    
    /* Prepare DTESN type */
    if (PyType_Ready(&PyDTESNType) < 0) {
        return NULL;
    }
    
    /* Create module */
    module = PyModule_Create(&pydtesn_module);
    if (module == NULL) {
        return NULL;
    }
    
    /* Add DTESN type to module */
    Py_INCREF(&PyDTESNType);
    if (PyModule_AddObject(module, "DTESN", (PyObject *)&PyDTESNType) < 0) {
        Py_DECREF(&PyDTESNType);
        Py_DECREF(module);
        return NULL;
    }
    
    /* Add constants */
    PyModule_AddIntConstant(module, "CREATE_DEFAULT", DTESN_CREATE_DEFAULT);
    PyModule_AddIntConstant(module, "CREATE_HARDWARE_ACCEL", DTESN_CREATE_HARDWARE_ACCEL);
    PyModule_AddIntConstant(module, "CREATE_HIGH_PRECISION", DTESN_CREATE_HIGH_PRECISION);
    PyModule_AddIntConstant(module, "CREATE_SPARSE_MODE", DTESN_CREATE_SPARSE_MODE);
    PyModule_AddIntConstant(module, "CREATE_REAL_TIME", DTESN_CREATE_REAL_TIME);
    PyModule_AddIntConstant(module, "CREATE_VALIDATE_OEIS", DTESN_CREATE_VALIDATE_OEIS);
    
    PyModule_AddIntConstant(module, "EVOLVE_SYNCHRONOUS", DTESN_EVOLVE_SYNCHRONOUS);
    PyModule_AddIntConstant(module, "EVOLVE_ASYNCHRONOUS", DTESN_EVOLVE_ASYNCHRONOUS);
    PyModule_AddIntConstant(module, "EVOLVE_CONTINUOUS", DTESN_EVOLVE_CONTINUOUS);
    PyModule_AddIntConstant(module, "EVOLVE_STEP_BY_STEP", DTESN_EVOLVE_STEP_BY_STEP);
    
    return module;
}