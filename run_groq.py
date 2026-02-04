# Custom imports
from at_spi_tree import *
from focus_listener import get_current_focus_state
from para_maker import at_pm

# Custom imports - CPP modules
import x11_mouse
import x11_keyboard

# Standard imports
import json
import time

# Groq Import
from groq import Groq

# Groq setup - Automatically pulls from os.environ.get("GROQ_API_KEY")
client = Groq()

# Model interaction
def generate_model_response(messages):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
    )

    full_text = completion.choices[0].message.content.strip()
    
    # Logic to extract only the ACTION line
    # This handles "ACTION: click 10" or just "click 10"
    lines = full_text.split('\n')
    action_line = [l for l in lines if l.startswith("ACTION:")]
    
    if action_line:
        final_command = action_line[0].replace("ACTION:", "").strip()
    else:
        # Fallback if the model didn't follow formatting perfectly
        final_command = lines[-1].strip()

    print(f"Model Thought: {full_text}") # Good for debugging
    return final_command


# Main interaction loop
def interact(messages):
    """Interactive mode to explore and interact with elements"""

    while True:
        print("messagevar\n\n\n",messages[1],messages[2],"\n\n\nendmessage")
        
        choice = generate_model_response(messages)
        # choice = "env"
        parts = choice.split(maxsplit=1)
        print(parts)
        try:
            command = parts[0].lower()
        except IndexError:
            continue

        if command == "end":
            print(f"From model: {parts[1]}")
            break

        app_id = get_focused_window_pid()
        my_app = find_application_by_pid(app_id)
        elements = traverse_tree_interactive(my_app)

        # Update the context messages at indices 1 and 2
        messages[1] = {
            "role": "system",
            "content": f"UI Tree State: {at_pm(elements)}"
        }
        messages[2] = {
            "role": "system",
            "content": f"Focus State: {get_current_focus_state()}"
        }

        try:
            if command == "env":
                with open("env.json") as f:
                    allowed_applications = json.load(f)

                res = "".join([app + "\n" for app in allowed_applications["apps"]])

                messages.append({"role": "user", "content": res})
                messages.append({
                    "role": "assistant", 
                    "content": f"Applications\n{filter_applications(list_applications(False))}"
                })

            elif command == "open":
                app_pid = open_application(parts[1])
                focus_window_by_pid(app_pid)
                messages.append({"role": "user", "content": f"Opened application. PID: {app_pid}"})

            elif command == "run":
                output = run_terminal_command(parts[1])
                messages.append({"role": "user", "content": f"Command output\n{output}"})

            elif command == "focus":
                idx = int(parts[1])
                focus_window_by_pid(idx)
                messages.append({"role": "user", "content": f"Window focused: {idx}"})

            elif command == "request":
                user_input = input("From model: " + parts[1])
                messages.append({"role": "user", "content": f"From user: {user_input}"})

            elif command == "click":
                idx = int(parts[1])
                elem = elements[idx]
                x11_mouse.move_human(elem['location'][0], elem['location'][1])
                x11_mouse.click()
                messages.append({"role": "user", "content": f"{command} [{elem['role']}-{elem['name']}]"})

            elif command == "dblclick":
                idx = int(parts[1])
                elem = elements[idx]
                x11_mouse.move_human(elem['location'][0], elem['location'][1])
                x11_mouse.double_click()
                messages.append({"role": "user", "content": f"{command} [{elem['role']}-{elem['name']}]"})

            elif command == "rclick":
                idx = int(parts[1])
                elem = elements[idx]
                x11_mouse.move_human(elem['location'][0], elem['location'][1])
                x11_mouse.right_click()
                messages.append({"role": "assistant", "content": f"{command} [{elem['role']}-{elem['name']}]"})

            elif command == "press":
                x11_keyboard.press_combo(parts[1])
                messages.append({"role": "assistant", "content": f"{command} {parts[1]}"})

            elif command == "type":
                x11_keyboard.type_text(parts[1])
                messages.append({"role": "assistant", "content": f"{command} {parts[1]}"})

            else:
                print(f"Command {command} is invalid")

        except Exception as e:
            error_msg = str(e)
            messages.append({
                "role": "system",
                "content": f"ERROR: Command '{command}' failed with: {error_msg}"
            })

# Bootstrap
if __name__ == "__main__":
    x11_mouse.init()
    x11_keyboard.init()
    print("X11 Input Systems Initialized.")
    messages = []

    with open("model_prompt.txt") as f:
        base_prompt = f.read()

    task_input = input("Enter your command: ")
    time.sleep(2)

    # Setup Initial State
    messages.append({
        "role": "system",
        "content": f"{base_prompt}\n\nTask: {task_input}"
    })
    messages.append({"role": "system", "content": "UI State: None currently"})
    messages.append({"role": "system", "content": "Focus State: None currently"})

    print("\nStarting Groq Interaction...\n")
    interact(messages)