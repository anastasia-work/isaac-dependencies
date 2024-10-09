"""Support for the widget that dumps the categories OmniGraph knows about."""
import json
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton

__all__ = ["ToolkitWidgetExtensionsUsed"]


# ==============================================================================================================
class ToolkitWidgetExtensionsUsed:
    ID = "ExtensionsUsed"
    LABEL = "Extensions Used By Nodes"
    TOOLTIP = "List all of the extensions used by OmniGraph nodes in the scene"
    RESULTS_TOOLTIP = "Extensions used by OmniGraph nodes in the scene"

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable, extension_information: og.ExtensionInformation):
        self.__button = None
        self.__extension_information = extension_information
        self.__set_output = set_output_callback

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
        ogt.destroy_property(self, "__extension_information")
        ogt.destroy_property(self, "__set_output")

    # ----------------------------------------------------------------------
    def build(self):
        """Build the UI section with the functionality to dump the list of nodes and their extensions from the scene"""
        self.__button = DestructibleButton(
            self.LABEL,
            name=self.ID,
            width=BUTTON_WIDTH,
            tooltip=self.TOOLTIP,
            clicked_fn=self.__on_click,
        )
        assert self.__button

    # --------------------------------------------------------------------------------------------------------------
    def __on_click(self):
        """Callback executed when the Extensions Used button is clicked"""
        try:
            enabled_node_types, _ = self.__extension_information.get_nodes_by_extension()
            text = json.dumps(enabled_node_types, indent=4)
        except Exception as error:  # pylint: disable=broad-except
            text = str(error)
        self.__set_output(text, self.RESULTS_TOOLTIP)
