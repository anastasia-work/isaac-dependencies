"""Support for the widget that dumps the categories OmniGraph knows about."""
import json
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton
from ..toolkit_utils import help_button

__all__ = ["ToolkitWidgetCategories"]


# ==============================================================================================================
class ToolkitWidgetCategories:
    ID = "DumpCategories"
    TOOLTIP = "Dump out the list of recognized node type categories"

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        self.__button = None
        self.__help_button = None
        self.__set_output = set_output_callback

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
        ogt.destroy_property(self, "__help_button")
        ogt.destroy_property(self, "__set_output")

    # ----------------------------------------------------------------------
    def build(self):
        """Build the UI section with the functionality to dump the node type categories"""
        self.__button = DestructibleButton(
            "Dump Categories",
            name=self.ID,
            width=BUTTON_WIDTH,
            tooltip=self.TOOLTIP,
            clicked_fn=self.__on_click,
        )
        assert self.__button
        self.__help_button = help_button(lambda x, y, b, m: self.__on_click(force_help=True))
        assert self.__help_button

    # --------------------------------------------------------------------------------------------------------------
    def __on_click(self, force_help: bool = False):
        """Callback executed when the Dump Categories button is clicked"""
        if force_help:
            text = json.dumps({"help": "Dump the current list of recognized node type categories"}, indent=4)
        else:
            categories = {}
            interface = og.get_node_categories_interface()
            for category_name, category_description in interface.get_all_categories().items():
                categories[category_name] = category_description
            text = json.dumps({"nodeTypeCategories": categories}, indent=4)
        tooltip = "Node Type Categories"
        self.__set_output(text, tooltip)
