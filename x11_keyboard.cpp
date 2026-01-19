#include <Python.h>
#include <X11/Xlib.h>
#include <X11/keysym.h>
#include <X11/extensions/XTest.h>
#include <ctype.h>
#include <map>
#include <string>
#include <vector>
#include <sstream>
#include <unistd.h>

static Display *display = NULL;

// Key mappings to X11 KeySyms
static std::map<std::string, KeySym> key_map = {
    {"ctrl", XK_Control_L}, {"control", XK_Control_L},
    {"shift", XK_Shift_L}, {"alt", XK_Alt_L},
    {"super", XK_Super_L}, {"win", XK_Super_L},
    {"tab", XK_Tab}, {"enter", XK_Return},
    {"esc", XK_Escape}, {"escape", XK_Escape}, {"space", XK_space},
    {"backspace", XK_BackSpace}, {"delete", XK_Delete},
    {"insert", XK_Insert}, {"home", XK_Home}, {"end", XK_End},
    {"pageup", XK_Page_Up}, {"pagedown", XK_Page_Down},
    {"up", XK_Up}, {"down", XK_Down}, {"left", XK_Left}, {"right", XK_Right},
    {"f1", XK_F1}, {"f2", XK_F2}, {"f3", XK_F3}, {"f4", XK_F4},
    {"f5", XK_F5}, {"f6", XK_F6}, {"f7", XK_F7}, {"f8", XK_F8},
    {"f9", XK_F9}, {"f10", XK_F10}, {"f11", XK_F11}, {"f12", XK_F12},
    {"capslock", XK_Caps_Lock}, {"numlock", XK_Num_Lock},
};

// Shift character mappings
static std::map<char, char> shift_chars = {
    {'!', '1'}, {'@', '2'}, {'#', '3'}, {'$', '4'}, {'%', '5'},
    {'^', '6'}, {'&', '7'}, {'*', '8'}, {'(', '9'}, {')', '0'},
    {'_', '-'}, {'+', '='}, {'{', '['}, {'}', ']'}, {'|', '\\'},
    {':', ';'}, {'"', '\''}, {'<', ','}, {'>', '.'}, {'?', '/'},
    {'~', '`'}
};

void send_key(KeySym keysym, bool press) {
    KeyCode keycode = XKeysymToKeycode(display, keysym);
    if (keycode != 0) {
        XTestFakeKeyEvent(display, keycode, press ? True : False, CurrentTime);
        XFlush(display);
    }
}

KeySym char_to_keysym(char c, bool &needs_shift) {
    needs_shift = false;
    
    // Check if character requires shift first
    for (auto &pair : shift_chars) {
        if (pair.first == c) {
            needs_shift = true;
            c = pair.second;
            break;
        }
    }
    
    // Handle uppercase letters
    if (c >= 'A' && c <= 'Z') {
        needs_shift = true;
        return XK_a + (c - 'A');
    }
    
    // Handle lowercase letters
    if (c >= 'a' && c <= 'z') {
        return XK_a + (c - 'a');
    }
    
    // Handle numbers
    if (c >= '0' && c <= '9') {
        return XK_0 + (c - '0');
    }
    
    // Special characters without shift
    switch(c) {
        case ' ': return XK_space;
        case '-': return XK_minus;
        case '=': return XK_equal;
        case '[': return XK_bracketleft;
        case ']': return XK_bracketright;
        case '\\': return XK_backslash;
        case ';': return XK_semicolon;
        case '\'': return XK_apostrophe;
        case '`': return XK_grave;
        case ',': return XK_comma;
        case '.': return XK_period;
        case '/': return XK_slash;
        case '\n': return XK_Return;
        case '\t': return XK_Tab;
    }
    
    return 0;
}

std::vector<std::string> split_combo(const std::string &combo) {
    std::vector<std::string> parts;
    std::stringstream ss(combo);
    std::string item;
    
    while (std::getline(ss, item, '+')) {
        // Trim whitespace
        size_t start = item.find_first_not_of(" \t");
        size_t end = item.find_last_not_of(" \t");
        if (start != std::string::npos) {
            parts.push_back(item.substr(start, end - start + 1));
        }
    }
    
    return parts;
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
    
    // Check if XTest extension is available
    int event_base, error_base, major, minor;
    if (!XTestQueryExtension(display, &event_base, &error_base, &major, &minor)) {
        XCloseDisplay(display);
        display = NULL;
        PyErr_SetString(PyExc_RuntimeError, "XTest extension not available.");
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* type_text(PyObject *self, PyObject *args) {
    const char *text;
    
    if (!PyArg_ParseTuple(args, "s", &text)) {
        return NULL;
    }
    
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }
    
    for (size_t i = 0; i < strlen(text); i++) {
        bool needs_shift = false;
        KeySym keysym = char_to_keysym(text[i], needs_shift);
        
        if (keysym == 0) continue;
        
        if (needs_shift) {
            send_key(XK_Shift_L, true);
            usleep(10000);
        }
        
        send_key(keysym, true);
        usleep(10000);
        
        send_key(keysym, false);
        usleep(10000);
        
        if (needs_shift) {
            send_key(XK_Shift_L, false);
            usleep(10000);
        }
        
        usleep(10000); // Delay between keys
    }
    
    Py_RETURN_NONE;
}

static PyObject* press_key_combo(PyObject *self, PyObject *args) {
    const char *combo_str;
    
    if (!PyArg_ParseTuple(args, "s", &combo_str)) {
        return NULL;
    }
    
    if (display == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "X11 not initialized. Call init() first.");
        return NULL;
    }
    
    std::string combo(combo_str);
    std::vector<std::string> parts = split_combo(combo);
    std::vector<KeySym> keysyms;
    
    // Convert all parts to keysyms
    for (const auto &part : parts) {
        std::string lower_part = part;
        for (char &c : lower_part) c = tolower(c);
        
        if (key_map.find(lower_part) != key_map.end()) {
            keysyms.push_back(key_map[lower_part]);
        } else if (part.length() == 1) {
            bool needs_shift = false;
            KeySym keysym = char_to_keysym(part[0], needs_shift);
            if (needs_shift) {
                keysyms.push_back(XK_Shift_L);
            }
            if (keysym != 0) {
                keysyms.push_back(keysym);
            }
        }
    }
    
    // Press all keys
    for (KeySym keysym : keysyms) {
        send_key(keysym, true);
        usleep(10000);
    }
    
    // Release all keys in reverse order
    for (auto it = keysyms.rbegin(); it != keysyms.rend(); ++it) {
        send_key(*it, false);
        usleep(10000);
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

static PyMethodDef KeyboardMethods[] = {
    {"init", init_x11, METH_VARARGS, "Initialize X11 display"},
    {"type_text", type_text, METH_VARARGS, "Type text"},
    {"press_combo", press_key_combo, METH_VARARGS, "Press key combination"},
    {"cleanup", cleanup, METH_VARARGS, "Cleanup X11 display"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef keyboardmodule = {
    PyModuleDef_HEAD_INIT,
    "x11_keyboard",
    "X11 keyboard simulator using XTest",
    -1,
    KeyboardMethods
};

PyMODINIT_FUNC PyInit_x11_keyboard(void) {
    return PyModule_Create(&keyboardmodule);
}