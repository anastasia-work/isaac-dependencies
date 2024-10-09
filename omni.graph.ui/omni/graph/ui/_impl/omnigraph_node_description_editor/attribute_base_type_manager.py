"""
Manager class for the attribute base type combo box.
"""
from typing import Callable, Optional

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from .ogn_editor_utils import ComboBoxOptions

BaseTypeChangeCallback = Optional[Callable[[str], None]]


# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_BASE_DATA_TYPE = "attributeBaseDataType"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_ATTR_BASE_DATA_TYPE: "Base type of an attribute's data"}


# ======================================================================
class AttributeBaseTypeComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows attribute base data types available

    Internal Properties:
        __controller: Controller managing the type information
        __type_changed_callback: Option callback to execute when a new base type is chosen
        __current_index: Model for the currently selected value
        __subscription: Subscription object for the type change callback
        __items: List of models for each legal value in the combobox
    """

    OPTIONS = sorted(list(ogn.ALL_ATTRIBUTE_TYPES.keys()) + list(ogn.ATTRIBUTE_UNION_GROUPS.keys()))
    OPTION_INDEX = {}
    for (index, attribute_type_name) in enumerate(OPTIONS):
        OPTION_INDEX[attribute_type_name] = index

    def __init__(self, controller, type_changed_callback: BaseTypeChangeCallback = None):
        """Initialize the attribute base type combo box details"""
        super().__init__()
        self.__controller = controller
        self.__current_index = ui.SimpleIntModel()
        self.__type_changed_callback = type_changed_callback
        try:
            self.__current_index.set_value(self.OPTION_INDEX[self.__controller.base_type])
        except KeyError:
            log_warn(f"Initial attribute type {self.__controller.base_type} not recognized")
        self.__subscription = self.__current_index.subscribe_value_changed_fn(self.__on_base_type_changed)
        assert self.__subscription
        # Using a list comprehension instead of values() guarantees the pre-sorted ordering
        self.__items = [ComboBoxOptions(attribute_type_name) for attribute_type_name in self.OPTIONS]

    def destroy(self):
        """Called when the widget is being destroyed, to remove callbacks"""
        self.__controller = None
        self.__subscription = None
        self.__type_changed_callback = None
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

    def __on_base_type_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new base type was selected"""
        self._item_changed(None)
        try:
            ogt.dbg_ui(f"Set attribute base type to {new_value.as_int}")
            new_type_name = self.OPTIONS[new_value.as_int]
            ogt.dbg_ui(f"Type name is {new_type_name}")
            if self.__type_changed_callback:
                self.__type_changed_callback(new_type_name)
        except KeyError:
            log_warn(f"Base type index change was rejected - {new_value.as_int} not found")
        except AttributeError as error:
            log_warn(f"base type '{new_value.as_int}' on attribute '{self.__controller.name}' was rejected - {error}")


# ======================================================================
class AttributeBaseTypeManager:
    """Handle the combo box and responses for getting and setting attribute base type values

    Internal Properties:
        __controller: Controller for the data of the attribute this will modify
        __widget: ComboBox widget controlling the base type
        __widget_model: Model for the ComboBox value
    """

    def __init__(self, controller, type_changed_callback: BaseTypeChangeCallback = None):
        """Set up the initial UI and model

        Args:
            controller: AttributePropertiesController in charge of the data for the attribute being managed
        """
        self.__controller = controller
        assert self.__controller
        self.__widget_model = AttributeBaseTypeComboBox(controller, type_changed_callback)
        self.__widget = ui.ComboBox(
            self.__widget_model,
            alignment=ui.Alignment.LEFT_CENTER,
            width=80,
            name=ID_ATTR_BASE_DATA_TYPE,
            tooltip=TOOLTIPS[ID_ATTR_BASE_DATA_TYPE],
        )
        assert self.__widget

    def destroy(self):
        """Called to clean up when the widget is being destroyed"""
        self.__controller = None
        ogt.destroy_property(self, "__widget")
        ogt.destroy_property(self, "__widget_model")
