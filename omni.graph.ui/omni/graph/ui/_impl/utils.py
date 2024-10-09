"""
* Copyright (c) 2021-2023, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
"""

import asyncio
from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import omni.graph.core as og
import omni.graph.tools.ogn as ogn
import omni.kit
import omni.ui as ui
from omni.kit.property.usd.usd_attribute_widget import UsdPropertyUiEntry
from pxr import Sdf

# ======================================================================

_preferred_types = ["double", "double[3]", "float", "float[3]", "int", "string", "token", "unknown"]


# ======================================================================
def get_icons_dir() -> str:
    """Returns the location of the directory containing the icons used by these windows"""
    return Path(__file__).parent.parent.parent.parent.parent.joinpath("icons")


# ======================================================================
class DestructibleButton(ui.Button):
    """Class that enhances the standard button with a destroy method that removes callbacks"""

    def destroy(self):
        """Called when the button is being destroyed"""
        self.set_clicked_fn(None)


# ======================================================================
class DestructibleImage(ui.Image):
    """Class that enhances the standard image with a destroy method that removes callbacks"""

    def destroy(self):
        """Called when the image is being destroyed"""
        self.set_mouse_pressed_fn(None)


# ======================================================================


class Prompt:
    def __init__(
        self,
        title,
        text,
        ok_button_text="OK",
        cancel_button_text=None,
        middle_button_text=None,
        ok_button_fn=None,
        cancel_button_fn=None,
        middle_button_fn=None,
        modal=False,
    ):
        self._title = title
        self._text = text
        self._cancel_button_text = cancel_button_text
        self._cancel_button_fn = cancel_button_fn
        self._ok_button_fn = ok_button_fn
        self._ok_button_text = ok_button_text
        self._middle_button_text = middle_button_text
        self._middle_button_fn = middle_button_fn
        self._modal = modal
        self._build_ui()

    def __del__(self):
        self._cancel_button_fn = None
        self._ok_button_fn = None

    def __enter__(self):
        self._window.show()
        return self

    def __exit__(self, exit_type, value, trace):
        self._window.hide()

    def show(self):
        self._window.visible = True

    def hide(self):
        self._window.visible = False

    def is_visible(self):
        return self._window.visible

    def set_text(self, text):
        self._text_label.text = text

    def set_confirm_fn(self, on_ok_button_clicked):
        self._ok_button_fn = on_ok_button_clicked

    def set_cancel_fn(self, on_cancel_button_clicked):
        self._cancel_button_fn = on_cancel_button_clicked

    def set_middle_button_fn(self, on_middle_button_clicked):
        self._middle_button_fn = on_middle_button_clicked

    def _on_ok_button_fn(self):
        self.hide()
        if self._ok_button_fn:
            self._ok_button_fn()

    def _on_cancel_button_fn(self):
        self.hide()
        if self._cancel_button_fn:
            self._cancel_button_fn()

    def _on_middle_button_fn(self):
        self.hide()
        if self._middle_button_fn:
            self._middle_button_fn()

    def _build_ui(self):
        self._window = ui.Window(self._title, visible=False, height=0, dockPreference=ui.DockPreference.DISABLED)
        self._window.flags = (
            ui.WINDOW_FLAGS_NO_COLLAPSE
            | ui.WINDOW_FLAGS_NO_RESIZE
            | ui.WINDOW_FLAGS_NO_SCROLLBAR
            | ui.WINDOW_FLAGS_NO_RESIZE
            | ui.WINDOW_FLAGS_NO_MOVE
        )

        if self._modal:
            self._window.flags = self._window.flags | ui.WINDOW_FLAGS_MODAL

        with self._window.frame:
            with ui.VStack(height=0):
                ui.Spacer(width=0, height=10)
                with ui.HStack(height=0):
                    ui.Spacer()
                    self._text_label = ui.Label(self._text, word_wrap=True, width=self._window.width - 80, height=0)
                    ui.Spacer()
                ui.Spacer(width=0, height=10)
                with ui.HStack(height=0):
                    ui.Spacer(height=0)
                    if self._ok_button_text:
                        ok_button = ui.Button(self._ok_button_text, width=60, height=0)
                        ok_button.set_clicked_fn(self._on_ok_button_fn)
                    if self._middle_button_text:
                        middle_button = ui.Button(self._middle_button_text, width=60, height=0)
                        middle_button.set_clicked_fn(self._on_middle_button_fn)
                    if self._cancel_button_text:
                        cancel_button = ui.Button(self._cancel_button_text, width=60, height=0)
                        cancel_button.set_clicked_fn(self._on_cancel_button_fn)
                    ui.Spacer(height=0)
                ui.Spacer(width=0, height=10)


# -----------------------------------------------------------------------------


def _get_convertible_types(port: Sdf.Path) -> Tuple[List[str], Dict[str, str]]:
    """
    Given an unconnected port, returns the list of types that it could be converted to.
    This does not guarantee matching types, as nodes may have custom resolution
    logic that is not validated. Bundles will return an empty list.

    Args:
        port (Sdf.Path): The path to the port

    Returns:
        Tuple[List[str], Dict[str, str]]: The list of ogn-types and dict of types to titles
    """
    types = []
    titles = {}
    with suppress(og.OmniGraphError):
        attr = og.Controller.attribute(port.pathString)
        if attr:
            extended_type = attr.get_extended_type()
            if extended_type == og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_ANY:
                types = ogn.supported_attribute_type_names()
            if extended_type == og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_UNION:
                types = attr.get_union_types()
            for type_name in types:
                titles[type_name] = type_name.replace("[]", " array")

            if attr.get_resolved_type().base_type != og.BaseDataType.UNKNOWN:
                types.append("unknown")
                titles["unknown"] = "Reset Type"

    return (types, titles)


# -----------------------------------------------------------------------------


def build_port_type_convert_menu(port: Sdf.Path) -> ui.Menu:
    """Builds the menu used to select what data type to convert an extended-type port to

    Args: (Sdf.Path): The path to the port

    Returns:
        ui.Menu: The newly created menu
    """

    def convert_type_fn(attrib_type: str):
        async def fn():
            # Wait for the menu to be dismissed before issuing the resolution command
            await omni.kit.app.get_app().next_update_async()
            og.cmds.ResolveAttrType(attr=port, type_id=attrib_type)

        asyncio.ensure_future(fn())

    k_max_types_for_flat_menu = 8  # More than this number of types required to do All
    k_min_types_for_all_menu = 3  # Any less than this we will not have an "All" menu

    type_tree = {}  # The role submenus

    def _process_type(type_name: str):
        base_type_name, _, _, _ = ogn.split_attribute_type_name(type_name)
        og_type = og.AttributeType.type_from_ogn_type_name(type_name)
        if og_type.role != og.AttributeRole.NONE:
            base_type = og_type.get_role_name()
        else:
            base_type = base_type_name
        type_list = type_tree.setdefault(base_type, [])
        type_list.append(type_name)

    def _populate_from_type_tree(titles: Dict[str, str]):
        for base_type_name, type_list in type_tree.items():
            if not type_list:
                continue
            # single entries in a role group are shown as-is
            if len(type_list) == 1:
                type_name = type_list[0]
                ui.MenuItem(titles[type_name], triggered_fn=partial(convert_type_fn, type_name))
            else:
                base_menu = ui.Menu(base_type_name)
                with base_menu:
                    for type_name in type_list:
                        ui.MenuItem(titles[type_name], triggered_fn=partial(convert_type_fn, type_name))

    tp_menu = ui.Menu("Convert to Type")
    with tp_menu:
        convertible_types, titles = _get_convertible_types(port)
        if len(convertible_types) <= k_max_types_for_flat_menu:
            for type_name in convertible_types:
                ui.MenuItem(titles[type_name], triggered_fn=partial(convert_type_fn, type_name))
        else:
            top_types = []
            for type_name in sorted(convertible_types):
                if type_name in _preferred_types:
                    top_types.append(type_name)
                    continue
                _process_type(type_name)

            want_all_menu = True
            if len(top_types) < k_min_types_for_all_menu:
                # If we have no top level types, then forget the "All" menu. Put those
                # types into the tree instead
                while top_types:
                    _process_type(top_types.pop())
                want_all_menu = False

            if len(type_tree):
                if want_all_menu:
                    all_menu = ui.Menu("All")
                    with all_menu:
                        _populate_from_type_tree(titles)
                else:
                    _populate_from_type_tree(titles)
            if top_types:
                ui.Separator()
                for type_name in top_types:
                    ui.MenuItem(titles[type_name], triggered_fn=partial(convert_type_fn, type_name))
        return tp_menu


# ======================================================================


def find_prop(props: List[UsdPropertyUiEntry], name: str) -> Optional[UsdPropertyUiEntry]:
    """Find the first matching ui_prop from the given list, or None if not found"""
    with suppress(StopIteration):
        return next((p for p in props if p.prop_name == name))
    return None
