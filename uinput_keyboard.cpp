#include <Python.h>
#include <linux/uinput.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <map>
#include <string>
#include <vector>
#include <sstream>

static int uinput_fd = -1;

// Key mappings
static std::map<std::string, int> key_map = {
    {"ctrl", KEY_LEFTCTRL}, {"control", KEY_LEFTCTRL},
    {"shift", KEY_LEFTSHIFT}, {"alt", KEY_LEFTALT},
    {"super", KEY_LEFTMETA}, {"win", KEY_LEFTMETA},
    {"fn", KEY_FN}, {"tab", KEY_TAB}, {"enter", KEY_ENTER},
    {"esc", KEY_ESC}, {"escape", KEY_ESC}, {"space", KEY_SPACE},
    {"backspace", KEY_BACKSPACE}, {"delete", KEY_DELETE},
    {"insert", KEY_INSERT}, {"home", KEY_HOME}, {"end", KEY_END},
    {"pageup", KEY_PAGEUP}, {"pagedown", KEY_PAGEDOWN},
    {"up", KEY_UP}, {"down", KEY_DOWN}, {"left", KEY_LEFT}, {"right", KEY_RIGHT},
    {"f1", KEY_F1}, {"f2", KEY_F2}, {"f3", KEY_F3}, {"f4", KEY_F4},
    {"f5", KEY_F5}, {"f6", KEY_F6}, {"f7", KEY_F7}, {"f8", KEY_F8},
    {"f9", KEY_F9}, {"f10", KEY_F10}, {"f11", KEY_F11}, {"f12", KEY_F12},
    {"capslock", KEY_CAPSLOCK}, {"numlock", KEY_NUMLOCK},
};

// Shift character mappings
static std::map<char, char> shift_chars = {
    {'!', '1'}, {'@', '2'}, {'#', '3'}, {'$', '4'}, {'%', '5'},
    {'^', '6'}, {'&', '7'}, {'*', '8'}, {'(', '9'}, {')', '0'},
    {'_', '-'}, {'+', '='}, {'{', '['}, {'}', ']'}, {'|', '\\'},
    {':', ';'}, {'"', '\''}, {'<', ','}, {'>', '.'}, {'?', '/'},
    {'~', '`'}
};

void emit_event(int type, int code, int val) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = val;
    write(uinput_fd, &ev, sizeof(ev));
}

void sync_event() {
    emit_event(EV_SYN, SYN_REPORT, 0);
}

int char_to_keycode(char c, bool &needs_shift) {
    needs_shift = false;
    
    // Check if character requires shift first
    for (auto &pair : shift_chars) {
        if (pair.first == c) {
            needs_shift = true;
            c = pair.second;  // Update c to the base character
            break;
        }
    }
    
    // Now handle the base character (after potential shift mapping)
    if (c >= 'A' && c <= 'Z') {
        needs_shift = true;
        return KEY_A + (c - 'A');
    }
    if (c >= 'a' && c <= 'z') {
        return KEY_A + (c - 'a');
    }
    if (c == '0') {
        return KEY_0;
    }
    
    // Check if character requires shift
    for (auto &pair : shift_chars) {
        if (pair.first == c) {
            needs_shift = true;
            return char_to_keycode(pair.second, needs_shift);
        }
    }
    
    // Special characters without shift
    switch(c) {
        case ' ': return KEY_SPACE;
        case '-': return KEY_MINUS;
        case '=': return KEY_EQUAL;
        case '[': return KEY_LEFTBRACE;
        case ']': return KEY_RIGHTBRACE;
        case '\\': return KEY_BACKSLASH;
        case ';': return KEY_SEMICOLON;
        case '\'': return KEY_APOSTROPHE;
        case '`': return KEY_GRAVE;
        case ',': return KEY_COMMA;
        case '.': return KEY_DOT;
        case '/': return KEY_SLASH;
        case '\n': return KEY_ENTER;
        case '\t': return KEY_TAB;
    }
    
    return -1;
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

static PyObject* init_uinput(PyObject *self, PyObject *args) {
    if (uinput_fd >= 0) {
        close(uinput_fd);
    }
    
    uinput_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (uinput_fd < 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to open /dev/uinput. Run with sudo or check permissions.");
        return NULL;
    }
    
    // Enable key events
    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    ioctl(uinput_fd, UI_SET_EVBIT, EV_SYN);
    
    // Enable all keys
    for (int i = 0; i < KEY_MAX; i++) {
        ioctl(uinput_fd, UI_SET_KEYBIT, i);
    }
    
    // Setup device
    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "python-uinput-keyboard");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1234;
    uidev.id.product = 0x5678;
    uidev.id.version = 1;
    
    write(uinput_fd, &uidev, sizeof(uidev));
    ioctl(uinput_fd, UI_DEV_CREATE);
    
    usleep(100000); // Wait 100ms for device to be ready
    
    Py_RETURN_NONE;
}

static PyObject* type_text(PyObject *self, PyObject *args) {
    const char *text;
    
    if (!PyArg_ParseTuple(args, "s", &text)) {
        return NULL;
    }
    
    if (uinput_fd < 0) {
        PyErr_SetString(PyExc_RuntimeError, "uinput not initialized. Call init() first.");
        return NULL;
    }
    
    for (size_t i = 0; i < strlen(text); i++) {
        bool needs_shift = false;
        int keycode = char_to_keycode(text[i], needs_shift);
        
        if (keycode < 0) continue;
        
        if (needs_shift) {
            emit_event(EV_KEY, KEY_LEFTSHIFT, 1);
            sync_event();
        }
        
        emit_event(EV_KEY, keycode, 1);
        sync_event();
        usleep(10000); // 10ms delay
        
        emit_event(EV_KEY, keycode, 0);
        sync_event();
        
        if (needs_shift) {
            emit_event(EV_KEY, KEY_LEFTSHIFT, 0);
            sync_event();
        }
        
        usleep(10000); // 10ms delay between keys
    }
    
    Py_RETURN_NONE;
}

static PyObject* press_key_combo(PyObject *self, PyObject *args) {
    const char *combo_str;
    
    if (!PyArg_ParseTuple(args, "s", &combo_str)) {
        return NULL;
    }
    
    if (uinput_fd < 0) {
        PyErr_SetString(PyExc_RuntimeError, "uinput not initialized. Call init() first.");
        return NULL;
    }
    
    std::string combo(combo_str);
    std::vector<std::string> parts = split_combo(combo);
    std::vector<int> keycodes;
    
    // Convert all parts to keycodes
    for (const auto &part : parts) {
        std::string lower_part = part;
        for (char &c : lower_part) c = tolower(c);
        
        if (key_map.find(lower_part) != key_map.end()) {
            keycodes.push_back(key_map[lower_part]);
        } else if (part.length() == 1) {
            bool needs_shift = false;
            int keycode = char_to_keycode(part[0], needs_shift);
            if (needs_shift) {
                keycodes.push_back(KEY_LEFTSHIFT);
            }
            if (keycode >= 0) {
                keycodes.push_back(keycode);
            }
        }
    }
    
    // Press all keys
    for (int keycode : keycodes) {
        emit_event(EV_KEY, keycode, 1);
        sync_event();
        usleep(10000);
    }
    
    // Release all keys in reverse order
    for (auto it = keycodes.rbegin(); it != keycodes.rend(); ++it) {
        emit_event(EV_KEY, *it, 0);
        sync_event();
        usleep(10000);
    }
    
    Py_RETURN_NONE;
}

static PyObject* cleanup(PyObject *self, PyObject *args) {
    if (uinput_fd >= 0) {
        ioctl(uinput_fd, UI_DEV_DESTROY);
        close(uinput_fd);
        uinput_fd = -1;
    }
    Py_RETURN_NONE;
}

static PyMethodDef KeyboardMethods[] = {
    {"init", init_uinput, METH_VARARGS, "Initialize uinput device"},
    {"type_text", type_text, METH_VARARGS, "Type text"},
    {"press_combo", press_key_combo, METH_VARARGS, "Press key combination"},
    {"cleanup", cleanup, METH_VARARGS, "Cleanup uinput device"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef keyboardmodule = {
    PyModuleDef_HEAD_INIT,
    "uinput_keyboard",
    "Linux uinput keyboard simulator",
    -1,
    KeyboardMethods
};

PyMODINIT_FUNC PyInit_uinput_keyboard(void) {
    return PyModule_Create(&keyboardmodule);
}