"""Handler for the memory usage frame of the OmniGraph toolkit"""
import carb
import omni.graph.core as og
import omni.graph.tools as ogt
import omni.kit
import omni.ui as ui

from ..style import BUTTON_WIDTH, VSTACK_ARGS, name_value_hstack, name_value_label
from ..utils import DestructibleButton


# ======================================================================
class ToolkitFrameMemory:
    """Class containing all of the functionality for the memory usage frame in the OmniGraph Toolkit Window

    Public Functions:
        build() : Construct the frame

    Layout of the class constants is stacked:
        Constants
        Initialize/Destroy
        Public Functions
        Build Functions
        Callback Functions
    """

    # ----------------------------------------------------------------------
    # Frame information
    ID = "FrameMemory"
    TITLE = "Memory Usage"

    # ----------------------------------------------------------------------
    # IDs for widgets
    ID_BTN_UPDATE_MEMORY = "UpdateMemoryUsed"
    ID_MEMORY_USED = "MemoryUsed"
    ID_BTN_SHOW_FABRIC = "ShowFabricDebug"

    # ----------------------------------------------------------------------
    # Tooltips for the editable widgets
    TOOLTIPS = {
        ID_MEMORY_USED: "How much memory is currently being used by OmniGraph?",
        ID_BTN_UPDATE_MEMORY: "Update the memory usage for the current OmniGraph",
        ID_BTN_SHOW_FABRIC: "Enable the Fabric debug window",
    }

    # --------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """Set up the frame elements - use build() for constructing the frame"""
        # Dictionary of widgets in the window
        self.__widgets = {}
        # Dictionary of data models belonging to widgets in the window
        self.__widget_models = {}

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        """Destroy the memory usage frame"""
        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__widgets")
        # __widget_models are destroyed when __widgets are destroyed

    # ----------------------------------------------------------------------
    def build(self):
        """Construct the widgets used in the memory usage section"""
        with ui.VStack(**VSTACK_ARGS):
            with name_value_hstack():
                name_value_label("Memory Used By Graph:")
                model = ui.SimpleIntModel(0)
                self.__widgets[self.ID_MEMORY_USED] = ui.IntField(
                    model=model,
                    width=100,
                    name=self.ID_MEMORY_USED,
                    tooltip=self.TOOLTIPS[self.ID_MEMORY_USED],
                    alignment=ui.Alignment.LEFT_CENTER,
                )
                self.__widget_models[self.ID_MEMORY_USED] = model
                self.__widgets[self.ID_BTN_UPDATE_MEMORY] = DestructibleButton(
                    "Update Memory Used",
                    name=self.ID_BTN_UPDATE_MEMORY,
                    width=BUTTON_WIDTH,
                    tooltip=self.TOOLTIPS[self.ID_BTN_UPDATE_MEMORY],
                    clicked_fn=self.__on_update_memory_used_button,
                )
            self.__widgets[self.ID_BTN_SHOW_FABRIC] = DestructibleButton(
                "Fabric Inspector...",
                name=self.ID_BTN_SHOW_FABRIC,
                width=BUTTON_WIDTH,
                tooltip=self.TOOLTIPS[self.ID_BTN_SHOW_FABRIC],
                clicked_fn=self.__on_enable_fabric_debug_button,
            )

    # --------------------------------------------------------------------------------------------------------------
    def __on_update_memory_used_button(self):
        """Callback executed when the Update Memory Used button is clicked"""
        ctx = og.get_compute_graph_contexts()[0]
        self.__widget_models[self.ID_MEMORY_USED].set_value(og.OmniGraphInspector().memory_use(ctx))

    # --------------------------------------------------------------------------------------------------------------
    def __on_enable_fabric_debug_button(self):
        """Callback executed when the Fabric Debug button is clicked"""
        fabric_debug_extension_name = "omni.fabric.fabric_inspector"
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if ext_manager.is_extension_enabled(fabric_debug_extension_name):
            return

        try:
            ext_id = ext_manager.fetch_extension_versions("omni.fabric.fabric_inspector")[0]["id"]
        except (ValueError, IndexError, TypeError) as error:
            carb.log_warn(f"Could not find the Fabric inspector extension - {error}")

        ext_manager.set_extension_enabled_immediate(ext_id, True)
