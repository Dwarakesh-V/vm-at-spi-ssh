#!/usr/bin/env python3

import pyatspi
import subprocess
import time
import re
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
            
            # Add state information
            state = obj.getState()
            states = []
            if state.contains(pyatspi.STATE_FOCUSED):
                states.append("FOCUSED")
            if state.contains(pyatspi.STATE_VISIBLE):
                states.append("VISIBLE")
            if state.contains(pyatspi.STATE_ENABLED):
                states.append("ENABLED")
            if states:
                result += f" [{','.join(states)}]"
            
            result += "\n"
            
            for i in range(obj.childCount):
                child = obj.getChildAtIndex(i)
                result += self.get_tree(child, indent + 1, max_depth)
        except:
            pass
        
        return result
    
    def get_state_summary(self) -> str:
        """Get a concise summary of current application state"""
        if not self.current_app:
            return "No application is currently focused."
        
        try:
            summary = f"Application: {self.current_app.name}\n"
            summary += f"Tree structure (max depth 3):\n"
            summary += self.get_tree(max_depth=3)
            
            # Find focused element
            focused = self.find_focused_element()
            if focused:
                summary += f"\nCurrently focused: [{focused.getRoleName()}] {focused.name}"
            
            return summary
        except Exception as e:
            return f"Error getting state: {e}"
    
    def find_element(self, role: str = None, name: str = None, 
                     obj=None, max_depth=10, current_depth=0) -> Optional[Any]:
        """Recursively find an element by role and/or name"""
        if obj is None:
            obj = self.current_app if self.current_app else self.desktop
        
        if current_depth > max_depth:
            return None
        
        try:
            role_match = role is None or obj.getRoleName().lower() == role.lower()
            name_match = name is None or (name.lower() in obj.name.lower() if obj.name else False)
            
            if role_match and name_match:
                return obj
            
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
            element = self.find_element(name=target)
            if not element:
                return False
            
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
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Launch error: {e}")
            return False


class ActionParser:
    """Parse AI model output into executable actions"""
    
    @staticmethod
    def parse_single_action(text: str) -> Optional[Dict[str, Any]]:
        """Extract the FIRST action call from model output"""
        # Pattern: function_name('arg1', 'arg2', ...)
        pattern = r"(\w+)\((.*?)\)"
        match = re.search(pattern, text)
        
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            
            args = []
            if args_str.strip():
                for arg in re.findall(r"'([^']*)'|\"([^\"]*)\"|([^,]+)", args_str):
                    arg_value = next(x for x in arg if x)
                    args.append(arg_value.strip())
            
            return {
                "function": func_name,
                "args": args
            }
        
        return None


class AISystemController:
    """Main controller integrating AI model with system automation"""
    
    def __init__(self, model_path: str, env_apps: List[str]):
        print("Initializing AI System Controller...")
        
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        print("Model loaded successfully")
        
        self.atspi = ATSPIController()
        self.terminal = TerminalController()
        self.parser = ActionParser()
        self.env_apps = env_apps
        
        # Internal thinking conversation (for step-by-step reasoning)
        self.internal_messages = []
        
        # User conversation
        self.user_messages = []
        
        self.current_task = None
        self.task_complete = False
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for the AI model"""
        return f"""You are an AI system automation assistant with iterative control. You observe the system state after EACH action and decide the next step.

Available functions:
- run('command'): Execute terminal command
- launch('app_name'): Launch application (available: {', '.join(self.env_apps)})
- click('element_name'): Click GUI element
- type('text'): Type into focused element
- key('key_combination'): Send keyboard shortcut
- wait(seconds): Wait
- observe(): Get current application state
- task_complete(): Signal task is finished

CRITICAL INSTRUCTIONS:
1. You work ONE action at a time
2. After EACH action, you'll see the current system state
3. You must reason about what you observe before taking the next action
4. Use observe() frequently to check application state
5. Think step-by-step in your reasoning
6. Only call task_complete() when the user's request is fully satisfied

Response format:
THOUGHT: [Your reasoning about current state and what to do next]
ACTION: function_name('arg1', 'arg2')

Example flow for "Open calculator and compute 5+3":
THOUGHT: I need to launch the calculator application first
ACTION: launch('qalculate-gtk')

[System shows calculator opened]
THOUGHT: Calculator is now open. I should check what buttons are available
ACTION: observe()

[System shows calculator interface with number buttons]
THOUGHT: I can see the calculator interface. I need to click 5, then +, then 3, then =
ACTION: click('5')

[System shows 5 entered]
THOUGHT: 5 is entered, now I need to click the plus button
ACTION: click('+')

... and so on until:
THOUGHT: Result shows 8, which is correct. Task is complete.
ACTION: task_complete()

Always output THOUGHT and ACTION on separate lines."""
    
    def generate_next_action(self, state_info: str = "") -> tuple[str, Optional[Dict[str, Any]]]:
        """Generate the next action based on current state"""
        # Build context message
        if state_info:
            context_msg = f"CURRENT SYSTEM STATE:\n{state_info}\n\nBased on this state, what is your next action?"
        else:
            context_msg = f"Current task: {self.current_task}\n\nWhat is your first action?"
        
        self.internal_messages.append({"role": "user", "content": context_msg})
        
        # Generate response
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": self.get_system_prompt()}] + self.internal_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        self.internal_messages.append({"role": "assistant", "content": response})
        
        # Parse action
        action = self.parser.parse_single_action(response)
        
        return response, action
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action and return result with state"""
        func = action["function"]
        args = action["args"]
        
        print(f"  → Executing: {func}({', '.join(repr(a) for a in args)})")
        
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
                time.sleep(0.5)  # Wait for UI to update
                return {"success": success}
            
            elif func == "type":
                text = args[0].encode().decode('unicode_escape')
                success = self.atspi.type_text(text)
                return {"success": success}
            
            elif func == "key":
                result = self.terminal.run_command(f"xdotool key {args[0]}")
                time.sleep(0.3)
                return result
            
            elif func == "wait":
                time.sleep(float(args[0]))
                return {"success": True}
            
            elif func == "observe":
                state = self.atspi.get_state_summary()
                print(f"    State:\n{state[:300]}...")
                return {"success": True, "state": state}
            
            elif func == "task_complete":
                self.task_complete = True
                return {"success": True, "message": "Task marked as complete"}
            
            else:
                return {"success": False, "error": f"Unknown function: {func}"}
                
        except Exception as e:
            print(f"    Error: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_task_iteratively(self, task: str, max_iterations: int = 30):
        """Execute a task with iterative state checking"""
        self.current_task = task
        self.task_complete = False
        self.internal_messages = []
        
        print(f"\n{'='*60}")
        print(f"TASK: {task}")
        print(f"{'='*60}\n")
        
        state_info = ""
        iteration = 0
        
        while not self.task_complete and iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # AI generates next action
            print("AI is thinking...")
            response, action = self.generate_next_action(state_info)
            
            # Show AI's thought process
            print(f"\n{response}\n")
            
            if not action:
                print("⚠ No valid action found in response")
                break
            
            if action["function"] == "task_complete":
                self.task_complete = True
                print("✓ Task completed!")
                break
            
            # Execute action
            result = self.execute_action(action)
            
            # Get updated state
            if action["function"] == "observe":
                state_info = result.get("state", "")
            else:
                # Auto-observe after actions that change state
                if action["function"] in ["launch", "click", "type", "key"]:
                    time.sleep(0.5)
                    state_info = self.atspi.get_state_summary()
                else:
                    state_info = f"Action result: {result}"
            
            # Small delay between iterations
            time.sleep(0.3)
        
        if iteration >= max_iterations:
            print(f"\n⚠ Reached maximum iterations ({max_iterations})")
        
        print(f"\n{'='*60}")
        print(f"Task execution finished")
        print(f"{'='*60}\n")
    
    def run(self):
        """Main interaction loop"""
        print("\n" + "="*60)
        print("Dynamic AI System Controller Active")
        print("="*60)
        print("The AI will observe state after each action and adapt.")
        print("Type your requests, or 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nShutting down...")
                    break
                
                if not user_input:
                    continue
                
                # Execute task iteratively
                self.execute_task_iteratively(user_input)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Entry point"""
    env_apps = ["qalculate-gtk", "xfce4-terminal", "python3", "gcc", "g++"]
    model_path = "Llama-3.2-3B-Instruct"
    
    controller = AISystemController(model_path, env_apps)
    controller.run()


if __name__ == "__main__":
    main()