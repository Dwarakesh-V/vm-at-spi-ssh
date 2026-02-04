# sudo apt install python3-gi gir1.2-atspi-2.0 at-spi2-core
# python3/python/py -m venv .venv --system-site-packages

# Custom
import pyatspi
import x11_keyboard
import x11_mouse
from para_maker import at_pm

# Built-in
import subprocess
import time
import argparse
import sys
import json

# Initialize the virtual keyboard and mouse
x11_keyboard.init()
x11_mouse.init()

def focus_window_by_pid(pid: int) -> None:
    search = subprocess.run(
        ["xdotool", "search", "--pid", str(pid)],
        capture_output=True,
        text=True
    )

    if search.returncode != 0 or not search.stdout.strip():
        return

    for wid in search.stdout.split():
        subprocess.run(
            ["xdotool", "windowactivate", wid],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    
def get_focused_window_pid():
    try:
        wid = subprocess.check_output(
            ["xdotool", "getwindowfocus"],
            stderr=subprocess.DEVNULL
        ).strip()

        pid = subprocess.check_output(
            ["xdotool", "getwindowpid", wid],
            stderr=subprocess.DEVNULL
        ).strip()

        return int(pid)

    except subprocess.CalledProcessError:
        return None

# Locate application

def list_applications(disp_res=True):
    """List all available applications"""
    desktop = pyatspi.Registry.getDesktop(0)
    if disp_res:
        print("Available applications:")
    applications = []

    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            try:
                pid = app.get_process_id()
                if disp_res:
                    print(f"  {i+1}. {app.name} (PID: {pid})")
                applications.append({"name":app.name,"pid":pid})
            except:
                if disp_res:
                    print(f"  {i+1}. {app.name}")
                applications.append({"name":app.name,"pid":None})
        except:
            continue
    if disp_res:
        print()
    return applications

def filter_applications(applications):
    filtered_apps = []

    with open("env.json") as f:
        allowed_applications = json.load(f)

    applications = list_applications(False)
    for app in applications:
        if app["name"] in allowed_applications["apps"]:
            filtered_apps.append({"name":app["name"],"pid":app["pid"]})

    apps = ""
    for app_data in filtered_apps:
        apps+= f"{app_data['name']}-{app_data['pid']}\n"

    return apps

def find_application_by_pid(pid, timeout=10):
    """Find application by process ID with a 10 second timeout"""
    desktop = pyatspi.Registry.getDesktop(0)
    end_time = time.time() + timeout

    while time.time() < end_time:
        for i in range(desktop.childCount):
            try:
                app = desktop.getChildAtIndex(i)
                if app.get_process_id() == pid:
                    return app
            except:
                continue
        time.sleep(0.2)
    return None

def find_application_by_name(app_name):
    """Find an application in the accessibility tree by name"""
    desktop = pyatspi.Registry.getDesktop(0)
    
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            if app_name.lower() in app.name.lower():
                return app
        except:
            continue
    return None

def open_application(command, wait_time=2):
    """Open an application using Popen"""
    print(f"Opening application: {command}")
    
    # Open the application
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"Application started (PID: {process.pid})")
    print(f"Waiting for application to initialize...\n")
    time.sleep(wait_time)
    
    # Try to find the application in the accessibility tree
    app = find_application_by_pid(process.pid)
    
    return process.pid

# Accessibility tree elements
def get_text_content(accessible):
    """Helper to get text from the Text interface if Name is empty"""
    try:
        if accessible.name and accessible.name.strip():
            return accessible.name
            
        # text interface
        text_iface = accessible.queryText()
        content = text_iface.getText(0, -1)
        if content and content.strip():
            return content.strip()
            
    except:
        pass
    return ""

def is_relevant_element(accessible):
    try:
        state = accessible.getState()
        
        # 1. Basic Visibility
        if not (state.contains(pyatspi.STATE_VISIBLE) and state.contains(pyatspi.STATE_SHOWING)):
            return False
        if state.contains(pyatspi.STATE_DEFUNCT):
            return False

        # 2. Check Roles
        role = accessible.getRoleName().lower()
        
        # Note: 'paragraph', 'heading', 'section' are key for your quiz questions
        static_roles = [
            'label', 'static', 'text', 'heading', 'image', 'icon', 
            'paragraph', 'terminal', 'section', 'document', 'panel', 'entry'
        ]
        
        is_static_info = any(sr in role for sr in static_roles)
        is_interactive = ((state.contains(pyatspi.STATE_ENABLED) or
                          state.contains(pyatspi.STATE_FOCUSABLE)) and
                          state.contains(pyatspi.STATE_SENSITIVE))

        # 3. Check for Content (Name OR Text Interface)
        # This is where the previous version failed for <p> tags
        content = get_text_content(accessible)
        has_content = len(content) > 0

        # We keep it if it's interactive OR (it's a static role AND has text)
        return is_interactive or (is_static_info and has_content)
    except:
        return False

def get_element_info(accessible, depth):
    try:
        # Use our new helper to get the real text
        name = get_text_content(accessible)
        role = accessible.getRoleName()
        description = accessible.description or ""
        
        # Relations
        relations_info = []
        try:
            rel_set = accessible.getRelationSet()
            for i in range(rel_set.getNRelations()):
                rel = rel_set.getRelation(i)
                rtype = rel.getRelationType()
                
                if rtype == pyatspi.RELATION_LABELLED_BY:
                    target = rel.getTarget(0)
                    t_name = get_text_content(target) # Use helper here too
                    relations_info.append(f"LabelledBy: '{t_name}'")
                elif rtype == pyatspi.RELATION_LABEL_FOR:
                    target = rel.getTarget(0)
                    t_name = get_text_content(target)
                    relations_info.append(f"LabelFor: '{t_name}'")
        except:
            pass

        component = accessible.queryComponent()
        extents = component.getExtents(0) 
        
        full_description = description
        if relations_info:
            rel_str = " | ".join(relations_info)
            full_description = f"{full_description} ({rel_str})" if full_description else rel_str

        return {
            'name': name, # Can now contain static elements
            'role': role,
            'description': full_description,
            'depth': depth,
            'location': ((extents.x*2)+10, (extents.y*2)+10),
        }
    except Exception as e:
        return None

def traverse_tree(accessible, depth=0, max_depth=50):
    """Recursively traverse the accessibility tree for both static and interactive elements"""
    if depth > max_depth:
        return []
    
    elements = []
    
    try:
        # Check relevance
        if is_relevant_element(accessible):
            info = get_element_info(accessible, depth)
            if info:
                elements.append(info)
        
        # Traverse children
        for i in range(accessible.childCount):
            try:
                child = accessible.getChildAtIndex(i)
                if child:
                    elements.extend(traverse_tree(child, depth + 1, max_depth))
            except:
                continue
                
    except Exception:
        pass
    
    return elements

def run_terminal_command(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()

# ---------- EVERYTHING AFTER THIS PART IS ONLY FOR DEBUGGING AND VISUALIZATION ---------- #
# ---------------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------------- #

def perform_action(accessible, action_name="click"):
    """Perform an action on an accessible element"""
    try:
        action = accessible.queryAction()
        for i in range(action.nActions):
            if action_name.lower() in action.getName(i).lower():
                action.doAction(i)
                print(f"Performed action: {action.getName(i)}")
                return True
        
        if action.nActions > 0:
            action.doAction(0)
            print(f"Performed default action: {action.getName(0)}")
            return True
            
        print("No actions available for this element")
        return False
    except NotImplementedError:
        print(f"Element does not support actions")
        return False
    except Exception as e:
        print(f"Error performing action: {e}")
        return False

def get_available_actions(accessible):
    """List all available actions for an element"""
    try:
        action = accessible.queryAction()
        actions = []
        for i in range(action.nActions):
            actions.append({
                'index': i,
                'name': action.getName(i),
                'description': action.getDescription(i),
                'keybinding': action.getKeyBinding(i)
            })
        return actions
    except NotImplementedError:
        return []
    except Exception:
        return []

def interactive_mode(elements):
    """Interactive mode to explore and interact with elements"""
    if not elements:
        print("No elements to interact with")
        return
    
    print("\n--- Interactive Mode ---")
    print("Commands:")
    print("  click <idx>        : Click/activate element")
    print("  type <text>        : Type text")
    print("  press <keys>       : Press key combo (e.g., ctrl+c)")
    print("  actions <idx>      : Show actions for element")
    print("  info <idx>         : Show full info including relations")
    print("  list               : Re-list elements")
    print("  end                : Exit")
    print("-" * 30)

    # Helper to print list
    def print_list():
        for i, elem in enumerate(elements):
            indent = "  " * elem['depth']
            desc = f" ({elem['description']})" if elem['description'] else ""
            print(f"{i}: {indent}[{elem['role']}] {elem['name']}{desc}")

    print_list()

    while True:
        try:
            choice = input("\nCommand: ").strip()
            if not choice: continue
            
            if choice.lower() == 'end':
                break
            
            if choice.lower() == 'list':
                print_list()
                continue
            
            parts = choice.split(maxsplit=1)
            command = parts[0].lower()
            
            if command == 'type':
                if len(parts) > 1:
                    x11_keyboard.type_text(parts[1])
                continue
                
            if command == 'press':
                if len(parts) > 1:
                    x11_keyboard.press_combo(parts[1])
                continue

            # Index-based commands
            if len(parts) < 2:
                print("Missing argument")
                continue
                
            idx = int(parts[1])
            if idx < 0 or idx >= len(elements):
                print("Index out of range")
                continue
                
            elem = elements[idx]
            
            if command == 'click':
                print(f"Clicking: {elem['name']}")
                perform_action(elem['accessible'])
                
            elif command == 'actions':
                acts = get_available_actions(elem['accessible'])
                if acts:
                    for a in acts:
                        print(f"  {a['index']}. {a['name']} ({a['description']})")
                else:
                    print("  No actions available")

            elif command == 'info':
                print(f"\n--- Element Info [{idx}] ---")
                print(f"Name: {elem['name']}")
                print(f"Role: {elem['role']}")
                print(f"Desc: {elem['description']}")
                print(f"Loc : {elem['location']}")
                
            else:
                print("Unknown command")

        except ValueError:
            print("Invalid number")
        except Exception as e:
            print(f"Error: {e}")


# Entry
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AT-SPI Comprehensive Scanner")
    parser.add_argument('--list', action='store_true', help='List running apps')
    parser.add_argument('--open', metavar='CMD', help='Open app by command')
    parser.add_argument('--name', metavar='NAME', help='Find app by name')
    parser.add_argument('--pid', type=int, help='Find app by PID')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    if args.list:
        list_applications()
        sys.exit(0)

    app = None
    if args.open:
        pid = open_application(args.open)
        app = find_application_by_pid(pid)
    elif args.name:
        app = find_application_by_name(args.name)
    elif args.pid:
        app = find_application_by_pid(args.pid)
    else:
        # Default behavior: Try to focus current window if nothing specified, or list
        focused_pid = get_focused_window_pid()
        if focused_pid:
            print(f"Scanning focused window (PID: {focused_pid})...")
            app = find_application_by_pid(focused_pid)
        else:
            parser.print_help()
            sys.exit(1)

    if app:
        print(f"Scanning: {app.name} (PID: {app.get_process_id()})")
        
        elements = traverse_tree(app)
        
        print(at_pm(elements))
        print(f"\nTotal elements found: {len(elements)}")

        if args.interactive:
            interactive_mode(elements)
    else:
        print("Application not found.")

    x11_keyboard.cleanup()