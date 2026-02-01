#!/usr/bin/env bash

sleep 3
# Get the window ID of the currently focused window
wid=$(xdotool getwindowfocus)

# Get the PID associated with that window
pid=$(xdotool getwindowpid "$wid")

echo "$pid"
