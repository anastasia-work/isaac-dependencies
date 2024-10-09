"""
Support for the menu containing the OmniGraph UI operations.
"""
import asyncio
from functools import partial
from typing import List, TypeVar

import carb
import carb.settings
import omni.graph.core as og
import omni.graph.tools as ogt
import omni.kit.ui
import omni.usd
from omni import ui
from omni.kit.app import get_app_interface
from omni.kit.menu.utils import MenuItemDescription
from omni.kit.window.preferences import register_page, unregister_page
from pxr import Sdf

from .metaclass import Singleton  # noqa: PLE0402
from .omnigraph_node_description_editor.main_editor import MENU_PATH as MENU_OGN_EDITOR  # noqa: PLE0402
from .omnigraph_node_description_editor.main_editor import Editor
from .omnigraph_settings_editor import OmniGraphSettingsEditor  # noqa: PLE0402
from .omnigraph_toolkit import MENU_PATH as MENU_TOOLKIT  # noqa: PLE0402
from .omnigraph_toolkit import Toolkit

# Settings

# For now we always have an implicit global graph which encompasses the stage. Once that is deprecated we can
# disable the workaround code by setting this to False
USE_IMPLICIT_GLOBAL_GRAPH = True

# ======================================================================
# Menu item names
MENU_RELOAD_FROM_STAGE = "deprecated"
# ======================================================================

# ==============================================================================================================
# Lookup table for operations triggered by the menu items.
# They are called with (KEY, ENABLE) values, where KEY is the key in this dictionary and ENABLE is a boolean
# where the menu item is triggered when True and "untriggered" when False (i.e. window is opened or closed)
MENU_WINDOWS = {
    MENU_OGN_EDITOR: Editor,
}
TOOLKIT_WINDOW = Toolkit
WindowClassType = TypeVar("WindowClassType", OmniGraphSettingsEditor, Editor, Toolkit)

VISUAL_SCRIPTING_MENU_INDEX_OFFSET = 20
MENU_GRAPH = "menu_graph.svg"

original_svg_color = carb.settings.get_settings().get("/exts/omni.kit.menu.create/original_svg_color")


# ======================================================================
class Menu(metaclass=Singleton):
    """Manage the menu containing OmniGraph operations

    Internal Attributes:
        __menu_items: List of menu trigger subscriptions
        __toolkit_menu_item: Trigger subscription for the optional toolkit menu item
        __windows: Dictionary of menu_item/editor_object for editors the menu can open
        __extension_change_subscription: Subscription to extension changes
    """

    def __init__(self):
        """Initialize the menu by finding the current context and selection information"""
        self.__menu_items = []
        self.__edit_menu_items = []
        self.__create_menu_items = []
        self.__create_graph_menu_tuples = []  # noqa: PLW0238
        self.__context_menus = []  # noqa: PLW0238
        self.__preferences_page = None
        self.__extension_change_subscription = None
        self.__toolkit_menu_item = None
        self.__windows = {}
        self.on_startup()

    # --------------------------------------------------------------------------------------------------------------
    def set_window_state(self, menu: str, value: bool):
        """Trigger the visibility state of the given window object.

           Note: This is not called when the window is manually closed

        Args:
            menu: Name of the menu to which the window class is attached
            value: True means show the window, else hide and destroy

        Note:
            It is assumed that the window_class can be destroyed, has is_visible() and is a singleton
        """
        if value:
            self.__windows[menu].show_window()
        else:
            self.__windows[menu].hide_window()

    def __deferred_set_window_state(self, menu: str, value: bool):
        # We can't modify UI elements safely from callbacks, so defer that work
        async def __func():
            await omni.kit.app.get_app().next_update_async()
            self.set_window_state(menu, value)

        asyncio.ensure_future(__func())

    # --------------------------------------------------------------------------------------------------------------
    @property
    def menu_items(self) -> List[ui.MenuItem]:
        """Returns a list of the menu items owned by this menu class"""
        return self.__menu_items + self.__edit_menu_items

    # --------------------------------------------------------------------------------------------------------------
    def __on_extension_change(self):
        """Callback executed when extensions change state"""
        # Only enable the toolkit debugging window if the inspection extension was enabled since
        # it supplies the features
        inspection_enabled = get_app_interface().get_extension_manager().is_extension_enabled("omni.inspect")
        menu = omni.kit.ui.get_editor_menu()
        if inspection_enabled:
            if self.__toolkit_menu_item is None:
                self.__windows[MENU_TOOLKIT] = TOOLKIT_WINDOW()
                # Toolkit goes to bottom. There are two graph editors and one node description editor
                self.__toolkit_menu_item = menu.add_item(
                    MENU_TOOLKIT,
                    self.__deferred_set_window_state,
                    priority=4 + VISUAL_SCRIPTING_MENU_INDEX_OFFSET,
                    toggle=True,
                    value=False,
                )
        else:
            ogt.destroy_property(self, "__toolkit_menu_item")

    # --------------------------------------------------------------------------------------------------------------
    # Used to be OnClick function for reload from stage menu item
    # The item is no longer available to external customers but we can keep it alive internally
    def _on_menu_click(self, menu_item, value):
        if menu_item == MENU_RELOAD_FROM_STAGE:
            usd_context = omni.usd.get_context()
            selection = usd_context.get_selection()
            selected_prim_paths = selection.get_selected_prim_paths()
            found_selected_graph = False
            if selected_prim_paths:
                all_graphs = og.get_all_graphs()
                for selected_path in selected_prim_paths:
                    for graph in all_graphs:
                        if graph.get_path_to_graph() == selected_path:
                            found_selected_graph = True
                            carb.log_info(f"reloading graph: '{selected_path}'")
                            graph.reload_from_stage()

            if not found_selected_graph:
                current_graph = og.get_all_graphs()[0]
                current_graph_path = current_graph.get_path_to_graph()
                carb.log_info(f"reloading graph: '{current_graph_path}'")
                current_graph.reload_from_stage()

    @classmethod
    def add_create_menu_type(cls, menu_title: str, evaluator_type: str, prefix: str, glyph_file: str, open_editor_fn):
        if cls not in cls._instances:  # noqa: PLE1101
            return

        instance = cls._instances[cls]  # noqa: PLE1101

        instance.__create_graph_menu_tuples.append(  # noqa: PLW0212,PLW0238
            (menu_title, evaluator_type, prefix, glyph_file, open_editor_fn)
        )

        # A wrapper to the create_graph function. Create the graph first and then open that graph
        def onclick_fn(evaluator_type: str, name_prefix: str, open_editor_fn, menu_arg=None, value=None):
            node = instance.create_graph(evaluator_type, name_prefix)
            if open_editor_fn:
                stage = omni.usd.get_context().get_stage()
                prim = stage.GetPrimAtPath(node.get_wrapped_graph().get_path_to_graph())
                open_editor_fn([prim])

        def build_context_menu(objects):
            with omni.ui.Menu(f' {omni.kit.ui.get_custom_glyph_code("${glyphs}/" + MENU_GRAPH)}   Visual Scripting'):
                for (
                    title,
                    evaluator_type,
                    prefix,
                    glyph_file,
                    _open_editor_fn,
                ) in instance.__create_graph_menu_tuples:  # noqa: PLW0212,E501
                    omni.ui.MenuItem(
                        f' {omni.kit.ui.get_custom_glyph_code("${glyphs}/" + f"{glyph_file}")}   {title}',
                        triggered_fn=partial(onclick_fn, evaluator_type, prefix, _open_editor_fn, objects),
                    )

        # First time to add items to create menu, need to create the Visual Scripting submenu
        if not instance.__context_menus:  # noqa: PLW0212
            menu_dict = {
                "name": "Omnigraph Context Create Menu",
                "glyph": MENU_GRAPH,
                "populate_fn": build_context_menu,
            }
            instance.__context_menus.append(  # noqa: PLW0212
                omni.kit.context_menu.add_menu(menu_dict, "CREATE", "omni.kit.widget.stage")
            )
            instance.__context_menus.append(  # noqa: PLW0212
                omni.kit.context_menu.add_menu(menu_dict, "CREATE", "omni.kit.window.viewport")
            )

        if not instance.__create_menu_items:  # noqa: PLW0212
            instance.__create_menu_items.append(  # noqa: PLW0212
                MenuItemDescription(
                    name="Visual Scripting",
                    glyph=MENU_GRAPH,
                    appear_after=["Xform"],
                    sub_menu=[
                        MenuItemDescription(
                            name=title,
                            glyph=glyph_file,
                            onclick_fn=partial(onclick_fn, evaluator_type, prefix, _open_editor_fn),
                            original_svg_color=original_svg_color,
                        )
                        for (
                            title,
                            evaluator_type,
                            prefix,
                            glyph_file,
                            _open_editor_fn,
                        ) in instance.__create_graph_menu_tuples  # noqa: PLW0212
                    ],
                    original_svg_color=original_svg_color,
                )
            )
            omni.kit.menu.utils.add_menu_items(instance.__create_menu_items, "Create", -9)  # noqa: PLW0212
        else:
            instance.__create_menu_items[0].sub_menu.append(  # noqa: PLW0212
                MenuItemDescription(
                    name=menu_title,
                    glyph=glyph_file,
                    onclick_fn=partial(onclick_fn, evaluator_type, prefix, open_editor_fn),
                    original_svg_color=original_svg_color,
                )
            )

            omni.kit.menu.utils.rebuild_menus()

    @classmethod
    def remove_create_menu_type(cls, menu_title: str):
        if cls not in cls._instances:  # noqa: PLE1101
            return

        instance = cls._instances[cls]  # noqa: PLE1101

        instance.__create_graph_menu_tuples = [  # noqa: PLW0212,PLW0238
            item for item in instance.__create_graph_menu_tuples if item[0] != menu_title  # noqa: PLW0212
        ]

        if not instance.__create_menu_items:  # noqa: PLW0212
            return

        if len(instance.__create_graph_menu_tuples) == 0:  # noqa: PLW0212
            omni.kit.menu.utils.remove_menu_items(instance.__create_menu_items, "Create")  # noqa: PLW0212
            ogt.destroy_property(instance, "__context_menus")
            ogt.destroy_property(instance, "__create_menu_items")
        else:
            instance.__create_menu_items[0].sub_menu = [  # noqa: PLW0212
                item for item in instance.__create_menu_items[0].sub_menu if item.name != menu_title  # noqa: PLW0212
            ]
            omni.kit.menu.utils.rebuild_menus()

    # --------------------------------------------------------------------------------------------------------------
    def on_startup(self):
        """Called when the menu is invoked - build all of the menu entries"""
        self._settings = carb.settings.get_settings()
        editor_menu = omni.kit.ui.get_editor_menu()
        # In a testing environment there may not be an editor, but that's okay
        if editor_menu is None:
            return

        # Add settings page to preference
        self.__preferences_page = OmniGraphSettingsEditor()
        register_page(self.__preferences_page)

        for index, (menu_path, menu_window) in enumerate(MENU_WINDOWS.items()):
            self.__windows[menu_path] = menu_window()
            self.__menu_items.append(
                editor_menu.add_item(
                    menu_path,
                    self.__deferred_set_window_state,
                    priority=index + 1 + VISUAL_SCRIPTING_MENU_INDEX_OFFSET,
                    toggle=True,
                    value=False,
                )
            )

        # Set up a subscription to monitor for events that may change whether the toolkit is visible or not
        change_stream = get_app_interface().get_extension_manager().get_change_event_stream()
        self.__extension_change_subscription = change_stream.create_subscription_to_pop(
            lambda _: self.__on_extension_change(), name="OmniGraph Menu Extension Changes"
        )
        assert self.__extension_change_subscription
        # Ensure the initial state is correct
        self.__on_extension_change()

    # --------------------------------------------------------------------------------------------------------------
    def on_shutdown(self):
        """Remove all of the menu objects when the menu is closed"""
        self.__extension_change_subscription = None
        if self.__preferences_page:
            unregister_page(self.__preferences_page)
        self.__preferences_page = None
        # Remove all of the menu items from the main menu. Most important when removing callbacks
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            for menu in self.__windows:
                editor_menu.remove_item(menu)
            if self.__toolkit_menu_item is not None:
                editor_menu.remove_item(MENU_TOOLKIT)
        omni.kit.menu.utils.remove_menu_items(self.__create_menu_items, "Create")
        ogt.destroy_property(self, "__create_menu_items")
        ogt.destroy_property(self, "__extension_change_subscription")
        ogt.destroy_property(self, "__toolkit_menu_item")
        ogt.destroy_property(self, "__menu_items")
        ogt.destroy_property(self, "__edit_menu_items")
        ogt.destroy_property(self, "__context_menus")
        ogt.destroy_property(self, "__create_graph_menu_tuples")
        ogt.destroy_property(self, "__windows")
        # Note that Singleton.forget(Menu) has to be called in the main shutdown since it has a Menu reference

    # --------------------------------------------------------------------------------------------------------------
    def create_graph(self, evaluator_type: str, name_prefix: str, menu_arg=None, value=None) -> og.Node:
        """Create a new GlobalGraph below the default prim

        Args:
            evaluator_type: the evaluator type to use for the new graph
            name_prefix: the desired name of the GlobalGraph node. Will be made unique
            menu_arg: menu info
            value: menu value
        Returns:
            wrapper_node: the node that wraps the new graph
        """
        # FIXME: How to specify USD backing?
        usd_backing = True
        usd_context = omni.usd.get_context()
        stage = usd_context.get_stage()
        graph_path = Sdf.Path(name_prefix).MakeAbsolutePath(Sdf.Path.absoluteRootPath)
        graph_path = omni.usd.get_stage_next_free_path(stage, graph_path, True)

        orchestration_graphs = og.get_global_orchestration_graphs()
        # FIXME: Just use the first one? We may want a clearer API here.
        orchestration_graph = orchestration_graphs[0]
        with omni.kit.undo.group():
            _, wrapper_node = og.cmds.CreateGraphAsNode(
                graph=orchestration_graph,
                node_name=Sdf.Path(graph_path).name,
                graph_path=graph_path,
                evaluator_name=evaluator_type,
                is_global_graph=True,
                backed_by_usd=usd_backing,
                fc_backing_type=og.GraphBackingType.GRAPH_BACKING_TYPE_FABRIC_SHARED,
                pipeline_stage=og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_SIMULATION,
            )

        return wrapper_node


def add_create_menu_type(menu_title: str, evaluator_type: str, prefix: str, glyph_file: str, open_editor_fn):
    """Add a new graph type menu item under Create/Visual Scripting menu which creates a new graph and open the graph.
    This will create the Visual Scripting menu if menu_title is the first one added

    Args:
        menu_title: the display name of this menu item
        evaluator_type: the evaluator type to use for the new graph
        prefix: the desired name of the GlobalGraph node. Will be made unique
        glyph_file: the file name of the svg icon to be displayed. This file must be in the resources package
        open_editor_fn: the function to open the corresponding graph editor and open the created graph.
        This is invoked after create_graph

    """
    Menu.add_create_menu_type(menu_title, evaluator_type, prefix, glyph_file, open_editor_fn)


def remove_create_menu_type(menu_title: str):
    """
    Remove the menu item named menu_title from Create/Visual Scripting menu.
    This will remove the entire Visual Scripting menu if menu_title is the last one under it.

    Args:
        menu_title: the display name of this menu item
    """
    Menu.remove_create_menu_type(menu_title)
