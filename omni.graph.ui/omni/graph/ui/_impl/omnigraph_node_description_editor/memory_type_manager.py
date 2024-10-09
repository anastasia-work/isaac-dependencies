"""
Support for the combo box representing the choice of attribute memory types.
Shared between the node and attribute properties since both allow that choice.
"""
import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from ..style import name_value_label  # noqa: PLE0402
from .ogn_editor_utils import ComboBoxOptions

# ======================================================================
# ID values for widgets that are editable or need updating
ID_MEMORY_TYPE = "memoryType"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_MEMORY_TYPE: "The physical location of attribute data. Attribute values override node values"}


# ======================================================================
class MemoryTypeComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows types of memory locations available

    Internal Properties:
        __controller: Controller object manipulating the underlying memory model
        __current_index: Model containing the combo box selection
        __items: List of options available to choose from in the combo box
        __subscription: Contains the scoped subscription object for value changes
    """

    OPTION_CPU = "Store Attribute Memory on CPU"
    OPTION_CUDA = "Store Attribute Memory on GPU (CUDA style)"
    OPTION_ANY = "Choose Attribute Memory Location at Runtime"
    OPTIONS = [ogn.MemoryTypeValues.CPU, ogn.MemoryTypeValues.CUDA, ogn.MemoryTypeValues.ANY]
    OPTION_NAME = {
        ogn.MemoryTypeValues.CPU: OPTION_CPU,
        ogn.MemoryTypeValues.CUDA: OPTION_CUDA,
        ogn.MemoryTypeValues.ANY: OPTION_ANY,
    }

    def __init__(self, controller):
        """Initialize the memory type combo box details"""
        super().__init__()
        self.__controller = controller
        self.__current_index = ui.SimpleIntModel()
        self.__current_index.set_value(self.OPTIONS.index(self.__controller.memory_type))
        self.__subscription = self.__current_index.subscribe_value_changed_fn(self.__on_memory_type_changed)
        assert self.__subscription
        # Using a list comprehension instead of values() guarantees the ordering
        self.__items = [ComboBoxOptions(self.OPTION_NAME[memory_type]) for memory_type in self.OPTIONS]

    def destroy(self):
        """Called when the manager is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__controller = None
        self.__subscription = None
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

    def __on_memory_type_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new memory type was selected"""
        try:
            new_memory_type = self.OPTION_NAME[self.OPTIONS[new_value.as_int]]
            ogt.dbg_ui(f"Set memory type to {new_value.as_int} - {new_memory_type}")
            self.__controller.memory_type = self.OPTIONS[new_value.as_int]
            self._item_changed(None)
        except (AttributeError, KeyError) as error:
            log_warn(f"Node memory type '{new_value.as_int}' was rejected - {error}")


# ======================================================================
class MemoryTypeManager:
    """Handle the combo box and responses for getting and setting the memory type location

    Internal Properties:
        __controller: Controller for the data of the attribute this will modify
        __widget: ComboBox widget controlling the base type
        __widget_model: Model for the ComboBox value
    """

    def __init__(self, controller):
        """Set up the initial UI and model

        Args:
            controller: AttributePropertiesController in charge of the data for the attribute being managed
        """
        self.__controller = controller
        name_value_label("Memory Type:", TOOLTIPS[ID_MEMORY_TYPE])
        self.__widget_model = MemoryTypeComboBox(controller)
        self.__widget = ui.ComboBox(
            self.__widget_model,
            alignment=ui.Alignment.LEFT_BOTTOM,
            name=ID_MEMORY_TYPE,
            tooltip=TOOLTIPS[ID_MEMORY_TYPE],
        )
        assert self.__widget
        assert self.__controller

    def destroy(self):
        """Called when the manager is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__controller = None
        ogt.destroy_property(self, "__widget")
        ogt.destroy_property(self, "__widget_model")
