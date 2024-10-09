"""Handler for the scene manipulation frame of the OmniGraph toolkit"""
from contextlib import suppress
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt
import omni.ui as ui

from ..style import VSTACK_ARGS
from .widgets.extensions_all import ToolkitWidgetExtensionsAll
from .widgets.extensions_missing import ToolkitWidgetExtensionsMissing
from .widgets.extensions_used import ToolkitWidgetExtensionsUsed
from .widgets.ogn_from_node import ToolkitWidgetOgnFromNode


# ======================================================================
class ToolkitFrameScene:
    """Class containing all of the functionality for the scene manipulation frame of the OmniGraph Toolkit Window

    Public Functions:
        build() : Construct the frame
    """

    # ----------------------------------------------------------------------
    # Frame information
    ID = "FrameScene"
    TITLE = "OmniGraph Scene Manipulation"

    # ----------------------------------------------------------------------
    # Layout constants specific to this frame
    FLAG_COLUMN_WIDTH = 80

    # ----------------------------------------------------------------------
    # Labels for widgets
    LABEL_SCENE = "Scene"

    # --------------------------------------------------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        """Set up the frame elements - use build() for constructing the frame"""
        # Dictionary of widgets in the window
        self.__widgets = {}
        # Dictionary of widget managers in the window
        self.__widget_managers = []
        # Callback to use for reporting new output
        self.__set_output = set_output_callback
        # Manager for the per-extension information
        self.__extension_information = og.ExtensionInformation()

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        """Destroy the frame"""
        with suppress(AttributeError, KeyError):
            self.__widgets[self.ID].set_build_fn(None)

        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__widget_managers")
        ogt.destroy_property(self, "__set_output")

    # ----------------------------------------------------------------------
    def build(self):
        """Construct the collapsable frame containing the inspection operations"""
        self.__widgets[self.ID] = ui.CollapsableFrame(title=self.TITLE, collapsed=False)
        self.__widgets[self.ID].set_build_fn(self.__rebuild_scene_frame)

    # ----------------------------------------------------------------------
    def __rebuild_scene_frame(self):
        """Construct the widgets for running inspection operations"""
        self.__widget_managers.append(ToolkitWidgetExtensionsUsed(self.__set_output, self.__extension_information))
        self.__widget_managers.append(ToolkitWidgetExtensionsMissing(self.__set_output, self.__extension_information))
        self.__widget_managers.append(ToolkitWidgetExtensionsAll(self.__set_output, self.__extension_information))
        self.__widget_managers.append(ToolkitWidgetOgnFromNode(self.__set_output))

        with self.__widgets[self.ID]:
            self.__widgets[self.LABEL_SCENE] = ui.Label("", style_type_name_override="Code")

            with ui.VStack(**VSTACK_ARGS, name="main_vertical_stack"):
                with ui.HStack(width=0, spacing=10):
                    for widget in self.__widget_managers:
                        widget.build()
