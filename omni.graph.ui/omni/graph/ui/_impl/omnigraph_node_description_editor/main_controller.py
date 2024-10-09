"""
Controller part of the Model-View-Controller providing editing capabilities to OGN files
"""
from typing import Dict, Union

import omni.graph.tools as ogt
from carb import log_warn

from .attribute_properties import AttributeListController
from .change_management import ChangeManager
from .main_model import Model
from .node_properties import NodePropertiesController
from .ogn_editor_utils import show_wip
from .test_configurations import TestListController

# TODO: Introduce methods in the node generator to allow translation between attribute type name and component values
# TODO: Immediate parsing, with parse errors shown in the "Raw" frame


# ======================================================================
class Controller(ChangeManager):
    """
    Class responsible for coordinating changes to the OGN internal model.

    External Properties:
        ogn_data: Generated value of the OGN dictionary for the controlled model

    Internal Properties:
        __model: The main model being controlled, which encompasses all of the submodels
        __node_properties_controller: Controller for the section containing node properties
        __input_attribute_controller: Controller for the section containing input attributes
        __output_attribute_controller: Controller for the section containing output attributes
        __tests_controller: Controller for the section containing algorithm tests
    """

    def __init__(self, model: Model, initial_contents: Union[None, str, Dict]):
        """Initialize the model being controlled"""
        super().__init__()
        self.__model = model
        self.node_properties_controller = None
        self.input_attribute_controller = None
        self.output_attribute_controller = None
        self.tests_controller = None
        self.set_ogn_data(initial_contents)

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the controller is destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        # The main controller owns all sub-controllers so destroy them here
        ogt.destroy_property(self, "node_properties_controller")
        ogt.destroy_property(self, "input_attribute_controller")
        ogt.destroy_property(self, "output_attribute_controller")
        ogt.destroy_property(self, "tests_controller")
        self.__model = None

    # ----------------------------------------------------------------------
    def set_ogn_data(self, new_contents: Union[None, str, Dict]):
        """Reset the underlying model to new values"""
        ogt.dbg_ui(f"Controller: set_ogn_data to {new_contents}")
        try:
            self.__model.set_ogn_data(new_contents)
            self.node_properties_controller = NodePropertiesController(self.__model.node_properties_model)
            self.input_attribute_controller = AttributeListController(self.__model.input_attribute_model)
            self.output_attribute_controller = AttributeListController(self.__model.output_attribute_model)
            if show_wip():
                self.tests_controller = TestListController(
                    self.__model.tests_model, self.input_attribute_controller, self.output_attribute_controller
                )
            # Change callbacks on the main controller should also be executed by the child controllers when they change
            self.node_properties_controller.forward_callbacks_to(self)
            self.input_attribute_controller.forward_callbacks_to(self)
            self.output_attribute_controller.forward_callbacks_to(self)
            if show_wip():
                self.tests_controller.forward_callbacks_to(self)
        except Exception as error:  # pylint: disable=broad-except
            log_warn(f"Error redefining the OGN data - {error}")

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self) -> Dict:
        """Return the current full OGN data content, reassembled from the component pieces"""
        return self.__model.ogn_data

    # ----------------------------------------------------------------------
    def is_dirty(self) -> bool:
        """Return True if the contents have been modified since being set clean"""
        return self.__model.is_dirty

    # ----------------------------------------------------------------------
    def set_clean(self):
        """Reset the current status of the data to be clean (e.g. after a file save)."""
        ogt.dbg_ui("Controller: set_clean")
        self.__model.set_clean()
