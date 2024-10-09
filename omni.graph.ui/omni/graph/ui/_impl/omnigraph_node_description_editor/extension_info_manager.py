"""
Contains support for the UI to create and manage extensions containing OmniGraph nodes.
"""
import asyncio
import os
from contextlib import suppress

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_error, tokens
from omni import ui
from omni.kit.app import get_app_interface
from omni.kit.widget.filebrowser import FileBrowserItem
from omni.kit.widget.prompt import Prompt
from omni.kit.window.filepicker import FilePickerDialog

from ..style import VSTACK_ARGS, name_value_hstack, name_value_label  # noqa: PLE0402
from .file_manager import FileManager
from .main_controller import Controller
from .main_generator import Generator
from .ogn_editor_utils import DestructibleButton, ValidatedStringModel

# ======================================================================
# Pattern recognizing a legal import path
IMPORT_PATH_EXPLANATION = (
    "Import paths must start with a letter or underscore and only contain letters, numbers, underscores,"
    " and periods as separators"
)


# ======================================================================
# ID values for widgets that are editable or need updating
ID_BTN_CHOOSE_ROOT = "extensionButtonChooseRoot"
ID_BTN_CLEAN_EXTENSION = "extensionButtonClean"
ID_BTN_POPULATE_EXTENSION = "extensionButtonCreate"
ID_EXTENSION_ROOT = "extensionRoot"
ID_EXTENSION_IMPORT = "extensionImport"
ID_WINDOW_CHOOSE_ROOT = "extensionWindowChooseRoot"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {
    ID_BTN_CHOOSE_ROOT: "Select a new root location for your extension",
    ID_BTN_CLEAN_EXTENSION: "Clean out all generated files from your extension",
    ID_BTN_POPULATE_EXTENSION: "Populate a new python extension with your generated node files",
    ID_EXTENSION_ROOT: "Root directory where the extension will be installed",
    ID_EXTENSION_IMPORT: "Extension name, also used as the Python import path",
}


# ======================================================================
class ExtensionInfoManager:
    """Class encapsulating the tasks around management of extensions and .ogn file generation

    Properties:
        __controller: Main data controller
        __extension: ogn.OmniGraphExtension that manages the extension location and default file generation
        __file_manager: Object used to manage file-based interactions
        __frame: Main frame for this subsection of the editor
        __subscriptions: Diction of ID:Subscription for all callbacks, for easier destruction
        __widgets: Dictionary of ID:Widget for all elements in this subsection of the editor
        __widget_models: Dictionary of ID:Model for all elements in this subsection of the editor
                        The widgets do not maintain references to derived model classes so these must be explicit
    """

    def __init__(self, file_manager: FileManager, controller: Controller):
        """Set up an initial empty default extension environment"""
        # Carbonite has the notion of a shared extension location, default to that
        shared_path = tokens.get_tokens_interface().resolve("${shared_documents}")
        self.__extension = ogn.OmniGraphExtension(
            os.path.join(os.path.normpath(shared_path), "exts"), "omni.new.extension"
        )
        self.__file_manager = file_manager
        file_manager.ogn_directory = self.__extension.ogn_nodes_directory
        self.__controller = controller
        self.__subscription_to_enable = None
        self.__frame = None
        self.__subscriptions = {}
        self.__widgets = {}
        self.__widget_models = {}

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the manager is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__controller = None
        self.__extension = None
        self.__file_manager = None
        self.__frame = None
        self.__subscriptions = {}
        self.__subscription_to_enable = None
        ogt.destroy_property(self, "__widget_models")
        ogt.destroy_property(self, "__widgets")

    # ----------------------------------------------------------------------
    @property
    def extension(self) -> str:
        """Returns the information for the current extension"""
        return self.__extension

    # ----------------------------------------------------------------------
    def __on_import_path_changed(self, new_import_path: ui.SimpleStringModel):
        """Callback executed when the user has selected a new import path"""
        with suppress(ValueError):
            self.__extension.import_path = new_import_path.as_string
            ogt.dbg_ui(f"Import path changed to {new_import_path.as_string}")
            self.__file_manager.ogn_directory = self.__extension.ogn_nodes_directory

    # ----------------------------------------------------------------------
    def __on_root_changed(self, new_root_path: ui.SimpleStringModel):
        """Callback executed when the user has selected a new root directory"""
        ogt.dbg_ui(f"Root changed to {new_root_path.as_string}")
        self.__extension.extension_root = new_root_path.as_string
        self.__file_manager.ogn_directory = self.__extension.ogn_nodes_directory

    # ----------------------------------------------------------------------
    def __on_choose_root(self):
        """Callback executed when the Choose Root button is clicked"""

        def __on_filter_roots(item: FileBrowserItem) -> bool:
            """Callback to filter the choices of file names in the open or save dialog"""
            return not item or item.is_folder

        def __on_click_cancel(file_name: str, directory_name: str):
            """Callback executed when the user cancels the file open dialog"""
            ogt.dbg_ui("Clicked cancel in file open")
            self.__widgets[ID_WINDOW_CHOOSE_ROOT].hide()

        def __on_root_chosen(filename: str, dirname: str):
            """Callback executed when the user has selected a new root directory"""
            self.__widget_models[ID_EXTENSION_ROOT].set_value(os.path.join(dirname, filename))
            self.__widgets[ID_WINDOW_CHOOSE_ROOT].hide()

        ogt.dbg_ui("Choose Root Button Clicked")
        if ID_WINDOW_CHOOSE_ROOT not in self.__widgets:
            self.__widgets[ID_WINDOW_CHOOSE_ROOT] = FilePickerDialog(
                "Select Extension Root",
                allow_multi_selection=False,
                apply_button_label="Open",
                click_apply_handler=__on_root_chosen,
                click_cancel_handler=__on_click_cancel,
                item_filter_fn=__on_filter_roots,
                error_handler=log_error,
            )
        self.__widgets[ID_WINDOW_CHOOSE_ROOT].refresh_current_directory()
        self.__widgets[ID_WINDOW_CHOOSE_ROOT].show(path=self.__extension.extension_root)

    # ----------------------------------------------------------------------
    def __on_clean_extension_button(self):
        """Callback executed when the Clean Extension button is clicked"""
        ogt.dbg_ui("Clean Extension Button Clicked")
        # Find and remove all generated files
        self.__extension.remove_generated_files()
        self.__extension.write_ogn_init(force=True)

    # ----------------------------------------------------------------------
    def __on_populate_extension_button(self):
        """Callback executed when the Populate Extension button is clicked"""
        ogt.dbg_ui("Populate Extension Button Clicked")
        # Verify that the node is implemented in Python
        if self.__controller.node_properties_controller.node_language != ogn.LanguageTypeValues.PYTHON:
            Prompt("Node Language", "Only Python nodes can be processed", "Okay").show()

        # Create the extension directory tree if necessary
        self.__extension.create_directory_tree()
        self.__extension.remove_generated_files()
        self.__extension.write_all_files(force=True)

        # Ensure .ogn file was saved if it has already been defined
        if self.__file_manager.ogn_path is not None:
            self.__file_manager.save()
            if self.__file_manager.save_failed():
                Prompt(".ogn Not Generated", f"Could not generate {self.__file_manager.ogn_path}", "Okay").show()
                return

            # Generate the Python, USD, Tests, and Docs files
            try:
                generator = Generator(self.__extension)
                generator.parse(self.__file_manager.ogn_path)
            except ogn.ParseError as error:
                Prompt("Parse Failure", f"Could not parse .ogn file : {error}", "Okay").show()
                return
            except FileNotFoundError as error:
                Prompt(".ogn Not Found", f"Could not generate {self.__file_manager.ogn_path} - {error}", "Okay").show()
                return
            try:
                generator.generate_python()
            except ogn.NodeGenerationError as error:
                Prompt("Generation Failure", f"Python file could not be generated : {error}", "Okay").show()
                return
            try:
                generator.generate_tests()
            except ogn.NodeGenerationError as error:
                Prompt("Generation Failure", f"Test script could not be generated : {error}", "Okay").show()
                return
            try:
                generator.generate_documentation()
            except ogn.NodeGenerationError as error:
                Prompt("Generation Failure", f"Documentation file could not be generated : {error}", "Okay").show()
                return
            try:
                generator.generate_usd()
            except ogn.NodeGenerationError as error:
                Prompt("Generation Failure", f"USD file could not be generated : {error}", "Okay").show()
                return

        async def enable_extension_when_ready():
            """Wait for the load to be complete and then enable the new extension"""
            ext_manager = get_app_interface().get_extension_manager()
            if self.__extension:
                ext_manager.set_extension_enabled_immediate(self.__extension.import_path, True)

        # The extension manager needs an opportunity to scan the directory again before the extension can be
        # enabled so use a coroutine to wait for the next update to do so.
        ext_manager = get_app_interface().get_extension_manager()
        self.__subscription_to_enable = ext_manager.get_change_event_stream().create_subscription_to_pop(
            lambda _: asyncio.ensure_future(enable_extension_when_ready()), name=self.__extension.import_path
        )
        assert self.__subscription_to_enable

    # ----------------------------------------------------------------------
    def build_ui(self):
        """Runs UI commands that implement the extension management interface"""
        self.__frame = ui.CollapsableFrame("Extension Management", collapsed=True)
        with self.__frame:
            with ui.VStack(**VSTACK_ARGS):

                with ui.HStack(width=0):
                    self.__widgets[ID_BTN_POPULATE_EXTENSION] = DestructibleButton(
                        "Populate Extension",
                        name=ID_BTN_POPULATE_EXTENSION,
                        tooltip=TOOLTIPS[ID_BTN_POPULATE_EXTENSION],
                        clicked_fn=self.__on_populate_extension_button,
                    )
                    self.__widgets[ID_BTN_CLEAN_EXTENSION] = DestructibleButton(
                        "Clean Extension",
                        name=ID_BTN_CLEAN_EXTENSION,
                        tooltip=TOOLTIPS[ID_BTN_CLEAN_EXTENSION],
                        clicked_fn=self.__on_clean_extension_button,
                        style_type_name_override="DangerButton",
                    )

                with name_value_hstack():
                    name_value_label("Extension Location:")
                    model = ui.SimpleStringModel(self.__extension.extension_root)
                    self.__subscriptions[ID_EXTENSION_ROOT] = model.subscribe_end_edit_fn(self.__on_root_changed)
                    self.__widgets[ID_EXTENSION_ROOT] = ui.StringField(
                        model=model,
                        name=ID_EXTENSION_ROOT,
                        tooltip=TOOLTIPS[ID_EXTENSION_ROOT],
                        alignment=ui.Alignment.LEFT_BOTTOM,
                    )
                    self.__widget_models[ID_EXTENSION_ROOT] = model
                    self.__widgets[ID_BTN_CHOOSE_ROOT] = DestructibleButton(
                        width=24,
                        height=24,
                        clicked_fn=self.__on_choose_root,
                        style_type_name_override="FolderImage",
                        tooltip=TOOLTIPS[ID_BTN_CHOOSE_ROOT],
                    )

                with name_value_hstack():
                    name_value_label("Extension Name:")
                    model = ValidatedStringModel(
                        self.__extension.import_path,
                        ogn.OmniGraphExtension.validate_import_path,
                        IMPORT_PATH_EXPLANATION,
                    )
                    self.__subscriptions[ID_EXTENSION_IMPORT] = model.subscribe_end_edit_fn(
                        self.__on_import_path_changed
                    )
                    self.__widgets[ID_EXTENSION_IMPORT] = ui.StringField(
                        model=model, name=ID_EXTENSION_IMPORT, tooltip=TOOLTIPS[ID_EXTENSION_IMPORT]
                    )
                    self.__widget_models[ID_EXTENSION_IMPORT] = model
