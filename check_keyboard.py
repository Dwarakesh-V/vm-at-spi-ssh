import os

# Check if running as superuser
if os.geteuid() == 0:
    # Running as root/sudo - use uinput
    import uinput_keyboard
    uinput_keyboard.init()
    uinput_keyboard.type_text("Hello World!")
    uinput_keyboard.cleanup()
    print("Root user - using uinput")
else:
    # Running as normal user - use X11
    import x11_keyboard
    x11_keyboard.init()
    x11_keyboard.type_text("Hello World!")
    x11_keyboard.cleanup()
    print("Non root user - using x11 (May not work on wayland)")