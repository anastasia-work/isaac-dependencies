"""Handler for the debug output frame of the OmniGraph toolkit"""
import asyncio
import sys
from contextlib import suppress
from typing import Optional

import carb
import omni.graph.core as og
import omni.graph.tools as ogt
import omni.ui as ui

from ..style import VSTACK_ARGS  # noqa: PLE0402
from ..utils import DestructibleButton  # noqa: PLE0402


# ======================================================================
class ToolkitFrameOutput:
    """Class containing all of the functionality for the debug output frame in the OmniGraph Toolkit Window

    Public Functions:
        build() : Construct the frame
        set_debug_output(output, tooltip): Define the text contents of the frame

    Layout of the class constants is stacked:
        Constants
        Initialize/Destroy
        Public Functions
        Build Functions
        Callback Functions
    """

    # ----------------------------------------------------------------------
    # Frame information
    ID = "FrameOutput"
    TITLE = "Debug Output"

    # ----------------------------------------------------------------------
    # Maximum number of lines to show in the debug preview pane (limited to avoid overflow crash)
    DEBUG_PREVIEW_LINE_LIMIT = 10000

    # ----------------------------------------------------------------------
    # IDs for widgets
    ID_DEBUG_LABEL = "DebugOutputLabel"
    ID_DEBUG_CONTENTS = "DebugOutput"
    ID_TEXT_CLIPPED = "Clipped"

    # ----------------------------------------------------------------------
    # Tooltip for the frame
    TOOLTIP = "View the output from the debugging functions"

    # --------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """Set up the frame elements - use build() for constructing the frame"""
        # Dictionary of widgets in the window
        self.__widgets = {}
        # Output text from various functions to show in an auxiliary frame
        self.__debug_output = "No output available yet"
        self.__debug_tooltip = self.TOOLTIP
        # Task for the delayed fade out of the clipboard message
        self.__delayed_fade_task = None

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        """Destroy the debug output frame"""
        with suppress(AttributeError, KeyError):
            self.__widgets[self.ID].set_build_fn(None)
        with suppress(AttributeError):
            self.__delayed_fade_task.cancel()

        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__widgets")

    # ----------------------------------------------------------------------
    def build(self):
        """Construct the collapsable frame containing the debug output contents"""
        self.__widgets[self.ID] = ui.CollapsableFrame(title=self.TITLE, collapsed=False)
        self.__widgets[self.ID].set_build_fn(self.__rebuild_output_display_frame)

    # ----------------------------------------------------------------------
    def set_debug_output(self, new_output: str, new_tooltip: Optional[str]):
        """Manually set new output data and update it"""
        self.__debug_output = new_output
        self.__debug_tooltip = new_tooltip if new_tooltip else self.TOOLTIP
        self.__on_debug_output_changed()
        sys.stdout.write(self.__debug_output)

    # ----------------------------------------------------------------------
    def __rebuild_output_display_frame(self):
        """Construct and populate the display area for output from the serialization functions"""
        with self.__widgets[self.ID]:
            with ui.VStack(**VSTACK_ARGS):
                self.__widgets[self.ID_DEBUG_LABEL] = ui.Label(
                    "Available in the Python variable omni.graph.core.DEBUG_DATA - (RMB to copy contents to clipboard)",
                    style_type_name_override="Info",
                )
                with ui.ZStack():
                    self.__widgets[self.ID_DEBUG_CONTENTS] = ui.Label(
                        self.ID_DEBUG_CONTENTS, style_type_name_override="Code"
                    )
                    self.__widgets[self.ID_TEXT_CLIPPED] = DestructibleButton(
                        " ",
                        height=ui.Percent(100),
                        width=ui.Percent(100),
                        alignment=ui.Alignment.CENTER_TOP,
                        style={"background_color": 0x00000000, "color": 0xFF00FFFF},
                        mouse_pressed_fn=self.__on_copy_debug_output_to_clipboard,
                    )

        self.__on_debug_output_changed()

    # --------------------------------------------------------------------------------------------------------------
    def __fade_clip_message(self):
        """Enable the clipboard message, then set a timer to remove it after 3 seconds."""

        async def __delayed_fade(self):
            await asyncio.sleep(1.0)
            color = 0xFF00FFFF
            for _ in range(31):
                color -= 0x08000000
                self.__widgets[self.ID_TEXT_CLIPPED].set_style({"background_color": 0x00000000, "color": color})
                await asyncio.sleep(0.02)
            with suppress(KeyError):
                self.__widgets[self.ID_TEXT_CLIPPED].set_style({"background_color": 0x00000000, "color": 0xFF00FFFF})
                self.__widgets[self.ID_TEXT_CLIPPED].text = " "

        with suppress(Exception):
            self.__delayed_fade_task.cancel()

        carb.log_info("Copied debug output to the clipboard")
        self.__widgets[self.ID_TEXT_CLIPPED].text = "Debug Output Clipped"
        self.__delayed_fade_task = asyncio.ensure_future(__delayed_fade(self))

    # ----------------------------------------------------------------------
    def __on_debug_output_changed(self):
        """Callback executed whenever any data affecting the debug output has changed"""

        def find_max_line_end(full_string: str):
            index = -1
            for _ in range(self.DEBUG_PREVIEW_LINE_LIMIT + 1):
                index = full_string.find("\n", index + 1)
                if index < 0:
                    break
            return index

        with suppress(KeyError):
            if self.__debug_output and self.__debug_output.count("\n") > self.DEBUG_PREVIEW_LINE_LIMIT:
                last_line_ends = find_max_line_end(self.__debug_output)
                if last_line_ends > 0:
                    self.__widgets[self.ID_DEBUG_CONTENTS].text = self.__debug_output[: last_line_ends + 1] + "...\n"
            else:
                self.__widgets[self.ID_DEBUG_CONTENTS].text = self.__debug_output
            og.DEBUG_DATA = self.__debug_output
            self.__widgets[self.ID_DEBUG_LABEL].set_tooltip(self.__debug_tooltip)

    # ----------------------------------------------------------------------
    def __on_copy_debug_output_to_clipboard(self, x, y, button, modifier):
        """Callback executed when right-clicking on the output location"""
        if button != 1:
            return
        try:
            import omni.kit.clipboard

            omni.kit.clipboard.copy(self.__debug_output)
            self.__fade_clip_message()
        except ImportError:
            carb.log_warn("Could not import omni.kit.clipboard.")
