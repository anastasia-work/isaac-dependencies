"""
Classes and functions relating to the handling of a list of attribute values
"""
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional

import omni.graph.tools as ogt
from carb import log_warn
from omni import ui

from .attribute_list_manager import AttributeListManager
from .attribute_properties import AttributeAddedMessage, AttributeRemovedMessage
from .change_management import RenameMessage
from .ogn_editor_utils import DestructibleButton


# ======================================================================
def find_next_unused_name(current_values: Dict[str, Any], available_values: List[str]):
    """Find the first unused name from the available_values

    Args:
        current_values: Dictionary of currently used values; key is the value to be checked
        available_values: Ordered list of available key values to check

    Returns:
        First value in available_values that is not a key in current_values, None if there are none
    """
    for available_value in available_values:
        if available_value not in current_values:
            return available_value
    return None


# ======================================================================
class AttributeNameValueTreeManager:
    """Class that provides a simple interface to ui.TreeView model and delegate management for name/value lists.

    Usage:
        def __on_model_changed(new_dictionary):
            print(f"Model changed to {new_dictionary})
        my_dictionary = {"Hello": "Greeting", "World": "Scope"}
        my_manager = AttributeNameValueTreeManager(my_dictionary, _on_model_changed)
        ui.TreeView(my_manager.model)
    """

    # ----------------------------------------------------------------------
    class AttributeNameValueModel(ui.AbstractItemModel):
        """Represents the model for name-value table."""

        class AttributeNameValueItem(ui.AbstractItem):
            """Single key/value pair in the model, plus the index in the overall model of this item"""

            def __init__(self, key: str, value: Any):
                """Initialize both of the models to the key/value pairs"""
                super().__init__()
                self.name_model = ui.SimpleStringModel(key)
                self.value_model = ui.SimpleStringModel(str(value))

            def __repr__(self):
                """Return a nice representation of the string pair"""
                return f'"{self.name_model.as_string} : {self.value_model.as_string}"'

        # ----------------------------------------------------------------------
        def __init__(self, key_value_pairs: Dict[str, str], available_attribute_names: List[str]):
            """Initialize the children into sorted tuples from the dictionary"""
            ogt.dbg_ui(f"AttributeNameValueModel({key_value_pairs}))")
            super().__init__()
            self.__children = []
            self.__key_value_pairs = {}
            self.set_values(key_value_pairs)
            self.available_attribute_names = available_attribute_names

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def reset(self):
            """Initialize the children to an empty list"""
            ogt.dbg_ui("Reset AttributeNameValueModel")
            self.__key_value_pairs = {}
            self.rebuild_children()

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def set_values(self, key_value_pairs: Dict[str, str]):
            """Define the children based on the new dictionary of key/value pairs"""
            ogt.dbg_ui(f"Set values in AttributeNameValueModel to {key_value_pairs}")
            self.__key_value_pairs = key_value_pairs.copy()
            self.rebuild_children()

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def rebuild_children(self):
            """Set the child string list, either for the initial state or after editing"""
            ogt.dbg_ui("Rebuilding children")
            self.__children = [
                self.AttributeNameValueItem(key, self.__key_value_pairs[key])
                for key in sorted(self.__key_value_pairs.keys())
            ]
            # Insert a blank entry at the begining for adding new values
            self.__children.insert(0, self.AttributeNameValueItem("", ""))
            self.__item_changed(None)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def add_child(self):
            """Add a new default child to the list"""
            ogt.dbg_ui("Add a new key/value pair")
            suggested_name = find_next_unused_name(self.__key_value_pairs, self.available_attribute_names)
            if suggested_name is None:
                log_warn("No unused attributes remain - modify an existing one")
            else:
                self.__key_value_pairs[suggested_name] = ""
                self.rebuild_children()

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def remove_child(self, key_value: str):
            """Remove the child corresponding to the given item from the list

            Raises:
                KeyError: If the key value was not in the list
            """
            ogt.dbg_ui(f"Removing key {key_value}")
            del self.__key_value_pairs[key_value]
            self.rebuild_children()

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def rename_child(self, old_key_name: str, new_key_name: str):
            """Rename the child corresponding to the given item from the list

            Raises:
                KeyError: If the old key value was not in the list
            """
            ogt.dbg_ui(f"Renaming key {old_key_name} to {new_key_name}")
            old_value = self.__key_value_pairs[old_key_name]
            del self.__key_value_pairs[old_key_name]
            self.__key_value_pairs[new_key_name] = old_value
            self.rebuild_children()

        # ----------------------------------------------------------------------
        def on_available_attributes_changed(self, change_message):
            """Callback that executes when the attributes under control"""
            ogt.dbg_ui(f"MODEL: Attribute list changed - {change_message}")
            if isinstance(change_message, RenameMessage):
                with suppress(KeyError):
                    self.rename_child(change_message.old_name, change_message.new_name)
            elif isinstance(change_message, AttributeAddedMessage):
                self.rebuild_children()
            elif isinstance(change_message, AttributeRemovedMessage):
                with suppress(IndexError, KeyError, ValueError):
                    self.remove_child(change_message.attribute_name)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def get_item_count(self):
            """Returns the number of children (i.e. rows in the tree widget)."""
            return len(self.__children)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def get_item_children(self, item):
            """Returns all the children when the widget asks it."""
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return the empty list.
            return item.model if item is not None else self.__children

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def get_item_value_model_count(self, item):
            """The number of columns, always 2 since the data is key/value pairs"""
            return 3

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def get_item_value_model(self, item, column_id: int):
            """Returns the model for the item's column. Only columns 0 and 1 will be requested"""
            return [item.name_model, item.name_model, item.value_model][column_id]

    # ----------------------------------------------------------------------
    class EditableDelegate(ui.AbstractItemDelegate):
        """
        Delegate is the representation layer. TreeView calls the methods
        of the delegate to create custom widgets for each item.

        External Properties:
            add_tooltip: Text for the tooltip on the button to add a new value
            available_attribute_names: List of attributes that can be selected
            subscription: Subscription that watches the value editing
            value_change_cb: Callback to execute when the value has been modified

        Internal Properties:
            __attribute_list_managers: Managers for each of the attribute lists within the test list
        """

        def __init__(self, value_change_cb: Callable, add_tooltip: str, available_attribute_names: List[str]):
            """Initialize the state with no subscription on the end edit; it will be used later"""
            super().__init__()
            self.subscription = None
            self.value_change_cb = value_change_cb
            self.add_tooltip = add_tooltip
            self.available_attribute_names = available_attribute_names
            self.__attribute_list_managers = []
            self.__remove_button = None
            self.__add_button = None

        def destroy(self):
            """Cleanup any hanging references"""
            self.subscription = None
            self.value_change_cb = None
            self.add_tooltip = None
            self.available_attribute_names = None
            ogt.destroy_property(self, "__add_button")
            ogt.destroy_property(self, "__remove_button")
            ogt.destroy_property(self, "__attribute_list_managers")

        def build_branch(self, model, item, column_id: int, level: int, expanded: bool):
            """Create a branch widget that opens or closes subtree - must be defined"""

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def __on_add_item(self, model):
            """Callback hit when the button to add a new item was pressed"""
            ogt.dbg_ui("Add new item")
            model.add_child()
            if self.value_change_cb is not None:
                self.value_change_cb(model)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def __on_remove_item(self, model, item):
            """Callback hit when the button to remove an existing item was pressed"""
            ogt.dbg_ui(f"Remove item '{item.name_model.as_string}'")
            model.remove_child(item.name_model.as_string)
            if self.value_change_cb is not None:
                self.value_change_cb(model)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def __on_attribute_selected(self, new_value: str, model, item):
            """Callback hit when the attribute selector for a particular item has a new value

            Args:
                new_value: Newly selected attribute name for the given item
                model: AttributeNameValueModel controlling the item information
                item: AttributeNameValueItem that generated the change

            Raises:
                ValueError: When the new value is not legal (i.e. the same value exists on another item)
            """
            ogt.dbg_ui(f"Verifying new selection {new_value} from child list {model.get_item_children(None)} on {item}")
            for child in model.get_item_children(None):
                if child != item and child.name_model.as_string == new_value:
                    raise ValueError(f"{new_value} can only appear once in the test data list")

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def build_widget(self, model, item, column_id: int, level: int, expanded: bool):
            """Create a widget per column per item"""
            ogt.dbg_ui(
                f"Build widget on {model.__class__.__name__} for item {item}"
                f" in column {column_id} at {level} expansion {expanded}"
            )
            if column_id == 0:
                if item.name_model.as_string:
                    self.__remove_button = DestructibleButton(
                        width=20,
                        height=20,
                        style_type_name_override="RemoveElement",
                        clicked_fn=lambda: self.__on_remove_item(model, item),
                        tooltip="Remove this value from the test",
                    )
                    assert self.__remove_button
                else:
                    self.__add_button = DestructibleButton(
                        width=20,
                        height=20,
                        style_type_name_override="AddElement",
                        clicked_fn=lambda: self.__on_add_item(model),
                        tooltip=self.add_tooltip,
                    )
                    assert self.__add_button
            elif column_id == 1:
                # First row, marked by empty name_mode, only has the "add" icon
                if item.name_model.as_string:
                    self.__attribute_list_managers.append(
                        AttributeListManager(
                            item.name_model.as_string,
                            self.available_attribute_names,
                            lambda new_selection: self.__on_attribute_selected(new_selection, model, item),
                        )
                    )
                else:
                    ui.Label("")
            elif not item.name_model.as_string:
                # First row, marked by empty name_mode, only has the "add" icon
                ui.Label("")
            else:
                # The default value is a field editable on double-click
                stack = ui.ZStack(height=20)
                with stack:
                    value_model = model.get_item_value_model(item, column_id)
                    label = ui.Label(
                        value_model.as_string,
                        style_type_name_override="LabelOverlay",
                        alignment=ui.Alignment.CENTER_BOTTOM,
                    )
                    field = ui.StringField(value_model, visible=False)
                    # Start editing when double clicked
                    stack.set_mouse_double_clicked_fn(
                        lambda x, y, b, m, f=field, l=label: self.on_double_click(b, f, l)
                    )

        # ----------------------------------------------------------------------
        def on_available_attributes_changed(self, change_message):
            """Callback that executes when the attributes in the available list have changed"""
            ogt.dbg_ui(f"DELEGATE: Attribute list changed - {change_message}")
            if isinstance(change_message, RenameMessage):
                for list_manager in self.__attribute_list_managers:
                    list_manager.on_child_renamed(change_message.old_name, change_message.new_name)
            elif isinstance(change_message, AttributeAddedMessage):
                for list_manager in self.__attribute_list_managers:
                    list_manager.on_child_added(change_message.attribute_name)
            elif isinstance(change_message, AttributeRemovedMessage):
                try:
                    for list_manager in self.__attribute_list_managers:
                        list_manager.on_child_removed(change_message.attribute_name)
                except KeyError:
                    log_warn(f"Tried to remove nonexistent attribute {change_message.attribute_name}")

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def on_double_click(self, button, field, label):
            """Called when the user double-clicked the item in TreeView"""
            if button != 0:
                return

            # Make Field visible when double clicked
            field.visible = True
            field.focus_keyboard()
            # When editing is finished (enter pressed of mouse clicked outside of the viewport)
            self.subscription = field.model.subscribe_end_edit_fn(lambda m, f=field, l=label: self.on_end_edit(m, f, l))

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        def on_end_edit(self, model, field, label):
            """Called when the user is editing the item and pressed Enter or clicked outside of the item"""
            ogt.dbg_ui(f"Ended edit of '{label.text}' as '{model.as_string}'")
            field.visible = False
            label.text = model.as_string
            self.subscription = None
            if self.value_change_cb is not None:
                self.value_change_cb(model)

    # ----------------------------------------------------------------------
    def __init__(self, controller, value_change_cb: Optional[Callable], add_tooltip: str):
        """Initialize the model and delegate information from the dictionary"""
        self.value_change_cb = value_change_cb
        self.original_values = controller.test_data
        # This same list is referenced by the model and delegate for simplicity
        self.available_attribute_names = controller.available_attribute_names()
        controller.add_change_callback(self.on_available_attributes_changed)
        self.model = self.AttributeNameValueModel(self.original_values, self.available_attribute_names)
        self.delegate = self.EditableDelegate(value_change_cb, add_tooltip, self.available_attribute_names)

    # ----------------------------------------------------------------------
    def on_available_attributes_changed(self, change_message):
        """Callback that executes when the attributes in the available list have changed"""
        ogt.dbg_ui(f"MGR: Attribute list changed - {change_message}")
        # Make sure list modifications are made in-place so that every class gets it
        if isinstance(change_message, RenameMessage):
            try:
                attribute_index = self.available_attribute_names.index(change_message.old_name)
                self.available_attribute_names[attribute_index] = change_message.new_name
            except KeyError:
                log_warn(f"Tried to rename nonexistent attribute {change_message.old_name}")
        elif isinstance(change_message, AttributeAddedMessage):
            self.available_attribute_names.append(change_message.attribute_name)
        elif isinstance(change_message, AttributeRemovedMessage):
            try:
                self.available_attribute_names.remove(change_message.attribute_name)
            except KeyError:
                log_warn(f"Tried to remove nonexistent attribute {change_message.attribute_name}")
        else:
            ogt.dbg_ui(f"Unknown test data message ignored -> {change_message}")

        # Update the UI that relies on the list of available attribues
        self.model.on_available_attributes_changed(change_message)
        self.delegate.on_available_attributes_changed(change_message)


# ======================================================================
class TestsDataManager(AttributeNameValueTreeManager):
    """Class that handles interaction with the node metadata fields."""

    def list_values_changed(self, what):
        """Callback invoked when any of the values in the attribute list change"""
        ogt.dbg_ui(f"Changing list values {what}")
        new_values = {}
        for child in self.model.get_item_children(None):
            if child.name_model.as_string:
                new_values[child.name_model.as_string] = child.value_model.as_string

        # Edit the test data based on new values and reset the widget to keep a single blank row.
        # Throws an exception if the test data is not legal, which will skip setting the model values
        try:
            self.__controller.test_data = new_values
            self.model.set_values(new_values)
        except AttributeError:
            pass

    def __init__(self, controller, add_element_tooltip: str):
        """Initialize the fields inside the given controller and set up the initial frame

        Args:
            controller: Controller for the list of attribute values managed by this widget
            add_element_tooltip: Tooltip to use on the "add element" button
        """
        super().__init__(controller, self.list_values_changed, add_element_tooltip)
        self.__controller = controller
        self.attribute_value_tree = None

    # ----------------------------------------------------------------------
    def on_rebuild_ui(self):
        """Callback that runs when the frame in which this widget lives is rebuilding"""
        # Whenever values are updated the metadata list is synchronized with the set of non-empty metadata name models.
        # This allows creation of new metadata values by adding text in the final empty field, and removal
        # of existing metadata values by erasing the name. This avoids extra clutter in the UI with add/remove
        # buttons, though it's important that the tooltip explain this.
        self.attribute_value_tree = ui.TreeView(
            self.model,
            delegate=self.delegate,
            root_visible=False,
            header_visible=False,
            height=0,
            column_widths=[30, ui.Percent(40), ui.Percent(40)],
        )
