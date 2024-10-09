import omni.kit.ui
import omni.ui as ui
from functools import partial
from pxr import UsdGeom, Sdf, PhysxSchema

"""
* Note: The dual menu functionality is removed at the moment and will probably never return. It still makes sense
* to use WindowMenuItem for our windows though, since that enables us to apply any menu API changes at one place.

Helper to handle a dynamically spawned ui.Window controlled with two menu items (one in the
Window/Physics submenu, the other in Physics submenu). Both menu items are synchronized to show
the visibility toggle of the window correctly + if the user hides the window manually the menu
items will get updated too. Helper will call on_shutdown on the child window if such method
is present.

note: WindowMenuItem will use set_visibility_changed_fn callback on the spawned window, so if you want
callbacks on that too you can use window_visibility_changed_fn on construction or set_window_visibility_changed_fn,
since ui.Window:set_visibility_changed_fn does not support multiple listeners

Args:
    menu_path: relative menu path
    spawn_window_fn: function that returns created ui.Window instance
    spawn_immediately: window will spawn either immediately with the helper's creation or only after the user selects
                       one of the menu items for the first time
    additional_physmenu_path: additional path added after the Physics/ menu item path
    window_visibility_changed_fn:


Example:

class PhysXDebugView():
    def __init__(self):
        self._menu = WindowMenuItem("PhysX Debug", lambda: PhysxDebugWindow(), spawn_immediately)

    def on_shutdown(self):
        self._menu.on_shutdown()
        self._menu = None

class PhysxDebugWindow(ui.Window):
    def __init__(self):
        ...

    def on_shutdown(self):
        ...
"""


class WindowMenuItem():
    def __init__(self, menu_path, spawn_window_fn, spawn_immediately=False, additional_physmenu_path="", window_visibility_changed_fn=None):
        self._menu_path_win = f"Window/Physics/{menu_path}"

        editor_menu = omni.kit.ui.get_editor_menu()
        self._menu_win = editor_menu.add_item(self._menu_path_win, self._on_menu_click, True)

        self._spawn_window_fn = spawn_window_fn
        self._window = None
        self._window_visibility_changed_fn = window_visibility_changed_fn

        if spawn_immediately:
            self._toggle_menu_items(True)
            self._spawn_window()

    def set_window_visibility(self, visibility : bool):
        self.show_window() if visibility else self.hide_window()

    def hide_window(self):
        if self._window is None:
            return

        if isinstance(self._window, ui.Window):
            self._window.visible = False
        else:
            self._window.hide()

    def show_window(self):
        if self._window is None:
            # if called externally
            self._toggle_menu_items(True)
            self._spawn_window()
            return

        if isinstance(self._window, ui.Window):
            self._window.visible = True
            self._window.focus()
        else:
            self._window.show()

    def on_shutdown(self):
        self._window_visibility_changed_fn = None
        if self._window is not None:
            if hasattr(self._window, "on_shutdown"):
                self._window.on_shutdown()
            self.hide_window()
            self._window = None
        self._menu_win = None

    def set_window_visibility_changed_fn(self, fn):
        self._window_visibility_changed_fn = fn

    def _spawn_window(self):
        self._window = self._spawn_window_fn()
        self._window.set_visibility_changed_fn(self._on_visibility_changed)

    def _toggle_menu_items(self, toggled):
        editor_menu = omni.kit.ui.get_editor_menu()
        editor_menu.set_value(self._menu_path_win, toggled)

    def _on_menu_click(self, menu, toggled):
        self._toggle_menu_items(toggled)

        if toggled:
            if self._window is None:
                self._spawn_window()
            else:
                self.show_window()
        else:
            self.hide_window()

    def _on_visibility_changed(self, visible):
        if self._window_visibility_changed_fn is not None:
            self._window_visibility_changed_fn(visible)
        self._toggle_menu_items(visible)
