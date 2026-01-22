import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load model and tokenizer from local directory
model_path = "./Llama-3.2-3B-Instruct"
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
print("Model loaded successfully\n")

# System prompt
system_prompt = """
You are a helpful AI assistant.
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
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
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
    print("LLama:",response)
    
    # Add assistant response to history
    messages.append({"role": "assistant", "content": response})