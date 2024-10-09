"""Manager for the OmniGraph Toolkit window"""
from contextlib import suppress

import omni.graph.tools as ogt
import omni.kit.ui as kit_ui
import omni.ui as ui

from ..metaclass import Singleton  # noqa: PLE0402
from ..style import VSTACK_ARGS  # noqa: PLE0402
from ..style import get_window_style  # noqa: PLE0402
from .toolkit_frame_inspection import ToolkitFrameInspection
from .toolkit_frame_memory import ToolkitFrameMemory
from .toolkit_frame_output import ToolkitFrameOutput
from .toolkit_frame_scene import ToolkitFrameScene

MENU_PATH = "Window/Visual Scripting/Toolkit"


# ======================================================================
class Toolkit(metaclass=Singleton):
    """Class containing all of the functionality for the OmniGraph Toolkit Window"""

    @staticmethod
    def get_name():
        """Returns the name of this window extension"""
        return "OmniGraph Toolkit"

    # --------------------------------------------------------------------------------------------------------------
    @staticmethod
    def get_description():
        """Returns a description of this window extension"""
        return "Collection of utilities and inspectors to help in working with OmniGraph"

    # --------------------------------------------------------------------------------------------------------------
    @staticmethod
    def get_menu_path():
        """Returns the menu path where this window can be accessed"""
        return MENU_PATH

    # --------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """Set up the window elements - use show() for displaying the window"""
        # The window object
        self.__window = ui.Window(
            self.get_name(),
            width=800,
            height=500,
            menu_path=self.get_menu_path(),
            visible=False,
            visibility_changed_fn=self._visibility_changed_fn,
        )
        self.__window.frame.set_style(get_window_style())
        self.__window.frame.set_build_fn(self.__rebuild_window_frame)
        self.__window.frame.rebuild()

        # Manager for the debug output frame of the toolkit
        self.__frame_output = ToolkitFrameOutput()
        # Manager for the inspection frame of the toolkit
        self.__frame_inspection = ToolkitFrameInspection(self.__frame_output.set_debug_output)
        # Manager for the memory usage frame of the toolkit
        self.__frame_memory = ToolkitFrameMemory()
        # Manager for the scene manipulation frame of the toolkit
        self.__frame_scene = ToolkitFrameScene(self.__frame_output.set_debug_output)

    # --------------------------------------------------------------------------------------------------------------
    def destroy(self):
        """Destroy the singleton editor, if it exists"""
        with suppress(AttributeError):
            self.__window.visible = False
        with suppress(AttributeError):
            self.__window.frame.set_build_fn(None)
        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__frame_inspection")
        ogt.destroy_property(self, "__frame_output")
        ogt.destroy_property(self, "__frame_memory")
        ogt.destroy_property(self, "__frame_scene")
        ogt.destroy_property(self, "__window")
        self.__window = None
        Singleton.forget(Toolkit)

    # --------------------------------------------------------------------------------------------------------------
    def show_window(self):
        """Display the window"""
        self.__window.visible = True

    def hide_window(self):
        self.__window.visible = False

    def _visibility_changed_fn(self, visible):
        editor_menu = kit_ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(MENU_PATH, visible)

    # --------------------------------------------------------------------------------------------------------------
    def is_visible(self):
        """Returns the visibility state of our window"""
        return self.__window and self.__window.visible

    # --------------------------------------------------------------------------------------------------------------
    def __rebuild_window_frame(self):
        """Construct the widgets within the window"""

        with ui.ScrollingFrame(
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            name="main_frame",
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
        ):
            with ui.VStack(**VSTACK_ARGS, name="main_vertical_stack"):
                self.__frame_memory.build()
                self.__frame_inspection.build()
                self.__frame_scene.build()
                self.__frame_output.build()
