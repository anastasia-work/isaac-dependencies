"""Manage the OGN data controlled by the OmniGraphNodeDescriptionEditor"""
from __future__ import annotations

import json
import pprint
from typing import Dict, Union

import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn
from carb import log_warn

from .attribute_properties import AttributeListModel
from .file_manager import FileManager
from .node_properties import NodePropertiesModel
from .ogn_editor_utils import OGN_DEFAULT_CONTENT, OGN_NEW_NODE_NAME
from .test_configurations import TestListModel


# ======================================================================
class Model:
    """Manager of the OGN contents in the node description editor.

    External Properties:
        input_attribute_model: The owned models containing all of the input attributes
        is_dirty: True if the OGN has changed since being set clean
        node_properties_model: The owned model containing just the properties of the node
        ogn_data: Raw JSON containing the node's OGN data
        output_attribute_model: The owned models containing all of the output attributes
        state_attribute_model: The owned models containing all of the state attributes
        tests_model: The owned model containing information about the tests

    Internal Properties:
        __checksum: Unique checksum of the current OGN data, to use for determining if the data needs to be saved
        __extension: Information regarding the extension to which the node belongs
        __file_manager: File manager for OGN data
    """

    def __init__(self):
        """Set up initial empty contents of the editor

        Args:
            file_manager: File manager for OGN data
        """
        ogt.dbg_ui("Initializing the model contents")
        # Just set the data for now - parse only on request
        self.input_attribute_model = None
        self.node_properties_model = None
        self.output_attribute_model = None
        self.state_attribute_model = None
        self.tests_model = None
        self.__checksum = None
        self.__extension = None
        self.__file_manager = None
        self.__node_name = None

    # ----------------------------------------------------------------------
    def destroy(self):
        """Runs when the model is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        # The main model owns all sub-models so destroy them here
        ogt.destroy_property(self, "input_attribute_model")
        ogt.destroy_property(self, "node_properties_model")
        ogt.destroy_property(self, "output_attribute_model")
        ogt.destroy_property(self, "tests_model")
        self.__checksum = None

    # ----------------------------------------------------------------------
    def __set_data(self, new_contents: Dict):
        """
        Initialize the OGN contents with a new dictionary of JSON data

        Args:
            new_contents: Dictionary of new data

        Returns:
            True if the data set is fully supported in the current codebase
        """
        ogt.dbg_ui(f"Setting model OGN to {new_contents}")
        try:
            self.__node_name = list(new_contents.keys())[0]
            node_data = new_contents[self.__node_name]
            try:
                # Construct the input attribute models
                self.input_attribute_model = AttributeListModel(node_data[ogn.NodeTypeKeys.INPUTS], ogn.INPUT_GROUP)
            except KeyError:
                self.input_attribute_model = AttributeListModel(None, ogn.INPUT_GROUP)

            try:
                # Construct the output attribute models
                self.output_attribute_model = AttributeListModel(node_data[ogn.NodeTypeKeys.OUTPUTS], ogn.OUTPUT_GROUP)
            except KeyError:
                self.output_attribute_model = AttributeListModel(None, ogn.OUTPUT_GROUP)

            try:
                # Construct the state attribute models
                self.state_attribute_model = AttributeListModel(node_data[ogn.NodeTypeKeys.STATE], ogn.STATE_GROUP)
            except KeyError:
                self.state_attribute_model = AttributeListModel(None, ogn.STATE_GROUP)

            try:
                # Construct the tests model
                self.tests_model = TestListModel(node_data[ogn.NodeTypeKeys.TESTS])
            except KeyError:
                self.tests_model = TestListModel(None)

            # Construct the node properties model
            filtered_keys = [
                ogn.NodeTypeKeys.INPUTS,
                ogn.NodeTypeKeys.OUTPUTS,
                ogn.NodeTypeKeys.STATE,
                ogn.NodeTypeKeys.TESTS,
            ]
            self.node_properties_model = NodePropertiesModel(
                self.__node_name,
                self.__extension,
                {key: value for key, value in node_data.items() if key not in filtered_keys},
                self.__file_manager,
            )

        except (AttributeError, IndexError, KeyError) as error:
            ogt.dbg_ui(f"Error setting new OGN data - {error}")
            self.input_attribute_model = AttributeListModel(None, ogn.INPUT_GROUP)
            self.output_attribute_model = AttributeListModel(None, ogn.OUTPUT_GROUP)
            self.state_attribute_model = AttributeListModel(None, ogn.STATE_GROUP)
            self.tests_model = TestListModel(None)
            self.node_properties_model = NodePropertiesModel(
                OGN_NEW_NODE_NAME, self.__extension, None, self.__file_manager
            )

        # By definition when new contents are just set they are clean
        self.set_clean()

    # ----------------------------------------------------------------------
    def set_ogn_data(self, new_contents: Union[str, None, Dict] = None) -> bool:
        """Initialize the OGN content to the given contents, or an empty node if None.

        Args:
            new_contents: If None reset to default, else it is a path to the new contents

        Return:
            True if the data read in is fully supported in the current codebase
        """
        if new_contents is None:
            ogt.dbg_ui("Resetting the content to the default")
            self.__set_data(OGN_DEFAULT_CONTENT)
        elif isinstance(new_contents, dict):
            self.__set_data(new_contents)
        else:
            ogt.dbg_ui(f"Setting the new content from file {new_contents}")
            try:
                with open(new_contents, "r", encoding="utf-8") as content_fd:
                    self.__set_data(json.load(content_fd))
            except json.decoder.JSONDecodeError as error:
                log_warn(f"Could not reset the contents due to a JSON error : {error}")

    # ----------------------------------------------------------------------
    def __compute_checksum(self) -> int:
        """Find the checksum for the current data in the class - used to automatically find dirty state."""
        ogt.dbg_ui("Computing the checksum")
        try:
            as_string = pprint.pformat(self.ogn_data)
        except Exception:  # pylint: disable=broad-except
            # If not printable then fall back on a raw representation of the dictionary
            as_string = str(self.ogn_data)
        checksum_value = hash(as_string)
        ogt.dbg_ui(f"-> {checksum_value}")
        return checksum_value

    # ----------------------------------------------------------------------
    def set_clean(self):
        """Reset the current status of the data to be clean (e.g. after a file save)."""
        ogt.dbg_ui("Set clean")
        self.__checksum = self.__compute_checksum()

    # ----------------------------------------------------------------------
    @property
    def ogn_data(self) -> Dict:
        """
        Return the current full OGN data content, as-is.
        As the data is spread out among submodels it has to be reassembled first.
        """
        ogt.dbg_ui("Regenerating the OGN data")
        raw_data = self.node_properties_model.ogn_data
        input_attribute_ogn = self.input_attribute_model.ogn_data()
        if input_attribute_ogn:
            raw_data.update(input_attribute_ogn)
        output_attribute_ogn = self.output_attribute_model.ogn_data()
        if output_attribute_ogn:
            raw_data.update(output_attribute_ogn)
        state_attribute_ogn = self.state_attribute_model.ogn_data()
        if state_attribute_ogn:
            raw_data.update(state_attribute_ogn)
        if self.tests_model:
            tests_ogn_data = self.tests_model.ogn_data
            if tests_ogn_data:
                raw_data[ogn.NodeTypeKeys.TESTS] = tests_ogn_data
        return {self.node_properties_model.name: raw_data}

    # ----------------------------------------------------------------------
    def ogn_node(self) -> ogn.NodeInterface:
        """Return the current interface to the OGN data

        Raises:
            ParseError: If the current data cannot be interpreted by the OGN node interface builder
        """
        return ogn.NodeInterfaceWrapper(None, self.ogn_data, self.__extension.name).node_interface

    # ----------------------------------------------------------------------
    def metadata(self) -> Dict[str, str]:
        """Returns the contents of the node's metadata, or empty dictionary if there is none"""
        return self.node_properties_model.metadata

    # ----------------------------------------------------------------------
    @property
    def is_dirty(self) -> bool:
        """Return True if the contents have been modified since being set clean"""
        ogt.dbg_ui("Checking for dirty state")
        return self.__compute_checksum() != self.__checksum

    # ----------------------------------------------------------------------
    @property
    def extension(self) -> ogn.OmniGraphExtension:
        """Return the extension information on the current model"""
        return self.__extension

    # ----------------------------------------------------------------------
    @extension.setter
    def extension(self, extension: ogn.OmniGraphExtension):
        """Sets the extension information on the current model"""
        self.__extension = extension
        self.node_properties_model.extension = extension

    # ----------------------------------------------------------------------
    @property
    def file_manager(self) -> FileManager:
        """Return the ogn file manager on the current model"""
        return self.__file_manager

    # ----------------------------------------------------------------------
    @file_manager.setter
    def file_manager(self, file_manager: FileManager):
        """Sets the ogn file manager on the current model"""
        self.__file_manager = file_manager
        self.node_properties_model.file_manager = self.__file_manager
