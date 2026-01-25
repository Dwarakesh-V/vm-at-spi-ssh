import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, GLib

def build_path(obj):
    parts = []
    cur = obj
    while cur:
        try:
            parent = cur.get_parent()
            if parent:
                idx = parent.get_index_in_parent(cur)
                parts.append(str(idx))
            else:
                parts.append("root")
            cur = parent
        except Exception:
            break
    return "/" + "/".join(reversed(parts))

def get_text_content(obj):
    try:
        text_iface = Atspi.Accessible.get_text_iface(obj)
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
        desc = obj.get_description()
        if desc:
            return desc
    except Exception:
        pass
    return ""

def get_label_text(obj):
    try:
        relset = obj.get_relation_set()
        for rel in relset:
            if rel.get_relation_type() == Atspi.RelationType.LABELLED_BY:
                targets = rel.get_targets()
                if targets:
                    label_obj = targets[0]
                    name = label_obj.get_name()
                    if name:
                        return name
    except Exception:
        pass
    return ""

def get_current_focus():
    try:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            focus = app.get_focused()
            if focus:
                name = focus.get_name() or ""
                role = focus.get_role_name() or ""
                app_name = app.get_name() or ""
                synth_path = build_path(focus)

                text = get_text_content(focus)
                desc = get_description(focus)
                label = get_label_text(focus)

                semantic = (
                    text.strip()
                    or desc.strip()
                    or label.strip()
                    or name.strip()
                    or role.strip()
                )

                return {
                    "app": app_name,
                    "role": role,
                    "name": name,
                    "text": text,
                    "description": desc,
                    "label": label,
                    "semantic": semantic,
                    "path": synth_path,
                    "object": focus,
                }
    except Exception:
        pass

    return None

def on_event(event):
    obj = event.source
    try:
        name = obj.get_name() or ""
        role = obj.get_role_name() or ""
        app = obj.get_application().get_name() or ""
        synth_path = build_path(obj)

        text = get_text_content(obj)
        desc = get_description(obj)
        label = get_label_text(obj)

        # Pick the best human description
        semantic = (
            text.strip()
            or desc.strip()
            or label.strip()
            or name.strip()
            or role.strip()
        )

        print(
            f"[FOCUS] app={app} role={role} name={name} "
            f"text={text} desc={desc} label={label} "
            f"semantic={semantic} path={synth_path}",
            flush=True
        )

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)

def main():
    Atspi.init()

    # Initial snapshot
    current = get_current_focus()
    if current:
        print(
            f"[CURRENT] app={current['app']} role={current['role']} name={current['name']} "
            f"text={current['text']} desc={current['description']} label={current['label']} "
            f"semantic={current['semantic']} path={current['path']}",
            flush=True
        )

    listener = Atspi.EventListener.new(on_event)
    listener.register("object:state-changed:focused")

    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()
