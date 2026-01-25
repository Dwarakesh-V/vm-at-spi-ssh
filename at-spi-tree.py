import pyatspi
import subprocess
import time
import x11_keyboard
x11_keyboard.init()

def list_applications():
    """List all available applications"""
    desktop = pyatspi.Registry.getDesktop(0)
    print("Available applications:")
    
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            try:
                pid = app.get_process_id()
                print(f"  {i+1}. {app.name} (PID: {pid})")
            except:
                print(f"  {i+1}. {app.name}")
        except:
            continue
    print()

def traverse_tree_interactive(accessible, depth=0, max_depth=50):
    """Recursively traverse the accessibility tree"""
    if depth > max_depth:
        return []
    
    interactive_elements = []
    
    try:
        # Check if this element is accessible
        if is_visible_and_enabled(accessible):
            info = get_element_info(accessible, depth)
            if info:
                interactive_elements.append(info)
        
        # Traverse children
        for i in range(accessible.childCount):
            try:
                child = accessible.getChildAtIndex(i)
                if child:
                    interactive_elements.extend(traverse_tree_interactive(child, depth + 1, max_depth))
            except:
                continue
                
    except Exception as e:
        pass
    
    return interactive_elements

def get_element_info(accessible, depth):
    """Extract relevant information from any SINGLE accessible element"""
    try:
        name = accessible.name or None
        if not name:
            return None
        role = accessible.getRoleName()
        description = accessible.description or ""
        
        return {
            'name': name,
            'role': role,
            'description': description,
            'depth': depth,
            'accessible': accessible  # Store the actual accessible object
        }
    except Exception as e:
        print(f"Exception {e} has occurred")
        return None

def is_visible_and_enabled(accessible):
    """Check the enabled state and visibility state of the elements on screen"""
    try:
        state = accessible.getState()
        return (
            state.contains(pyatspi.STATE_VISIBLE) and
            state.contains(pyatspi.STATE_ENABLED) and
            state.contains(pyatspi.STATE_SHOWING) and 
            not state.contains(pyatspi.STATE_DEFUNCT)
        )
    except:
        return False
    
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

def scan(app):
    """Scan for interactive elements in a specific application"""
    print(f"Scanning accessibility tree for: {app.name}")
    
    elements = traverse_tree_interactive(app)
    
    if elements:
        for elem in elements:
            indent = "  " * elem['depth']
            print(f"{indent}[{elem['role']}] {elem['name']}")
            if elem['description']:
                print(f"{indent}  Description: {elem['description']}")
    else:
        print("No interactive elements found\n")
    
    print(f"\nTotal interactive elements found: {len(elements)}")
    return elements

def open_application(command, wait_time=3):
    """Open an application using Popen"""
    print(f"Opening application: {command}")
    
    try:
        # Open the application
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Application started (PID: {process.pid})")
        print(f"Waiting for application to initialize...\n")
        time.sleep(wait_time)
        
        # Try to find the application in the accessibility tree
        app = find_application_by_pid(process.pid)
        
        if app:
            print(f"Found application: {app.name}")
            return app
        else:
            print(f"Could not find application in accessibility tree")
            print(f"\nCurrently available applications:")
            list_applications()
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

# Interactiveness

def perform_action(accessible, action_name="click"):
    """Perform an action on an accessible element"""
    try:
        # Get the Action interface
        action = accessible.queryAction()
        
        # Find and perform the action
        for i in range(action.nActions):
            if action_name.lower() in action.getName(i).lower():
                action.doAction(i)
                print(f"Performed action: {action.getName(i)}")
                return True
        
        # If specific action not found, try default action (usually index 0)
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

def click_element(accessible):
    """Click/activate an element"""
    return perform_action(accessible, "click")

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
    except Exception as e:
        print(f"Error getting actions: {e}")
        return []

def interactive_mode(elements):
    """Interactive mode to explore and interact with elements"""
    if not elements:
        print("No elements to interact with")
        return
    
    while True:
        print("--- Interactive Mode ---")
        
        # Show elements with indices
        for i, elem in enumerate(elements):
            indent = "  " * elem['depth']
            print(f"{i}: {indent}[{elem['role']}] {elem['name']}")
        
        print("\n" + "-"*60)
        print("Commands:")
        print("  click <number> - Click/activate element")
        print("  type_text <text> - Type text using virtual keyboard")
        print("  press_combo <keys> (e.g., ctrl+c) - Press keys on virtual keyboard")
        print("  actions <number> - Show available actions")
        print("  end - Quit interactive mode")
        print("-"*60+"\n")
        
        choice = input("Enter command: ").strip()
        
        if choice.lower() == 'end':
            break
        
        parts = choice.split()
        command = parts[0].lower()
        
        try:
            if command == 'click':
                idx = int(parts[1])
                elem = elements[idx]
                print(f"\nClicking: [{elem['role']}] {elem['name']}")
                click_element(elem['accessible'])

            elif command == 'type_text':       
                x11_keyboard.type_text(parts[1])
            
            elif command == 'press_combo':
                x11_keyboard.press_combo(parts[1])
                
            elif command == 'actions':
                idx = int(parts[1])
                elem = elements[idx]
                print(f"\nAvailable actions for: [{elem['role']}] {elem['name']}")
                actions = get_available_actions(elem['accessible'])
                if actions:
                    for action in actions:
                        print(f"  - {action['name']}: {action['description']}")
                        if action['keybinding']:
                            print(f"    Keybinding: {action['keybinding']}")
                else:
                    print("  No actions available")           
            else:
                print("Invalid command")
                
        except IndexError:
            print(f"Invalid element number. Valid range: 0-{len(elements)-1}")
        except ValueError:
            print("Invalid number format")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AT-SPI Interactive Elements Scanner - Opens and scans applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List running applications
  python3 at-spi-tree.py --list
  
  # Open an application and scan it
  python3 at-spi-tree.py --open "xfce4-terminal"
  
  # Find by name and scan
  python3 at-spi-tree.py --name firefox
  
  # Find by PID and scan
  python3 at-spi-tree.py --pid 1234
  
  # Interactive mode (add -i flag to any scan command)
  python3 at-spi-tree.py --name gedit -i
        """
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all currently running applications'
    )
    parser.add_argument(
        '--open',
        metavar='COMMAND',
        help='Open an application with the given command'
    )
    parser.add_argument(
        '--name',
        metavar='APP_NAME',
        help='Find and scan an application by name'
    )
    parser.add_argument(
        '--pid',
        metavar='PID',
        type=int,
        help='Find and scan an application by process ID'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Enter interactive mode after scanning'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_applications()
    else:
        app = None
        
        # Find or open the application
        if args.open:
            app = open_application(args.open)
        elif args.name:
            print(f"Finding application: {args.name}")
            app = find_application_by_name(args.name)
            if app:
                print(f"Found application: {app.name}\n")
            else:
                print(f"Application not found: {args.name}")
                print("\nCurrently available applications:")
                list_applications()
        elif args.pid:
            print(f"Finding application by PID: {args.pid}")
            app = find_application_by_pid(args.pid)
            if app:
                print(f"Found application: {app.name}\n")
            else:
                print(f"Application not found with PID: {args.pid}")
                print("\nCurrently available applications:")
                list_applications()
        else:
            parser.print_help()
            print("\n")
            list_applications()
            exit(0)
        
        # Scan the application if found
        if app:
            elements_int = scan(app)
            try:
                print(elements_int[0],end=" ")
            except IndexError:
                print("No interactive elements found.")
            
            # Enter interactive mode if requested
            if args.interactive and elements_int:
                interactive_mode(elements_int)

    x11_keyboard.cleanup()