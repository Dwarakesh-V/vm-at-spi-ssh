# Custom imports
from at_spi_tree import *
from focus_listener import get_current_focus_state
from para_maker import at_pm
from llama_gen import generate_response

# Custom imports - CPP modules
import x11_mouse
import x11_keyboard

# Built-in imports
import json

# Downloaded imports
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

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

print(apps)

def generate_model_response(model,messages):
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
            max_new_tokens=16,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode only the new tokens
    response = tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[1]:], 
        skip_special_tokens=True
    )
    
    return response

def interact(model,messages,prev=None):
    """Interactive mode to explore and interact with elements"""
    
    while True:
        choice = generate_response(model,messages)
        if choice=="end":
            break
        parts = choice.split(maxsplit=2)
        command = parts[0].lower()

        # Not useful when command is open/request/end which case these variables are overridden
        app_id = int(parts[1])
        my_app = find_application_by_pid(app_id)
        elements = traverse_tree_interactive(my_app) # This is done repeatedly to ensure that UI update changes are reflected

        try:
            # Mouse actions
            if command == "click":
                idx = int(parts[2])
                elem = elements[idx]
                print(f"\nClicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
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
                    "content": choice
                })

            elif command == "rclick":
                idx = int(parts[2])
                elem = elements[idx]
                print(f"\nRight clicking: [{elem['role']}] {elem['name']}")
                x11_mouse.move_human(elem['location'][0],elem['location'][1])
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

            # Keyboard actions
            if command == "press":
                x11_keyboard.press_combo(parts[2]) # parts[2] is the key combo here
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

            elif command == 'type_text':       
                x11_keyboard.type_text(parts[2]) # parts[2] is the text to be typed here
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
                
            elif command == 'open':
                app,pid=open_application(parts[1])
                        
            else:
                print("Invalid command")
                
        except IndexError:
            print(f"Invalid element number. Valid range: 0-{len(elements)-1}")
        except ValueError:
            print("Invalid number format")
        except Exception as e:
            print(f"Error: {e}")

model_path = "./Llama-3.2-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype=torch.bfloat16,
    device_map="auto",
)

# IMPORTANT: messages[0] contains base prompt, messages[-2] contains currently focused application tree data, messages[-1] contains the focus, the messages in between contain model actions
messages = {}
