import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi
import sys
from time import sleep

def find_app_by_pid(pid):
    desktop = Atspi.get_desktop(0)

    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        try:
            if app.get_process_id() == pid:
                return app
        except Exception:
            pass

    return None


def get_visible_buttons(app):
    buttons = []

    def walk(node):
        try:
            state = node.get_state_set()
            if (
                state.contains(Atspi.StateType.VISIBLE) and
                state.contains(Atspi.StateType.SHOWING) and
                state.contains(Atspi.StateType.ENABLED) and
                state.contains(Atspi.StateType.SENSITIVE)
            ):
                try:
                    comp = node.get_component_iface()
                    if comp:
                        x, y, w, h = comp.get_extents(
                            Atspi.CoordType.DESKTOP
                        )
                        if w > 0 and h > 0:
                            buttons.append(node)
                except Exception:
                    pass
        except Exception:
            pass

        for i in range(node.get_child_count()):
            walk(node.get_child_at_index(i))

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

    print(f"Application: {app.get_name()} (PID {pid})")

    buttons = get_visible_buttons(app)
    for btn in buttons:
        name = btn.get_name()
        if name:
            print(f"  Button: {name}")


if __name__ == "__main__":
    sleep(3)  # interact with UI before scan
    main()
