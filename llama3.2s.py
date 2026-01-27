import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load model and tokenizer from local directory
model_path = "./Llama-3.2-3B-Instruct"
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype=torch.bfloat16,
    device_map="auto",
)
print("Model loaded successfully\n")

# System prompt
system_prompt = """
You will be given assistive technology tree and the current focus and you need to determine the correct actions for the task given. You are only allowed to output ONE of these actions:
open <env_app> - Open an app that if it is there in the list of environment variables
view - Show running apps
request <pid> - Get accessible data of process with pid
click <pid> <number> - Click on element of the app with pid at the given number
rclick <pid> <number> - Right click on element of the app with pid at the given number
press <key-combo> - Press keys in combination (ctrl+c, shift+h, enter)
type <text> - Type text
For example, if you are asked to open a new browser tab and go to wikipedia.com, and the input says '10: Open a new tab', You have to do 'click 10'. Then you will recieve an update on what the current screen state is. The update will say - '12: Search with Google or enter address'. Then you have to do 'click 12'. Then the update will notify you of any changes. Then you need to do 'type wikipedia.com', and after another update, you need to do 'press enter'.
"""

# Conversation history
messages = [
    {"role": "system", "content": system_prompt}
]

def generate_response(messages):
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

while True:
    # Get user input
    user_input = input("\nYou: ").strip()
    
    # Check for exit
    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("\nSee you")
        break
    
    if not user_input:
        continue
    
    # Add user message to history
    messages.append({"role": "user", "content": user_input})
    
    # Generate response
    response = generate_response(messages) # Must be verfied and parsed.
    print("LLama:",response,type(response))
    
    # Add assistant response to history
    messages.append({"role": "assistant", "content": response})