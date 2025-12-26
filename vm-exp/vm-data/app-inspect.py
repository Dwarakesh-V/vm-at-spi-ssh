import pyatspi
import sys
from time import sleep

def find_app_by_pid(pid):
    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        try:
            if app.get_process_id() == pid:
                return app
        except:
            pass
    return None


def get_visible_buttons(app):
    buttons = []

    def walk(node):
        try:
            state = node.getState()
            if (
                state.contains(pyatspi.STATE_VISIBLE) and
                state.contains(pyatspi.STATE_SHOWING) and
                state.contains(pyatspi.STATE_ENABLED) and
                state.contains(pyatspi.STATE_SENSITIVE)
            ):
                try:
                    comp = node.queryComponent()
                    x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
                    if w > 0 and h > 0:
                        buttons.append(node)
                except:
                    pass
        except:
            pass

        for i in range(node.childCount):
            walk(node.getChildAtIndex(i))

    walk(app)
    return buttons


def main():
    if len(sys.argv) != 2:
        print("Usage: python visible_buttons_by_pid.py <PID>")
        sys.exit(1)

    pid = int(sys.argv[1])
    app = find_app_by_pid(pid)

    if not app:
        print(f"No AT-SPI application found for PID {pid}")
        sys.exit(1)

    print(f"Application: {app.name} (PID {pid})")

    buttons = get_visible_buttons(app)
    for btn in buttons:
        if btn.name:
            print(f"  Button: {btn.name}")


if __name__ == "__main__":
    sleep(3) # Click on any button to specifically look for its children like File -> Export
    main()