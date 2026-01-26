from time import sleep
import x11_keyboard
import x11_mouse

def demo_keyboard():
    print("KEYBOARD DEMO")

    # Initialize keyboard subsystem
    x11_keyboard.init()
    sleep(1)
    print("Keyboard initialized\n")

    x11_keyboard.press_combo("ctrl+v")

    # Type plain text
    print("Typing: Hello, world!")
    x11_keyboard.type_text("Hello, world!\n")
    sleep(1)

    # Type mixed case, numbers, and symbols
    print("Typing: Mixed CASE 123 !@#$%^&*()")
    x11_keyboard.type_text("Mixed CASE 123 !@#$%^&*()\n")
    sleep(1)

    # Press modifier combos
    print("Pressing Ctrl+A (select all)")
    x11_keyboard.press_combo("ctrl+a")
    sleep(1)

    print("Pressing Ctrl+C (copy)")
    x11_keyboard.press_combo("ctrl+c")
    sleep(1)

    x11_keyboard.press_combo("down")
    sleep(1)

    print("Pressing Ctrl+V (paste)")
    x11_keyboard.press_combo("ctrl+v")
    sleep(1)

    # Function keys
    # print("Pressing F5")
    # x11_keyboard.press_combo("f5")
    # sleep(1)

    # Navigation keys
    print("Pressing Up, Down, Left, Right")
    x11_keyboard.press_combo("up")
    x11_keyboard.press_combo("down")
    x11_keyboard.press_combo("left")
    x11_keyboard.press_combo("right")
    sleep(1)

    # Special keys
    print("Pressing Tab")
    x11_keyboard.press_combo("tab")
    sleep(1)

    print("Pressing Enter")
    x11_keyboard.press_combo("enter")
    sleep(1)

    print("Pressing Escape")
    x11_keyboard.press_combo("esc")
    sleep(1)

    # Cleanup keyboard
    x11_keyboard.cleanup()
    sleep(1)


def demo_mouse():
    print("\nMOUSE DEMO")

    # Initialize mouse subsystem
    x11_mouse.init()
    sleep(1)
    print("Mouse initialized\n")

    # Human-like movement to a visible location
    print("Human-like move to (300, 300)")
    x11_mouse.move_human(300, 300)
    sleep(1)

    # Left click
    print("Left click")
    x11_mouse.click()
    sleep(1)

    # Move somewhere else
    print("Human-like move to (700, 300)")
    x11_mouse.move_human(700, 300)
    sleep(1)

    # Right click
    print("Right click")
    x11_mouse.right_click()
    sleep(1)

    # Move somewhere else
    print("Human-like move to (500, 500)")
    x11_mouse.move_human(500, 500)
    sleep(1)

    # Middle click
    print("Middle click")
    x11_mouse.middle_click()
    sleep(1)

    # Double click
    print("Double click")
    x11_mouse.double_click()
    sleep(1)

    # Scroll down
    print("Scroll down (distance = -10)")
    x11_mouse.scroll(-10)
    sleep(1)

    # Scroll up
    print("Scroll up (distance = 10)")
    x11_mouse.scroll(10)
    sleep(1)

    # Cleanup mouse
    x11_mouse.cleanup()
    sleep(1)


def main():
    print("X11 INPUT SHOWCASE")
    print("This script showcases every available keyboard and mouse action.")
    sleep(3)

    demo_keyboard()
    demo_mouse()

    print("\nDEMO COMPLETE")


if __name__ == "__main__":
    print("Focus on your desired window. Time remaining until action: ")
    pauseTime = 5
    
    while True:
        print(pauseTime,end="\r")
        sleep(1)
        pauseTime-=1
        if pauseTime<=0:
            main()
            break
