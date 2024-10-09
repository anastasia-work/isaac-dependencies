"""
Standard file used to manage extension load and unload
"""
from pathlib import Path

import carb
import omni.ext
import omni.kit

from .compute_node_widget import ComputeNodeWidget
from .menu import Menu
from .metaclass import Singleton
from .properties_widget import OmniGraphProperties
from .test_populator import TestPopulateFromFile


# ==============================================================================================================
class _PublicExtension(omni.ext.IExt):
    """Standard extension support class, necessary for extension management"""

    TestRunnerWindow = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__menu = None
        self.__widget = None
        self._properties = None
        self._exts_window_initialized = False
        self._hook_exts_window = None
        self._hook_stage = None
        self._hook_test_window = None
        self._test_populator = None

    def register_stage_icon(self):
        """Register the icon used in the stage widget for OmniGraph Prims"""
        try:
            import omni.kit.widget.stage  # noqa: PLW0621
        except ImportError:
            # No stage widget, no need to register icons
            return
        stage_icons = omni.kit.widget.stage.StageIcons()
        current_path = Path(__file__).parent
        icon_path = current_path.parent.parent.parent.parent.joinpath("icons")
        style = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"
        icon_path = icon_path.joinpath(style)

        for file_name, prim_type in [("OmniGraph.svg", "OmniGraph")]:
            file_path = icon_path.joinpath(file_name)
            stage_icons.set(prim_type, file_path)

    def _add_populator(self):
        if not self._test_populator:
            manager = omni.kit.app.get_app().get_extension_manager()
            if manager.is_extension_enabled("omni.kit.window.tests"):
                from omni.kit.window.tests import TestRunnerWindow

                self.TestRunnerWindow = TestRunnerWindow
                self._test_populator = TestPopulateFromFile()
                TestRunnerWindow.add_populator(self._test_populator)

    def _remove_populator(self):
        if self.TestRunnerWindow and self._test_populator:
            self.TestRunnerWindow.remove_populator(self._test_populator.name)
            self.TestRunnerWindow = None
            self._test_populator = None

    def _extensions_window_setup(self):
        # Addition of OmniGraph functionality to the extension window
        if not self._exts_window_initialized:
            from omni.kit.window.extensions import ExtsWindowExtension

            from .omnigraph_in_extension_window import OmniGraphPage, clear_omnigraph_caches, has_omnigraph_nodes

            ComputeNodeWidget.get_instance().add_template_path(__file__)
            ExtsWindowExtension.add_tab_to_info_widget(OmniGraphPage)
            ExtsWindowExtension.add_searchable_keyword(
                "@omnigraph",
                "Uses OmniGraph",
                has_omnigraph_nodes,
                clear_omnigraph_caches,
            )
            self._exts_window_initialized = True

    def _extensions_window_cleanup(self):
        if self._exts_window_initialized:
            from omni.kit.window.extensions import ExtsWindowExtension

            from .omnigraph_in_extension_window import OmniGraphPage

            ExtsWindowExtension.remove_searchable_keyword("@omnigraph")
            ExtsWindowExtension.remove_tab_from_info_widget(OmniGraphPage)
            self._exts_window_initialized = False

    def on_startup(self):
        """Callback executed when the extension is starting up. Create the menu that houses the UI functionality"""
        self.__menu = Menu()
        self.__widget = ComputeNodeWidget()
        self._properties = OmniGraphProperties()
        self._test_populator = None

        # Callback to set up the OmniGraph stage window icon
        manager = omni.kit.app.get_app().get_extension_manager()
        self._hook_stage = manager.subscribe_to_extension_enable(
            on_enable_fn=lambda _: self.register_stage_icon(),
            ext_name="omni.kit.widget.stage",
            hook_name="omni.graph.ui.stage",
        )

        # We need to allow for apps which don't include the extensions window. So we only use
        # it if its extension is loaded.
        self._hook_exts_window = manager.subscribe_to_extension_enable(
            on_enable_fn=lambda _: self._extensions_window_setup(),
            on_disable_fn=lambda _: self._extensions_window_cleanup(),
            ext_name="omni.kit.window.extensions",
            hook_name="omni.graph.ui.exts_window",
        )

        # Addition of test population from a file to the test runner window.
        # If the window extension is already enabled there will still be a callback so this is all that is needed.
        self._hook_test_window = manager.subscribe_to_extension_enable(
            on_enable_fn=lambda _: self._add_populator(),
            on_disable_fn=lambda _: self._remove_populator(),
            ext_name="omni.kit.window.tests",
            hook_name="omni.graph.ui.window",
        )

    def on_shutdown(self):
        """Callback executed when the extension is being shut down. The menu will clean up the dangling editors"""
        self._hook_exts_window = None
        self._extensions_window_cleanup()

        self.__menu.on_shutdown()
        self.__menu = None
        # Must do this here to avoid the dangling reference
        Singleton.forget(Menu)

        self.__widget.on_shutdown()
        self.__widget = None

        self._properties.on_shutdown()
        self._properties = None

        self._hook_stage = None
        self._hook_test_window = None

        self._remove_populator()

        if self._test_populator:
            self._test_populator.destroy()
            self._test_populator = None
