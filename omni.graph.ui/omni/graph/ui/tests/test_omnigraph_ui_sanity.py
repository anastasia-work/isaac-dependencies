"""
Tests that do basic sanity checks on the OmniGraph UI
"""
import omni.graph.core as og
import omni.graph.core.tests as ogts
import omni.graph.tools as ogt
import omni.kit.test
import omni.usd
from carb import log_warn

from .._impl.menu import MENU_WINDOWS, Menu
from .._impl.omnigraph_node_description_editor.main_editor import Editor

# Data-driven information to allow creation of all windows without specifics.
# This assumes every class has a static get_name() method so that prior existence can be checked,
# and a show_window() or show() method which displays the window.
#
# Dictionary key is the attribute name in the test class under which this window is stored.
# Value is a list of [class, args] where:
#   ui_class: Class type that instantiates the window
#   args: Arguments to be passed to the window's constructor
#
ALL_WINDOW_INFO = {"_ogn_editor_window": [Editor, []]}


# ======================================================================
class TestOmniGraphUiSanity(ogts.OmniGraphTestCase):
    """Encapsulate simple sanity tests"""

    # ----------------------------------------------------------------------
    async def test_open_and_close_all_omnigraph_ui(self):
        """Open and close all of the OmniGraph UI windows as a basic sanity check

        In order for this test to work all of the UI management classes must support these methods:
            show(): Build and display the window contents
            destroy(): Close the window and destroy the window elements
        And the classes must derive from (metaclass=Singleton) to avoid multiple instantiations
        """

        class AllWindows:
            """Encapsulate all of the windows to be tested in an object for easier destruction"""

            def __init__(self):
                """Open and remember all of the windows (closing first if they were already open)"""

                # The graph window needs to be passed a graph.
                graph_path = "/World/TestGraph"
                og.Controller.edit({"graph_path": graph_path, "evaluator_name": "push"})

                for (member, (ui_class, args)) in ALL_WINDOW_INFO.items():
                    setattr(self, member, ui_class(*args))

            async def show_all(self):
                """Find all of the OmniGraph UI windows and show them"""
                for (member, (ui_class, _)) in ALL_WINDOW_INFO.items():
                    window = getattr(self, member)
                    show_fn = getattr(window, "show_window", getattr(window, "show", None))
                    if show_fn:
                        show_fn()
                        # Wait for an update to ensure the window has been opened
                        await omni.kit.app.get_app().next_update_async()
                    else:
                        log_warn(f"Not testing type {ui_class.__name__} - no show_window() or show() method")

            def destroy(self):
                """Destroy the members, which cleanly destroys the windows"""
                for member in ALL_WINDOW_INFO:
                    ogt.destroy_property(self, member)

        all_windows = AllWindows()
        await all_windows.show_all()

        await omni.kit.app.get_app().next_update_async()

        all_windows.destroy()
        all_windows = None

    # ----------------------------------------------------------------------
    async def test_omnigraph_ui_menu(self):
        """Verify that the menu operations all work"""
        menu = Menu()
        for menu_path in MENU_WINDOWS:
            menu.set_window_state(menu_path, True)
            await omni.kit.app.get_app().next_update_async()
            menu.set_window_state(menu_path, False)

    async def test_omnigraph_ui_node_creation(self):
        """Check that all of the registered omni.graph.ui nodes can be created without error."""
        graph_path = "/World/TestGraph"
        (graph, *_) = og.Controller.edit({"graph_path": graph_path, "evaluator_name": "push"})

        # Add one of every type of omni.graph.ui node to the graph.
        node_types = [t for t in og.get_registered_nodes() if t.startswith("omni.graph.ui")]
        prefix_len = len("omni.graph.ui_nodes.")
        node_names = [name[prefix_len:] for name in node_types]

        (_, nodes, _, _) = og.Controller.edit(
            graph, {og.Controller.Keys.CREATE_NODES: list(zip(node_names, node_types))}
        )
        self.assertEqual(len(nodes), len(node_types), "Check that all nodes were created.")

        for i, node in enumerate(nodes):
            self.assertEqual(
                node.get_prim_path(), graph_path + "/" + node_names[i], f"Check node type '{node_types[i]}'"
            )
