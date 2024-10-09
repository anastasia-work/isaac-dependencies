"""
Support for the combo box representing the choice of node languages.
"""
import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from ..style import name_value_label  # noqa: PLE0402
from .ogn_editor_utils import ComboBoxOptions

# ======================================================================
# ID values for widgets that are editable or need updating
ID_NODE_LANGUAGE = "nodeLanguage"

# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {ID_NODE_LANGUAGE: "The language in which the node is implemented, e.g. Python or C++"}


# ======================================================================
class NodeLanguageComboBox(ui.AbstractItemModel):
    """Implementation of a combo box that shows types of implementation languages available

    Internal Properties:
        __controller: Controller object manipulating the underlying memory model
        __current_index: Model containing the combo box selection
        __items: List of options available to choose from in the combo box
        __subscription: Contains the scoped subscription object for value changes
    """

    OPTION_CPP = "Node Is Implemented In C++"
    OPTION_PYTHON = "Node Is Implemented In Python"
    OPTIONS = [ogn.LanguageTypeValues.CPP, ogn.LanguageTypeValues.PYTHON]
    OPTION_NAMES = {OPTIONS[0]: OPTION_CPP, OPTIONS[1]: OPTION_PYTHON}

    def __init__(self, controller):
        """Initialize the node language combo box details"""
        super().__init__()
        self.__controller = controller
        self.__current_index = ui.SimpleIntModel()
        self.__current_index.set_value(self.OPTIONS.index(ogn.check_node_language(self.__controller.node_language)))
        self.__subscription = self.__current_index.subscribe_value_changed_fn(self.__on_language_changed)
        assert self.__subscription
        assert self.__controller
        # Using a list comprehension instead of values() guarantees the ordering
        self.__items = [ComboBoxOptions(self.OPTION_NAMES[node_language]) for node_language in self.OPTIONS]

    def destroy(self):
        """Clean up when the widget is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__subscription = None
        self.__controller = None
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

    def __on_language_changed(self, new_value: ui.SimpleIntModel):
        """Callback executed when a new language was selected"""
        try:
            new_node_language = self.OPTION_NAMES[self.OPTIONS[new_value.as_int]]
            ogt.dbg_ui(f"Set node language to {new_value.as_int} - {new_node_language}")
            self.__controller.node_language = self.OPTIONS[new_value.as_int]
            self._item_changed(None)
        except (AttributeError, KeyError) as error:
            log_warn(f"Node language '{new_value.as_int}' was rejected - {error}")


# ======================================================================
class NodeLanguageManager:
    """Handle the combo box and responses for getting and setting the node implementation language

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
        name_value_label("Implementation Language:", TOOLTIPS[ID_NODE_LANGUAGE])
        self.__widget_model = NodeLanguageComboBox(controller)
        self.__widget = ui.ComboBox(
            self.__widget_model,
            alignment=ui.Alignment.LEFT_BOTTOM,
            name=ID_NODE_LANGUAGE,
            tooltip=TOOLTIPS[ID_NODE_LANGUAGE],
        )
        assert self.__widget
        assert self.__controller

    def destroy(self):
        """Called to clean up when the widget is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__controller = None
        ogt.destroy_property(self, "__widget")
        ogt.destroy_property(self, "__widget_model")
