"""Support for the widget that dumps the categories OmniGraph knows about."""
import json
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt
import omni.ui as ui

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton
from ..toolkit_utils import help_button
from .flag_manager import FlagManager

__all__ = ["ToolkitWidgetGraphContents"]


# ==============================================================================================================
class ToolkitWidgetGraphContents:
    ID = "DumpGraphContents"
    TOOLTIP = "Dump the contents of the OmniGraph, not including nodes belonging to it"
    # ----------------------------------------------------------------------
    # Checkboxes representing flags for the JSON serialization of the graph context and graph objects
    # KEY: ID of the checkbox for the flag
    # VALUE: (Label Text, Tooltip Text, Default Value)
    FLAGS = {
        "jsonFlagMaps": ("maps", "Show the context-independent attribute mapping information", False),
        "jsonFlagDetails": ("noDataDetail", "Hide the detailed attribute data", False),
        "jsonFlagLimit": ("limit", "Limit the number of output array elements to 100", False),
        "jsonFlagUnreferenced": ("unreferenced", "Show the connections between nodes in the graph", False),
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
        """Build the UI section with the functionality to dump the contents of the graph"""
        self.__button = DestructibleButton(
            "Dump Contents",
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
        """Callback executed when the Dump Contents button is clicked"""
        result = []
        if force_help:
            flags = ["help"]
        else:
            flags = [flag_manager.name for flag_manager in self.__flag_managers.values() if flag_manager.is_set]
        tooltip = f"Graph contents, filtered with flags {flags}"

        for ctx in og.get_compute_graph_contexts():
            json_string = "Not generated"
            try:
                json_string = og.OmniGraphInspector().as_json(ctx, flags=flags)
                result.append(json.loads(json_string))
            except json.JSONDecodeError as error:
                self.__set_output(f"Error decoding json for context {ctx}: {error}\n{json_string}", json_string)
                return
        self.__set_output(json.dumps(result, indent=4), tooltip)
