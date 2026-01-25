#!/bin/bash

# Diagnostic script for D-Bus and AT-SPI2 accessibility setup

echo "D-Bus environment check"
echo

# Check if D-Bus session bus is running
echo "1. D-Bus Session Bus Address:"
echo "   $DBUS_SESSION_BUS_ADDRESS"
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    echo "   WARNING: DBUS_SESSION_BUS_ADDRESS is not set!"
else
    echo "   * Session bus address is set"
fi
echo

# Check if D-Bus daemon is running
echo "2. D-Bus Daemon Process:"
if pgrep -x dbus-daemon > /dev/null; then
    echo "   * dbus-daemon is running"
    pgrep -a dbus-daemon | head -3
else
    echo "   ! dbus-daemon is NOT running"
fi
echo

# Test D-Bus connectivity
echo "3. D-Bus Session Bus Connection:"
if dbus-send --session --print-reply --dest=org.freedesktop.DBus \
    /org/freedesktop/DBus org.freedesktop.DBus.ListNames > /dev/null 2>&1; then
    echo "   * Can connect to session bus"
else
    echo "   ! Cannot connect to session bus"
fi
echo

echo "Accessibility check"
echo

# Check if at-spi2 packages are installed
echo "4. AT-SPI2 packages availability"
for pkg in at-spi2-core at-spi2-atk libatk-adaptor; do
    if dpkg -l | grep -q "^ii.*$pkg"; then
        echo "   * $pkg is installed (dpkg)"
    else
        echo "   ! $pkg is NOT installed (dpkg)"
    fi
done
echo

# Check if at-spi-bus-launcher is running
echo "5. AT-SPI Bus Launcher:"
if pgrep -x at-spi-bus-launcher > /dev/null || pgrep -f at-spi-bus-launcher > /dev/null; then
    echo "   * at-spi-bus-launcher is running"
    pgrep -a at-spi-bus-launcher
else
    echo "   ! at-spi-bus-launcher is NOT running"
fi
echo

# Check AT-SPI registry
echo "6. AT-SPI Registry Service:"
if dbus-send --session --print-reply --dest=org.a11y.Bus \
    /org/a11y/bus org.a11y.Bus.GetAddress > /dev/null 2>&1; then
    echo "   * AT-SPI registry is accessible"
    echo "   AT-SPI Bus Address:"
    dbus-send --session --print-reply --dest=org.a11y.Bus \
        /org/a11y/bus org.a11y.Bus.GetAddress 2>&1 | grep string || echo "   (Could not retrieve)"
else
    echo "   ! AT-SPI registry is NOT accessible"
    echo "   This is the main issue preventing the script from working"
fi
echo

# List accessibility-related D-Bus services
echo "7. Accessibility D-Bus Services:"
dbus-send --session --print-reply --dest=org.freedesktop.DBus \
    /org/freedesktop/DBus org.freedesktop.DBus.ListNames 2>/dev/null | \
    grep -E "a11y|atspi" || echo "   No AT-SPI services found"
echo

# Check desktop environment accessibility settings
echo "8. Desktop Environment Accessibility:"
if command -v gsettings &> /dev/null; then
    TOOLKIT_ACCESS=$(gsettings get org.gnome.desktop.interface toolkit-accessibility 2>/dev/null || echo "not set")
    echo "   GNOME toolkit-accessibility: $TOOLKIT_ACCESS"
    if [ "$TOOLKIT_ACCESS" = "false" ]; then
        echo "   Accessibility is DISABLED. Enable with:"
        echo "   gsettings set org.gnome.desktop.interface toolkit-accessibility true"
    fi
else
    echo "   gsettings not available (not GNOME/GTK-based?)"
fi
echo

# Check environment variables
echo "9. Accessibility Environment Variables:"
env | grep -E "GTK_MODULES|GNOME_ACCESSIBILITY|NO_AT_BRIDGE" || echo "   None set"
echo
