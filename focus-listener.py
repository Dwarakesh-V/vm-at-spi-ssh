import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio
import json
from time import sleep

BUS_NAME = "org.vmatspissh.FocusWatcher"
OBJ_PATH = "/org/example/FocusWatcher"
IFACE_NAME = "org.vmatspissh.FocusWatcher"

def get_current_focus_state():
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    proxy = Gio.DBusProxy.new_sync(
        connection,
        Gio.DBusProxyFlags.NONE,
        None,
        BUS_NAME,
        OBJ_PATH,
        IFACE_NAME,
        None
    )

    result = proxy.call_sync(
        "GetCurrentState",
        None,
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )

    payload = result.unpack()[0]
    return json.loads(payload)

if __name__ == "__main__":
    print("Getting current state in 2 seconds...")
    sleep(2)
    state = get_current_focus_state()
    print(state)
