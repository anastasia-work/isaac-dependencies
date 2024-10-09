"""Support for adding OmniGraph information to the Kit extensions window"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import omni.kit.app
import omni.ui as ui
from omni.kit.window.extensions.common import ExtensionCommonInfo


# ==============================================================================================================
class OmniGraphTab:
    def build(self, ext_info):
        try:
            ext_name = ext_info["package"]["name"]
        except KeyError:
            ext_name = "omni.graph"
        with ui.VStack(height=0):
            found_nodes = False
            node_data = _get_omnigraph_info(ext_info.get("path"))
            if node_data:
                node_name_map = {
                    node_name: node_name.replace(f"{ext_name}.", "") for node_name in node_data["nodes"].keys()
                }
                for node_name in sorted(node_data["nodes"].keys(), key=lambda name: node_name_map[name]):
                    node_info = node_data["nodes"][node_name]
                    found_nodes = True
                    try:
                        description = node_info["description"]
                    except KeyError:
                        description = "No description provided"
                    with ui.CollapsableFrame(node_name_map[node_name], collapsed=True, tooltip=description):
                        with ui.VStack():
                            for property_key, property_value in node_info.items():
                                if property_key == "extension":
                                    continue
                                with ui.HStack():
                                    ui.Spacer(width=20)
                                    ui.Label(
                                        f"{property_key.capitalize()}: ",
                                        width=0,
                                        style={"color": 0xFF8A8777},
                                        alignment=ui.Alignment.LEFT_TOP,
                                    )
                                    ui.Spacer(width=5)
                                    ui.Label(str(property_value), word_wrap=True)
            if not found_nodes:
                ui.Label(
                    "No OmniGraph nodes are present in this extension",
                    style_type_name_override="ExtensionDescription.Title",
                )

    def destroy(self):
        pass


# ==============================================================================================================
class OmniGraphPage:
    """Wrapper for an OmniGraph tab inside the extension window"""

    def __init__(self):
        self.tab = OmniGraphTab()

    def build_tab(self, ext_info, is_local: bool):
        self.tab.build(ext_info)

    def destroy(self):
        self.tab.destroy()

    @staticmethod
    def get_tab_name():
        return "OMNIGRAPH"


# ==============================================================================================================
@lru_cache()
def _get_omnigraph_info(ext_path) -> Dict[str, Any]:
    """Returns the OmniGraph data associated with the extension as a dictionary of path:NodeJsonData
    The NodeJsonData will be empty if there is no OmniGraph data for the given extension
    """
    node_data = {}
    path = Path(ext_path) / "ogn" / "nodes.json"
    if path.is_file():
        with open(path, "r", encoding="utf-8") as json_fd:
            node_data = json.load(json_fd)
    return node_data


# ==============================================================================================================
@lru_cache()
def _get_omnigraph_user_exts() -> List[Dict[str, Any]]:
    """Returns the list of all visible extensions that are known to contain OmniGraph nodes.
    This can be expensive so the results are cached and it is not called until the user explicitly asks for it.
    TODO: This current method of discovery does not work for extensions that are not installed as there is no
    information in the .toml file to identify that they have nodes. Once that information is added then it can be
    checked instead of looking at the extensions on disk as that will be much faster for this quick check.
    """
    found_exts = set()
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    for ext_info in ext_manager.get_extensions():
        ext_omnigraph_info = _get_omnigraph_info(ext_info.get("path"))
        if ext_omnigraph_info:
            found_exts.add(ext_info["name"])
    return found_exts


# ==============================================================================================================
def clear_omnigraph_caches():
    """Clear the cached OmniGraph info for extensions. Use only when extensions are modified as this could be
    costly to call repeatedly as it will force reload of OmniGraph node description files
    """
    _get_omnigraph_info.cache_clear()
    _get_omnigraph_user_exts.cache_clear()


# ==============================================================================================================
def has_omnigraph_nodes(extension_info: ExtensionCommonInfo) -> bool:
    """Check to see if the extension info item refers to an extension that contains OmniGraph nodes."""
    return extension_info.fullname in _get_omnigraph_user_exts()
