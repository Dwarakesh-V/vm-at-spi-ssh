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

print(filtered_apps)

"""
What the AI can do:
open <app> - Open an app that if it is there in the list of environment variables
view - Show running apps
focus <pid> - Focus on window with pid
request <pid> - Get accessible data of process with pid
click <pid> <number> - Click on element of the app with pid at the given number
rclick <pid> <number> - Right click on element of the app with pid at the given number
press <key-combo> - Press keys in combination (ctrl+c, shift+h, enter)
type <text> - Type text
"""
