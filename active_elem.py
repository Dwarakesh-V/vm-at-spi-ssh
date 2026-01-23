import pyatspi
from time import sleep

def find_focused_text_element():
    desktop = pyatspi.Registry.getDesktop(0)

    for app in desktop:
        try:
            # Skip apps that aren’t active
            if not app.getState().contains(pyatspi.STATE_ACTIVE):
                continue

            focused = app.queryComponent().getFocus()
            if not focused:
                continue

            role = focused.getRoleName().lower()

            # Heuristic: only return real text inputs
            if role in ("text", "entry", "password text", "editable text"):
                return focused

            # Fallback: return whatever has focus
            return focused

        except Exception:
            pass

    return None

sleep(3)
el = find_focused_text_element()

if el:
    print("Name:", el.name)
    print("Role:", el.getRoleName())
    print("Description:", el.description)
    print("Application:", el.getApplication().name)

    # If it’s actually a text field, dump the text
    try:
        text_iface = el.queryText()
        content = text_iface.getText(0, text_iface.characterCount)
        print("Text content:", repr(content))
        print("Cursor position:", text_iface.caretOffset)
    except Exception:
        print("Focused element is not a text field")
else:
    print("No focused element found")
