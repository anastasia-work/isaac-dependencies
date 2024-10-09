"""Support for the widget that dumps the categories OmniGraph knows about."""
import json
from typing import Callable

import carb
import omni.graph.core as og
import omni.graph.tools as ogt
import omni.usd

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton

__all__ = ["ToolkitWidgetOgnFromNode"]


# ==============================================================================================================
class ToolkitWidgetOgnFromNode:
    ID = "OgnFromNode"
    LABEL = "Generate .ogn From Selected Node"
    TOOLTIP = "Generate a .ogn definition that matches the contents of the selected node (one node only)"
    RESULTS_TOOLTIP = ".ogn file that describes the selected node"

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        self.__button = None
        self.__set_output = set_output_callback

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
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
        """Callback executed when the OGN From Node button is clicked"""
        try:
            selected_paths = omni.usd.get_context().get_selection().get_selected_prim_paths()
            if not selected_paths:
                text = "Select a node to generate the .ogn file for it"
            else:
                omnigraph_nodes = []
                prims = []
                graph = og.get_all_graphs()[0]
                for path in selected_paths:
                    node = graph.get_node(path)
                    if node.is_valid():
                        omnigraph_nodes.append(node)
                    else:
                        prims.append(omni.usd.get_context().get_stage().GetPrimAtPath(path))
                if not omnigraph_nodes:
                    # TODO: Most of the .ogn information could be generated from a plain prim as well
                    text = "Select an OmniGraph node to generate the .ogn file for it"
                else:
                    if len(omnigraph_nodes) > 1:
                        carb.log_warn(f"More than one node selected. Only generating the first one - {selected_paths}")
                    generated_ogn = og.generate_ogn_from_node(omnigraph_nodes[0])
                    text = json.dumps(generated_ogn, indent=4)
        except Exception as error:  # pylint: disable=broad-except
            text = str(error)
        self.__set_output(text, self.RESULTS_TOOLTIP)
