# Custom imports
from at_spi_tree import *
from focus_listener import get_current_focus_state
from para_maker import at_pm
from web_aut import rcv_web_int

# Custom imports - CPP modules
import x11_mouse
import x11_keyboard

import time
import asyncio

def cur_state():
    app_id = get_focused_window_pid()
    my_app = find_application_by_pid(app_id)
    elements = traverse_tree(my_app) # This is done repeatedly to ensure that UI update changes are reflected, and indexing errors are avoided
    return (elements,at_pm(elements))

def interact(prompt,model):
    """Interactive mode to explore and interact with elements"""
    
    while True:
        choice = asyncio.run(rcv_web_int(model,prompt))
        print(choice)
        if choice[:7]=="THOUGHT":
            choice = choice.split("\n")
            print(f"THOUGHT: <{choice[0]}>")
            choice=choice[1][8:]
            print(f"ACTION: <{choice}>")
        parts = choice.split(maxsplit=1)
        command = parts[0].lower()
        if command=="end":
            print(f"From model: {parts[1]}")
            break
        
        elementsf,parse = cur_state()
        cur_focus = get_current_focus_state()
        focused_all = parse+"\n"+cur_focus

        try:
            if command == "env": # VIEW ENVIRONMENTAL APPS
                with open("env.json") as f:
                    allowed_applications = json.load(f)

                res=""
                for app in allowed_applications["apps"]:
                    res+=app+"\n"
                prompt = res

            elif command == "view": # VIEW APPLICATIONS
                prompt = f"view:\n{filter_applications(list_applications(False))}"

            elif command == "open": # OPEN AN APPLICATION
                app_pid=open_application(parts[1])
                focus_window_by_pid(app_pid)
                prompt = focused_all

            elif command == "run": # RUN TERMINAL COMMAND AND RETRIEVE OUTPUT
                output = run_terminal_command(parts[1])
                prompt = output

            elif command == "focus": # FOCUS ON APPLICATION
                idx=int(parts[1])
                focus_window_by_pid(idx)
                prompt = focused_all

            elif command == "request":
                prompt = input("From model: "+parts[1]+": ") 

            # Mouse actions
            elif command == "click": # LEFT CLICK
                idx = int(parts[1])
                elem = elementsf[idx]
                print(f"\nClicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
                x11_mouse.click()
                prompt = focused_all

            elif command == "rclick": # RIGHT CLICK
                idx = int(parts[1])
                elem = elementsf[idx]
                print(f"\nRight clicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
                x11_mouse.right_click()
                prompt = focused_all

            elif command == "dblclick":
                idx = int(parts[1])
                elem = elementsf[idx]
                print(f"\nDouble clicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
                x11_mouse.double_click()
                prompt = focused_all

            # Keyboard actions
            elif command == "press": # KEY PRESS
                x11_keyboard.press_combo(parts[1]) # parts[1] is the key combo here
                prompt = focused_all

            elif command == 'type': # TYPE TEXT
                x11_keyboard.type_text(parts[1]) # parts[1] is the text to be typed here
                prompt = focused_all
               
            else:
                print(f"Command {command} is invalid")
                
        except Exception as e:
            error_msg = str(e)
            prompt = f"ERROR: Command '{command}' failed with: {error_msg}\n"

x11_mouse.init()
x11_keyboard.init()
command = input("Enter your command: ")
model = "chatgpt"
interact(command,model)
