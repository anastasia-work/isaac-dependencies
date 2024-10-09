"""
Manager class for the attribute union type adder combo box.
"""
from typing import Callable, Optional

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from .ogn_editor_utils import ComboBoxOptions

SelectionFinishedCallback = Optional[Callable[[str], None]]


# ======================================================================
# ID values for widgets that are editable or need updating
ID_ATTR_UNION_TYPE_ADDER = "attributeUnionTypeAdder"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_ATTR_UNION_TYPE_ADDER: "Add data types to the union accepted by the attribute"}


# ======================================================================
class AttributeUnionTypeAdderComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows data types addable to the attribute union

    Internal Properties:
        __controller: Controller managing the type information
        __type_changed_callback: Option callback to execute when a new base type is chosen
        __current_index: Model for the currently selected value
        __subscription: Subscription object for the type change callback
        __items: List of models for each legal value in the combobox
    """

    OPTIONS = [""] + list(ogn.ATTRIBUTE_UNION_GROUPS.keys())
    OPTIONS += sorted({t for attr_groups in ogn.ATTRIBUTE_UNION_GROUPS.values() for t in attr_groups})

    OPTION_INDEX = {}
    for (index, attribute_type_name) in enumerate(OPTIONS):
        OPTION_INDEX[attribute_type_name] = index

    def __init__(self, controller, selection_finished_callback: SelectionFinishedCallback = None):
        """Initialize the attribute base type combo box details"""
        super().__init__()
        self.__controller = controller
        self.__current_index = ui.SimpleIntModel()
        self.__selection_finished_callback = selection_finished_callback
        self.__current_index.set_value(0)
        self.__subscription = self.__current_index.subscribe_value_changed_fn(self.__on_selection_finished)
        assert self.__subscription
        # Using a list comprehension instead of values() guarantees the pre-sorted ordering
        self.__items = [ComboBoxOptions(attribute_type_name) for attribute_type_name in self.OPTIONS]

    def destroy(self):
        """Called when the widget is being destroyed, to remove callbacks"""
        self.__controller = None
        self.__subscription = None
        self.__selection_finished_callback = None
        ogt.destroy_property(self, "__current_index")
        ogt.destroy_property(self, "__items")

    def get_item_children(self, parent):
        """Get the model children of this item"""
        return self.__items

    def get_item_value_model(self, item: ui.AbstractItem = None, column_id: int = 0) -> ui.AbstractValueModel:
        """Get the model at the specified column_id"""
        if item is None:
            return self.__current_index
        return item.model

    def __on_selection_finished(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new type was selected"""
        self._item_changed(None)
        try:
            ogt.dbg_ui(f"Adding type to union: {new_value.as_int}")
            new_type_name = self.OPTIONS[new_value.as_int]
            ogt.dbg_ui(f"Type name is {new_type_name}")

            if self.__selection_finished_callback and new_type_name:
                self.__selection_finished_callback(new_type_name)
        except KeyError:
            log_warn(f"Union type add change was rejected - {new_value.as_int} not found")
        except AttributeError as error:
            log_warn(
                f"Union type add '{new_value.as_int}' on attribute '{self.__controller.name}' was rejected - {error}"
            )


# ======================================================================
class AttributeUnionTypeAdderManager:
    """Handle the combo box and responses for getting and adding union types

    Internal Properties:
        __controller: Controller for the data of the attribute this will modify
        __widget: ComboBox widget controlling the base type
        __widget_model: Model for the ComboBox value
    """

    def __init__(self, controller, selection_finished_callback: SelectionFinishedCallback = None):
        """Set up the initial UI and model

        Args:
            controller: AttributePropertiesController in charge of the data for the attribute being managed
        """
        self.__controller = controller
        self.__widget_model = AttributeUnionTypeAdderComboBox(self.__controller, selection_finished_callback)
        self.__widget = ui.ComboBox(
            self.__widget_model,
            alignment=ui.Alignment.LEFT_BOTTOM,
            name=ID_ATTR_UNION_TYPE_ADDER,
            tooltip=TOOLTIPS[ID_ATTR_UNION_TYPE_ADDER],
            arrow_only=True,
            width=ui.Length(7),
        )
        assert self.__widget

    def destroy(self):
        """Called to clean up when the widget is being destroyed"""
        self.__controller = None
        ogt.destroy_property(self, "__widget")
        ogt.destroy_property(self, "__widget_model")
