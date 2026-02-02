# Custom imports
from at_spi_tree import *
from focus_listener import get_current_focus_state
from para_maker import at_pm

# Custom imports - CPP modules
import x11_mouse
import x11_keyboard

# Standard imports
import os
import json

# Gemini
import google.generativeai as genai

# Gemini setup
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "temperature": 0.4,
        "top_p": 0.9,
        "max_output_tokens": 128,
    }
)

# Model interaction
def generate_model_response(model, messages):
    """
    Generate a response from Gemini.
    Behavior is fully determined by the current messages list.
    """

    prompt = build_prompt_from_messages(messages)
    response = model.generate_content(prompt)

    text = response.text.strip()
    print(text)
    return text


def build_prompt_from_messages(messages):
    """
    Deterministically rebuilds the prompt from messages.
    Backward edits are fully respected.
    """

    role_map = {
        "system": "System",
        "user": "User",
        "assistant": "Assistant"
    }

    parts = []
    for msg in messages:
        role = role_map.get(msg["role"], "User")
        parts.append(f"{role}:\n{msg['content']}")

    return "\n\n".join(parts)

# Main interaction loop
def interact(model, messages):
    """Interactive mode to explore and interact with elements"""

    while True:
        choice = generate_model_response(model, messages)

        parts = choice.split(maxsplit=1)
        command = parts[0].lower()

        if command == "end":
            print(f"From model: {parts[1]}")

        app_id = get_focused_window_pid()
        my_app = find_application_by_pid(app_id)
        elements = traverse_tree_interactive(my_app)

        try:
            if command == "env":
                with open("env.json") as f:
                    allowed_applications = json.load(f)

                res = ""
                for app in allowed_applications["apps"]:
                    res += app + "\n"

                print(res)
                messages.append({
                    "role": "assistant",
                    "content": res
                })

            elif command == "view":
                messages.append({
                    "role": "assistant",
                    "content": f"view:\n{filter_applications(list_applications(False))}"
                })

            elif command == "open":
                app_pid = open_application(parts[1])
                focus_window_by_pid(app_pid)
                messages.append({
                    "role": "assistant",
                    "content": f"Opened application. PID: {app_pid}"
                })

            elif command == "run":
                output = run_terminal_command(parts[1])

                messages[1] = {
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2] = {
                    "role": "system",
                    "content": get_current_focus_state()
                }

                messages.append({
                    "role": "user",
                    "content": f"Command output\n{output}"
                })

            elif command == "focus":
                idx = int(parts[1])
                focus_window_by_pid(idx)
                messages.append({
                    "role": "user",
                    "content": f"Window focused: {idx}"
                })

            elif command == "request":
                user_input = input("From model: " + parts[1])
                messages.append({
                    "role": "user",
                    "content": f"From user: {user_input}"
                })

            elif command == "click":
                idx = int(parts[1])
                elem = elements[idx]

                print(f"\nClicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0], elem['location'][1])
                x11_mouse.click()

                messages[1] = {
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2] = {
                    "role": "system",
                    "content": get_current_focus_state()
                }

                messages.append({
                    "role": "assistant",
                    "content": f"{command} [{elem['role']}-{elem['name']}]"
                })

            elif command == "rclick":
                idx = int(parts[1])
                elem = elements[idx]

                print(f"\nRight clicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0], elem['location'][1])
                x11_mouse.right_click()

                messages[1] = {
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2] = {
                    "role": "system",
                    "content": get_current_focus_state()
                }

                messages.append({
                    "role": "assistant",
                    "content": choice
                })

            elif command == "press":
                x11_keyboard.press_combo(parts[1])

                messages[1] = {
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2] = {
                    "role": "system",
                    "content": get_current_focus_state()
                }

                messages.append({
                    "role": "assistant",
                    "content": f"{command} {parts[1]}"
                })

            elif command == "type":
                x11_keyboard.type_text(parts[1])

                messages[1] = {
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2] = {
                    "role": "system",
                    "content": get_current_focus_state()
                }

                messages.append({
                    "role": "assistant",
                    "content": f"{command} {parts[1]}"
                })

            else:
                print(f"Command {command} is invalid")

        except Exception as e:
            error_msg = str(e)
            messages.append({
                "role": "system",
                "content": (
                    f"ERROR: Command '{command}' failed with: {error_msg}\n"
                    f"Available commands: env, view, open <app>, request <pid>, "
                    f"click <n>, rclick <n>, press <key>, type <text>, end\n"
                    f"If you tried to open an app, first use 'env' to see available apps."
                )
            })

# Bootstrap
messages = []

with open("model_prompt.txt") as f:
    base_prompt = f.read()

command = input("Enter your command: ")

messages.append({
    "role": "system",
    "content": base_prompt + "\n\nTask: " + command
})

messages.append({
    "role": "assistant",
    "content": "None currently"
})

messages.append({
    "role": "assistant",
    "content": "None currently"
})

print("\n\n")

interact(model, messages)
