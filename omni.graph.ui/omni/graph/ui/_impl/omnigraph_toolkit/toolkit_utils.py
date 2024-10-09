"""An assortment of utilities shared by various pieces of the toolkit"""
import os

import omni.ui as ui

from ..utils import DestructibleImage, get_icons_dir

__all__ = ["help_button"]


# ----------------------------------------------------------------------
def help_button(callback) -> ui.Image:
    """Build the standard help button with a defined callback when the mouse button is pressed"""
    with ui.HStack(spacing=10):
        button = DestructibleImage(
            os.path.join(get_icons_dir(), "help.svg"),
            width=20,
            height=20,
            mouse_pressed_fn=callback,
            tooltip="Show the help information for the inspector on the object",
        )
    return button
