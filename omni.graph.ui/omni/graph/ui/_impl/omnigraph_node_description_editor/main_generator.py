"""
Management for the functions that generate code from the .ogn files.
"""
import os

import omni.graph.core as og
import omni.graph.tools as ogt
import omni.graph.tools.ogn as ogn


# ================================================================================
class Generator:
    """Class responsible for generating files from the current .ogn model"""

    def __init__(self, extension: ogn.OmniGraphExtension):
        """Initialize the model being used for generation

        Args:
            extension: Container with information needed to configure the parser
        """
        self.ogn_file_path = None
        self.extension = extension
        self.node_interface_wrapper = None
        self.configuration = None

    # ----------------------------------------------------------------------
    def parse(self, ogn_file_path: str):
        """Perform an initial parsing pass on a .ogn file, keeping the parse information locally for later generation

        Args:
            ogn_file_path: Path to the .ogn file to use for regeneration

        Raises:
            ParseError: File parsing failed
            FileNotFoundError: .ogn file did not exist
        """
        ogt.dbg_ui(f"Parsing OGN file {ogn_file_path}")
        self.ogn_file_path = ogn_file_path

        # Parse the .ogn file
        with open(ogn_file_path, "r", encoding="utf-8") as ogn_fd:
            self.node_interface_wrapper = ogn.NodeInterfaceWrapper(ogn_fd, self.extension.extension_name)
        ogt.dbg_ui(f"Generated a wrapper {self.node_interface_wrapper}")

        # Set up the configuration to write into the correct directories
        base_name, _ = os.path.splitext(os.path.basename(ogn_file_path))
        self.configuration = ogn.GeneratorConfiguration(
            ogn_file_path,
            self.node_interface_wrapper.node_interface,
            self.extension.import_path,
            self.extension.import_path,
            base_name,
            None,
            ogn.OGN_PARSE_DEBUG,
            og.Settings.generator_settings(),
        )

    # ----------------------------------------------------------------------
    def check_wrapper(self):
        """Check to see if the node_interface_wrapper was successfully parsed

        Raises:
            NodeGenerationError if a parsed interface was not available
        """
        if self.node_interface_wrapper is None:
            raise ogn.NodeGenerationError(f"Cannot generate file due to parse error in {self.ogn_file_path}")

    # ----------------------------------------------------------------------
    def generate_cpp(self):
        """Take the existing OGN model and generate the C++ database interface header file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_cpp")
        self.check_wrapper()

        # Generate the C++ NODEDatabase.h file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("c++"):
            self.configuration.destination_directory = self.extension.ogn_include_directory
            ogn.generate_cpp(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate C++ database")

    # ----------------------------------------------------------------------
    def generate_python(self):
        """Take the existing OGN model and generate the Python database interface file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_python")
        self.check_wrapper()

        # Generate the Python NODEDatabase.py file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("python"):
            self.configuration.destination_directory = self.extension.ogn_python_directory
            ogn.generate_python(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate Python database")

    # ----------------------------------------------------------------------
    def generate_documentation(self):
        """Take the existing OGN model and generate the documentation file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_documentation")
        self.check_wrapper()

        # Generate the documentation NODE.rst file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("docs"):
            self.configuration.destination_directory = self.extension.ogn_docs_directory
            ogn.generate_documentation(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate documentation file")

    # ----------------------------------------------------------------------
    def generate_tests(self):
        """Take the existing OGN model and generate the tests file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_tests")
        self.check_wrapper()

        # Generate the tests TestNODE.py file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("tests"):
            self.configuration.destination_directory = self.extension.ogn_tests_directory
            ogn.generate_tests(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate tests file")

    # ----------------------------------------------------------------------
    def generate_usd(self):
        """Take the existing OGN model and generate the usd file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_usd")
        self.check_wrapper()

        # Generate the USD NODE_Template.usda file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("usd"):
            self.configuration.destination_directory = self.extension.ogn_usd_directory
            ogn.generate_usd(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate usd file")

    # ----------------------------------------------------------------------
    def generate_template(self):
        """Take the existing OGN model and generate the template file for it

        Returns:
            True if the file was successfully generated, else False
        """
        ogt.dbg_ui("Generator::generate_template")
        self.check_wrapper()

        # Generate the template NODE_Template.c++|py file if this .ogn description allows it
        if self.node_interface_wrapper.can_generate("template"):
            self.configuration.destination_directory = self.extension.ogn_nodes_directory
            ogn.generate_template(self.configuration)
        else:
            ogt.dbg_ui("...Skipping -> File cannot generate template file")
