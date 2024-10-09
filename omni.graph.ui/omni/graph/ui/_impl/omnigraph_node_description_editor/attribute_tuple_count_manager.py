"""
Manager class for the attribute tuple count combo box.
"""
from typing import Callable, Optional

import omni.graph.tools as ogt
from carb import log_warn
from omni import ui

from .ogn_editor_utils import ComboBoxOptions

TupleChangeCallback = Optional[Callable[[int], None]]


# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_TYPE_TUPLE_COUNT = "attributeTypeTupleCount"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_ATTR_TYPE_TUPLE_COUNT: "Fixed number of basic elements, e.g. 3 for a float[3]"}


# ======================================================================
class AttributeTupleComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows attribute tuple counts available

    Internal Properties:
        __controller: Controller for the data of the attribute this will modify
        __legal_values: List of tuples the current attribute type supports
        __value_index: Dictionary of tuple-value to combobox index for reverse lookup
        __count_changed_callback: Option callback to execute when a new tuple count is chosen
        __current_index: Model for the currently selected value
        __subscription: Subscription object for the tuple count change callback
        __items: List of models for each legal value in the combobox
    """

    def __init__(self, controller, count_changed_callback: TupleChangeCallback = None):
        """Initialize the attribute tuple count combo box details"""
        super().__init__()
        self.__controller = controller
        self.__legal_values = controller.tuples_supported
        self.__value_index = {}
        for (index, value) in enumerate(self.__legal_values):
            self.__value_index[value] = index
        self.__count_changed_callback = count_changed_callback
        self.__current_index = ui.SimpleIntModel()
        self.__current_index.set_value(self.__value_index[self.__controller.tuple_count])
        self.__subscription = self.__current_index.subscribe_value_changed_fn(self.__on_tuple_count_changed)
        assert self.__subscription
        # Using a list comprehension instead of values() guarantees the ordering
        self.__items = [ComboBoxOptions(str(value)) for value in self.__legal_values]

    def destroy(self):
        """Cleanup when the combo box is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__count_changed_callback = None
        self.__subscription = None
        self.__legal_values = None
        self.__value_index = None
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

    def __on_tuple_count_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new tuple count was selected"""
        self._item_changed(None)
        new_selection = "Unknown"
        try:
            # The combo box new_value is the index of the selection within the list of legal values.
            # Report the index selected in case there isn't a corresponding selection value, then use the selection
            # value to define the new tuple count.
            ogt.dbg_ui(f"Set attribute tuple count to {new_value.as_int}")
            new_selection = self.__legal_values[new_value.as_int]
            if self.__count_changed_callback:
                self.__count_changed_callback(new_selection)
        except AttributeError as error:
            log_warn(f"Tuple count '{new_selection}' on attribute '{self.__controller.name}' was rejected - {error}")


# ======================================================================
class AttributeTupleCountManager:
    """Handle the combo box and responses for getting and setting attribute tuple count values

    Properties:
        __widget: ComboBox widget controlling the tuple count
        __widget_model: Model for the ComboBox value
    """

    def __init__(self, controller, count_changed_callback: TupleChangeCallback = None):
        """Set up the initial UI and model

        Args:
            controller: AttributePropertiesController in charge of the data for the attribute being managed
            count_changed_callback: Optional callback to execute when a new tuple count is chosen
        """
        self.__widget_model = AttributeTupleComboBox(controller, count_changed_callback)
        self.__widget = ui.ComboBox(
            self.__widget_model,
            alignment=ui.Alignment.LEFT_BOTTOM,
            name=ID_ATTR_TYPE_TUPLE_COUNT,
            tooltip=TOOLTIPS[ID_ATTR_TYPE_TUPLE_COUNT],
        )
        assert self.__widget

    def destroy(self):
        """Cleanup when the object is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        ogt.destroy_property(self, "__widget_model")
        ogt.destroy_property(self, "__widget")
