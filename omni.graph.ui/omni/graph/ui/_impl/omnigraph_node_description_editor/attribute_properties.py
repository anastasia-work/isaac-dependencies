"""
Collection of classes managing the Model-View-Controller paradigm for individual attributes within the node.
This attribute information is collected with the node information later to form the combined .ogn file.
"""  # noqa: PLC0302
import json
from contextlib import suppress
from functools import partial
from typing import Dict, List, Optional

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from ..style import VSTACK_ARGS  # noqa: PLE0402
from ..style import name_value_hstack  # noqa: PLE0402
from ..style import name_value_label  # noqa: PLE0402
from .attribute_base_type_manager import AttributeBaseTypeManager
from .attribute_tuple_count_manager import AttributeTupleCountManager
from .attribute_union_type_adder_manager import ID_ATTR_UNION_TYPE_ADDER, AttributeUnionTypeAdderManager
from .change_management import ChangeManager, ChangeMessage, RenameMessage
from .memory_type_manager import MemoryTypeManager
from .metadata_manager import MetadataManager
from .ogn_editor_utils import DestructibleButton, GhostedWidgetInfo, find_unique_name, ghost_text

# ======================================================================
# List of metadata elements that will not be edited directly in the "Metadata" section.
FILTERED_METADATA = [ogn.AttributeKeys.UI_NAME]


# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_BASE_TYPE = "attributeBaseType"
ID_ATTR_DEFAULT = "attributeDefault"
ID_ATTR_DEFAULT_PROMPT = "attributeDefaultPrompt"
ID_ATTR_DESCRIPTION = "attributeDescription"
ID_ATTR_DESCRIPTION_PROMPT = "attributeDescriptionPrompt"
ID_ATTR_MAXIMUM = "attributeMaximum"
ID_ATTR_MEMORY_TYPE = "attributeMemoryType"
ID_ATTR_MINIMUM = "attributeMinium"
ID_ATTR_UNION_TYPES = "attributeUnionTypes"
ID_ATTR_UNION_TYPES_PROMPT = "attributeUnionTypesPrompt"
ID_ATTR_NAME = "attributeName"
ID_ATTR_NAME_PROMPT = "attributeNamePrompt"
ID_UI_ATTR_NAME = "attributeUiName"
ID_UI_ATTR_NAME_PROMPT = "attributeUiNamePrompt"
ID_ATTR_OPTIONAL = "attributeOptional"
ID_ATTR_TUPLE_COUNT = "attributeTupleCount"
ID_ATTR_TYPE = "attributeType"
ID_ATTR_TYPE_ARRAY_DEPTH = "attributeTypeIsArray"
ID_ATTR_TYPE_BASE_TYPE = "attributeTypeBaseType"

# ======================================================================
# ID for frames that will be dynamically rebuild
ID_ATTR_FRAME_TYPE = "attributeTypeFrame"
ID_ATTR_FRAME_RANGE = "attributeRange"
ID_ATTR_FRAME_UNION_TYPES = "attributeUnionTypesFrame"

# ======================================================================
# ID for dictionary of classes that manage subsections of the editor, named for their class
ID_MGR_ATTR_METADATA = "AttributeMetadataManager"


# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {
    ID_ATTR_BASE_TYPE: "Base type of an attribute's data",
    ID_ATTR_DEFAULT: "Default value of the attribute when none has been set",
    ID_ATTR_DESCRIPTION: "Description of what information the attribute holds",
    ID_ATTR_FRAME_RANGE: "Lowest and highest values the attribute is allowed to take",
    ID_ATTR_FRAME_TYPE: "Properties defining the type of data the attribute manages",
    ID_ATTR_MAXIMUM: "Maximum value of the attribute or attribute component",
    ID_ATTR_MEMORY_TYPE: "Type of memory in which the attribute's data will reside",
    ID_ATTR_MINIMUM: "Minimum value of the attribute or attribute component",
    ID_ATTR_NAME: "Name of the attribute (without the inputs: or outputs: namespace)",
    ID_ATTR_OPTIONAL: "Can the attribute be left off the node and still have it operate correctly?",
    ID_ATTR_TUPLE_COUNT: "Number of base elements in the attribute",
    ID_ATTR_TYPE: "Type of data the attribute holds",
    ID_ATTR_UNION_TYPES: "Accepted union types if the attribute is a union",
    ID_ATTR_TYPE_ARRAY_DEPTH: "Is the attribute data an array of elements?",
    ID_ATTR_TYPE_BASE_TYPE: "Basic data elements in the attribute data",
    ID_UI_ATTR_NAME: "User-friendly name for the attribute",
}


# ================================================================================
def attribute_key_from_group(attribute_group: str) -> str:
    """Returns the name of the attribute group key to use at the node level of the .ogn file"""
    if attribute_group == ogn.INPUT_GROUP:
        attribute_group_key = ogn.NodeTypeKeys.INPUTS
    elif attribute_group == ogn.OUTPUT_GROUP:
        attribute_group_key = ogn.NodeTypeKeys.OUTPUTS
    else:
        attribute_group_key = ogn.NodeTypeKeys.STATE
    return attribute_group_key


# ================================================================================
def is_attribute_name_valid(attribute_group: str, tentative_attr_name: str) -> bool:
    """Returns True if the tentative attribute name is legal in the given group's namespace"""
    try:
        ogn.check_attribute_name(
            ogn.attribute_name_in_namespace(tentative_attr_name, ogn.namespace_of_group(attribute_group)),
            ogn.LanguageTypeValues.PYTHON,
        )
        return True
    except ogn.ParseError:
        return False


# ================================================================================
def is_attribute_ui_name_valid(tentative_attr_ui_name: str) -> bool:
    """Returns True if the tentative attribute name is legal"""
    try:
        ogn.check_attribute_ui_name(tentative_attr_ui_name)
        return True
    except ogn.ParseError:
        return False


# ================================================================================
class AttributeAddedMessage(ChangeMessage):
    """Encapsulation of a message sent just after an attribute is added"""

    def __init__(self, caller, attribute_name: str, attribute_group: str):
        """Set up a message with information needed to indicate an attribute addition"""
        super().__init__(caller)
        self.attribute_name = attribute_name
        self.attribute_group = attribute_group

    def __str__(self) -> str:
        """Returns a human-readable representation of the add information"""
        caller_info = super().__str__()
        namespace = ogn.namespace_of_group(self.attribute_group)
        return f"Add {namespace}:{self.attribute_name} (from {caller_info})"


# ================================================================================
class AttributeRemovedMessage(ChangeMessage):
    """Encapsulation of a message sent just before an attribute is removed"""

    def __init__(self, caller, attribute_name: str, attribute_group: str):
        """Set up a message with information needed to indicate an attribute removal"""
        super().__init__(caller)
        self.attribute_name = attribute_name
        self.attribute_group = attribute_group

    def __str__(self) -> str:
        """Returns a human-readable representation of the removal information"""
        caller_info = super().__str__()
        namespace = ogn.namespace_of_group(self.attribute_group)
        return f"Remove {namespace}:{self.attribute_name} (from {caller_info})"


# ================================================================================
class AttributePropertiesModel:
    """
    Manager for the attribute description data. Handles the data in both the raw and parsed OGN form.
    The raw form is used wherever possible for more flexibility in editing, allowing temporarily illegal
    data that can have notifications to the user for fixing (e.g. duplicate names)

    External Properties:
        array_depth
        array_depths_supported
        attribute_group
        attribute_manager
        base_name
        default
        description
        full_type
        is_output
        maximum
        memory_type
        metadata
        minimum
        name
        ogn_data
        optional
        tuple_count
        tuples_supported
        ui_name
        union_types

    Internal Properties:
        __attribute_group: Enum with the attribute's group (input, output, or state)
        __data: Raw attribute data dictionary
        __error: Error found in parsing the attribute data
        __name: Name of the attribute without the inputs: or outputs: namespace
        __namespace: The inputs: or outputs: namespace of the attribute when checking the name
    """

    def __init__(self, raw_attribute_name: str, attribute_group: str, attribute_data: Dict):
        """
        Create an initial attribute model.

        Args:
            raw_attribute_name: Raw name of the attribute, may or may not be namespaced as input or output
            _attribute_group: Is the attribute an output?
            attribute_data: Dictionary of attribute data, in the .ogn format
        """
        try:
            self.__attribute_group = attribute_group
            self.__data = attribute_data
            self.__namespace = ogn.namespace_of_group(attribute_group)
            self.__name = raw_attribute_name
        except ogn.ParseError as error:
            self.__error = error

    # ----------------------------------------------------------------------
    def ogn_interface(self):
        """Returns the extracted OGN attribute manager for this attribute's data, None if it cannot be parsed"""
        try:
            return ogn.get_attribute_manager(
                ogn.attribute_name_in_namespace(self.__name, ogn.namespace_of_group(self.__attribute_group)),
                attribute_data=self.__data,
            )
        except ogn.ParseError as error:
            self.__error = error
            return None

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self):
        """Returns the raw OGN data for this attribute's definition"""
        return {self.__name: self.__data}

    # ----------------------------------------------------------------------
    @property
    def attribute_group(self) -> str:
        """Returns the type of group to which this attribute belongs"""
        return self.__attribute_group

    # ----------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Returns the current attribute name"""
        return self.__name

    @name.setter
    def name(self, new_name: str):
        """Modifies the name of this attribute

        Raises:
            AttributeError: If the name was illegal or already taken
        """
        try:
            ogn.check_attribute_name(
                ogn.attribute_name_in_namespace(new_name, self.__namespace),
                ogn.LanguageTypeValues.PYTHON,
            )
            self.__name = new_name
        except ogn.ParseError as error:
            log_warn(f"Attribute name {new_name} is not legal - {error}")

    # ----------------------------------------------------------------------
    @property
    def ui_name(self) -> str:
        """Returns the current user-friendly attribute name"""
        try:
            return self.metadata[ogn.AttributeKeys.UI_NAME]
        except (AttributeError, KeyError):
            return ""

    @ui_name.setter
    def ui_name(self, new_ui_name: str):
        """Modifies the user-friendly name of this attribute"""
        try:
            ogn.check_attribute_ui_name(new_ui_name)
            self.set_metadata_value(ogn.AttributeKeys.UI_NAME, new_ui_name, True)
        except ogn.ParseError as error:
            self.__error = error
            log_warn(f"User-friendly attribute name {new_ui_name} is not legal - {error}")

    # ----------------------------------------------------------------------
    @property
    def description(self) -> str:
        """Returns the current attribute description as a single line of text"""
        try:
            description_data = self.__data[ogn.AttributeKeys.DESCRIPTION]
            if isinstance(description_data, list):
                description_data = " ".join(description_data)
        except KeyError:
            description_data = ""
        return description_data

    @description.setter
    def description(self, new_description: str):
        """Sets the attribute description to a new value"""
        self.__data[ogn.AttributeKeys.DESCRIPTION] = new_description

    # ----------------------------------------------------------------------
    @property
    def attribute_manager(self) -> ogn.AttributeManager:
        """Returns the class type that this attribute uses to manage its properties. Changes when base type changes"""
        try:
            return ogn.ALL_ATTRIBUTE_TYPES[self.base_type]
        except KeyError:
            return None

    # ----------------------------------------------------------------------
    @property
    def base_type(self) -> str:
        """Returns the current base data type for this attribute"""
        try:
            attribute_type = self.__data[ogn.AttributeKeys.TYPE]
            attribute_type_name, _, _, _ = ogn.split_attribute_type_name(attribute_type)
        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for {self.name} - {error}, defaulting to integer")
            attribute_type_name = "int"
        return attribute_type_name

    @base_type.setter
    def base_type(self, new_base_type: str):
        """Sets the current base data type for this attribute. Resets tuple and array information if needed."""
        try:
            _, tuple_count, array_depth, extra_info = ogn.split_attribute_type_name(self.__data[ogn.AttributeKeys.TYPE])
            manager = ogn.ALL_ATTRIBUTE_TYPES[new_base_type]
            if tuple_count not in manager.tuples_supported():
                new_tuple_count = manager.tuples_supported()[0]
                log_warn(f"Old tuple count of {tuple_count} not supported, defaulting to {new_tuple_count}")
                tuple_count = new_tuple_count

            if array_depth not in manager.array_depths_supported():
                new_array_depth = manager.array_depths_supported()[0]
                log_warn(f"Old array depth of {array_depth} not supported, defaulting to {new_array_depth}")
                array_depth = new_array_depth

            ogn.validate_attribute_type_name(new_base_type, tuple_count, array_depth)
            self.full_type = ogn.assemble_attribute_type_name(new_base_type, tuple_count, array_depth, extra_info)

        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for {self.name} - {error}, defaulting to integer")
            self.full_type = ogn.assemble_attribute_type_name("int", 1, 0)

    # ----------------------------------------------------------------------
    @property
    def tuple_count(self) -> int:
        """Returns the current tuple count for this attribute"""
        try:
            attribute_type = self.__data[ogn.AttributeKeys.TYPE]
            _, tuple_count, _, _ = ogn.split_attribute_type_name(attribute_type)
        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for {self.name} - {error}, defaulting to integer")
            tuple_count = 1
        return tuple_count

    @tuple_count.setter
    def tuple_count(self, new_tuple_count: int):
        """Sets the current tuple count for this attribute"""
        try:
            attribute_type_name, _, array_depth, extra_info = ogn.split_attribute_type_name(self.full_type)
            self.full_type = ogn.assemble_attribute_type_name(
                attribute_type_name, new_tuple_count, array_depth, extra_info
            )
        except ogn.ParseError as error:
            log_warn(f"Tuple count {new_tuple_count} not supported on {self.name}, {error}")

    @property
    def tuples_supported(self) -> List[int]:
        """Returns the list of tuple counts this attribute type permits"""
        try:
            return self.attribute_manager.tuples_supported()
        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for tuple counts on {self.name} - {error}, assuming only 1")
            tuple_counts = [1]
        return tuple_counts

    # ----------------------------------------------------------------------
    @property
    def array_depth(self) -> int:
        """Returns the array depth of this attribute"""
        try:
            attribute_type = self.__data[ogn.AttributeKeys.TYPE]
            _, _, array_depth, _ = ogn.split_attribute_type_name(attribute_type)
        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for {self.name} - {error}, defaulting to integer")
            array_depth = 0
        return array_depth

    @array_depth.setter
    def array_depth(self, new_array_depth: int):
        """Sets the current array depth for this attribute"""
        try:
            attribute_type_name, tuple_count, _, extra_info = ogn.split_attribute_type_name(self.full_type)
            self.full_type = ogn.assemble_attribute_type_name(
                attribute_type_name, tuple_count, new_array_depth, extra_info
            )
        except ogn.ParseError as error:
            log_warn(f"Array depth {new_array_depth} not supported on {self.name}, {error}")

    @property
    def array_depths_supported(self) -> List[int]:
        """Returns the list of array depth counts this attribute type permits"""
        try:
            return self.attribute_manager.array_depths_supported()
        except (KeyError, ogn.ParseError) as error:
            log_warn(f"Type not parsed for tuple counts on {self.name} - {error}, assuming only 1")
            tuple_counts = [1]
        return tuple_counts

    # ----------------------------------------------------------------------
    @property
    def full_type(self) -> str:
        """Returns the combined type/tuple_count/array_depth representation for this attribute"""
        try:
            attribute_type = self.__data[ogn.AttributeKeys.TYPE]
        except KeyError:
            log_warn(f"Type not found for {self.name}, defaulting to integer")
            attribute_type = "int"
        return attribute_type

    @full_type.setter
    def full_type(self, new_type: str):
        """Sets the attribute information based on the fully qualified type name"""
        # Splitting the type has the side effect of verifying the component parts and their combination
        try:
            _ = ogn.split_attribute_type_name(new_type)
            self.__data[ogn.AttributeKeys.TYPE] = new_type
            self.validate_default()
        except ogn.ParseError as error:
            log_warn(f"Type '{new_type}' on attribute '{self.name}' is invalid - {error}")

    # ----------------------------------------------------------------------
    @property
    def memory_type(self) -> str:
        """Returns the current node memory type"""
        try:
            memory_type = self.__data[ogn.AttributeKeys.MEMORY_TYPE]
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
                del self.__data[ogn.AttributeKeys.MEMORY_TYPE]
        else:
            self.__data[ogn.AttributeKeys.MEMORY_TYPE] = new_memory_type

    # ----------------------------------------------------------------------
    @property
    def metadata(self):
        """Returns the current metadata dictionary"""
        try:
            return self.__data[ogn.AttributeKeys.METADATA]
        except KeyError:
            return {}

    def set_metadata_value(self, new_key: str, new_value: str, remove_if_empty: bool):
        """Sets a new value in the attribute's metadata

        Args:
            new_key: Metadata name
            new_value: Metadata value
            remove_if_empty: If True and the new_value is empty then delete the metadata value
        """
        try:
            self.__data[ogn.AttributeKeys.METADATA] = self.__data.get(ogn.AttributeKeys.METADATA, {})
            if remove_if_empty and not new_value:
                # Delete the metadata key if requested, cascading to the entire metadata dictionary if
                # removing this key empties it.
                with suppress(KeyError):
                    del self.__data[ogn.AttributeKeys.METADATA][new_key]
                    if not self.__data[ogn.AttributeKeys.METADATA]:
                        del self.__data[ogn.AttributeKeys.METADATA]
            else:
                self.__data[ogn.AttributeKeys.METADATA][new_key] = new_value
        except (AttributeError, IndexError, TypeError, ogn.ParseError) as error:
            raise AttributeError(str(error)) from error

    @metadata.setter
    def metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the attribute's metadata"""
        try:
            if not new_metadata:
                with suppress(KeyError):
                    del self.__data[ogn.AttributeKeys.METADATA]
            else:
                self.__data[ogn.AttributeKeys.METADATA] = new_metadata
        except (AttributeError, IndexError, TypeError, ogn.ParseError) as error:
            raise AttributeError(str(error)) from error

    # ----------------------------------------------------------------------
    @property
    def minimum(self):
        """Returns the current minimum value of the attribute, None if it is not set"""
        try:
            return self.__data[ogn.AttributeKeys.MINIMUM]
        except KeyError:
            return None

    @minimum.setter
    def minimum(self, new_minimum):
        """Sets the new minimum value of the attribute, removing it if the new value is None"""
        if new_minimum is None:
            with suppress(KeyError):
                del self.__data[ogn.AttributeKeys.MINIMUM]
        else:
            self.__data[ogn.AttributeKeys.MINIMUM] = new_minimum

    # ----------------------------------------------------------------------
    @property
    def maximum(self):
        """Returns the current maximum value of the attribute, None if it is not set"""
        try:
            return self.__data[ogn.AttributeKeys.MAXIMUM]
        except KeyError:
            return None

    @maximum.setter
    def maximum(self, new_maximum):
        """Sets the new maximum value of the attribute, removing it if the new value is None"""
        if new_maximum is None:
            with suppress(KeyError):
                del self.__data[ogn.AttributeKeys.MAXIMUM]
        else:
            self.__data[ogn.AttributeKeys.MAXIMUM] = new_maximum

    # ----------------------------------------------------------------------
    @property
    def union_types(self) -> List[str]:
        """Returns the accepted union types value of the attribute, [] if it is not set"""
        return self.full_type if self.base_type == "union" else []

    @union_types.setter
    def union_types(self, new_union_types: List[str]):
        """Sets the new accepted union types of the attribute, removing it if the new value is None"""
        if self.base_type != "union":
            return
        if not new_union_types:
            self.full_type = []
        else:
            self.full_type = new_union_types

    # ----------------------------------------------------------------------
    @property
    def default(self):
        """Returns the current default value of the attribute, None if it is not set"""
        try:
            return self.__data[ogn.AttributeKeys.DEFAULT]
        except KeyError:
            return None

    def validate_default(self):
        """Checks that the current default is valid for the current attribute type, resetting to empty if not"""
        ogt.dbg_ui(f"Validating default {self.default} on type {self.full_type}")
        try:
            manager = ogn.get_attribute_manager_type(self.full_type)
            if self.default is None and not manager.requires_default():
                return
        except (AttributeError, ogn.ParseError) as error:
            # If the manager cannot be retrieved no validation can happen; trivial acceptance
            ogt.dbg_ui(f"Could not retrieve manager for default value validation - {error}")
            return
        try:
            manager.validate_value_structure(self.default)
            ogt.dbg_ui("...the current default is okay")
        except (AttributeError, ogn.ParseError):
            empty_default = manager.empty_value()
            log_warn(
                f"Current default value of {self.default} is invalid, setting it to an empty value {empty_default}"
            )
            self.default = json.dumps(empty_default)

    @default.setter
    def default(self, new_default: str):
        """Sets the new default value of the attribute, removing it if the new value is None"""
        ogt.dbg_ui(f"Setting new default to {new_default} on {self.ogn_data}")
        # For deleting the default it has to be removed. For setting a new value the attribute manager
        # will be created for validation and it should not have an existing value in that case.
        try:
            original_default = self.__data[ogn.AttributeKeys.DEFAULT]
            del self.__data[ogn.AttributeKeys.DEFAULT]
        except KeyError:
            original_default = None

        if new_default is None:
            return

        try:
            # Use the JSON library to decode the string into Python types
            try:
                default_as_json = json.loads(new_default)
            except json.decoder.JSONDecodeError as error:
                raise AttributeError(f"Could not parse default '{new_default}'") from error

            # Create a temporary attribute manager for validating data
            try:
                self.__data[ogn.AttributeKeys.DEFAULT] = default_as_json
                original_default = None
                temp_manager = self.ogn_interface()
                temp_manager.validate_value_structure(default_as_json)
            except AttributeError as error:
                raise AttributeError(f"Current data for {self.name} cannot be parsed - {self.__error}.") from error
            except ogn.ParseError as error:
                raise AttributeError(f"New default for {self.name} is not valid.") from error
            except Exception as error:
                raise AttributeError(f"Unknown error setting default on {self.name}") from error

        except AttributeError as error:
            log_warn(str(error))
            if original_default is not None:
                self.__data[ogn.AttributeKeys.DEFAULT] = original_default

    # ----------------------------------------------------------------------
    @property
    def optional(self) -> bool:
        """Returns the current optional flag on the attribute"""
        try:
            return self.__data[ogn.AttributeKeys.OPTIONAL]
        except KeyError:
            return False

    @optional.setter
    def optional(self, new_optional: bool):
        """Sets the new optional flag on the attribute"""
        if new_optional:
            with suppress(KeyError):
                del self.__data[ogn.AttributeKeys.OPTIONAL]
        else:
            self.__data[ogn.AttributeKeys.OPTIONAL] = new_optional


# ================================================================================
class AttributePropertiesController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    External Properties:
        array_depth
        array_depths_supported
        attribute_manager
        base_name
        default
        description
        filtered_metadata
        full_type
        base_type
        is_output
        maximum
        memory_type
        metadata
        minimum
        name
        ogn_data
        optional
        tuple_count
        tuples_supported
        ui_name
        union_types

    Internal Properties:
        _model: The model this class controls
        __parent_controller: Controller for the list of properties, for changing membership callbacks
    """

    def __init__(self, model: AttributePropertiesModel, parent_controller):
        """Initialize the controller with the model it will control"""
        super().__init__()
        self._model = model
        self.__parent_controller = parent_controller

    def destroy(self):
        """Called when the view is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        self._model = None
        self.__parent_controller = None

    # ----------------------------------------------------------------------
    def on_int_minimum_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when the minimum value of the attribute was changed"""
        self._model.minimum = new_value.as_int
        self.on_change()

    # ----------------------------------------------------------------------
    def on_int_maximum_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when the maximum value of the attribute was changed"""
        self._model.maximum = new_value.as_int
        self.on_change()

    # ----------------------------------------------------------------------
    def on_float_minimum_changed(self, new_value: ui.SimpleFloatModel):
        """Callback executed when the minimum value of the attribute was changed"""
        self._model.minimum = new_value.as_float
        self.on_change()

    # ----------------------------------------------------------------------
    def on_float_maximum_changed(self, new_value: ui.SimpleFloatModel):
        """Callback executed when the maximum value of the attribute was changed"""
        self._model.maximum = new_value.as_float
        self.on_change()

    # ----------------------------------------------------------------------
    def on_remove_attribute(self):
        """Callback that executes when the view wants to remove the named attribute"""
        ogt.dbg_ui(f"Removing an existing attribute {self.name}")
        self.__parent_controller.on_remove_attribute(self)

    # ----------------------------------------------------------------------
    @property
    def attribute_manager(self) -> ogn.AttributeManager:
        """Returns the class type that this attribute uses to manage its properties. May change when type changes"""
        return self._model.attribute_manager

    # ----------------------------------------------------------------------
    @property
    def attribute_group(self) -> str:
        """Returns the type of group to which this attribute belongs"""
        return self._model.attribute_group

    # ----------------------------------------------------------------------
    def is_output(self) -> bool:
        """Returns whether this attribute is an output or not"""
        return self._model.is_output

    # ----------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Returns the base name (without the inputs: or outputs: namespace) of this attribute"""
        return self._model.name

    @name.setter
    def name(self, new_name: str) -> str:
        """Modifies the name of this attribute

        Raises:
            AttributeError: If the name was illegal or already taken
        """
        # The parent controller gets dibs on the name change as it may refuse to do it due to duplication
        self.__parent_controller.on_name_change(self._model.name, new_name)

        name_change_message = RenameMessage(self, self._model.name, new_name)
        self._model.name = new_name
        self.on_change(name_change_message)

    @property
    def namespace(self) -> str:
        """Returns the implicit namespace (inputs: or outputs:) of this attribute"""
        return self._model._namespace  # noqa: PLW0212

    # ----------------------------------------------------------------------
    @property
    def ui_name(self) -> str:
        """Returns the user-friendly name of this attribute"""
        return self._model.ui_name

    @ui_name.setter
    def ui_name(self, new_ui_name: str) -> str:
        """Modifies the user-friendly name of this attribute

        Raises:
            AttributeError: If the name was illegal
        """
        self._model.ui_name = new_ui_name
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def description(self) -> str:
        """Returns the description of this attribute"""
        return self._model.description

    @description.setter
    def description(self, new_description: str):
        """Sets the description of this attribute"""
        ogt.dbg_ui(f"Set description of {self.name} to {new_description}")
        self._model.description = new_description
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def base_type(self) -> str:
        """Returns the current base data type for this attribute"""
        return self._model.base_type

    @base_type.setter
    def base_type(self, new_base_type: str):
        """Sets the current base data base type for this attribute"""
        self._model.base_type = new_base_type
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def tuple_count(self) -> int:
        """Returns the current tuple count for this attribute"""
        return self._model.tuple_count

    @tuple_count.setter
    def tuple_count(self, new_tuple_count: int):
        """Sets the current tuple count for this attribute"""
        self._model.tuple_count = new_tuple_count
        self.on_change()

    @property
    def tuples_supported(self) -> List[int]:
        """Returns the list of tuple counts this attribute type permits"""
        return self._model.tuples_supported

    # ----------------------------------------------------------------------
    @property
    def array_depth(self) -> int:
        """Returns the array depth of this attribute"""
        return self._model.array_depth

    @array_depth.setter
    def array_depth(self, new_array_depth: int):
        """Sets the current array depth for this attribute"""
        self._model.array_depth = new_array_depth
        self.on_change()

    @property
    def array_depths_supported(self) -> List[int]:
        """Returns the list of array depths this attribute type permits"""
        return self._model.array_depths_supported

    # ----------------------------------------------------------------------
    @property
    def memory_type(self) -> str:
        """Returns the current memory type for this attribute"""
        return self._model.memory_type

    @memory_type.setter
    def memory_type(self, new_memory_type: str):
        """Sets the current memory type for this attribute"""
        self._model.memory_type = new_memory_type
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def metadata(self):
        """Returns the current metadata dictionary"""
        return self._model.metadata

    def set_metadata_value(self, new_key: str, new_value: str):
        """Sets a new value in the attribute's metadata"""
        self._model.set_metadata_value(new_key, new_value)
        self.on_change()

    @metadata.setter
    def metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the attribute's metadata"""
        self._model.metadata = new_metadata
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def filtered_metadata(self):
        """Returns the current metadata, not including the metadata handled by separate UI elements"""
        return {key: value for key, value in self._model.metadata.items() if key not in FILTERED_METADATA}

    @filtered_metadata.setter
    def filtered_metadata(self, new_metadata: Dict[str, str]):
        """Wholesale replacement of the node's metadata, not including the metadata handled by separate UI elements"""
        extra_metadata = {key: value for key, value in self._model.metadata.items() if key in FILTERED_METADATA}
        extra_metadata.update(new_metadata)
        self._model.metadata = extra_metadata
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def default(self) -> str:
        """Returns the default value of this attribute"""
        return self._model.default

    @default.setter
    def default(self, new_default: str):
        """Sets the default value of this attribute"""
        ogt.dbg_ui(f"Set default value of {self.name} to {new_default}")
        self._model.default = new_default
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def optional(self) -> str:
        """Returns the optional flag for this attribute"""
        return self._model.optional

    @optional.setter
    def optional(self, new_optional: str):
        """Sets the optional flag for this attribute"""
        ogt.dbg_ui(f"Set optional of {self.name} to {new_optional}")
        self._model.optional = new_optional
        self.on_change()

    # ----------------------------------------------------------------------
    @property
    def union_types(self) -> List[str]:
        """Returns the accepted union types of this attribute"""
        return self._model.union_types

    @union_types.setter
    def union_types(self, new_union_types: List[str]):
        """Sets the accepted union types for this attribute"""
        self._model.union_types = new_union_types
        self.on_change()


# ================================================================================
class AttributePropertiesView:
    """UI for a single attribute's data

    Internal Properties:
        _controller: The controller used to manipulate the model's data
        _frame: Main frame for this attribute's interface
        _widgets: Dictionary of ID:Widget for the components of the attribute's frame
    """

    def __init__(self, controller: AttributePropertiesController):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__controller = controller
        self.__subscriptions = {}
        self.__type_managers = {}
        self.__type_subscriptions = {}
        self.__type_widgets = {}
        self.__widgets = {}
        self.__widget_models = {}
        self.__managers = {}
        with ui.HStack(spacing=0):
            self.__remove_button = DestructibleButton(
                width=20,
                height=20,
                style_type_name_override="RemoveElement",
                clicked_fn=self._on_remove_attribute,
                tooltip="Remove this attribute",
            )
            assert self.__remove_button
            self.__frame = ui.CollapsableFrame(title=self.__controller.name, collapsed=False)
        self.__frame.set_build_fn(self.__rebuild_frame)

    def destroy(self):
        """Reset all of the attribute's widgets and delete the main frame (done when the attribute is removed)"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        with suppress(AttributeError, ValueError):
            self.__controller.remove_change_callback(self.__on_controller_change)
        self.__controller = None
        self.destroy_frame_contents()
        with suppress(AttributeError):
            self.__frame.set_build_fn(None)
        ogt.destroy_property(self, "__remove_button")
        ogt.destroy_property(self, "__frame")

    def destroy_frame_contents(self):
        """Destroy just the widgets within the attribute's frame, for rebuilding"""
        self.destroy_type_ui_frame()
        with suppress(AttributeError, KeyError):
            self.__widgets[ID_ATTR_FRAME_RANGE].set_build_fn(None)
        with suppress(AttributeError, KeyError):
            self.__widgets[ID_ATTR_FRAME_TYPE].set_build_fn(None)
        ogt.destroy_property(self, "__subscriptions")
        ogt.destroy_property(self, "__managers")
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__widget_models")

    def destroy_type_ui_frame(self):
        """Gracefully release references to elements that are part of the type specification frame"""
        ogt.destroy_property(self, "__type_managers")
        ogt.destroy_property(self, "__type_subscriptions")
        ogt.destroy_property(self, "__type_widgets")

    # ----------------------------------------------------------------------
    def __on_attribute_description_changed(self, new_description: str):
        """Callback that runs when the attribute description was edited"""
        ogt.dbg_ui(f"_on_attribute_description_changed({new_description})")
        self.__controller.description = new_description

    def __on_attribute_name_changed(self, new_name: str):
        """Callback that runs when the attribute name was edited"""
        ogt.dbg_ui(f"_on_attribute_name_changed({new_name})")
        self.__controller.name = new_name
        self.__frame.title = new_name

    def __on_attribute_ui_name_changed(self, new_ui_name: str):
        """Callback that runs when the attribute name was edited"""
        ogt.dbg_ui(f"_on_attribute_ui_name_changed({new_ui_name})")
        self.__controller.ui_name = new_ui_name

    def __on_attribute_default_changed(self, new_default: str):
        """Callback that runs when the attribute default was edited"""
        ogt.dbg_ui(f"_on_attribute_default_changed({new_default})")
        self.__controller.default = new_default

    def _on_remove_attribute(self):
        """Callback that runs when this attribute was removed via the remove button"""
        self.__controller.on_remove_attribute()
        # The frame rebuild will take care of destroying this view

    def __update_default(self):
        """Update the value in the default widget"""
        self.__widget_models[ID_ATTR_DEFAULT].set_value(json.dumps(self.__controller.default))

    def __on_union_types_changed(self, new_union_types_str: str):
        """Callback that runs when the attribute's union types were edited"""
        ogt.dbg_ui(f"union_types changed ({new_union_types_str})")
        # Format the input
        new_union_types = [union_type.strip() for union_type in new_union_types_str.strip(" ,\t\n").split(",")]
        new_union_types_str = ", ".join(new_union_types)
        self.__controller.union_types = new_union_types
        # Replace input box with formatted text if needed
        if self.__widget_models[ID_ATTR_UNION_TYPES].as_string != new_union_types_str:
            ogt.dbg_ui(f"Setting union types input to ({new_union_types_str})")
            self.__widget_models[ID_ATTR_UNION_TYPES].set_value(new_union_types_str)
            # Run end_edit to reset the prompt if needed
            self.__widget_models[ID_ATTR_UNION_TYPES].end_edit()

    # ----------------------------------------------------------------------
    def __register_ghost_info(self, ghost_info: GhostedWidgetInfo, widget_name: str, prompt_widget_name: str):
        """Add the ghost widget information to the model data"""
        self.__subscriptions[widget_name + "_begin"] = ghost_info.begin_subscription
        self.__subscriptions[widget_name + "_end"] = ghost_info.end_subscription
        self.__widgets[widget_name] = ghost_info.widget
        self.__widget_models[widget_name] = ghost_info.model
        self.__widgets[prompt_widget_name] = ghost_info.prompt_widget

    # ----------------------------------------------------------------------
    def __build_name_ui(self):
        """Build the contents implementing the attribute name editing widget"""
        ghost_info = ghost_text(
            label="Name:",
            tooltip=TOOLTIPS[ID_ATTR_NAME],
            widget_id=f"{self.__controller.name}_name",
            initial_value=self.__controller.name,
            ghosted_text="Enter Attribute Name...",
            change_callback=self.__on_attribute_name_changed,
            validation=(partial(is_attribute_name_valid, self.__controller.attribute_group), ogn.ATTR_NAME_REQUIREMENT),
        )
        self.__register_ghost_info(ghost_info, ID_ATTR_NAME, ID_ATTR_NAME_PROMPT)

    # ----------------------------------------------------------------------
    def __build_ui_name_ui(self):
        """Build the contents implementing the attribute user-friendly name editing widget"""
        ghost_info = ghost_text(
            label="UI Name:",
            tooltip=TOOLTIPS[ID_UI_ATTR_NAME],
            widget_id=f"{self.__controller.name}_ui_name",
            initial_value=self.__controller.ui_name,
            ghosted_text="Enter User-Friendly Attribute Name...",
            change_callback=self.__on_attribute_ui_name_changed,
            validation=(is_attribute_ui_name_valid, ogn.ATTR_UI_NAME_REQUIREMENT),
        )
        self.__register_ghost_info(ghost_info, ID_UI_ATTR_NAME, ID_UI_ATTR_NAME_PROMPT)

    # ----------------------------------------------------------------------
    def __build_description_ui(self):
        """Build the contents implementing the attribute description editing widget"""
        ghost_info = ghost_text(
            label="Description:",
            tooltip=TOOLTIPS[ID_ATTR_DESCRIPTION],
            widget_id=f"{self.__controller.name}_descripton",
            initial_value=self.__controller.description,
            ghosted_text="Enter Attribute Description...",
            change_callback=self.__on_attribute_description_changed,
        )
        self.__register_ghost_info(ghost_info, ID_ATTR_DESCRIPTION, ID_ATTR_DESCRIPTION_PROMPT)

    # ----------------------------------------------------------------------
    def __build_default_ui(self):
        """Build the contents implementing the attribute default value editing widget"""
        ghost_info = ghost_text(
            label="Default:",
            tooltip=TOOLTIPS[ID_ATTR_DEFAULT],
            widget_id=f"{self.__controller.name}_default",
            initial_value=str(self.__controller.default),
            ghosted_text="Enter Attribute Default...",
            change_callback=self.__on_attribute_default_changed,
        )
        self.__register_ghost_info(ghost_info, ID_ATTR_DEFAULT, ID_ATTR_DEFAULT_PROMPT)

    # ----------------------------------------------------------------------
    def __on_attribute_array_changed(self, model):
        """Callback executed when the checkbox for the array type is clicked"""
        ogt.dbg_ui("_on_attribute_array_changed()")
        new_array_setting = model.as_bool
        self.__controller.array_depth = 1 if new_array_setting else 0
        self.__update_default()

    # ----------------------------------------------------------------------
    def __on_tuple_count_changed(self, new_tuple_count: int):
        """Callback executed when a new tuple count is selected from the dropdown."""
        ogt.dbg_ui("__on_tuple_count_changed")
        self.__controller.tuple_count = new_tuple_count
        self.__update_default()

    # ---------------------------------------------------------------------
    def __on_base_type_changed(self, new_base_type: str):
        """Callback executed when a new base type is selected from the dropdown."""
        ogt.dbg_ui("__on_base_type_changed")
        # Support extended attribute union groups
        if new_base_type in ogn.ATTRIBUTE_UNION_GROUPS:
            self.__on_base_type_changed("union")
            self.__on_union_types_changed(new_base_type)
            return
        # Show / hide the union types editor
        self.__set_union_type_ui_visibility(new_base_type == "union")
        # Update defaults
        has_default = new_base_type not in ["any", "bundle", "union"]
        self.__widgets[ID_ATTR_DEFAULT].enabled = has_default
        self.__widgets[ID_ATTR_DEFAULT_PROMPT].enabled = has_default
        if not has_default:
            self.__controller.default = None
        self.__controller.base_type = new_base_type
        self.__update_default()
        # Use the old value of the union types field if available
        if new_base_type == "union" and self.__widget_models[ID_ATTR_UNION_TYPES].as_string:
            self.__on_union_types_changed(self.__widget_models[ID_ATTR_UNION_TYPES].as_string)

    # ----------------------------------------------------------------------
    def __rebuild_type_ui(self):
        """Build the contents implementing the attribute type editing widget"""
        self.destroy_type_ui_frame()
        with name_value_hstack():
            name_value_label("Attribute Type:", TOOLTIPS[ID_ATTR_FRAME_TYPE])
            with ui.HStack(spacing=5):
                ui.Label("Base Type:", tooltip="Basic data element type")
                self.__type_managers[ID_ATTR_BASE_TYPE] = AttributeBaseTypeManager(
                    self.__controller, self.__on_base_type_changed
                )
                if self.__controller.base_type not in ["union", "any"]:
                    ui.Label("Tuple Count:", tooltip="Number of elements in a tuple, e.g. 3 for a float[3]")
                    self.__type_managers[ID_ATTR_TUPLE_COUNT] = AttributeTupleCountManager(
                        self.__controller, self.__on_tuple_count_changed
                    )

                    ui.Label("Array:", tooltip=TOOLTIPS[ID_ATTR_TYPE_ARRAY_DEPTH], alignment=ui.Alignment.RIGHT_CENTER)
                    model = ui.SimpleIntModel(self.__controller.array_depth)
                    self.__type_subscriptions[ID_ATTR_TYPE_ARRAY_DEPTH] = model.subscribe_value_changed_fn(
                        self.__on_attribute_array_changed
                    )
                    widget = ui.CheckBox(
                        model=model,
                        name=ID_ATTR_TYPE_ARRAY_DEPTH,
                        width=0,
                        style_type_name_override="WhiteCheck",
                        alignment=ui.Alignment.LEFT_CENTER,
                        enabled=1 in self.__controller.array_depths_supported,
                    )
                    self.__type_widgets[ID_ATTR_TYPE_ARRAY_DEPTH] = widget
                else:
                    # Spacers to left-justify the base type ComboBox.
                    # 3 spacers is the same space that the tuple count and array elements take up
                    ui.Spacer()
                    ui.Spacer()
                    ui.Spacer()

    # ----------------------------------------------------------------------
    def __on_controller_change(self, caller):
        """Callback executed when the controller data changes"""
        self.__widgets[ID_ATTR_FRAME_TYPE].rebuild()

    # ----------------------------------------------------------------------
    def __build_type_ui(self):
        """Build the contents implementing the attribute type editing widget. In a frame because it is dynamic"""
        self.__widgets[ID_ATTR_FRAME_TYPE] = ui.Frame()
        self.__widgets[ID_ATTR_FRAME_TYPE].set_build_fn(self.__rebuild_type_ui)
        self.__controller.add_change_callback(self.__on_controller_change)

    # ----------------------------------------------------------------------
    def __set_union_type_ui_visibility(self, visible: bool):
        self.__widgets[ID_ATTR_FRAME_UNION_TYPES].visible = visible

    # ----------------------------------------------------------------------
    def __on_union_adder_selected(self, new_type):
        ogt.dbg_ui(f"_on_union_adder_selected({new_type})")
        union_types_str = self.__widget_models[ID_ATTR_UNION_TYPES].as_string
        if new_type not in union_types_str:
            self.__on_union_types_changed(union_types_str + ", " + new_type)

    # ----------------------------------------------------------------------
    def __rebuild_union_types_ui(self):
        with name_value_hstack():
            ghost_info = ghost_text(
                label="Union Types:",
                tooltip=TOOLTIPS[ID_ATTR_UNION_TYPES],
                widget_id=f"{self.__controller.name}_union_types",
                initial_value=", ".join(self.__controller.union_types),
                ghosted_text="Enter comma-separated list of union types",
                change_callback=self.__on_union_types_changed,
                validation=None,
            )
            self.__register_ghost_info(ghost_info, ID_ATTR_UNION_TYPES, ID_ATTR_UNION_TYPES_PROMPT)
            self.__widgets[ID_ATTR_UNION_TYPE_ADDER] = AttributeUnionTypeAdderManager(
                self.__controller, self.__on_union_adder_selected
            )
            self.__set_union_type_ui_visibility(self.__controller.base_type == "union")

    # ----------------------------------------------------------------------
    def __build_union_types_ui(self):
        """
        Build the contents implementing the union type editing widget.
        These widgets are selectively enabled when the attribute type is a union.
        """
        # Put it in a frame so it's easy to hide / show as needed
        self.__widgets[ID_ATTR_FRAME_UNION_TYPES] = ui.Frame()
        self.__widgets[ID_ATTR_FRAME_UNION_TYPES].set_build_fn(self.__rebuild_union_types_ui)

    # ----------------------------------------------------------------------
    def __build_memory_type_ui(self):
        """Build the contents implementing the attribute memory type editing widget"""
        self.__managers[ID_ATTR_MEMORY_TYPE] = MemoryTypeManager(self.__controller)

    # # ----------------------------------------------------------------------
    # def __rebuild_min_max_ui(self):
    #     """
    #     Build the contents implementing the attribute minimum and maximum editing widget.
    #     These widgets are selectively enabled when the attribute type is one that allows for min/max values.
    #     """
    #     type_manager = self.__controller.attribute_manager
    #     try:
    #         visibility = True
    #         numeric_type = type_manager.numeric_type()
    #         if numeric_type == ogn.NumericAttributeManager.TYPE_INTEGER:
    #             is_integer = True
    #         elif numeric_type == ogn.NumericAttributeManager.TYPE_UNSIGNED_INTEGER:
    #             is_integer = True
    #         elif numeric_type == ogn.NumericAttributeManager.TYPE_DECIMAL:
    #             is_integer = False
    #         else:
    #             raise AttributeError("Not really a numeric type")
    #         name_value_label("Range:", TOOLTIPS[ID_ATTR_FRAME_RANGE])
    #         ui.Label("Minimum:", tooltip=TOOLTIPS[ID_ATTR_MINIMUM])
    #         if is_integer:
    #             model = ui.SimpleIntModel(self.__controller.minimum)
    #             widget = ui.IntField(
    #                 alignment=ui.Alignment.RIGHT_BOTTOM,
    #                 model=model,
    #                 name=ID_ATTR_MINIMUM,
    #                 tooltip=TOOLTIPS[ID_ATTR_MINIMUM],
    #             )
    #             subscription = widget.subscribe_value_changed_fn(self.__controller.on_int_minimum_changed)
    #         else:
    #             model = ui.SimpleFloatModel(self.__controller.minimum)
    #             widget = ui.FloatField(
    #                 alignment=ui.Alignment.RIGHT_BOTTOM,
    #                 model=model,
    #                 name=ID_ATTR_MINIMUM,
    #                 tooltip=TOOLTIPS[ID_ATTR_MINIMUM],
    #             )
    #             subscription = widget.subscribe_value_changed_fn(self.__controller.on_float_minimum_changed)
    #         self.__widgets[ID_ATTR_MINIMUM] = widget
    #         self.__subscriptions[ID_ATTR_MINIMUM] = subscription
    #         ui.Label("Maximum:", tooltip=TOOLTIPS[ID_ATTR_MAXIMUM])
    #         if is_integer:
    #             model = ui.SimpleIntModel(self.__controller.maximum)
    #             widget = ui.IntField(
    #                 alignment=ui.Alignment.RIGHT_BOTTOM,
    #                 model=model,
    #                 name=ID_ATTR_MAXIMUM,
    #                 tooltip=TOOLTIPS[ID_ATTR_MAXIMUM],
    #             )
    #             subscription = widget.subscribe_value_changed_fn(self.__controller.on_int_maximum_changed)
    #         else:
    #             model = ui.SimpleFloatModel(self.__controller.maximum)
    #             widget = ui.FloatField(
    #                 alignment=ui.Alignment.RIGHT_BOTTOM,
    #                 model=model,
    #                 name=ID_ATTR_MAXIMUM,
    #                 tooltip=TOOLTIPS[ID_ATTR_MAXIMUM],
    #             )
    #             subscription = widget.subscribe_value_changed_fn(self.__controller.on_float_maximum_changed)
    #         self.__widgets[ID_ATTR_MAXIMUM] = widget
    #         self.__subscriptions[ID_ATTR_MAXIMUM] = subscription

    #     except AttributeError:
    #         visibility = False
    #     self.__widgets[ID_ATTR_FRAME_RANGE].visible = visibility

    # # ----------------------------------------------------------------------
    # def __build_min_max_ui(self) -> bool:
    #     """
    #     Build the contents implementing the attribute minimum and maximum editing widget.
    #     These widgets are selectively enabled when the attribute type is one that allows for min/max values.

    #     Returns:
    #         True if the UI elements should be visible for the current attribute
    #     """
    #     self.__widgets[ID_ATTR_FRAME_RANGE] = ui.Frame()
    #     self.__widgets[ID_ATTR_FRAME_RANGE].set_build_fn(self.__rebuild_frame_min_max_ui)

    # ----------------------------------------------------------------------
    # def __on_optional_changed(self, model):
    #     """Callback executed when the checkbox for the optional flag is clicked"""
    #     ogt.dbg_ui("_on_optional_changed()")
    #     self.__controller.optional = model.as_bool

    # ----------------------------------------------------------------------
    # def __build_optional_ui(self):
    #     """Build the contents implementing the optional checkbox widget"""
    #     name_value_label("Optional:", TOOLTIPS[ID_ATTR_OPTIONAL])
    #     model = ui.SimpleIntModel(self.__controller.optional)
    #     subscription = model.subscribe_value_changed_fn(self.__on_optional_changed)
    #     widget = ui.CheckBox(
    #         model=model,
    #         name=ID_ATTR_OPTIONAL,
    #         width=0,
    #         style_type_name_override="WhiteCheck",
    #         alignment=ui.Alignment.LEFT_CENTER,
    #         enabled=self.__controller.optional,
    #     )
    #     self.__widgets[ID_ATTR_OPTIONAL] = widget
    #     self.__subscriptions[ID_ATTR_OPTIONAL] = subscription

    # ----------------------------------------------------------------------
    def __build_metadata_ui(self):
        """Build the contents implementing the attribute metadata editing widget"""
        self.__managers[ID_MGR_ATTR_METADATA] = MetadataManager(self.__controller)

    # ----------------------------------------------------------------------
    def __rebuild_frame(self):
        """Rebuild the contents underneath the main attribute frame"""
        self.destroy_frame_contents()
        with ui.VStack(**VSTACK_ARGS):

            with name_value_hstack():
                self.__build_name_ui()

            with name_value_hstack():
                self.__build_description_ui()

            self.__build_type_ui()

            self.__build_union_types_ui()

            with name_value_hstack():
                self.__build_ui_name_ui()

            with name_value_hstack():
                self.__build_memory_type_ui()

            with name_value_hstack():
                self.__build_default_ui()

            # It's unclear what value if any these provide so they are omitted from the UI for now.
            # min_max_stack = name_value_hstack()
            # with min_max_stack:
            #     min_max_stack.visible = self.__build_min_max_ui()
            # with name_value_hstack():
            #     self.__build_optional_ui()

            with name_value_hstack():
                self.__build_metadata_ui()


# ================================================================================
class AttributeListModel:
    """
    Manager for an entire list of attribute description data. It's used as an intermediary between the
    input and output attribute lists and the individual attribute data in AttributePropertiesModel

    External Properties
        attribute_group
        is_output
        models

    Internal Properties:
        __attribute_group: Enum with the attribute's group (input, output, or state)
        __is_output: bool True when the attributes owned by this list are output types
        __models: List of AttributePropertiesModels for each attribute in the list
    """

    def __init__(self, attribute_data: Optional[Dict], attribute_group: str):
        """
        Create an initial attribute model from the list of attributes (empty list if None)

        Args:
            attribute_data: Dictionary of the initial attribute list
            attribute_group: Enum with the attribute's group (input, output, or state)
        """
        self.__attribute_group = attribute_group
        self.__models = []
        self.__is_output = False
        if attribute_data is not None:
            for name, data in attribute_data.items():
                self.__models.append(AttributePropertiesModel(name, attribute_group, data))

    def destroy(self):
        """Called when this model is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__models = []  # These are owned by their respective controllers
        self.__attribute_group = None

    # ----------------------------------------------------------------------
    def ogn_data(self) -> Dict:
        """Return a dictionary representing the list of attributes in .ogn format, None if the list is empty"""
        if self.__models:
            raw_data = {}
            for model in self.__models:
                raw_data.update(model.ogn_data)
            return {attribute_key_from_group(self.__attribute_group): raw_data}
        return None

    # ----------------------------------------------------------------------
    def all_attribute_names(self) -> List[str]:
        """Returns a list of all currently existing attribute names"""
        names = []
        for model in self.__models:
            names.append(model.name)
        return names

    # ----------------------------------------------------------------------
    def add_new_attribute(self) -> AttributePropertiesModel:
        """Create a new default attribute and add it to the list

        Returns:
            Newly created attribute properties model
        """
        attribute_key = attribute_key_from_group(self.__attribute_group)
        default_name = find_unique_name(f"new_{attribute_key[0:-1]}", self.all_attribute_names())
        default_data = {"type": "int", "description": ""}
        self.__is_output = self.__attribute_group == ogn.OUTPUT_GROUP
        if not self.__is_output:
            default_data["default"] = 0
        self.__models.append(AttributePropertiesModel(default_name, self.__attribute_group, default_data))
        return self.__models[-1]

    # ----------------------------------------------------------------------
    def remove_attribute(self, attribute_model):
        """Remove the attribute encapsulated in the given model"""
        try:
            self.__models.remove(attribute_model)
        except ValueError:
            log_warn(f"Failed to remove attribute model for {attribute_model.name}")

    # ----------------------------------------------------------------------
    @property
    def attribute_group(self):
        """Returns the group to which these attributes belong"""
        return self.__attribute_group

    # ----------------------------------------------------------------------
    @property
    def models(self):
        """Returns the list of models managing individual attributes"""
        return self.__models

    # ----------------------------------------------------------------------
    @property
    def is_output(self):
        """Returns whether this list represents output attributes or not"""
        return self.__is_output


# ================================================================================
class AttributeListController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    External Properties:
        all_attribute_controllers
        all_attribute_names
        attribute_group
        is_output

    Internal Properties:
        __controllers: List of individual attribute property controllers
        __model: The model this class controls
    """

    def __init__(self, model: AttributeListModel):
        """Initialize the controller with the model it will control"""
        super().__init__()
        self.__model = model
        self.__controllers = [AttributePropertiesController(model, self) for model in self.__model.models]
        # Be sure to forward all change callbacks from the children to this parent
        for controller in self.__controllers:
            controller.forward_callbacks_to(self)

    def destroy(self):
        """Called when the controller is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        ogt.destroy_property(self, "__controllers")
        self.__model = None

    # ----------------------------------------------------------------------
    def on_name_change(self, old_name: str, new_name: str):
        """Callback that executes when the individual attribute model wants to change its name.

        Raises:
            AttributeError: If the new name is a duplicate of an existing name
        """
        # If the name is not changing assume that no duplicates exist
        if old_name == new_name:
            return

        for controller in self.__controllers:
            if controller.name == new_name:
                raise AttributeError(f"Attribute with name {new_name} already exists. Names must be unique.")

    # ----------------------------------------------------------------------
    def on_new_attribute(self):
        """Callback that executes when the view wants to add a new attribute
        Insert a new attribute with some default values into the OGN data.
        """
        ogt.dbg_ui(f"Adding a new attribute in {attribute_key_from_group(self.attribute_group)}")
        new_model = self.__model.add_new_attribute()
        attribute_controller = AttributePropertiesController(new_model, self)
        self.__controllers.append(attribute_controller)
        attribute_controller.forward_callbacks_to(self)
        self.on_change(AttributeAddedMessage(self, attribute_controller.name, attribute_controller.attribute_group))

    # ----------------------------------------------------------------------
    def on_remove_attribute(self, attribute_controller: AttributePropertiesController):
        """Callback that executes when the given controller's attribute was removed"""
        ogt.dbg_ui(f"Removing an existing attribute from {attribute_key_from_group(self.attribute_group)}")
        try:
            (name, group) = (attribute_controller.name, attribute_controller.attribute_group)
            self.__model.remove_attribute(attribute_controller._model)  # noqa: PLW0212
            attribute_controller.destroy()
            self.__controllers.remove(attribute_controller)
            self.on_change(AttributeRemovedMessage(self, name, group))
        except ValueError:
            log_warn(f"Failed removal of controller for {attribute_controller.name}")

    # ----------------------------------------------------------------------
    @property
    def attribute_group(self):
        """Returns the group to which these attributes belong"""
        return self.__model.attribute_group

    # ----------------------------------------------------------------------
    @property
    def is_output(self):
        """Returns whether this list represents output attributes or not"""
        return self.__model.is_output

    # ----------------------------------------------------------------------
    @property
    def all_attribute_controllers(self) -> List[AttributePropertiesController]:
        """Returns the list of all controllers for attributes in this list"""
        return self.__controllers

    # ----------------------------------------------------------------------
    @property
    def all_attribute_names(self) -> List[str]:
        """Returns a list of all currently existing attribute names"""
        return self.__model.all_attribute_names


# ================================================================================
class AttributeListView:
    """UI for a list of attributes

    Internal Properties:
        __add_button: Widget managing creation of a new attribute
        __attribute_views: Per-attribute set of views, keyed by attribute name
        __controller: The controller used to manipulate the model's data
        __frame: Main frame for this attribute's interface
        __widgets: Dictionary of ID:Widget for the components of the attribute's frame
    """

    def __init__(self, controller: AttributeListController):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__add_button = None
        self.__controller = controller
        self.__attribute_views = {}
        if controller.attribute_group == ogn.INPUT_GROUP:
            title = "Input Attributes"
        elif controller.attribute_group == ogn.OUTPUT_GROUP:
            title = "Output Attributes"
        else:
            title = "State Attributes"
        self.__frame = ui.CollapsableFrame(title=title, collapsed=True)
        self.__frame.set_build_fn(self.__rebuild_frame)
        self.__controller.add_change_callback(self.__on_list_change)

    def destroy(self):
        """Called when the view is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        with suppress(AttributeError):
            self.__frame.set_build_fn(None)
        with suppress(ValueError):
            self.__controller.remove_change_callback(self.__on_list_change)
        self.__controller = None
        ogt.destroy_property(self, "__add_button")
        ogt.destroy_property(self, "__frame")
        ogt.destroy_property(self, "__attribute_views")

    # ----------------------------------------------------------------------
    def __on_list_change(self, change_message):
        """Callback executed when a member of the list changes.

        Args:
            change_message: Message with change information
        """
        ogt.dbg_ui(f"List change called on {self.__class__.__name__} with {change_message}")
        # Renaming does not require rebuilding of the attribute frame, other changes do
        if isinstance(change_message, (AttributeAddedMessage, AttributeRemovedMessage)):
            self.__frame.rebuild()

    # ----------------------------------------------------------------------
    def __rebuild_frame(self):
        """Rebuild the contents underneath the main attribute frame"""
        ogt.dbg_ui(f"Rebuilding the frame for {attribute_key_from_group(self.__controller.attribute_group)}")
        ogt.destroy_property(self, "__attribute_views")

        with ui.VStack(**VSTACK_ARGS):
            self.__add_button = DestructibleButton(
                width=20,
                height=20,
                style_type_name_override="AddElement",
                clicked_fn=self.__controller.on_new_attribute,  # noqa: PLW0212
                tooltip="Add a new attribute with default settings",
            )
            assert self.__add_button
            # Reconstruct the list of per-attribute views. Construction instantiates their UI.
            for controller in self.__controller.all_attribute_controllers:
                self.__attribute_views[controller.name] = AttributePropertiesView(controller)
