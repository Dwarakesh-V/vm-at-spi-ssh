#!/usr/bin/env python3

import pyatspi
import subprocess
import time
import re
import json
from typing import Optional, Dict, List, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class ATSPIController:
    """Handles AT-SPI interactions with GUI applications"""
    
    def __init__(self):
        self.desktop = pyatspi.Registry.getDesktop(0)
        self.current_app = None
        
    def find_app(self, app_name: str) -> Optional[Any]:
        """Find an application by name"""
        for i in range(self.desktop.childCount):
            app = self.desktop.getChildAtIndex(i)
            if app_name.lower() in app.name.lower():
                self.current_app = app
                return app
        return None
    
    def get_tree(self, obj=None, indent=0, max_depth=5) -> str:
        """Get AT-SPI tree structure as string"""
        if obj is None:
            obj = self.current_app if self.current_app else self.desktop
        
        if indent > max_depth:
            return ""
        
        result = "  " * indent
        try:
            result += f"[{obj.getRoleName()}] {obj.name}"
            if obj.description:
                result += f" ({obj.description})"
            result += "\n"
            
            for i in range(obj.childCount):
                child = obj.getChildAtIndex(i)
                result += self.get_tree(child, indent + 1, max_depth)
        except:
            pass
        
        return result
    
    def find_element(self, role: str = None, name: str = None, 
                     obj=None, max_depth=10, current_depth=0) -> Optional[Any]:
        """Recursively find an element by role and/or name"""
        if obj is None:
            obj = self.current_app if self.current_app else self.desktop
        
        if current_depth > max_depth:
            return None
        
        try:
            # Check current object
            role_match = role is None or obj.getRoleName().lower() == role.lower()
            name_match = name is None or (name.lower() in obj.name.lower() if obj.name else False)
            
            if role_match and name_match:
                return obj
            
            # Search children
            for i in range(obj.childCount):
                child = obj.getChildAtIndex(i)
                result = self.find_element(role, name, child, max_depth, current_depth + 1)
                if result:
                    return result
        except:
            pass
        
        return None
    
    def click(self, target: str) -> bool:
        """Click on an element (button, menu item, etc)"""
        try:
            # Try to find as button first
            element = self.find_element(name=target)
            if not element:
                return False
            
            # Try to click
            action = element.queryAction()
            for i in range(action.nActions):
                if action.getName(i) in ['click', 'press', 'activate']:
                    action.doAction(i)
                    return True
            
            return False
        except Exception as e:
            print(f"Click error: {e}")
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text into focused element"""
        try:
            # Find focused element
            focused = self.find_focused_element()
            if not focused:
                return False
            
            editable = focused.queryEditableText()
            editable.insertText(0, text, len(text))
            return True
        except Exception as e:
            print(f"Type error: {e}")
            return False
    
    def find_focused_element(self, obj=None) -> Optional[Any]:
        """Find the currently focused element"""
        if obj is None:
            obj = self.current_app if self.current_app else self.desktop
        
        try:
            state = obj.getState()
            if state.contains(pyatspi.STATE_FOCUSED):
                return obj
            
            for i in range(obj.childCount):
                child = obj.getChildAtIndex(i)
                result = self.find_focused_element(child)
                if result:
                    return result
        except:
            pass
        
        return None


class TerminalController:
    """Handles terminal command execution"""
    
    def __init__(self):
        self.process = None
        self.terminal_apps = ["xfce4-terminal", "gnome-terminal", "konsole"]
    
    def run_command(self, cmd: str, wait: bool = True, timeout: int = 30) -> Dict[str, Any]:
        """Execute a shell command"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout if wait else None
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def launch_app(self, app_name: str) -> bool:
        """Launch an application"""
        try:
            subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)  # Wait for app to start
            return True
        except Exception as e:
            print(f"Launch error: {e}")
            return False


class ActionParser:
    """Parse AI model output into executable actions"""
    
    @staticmethod
    def parse_actions(text: str) -> List[Dict[str, Any]]:
        """Extract action calls from model output"""
        actions = []
        
        # Pattern: function_name('arg1', 'arg2', ...)
        pattern = r"(\w+)\((.*?)\)"
        matches = re.finditer(pattern, text)
        
        for match in matches:
            func_name = match.group(1)
            args_str = match.group(2)
            
            # Parse arguments
            args = []
            if args_str.strip():
                # Simple parsing (handles string args with quotes)
                for arg in re.findall(r"'([^']*)'|\"([^\"]*)\"|([^,]+)", args_str):
                    arg_value = next(x for x in arg if x)
                    args.append(arg_value.strip())
            
            actions.append({
                "function": func_name,
                "args": args
            })
        
        return actions


class AISystemController:
    """Main controller integrating AI model with system automation"""
    
    def __init__(self, model_path: str, env_apps: List[str]):
        print("Initializing AI System Controller...")
        
        # Load AI model
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        print("Model loaded successfully")
        
        # Initialize controllers
        self.atspi = ATSPIController()
        self.terminal = TerminalController()
        self.parser = ActionParser()
        self.env_apps = env_apps
        
        # Conversation history
        self.messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Action history for context
        self.action_history = []
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for the AI model"""
        return f"""You are an AI system automation assistant. You can control the computer through function calls.

Available functions:
- run('command'): Execute a terminal command (e.g., run('touch file.c'), run('ls -la'))
- launch('app_name'): Launch an application (available: {', '.join(self.env_apps)})
- click('element_name'): Click on a GUI element by name
- type('text'): Type text into the focused element
- key('key_combination'): Send keyboard shortcut (e.g., key('ctrl+s'))
- get_tree(): Get the current application's AT-SPI tree structure
- wait(seconds): Wait for specified seconds

Guidelines:
1. Always respond with function calls on separate lines
2. For file editing: use nano or text editors via GUI
3. Chain commands logically (e.g., touch file, then edit it)
4. Use wait() between GUI actions to let apps respond
5. For nano: type content, then key('ctrl+o'), key('enter'), key('ctrl+x')
6. Be explicit and clear with each action

Example for "Write a C file":
launch('xfce4-terminal')
wait(2)
run('touch hello.c')
run('nano hello.c')
wait(1)
type('#include <stdio.h>\\nint main() {{\\n    printf("Hello\\\\n");\\n    return 0;\\n}}')
key('ctrl+o')
wait(0.5)
key('enter')
key('ctrl+x')

Only output function calls, no explanations unless asked."""
    
    def generate_response(self, user_input: str) -> str:
        """Generate AI response for user input"""
        # Add user message
        self.messages.append({"role": "user", "content": user_input})
        
        # Generate
        prompt = self.tokenizer.apply_chat_template(
            self.messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        # Add to history
        self.messages.append({"role": "assistant", "content": response})
        
        return response
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        func = action["function"]
        args = action["args"]
        
        print(f"  Executing: {func}({', '.join(repr(a) for a in args)})")
        
        try:
            if func == "run":
                result = self.terminal.run_command(args[0])
                if result.get("stdout"):
                    print(f"    Output: {result['stdout'][:200]}")
                return result
            
            elif func == "launch":
                success = self.terminal.launch_app(args[0])
                if success:
                    time.sleep(2)
                    self.atspi.find_app(args[0])
                return {"success": success}
            
            elif func == "click":
                success = self.atspi.click(args[0])
                return {"success": success}
            
            elif func == "type":
                # Handle escape sequences
                text = args[0].encode().decode('unicode_escape')
                success = self.atspi.type_text(text)
                return {"success": success}
            
            elif func == "key":
                # Use xdotool for keyboard shortcuts
                result = self.terminal.run_command(f"xdotool key {args[0]}")
                return result
            
            elif func == "wait":
                time.sleep(float(args[0]))
                return {"success": True}
            
            elif func == "get_tree":
                tree = self.atspi.get_tree()
                print(f"    Tree:\n{tree[:500]}")
                return {"success": True, "tree": tree}
            
            else:
                return {"success": False, "error": f"Unknown function: {func}"}
                
        except Exception as e:
            print(f"    Error: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse and execute all actions in the response"""
        actions = self.parser.parse_actions(response)
        
        if not actions:
            print("No actions found in response")
            return []
        
        print(f"\nExecuting {len(actions)} action(s):")
        results = []
        
        for action in actions:
            result = self.execute_action(action)
            results.append(result)
            
            # Record in history
            self.action_history.append({
                "action": action,
                "result": result
            })
            
            # Small delay between actions
            time.sleep(0.3)
        
        return results
    
    def run(self):
        """Main interaction loop"""
        print("\n" + "="*60)
        print("AI System Controller Active")
        print("="*60)
        print("Type your requests, and I'll automate them.")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nShutting down...")
                    break
                
                if not user_input:
                    continue
                
                # Generate AI response
                print("\nAI is thinking...")
                response = self.generate_response(user_input)
                print(f"\nAI Response:\n{response}\n")
                
                # Execute actions
                results = self.execute_response(response)
                
                # Summary
                success_count = sum(1 for r in results if r.get("success"))
                print(f"\n✓ Completed {success_count}/{len(results)} actions successfully")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"\nError: {e}")


def main():
    """Entry point"""
    env_apps = ["qalculate-gtk", "xfce4-terminal", "python3", "gcc", "g++"]
    model_path = "./Llama-3.2-3B-Instruct"
    
    controller = AISystemController(model_path, env_apps)
    controller.run()


if __name__ == "__main__":
    main()