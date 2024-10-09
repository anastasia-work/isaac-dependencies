"""
Collection of classes managing the Model-View-Controller paradigm for individual tests within the node.
This test information is collected with the node information later to form the combined .ogn file.

The classes are arranged in a hierarchy to manage the lists within lists within lists.

    TestList{Model,View,Controller}: Manage the list of tests
    TestsValueLists{Model, View, Controller}: Manage the set of inputs and outputs within a single test
    TestsValues{Model, View, Controller}: Manage a single list of input or output values
"""
from contextlib import suppress
from typing import Any, Dict, List, Optional

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn
from omni import ui

from ..style import VSTACK_ARGS  # noqa: PLE0402
from .change_management import ChangeManager, ChangeMessage
from .ogn_editor_utils import DestructibleButton
from .tests_data_manager import TestsDataManager

# ======================================================================
# ID for frames that will dynamically rebuild
ID_FRAME_MAIN = "testFrame"


# ======================================================================
# ID for dictionary of classes that manage subsections of the editor, named for their class
ID_INPUT_VALUES = "testManageInputs"
ID_OUTPUT_VALUES = "testManageOutputs"


# ======================================================================
# Tooltips for the editable widgets
TOOLTIPS = {
    ID_FRAME_MAIN: "Specifications for generated tests that set input values, compute, "
    "then compare results against expected outputs",
    ID_INPUT_VALUES: "Define a new input attribute value as part of the test setup",
    ID_OUTPUT_VALUES: "Define a new output attribute value expected as the test's compute result",
}


# ======================================================================
# Label information passed as parameters (Title, Tooltip)
LABELS = {
    ID_INPUT_VALUES: [
        "Setting These Input Values...",
        "Subsection containing inputs to be set as initial state for the test",
    ],
    ID_OUTPUT_VALUES: [
        "...Should Generate These Output Values",
        "Subsection containing expected output values from running the compute with the above inputs",
    ],
}


# ================================================================================
class TestsValuesModel:
    """
    Manager for a set of test data. Handles the data in both the raw and parsed OGN form.
    The raw form is used wherever possible for more flexibility in editing, allowing temporarily illegal
    data that can have notifications to the user for fixing (e.g. duplicate attribute names)

    External Properties:
        ogn_data
        test_data

    Internal Properties:
        __data: Raw test data dictionary
        __namespace: Namespace for the group to which this value's attribute belongs
        __use_nested_parsing: True if the test inputs and outputs are grouped together without namespaces
    """

    def __init__(self, test_data: Dict[str, Any], attribute_group: str, use_nested_parsing: bool):
        """
        Create an initial test model.

        Args:
            test_data: Dictionary of test data, in the .ogn format (attribute_name: value)
            is_output: True if the attribute values are outputs; guides which prefix to prepend in the OGN data
            use_nested_parsing: True if the test inputs and outputs are grouped together without namespaces
        """
        self.__data = test_data
        self.__namespace = ogn.namespace_of_group(attribute_group)
        self.__use_nested_parsing = use_nested_parsing

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self):
        """Returns the raw OGN data for this test's definition - empty data should return an empty dictionary"""
        if self.__use_nested_parsing:
            return {self.__namespace: {name: value for name, value in self.__data.items() if value}}

        return {f"{self.__namespace}:{name}": value for name, value in self.__data.items() if value}

    # ----------------------------------------------------------------------
    @property
    def test_data(self):
        """Return the dictionary of AttributeName:AttributeValue containing all test data in this subset"""
        return self.__data

    @test_data.setter
    def test_data(self, new_data: Dict[str, str]):
        """Sets a new set of attribute/data values for the test"""
        ogt.dbg_ui(f"Updating test data model to {new_data}")
        self.__data = new_data


# ================================================================================
class TestsValuesController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    Internal Properties:
        __attribute_controller: Controller managing the list of attributes accessed by this controller
        __model: The model this class controls
    """

    def __init__(self, model: TestsValuesModel, attribute_controller):
        """Initialize the controller with the model it will control

        Args:
            attribute_controller: Controller managing the list of attributes accessed by this controller
            model: Model on which this controller operates
        """
        super().__init__()
        self.__model = model
        self.__attribute_controller = attribute_controller

    # ----------------------------------------------------------------------
    def on_attribute_list_changed(self, change_message):
        """Callback that executes when the list of attributes changes"""
        ogt.dbg_ui(f"Attribute list changed - {change_message}")
        # The data does not change here since this is just an aggregator; someone might be listening that needs changes
        self.on_change(change_message)

    # ----------------------------------------------------------------------
    @property
    def available_attribute_names(self) -> List[str]:
        """Returns the list of attribute names known to this controller"""
        return self.__attribute_controller.all_attribute_names

    # ----------------------------------------------------------------------
    @property
    def test_data(self):
        """Return the dictionary of AttributeName:AttributeValue containing all test data in this subset"""
        return self.__model.test_data

    @test_data.setter
    def test_data(self, new_data: Dict[str, str]):
        """Sets a new set of attribute/data values for the test"""
        ogt.dbg_ui(f"Test Values data set to {new_data}")
        self.__model.test_data = new_data
        self.on_change(ChangeMessage(self))


# ================================================================================
class TestsValuesView:
    """UI for a single test's subset of data applicable to the attributes whose controller is passed in

    Internal Properties:
        __tooltip_id: ID for the labels and tooltips in this subsection
    """

    def __init__(self, controller: TestsValuesController, tooltip_id: str):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__tooltip_id = tooltip_id
        self.__manager = TestsDataManager(controller, add_element_tooltip=TOOLTIPS[tooltip_id])

    def on_rebuild_ui(self):
        """Callback executed when the frame in which these widgets live is rebuilt"""
        with ui.VStack(**VSTACK_ARGS):
            ui.Label(
                LABELS[self.__tooltip_id][0],
                # tooltip=LABELS[self.__tooltip_id][1],
            )
            self.__manager.on_rebuild_ui()


# ================================================================================
class TestsValueListsModel:
    """
    Manager for a set of test data. Handles the data in both the raw and parsed OGN form.
    The raw form is used wherever possible for more flexibility in editing, allowing temporarily illegal
    data that can have notifications to the user for fixing (e.g. duplicate attribute names)

    External Properties:
        ogn_data

    Internal Properties:
        __inputs_model: Model managing the input values in the test
        __outputs_model: Model managing the output values in the test
        __description: Description of the attribute
        __comments: Comments on the test as a whole, uneditable
        __gpu_attributes: Attributes forced on the GPU for the test
    """

    def __init__(self, test_data: Dict[str, Any]):
        """
        Create an initial test model.

        Args:
            test_data: Dictionary of test data, in the .ogn format (attribute_name: value)
        """
        ogt.dbg_ui(f"Initializing TestsValueListsModel with {test_data}")

        # TODO: Pull parsing of the test data into a common location in omni.graph.tools that can be used here

        # Description exists at the top level, if at all
        try:
            self.__description = test_data[ogn.TestKeys.DESCRIPTION]
        except KeyError:
            self.__description = ""

        # Top level comments should be preserved
        try:
            self.__comments = {key: value for key, value in test_data.items() if key[0] == "$"}
        except AttributeError:
            self.__comments = {}

        # Runtime GPU attributes are preserved
        # TODO: Implement editing of this
        try:
            self.__gpu_attributes = test_data[ogn.TestKeys.GPU_ATTRIBUTES]
        except KeyError:
            self.__gpu_attributes = []

        # TODO: It would be in our best interest to only support one type of test configuration
        use_nested_parsing = False
        # Switch parsing methods based on which type of test data configuration is present
        if ogn.TestKeys.INPUTS in test_data or ogn.TestKeys.OUTPUTS in test_data:
            use_nested_parsing = True
            try:
                input_list = test_data[ogn.TestKeys.INPUTS]
                input_data = dict(input_list.items())
            except KeyError:
                input_data = {}
            try:
                output_list = test_data[ogn.TestKeys.OUTPUTS]
                output_data = dict(output_list.items())
            except KeyError:
                output_data = {}
        else:
            try:
                prefix = f"{ogn.INPUT_NS}:"
                input_data = {
                    f"{key.replace(prefix, '')}": value for key, value in test_data.items() if key.find(prefix) == 0
                }
            except AttributeError:
                input_data = {}
            try:
                prefix = f"{ogn.OUTPUT_NS}:"
                output_data = {
                    f"{key.replace(prefix, '')}": value for key, value in test_data.items() if key.find(prefix) == 0
                }
            except AttributeError:
                output_data = {}

        self.__inputs_model = TestsValuesModel(input_data, ogn.INPUT_GROUP, use_nested_parsing)
        self.__outputs_model = TestsValuesModel(output_data, ogn.OUTPUT_GROUP, use_nested_parsing)

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the model is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.__inputs_model = None
        self.__outputs_model = None
        self.__description = None
        self.__comments = None
        self.__gpu_attributes = None

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self):
        """Returns the raw OGN data for this test's definition - empty data should return an empty dictionary"""
        ogt.dbg_ui(f"Generating OGN data for value lists {self.__inputs_model} and {self.__outputs_model}")
        data = self.__inputs_model.ogn_data
        # Direct update is okay because the returned values were constructed, not members of the class
        data.update(self.__outputs_model.ogn_data)
        if self.__description:
            data[ogn.TestKeys.DESCRIPTION] = self.__description
        if self.__comments:
            data.update(self.__comments)
        if self.__gpu_attributes:
            data[ogn.TestKeys.GPU_ATTRIBUTES] = self.__gpu_attributes
        return data


# ================================================================================
class TestsValueListsController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    Internal Properties:
        __index: Test index within the parent's list of indexes
        __inputs_controller: Controller managing the list of input attributes
        __model: The model this class controls
        __outputs_controller: Controller managing the list of output attributes
        __parent_controller: Controller for the list of properties, for changing membership callbacks
    """

    def __init__(
        self,
        model: TestsValueListsModel,
        parent_controller,
        index_in_parent: int,
        inputs_controller,
        outputs_controller,
    ):
        """Initialize the controller with the model it will control

        Args:
            inputs_controller: Controller managing the list of input attributes
            model: Model on which this controller operates
            outputs_controller: Controller managing the list of output attributes
            parent_controller: TestListController that aggregates this individual test
            index_in_parent: This test's index within the parent's list (used for unique naming)
        """
        super().__init__()
        self.__model = model
        self.__parent_controller = parent_controller
        self.__inputs_controller = TestsValuesController(model.inputs_model, inputs_controller)
        self.__outputs_controller = TestsValuesController(model.outputs_model, outputs_controller)
        self.__inputs_controller.forward_callbacks_to(self)
        self.__outputs_controller.forward_callbacks_to(self)
        self.__index = index_in_parent

    def destroy(self):
        """Called when the controller is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        ogt.destroy_property(self, "__model")
        ogt.destroy_property(self, "__parent_controller")
        ogt.destroy_property(self, "__inputs_controller")
        ogt.destroy_property(self, "__outputs_controller")

    # ----------------------------------------------------------------------
    @property
    def model(self) -> TestsValueListsModel:
        return self.__model

    # ----------------------------------------------------------------------
    def on_remove_test(self):
        """Callback that executes when the view wants to remove the named test"""
        ogt.dbg_ui(f"Removing existing test {self.__index + 1}")
        self.__parent_controller.on_remove_test(self)

    # ----------------------------------------------------------------------
    def on_input_attribute_list_changed(self, change_message):
        """Callback that executes when the list of input attributes changes"""
        ogt.dbg_ui(f"Input attribute list changed on test {self.__index} - {change_message}")
        self.__inputs_controller.on_attribute_list_changed(change_message)

    # ----------------------------------------------------------------------
    def on_output_attribute_list_changed(self, change_message):
        """Callback that executes when the list of output attributes changes"""
        ogt.dbg_ui(f"Output attribute list changed on test {self.__index} - {change_message}")
        self.__outputs_controller.on_attribute_list_changed(change_message)


# ================================================================================
class TestsValueListsView:
    """UI for the list of all tests

    Internal Properties:
        __controller: The controller used to manipulate the model's data
        __frame: Main frame for this test's interface
        __input_frame: Subframe containing input attribute values
        __output_frame: Subframe containing output attribute values
        __widgets: Dictionary of ID:Widget for the components of the test's frame
    """

    def __init__(self, controller: TestsValueListsController):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__controller = controller
        self.__input_view = TestsValuesView(self.__controller._inputs_controller, ID_INPUT_VALUES)
        self.__output_view = TestsValuesView(self.__controller._outputs_controller, ID_OUTPUT_VALUES)
        with ui.HStack(spacing=5):
            self.__remove_button = DestructibleButton(
                width=20,
                height=20,
                style_type_name_override="RemoveElement",
                clicked_fn=self.__controller.on_remove_test,
                tooltip="Remove this test",
            )
            assert self.__remove_button

            self.__frame = ui.CollapsableFrame(title=f"Test {self.__controller._index + 1}", collapsed=False)
        self.__frame.set_build_fn(self.__rebuild_frame)
        self.__input_frame = None
        self.__output_frame = None

    def destroy(self):
        """Called when the view is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        ogt.destroy_property(self, "__controller")
        ogt.destroy_property(self, "__remove_button")
        ogt.destroy_property(self, "__widget_models")
        ogt.destroy_property(self, "__widgets")
        ogt.destroy_property(self, "__managers")
        ogt.destroy_property(self, "__input_view")
        ogt.destroy_property(self, "__output_view")
        with suppress(AttributeError):
            self.__frame.set_build_fn(None)
        with suppress(AttributeError):
            self.__input_frame.set_build_fn(None)
        with suppress(AttributeError):
            self.__output_frame.set_build_fn(None)
        ogt.destroy_property(self, "__frame")

    # ----------------------------------------------------------------------
    def __rebuild_frame(self):
        """Rebuild the contents underneath the main test frame"""
        with ui.VStack(**VSTACK_ARGS):
            with ui.ZStack():
                ui.Rectangle(name="frame_background")
                self.__input_frame = ui.Frame(name="attribute_value_frame")
            with ui.ZStack():
                ui.Rectangle(name="frame_background")
                self.__output_frame = ui.Frame(name="attribute_value_frame")
            ui.Spacer(height=2)
        self.__input_frame.set_build_fn(self.__input_view.on_rebuild_ui)
        self.__output_frame.set_build_fn(self.__output_view.on_rebuild_ui)


# ================================================================================
class TestListModel:
    """
    Manager for an entire list of tests. It only manages the list as a whole. Individual tests are all
    managed through TestsValueListsModel

    External Properties:
        models
        ogn_data

    Internal Properties:
        __models: List of TestsValueListsModels for each test in the list
    """

    def __init__(self, test_data: Optional[List[Dict]]):
        """
        Create an initial test model from the list of tests (empty list if None)

        Args:
            test_data: Initial list of test dictionaries
        """
        self.__models = []
        if test_data is not None:
            self.__models = [TestsValueListsModel(test_datum) for test_datum in test_data]

    # ----------------------------------------------------------------------
    def destroy(self):
        """Run when the model is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        ogt.destroy_property(self, "__models")

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self) -> Dict:
        """Return a dictionary representing the list of tests in .ogn format, None if the list is empty"""
        ogt.dbg_ui(f"Generating OGN data for {self.__models}")
        return [model.ogn_data for model in self.__models] if self.__models else None

    # ----------------------------------------------------------------------
    @property
    def models(self) -> List:
        """Return a list of the models managing the individual tests"""
        return self.__models

    # ----------------------------------------------------------------------
    def add_new_test(self) -> TestsValueListsModel:
        """Create a new empty test and add it to the list

        Returns:
            Newly created test values model
        """
        self.__models.append(TestsValueListsModel({}))
        return self.__models[-1]

    # ----------------------------------------------------------------------
    def remove_test(self, test_model):
        """Remove the test encapsulated in the given model"""
        try:
            self.__models.remove(test_model)
        except ValueError:
            log_warn(f"Failed to remove test model for {test_model.name}")


# ================================================================================
class TestListController(ChangeManager):
    """Interface between the view and the model, making changes to the model on request

    Internal Properties:
        __inputs_controller: Controller managing the list of input attributes
        __model: The model this class controls
        __outputs_controller: Controller managing the list of output attributes
    """

    def __init__(self, model: TestListModel, inputs_controller, outputs_controller):
        """Initialize the controller with the model it will control"""
        super().__init__()
        self.__model = model
        self.__inputs_controller = inputs_controller
        self.__outputs_controller = outputs_controller

        # The tests need to know if attributes changed in order to update the list of available attributes
        # as well as potentially removing references to attributes that no longer exist.
        inputs_controller.add_change_callback(self.__on_input_attribute_list_changed)
        outputs_controller.add_change_callback(self.__on_output_attribute_list_changed)
        inputs_controller.forward_callbacks_to(self)
        outputs_controller.forward_callbacks_to(self)

        self.__controllers = [
            TestsValueListsController(model, self, index, inputs_controller, outputs_controller)
            for (index, model) in enumerate(self.__model.models)
        ]
        # Be sure to forward all change callbacks from the children to this parent
        for controller in self.__controllers:
            controller.forward_callbacks_to(self)

    def destroy(self):
        """Called when the controller is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        super().destroy()
        ogt.destroy_property(self, "__model")
        ogt.destroy_property(self, "__controllers")
        ogt.destroy_property(self, "__inputs_controller")
        ogt.destroy_property(self, "__outputs_controller")

    # ----------------------------------------------------------------------
    def on_new_test(self):
        """Callback that executes when the view wants to add a new test
        A test model controller and model are added, but no new OGN data will generate until values are set.
        """
        ogt.dbg_ui("Adding a new test")
        new_model = self.__model.add_new_test()
        new_index = len(self.__controllers)
        self.__controllers.append(
            TestsValueListsController(new_model, self, new_index, self.__inputs_controller, self.__outputs_controller)
        )
        self.__controllers[-1].forward_callbacks_to(self)
        self.on_change()

    # ----------------------------------------------------------------------
    def on_remove_test(self, test_controller: TestsValueListsController):
        """Callback that executes when the given controller's test was removed"""
        ogt.dbg_ui("Removing an existing test")
        try:
            self.__model.remove_test(test_controller.model)
            self.__controllers.remove(test_controller)
        except ValueError:
            log_warn(f"Failed removal of controller for {test_controller}")
        self.on_change()

    # ----------------------------------------------------------------------
    def __on_input_attribute_list_changed(self, change_message):
        """Callback that executes when the list of input attributes changes"""
        ogt.dbg_ui(f"Input attribute list changed on {change_message}")
        for controller in self.__controllers:
            controller.on_input_attribute_list_changed(change_message)

    # ----------------------------------------------------------------------
    def __on_output_attribute_list_changed(self, change_message):
        """Callback that executes when the list of output attributes changes"""
        ogt.dbg_ui(f"Output attribute list changed on {change_message}")
        for controller in self.__controllers:
            controller.on_output_attribute_list_changed(change_message)

    # ----------------------------------------------------------------------
    @property
    def all_test_controllers(self) -> List[TestsValueListsController]:
        """Returns the list of all controllers for tests in this list"""
        return self.__controllers


# ================================================================================
class TestListView:
    """UI for a list of tests

    Internal Properties:
        __test_views: Per-test set of views
        __controller: The controller used to manipulate the model's data
        __frame: Main frame for this test's interface
    """

    def __init__(self, controller: TestListController):
        """Initialize the view with the controller it will use to manipulate the model"""
        self.__controller = controller
        self.__test_views = []
        self.__add_button = None
        self.__frame = ui.CollapsableFrame(
            title="Tests",
            # tooltip=TOOLTIPS[ID_FRAME_MAIN],
            collapsed=True,
        )
        self.__frame.set_build_fn(self.__rebuild_frame)
        self.__controller.add_change_callback(self.__on_list_change)

    def destroy(self):
        """Called when the view is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        ogt.destroy_property(self, "__test_views")
        ogt.destroy_property(self, "__add_button")
        ogt.destroy_property(self, "__controller")
        with suppress(AttributeError):
            self.__frame.set_build_fn(None)
        ogt.destroy_property(self, "__frame")

    # ----------------------------------------------------------------------
    def __on_list_change(self, change_message):
        """Callback executed when a member of the list changes.

        Args:
            change_message: Message with information about the change
        """
        ogt.dbg_ui(f"List change called on {self} with {change_message}")
        # If the main controller was requesting the change then the frame must be rebuilt, otherwise the
        # individual test controllers are responsible for updating just their frame.
        if self.__controller == change_message.caller:
            self.__frame.rebuild()

    # ----------------------------------------------------------------------
    def __rebuild_frame(self):
        """Rebuild the contents underneath the main test frame"""
        ogt.dbg_ui("Rebuilding the frame tests")
        self.__test_views = []

        with ui.VStack(**VSTACK_ARGS):
            self.__add_button = DestructibleButton(
                width=20,
                height=20,
                style_type_name_override="AddElement",
                clicked_fn=self.__controller.on_new_test,
                tooltip="Add a new test",
            )
            assert self.__add_button
            # Reconstruct the list of per-test views. Construction instantiates their UI.
            self.__test_views = [
                TestsValueListsView(controller) for controller in self.__controller.all_test_controllers
            ]
            assert self.__test_views
