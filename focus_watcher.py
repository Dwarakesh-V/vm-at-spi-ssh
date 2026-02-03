import gi
gi.require_version("Atspi", "2.0")
gi.require_version("Gio", "2.0")
from gi.repository import Atspi, GLib, Gio
import json

BUS_NAME = "org.vmatspissh.FocusWatcher"
OBJ_PATH = "/org/example/FocusWatcher"
IFACE_NAME = "org.vmatspissh.FocusWatcher"

INTROSPECTION_XML = """
<node>
  <interface name="org.vmatspissh.FocusWatcher">
    <method name="GetCurrentState">
      <arg type="s" name="state_json" direction="out"/>
    </method>
  </interface>
</node>
"""

current_state = {}

def get_text_content(obj):
    try:
        text_iface = obj.get_text()
        if not text_iface:
            return ""
        count = text_iface.get_character_count()
        if count > 0:
            return text_iface.get_text(0, count)
    except Exception:
        pass
    return ""

def get_description(obj):
    try:
        return obj.get_description() or ""
    except Exception:
        return ""

def get_label_text(obj):
    try:
        relset = obj.get_relation_set()
        for rel in relset:
            if rel.get_relation_type() == Atspi.RelationType.LABELLED_BY:
                targets = rel.get_targets()
                if targets:
                    return targets[0].get_name() or ""
    except Exception:
        pass
    return ""

def on_event(event):
    global current_state
    obj = event.source

    name = obj.get_name() or ""
    role = obj.get_role_name() or ""
    app = obj.get_application().get_name() or ""

    text = get_text_content(obj)
    desc = get_description(obj)
    label = get_label_text(obj)

    semantic = (
        text.strip()
        or desc.strip()
        or label.strip()
        or name.strip()
        or role.strip()
    )

    current_state = {
        "app": app,
        "role": role,
        "name": name,
        "semantic": semantic,
    }

class FocusWatcherService:
    def __init__(self, connection):
        self.connection = connection

        self.node_info = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION_XML)
        self.iface_info = self.node_info.interfaces[0]

        self.connection.register_object(
            OBJ_PATH,
            self.iface_info,
            self.handle_method_call,
            None,
            None
        )

    def handle_method_call(self, connection, sender, object_path,
                           interface_name, method_name, parameters, invocation):

        if method_name == "GetCurrentState":
            payload = json.dumps(current_state)
            invocation.return_value(GLib.Variant("(s)", (payload,)))

def main():
    Atspi.init()

    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    Gio.bus_own_name_on_connection(
        connection,
        BUS_NAME,
        Gio.BusNameOwnerFlags.NONE,
        None,
        None
    )

    service = FocusWatcherService(connection)

    listener = Atspi.EventListener.new(on_event)
    listener.register("object:state-changed:focused")

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()
