#include <Python.h>
#include <X11/Xlib.h>
#include <X11/extensions/XTest.h>
#include <unistd.h>
#include <cmath>
#include <random>

static Display *display = NULL;

// Get current mouse position
void get_mouse_position(int &x, int &y) {
    Window root, child;
    int root_x, root_y;
    unsigned int mask;

    XQueryPointer(display, DefaultRootWindow(display),
                  &root, &child,
                  &root_x, &root_y,
                  &x, &y, &mask);
}

// Gaussian noise generator
double gaussian_noise(double mean, double stddev) {
    static std::mt19937 rng(std::random_device{}());
    std::normal_distribution<double> dist(mean, stddev);
    return dist(rng);
}

int safe_usleep(int base, int jitter) {
    int delta = (int)gaussian_noise(0, jitter);
    int total = base + delta;
    if (total < 5000) total = 5000;     // never below 1 ms
    if (total > 50000) total = 50000;   // never above 50 ms
    return total;
}

// Cubic Bezier interpolation
double bezier(double p0, double p1, double p2, double p3, double t) {
    double u = 1.0 - t;
    return u*u*u*p0 +
           3*u*u*t*p1 +
           3*u*t*t*p2 +
           t*t*t*p3;
}

// Human-like movement with overshoot, jitter, easing
void move_mouse_human_internal(int start_x, int start_y, int end_x, int end_y, int steps) {
    // Random overshoot (3–10 px)
    double overshoot_dist = 3 + std::abs(gaussian_noise(0, 3));
    double angle = atan2(end_y - start_y, end_x - start_x);

    double overshoot_x = end_x + cos(angle) * overshoot_dist;
    double overshoot_y = end_y + sin(angle) * overshoot_dist;

    // Slight miss of center (±2 px)
    end_x += (int)gaussian_noise(0, 2);
    end_y += (int)gaussian_noise(0, 2);

    // Control points (random curvature)
    double cx1 = start_x + (overshoot_x - start_x) * 0.3 + gaussian_noise(0, 25);
    double cy1 = start_y + (overshoot_y - start_y) * 0.3 + gaussian_noise(0, 25);

    double cx2 = start_x + (overshoot_x - start_x) * 0.7 + gaussian_noise(0, 25);
    double cy2 = start_y + (overshoot_y - start_y) * 0.7 + gaussian_noise(0, 25);

    for (int i = 0; i <= steps; i++) {
        double t = (double)i / steps;

        // Ease-in-out
        double eased_t = t * t * (3 - 2 * t);

        // Slow down near the target (Fitts' Law-ish)
        if (t > 0.85) {
            double slow_t = (t - 0.85) / 0.15;
            eased_t = 0.85 + slow_t * slow_t * 0.15;
        }

        double x = bezier(start_x, cx1, cx2, overshoot_x, eased_t);
        double y = bezier(start_y, cy1, cy2, overshoot_y, eased_t);

        // Micro jitter
        x += gaussian_noise(0, 1.2);
        y += gaussian_noise(0, 1.2);

        XTestFakeMotionEvent(display, -1, (int)x, (int)y, CurrentTime);
        XFlush(display);

        usleep(safe_usleep(6000, 2500));
    }

    // Correction phase: overshoot → final target
    int corr_steps = 15;
    for (int i = 0; i <= corr_steps; i++) {
        double t = (double)i / corr_steps;
        double eased_t = t * t * (3 - 2 * t);

        double x = overshoot_x + (end_x - overshoot_x) * eased_t + gaussian_noise(0, 0.8);
        double y = overshoot_y + (end_y - overshoot_y) * eased_t + gaussian_noise(0, 0.8);

        XTestFakeMotionEvent(display, -1, (int)x, (int)y, CurrentTime);
        XFlush(display);

        usleep(safe_usleep(8000, 2000));
    }

    // Micro-pause before click (30–120 ms)
    usleep(safe_usleep(30000, 30000));
}

static PyObject* move_mouse_human(PyObject *self, PyObject *args) {
    int target_x, target_y;
    int steps = 60;

    if (!PyArg_ParseTuple(args, "ii|i", &target_x, &target_y, &steps)) {
        return NULL;
    }

    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    int start_x, start_y;
    get_mouse_position(start_x, start_y);

    move_mouse_human_internal(start_x, start_y, target_x, target_y, steps);

    Py_RETURN_NONE;
}

void send_button(int button, bool press) {
    if (display == NULL) return;
    XTestFakeButtonEvent(display, button, press ? True : False, CurrentTime);
    XFlush(display);
}

static PyObject* init_x11(PyObject *self, PyObject *args) {
    if (display != NULL) {
        XCloseDisplay(display);
    }

    display = XOpenDisplay(NULL);
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to open X display. Make sure DISPLAY is set.");
        return NULL;
    }

    int event_base, error_base, major, minor;
    if (!XTestQueryExtension(display, &event_base, &error_base, &major, &minor)) {
        XCloseDisplay(display);
        display = NULL;
        PyErr_SetString(PyExc_RuntimeError, "XTest extension not available.");
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject* move_mouse(PyObject *self, PyObject *args) {
    int x, y;

    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }

    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    XTestFakeMotionEvent(display, -1, x, y, CurrentTime);
    XFlush(display);

    Py_RETURN_NONE;
}

static PyObject* click(PyObject *self, PyObject *args) {
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    send_button(1, true);
    usleep(10000);
    send_button(1, false);

    Py_RETURN_NONE;
}

static PyObject* right_click(PyObject *self, PyObject *args) {
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    send_button(3, true);
    usleep(10000);
    send_button(3, false);

    Py_RETURN_NONE;
}

static PyObject* middle_click(PyObject *self, PyObject *args) {
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    send_button(2, true);
    usleep(10000);
    send_button(2, false);

    Py_RETURN_NONE;
}

static PyObject* double_click(PyObject *self, PyObject *args) {
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    for (int i = 0; i < 2; i++) {
        send_button(1, true);
        usleep(10000);
        send_button(1, false);
        usleep(150000);
    }

    Py_RETURN_NONE;
}

static PyObject* scroll(PyObject *self, PyObject *args) {
    int distance;

    if (!PyArg_ParseTuple(args, "i", &distance)) {
        return NULL;
    }

    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }

    int button = (distance > 0) ? 4 : 5;
    int steps = abs(distance);

    for (int i = 0; i < steps; i++) {
        send_button(button, true);
        usleep(5000);
        send_button(button, false);
        usleep(5000);
    }

    Py_RETURN_NONE;
}

static PyObject* cleanup(PyObject *self, PyObject *args) {
    if (display != NULL) {
        XCloseDisplay(display);
        display = NULL;
    }
    Py_RETURN_NONE;
}

static PyMethodDef MouseMethods[] = {
    {"init", init_x11, METH_VARARGS, "Initialize X11 display"},
    {"move", move_mouse, METH_VARARGS, "Move mouse to x,y"},
    {"click", click, METH_VARARGS, "Left click"},
    {"right_click", right_click, METH_VARARGS, "Right click"},
    {"middle_click", middle_click, METH_VARARGS, "Middle click"},
    {"double_click", double_click, METH_VARARGS, "Double click"},
    {"scroll", scroll, METH_VARARGS, "Scroll by distance"},
    {"move_human", move_mouse_human, METH_VARARGS, "Human-like mouse movement"},
    {"cleanup", cleanup, METH_VARARGS, "Cleanup X11 display"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef mousemodule = {
    PyModuleDef_HEAD_INIT,
    "x11_mouse",
    "X11 mouse simulator using XTest",
    -1,
    MouseMethods
};

PyMODINIT_FUNC PyInit_x11_mouse(void) {
    return PyModule_Create(&mousemodule);
}
