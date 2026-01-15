import pyatspi
import subprocess
import time

def list_applications():
    """List all available applications"""
    desktop = pyatspi.Registry.getDesktop(0)
    print("Available applications:")
    
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            print(f"  {i+1}. {app.name}")
        except:
            continue
    print()

def traverse_tree(accessible, depth=0, max_depth=50):
    """Recursively traverse the accessibility tree"""
    if depth > max_depth:
        return []
    
    interactive_elements = []
    
    try:
        # Check if this element isaccessible
        if is_visible_and_enabled(accessible):
            info = get_element_info(accessible)
            if info:
                info['depth'] = depth
                interactive_elements.append(info)
        
        # Traverse children
        for i in range(accessible.childCount):
            try:
                child = accessible.getChildAtIndex(i)
                if child:
                    interactive_elements.extend(traverse_tree(child, depth + 1, max_depth))
            except:
                continue
                
    except Exception as e:
        pass
    
    return interactive_elements

def get_element_info(accessible):
    """Extract relevant information from any SINGLE accessible element"""
    try:
        name = accessible.name or None
        if not name:
            return
        role = accessible.getRoleName()
        description = accessible.description or ""
        
        return {
            'name': name,
            'role': role,
            'description': description
        }
    except Exception as e:
        print(f"Exception {e} has occured")
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

def scan_application(app_name=None):
    """Scan for interactive elements in a specific application or all applications"""
    desktop = pyatspi.Registry.getDesktop(0)
    
    print(f"Scanning accessibility tree...")
    
    all_elements = []
    
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            current_app_name = app.name
            
            # Filter by application name if specified
            if app_name and app_name.lower() not in current_app_name.lower():
                continue
            
            print(f"Application: {current_app_name}")
            
            elements = traverse_tree(app)
            
            if elements:
                for elem in elements:
                    indent = "  " * elem['depth']
                    print(f"{indent}[{elem['role']}] {elem['name']}")
                    if elem['description']:
                        print(f"{indent}  Description: {elem['description']}")
                
                all_elements.extend(elements)
            else:
                print("No interactive elements found\n")
            
            print()
            
        except Exception:
            continue
    
    print(f"Total interactive elements found: {len(all_elements)}")
    return all_elements


def scan_application_by_pid(target_pid):
    """Scan for interactive elements in a specific application by PID"""
    desktop = pyatspi.Registry.getDesktop(0)

    print(f"Scanning accessibility tree...")

    all_elements = []

    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)

            try:
                app_pid = app.getApplication().get_process_id()
            except Exception:
                continue

            # Filter by PID
            if target_pid != app_pid:
                continue

            current_app_name = app.name
            print(f"Application: {current_app_name}")

            elements = traverse_tree(app)

            if elements:
                for elem in elements:
                    indent = "  " * elem['depth']
                    print(f"{indent}[{elem['role']}] {elem['name']}")
                    if elem['description']:
                        print(f"{indent}  Description: {elem['description']}")

                all_elements.extend(elements)
            else:
                print("No interactive elements found\n")

            print()

        except Exception:
            continue

    print(f"Total interactive elements found: {len(all_elements)}")
    return all_elements

def open_and_scan_application(command, wait_time=3):
    """Open an application using Popen and scan its accessibility tree"""
    print(f"Opening application: {command}")
    
    process = None
    try:
        # Open the application
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Application started (PID: {process.pid})")
        print(f"Waiting for application to initialize...\n")
        time.sleep(wait_time)
        
        # Try to find the application in the accessibility tree
        app = find_application_by_pid(process.pid)

        
        if app:    
            # Scan the application
            elements = traverse_tree(app)
            
            if elements:
                for elem in elements:
                    indent = "  " * elem['depth']
                    print(f"{indent}[{elem['role']}] {elem['name']}")
                    if elem['description']:
                        print(f"{indent}  Description: {elem['description']}")
            else:
                print("No interactive elements found in the application")
            
            print(f"Total interactive elements found: {len(elements)}")
            return elements
        else:
            print(f"Could not find application")
            print(f"\nCurrently available applications:")
            list_applications()
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def find_application_by_command(command_name):
    """Find an application in the accessibility tree by command name"""
    desktop = pyatspi.Registry.getDesktop(0)
    
    # Extract base command name (e.g., "gedit" from "/usr/bin/gedit")
    base_cmd = command_name.split('/')[-1].split()[0]
    
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
            app_name = app.name.lower()
            
            # Check if the application name matches the command
            if base_cmd.lower() in app_name or app_name in base_cmd.lower():
                return app
        except:
            continue
    
    return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AT-SPI Interactive Elements Scanner - Opens and scans applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 atspi_scanner.py "xfce4-terminal"
  python3 atspi_scanner.py --list
  python3 atspi_scanner.py --scan firefox
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        help='Command to launch the application (e.g., gedit, firefox, gnome-calculator)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all currently running applications'
    )
    parser.add_argument(
        '--scan',
        metavar='APP_NAME',
        help='Scan an already running application by name'
    )
    parser.add_argument(
        '--scan_by_pid',
        metavar='APP_PID',
        help='Scan an already running application by process ID'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_applications()
    elif args.scan:
        scan_application(args.scan)
    elif args.scan_by_pid:
        scan_application_by_pid(int(args.scan_by_pid))
    elif args.command:
        open_and_scan_application(args.command)
    else:
        parser.print_help()
        print("\n")
        list_applications()