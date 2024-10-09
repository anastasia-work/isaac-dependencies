"""
Manage the window containing the node description editor. This main class manages several member
classes that handle different parts of the editor.

The general pattern is Model-View-Controller for each section. This file is the "View" for the
editor as a whole. Controller.py and Model.py form the other two parts.

change_management.py is a set of classes to handle notifications when structure or values change.
Icons.py houses utilities to manage icons used in the editor.
style.py contains the editor's style information, including sizing information that is not technically "style"

The editor itself is managed in sections, roughly corresponding to the files in the diagram below

    +------------------------------------+
    | MenuManager.py                     |
    |     FileManager.py                 |
    +====================================+
    | [Generator.py]                     |
    +------------------------------------+
    | v ExtensionInfoManager.py          |
    +------------------------------------+
    | v node_properties.py               |
    |     MemoryTypeManager.py           |
    |     NodeLanguageManager.py         |
    |     MetadataManager.py             |
    +------------------------------------+
    | v attribute_properties.py          |
    |     AttributeTupleCountManager.py  |
    |     AttributeListManager.py        |
    |     AttributeBaseTypeManager.py    |
    |     MemoryTypeManager.py           |
    |     MetadataManager.py             |
    +------------------------------------+
    | v test_configurations.py           |
    +------------------------------------+
    | v RawOgnManager.py                 |
    +------------------------------------+
"""
import asyncio
import json
import os
from contextlib import suppress

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
import omni.kit
from omni import ui
from omni.kit.widget.prompt import Prompt

from ..metaclass import Singleton  # noqa: PLE0402
from ..style import VSTACK_ARGS, get_window_style  # noqa: PLE0402
from .attribute_properties import AttributeListView  # noqa: PLE0402
from .extension_info_manager import ExtensionInfoManager  # noqa: PLE0402
from .file_manager import FileManager  # noqa: PLE0402
from .main_controller import Controller  # noqa: PLE0402
from .main_model import Model  # noqa: PLE0402
from .node_properties import NodePropertiesView  # noqa: PLE0402
from .ogn_editor_utils import show_wip  # noqa: PLE0402
from .test_configurations import TestListView  # noqa: PLE0402

# ======================================================================
# Constants for the layout of the window
EXTENSION_NAME = "OmniGraph Node Description Editor"
EXTENSION_DESC = "Description ui for the .ogn format of OmniGraph nodes"
MENU_PATH = "Window/Visual Scripting/Node Description Editor"

# ======================================================================
# ID values for the dictionary of frames within the window
ID_FRAME_OGN_CONTENTS = "frameOgn"
ID_GENERATED_CPP = "generatedCpp"
ID_GENERATED_USD = "generatedUsd"
ID_GENERATED_DOC = "generatedDocs"
ID_GENERATED_PYTHON = "generatedPython"
ID_GENERATED_TEMPLATE = "generatedTemplate"
ID_GENERATED_TESTS = "generatedTests"


# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_ARRAY_DEPTH = "attributeArrayDepth"
ID_ATTR_DEFAULT = "attributeDefault"
ID_ATTR_DESCRIPTION = "attributeDescription"
ID_ATTR_DESCRIPTION_PROMPT = "attributeDescriptionPrompt"
ID_ATTR_MEMORY_TYPE = "attributeMemoryType"
ID_ATTR_TYPE = "attributeType"
ID_INPUT_NAME = "attributeInputName"
ID_OGN_CONTENTS = "generatedOgn"
ID_OUTPUT_NAME = "attributeOutputName"


# ======================================================================
# ID for dictionary of classes that manage subsections of the editor, named for their class
ID_MGR_ATTR_METADATA = "AttributeMetadataManager"


# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {
    ID_OGN_CONTENTS: "The .ogn file that would result from the current configuration",
    ID_ATTR_ARRAY_DEPTH: "Array dimension of the attribute (e.g. 1 = float[], 0 = float)",
    ID_ATTR_DEFAULT: "Default value of the attribute when none has been set",
    ID_ATTR_DESCRIPTION: "Description of what information the attribute holds",
    ID_ATTR_MEMORY_TYPE: "Type of memory in which the attribute's data will reside",
    ID_ATTR_TYPE: "Type of data the attribute holds",
    ID_INPUT_NAME: "Name of the attribute without the 'inputs:' prefix",
    ID_OUTPUT_NAME: "Name of the attribute without the 'outputs:' prefix",
}


# ======================================================================
# Dispatch table for menu items.
# The menus are described as a dictionary of {MENU_NAME: MENU_ITEMS},
# where MENU_ITEMS is a list of tuples (MENU_ITEM_TEXT, MENU_ITEM_FUNCTION, MENU_ITEM_TOOLTIP)
# The MENU_ITEM_FUNCTION is a method on Editor, resolved by introspection.
MENU_DEFINITIONS = {
    "File": [
        ("Open...", "_on_menu_file_open", "Open a .ogn file into the editor"),
        ("Save...", "_on_menu_file_save", "Save a .ogn file from the editor"),
        ("Save as...", "_on_menu_file_save_as", "Save to a new .ogn file from the editor"),
        ("New Node", "_on_menu_file_new", "Create a new empty .ogn file in the editor"),
        ("Print OGN", "_on_menu_show_ogn", "Print the .ogn file contents to the console"),
        ("Extension Info", "_on_menu_show_extension", "Show extension information"),
    ]
}


# ======================================================================
class Editor(metaclass=Singleton):
    """Manager of the window for editing the Node Description values (.ogn file contents)

    Internal Properties:
        __controller: Helper that handles modifications to the underlying OGN data model
        __frame: Main frame of the window
        __input_attribute_view: AttributeListView objects controlling the UI for input attributes
        __managers: Dictionary of classes that manage various subparts of the editor
        __model: Contains the underlying OGN data model
        __output_attribute_view: AttributeListView objects controlling the UI for output attributes
        __tests_view: TestListView objects controlling the UI for automated test specifications
        __widget_models: Dictionary of model classes used by widgets, by ID
        __widgets: Dictionary of editable widgets, by ID
        __window: Window object containing the editor widgets
    """

    # ----------------------------------------------------------------------
    @staticmethod
    def get_name() -> str:
        """Returns the name of the window extension"""
        return EXTENSION_NAME

    # ----------------------------------------------------------------------
    @staticmethod
    def get_description() -> str:
        """Returns a description of the window extension"""
        return EXTENSION_DESC

    # ----------------------------------------------------------------------
    def __init__(self):
        """Sets up the internal state of the window"""
        ogt.dbg_ui("Creating the window")

        # These elements are built when the main frame rebuilds
        self.__input_attribute_view = None
        self.__node_view = None
        self.__output_attribute_view = None
        self.__tests_view = None

        self.__widgets = {}
        self.__model = Model()
        self.__controller = Controller(self.__model, None)
        self.__controller.add_change_callback(self.__on_ogn_changed)
        self.__file_manager = FileManager(self.__controller)
        self.__extension_manager = ExtensionInfoManager(self.__file_manager, self.__controller)
        self.__model.extension = self.__extension_manager.extension
        self.__model.file_manager = self.__file_manager

        self.__window = ui.Window(
            EXTENSION_NAME,
            flags=ui.WINDOW_FLAGS_MENU_BAR,
            menu_path=MENU_PATH,
            width=600,
            height=800,
            visible=False,
            visibility_changed_fn=self._visibility_changed_fn,
        )
        self.__window.frame.set_style(get_window_style())

        with self.__window.menu_bar:
            for menu_name, menu_info in MENU_DEFINITIONS.items():
                with ui.Menu(menu_name):
                    for (item_name, item_function, item_tooltip) in menu_info:
                        ui.MenuItem(item_name, tooltip=item_tooltip, triggered_fn=getattr(self, item_function))
        self.__window.menu_bar.visible = True
        self.__window.frame.set_build_fn(self.__rebuild_window_frame)
        self.__window.frame.rebuild()

    def destroy(self):
        """
        Called by the extension when it is being unloaded. Due to some ambiguities in references to C++ bound
        objects endemic to UI calls the explicit destroy must happen to avoid leaks.
        """
        ogt.dbg_ui(f"Destroying the OGN editor window {self} and {self.__extension_manager}")
        with suppress(AttributeError):
            self.__window.visible = False
        with suppress(KeyError, AttributeError):
            self.__widgets[ID_FRAME_OGN_CONTENTS].set_build_fn(None)
        with suppress(AttributeError):
            self.__window.frame.set_build_fn(None)
        # Ordering is important for ensuring owners destroy references last.
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__extension_manager")
        ogt.destroy_property(self, "__file_manager")
        ogt.destroy_property(self, "__node_view")
        ogt.destroy_property(self, "__input_attribute_view")
        ogt.destroy_property(self, "__output_attribute_view")
        ogt.destroy_property(self, "__tests_view")
        ogt.destroy_property(self, "__controller")
        ogt.destroy_property(self, "__model")
        ogt.destroy_property(self, "__window")
        Singleton.forget(Editor)

    # ----------------------------------------------------------------------
    def show_window(self):
        """Show the currently defined window"""
        self.__window.visible = True

    def hide_window(self):
        self.__window.visible = False

    def _visibility_changed_fn(self, visible):
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(MENU_PATH, visible)

    # ----------------------------------------------------------------------
    def is_visible(self):
        """Returns the visibility state of our window"""
        return self.__window and self.__window.visible

    # ----------------------------------------------------------------------
    def __on_node_class_changed(self):
        """Callback executed when the node class name changed as a result of a file operation"""
        ogt.dbg_ui("Node class changed")
        new_path = self.__file_manager.ogn_path
        if new_path is not None:
            self.__extension_manager.node_class = os.path.splitext(os.path.basename(new_path))[0]

    # ----------------------------------------------------------------------
    def _on_menu_file_open(self):
        """Callback executed when there is a request to open a new .ogn file"""
        ogt.dbg_ui("Editor._on_menu_file_open")
        self.__file_manager.open(on_open_done=lambda: asyncio.ensure_future(self.__file_opened()))
        self.__on_node_class_changed()

    # ----------------------------------------------------------------------
    def _on_menu_file_save(self):
        """Callback executed when there is a request to save a new .ogn file"""
        ogt.dbg_ui("Editor._on_menu_file_save")
        self.__file_manager.save()
        self.__on_node_class_changed()

    # ----------------------------------------------------------------------
    def _on_menu_file_save_as(self):
        """Callback executed when there is a request to save a new .ogn file"""
        ogt.dbg_ui("Editor._on_menu_file_save_as")
        self.__file_manager.save(None, True)
        self.__on_node_class_changed()

    # ----------------------------------------------------------------------
    def _on_menu_file_new(self):
        """Callback executed when there is a request to create a new .ogn file"""
        ogt.dbg_ui("Editor._on_menu_file_new")
        self.__file_manager.new()
        self.__window.frame.rebuild()

    # ----------------------------------------------------------------------
    def _on_menu_show_ogn(self):
        """Callback executed when there is a request to display the current .ogn file"""
        ogt.dbg_ui("Editor._on_menu_show_ogn")
        print(json.dumps(self.__controller.ogn_data, indent=4), flush=True)

    # ----------------------------------------------------------------------
    def _on_menu_show_extension(self):
        """Callback executed when the show extension info menu item was selected, for dumping useful information"""
        manager = omni.kit.app.get_app().get_extension_manager()
        print(json.dumps(manager.get_extensions(), indent=4), flush=True)

    # ----------------------------------------------------------------------
    def __on_ogn_changed(self, change_message=None):
        """Callback executed whenever any data affecting the .ogn file has changed"""
        ogt.dbg_ui("Updating OGN frame")
        try:
            self.__widgets[ID_OGN_CONTENTS].text = json.dumps(self.__controller.ogn_data, indent=4)
        except KeyError:
            ogt.dbg_ui("-> OGN frame does not exist")

    # ----------------------------------------------------------------------
    def __rebuild_ogn_frame(self):
        """Construct the current contents of the .ogn file"""
        ogt.dbg_ui("Rebuilding the .ogn frame")
        with self.__widgets[ID_FRAME_OGN_CONTENTS]:
            self.__widgets[ID_OGN_CONTENTS] = ui.Label("", style_type_name_override="Code")
            self.__on_ogn_changed()

    # ----------------------------------------------------------------------
    def __build_ogn_frame(self):
        """Construct the collapsable frame containing the current contents of the .ogn file"""
        ogt.dbg_ui("Building the .ogn frame")
        self.__widgets[ID_FRAME_OGN_CONTENTS] = ui.CollapsableFrame(
            title="Raw .ogn Data", tooltip=TOOLTIPS[ID_OGN_CONTENTS], collapsed=True
        )
        self.__widgets[ID_FRAME_OGN_CONTENTS].set_build_fn(self.__rebuild_ogn_frame)
        self.__on_ogn_changed()

    # ----------------------------------------------------------------------
    async def __file_opened(self):
        """Callback that happens after a file has finished opening. Refresh the window if needed."""
        ogt.dbg_ui("Callback after file was opened")
        self.__on_node_class_changed()
        self.__window.frame.rebuild()
        # Make sure the file data is synchronized before redrawing the window
        await omni.kit.app.get_app().next_update_async()

    # ----------------------------------------------------------------------
    def __rebuild_window_frame(self):
        """Callback to rebuild the window frame when the contents have changed.
        Call self.__window.frame.rebuild() to trigger this rebuild manually.
        """
        ogt.dbg_ui("-------------- Rebuilding the window frame --------------")
        self.__widgets = {}

        try:
            with ui.ScrollingFrame(
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                name="main_frame",
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            ):
                with ui.VStack(**VSTACK_ARGS, name="main_vertical_stack"):
                    self.__extension_manager.build_ui()
                    self.__node_view = NodePropertiesView(self.__controller.node_properties_controller)
                    self.__input_attribute_view = AttributeListView(self.__controller.input_attribute_controller)
                    self.__output_attribute_view = AttributeListView(self.__controller.output_attribute_controller)
                    assert self.__node_view
                    assert self.__input_attribute_view
                    assert self.__output_attribute_view
                    # TODO: This is not quite coordinating properly; add it back later
                    if show_wip():
                        self.__tests_view = TestListView(self.__controller.tests_controller)
                        assert self.__tests_view
                    self.__build_ogn_frame()
        except ogn.ParseError as error:
            Prompt("Parse Error", f"Could not populate values due to parse error - {error}", "Okay").show()
