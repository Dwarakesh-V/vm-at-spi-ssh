# Works without root
import x11_keyboard
x11_keyboard.init()
x11_keyboard.type_text("Hello World!")
x11_keyboard.cleanup()
print("Non root user - using x11 (May not work on wayland)")