# Custom imports
from at_spi_tree import *
from focus_listener import get_current_focus_state
from para_maker import at_pm

# Custom imports - CPP modules
import x11_mouse
import x11_keyboard

# Downloaded imports
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def generate_model_response(model,tokenizer,messages):
    """Generate a response from the model"""
    # Apply chat template
    prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=True,          # Enable sampling
        temperature=0.4,         # Add randomness
        top_p=0.9,              # Nucleus sampling
        pad_token_id=tokenizer.eos_token_id
    )
    
    # Decode only the new tokens
    response = tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[1]:], 
        skip_special_tokens=True
    )
    
    print(response)
    return response

def interact(model,tokenizer,messages):
    """Interactive mode to explore and interact with elements"""
    
    while True:
        choice = generate_model_response(model,tokenizer,messages)
        parts = choice.split(maxsplit=1)
        command = parts[0].lower()
        if command=="end":
            print(f"From model: {parts[1]}")
        
        app_id = get_focused_window_pid()
        my_app = find_application_by_pid(app_id)
        elements = traverse_tree_interactive(my_app) # This is done repeatedly to ensure that UI update changes are reflected, and indexing errors are avoided

        try:
            if command == "env": # VIEW ENVIRONMENTAL APPS
                with open("env.json") as f:
                    allowed_applications = json.load(f)

                res=""
                for app in allowed_applications["apps"]:
                    res+=app+"\n"
                print(res)
                messages.append({
                    "role": "assistant",
                    "content": res
                })

            elif command == "view": # VIEW APPLICATIONS
                messages.append({
                    "role": "assistant",
                    "content": f"view:\n{filter_applications(list_applications(False))}"
                })

            elif command == "open": # OPEN AN APPLICATION
                app_pid=open_application(parts[1])
                focus_window_by_pid(app_pid)
                messages.append({
                    "role": "assistant",
                    "content": f"Opened application. PID: {app_pid}"
                })

            elif command == "run": # RUN TERMINAL COMMAND AND RETRIEVE OUTPUT
                output = run_terminal_command(parts[1])
                messages[1]={
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2]={
                    "role": "system",
                    "content": get_current_focus_state()
                }
                messages.append({
                    "role": "user",
                    "content": f"Command output\n{output}"
                })

            elif command == "focus": # FOCUS ON APPLICATION
                idx=int(parts[1])
                focus_window_by_pid(idx)
                messages.append({
                    "role": "user",
                    "content": f"Window focused: {idx}"
                })

            elif command == "request":
                user_input = input("From model: "+parts[1])
                messages.append({
                    "role": "user",
                    "content": f"From user: {user_input}"
                })

            # Mouse actions
            elif command == "click": # LEFT CLICK
                idx = int(parts[1])
                elem = elements[idx]
                print(f"\nClicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
                x11_mouse.click()
                messages[1]={
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2]={
                    "role": "system",
                    "content": get_current_focus_state()
                }
                messages.append({
                    "role": "assistant",
                    "content": f"{command} [{elem['role']}-{elem['name']}]"
                })

            elif command == "rclick": # RIGHT CLICK
                idx = int(parts[1])
                elem = elements[idx]
                print(f"\nRight clicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
                x11_mouse.right_click()
                messages[1]={
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2]={
                    "role": "system",
                    "content": get_current_focus_state()
                }
                messages.append({
                    "role": "assistant",
                    "content": choice
                })

            # Keyboard actions
            elif command == "press": # KEY PRESS
                x11_keyboard.press_combo(parts[1]) # parts[1] is the key combo here
                messages[1]={
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2]={
                    "role": "system",
                    "content": get_current_focus_state()
                }
                messages.append({
                    "role": "assistant",
                    "content": f"{command} {parts[1]}"
                })

            elif command == 'type': # TYPE TEXT
                x11_keyboard.type_text(parts[1]) # parts[1] is the text to be typed here
                messages[1]={
                    "role": "system",
                    "content": at_pm(elements)
                }
                messages[2]={
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
                "content": f"ERROR: Command '{command}' failed with: {error_msg}\n"
                        f"Available commands: env, view, open <app>, request <pid>, click <n>, "
                        f"rclick <n>, press <key>, type <text>, end\n"
                        f"If you tried to open an app, first use 'env' to see available apps."
            })

model_path = "./Llama-3.2-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype=torch.bfloat16,
    device_map="auto",
)

# IMPORTANT: messages[0] contains base prompt, messages[-2] contains currently focused application tree data, messages[-1] contains the focus, the messages in between contain model actions
messages = []
with open("model_prompt.txt") as f:
    base_prompt = f.read()
command = input("Enter your command: ")
messages.append({
    "role": "system",
    "content": base_prompt+"\n\nTask: "+command
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
interact(model,tokenizer,messages)
