"""
Classes and functions relating to the handling of both attribute and node metadata in the OgnNodeDescriptionEditor
"""
from contextlib import suppress
from typing import Callable, Dict, Optional

import carb
import omni.graph.tools as ogt
from omni import ui

from ..style import name_value_hstack, name_value_label  # noqa: PLE0402
from .ogn_editor_utils import DestructibleButton, find_unique_name


# ======================================================================
class NameValueTreeManager:
    """Class that provides a simple interface to ui.TreeView model and delegate management for name/value lists.

    Class Hierarchy Properties:
        _model: NameValueModel containing a single name:value element
        _delegate: EditableDelegate object managing the tree view interaction

    Usage:
        def __on_model_changed(new_dictionary):
            print(f"Model changed to {new_dictionary})
        my_dictionary = {"Hello": "Greeting", "World": "Scope"}
        my_manager = NameValueTreeManager(my_dictionary, __on_model_changed)
        ui.TreeView(my_manager.model)
    """

    # ----------------------------------------------------------------------
    class NameValueModel(ui.AbstractItemModel):
        """Represents the model for name-value table."""

        class NameValueItem(ui.AbstractItem):
            """Single key/value pair in the model, plus the index in the overall model of this item"""

            def __init__(self, key: str, value: str):
                """Initialize both of the models to the key/value pairs"""
                super().__init__()
                self.name_model = ui.SimpleStringModel(key)
                self.value_model = ui.SimpleStringModel(value)

            def destroy(self):
                """Destruction of the underlying models"""
                ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
                ogt.destroy_property(self, "name_model")
                ogt.destroy_property(self, "value_model")

            def __repr__(self):
                """Return a nice representation of the string pair"""
                return f'NameValueModel("{self.name_model.as_string} : {self.value_model.as_string}")'

        # ----------------------------------------------------------------------
        def __init__(self, metadata_values: Dict[str, str]):
            """Initialize the children into sorted tuples from the dictionary"""
            ogt.dbg_ui(f"NameValueModel({metadata_values}))")
            super().__init__()
            self.__children = []
            self.__metadata_values = {}
            self.set_values(metadata_values)

        def destroy(self):
            """Cleanup when the model is being destroyed"""
            ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
            self.__metadata_values = None
            ogt.destroy_property(self, "__children")

        def set_values(self, metadata_values: Dict[str, str]):
            """Define the children based on the new dictionary of key/value pairs"""
            ogt.dbg_ui(f"Set values in NameValueModel to {metadata_values}")
            self.__metadata_values = metadata_values
            self.__rebuild_children()

        def __rebuild_children(self):
            """Set the child string list, either for the initial state or after editing"""
            ogt.dbg_ui(f"Rebuilding children from {self.__metadata_values}")
            self.__children = [
                self.NameValueItem(key, self.__metadata_values[key]) for key in sorted(self.__metadata_values.keys())
            ]
            # Insert a blank entry at the begining for adding new values
            self.__children.append(self.NameValueItem("", ""))
            self._item_changed(None)

        def add_child(self):
            """Add a new default child to the list"""
            ogt.dbg_ui("Add a new key/value pair")
            suggested_name = find_unique_name("metadataName", self.__metadata_values)
            self.__metadata_values[suggested_name] = "metadataValue"
            self.__rebuild_children()

        def remove_child(self, key_value: str):
            """Remove the child corresponding to the given item from the list"""
            ogt.dbg_ui(f"Removing key {key_value}")
            try:
                del self.__metadata_values[key_value]
            except KeyError:
                carb.log_error(f"Could not find child with key value of {key_value} for removal")
            self.__rebuild_children()

        def get_item_count(self):
            """Returns the number of children (i.e. rows in the tree widget)."""
            return len(self.__children)

        def get_item_children(self, item):
            """Returns all the children when the widget asks it."""
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return the empty list.
            return item.model if item is not None else self.__children

        def get_item_value_model_count(self, item):
            """The number of columns, always 2 since the data is key/value pairs"""
            return 3

        def get_item_value_model(self, item, column_id: int):
            """Returns the model for the item's column. Only columns 0 and 1 will be requested"""
            return [item.name_model, item.name_model, item.value_model][column_id]

    # ----------------------------------------------------------------------
    class EditableDelegate(ui.AbstractItemDelegate):
        """
        Delegate is the representation layer. TreeView calls the methods
        of the delegate to create custom widgets for each item.

        Internal Properties:
            __add_button: Widget managing the button to add new elements
            __remove_buttons: Widget list managing the button to remove existing elements
            __stack_widgets: Widget list managing the editable fields
            __subscription: Subscription object for the callback on end of an edit
            __value_change_cb: Function to call when any values change
        """

        def __init__(self, value_change_cb: Callable):
            """Initialize the state with no subscription on the end edit; it will be used later"""
            super().__init__()
            self.__add_button = None
            self.__remove_buttons = []
            self.__subscription = None
            self.__value_change_cb = value_change_cb
            self.__stack_widgets = []

        def destroy(self):
            """Release any hanging references"""
            ogt.destroy_property(self, "__add_button")
            ogt.destroy_property(self, "__remove_buttons")
            self.__subscription = None
            self.__value_change_cb = None
            with suppress(AttributeError):
                for stack_widget in self.__stack_widgets:
                    stack_widget.set_mouse_double_clicked_fn(None)
            self.__stack_widgets = []

        def build_branch(self, model, item, column_id: int, level: int, expanded: bool):
            """Create a branch widget that opens or closes subtree"""

        def build_header(self, column_id: int):
            """Set up the header entry at the named column"""
            ogt.dbg_ui(f"Build header for column {column_id}")
            header_style = "TreeView.Header"
            if column_id == 0:
                ui.Label("", width=20, style_type_name_override=header_style)
            else:
                ui.Label("Name" if column_id == 1 else "Value", style_type_name_override=header_style)

        def __on_add_item(self, model):
            """Callback hit when the button to add a new item was pressed"""
            ogt.dbg_ui("Add new item")
            model.add_child()
            if self.__value_change_cb is not None:
                self.__value_change_cb(model)

        def __on_remove_item(self, model, item):
            """Callback hit when the button to remove an existing item was pressed"""
            ogt.dbg_ui(f"Remove item '{item.name_model.as_string}'")
            model.remove_child(item.name_model.as_string)
            if self.__value_change_cb is not None:
                self.__value_change_cb(model)

        def __on_double_click(self, button, field, label):
            """Called when the user double-clicked the item in TreeView"""
            if button != 0:
                return

            ogt.dbg_ui(f"Double click on {label}")

            # Make Field visible when double clicked
            field.visible = True
            field.focus_keyboard()
            # When editing is finished (enter pressed of mouse clicked outside of the viewport)
            self.__subscription = field.model.subscribe_end_edit_fn(
                lambda m, f=field, l=label: self.__on_end_edit(m, f, l)
            )
            assert self.__subscription

        def __on_end_edit(self, model, field, label):
            """Called when the user is editing the item and pressed Enter or clicked outside of the item"""
            ogt.dbg_ui(f"Ended edit of '{label.text}' as '{model.as_string}'")
            field.visible = False
            label.text = model.as_string
            # TODO: Verify that this is not duplicating an existing entry
            self.__subscription = None
            if self.__value_change_cb is not None:
                self.__value_change_cb(model)

        def build_widget(self, model, item, column_id: int, level: int, expanded: bool):
            """Create a widget per column per item"""
            ogt.dbg_ui(
                f"Build widget on {model.__class__.__name__} for item {item}"
                f" in column {column_id} at {level} expansion {expanded}"
            )
            if column_id == 0:
                if item.name_model.as_string:
                    self.__remove_buttons.append(
                        DestructibleButton(
                            width=20,
                            height=20,
                            style_type_name_override="RemoveElement",
                            clicked_fn=lambda: self.__on_remove_item(model, item),
                        )
                    )
                else:
                    self.__add_button = DestructibleButton(
                        width=20,
                        height=20,
                        style_type_name_override="AddElement",
                        clicked_fn=lambda: self.__on_add_item(model),
                    )
                    assert self.__add_button
            else:
                stack = ui.ZStack(height=20)
                with stack:
                    value_model = model.get_item_value_model(item, column_id)
                    if not item.name_model.as_string:
                        ui.Label("")
                    else:
                        label = ui.Label(value_model.as_string)
                        field = ui.StringField(value_model, visible=False)
                        # Start editing when double clicked
                        stack.set_mouse_double_clicked_fn(
                            lambda x, y, b, m, f=field, l=label: self.__on_double_click(b, f, l)
                        )
                self.__stack_widgets.append(stack)

    # ----------------------------------------------------------------------
    def __init__(self, value_dictionary: Dict[str, str], value_change_cb: Optional[Callable]):
        """Initialize the model and delegate information from the dictionary"""
        self._model = self.NameValueModel(value_dictionary)
        self._delegate = self.EditableDelegate(value_change_cb)

    # ----------------------------------------------------------------------
    def destroy(self):
        """Cleanup when the manager is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self._model = None
        self._delegate.destroy()
        self._delegate = None


# ======================================================================
class MetadataManager(NameValueTreeManager):
    """Class that handles interaction with the node metadata fields."""

    def list_values_changed(self, what):
        new_metadata = {}
        for child in self._model.get_item_children(None):
            if child.name_model.as_string:
                new_metadata[child.name_model.as_string] = child.value_model.as_string
        # Edit the metadata based on new values and reset the widget to keep a single blank row
        self.__controller.filtered_metadata = new_metadata
        self._model.set_values(new_metadata)

    def __init__(self, controller):
        """Initialize the fields inside the given controller and set up the initial frame"""
        super().__init__(controller.filtered_metadata, self.list_values_changed)
        self.__controller = controller
        # Whenever values are updated the metadata list is synchronized with the set of non-empty metadata name models.
        # This allows creation of new metadata values by adding text in the final empty field, and removal
        # of existing metadata values by erasing the name. This avoids extra clutter in the UI with add/remove
        # buttons, though it's important that the tooltip explain this.
        with name_value_hstack():
            name_value_label("Metadata:", "Name/Value pairs to store as metadata.")
            self.__metadata_tree = ui.TreeView(
                self._model,
                delegate=self._delegate,
                root_visible=False,
                header_visible=True,
                height=0,
                column_widths=[30],
            )
            assert self.__metadata_tree

    def destroy(self):
        """Destroy the widget and cleanup the callbacks"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        ogt.destroy_property(self, "__metadata_tree")
        self.__controller = None
