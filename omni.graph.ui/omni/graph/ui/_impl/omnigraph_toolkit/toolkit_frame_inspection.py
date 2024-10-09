"""Handler for the inspection frame of the OmniGraph toolkit"""
from contextlib import suppress
from typing import Callable

import omni.graph.tools as ogt
import omni.kit
import omni.ui as ui

from ..style import VSTACK_ARGS
from .widgets.categories import ToolkitWidgetCategories
from .widgets.extension_timing import ToolkitWidgetExtensionTiming
from .widgets.graph_contents import ToolkitWidgetGraphContents
from .widgets.graph_registry import ToolkitWidgetGraphRegistry
from .widgets.graph_structure import ToolkitWidgetGraphStructure


# ======================================================================
class ToolkitFrameInspection:
    """Class containing all of the functionality for the inspection frame of the OmniGraph Toolkit Window"""

    # ----------------------------------------------------------------------
    # Frame information
    ID = "FrameInspection"
    TITLE = "OmniGraph Object Inspection"

    # ----------------------------------------------------------------------
    # IDs for widgets
    ID_INSPECTION_LABEL = "Inspection"

    # --------------------------------------------------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        """Set up the frame elements - use build() for constructing the frame"""
        # Dictionary of widgets in the window
        self.__widgets = {}
        # Dictionary of widget classes in the window
        self.__widget_classes = []
        # Callback to use for reporting new output
        self.__set_output = set_output_callback

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        """Destroy the frame"""
        with suppress(AttributeError, KeyError):
            self.__widgets[self.ID].set_build_fn(None)

        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__widget_classes")
        # __widget_models are destroyed when __widgets are destroyed

    # ----------------------------------------------------------------------
    def build(self):
        """Construct the collapsable frame containing the inspection operations"""
        self.__widgets[self.ID] = ui.CollapsableFrame(title=self.TITLE, collapsed=False)
        self.__widgets[self.ID].set_build_fn(self.__rebuild_inspection_frame)

    # ----------------------------------------------------------------------
    def __rebuild_inspection_frame(self):
        """Construct the widgets for running inspection operations"""
        self.__widget_classes.append(ToolkitWidgetGraphContents(self.__set_output))
        self.__widget_classes.append(ToolkitWidgetGraphStructure(self.__set_output))
        self.__widget_classes.append(ToolkitWidgetGraphRegistry(self.__set_output))
        self.__widget_classes.append(ToolkitWidgetCategories(self.__set_output))

        # Only show the extension dependencies if the extensions window extension is already loaded.
        # We don't want to force apps to load the extension if they don't want it.
        manager = omni.kit.app.get_app().get_extension_manager()

        if manager.is_extension_enabled("omni.kit.window.extensions"):
            from .widgets.extension_dependencies import ToolkitWidgetExtensionDependencies

            self.__widget_classes.append(ToolkitWidgetExtensionDependencies(self.__set_output))

        self.__widget_classes.append(ToolkitWidgetExtensionTiming(self.__set_output))

        with self.__widgets[self.ID]:
            self.__widgets[self.ID_INSPECTION_LABEL] = ui.Label("", style_type_name_override="Code")
            with ui.VStack(**VSTACK_ARGS, name="main_vertical_stack"):
                for widget in self.__widget_classes:
                    with ui.HStack(width=0, spacing=10):
                        widget.build()
