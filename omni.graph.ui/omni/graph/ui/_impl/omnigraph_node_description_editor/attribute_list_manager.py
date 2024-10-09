"""
Manager class for the combo box that lets you select from a list of attribute names.
"""
from typing import Callable, List

import omni.graph.tools as ogt
from carb import log_warn
from omni import ui

from .ogn_editor_utils import ComboBoxOptions

# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_LIST = "attributeList"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_ATTR_LIST: "Attribute name (without namespace)"}


# ======================================================================
class AttributeListComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows attribute base data types available"""

    def __init__(self, initial_value: str, available_attribute_names: List[str]):
        """Initialize the attribute base type combo box details"""
        super().__init__()
        self.__available_attribute_names = available_attribute_names
        self.__current_index = ui.SimpleIntModel()
        self.item_selected_callback = None
        try:
            self.__current_index.set_value(available_attribute_names.index(initial_value))
        except ValueError:
            log_warn(f"Initial attribute type {initial_value} not recognized")
        self.__old_value = self.__current_index.as_int
        self.__current_index.add_value_changed_fn(self.__on_attribute_selected)
        # Using a list comprehension instead of values() guarantees the sorted ordering
        self.__items = [ComboBoxOptions(attribute_type_name) for attribute_type_name in available_attribute_names]

    def destroy(self):
        """Cleanup when the widget is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__available_attribute_names = None
        ogt.destroy_property(self, "__current_index")
        ogt.destroy_property(self, "__items")

    def get_item_children(self, item):
        """Get the model children of this item"""
        return self.__items

    def get_item_value_model(self, item, column_id: int):
        """Get the model at the specified column_id"""
        if item is None:
            return self.__current_index
        return item.model

    def add_child(self, child_name: str):
        """Callback invoked when a child is added"""
        self.__items.append(ComboBoxOptions(child_name))
        self._item_changed(None)

    def rename_child(self, old_name: str, new_name: str):
        """Callback invoked when a child is renamed"""
        for item in self.__items:
            if item.model.as_string == old_name:
                ogt.dbg_ui("Found combo box item to rename")
                item.model.set_value(new_name)
                break
        self._item_changed(None)

    def remove_child(self, child_name: str):
        """Callback invoked when a child is removed to adjust for the fact that higher indexes must decrement"""
        selected = self.__current_index.as_int
        for (index, item) in enumerate(self.__items):
            if item.model.as_string == child_name:
                ogt.dbg_ui(f"Removing combo box item {index} = {child_name}")
                if selected > index:
                    self.__current_index.set_value(selected - 1)
                self.__items.pop(index)
                break
            index += 1
        self._item_changed(None)

    def __on_attribute_selected(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new base type was selected"""
        try:
            ogt.dbg_ui(f"Set selected attribute to {new_value.as_int} from {self.__current_index.as_int}")
            new_attribute_name = self.__available_attribute_names[new_value.as_int]
            ogt.dbg_ui(f"Type name is {new_attribute_name}")
            if self.item_selected_callback is not None:
                ogt.dbg_ui(f"...calling into {self.item_selected_callback}")
                self.item_selected_callback(new_attribute_name)
            self.__old_value = new_value.as_int
        except ValueError as error:
            log_warn(f"Attribute selection rejected - {error}")
            new_value.set_value(self.__old_value)
        except KeyError as error:
            log_warn(f"Attribute selection could not be found - {error}")
            new_value.set_value(self.__old_value)
        except IndexError:
            log_warn(f"Attribute {new_value.as_int} was selected but there is no such attribute")
            new_value.set_value(self.__old_value)
        self._item_changed(None)


# ======================================================================
class AttributeListManager:
    """Handle the combo box and responses for getting and setting attribute base type values

    Internal Properties:
        __widget: ComboBox widget controlling the base type
        __widget_model: Model for the ComboBox value
    """

    def __init__(self, initial_value: str, available_attribute_names: List[str], item_selected_callback: Callable):
        """Set up the initial UI and model

        Args:
            initial_value: Initially selected value
            available_attribute_names: List of potential names
        """
        self.__widget_model = AttributeListComboBox(initial_value, available_attribute_names)
        self.__widget_model.item_selected_callback = item_selected_callback
        self.__widget = ui.ComboBox(
            self.__widget_model, alignment=ui.Alignment.LEFT_BOTTOM, name=ID_ATTR_LIST, tooltip=TOOLTIPS[ID_ATTR_LIST]
        )
        assert self.__widget

    def destroy(self):
        """Cleanup when the object is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        ogt.destroy_property(self, "__widget")
        ogt.destroy_property(self, "__widget_model")

    def on_child_added(self, child_name: str):
        """Callback invoked when a child is added"""
        self.__widget_model.add_child(child_name)

    def on_child_renamed(self, old_name: str, new_name: str):
        """Callback invoked when a child is renamed"""
        self.__widget_model.rename_child(old_name, new_name)

    def on_child_removed(self, child_name: str):
        """Callback invoked when a child is removed to adjust for the fact that higher indexes must decrement"""
        self.__widget_model.remove_child(child_name)
