from at_spi_tree import *
from focus_listener import get_current_focus_state
import json

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

def parse_input(gen):
    gen=gen.split()
    

# focus_window_by_pid(47182)

"""
What the AI can do:
open <app> - Open an app if it is there in the list of environment variables - Creates a new app with a new pid
view - Show running apps
focus <pid> - Focus on window with pid
request <pid> - Get accessible data of process with pid
click <pid> <number> - Click on element of the app with pid at the given number
rclick <pid> <number> - Right click on element of the app with pid at the given number
press <key-combo> - Press keys in combination (ctrl+c, shift+h, enter)
type <text> - Type text
"""
