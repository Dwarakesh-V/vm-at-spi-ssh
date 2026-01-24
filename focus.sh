#!/bin/bash

# Script to find the currently focused element using D-Bus and AT-SPI2
# Requires: at-spi2-core, gdbus (part of glib2)

set -e

# Get the accessible bus address
ATSPI_BUS=$(dbus-send --session --print-reply --dest=org.a11y.Bus \
    /org/a11y/bus org.a11y.Bus.GetAddress | \
    grep -oP '(?<=").*(?=")')

if [ -z "$ATSPI_BUS" ]; then
    echo "Error: Could not get AT-SPI bus address"
    exit 1
fi

# Export the AT-SPI bus address
export DBUS_SESSION_BUS_ADDRESS="$ATSPI_BUS"

echo "Currently focused element"
echo

# Query the registry for the focused object
FOCUS_INFO=$(gdbus call --session \
    --dest org.a11y.atspi.Registry \
    --object-path /org/a11y/atspi/accessible/root \
    --method org.a11y.atspi.Accessible.GetState 2>/dev/null || echo "")

# Get the application with focus
FOCUSED_APP=$(gdbus introspect --session \
    --dest org.a11y.atspi.Registry \
    --object-path /org/a11y/atspi/accessible 2>/dev/null | \
    grep -m1 "node" || echo "Unknown")

# Alternative approach: Query each accessible application
for app in $(busctl --user --address="$ATSPI_BUS" list | grep "^org.a11y.atspi.Application" | awk '{print $1}'); do
    # Try to get the focused component from this application
    FOCUSED=$(busctl --user --address="$ATSPI_BUS" call \
        "$app" \
        /org/a11y/atspi/accessible/root \
        org.a11y.atspi.Component GetFocusedAccessible 2>/dev/null || echo "")
    
    if [ -n "$FOCUSED" ]; then
        echo "Application: $app"
        
        # Get the name of the focused element
        NAME=$(busctl --user --address="$ATSPI_BUS" get-property \
            "$app" \
            /org/a11y/atspi/accessible/root \
            org.a11y.atspi.Accessible Name 2>/dev/null | \
            grep -oP '(?<=").*(?=")' || echo "Unknown")
        
        echo "Focused Element Name: $NAME"
        
        # Get the role
        ROLE=$(busctl --user --address="$ATSPI_BUS" get-property \
            "$app" \
            /org/a11y/atspi/accessible/root \
            org.a11y.atspi.Accessible Role 2>/dev/null || echo "Unknown")
        
        echo "Role: $ROLE"
        echo
    fi
done

# Alternative simpler method using atspi tools if available
if command -v accerciser &> /dev/null; then
    echo "Note: For better results, consider using 'accerciser' GUI tool"
fi
