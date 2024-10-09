# noqa: PLC0302
"""
Collection of classes managing the Node Properties section of the OmniGraphNodeDescriptionEditor

These classes use a Model-View-Controller paradigm to manage the interface between the UI and the raw OGN data.
"""
import os
import shutil
from contextlib import suppress
from functools import partial
from subprocess import Popen
from typing import Dict, Optional

import carb
import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_error, log_warn
from omni import ui
from omni.kit.widget.prompt import Prompt

from ..style import VSTACK_ARGS, name_value_hstack, name_value_label  # noqa: PLE0402
from .change_management import ChangeManager
from .file_manager import FileManager
from .memory_type_manager import MemoryTypeManager
from .metadata_manager import MetadataManager
from .node_language_manager import NodeLanguageManager
from .ogn_editor_utils import DestructibleButton, GhostedWidgetInfo, OptionalCallback, ghost_int, ghost_text, show_wip

# ======================================================================
# List of metadata elements that will not be edited directly in the "Metadata" section.
FILTERED_METADATA = [ogn.NodeTypeKeys.UI_NAME]

# ======================================================================
# ID values for widgets that are editable or need updating
ID_BTN_SAVE = "nodeButtonSave"
ID_BTN_SAVE_AS = "nodeButtonSaveAs"
ID_BTN_GENERATE_TEMPLATE = "nodeButtonGenerateTemplate"
ID_BTN_EDIT_NODE = "nodeEditImplButton"
ID_BTN_EDIT_OGN = "nodeEditOgnButton"
ID_NODE_DESCRIPTION = "nodeDescription"
ID_NODE_DESCRIPTION_PROMPT = "nodeDescriptionPrompt"
ID_NODE_LANGUAGE = "nodeLanguage"
ID_NODE_MEMORY_TYPE = "nodeMemoryType"
ID_NODE_NAME = "nodeName"
ID_NODE_NAME_PROMPT = "nodeNamePrompt"
ID_NODE_UI_NAME = "nodeUiName"
ID_NODE_UI_NAME_PROMPT = "nodeUiNamePrompt"
ID_NODE_UNSUPPORTED = "nodeUnsupported"
ID_NODE_VERSION = "nodeVersion"
ID_NODE_VERSION_PROMPT = "nodeVersionPrompt"

# ======================================================================
# ID for dictionary of classes that manage subsections of the editor, named for their class
ID_MGR_NODE_METADATA = "NodeMetadataManager"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {
    ID_BTN_SAVE: "Save .ogn file",
    ID_BTN_SAVE_AS: "Save .ogn file in a new location",
    ID_BTN_GENERATE_TEMPLATE: "Generate an empty implementation of your node algorithm",
    ID_BTN_EDIT_NODE: "Launch the text editor on your node implementation file, if it exists",
    ID_BTN_EDIT_OGN: "Launch the text editor on your .ogn file, if it exists",
    ID_NODE_DESCRIPTION: "Description of what the node's compute algorithm does, ideally with examples",
    ID_NODE_NAME: "Name of the node type as it will appear in the graph",
    ID_NODE_UI_NAME: "Name of the node type that will show up in user-interface elements",
    ID_NODE_UNSUPPORTED: "This node contains one or more elements that, while legal, are not yet supported in code",
    ID_NODE_VERSION: "Current version of the node type (integer value)",
}

# ======================================================================
# Dispatch table for generated file type exclusion checkboxes.
# Key is the ID of the checkbox for the file type exclusions.
# Value is a tuple of (CHECKBOX_TEXT, EXCLUSION_NAME, CHECKBOX_TOOLTIP)
NODE_EXCLUSION_CHECKBOXES = {
    "nodeExclusionsCpp": ("C++", "c++", "Allow generation of C++ database interface header (if not a Python node)"),
    "nodeExclusionsPython": ("Python", "python", "Allow generation of Python database interface class"),
    "nodeExclusionsDocs": ("Docs", "docs", "Allow generation of node documentation file"),
    "nodeExclusionsTests": ("Tests", "tests", "Allow generation of node test scripts"),
    "nodeExclusionsUsd": ("USD", "usd", "Allow generation of USD template file with node description"),
    "nodeExclusionsTemplate": (
        "Template",
        "template",
        "Allow generation of template file with sample node implementation in the chosen language",
    ),
}


# ================================================================================
def is_node_name_valid(tentative_node_name: str) -> bool:
    """Returns True if the tentative node name is legal"""
    try:
        ogn.check_node_name(tentative_node_name)
        return True
    except ogn.ParseError:
        return False


# ================================================================================
def is_node_ui_name_valid(tentative_node_ui_name: str) -> bool:
    """Returns True if the tentative node name is legal"""
    try:
        ogn.check_node_ui_name(tentative_node_ui_name)
        return True
    except ogn.ParseError:
        return False


# ================================================================================
class NodePropertiesModel:
    """
    Manager for the node description data. Handles the data in both the raw and parsed OGN form.
    The raw form is used wherever possible for more flexibility in editing, allowing temporarily illegal
    data that can have notifications to the user for fixing (e.g. duplicate names)

    External Properties:
        description
        error
        memory_type
        metadata
        name
        node_language
        ogn_data
        ogn_directory
        ui_name
        version

    Internal Properties:
        __name: Name of the node
        __comments: List of comment fields found at the node level
        __data: Raw node data dictionary, not including the attributes or tests
        __error: Error found in parsing the top level node data
    """

    def __init__(
        self,
        node_name: str,
        extension: ogn.OmniGraphExtension,
        node_data: Optional[Dict],
        file_manager: Optional[FileManager],
    ):
        """
        Create an initial node model.

        Args:
            node_name: Name of the node; will be checked
            extension: Information regarding the extension to which the node belongs
            node_data: Dictionary of node data, in the .ogn format
            file_manager: File manager for OGN data
        """
        self.__error = None
        self.__name = None
        self.__comments = {}
        self.__extension = extension
        self.__file_manager = file_manager

        self.name = node_name
        if node_data is None:
            self.__data = {ogn.NodeTypeKeys.DESCRIPTION: "", ogn.NodeTypeKeys.VERSION: 1}
        else:
            for key, value in node_data.items():
                if key and key[0] == "$":
                    self.__comments[key] = value
            self.__data = {key: value for key, value in node_data.items() if len(key) == 0 or key[0] != "$"}

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when this model is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__comments = {}
        self.__data = {}
        self.__error = None
        self.__name = None

    # ----------------------------------------------------------------------
    def ogn_interface(self):
        """Returns the extracted OGN node manager for this node's data, None if it cannot be parsed"""
        return ogn.NodeInterfaceWrapper({self.__name: self.__data}, self.extension_name, None).node_interface

    # ----------------------------------------------------------------------
    @staticmethod
    def edit_file(file_path: Optional[str]):
        """Try to launch the editor on the file, giving appropriate messaging if it fails

        Raises:
            AttributeError: Path is not defined
        """
        if not file_path or not os.path.isfile(file_path):
            log_warn(f"Could not edit non-existent file {file_path}")
            return

        settings = carb.settings.get_settings()

        # Find out which editor it's necessary to use
        # Check the settings
        editor = settings.get("/app/editor")
        if not editor:
            # If settings doesn't have it, check the environment variable EDITOR.
            # It's the standard way to set the editor in Linux.
            editor = os.environ.get("EDITOR", None)
            if not editor:
                # VSCode is the default editor
                editor = "code"

        # Remove quotes because it's a common way for windows to specify paths
        if editor[0] == '"' and editor[-1] == '"':
            editor = editor[1:-1]

        # Check if editor is not executable, preferring a .cmd or .bat since they have fewer escaping problems
        if shutil.which(f"{editor}.cmd") is not None:
            editor = editor + ".cmd"
        elif shutil.which(f"{editor}.bat") is not None:
            editor = editor + ".bat"
        elif shutil.which(editor) is None:
            log_warn(f"Editor not found '{editor}', switching to default editor")
            editor = None

        if not editor:
            if os.name == "nt":
                # All Windows have notepad
                editor = "notepad"
            else:
                # Most Linux systems have gedit
                editor = "gedit"

        if os.name == "nt" and not editor.endswith(".bat") and not editor.endswith(".cmd"):
            # Using cmd on the case the editor is bat or cmd file
            call_command = ["cmd", "/c"]
        else:
            call_command = []

        call_command.append(editor)
        call_command.append(file_path)

        # Non blocking call
        try:
            Popen(call_command)  # noqa: PLR1732
        except Exception as error:  # pylint: disable=broad-except
            log_warn(f"Could not edit file {file_path} - {error}")

    # ----------------------------------------------------------------------
    def save_node(self, on_save_done: OptionalCallback = None):
        """Save the OGN file"""
        if not self.__file_manager:
            log_error("Unable to save node: File manager is not initialized")
            return
        self.__file_manager.save(on_save_done)

    # ----------------------------------------------------------------------
    def save_as_node(self, on_save_as_done: OptionalCallback = None):
        """Save the OGN file"""
        if not self.__file_manager:
            log_error("Unable to save node: File manager is not initialized")
            return
        self.__file_manager.save(on_save_as_done, open_save_dialog=True)

    # ----------------------------------------------------------------------
    def generate_template(self):
        """Generate a template implementaiton based on the OGN file"""

        if not self.__file_manager:
            log_error("Unable to generate template: File manager is not initialized")
            return

        # Ensure nodes/ directory exists
        os.makedirs(self.__file_manager.ogn_directory, exist_ok=True)
        # Ensure .ogn file was saved
        self.save_node()
        if self.__file_manager.save_failed() or not self.__file_manager.ogn_path:
            log_error("Save failed")
            return

        # Generate the template file
        try:
            node_interface = self.ogn_interface()
            base_name, _ = os.path.splitext(os.path.basename(self.__file_manager.ogn_path))
            configuration = ogn.GeneratorConfiguration(
                self.__file_manager.ogn_path,
                node_interface,
                self.__extension.import_path,
                self.__extension.import_path,
                base_name,
                self.__file_manager.ogn_directory,
                ogn.OGN_PARSE_DEBUG,
            )
        except ogn.ParseError as error:
            log_error(f"Could not parse .ogn file : {error}")
            Prompt("Parse Failure", f"Could not parse .ogn file : {error}", "Okay").show()
            return
        try:
            ogn.generate_template(configuration)
        except ogn.NodeGenerationError as error:
            log_error(f"Template file could not be generated : {error}")
            Prompt("Generation Failure", f"Template file could not be generated : {error}", "Okay").show()
            return

    # ----------------------------------------------------------------------
    def edit_node(self):
        """Edit the OGN file implementation in an external editor"""
        ogt.dbg_ui("Edit the Node file")
        try:
            ogn_path = self.__file_manager.ogn_path
            node_path = ogn_path.replace(".ogn", ".py")
            if os.path.exists(node_path):
                self.edit_file(node_path)
            else:
                node_path = ogn_path.replace(".py", ".cpp")
                self.edit_file(node_path)
        except AttributeError:
            log_warn("Node file not found, generate a blank implementation first")
            Prompt(
                "Node File Missing",
                "Node file does not exist. Please generate a blank implementation first.",
                "Okay",
            ).show()

    # ----------------------------------------------------------------------
    def edit_ogn(self):
        """Edit the ogn file in an external editor"""
        ogt.dbg_ui("Edit the OGN file")
        try:
            if self.__file_manager.ogn_path and os.path.exists(self.__file_manager.ogn_path):
                self.edit_file(self.__file_manager.ogn_path)
            else:
                raise AttributeError(f'No such file "{self.__file_manager.ogn_path}"')
        except AttributeError as error:
            ogt.dbg_ui(f"OGN edit error {error}")
            log_warn(f'.ogn file "{self.__file_manager.ogn_path}" does not exist. Please save the node first.')
            Prompt(
                "OGN File Missing",
                f'.ogn file "{self.__file_manager.ogn_path}" does not exist. Please save the node first.',
                "Okay",
            ).show()

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self):
        """Returns the raw OGN data for this node's definition, putting the comments back in place"""
        main_data = self.__comments.copy()
        main_data.update(self.__data)
        return main_data

    # ----------------------------------------------------------------------
    @property
    def extension_name(self):
        """Returns the name of the extension to which the node belongs"""
        return self.__extension.extension_name if self.__extension is not None else ""

    # ----------------------------------------------------------------------
    @property
    def error(self):
        """Returns the current parse errors in the object, if any"""
        return self.__error

    # ----------------------------------------------------------------------
    @property
    def description(self) -> str:
        """Returns the current node description as a single line of text"""
        try:
            description_data = self.__data[ogn.NodeTypeKeys.DESCRIPTION]
            if isinstance(description_data, list):
                description_data = " ".join(description_data)
        except KeyError:
            description_data = ""
        return description_data

    @description.setter
    def description(self, new_description: str):
        """Sets the node description to a new value"""
        self.__data[ogn.NodeTypeKeys.DESCRIPTION] = new_description

    # ----------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Returns the current node name as a single line of text"""
        return self.__name

    @name.setter
    def name(self, new_name: str):
        """Sets the node name to a new value"""
        try:
            ogn.check_node_name(new_name)
            self.__name = new_name

        except ogn.ParseError as error:
            self.__error = error
            log_warn(f"Node name {new_name} is not legal - {error}")

    # ----------------------------------------------------------------------
    @property
    def ui_name(self) -> str:
        """Returns the current user-friendly node name as a single line of text, default to empty string"""
        try:
            return self.metadata[ogn.NodeTypeKeys.UI_NAME]
        except (AttributeError, KeyError):
            return ""

    @ui_name.setter
    def ui_name(self, new_ui_name: str):
        """Sets the user-friendly node name to a new value"""
        try:
            ogn.check_node_ui_name(new_ui_name)
            self.set_metadata_value(ogn.NodeTypeKeys.UI_NAME, new_ui_name, True)
        except ogn.ParseError as error:
            self.__error = error
            log_warn(f"User-friendly node name {new_ui_name} is not legal - {error}")

    # ----------------------------------------------------------------------
    @property
    def version(self) -> int:
        """Returns the current node version as a single line of text"""
        try:
            version_number = int(self.__data[ogn.NodeTypeKeys.VERSION])
        except KeyError:
            version_number = 1
        return version_number

    @version.setter
    def version(self, new_version: int):
        """Sets the node version to a new value"""
        self.__data[ogn.NodeTypeKeys.VERSION] = new_version

    # ----------------------------------------------------------------------
    @property
    def memory_type(self) -> str:
        """Returns the current node memory type"""
        try:
            memory_type = self.__data[ogn.NodeTypeKeys.MEMORY_TYPE]
        except KeyError:
            memory_type = ogn.MemoryTypeValues.CPU
        return memory_type

    @memory_type.setter
    def memory_type(self, new_memory_type: str):
        """Sets the node memory_type to a new value"""
        ogn.check_memory_type(new_memory_type)
        if new_memory_type == ogn.MemoryTypeValues.CPU:
            # Leave out the memory type if it is the default
            with suppress(KeyError):
                del self.__data[ogn.NodeTypeKeys.MEMORY_TYPE]
        else:
            self.__data[ogn.NodeTypeKeys.MEMORY_TYPE] = new_memory_type

    # ----------------------------------------------------------------------
    @property
    def node_language(self) -> str:
        """Returns the current node node language"""
        try:
            node_language = self.__data[ogn.NodeTypeKeys.LANGUAGE]
        except KeyError:
            node_language = ogn.LanguageTypeValues.CPP
        return node_language

    @node_language.setter
    def node_language(self, new_node_language: str):
        """Sets the node node_language to a new value"""
        ogn.check_node_language(new_node_language)
        if new_node_language == ogn.LanguageTypeValues.CPP:
            # Leave out the language type if it is the default
            with suppress(KeyError):
                del self.__data[ogn.NodeTypeKeys.LANGUAGE]
        else:
            self.__data[ogn.NodeTypeKeys.LANGUAGE] = new_node_language

    # ----------------------------------------------------------------------
    def excluded(self, file_type: str):
        """
        Returns whethe the named file type will not be generated by this node.
        These are not properties as it is more efficient to use a parameter since they are all in the same list.
        """
        try:
            exclude = file_type in self.__data[ogn.NodeTypeKeys.EXCLUDE]
        except KeyError:
            exclude = False
        return exclude

    def set_excluded(self, file_type: str, new_value: bool):
        """Sets whether the given file type will not be generated by this node"""
        if new_value:
            exclusions = self.__data.get(ogn.NodeTypeKeys.EXCLUDE, [])
            exclusions = list(set(exclusions + [file_type]))
            self.__data[ogn.NodeTypeKeys.EXCLUDE] = exclusions
        else:
            try:
                exclusions = self.__data[ogn.NodeTypeKeys.EXCLUDE]
                exclusions.remove(file_type)
                # Remove the list itself if it becomes empty
                if not exclusions:
                    del self.__data[ogn.NodeTypeKeys.EXCLUDE]
            except KeyError:
                pass

    # ----------------------------------------------------------------------
    @property
    def metadata(self):
        """Returns the current metadata dictionary"""
        try:
            return self.__data[ogn.NodeTypeKeys.METADATA]
        except KeyError:
            return {}

    def set_metadata_value(self, new_key: str, new_value: str, remove_if_empty: bool):
        """Sets a new value in the node's metadata

        Args:
            new_key: Metadata name
            new_value: Metadata value
            remove_if_empty: If True and the new_value is empty then delete the metadata value
        """
        try:
            self.__data[ogn.NodeTypeKeys.METADATA] = self.__data.get(ogn.NodeTypeKeys.METADATA, {})
            if remove_if_empty and not new_value:
                # Delete the metadata key if requested, cascading to the entire metadata dictionary if
                # removing this key empties it.
                try:
                    del self.__data[ogn.NodeTypeKeys.METADATA][new_key]
                    if not self.__data[ogn.NodeTypeKeys.METADATA]:
                        del self.__data[ogn.NodeTypeKeys.METADATA]
                except KeyError:
                    pass
            else:
                self.__data[ogn.NodeTypeKeys.METADATA][new_key] = new_value
        except (AttributeError, IndexError, TypeError, ogn.ParseError) as error:
            raise AttributeError(str(error)) from error

    @metadata.setter
    def metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the node's metadata"""
        try:
            if not new_metadata:
                with suppress(KeyError):
                    del self.__data[ogn.NodeTypeKeys.METADATA]
            else:
                self.__data[ogn.NodeTypeKeys.METADATA] = new_metadata
        except (AttributeError, IndexError, TypeError, ogn.ParseError) as error:
            raise AttributeError(str(error)) from error

    # ----------------------------------------------------------------------
    @property
    def file_manager(self) -> "FileManager":
        """Return the file manager on the current ogn"""
        return self.__file_manager

    # ----------------------------------------------------------------------
    @file_manager.setter
    def file_manager(self, file_manager: "FileManager"):
        """Sets the file manager on the current model"""
        self.__file_manager = file_manager

    # ----------------------------------------------------------------------
    @property
    def extension(self) -> ogn.OmniGraphExtension:
        """Return the extension information on the current model"""
        return self.__extension

    # ----------------------------------------------------------------------
    @extension.setter
    def extension(self, extension: ogn.OmniGraphExtension):
        """Sets the extension information on the current model"""
        self.__extension = extension


# ================================================================================
class NodePropertiesController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    External Methods:
        generate_template(self)
        save_node(self)
        edit_node(self)
        edit_ogn(self)

    External Properties:
        description
        filtered_metadata
        memory_type
        metadata
        name
        node_language
        ui_name
        version

    Internal Properties:
        __model: The model this class controls
    """

    def __init__(self, model: NodePropertiesModel):
        """Initialize the controller with the model it will control"""
        super().__init__()
        self.__model = model

    def destroy(self):
        """Called when this controller is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        self.__model = None

    # ----------------------------------------------------------------------
    def generate_template(self):
        """Generate a template implementaiton based on the OGN file"""
        self.__model.generate_template()

    def save_node(self):
        """Save the OGN file"""
        self.__model.save_node()

    def save_as_node(self):
        """Save the OGN file in a new location"""
        self.__model.save_as_node()

    def edit_node(self):
        """Edit the OGN file implementation in an external editor"""
        self.__model.edit_node()

    def edit_ogn(self):
        """Edit the ogn file in an external editor"""
        self.__model.edit_ogn()

    # ----------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Returns the fully namespaced name of this node"""
        return self.__model.name

    @name.setter
    def name(self, new_name: str):
        """Renames the node

        Raises:
            ogn.ParseError: If the new name is not a legal node name
        """
        ogt.dbg_ui(f"Change name from {self.name} to {new_name}")
        self.__model.name = new_name
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def ui_name(self) -> str:
        """Returns the fully namespaced name of this node"""
        return self.__model.ui_name

    @ui_name.setter
    def ui_name(self, new_ui_name: str):
        """Sets a new user-friendly name for the node

        Raises:
            ogn.ParseError: If the new name is not a legal node name
        """
        ogt.dbg_ui(f"Change name from {self.name} to {new_ui_name}")
        self.__model.ui_name = new_ui_name
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def description(self) -> str:
        """Returns the description of this node"""
        return self.__model.description

    @description.setter
    def description(self, new_description: str):
        """Sets the description of this node"""
        ogt.dbg_ui(f"Set description of {self.name} to {new_description}")
        self.__model.description = new_description
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def version(self) -> str:
        """Returns the version number of this node"""
        return self.__model.version

    @version.setter
    def version(self, new_version: str):
        """Sets the version number of this node"""
        ogt.dbg_ui(f"Set version of {self.name} to {new_version}")
        self.__model.version = new_version
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def memory_type(self) -> str:
        """Returns the current memory type for this node"""
        return self.__model.memory_type

    @memory_type.setter
    def memory_type(self, new_memory_type: str):
        """Sets the current memory type for this node"""
        self.__model.memory_type = new_memory_type
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def node_language(self) -> str:
        """Returns the current implementation language for this node"""
        return self.__model.node_language

    @node_language.setter
    def node_language(self, new_node_language: str):
        """Sets the current implementation language for this node"""
        self.__model.node_language = new_node_language
        self.on_change()

    # ----------------------------------------------------------------------
    def excluded(self, file_type: str):
        """
        Returns whethe the named file type will not be generated by this node.
        These are not properties as it is more efficient to use a parameter since they are all in the same list.
        """
        return self.__model.excluded(file_type)

    def set_excluded(self, file_type: str, new_value: bool):
        """Sets whether the given file type will not be generated by this node"""
        self.__model.set_excluded(file_type, new_value)
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def metadata(self):
        """Returns the current metadata dictionary"""
        return self.__model.metadata

    def set_metadata_value(self, new_key: str, new_value: str):
        """Sets a new value in the node's metadata"""
        self.__model.set_metadata_value(new_key, new_value, new_key == ogn.NodeTypeKeys.UI_NAME)
        self.on_change()

    @metadata.setter
    def metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the node's metadata"""
        self.__model.metadata = new_metadata
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def filtered_metadata(self):
        """Returns the current metadata, not including the metadata handled by separate UI elements"""
        return {key: value for key, value in self.__model.metadata.items() if key not in FILTERED_METADATA}

    @filtered_metadata.setter
    def filtered_metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the node's metadata, not including the metadata handled by separate UI elements"""
        extra_metadata = {key: value for key, value in self.__model.metadata.items() if key in FILTERED_METADATA}
        extra_metadata.update(new_metadata)
        self.__model.metadata = extra_metadata
        self.on_change()


# ================================================================================
class NodePropertiesView:
    """
    Manage the UI elements for the node properties frame. Instantiated as part of the editor.

    Internal Properties:
        __controller: Controller for the node properties
        __frame: Main frame for the node property interface
        __managers: Dictionary of ID:Manager for the components of the node's frame
        __subscriptions: Dictionary of ID:Subscription for the components of the node's frame
        __widget_models: Dictionary of ID:Model for the components of the node's frame
        __widgets: Dictionary of ID:Widget for the components of the node's frame
    """

    def __init__(self, controller: NodePropertiesController):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__controller = controller
        assert self.__controller
        self.__subscriptions = {}
        self.__widgets = {}
        self.__widget_models = {}
        self.__managers = {}
        self.__frame = ui.CollapsableFrame(title="Node Properties", collapsed=False)
        self.__frame.set_build_fn(self.__rebuild_frame)

    def destroy(self):
        """Called when the view is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        with suppress(AttributeError):
            self.__frame.set_build_fn(None)
        self.__controller = None
        ogt.destroy_property(self, "__widget_models")
        ogt.destroy_property(self, "__subscriptions")
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__managers")
        ogt.destroy_property(self, "__frame")

    # ----------------------------------------------------------------------
    def __on_description_changed(self, new_description: str):
        """Callback that runs when the node description was edited"""
        ogt.dbg_ui(f"__on_description_changed({new_description})")
        self.__controller.description = new_description

    def __on_name_changed(self, new_name: str):
        """Callback that runs when the node name was edited"""
        ogt.dbg_ui(f"__on_name_changed({new_name})")
        self.__controller.name = new_name

    def __on_ui_name_changed(self, new_ui_name: str):
        """Callback that runs when the user-friendly version of the node name was edited"""
        ogt.dbg_ui(f"__on_name_changed({new_ui_name})")
        self.__controller.ui_name = new_ui_name

    def __on_version_changed(self, new_version: str):
        """Callback that runs when the node version was edited"""
        ogt.dbg_ui(f"__on_version_changed({new_version})")
        self.__controller.version = int(new_version)

    def __on_exclusion_changed(self, widget_id: str, mouse_x: int, mouse_y: int, mouse_button: int, value: str):
        """Callback executed when there is a request to change exclusion status for one of the generated file types"""
        ogt.dbg_ui(f"__on_exclusion_changed({widget_id}, {mouse_x}, {mouse_y}, {mouse_button}, {value})")
        new_exclusion = self.__widgets[widget_id].model.as_bool
        exclusion_changed = NODE_EXCLUSION_CHECKBOXES[widget_id][1]
        self.__controller.set_excluded(exclusion_changed, new_exclusion)

    # ----------------------------------------------------------------------
    def __on_save_button(self):
        """Callback executed when the Save button is clicked"""
        self.__controller.save_node()

    # ----------------------------------------------------------------------
    def __on_save_as_button(self):
        """Callback executed when the Save As button is clicked"""
        self.__controller.save_as_node()

    # ----------------------------------------------------------------------
    def __on_generate_template_button(self):
        """Callback executed when the Generate button is clicked"""
        ogt.dbg_ui("Generate Template Button Clicked")
        self.__controller.generate_template()

    # ----------------------------------------------------------------------
    def __on_edit_ogn_button(self):
        """Callback executed with the Edit OGN button was pressed - launch the editor if the file exists"""
        self.__controller.edit_ogn()

    # ----------------------------------------------------------------------
    def __on_edit_node_button(self):
        """Callback executed with the Edit Node button was pressed - launch the editor if the file exists"""
        self.__controller.edit_node()

    # ----------------------------------------------------------------------
    def __register_ghost_info(self, ghost_info: GhostedWidgetInfo, widget_name: str, prompt_widget_name: str):
        """Add the ghost widget information to the model data"""
        self.__subscriptions[widget_name + "_begin"] = ghost_info.begin_subscription
        self.__subscriptions[widget_name + "_end"] = ghost_info.end_subscription
        self.__widgets[widget_name] = ghost_info.widget
        self.__widget_models[widget_name] = ghost_info.model
        self.__widgets[prompt_widget_name] = ghost_info.prompt_widget

    # ----------------------------------------------------------------------
    def __build_controls_ui(self):
        self.__widgets[ID_BTN_SAVE] = DestructibleButton(
            "Save Node",
            name=ID_BTN_SAVE,
            tooltip=TOOLTIPS[ID_BTN_SAVE],
            clicked_fn=self.__on_save_button,
        )

        self.__widgets[ID_BTN_SAVE_AS] = DestructibleButton(
            "Save Node As...",
            name=ID_BTN_SAVE_AS,
            tooltip=TOOLTIPS[ID_BTN_SAVE_AS],
            clicked_fn=self.__on_save_as_button,
        )

        self.__widgets[ID_BTN_GENERATE_TEMPLATE] = DestructibleButton(
            "Generate Blank Implementation",
            name=ID_BTN_GENERATE_TEMPLATE,
            tooltip=TOOLTIPS[ID_BTN_GENERATE_TEMPLATE],
            clicked_fn=self.__on_generate_template_button,
        )

        self.__widgets[ID_BTN_EDIT_OGN] = DestructibleButton(
            "Edit .ogn",
            name=ID_BTN_EDIT_OGN,
            tooltip=TOOLTIPS[ID_BTN_EDIT_OGN],
            clicked_fn=self.__on_edit_ogn_button,
        )

        self.__widgets[ID_BTN_EDIT_NODE] = DestructibleButton(
            "Edit Node",
            name=ID_BTN_EDIT_NODE,
            tooltip=TOOLTIPS[ID_BTN_EDIT_NODE],
            clicked_fn=self.__on_edit_node_button,
        )

    # ----------------------------------------------------------------------
    def __build_name_ui(self):
        """Build the contents implementing the node name editing widget"""
        ghost_info = ghost_text(
            label="Name:",
            tooltip=TOOLTIPS[ID_NODE_NAME],
            widget_id=ID_NODE_NAME,
            initial_value=self.__controller.name,
            ghosted_text="Enter Node Name...",
            change_callback=self.__on_name_changed,
            validation=(is_node_name_valid, ogn.NODE_NAME_REQUIREMENT),
        )
        self.__register_ghost_info(ghost_info, ID_NODE_NAME, ID_NODE_NAME_PROMPT)

    # ----------------------------------------------------------------------
    def __build_ui_name_ui(self):
        """Build the contents implementing the user-friendly node name editing widget"""
        ghost_info = ghost_text(
            label="UI Name:",
            tooltip=TOOLTIPS[ID_NODE_UI_NAME],
            widget_id=ID_NODE_UI_NAME,
            initial_value=self.__controller.ui_name,
            ghosted_text="Enter User-Friendly Node Name...",
            change_callback=self.__on_ui_name_changed,
            validation=(is_node_ui_name_valid, ogn.NODE_UI_NAME_REQUIREMENT),
        )
        self.__register_ghost_info(ghost_info, ID_NODE_UI_NAME, ID_NODE_UI_NAME_PROMPT)

    # ----------------------------------------------------------------------
    def __build_description_ui(self):
        """Build the contents implementing the node description editing widget"""
        ghost_info = ghost_text(
            label="Description:",
            tooltip=TOOLTIPS[ID_NODE_DESCRIPTION],
            widget_id=ID_NODE_DESCRIPTION,
            initial_value=self.__controller.description,
            ghosted_text="Enter Node Description...",
            change_callback=self.__on_description_changed,
        )
        self.__register_ghost_info(ghost_info, ID_NODE_DESCRIPTION, ID_NODE_DESCRIPTION_PROMPT)

    # ----------------------------------------------------------------------
    def __build_version_ui(self):
        """Build the contents implementing the node version editing widget"""
        ghost_info = ghost_int(
            label="Version:",
            tooltip=TOOLTIPS[ID_NODE_VERSION],
            widget_id=ID_NODE_VERSION,
            initial_value=self.__controller.version,
            ghosted_text="Enter Node Version Number...",
            change_callback=self.__on_version_changed,
        )
        self.__register_ghost_info(ghost_info, ID_NODE_VERSION, ID_NODE_VERSION_PROMPT)

    # ----------------------------------------------------------------------
    def __build_memory_type_ui(self):
        """Build the contents implementing the node memory type editing widget"""
        self.__managers[ID_NODE_MEMORY_TYPE] = MemoryTypeManager(self.__controller)

    # ----------------------------------------------------------------------
    def __build_node_language_ui(self):
        """Build the contents implementing the node language type editing widget"""
        self.__managers[ID_NODE_LANGUAGE] = NodeLanguageManager(self.__controller)

    # ----------------------------------------------------------------------
    def __build_node_exclusions_ui(self):
        """Build the contents implementing the set of checkboxes selecting which files will be generated"""
        if show_wip():
            name_value_label("Generated By Build:", "Select the file types the node is allowed to generate")
            with ui.VStack(**VSTACK_ARGS):
                for checkbox_id, checkbox_info in NODE_EXCLUSION_CHECKBOXES.items():
                    with ui.HStack(spacing=10):
                        model = ui.SimpleIntModel(not self.__controller.excluded(checkbox_info[1]))
                        widget = ui.CheckBox(
                            model=model,
                            mouse_released_fn=partial(self.__on_exclusion_changed, checkbox_id),
                            name=checkbox_id,
                            width=0,
                            style_type_name_override="WhiteCheck",
                        )
                        ui.Label(checkbox_info[0], alignment=ui.Alignment.LEFT_CENTER, tooltip=checkbox_info[2])
                        self.__widgets[checkbox_id] = widget
                        self.__widget_models[checkbox_id] = widget

    # ----------------------------------------------------------------------
    def __build_metadata_ui(self):
        """Build the contents implementing the metadata value list"""
        self.__managers[ID_MGR_NODE_METADATA] = MetadataManager(self.__controller)

    # ----------------------------------------------------------------------
    def __rebuild_frame(self):
        """Rebuild the contents underneath the main node frame"""
        with ui.VStack(**VSTACK_ARGS):
            with ui.HStack(width=0):
                self.__build_controls_ui()

            with name_value_hstack():
                self.__build_name_ui()

            with name_value_hstack():
                self.__build_description_ui()

            with name_value_hstack():
                self.__build_version_ui()

            with name_value_hstack():
                self.__build_ui_name_ui()

            with name_value_hstack():
                self.__build_memory_type_ui()

            with name_value_hstack():
                self.__build_node_language_ui()

            with name_value_hstack():
                self.__build_node_exclusions_ui()

            with name_value_hstack():
                self.__build_metadata_ui()
