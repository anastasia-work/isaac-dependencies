"""Support for the widget that dumps the categories OmniGraph knows about."""
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt
import omni.ui as ui

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton
from ..toolkit_utils import help_button
from .flag_manager import FlagManager

__all__ = ["ToolkitWidgetGraphRegistry"]


# ==============================================================================================================
class ToolkitWidgetGraphRegistry:
    ID = "DumpGraphRegistry"
    TOOLTIP = "Dump the contents of the current OmniGraph registry to the console"
    FLAGS = {
        "jsonFlagAttributes": ("attributes", "Show the attributes on registered node types", False),
        "jsonFlagDetails": ("nodeTypes", "Show the details of the registered node types", False),
    }

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        self.__button = None
        self.__flag_managers = {}
        self.__help_button = None
        self.__set_output = set_output_callback

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
        ogt.destroy_property(self, "__flag_managers")
        ogt.destroy_property(self, "__help_button")
        ogt.destroy_property(self, "__set_output")

    # ----------------------------------------------------------------------
    def build(self):
        """Build the UI section with the functionality to dump the graph registry"""
        self.__button = DestructibleButton(
            "Dump Registry",
            name=self.ID,
            width=BUTTON_WIDTH,
            tooltip=self.TOOLTIP,
            clicked_fn=self.__on_click,
        )
        assert self.__button

        self.__help_button = help_button(lambda x, y, b, m: self.__on_click(force_help=True))
        assert self.__help_button

        for checkbox_id, (flag, tooltip, default_value) in self.FLAGS.items():
            self.__flag_managers[checkbox_id] = FlagManager(checkbox_id, flag, tooltip, default_value)
            with ui.HStack(spacing=5):
                self.__flag_managers[checkbox_id].checkbox()

    # --------------------------------------------------------------------------------------------------------------
    def __on_click(self, force_help: bool = False):
        """Callback executed when the Dump Registry button is clicked"""
        if force_help:
            flags = ["help"]
        else:
            flags = [flag_manager.name for flag_manager in self.__flag_managers.values() if flag_manager.is_set]
        tooltip = f"OmniGraph registry contents, filtered with flags {flags}"

        text = og.OmniGraphInspector().as_json(og.GraphRegistry(), flags=flags)
        self.__set_output(text, tooltip)
