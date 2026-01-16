import pyatspi

def extract_text_from_tree(obj, depth=0, max_depth=50):
    if depth > max_depth:
        return

    indent = "  " * depth

    try:
        role = obj.getRoleName()
        name = obj.name
        print(f"{indent}{role} | {name}")
    except:
        pass

    # Try to extract text
    try:
        text_iface = obj.queryText()
        char_count = text_iface.characterCount
        if char_count > 0:
            text = text_iface.getText(0, char_count)
            if text.strip():
                print(f"{indent}  TEXT: {repr(text[:200])}")
    except:
        pass

    # Recurse
    try:
        for i in range(obj.childCount):
            child = obj.getChildAtIndex(i)
            extract_text_from_tree(child, depth + 1, max_depth)
    except:
        pass

desktop = pyatspi.Registry.getDesktop(0)

for i in range(desktop.childCount):
    app = desktop.getChildAtIndex(i)
    print(f"\n=== APP: {app.name} ===")
    extract_text_from_tree(app)
