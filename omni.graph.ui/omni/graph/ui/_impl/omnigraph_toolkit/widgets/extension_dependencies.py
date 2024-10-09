"""Support for the toolkit widget that shows OmniGraph downstream dependencies.

The output is in a hierarchy showing the dependencies of the various omni.graph extensions. Since these have their
own internal dependencies you can find all OmniGraph dependencies just by looking at the list for omni.graph.core
"""
import asyncio
import json
from contextlib import suppress
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import carb
import omni.graph.tools as ogt
import omni.kit
import omni.ui as ui
from omni.kit.window.extensions.common import build_ext_info

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton
from ..toolkit_utils import help_button
from .flag_manager import FlagManager

__all__ = ["ToolkitWidgetExtensionDependencies"]


# ==============================================================================================================
class ToolkitWidgetExtensionDependencies:
    ID = "DumpExtensionDependencies"
    LABEL = "Extensions"
    TOOLTIP = "Dump information on extension dependencies on OmniGraph"
    FLAGS = {
        "flagAll": ("all", "Include dependencies on all omni.graph extensions, not just omni.graph.core", False),
        "flagVerbose": ("verbose", "Include the list of nodes that are defined inside dependent extensions", False),
    }

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        self.__button = None
        self.__ext_information = {}
        self.__flag_managers = {}
        self.__help_button = None
        self.__set_output = set_output_callback
        self.__dependents_calculated = False
        self.__dependents_expansions_calculated = False

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
        ogt.destroy_property(self, "__ext_information")
        ogt.destroy_property(self, "__flag_managers")
        ogt.destroy_property(self, "__help_button")
        ogt.destroy_property(self, "__set_output")
        ogt.destroy_property(self, "__dependents_calculated")
        ogt.destroy_property(self, "__dependents_expansions_calculated")

    # ----------------------------------------------------------------------
    def build(self):
        """Build the UI section with the functionality to dump the extension information"""
        self.__button = DestructibleButton(
            self.LABEL,
            name=self.ID,
            width=BUTTON_WIDTH,
            tooltip=self.TOOLTIP,
            clicked_fn=self.__on_click,
        )
        assert self.__button

        self.__help_button = help_button(lambda x, y, b, m: self.__on_click(force_help=True))
        assert self.__help_button

        for checkbox_id, (flag, tooltip, default_value) in self.FLAGS.items():
            self.__flag_managers[checkbox_id] = FlagManager(checkbox_id, flag, tooltip, default_value)
            with ui.HStack(spacing=5):
                self.__flag_managers[checkbox_id].checkbox()

    # --------------------------------------------------------------------------------------------------------------
    def __populate_extension_information(self):
        """Use the extension manager to find out all of the details for known extensions.
        Populates self.__ext_information as a dictionary where:
            KEY: Name of the extension (with version information stripped)
            VALUE: Tuple(ExtensionCommonInfo, Extension Dictionary)
        """
        if self.__ext_information:
            return

        manager = omni.kit.app.get_app().get_extension_manager()
        carb.log_info("Syncing extension registry. May take a minute...")
        asyncio.ensure_future(omni.kit.app.get_app().next_update_async())
        manager.sync_registry()  # Make sure all extensions are available
        known_extensions = manager.fetch_extension_summaries()

        # Use the utility to convert all of the extension information into a more processing friendly format.
        # The latest version is used, although if we wanted to be thorough there would be entries for every version
        # since they could potentially have different dependencies.
        for extension in known_extensions:
            latest_version = extension["latest_version"]
            ext_id = latest_version["id"]
            ext_name = latest_version["name"]
            package_id = latest_version["package_id"]
            self.__ext_information[ext_name] = build_ext_info(ext_id, package_id)

    # --------------------------------------------------------------------------------------------------------------
    def __expand_downstream_extension_dependencies(self, ext_name: str):
        """Expand the upstream dependencies of the given extension

        Args:
            ext_name: Name of the extension being expanded
        """
        (_, ext_info) = self.__ext_information[ext_name]
        if ext_info.get("full_dependents", None) is not None:
            return ext_info["full_dependents"]

        ext_info["full_dependents"] = set()
        for ext_downstream in ext_info.get("dependents", []):
            ext_info["full_dependents"].add(ext_downstream)
            ext_info["full_dependents"].update(self.__expand_downstream_extension_dependencies(ext_downstream))

        return ext_info["full_dependents"]

    # --------------------------------------------------------------------------------------------------------------
    def __expand_downstream_dependencies(self):
        """Take the existing one-step dependencies and expand them into lists of everything upstream of an extension"""
        # Only do this once
        if self.__dependents_expansions_calculated:
            return
        self.__dependents_expansions_calculated = True

        for ext_name in self.__ext_information:
            self.__expand_downstream_extension_dependencies(ext_name)

    # --------------------------------------------------------------------------------------------------------------
    def __create_downstream_dependencies(self):
        """Take the existing set of downstream dependencies on every extension and compute the equivalent upstream
        dependencies, adding them to the extension information
        """
        # Only do this once
        if self.__dependents_calculated:
            return
        self.__dependents_calculated = True

        for ext_name, (_, ext_info) in self.__ext_information.items():
            dependencies = ext_info.get("dependencies", {})
            for ext_dependency in dependencies:
                with suppress(KeyError):
                    (_, dependencies_info) = self.__ext_information[ext_dependency]
                    dependencies_info["dependents"] = dependencies_info.get("dependents", []) + [ext_name]

    # --------------------------------------------------------------------------------------------------------------
    def __get_dependent_output(self, ext_name: str) -> Dict[str, List[str]]:
        """Returns a dictionary of repo_name:extensions_in_repo that are dependents of the 'ext_name' extension"""
        (_, ext_info) = self.__ext_information[ext_name]
        dependencies_by_repo = {}
        for dependent in ext_info.get("full_dependents", []):
            with suppress(KeyError):
                repo = self.__ext_information[dependent][0].repository
                if not repo and self.__ext_information[dependent][0].is_kit_file:
                    repo = "https://gitlab-master.nvidia.com/omniverse/kit"
                dependencies_by_repo[repo] = dependencies_by_repo.get(repo, set())
                dependencies_by_repo[repo].add(dependent)

        return {repo: list(repo_dependencies) for repo, repo_dependencies in dependencies_by_repo.items()}

    # --------------------------------------------------------------------------------------------------------------
    def __add_nodes_to_extensions(
        self, output: Dict[str, List[str]]
    ) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, List[str]]]:
        """Take the dictionary of extension_repo:extension_names[] and add per-extension node information to return
        (extension_repo:{extension_name:nodes_in_extension},extension_repo:{extension_name[apps_using_extension]})
        """
        # If showing the nodes then transform the list of extension names to a dictionary of extension:node_list
        extensions_with_nodes = {}
        apps_with_nodes = {}
        for repo, repo_dependencies in output.items():
            extensions_with_nodes[repo] = {}
            for ext_name in repo_dependencies:
                try:
                    extensions_with_nodes[repo][ext_name] = []
                    ogn_node_file = Path(self.__ext_information[ext_name][0].path) / "ogn" / "nodes.json"
                    if ogn_node_file.is_file():
                        with open(ogn_node_file, "r", encoding="utf-8") as nodes_fd:
                            json_nodes = json.load(nodes_fd)["nodes"]
                            extensions_with_nodes[repo][ext_name] = list(json_nodes.keys())
                    else:
                        raise AttributeError
                except (AttributeError, KeyError, json.decoder.JSONDecodeError):
                    if str(self.__ext_information[ext_name][0].path).endswith(".kit"):
                        apps_with_nodes[repo] = apps_with_nodes.get(repo, []) + [ext_name]
                    elif self.__ext_information[ext_name][0].is_local:
                        extensions_with_nodes[repo][ext_name] = []
                    else:
                        extensions_with_nodes[repo][ext_name] = "--- Install Extension To Get Node List ---"

        return extensions_with_nodes, apps_with_nodes

    # --------------------------------------------------------------------------------------------------------------
    def __on_click(self, force_help: bool = False):
        """Callback executed when the Dump Graph button is clicked"""
        if force_help:
            flags = ["help"]
            text = (
                "Dump the dependencies of other extensions on the OmniGraph extensions.\n"
                "The following flags are accepted:\n"
            )
            for flag_manager in self.__flag_managers.values():
                text += f"    {flag_manager.name} ({flag_manager.default_value}): {flag_manager.tooltip}\n"
            self.__set_output(text, "Help Information")
            return

        flags = [flag_manager.name for flag_manager in self.__flag_managers.values() if flag_manager.is_set]
        tooltip = f"OmniGraph extension dependencies, filtered with flags {flags}"

        # Clean out the information so that the extensions can be reread each time. There is no callback when extensions
        # are installed or updated so this is the only way to ensure correct information.
        self.__ext_information = {}
        self.__dependents_calculated = False
        self.__dependents_expansions_calculated = False

        # Get all of the extension information for analysis
        self.__populate_extension_information()

        # If the "all" flag is set then scan the extensions to get the ones starting with omni.graph
        # Doing this instead of using a hardcoded list future-proofs us.
        omnigraph_extensions = ["omni.graph.core"]
        if "all" in flags:
            omnigraph_extensions = []
            for ext_name in self.__ext_information:
                if ext_name.startswith("omni.graph"):
                    omnigraph_extensions.append(ext_name)
        include_nodes = "verbose" in flags

        output = {
            "flags": {
                "verbose": include_nodes,
                "extensions": omnigraph_extensions,
            },
            "paths": {ext: self.__ext_information[ext][0].path for ext in omnigraph_extensions},
            "apps": {},
        }

        # Add direct downstream dependencies to the extension info based on the known dependencies
        self.__create_downstream_dependencies()

        # Expand the entire downstream tree of dependencies for all extensions based on the computed edges
        self.__expand_downstream_dependencies()

        # Populate the per-extension output for each of the requested output extensions
        for ext_name in omnigraph_extensions:
            output[ext_name] = self.__get_dependent_output(ext_name)
            if include_nodes:
                (output[ext_name], output["apps"][ext_name]) = self.__add_nodes_to_extensions(output[ext_name])

        # Pipe the output to the final destination
        self.__set_output(json.dumps(output, indent=4), tooltip)
