"""Display protocol detection for GUI services."""

import os
from pathlib import Path


def detect_display_protocol():
    """
    Detect the display protocol (Wayland or X11).

    Returns
    -------
    str
        'wayland', 'x11', or falls back to 'x11'
    """
    if display_protocol := os.getenv("DISPLAY_PROTOCOL"):
        return display_protocol

    user_id = os.getuid()

    wayland_display = os.getenv("WAYLAND_DISPLAY")
    if wayland_display:
        wayland_socket = Path(f"/run/user/{user_id}/{wayland_display}")
        if wayland_socket.is_socket():
            return "wayland"

    display = os.getenv("DISPLAY")
    if display:
        display_num = display.split(":")[-1].split(".")[0]
        x11_socket = Path(f"/tmp/.X11-unix/X{display_num}")
        if x11_socket.is_socket():
            return "x11"

    return "x11"
