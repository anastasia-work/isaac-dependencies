import sys, os, inspect, importlib
import omni.kit.app
import omni.kit.stage_templates
import omni.kit.ui
import omni.kit.commands
import omni.kit.window
import omni.kit.window.file
import omni.usd
import carb
import carb.settings
import omni.ext
from fnmatch import fnmatch
from omni import ui
from collections import defaultdict, OrderedDict
from omni.physx import get_physx_interface
from omni.physx.scripts.pythonUtils import get_all_submodules
from omni.physxui.scripts.ui import WindowMenuItem
from omni.physxui.scripts.utils import cleanup_fp_dialog
from omni.physxui.scripts.settings import load_physics_settings_from_stage
from omni.kit.window.filepicker import FilePickerDialog
from pxr import Sdf, Usd, UsdUtils, Gf, UsdGeom, UsdPhysics
from functools import partial
import importlib
import types
import queue
import omni.physx.bindings._physx as pb
from omni.kit.widget.text_editor import TextEditor
import omni.kit.viewport.utility as vp_utils
from omni.kit.viewport.utility.camera_state import ViewportCameraState
import asyncio
from omni.physxdemos.utils.room_helper import RoomHelper, RoomInstancer

"""
Each demo:
*] Must be inherited from the demo.Base class.
*] Must set its category to one from the base.Categories enum.
*] Defines a create method, which sets up the demo.
*] May define configurable parameters for the create method (see demo.Base.params).
*] May define an update method (called every frame), an on_startup method or an on_shutdown method (called before the
   demo stage is created and when the demo stage is closed).

Each folder(package) with demos:
*] Must have an __init__.py file with the __all__ variable filled with the result of demo.get_all_submodules(__file__).
If for any reason you don't want to use this helper you have to fill it manually with all the demo modules you want to include.
*] Must be registered using demo.register() and unregistered using demo.unregister(), prefferably at the time the extension
is loaded or unloaded.
"""


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        developer_mode = carb.settings.get_settings().get("physics/developmentMode")

        self._demo_menu = WindowMenuItem("Demo Scenes", lambda: Manager(), developer_mode)

        omni.ui.Workspace.set_show_window_fn(Manager.get_window_name(), self._demo_menu.set_window_visibility)

    def on_shutdown(self):
        # Deregister the function that shows the window from omni.ui
        omni.ui.Workspace.set_show_window_fn(Manager.get_window_name(), None)

        self._demo_menu.on_shutdown()
        self._demo_menu = None

        if Manager.instance:
            Manager.instance.shutdown()


DEMO_MODULES = ["omni.physxdemos.scenes"]


def register(module_name):
    DEMO_MODULES.append(module_name)
    if Manager.instance is not None:
        Manager.instance.refresh_scenes()


def unregister(module_name):
    try:
        DEMO_MODULES.remove(module_name)
        if Manager.instance is not None:
            Manager.instance.refresh_scenes()
    except ValueError:
        carb.log_warn(f"omni.physx.demos: {module_name} was not found and cannot be unregistered")


def execute_demo(demo_title, demo_config_parameters=None):
    """
    Runs demo with title demo_title (see omni.physxdemos.Base.title).

    Args:
    demo_config_parameters: Optional dict with {param_name: value, ...}, where param_name corresponds to the demo
                            load-time config parameter name (see omni.physxdemos.Base.params) that will be passed on
                            to its create method.
    """
    try:
        if Manager.instance is not None:
            Manager.instance.execute_scene(demo_title, demo_config_parameters)
        else:
            carb.log_warn("omni.physx.demos: Manager instance is not alive")
    except ValueError:
        carb.log_warn(f"omni.physx.demos: {demo_title} was not found and cannot be executed")


async def __test_demo_class(demo_class, before_stage_async_fn = None, after_stage_async_fn = None, curr_params={}):
    def on_stage_opened(demo_instance, res, err):
        stage = Manager.instance._usd_context.get_stage()
        demo_instance.on_startup()

        args = {}
        if isinstance(demo_instance.params, list):
            for param_dict in demo_instance.params:
                for key, param in param_dict.items():
                    args[key] = param.val
        else:
            args = {key: param.val for key, param in demo_instance.params.items()}

        args.update(curr_params)
        Manager.instance._set_base_stage(stage)
        demo_instance.create(stage, **args)

        nonlocal update_sub
        update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            Manager.instance._on_update,
            name="omni.physx demo test update"
        )

        nonlocal stage_opened
        stage_opened = True

    demo_instance = None
    update_sub = None
    stage_opened = False

    try:
        if before_stage_async_fn is not None:
            await before_stage_async_fn(demo_class)

        demo_instance = demo_class()
        demo_instance._is_test = True
        Manager.open_new_stage(demo_instance, partial(on_stage_opened, demo_instance))

        # wait until the stage is opened, this might take some frames, so have some leeway
        wait_frames = 100
        for _ in range(0, wait_frames):
            await omni.kit.app.get_app().next_update_async()
            if stage_opened:
                break

        if not stage_opened:
            raise Exception(f"Stage not opened in {wait_frames} frames")

        Manager.instance._demo_instance = demo_instance
        Manager.instance._first_update = True

        if after_stage_async_fn is not None:
            await after_stage_async_fn(demo_class)
    finally:
        Manager.instance._demo_instance = None

        if demo_instance is not None:
            demo_instance.on_shutdown()

    Manager.instance._usd_context.close_stage()
    await omni.kit.app.get_app().next_update_async()

    update_sub = None
    demo_instance = None


async def test_demo(demo_class_module_name, before_stage_async_fn = None, after_stage_async_fn = None, curr_params={}):
    """
    Utility for testing a single demo.

    Args:
    demo_class_module_name: Demo class module name.
    before_stage_async_fn: Callback before each demo stage is opened.
    after_stage_async_fn: Callback after each demo stage is opened. This is where you typically do your testing.
    params: Dictionary of demo parameter overrides.
    """
    if Manager.instance is None:
        carb.log_error("Demo manager instance does not exist")
        return

    demo_class = Manager.instance._scenes.get(demo_class_module_name)
    if not demo_class:
        carb.log_error(f"Unable to find {demo_class_module_name}")

    await __test_demo_class(demo_class, before_stage_async_fn, after_stage_async_fn, curr_params)


async def test(module_name, before_stage_async_fn = None, after_stage_async_fn = None, exclude_list = [], params = {},
               test_case = None, inspect_offset=1):
    """
    Utility for easily testing demos. Run all demos in sequence where module_name is a part of its scene class module name

    Args:
    module_name: All demos where module_name is a part of the scene class module name will be included.
    before_stage_async_fn: Callback before each demo stage is opened.
    after_stage_async_fn: Callback after each demo stage is opened. This is where you typically do your testing.
    exclude_list: Exclude all demos with strings in exclude list a part of their scene class module name.
    params: Override default params. Keys are exact scene class module names, Values are a dictionary or a list of
            dictionaries of params. When multiple dictionaries are defined a single scene class will be run multiple times
            with changed params.
    test_case: Enables explicit subTest calls (needs test_case instance)
    inspect_offset: Offset into stack to get correct test function caller for subTest naming (1 is default and will get
                    the name of the direct caller of this function)
    """
    if Manager.instance is None:
        carb.log_error("Demo manager instance does not exist")
        return

    def include_demo(scene_class_module):
        for exclude in exclude_list:
            if exclude in scene_class_module:
                return False
        if module_name in scene_class_module:
            return True
        return False

    async def test_demo(curr_name):
        curr_params = params.get(curr_name)
        if curr_params is None:
            await __test_demo_class(scene_class, before_stage_async_fn, after_stage_async_fn, params)
        else:
            if isinstance(curr_params, list):
                for sub_params in curr_params:
                    await __test_demo_class(scene_class, before_stage_async_fn, after_stage_async_fn, sub_params)
            else:
                await __test_demo_class(scene_class, before_stage_async_fn, after_stage_async_fn, curr_params)

    for scene_class in Manager.instance._scenes.values():
        curr_name = scene_class.__module__
        if include_demo(curr_name):
            if test_case is not None:
                with test_case.subTest(curr_name, test_name=inspect.stack()[inspect_offset][0].f_code.co_name) as include:
                    if include:
                        await test_demo(curr_name)
            else:
                await test_demo(curr_name)


class Manager(ui.Window):
    # TODO: rewrite this to get_instance and check for the ext being started
    instance = None

    def __new__(cls, *args, **kwargs):
        return cls.instance if cls.instance else super().__new__(cls, *args, **kwargs)

    def get_window_name() -> str:
        return "Physics Demo Scenes"

    def __init__(self):
        if Manager.instance:
            # make sure to init only once
            return

        super().__init__(Manager.get_window_name(), ui.DockPreference.LEFT_BOTTOM, width=960, height=600)
        self.deferred_dock_in("Content", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)

        Manager.instance = self
        self._usd_context = omni.usd.get_context()
        self._selected_demo_class = None
        self._demo_instance = None

        self._first_update = False
        self._apply_kit_settings = False
        self._kit_settings_backup = {}

        self._window_src = None
        self._src_path_label = None
        self._src_code_label = None

        stage_event_stream = self._usd_context.get_stage_event_stream()
        self._stage_event_sub = stage_event_stream.create_subscription_to_pop(self._on_stage_event)

        self._build_main_ui()

    def shutdown(self):
        Manager.instance = None
        self._usd_context = None
        self._update_sub = None
        self._selected_demo_class = None

        if self._demo_instance:
            self._demo_instance.on_shutdown()
            self._demo_instance = None
        self._stage_event_sub = None

        self._release_ui()

    def refresh_scenes(self):
        self._build_main_frame()

    def execute_scene(self, demo_title, demo_config_parameters=None, check_unsaved=False, apply_kit_settings=False):
        for scene in self._scenes.values():
            if scene.title == demo_title:
                print("Executing scene: " + demo_title)
                self._tags_stack.visible = True
                self._info_stack.visible = False
                self._selected_demo_class = scene
                self._refresh_config()
                if demo_config_parameters is not None:
                    for key, value in demo_config_parameters.items():
                        if key in self._config_params:
                            self._config_params[key].set_value(value)
                        else:
                            print(f"execute_scene got unknown demo config parameter {key}")
                self._open_new_stage_with_scene(check_unsaved, apply_kit_settings)
                return
        print("Demo not found: " + demo_title)

    def _add_sub_to_update(self):
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="omni.physx demo update"
        )

    """
    Loads all demos that can be found through browsing the attributes of DEMO_MODULES found in sys.modules.
    Expects that each demo module sets its __all__ variable so that importlib.__import__ can register
    the submodules automatically.
    """

    def _load_scenes(self):
        class CategoryData:
            def __init__(self):
                self.subcategories = {}
                self.scenes = []

        self._category_data = {}
        self._scenes = {}
        self._tags = set()
        self._tags_sorted = []

        def add_if_class_is_demo(scene_class):
            if issubclass(scene_class, Base) and scene_class.category is not Categories.NONE:
                cats = scene_class.category.split("/")
                curr_subs = self._category_data
                for cat in cats:
                    data = curr_subs.get(cat)
                    if data is None:
                        curr_subs[cat] = CategoryData()
                        data = curr_subs[cat]
                    curr_subs = data.subcategories
                data.scenes.append(scene_class)
                self._scenes[scene_class.__module__] = scene_class
                self._tags.update(scene_class.tags)
                return True
            return False

        for module in DEMO_MODULES:
            try:
                importlib.__import__(module, fromlist=['*'])
            except Exception as err:
                carb.log_error(f"Demo loader: {err}")
                continue

            scenes_module = sys.modules[module]
            for module_name in dir(scenes_module):
                attr = getattr(scenes_module, module_name, None)
                if attr is not None:
                    if inspect.isclass(attr) and add_if_class_is_demo(attr):
                        # attr can be a demo class directly
                        continue
                    else:
                        # or we can try iterating over submodules of a module
                        for _, scene_class in inspect.getmembers(attr, inspect.isclass):
                            add_if_class_is_demo(scene_class)

        self._tags_sorted = sorted(self._tags)

    class SceneItem(ui.AbstractItem):
        def __init__(self, scene_class):
            super().__init__()
            title = scene_class.title if scene_class.title != "" else scene_class.__name__
            self.name_model = ui.SimpleStringModel(title)
            self.children = []
            self.scene_class = scene_class
            description = scene_class.short_description
            self.scene_description = ui.SimpleStringModel(description)
            self.filtered = True
            self.scene_tags = ui.SimpleStringModel(", ".join(scene_class.tags))
            self.tags_set = set(scene_class.tags)
            self.filter_string = f"{scene_class.title}|{scene_class.short_description}|{scene_class.category}"

        def get_branch_text(self, expanded):
            return ""

        def update_filter(self, filters, tag):
            if tag:
                self.filtered = filters in self.tags_set
            else:
                self.filtered = all([not fnmatch(self.filter_string, f[1])^f[0] for f in filters])

        def is_filtered(self):
            return self.filtered

        def get_children(self):
            return self.children

    class LineItem(ui.AbstractItem):
        def update_filter(self, *_):
            ...

        def get_children(self):
            return []

        def is_filtered(self):
            return True

    class CategoryItem(ui.AbstractItem):
        def __init__(self, text, data):
            super().__init__()
            self.name_model = ui.SimpleStringModel(text)
            data.scenes.sort(key=lambda elem: elem.title)
            names = sorted(data.subcategories.keys())
            self.children_base = [Manager.CategoryItem(text, data.subcategories[text]) for text in names]
            self.children_base += [Manager.SceneItem(scene) for scene in data.scenes]
            self.children = self.children_base

        def get_branch_text(self, expanded):
            return ("-" if expanded else "+") if len(self.children) != 0 else " "

        def update_filter(self, filters, tag):
            for c in self.children_base:
                c.update_filter(filters, tag)

            self.children = [c for c in self.children_base if c.is_filtered()]

        def get_children(self):
            return self.children

        def is_filtered(self):
            return len(self.children)

    class RootItem(ui.AbstractItem):
        def __init__(self, data):
            super().__init__()

            self.children_base = [Manager.CategoryItem(str(n), data[n]) for n in CATEGORY_ORDER if data.get(n)]
            self.line = [Manager.LineItem()]
            names_sec = [n for n in data.keys() if n not in CATEGORY_ORDER]
            self.children_base_sec = [Manager.CategoryItem(str(n), data[n]) for n in names_sec]
            add_line = self.children_base and self.children_base_sec
            self.children = self.children_base + (self.line if add_line else []) + self.children_base_sec

        def update_filter(self, filters, tag=False):
            for c in self.children_base:
                c.update_filter(filters, tag)

            for c in self.children_base_sec:
                c.update_filter(filters, tag)

            self.children = []
            curr_base = [c for c in self.children_base if c.is_filtered()]
            sec_base = [c for c in self.children_base_sec if c.is_filtered()]
            add_line = curr_base and sec_base
            self.children = curr_base + (self.line if add_line else []) + sec_base

        def get_children(self):
            return self.children

    class TreeModel(ui.AbstractItemModel):
        def __init__(self, scenes):
            super().__init__()
            self._root = Manager.RootItem(scenes)

        def get_item_children(self, item):
            if item is None:
                return self._root.get_children()

            return item.get_children()

        def get_item_value_model_count(self, item):
            return 2

        def get_item_value_model(self, item, column_id):
            if column_id == 0:
                return item.name_model
            elif column_id == 1 and isinstance(item, Manager.SceneItem):
                return item.scene_description

        def update_filter(self, text):
            filters = []

            if text and text[0] == ":":
                self._root.update_filter(text[1:], True)
            else:
                for f in text.split(" "):
                    if len(f)==0:
                        continue
                    include = True
                    if f[0] == "-":
                        include = False
                        f = f[1:]
                    f = f"*{f}*"
                    filters.append((include, f))

                self._root.update_filter(filters)

            self._item_changed(None)
            for c in self._root.children:
                self._item_changed(c)

        def get_root(self):
            return self._root

    class TreeDelegate(ui.AbstractItemDelegate):
        def build_widget(self, model, item, column_id, level, expanded):
            if item is None:
                return

            if isinstance(item, Manager.LineItem):
                with ui.HStack(height=0):
                    if column_id == 0:
                        ui.Spacer(width=3)
                    ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=4)
                return

            text_model = model.get_item_value_model(item, column_id)
            if text_model is not None:
                with ui.HStack(height=0):
                    ui.Label(text_model.as_string, style_type_name_override="TreeView.Item", width=0)

        def build_branch(self, model, item, column_id, level, expanded):
            if isinstance(item, Manager.LineItem):
                return

            if column_id == 0:
                with ui.HStack(height=0):
                    ui.Spacer(width=4*level)
                    ui.Label(item.get_branch_text(expanded), style_type_name_override="TreeView.Item", width=15)

    def _on_double_click(self, x, y, b, m):
        if len(self._tree_view.selection) <= 0:
            return

        item = self._tree_view.selection[0]
        if isinstance(item, Manager.CategoryItem):
            self._tree_view.set_expanded(item, not self._tree_view.is_expanded(item), False)
        elif isinstance(item, Manager.SceneItem):
            self._open_new_stage_with_scene()

    def _build_tree_view(self):
        with ui.ScrollingFrame(
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            style_type_name_override="TreeView"
        ):
            self._list_model = self.TreeModel(self._category_data)
            self._delegate = self.TreeDelegate()
            self._tree_view = ui.TreeView(self._list_model, root_visible=False, delegate=self._delegate,
                                          style={"TreeView.Item": {"margin": 4}}, column_widths=[200])
            self._tree_view.set_selection_changed_fn(self._scene_selected)
            self._tree_view.set_mouse_double_clicked_fn(self._on_double_click)

    def _build_main_ui(self):
        self._build_main_frame()

    def _set_expand_tree(self, expand):
        async def expand_async():
            for _ in range(2):
                await omni.kit.app.get_app().next_update_async()
            for c in self._tree_view.model.get_root().get_children():
                self._tree_view.set_expanded(c, expand, True)
        asyncio.ensure_future(expand_async())

    def _update_filter(self, model):
        self._tree_view.model.update_filter(model.as_string)
        self._set_expand_tree(True)

    def _clear_filter(self):
        self.sf_filter.model.set_value("")
        self._tree_view.model.update_filter("")
        self._set_expand_tree(False)
        self._scene_selected([])

    def _build_main_frame(self):
        self._load_scenes()

        def right_frame_resize():
            self._tags_stack.rebuild()

        def build_tag_frame(frame):
            list_of_rows = []
            frame_size = frame.computed_width
            row_size = 0
            row_list = []
            for t in self._tags_sorted:
                text_size = len(t) * 7    # 7px avg per char
                row_size += 10 + text_size # 10px per padding and margin
                if row_size < frame_size:
                    row_list.append(t)
                else:
                    list_of_rows.append(row_list)
                    row_list = []
                    row_list.append(t)
                    row_size = text_size

            list_of_rows.append(row_list)

            with ui.VGrid(padding=5, row_height=30):
                for row in list_of_rows:
                    with ui.HStack(spacing=5):
                        for tag in row:
                            t = ui.Button(tag, width=0, clicked_fn=partial(click_tag, tag))

        def build_bottom():
            with ui.HStack():
                with ui.VStack(width=ui.Fraction(2)):
                    self._build_tree_view()
                ui.Spacer(width=10)
                right_frame = ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    computed_content_size_changed_fn=right_frame_resize
                )

                with right_frame:
                    with ui.ZStack():
                        self._tags_stack = ui.Frame(width=ui.Fraction(1), build_fn=partial(build_tag_frame, right_frame))
                        self._info_stack = ui.VStack(width=ui.Fraction(1), visible=False)
                        with self._info_stack:
                            self._title_label = ui.Label("", alignment=omni.ui.Alignment.LEFT_TOP, height=20)
                            self._description_label = ui.Label("", alignment=omni.ui.Alignment.LEFT_TOP, height=100)
                            self._description_label.word_wrap = True
                            self._config_frame = ui.Frame()
                            with ui.HStack():
                                self._load_button = ui.Button("Load scene", height=20, width=90)
                                self._load_button.set_clicked_fn(self._load_scene)
                                ui.Spacer(width=10)
                                self._open_button = ui.Button("Open source", height=20, width=90)
                                self._open_button.set_clicked_fn(self._open_source)
                                ui.Spacer(width=10)
                                self._reset_button = ui.Button("Reset params", height=20, width=90)
                                self._reset_button.set_clicked_fn(self._refresh_config)

        def click_tag(tag):
            self.sf_filter.model.set_value(f":{tag}")

        with self.frame:
            with ui.VStack():
                with ui.HStack(height=25):
                    ui.Label("Filter: ", width=0)
                    self.sf_filter = ui.StringField(width=200)
                    self.sf_filter.model.add_value_changed_fn(self._update_filter)
                    ui.Button("Clear", width=100, clicked_fn=self._clear_filter)
                ui.Spacer(height=2)
                build_bottom()

    def _build_source_ui(self):
        self._window_src = ui.Window("Source", width=960, height=600)

        def open_location(*_):
            if sys.platform == 'win32':
                os.startfile(self._src_dir_path)
            else:
                os.system(f'xdg-open "{self._src_dir_path}"')

        def open_editor(*_):
            if sys.platform == 'win32':
                os.startfile(self._src_path)
            else:
                editor = os.getenv('EDITOR')
                if editor is not None and editor != "":
                    os.system(f"{editor} {self._src_path}")
                else:
                    os.system(f'xdg-open "{self._src_path}"')

        with self._window_src.frame:
            with ui.VStack():
                self._src_path_label = ui.StringField(height=20)
                self._src_path_label.enabled = False
                self._src_code_editor = TextEditor()
                self._src_code_editor.read_only = True
                with ui.HStack(height=20):
                    ui.Button("Open file location", width=0, clicked_fn=open_location)
                    ui.Button("Open file in default editor", width=0, clicked_fn=open_editor)

    def _open_source_ui(self):
        if self._window_src is None:
            self._build_source_ui()

        path = os.path.abspath(sys.modules[self._selected_demo_class.__module__].__file__)
        file = open(path, "r")
        source = file.read()

        self._src_path_label.model.set_value(path)
        self._src_code_editor.text = source
        self._src_path = path
        self._src_dir_path = os.path.dirname(path)

        self._window_src.visible = True
        self._window_src.focus()

    def _release_ui(self):
        self._tree_view = None
        self._description_label = None
        self._title_label = None
        self._list_model = None
        self._load_button = None
        self._open_button = None
        self._reset_button = None
        self._config_frame = None
        self._config_params = None

        self._tags_stack = None
        self._info_stack = None

        self._window_src = None
        self._src_path_label = None
        self._src_code_label = None

    def _scene_selected(self, items):
        self._description_label.text = ""
        self._title_label.text = ""
        self._info_stack.visible = False
        self._selected_demo_class = None
        self._config_frame.clear()

        for item in items:
            if isinstance(item, Manager.SceneItem):
                self._title_label.text = item.scene_class.title
                self._description_label.text = item.scene_class.description
                self._selected_demo_class = item.scene_class
                self._refresh_config()
                self._tags_stack.visible = False
                self._info_stack.visible = True
                return

        self._tags_stack.visible = True
        self._info_stack.visible = False

    def _refresh_config(self):
        self._reset_button.visible = False
        sig = inspect.signature(self._selected_demo_class.create)
        self._config_params = OrderedDict()

        def process_param_line(param_dict):
            with ui.HStack():
                for name, param in param_dict.items():
                    if not issubclass(param.__class__, _Param):
                        carb.log_warn("Skipping '{}' configurable demo param, not inherited from Demo.Param() but {}".format(name, param.__class__))
                        continue

                    if name not in sig.parameters.keys():
                        carb.log_warn("Skipping '{}' configurable demo param, not present in the create method".format(name))
                        continue

                    self._add_config_control(name, param)

        with self._config_frame:
            with ui.VStack():
                if isinstance(self._selected_demo_class.params, list):
                    for param_dict in self._selected_demo_class.params:
                        process_param_line(param_dict)
                else:
                    process_param_line(self._selected_demo_class.params)

        if len(self._config_params) > 0:
            self._reset_button.visible = True

    def _add_config_control(self, name, param):
        with ui.VStack():
            label_name = param.name if param.name is not None else " ".join(name.split("_")).title()
            ui.Label(label_name, alignment=ui.Alignment.CENTER, height=20)
            self._config_params[name] = param.build_control()

    def _load_scene(self):
        self._update_enabled = False
        self._open_new_stage_with_scene()

    def _open_source(self):
        self._open_source_ui()

    @staticmethod
    def _duplicate_stage_to_memory(stage, path):
        in_memory_root_layer = Sdf.Layer.OpenAsAnonymous(path)
        layer_queue = [(stage.GetRootLayer(), in_memory_root_layer)]
        omni.usd.resolve_paths(stage.GetRootLayer().identifier, in_memory_root_layer.identifier, False)

        all_new_layers = {}
        while len(layer_queue) > 0:
            original_layer, new_layer = layer_queue.pop(0)

            new_layer.subLayerPaths.clear()
            for sublayer_path in original_layer.subLayerPaths:
                absolute_path = original_layer.ComputeAbsolutePath(sublayer_path)
                new_sublayer = all_new_layers.get(absolute_path, None)
                if not new_sublayer:
                    original_sublayer = Sdf.Layer.FindOrOpen(absolute_path)
                    if not original_sublayer:
                        continue

                    new_sublayer = Sdf.Layer.OpenAsAnonymous(absolute_path)
                    omni.usd.resolve_paths(original_sublayer.identifier, new_sublayer.identifier, False)
                    all_new_layers[absolute_path] = new_sublayer
                    layer_queue.append((original_sublayer, new_sublayer))

                new_layer.subLayerPaths.append(new_sublayer.identifier)

            return Usd.Stage.Open(in_memory_root_layer)

    @staticmethod
    def open_new_stage(demo_instance, stage_opened_fn):
        if demo_instance.demo_base_usd_url:
            original_stage = Usd.Stage.Open(demo_instance.demo_base_usd_url)
            in_memory_stage = Manager._duplicate_stage_to_memory(original_stage, demo_instance.demo_base_usd_url)
            original_stage = None
            cache = UsdUtils.StageCache.Get()
            stage_id = cache.Insert(in_memory_stage).ToLongInt()
            omni.usd.get_context().attach_stage_with_callback(stage_id=stage_id, on_finish_fn=stage_opened_fn)

            # refresh settings, attaching to a stage does not trigger that
            omni.usd.get_context().load_render_settings_from_stage(stage_id)
            load_physics_settings_from_stage(in_memory_stage)
        else:
            omni.kit.stage_templates.new_stage_with_callback(on_new_stage_fn=stage_opened_fn, template="empty")


    def _open_new_stage_with_scene(self, check_unsaved=True, apply_kit_settings=True):
        def new_stage():
            # close stage so that a possible previous demo is shutdown and deleted
            # and we can create a new demo class instance on which we can call its pre_stage_create
            omni.usd.get_context().close_stage()
            demo_instance = self._selected_demo_class()
            demo_instance.on_startup()
            Manager.open_new_stage(demo_instance, partial(self._on_stage_opened, demo_instance))

        self._kit_settings_backup.clear()
        self._apply_kit_settings = apply_kit_settings

        if check_unsaved:
            omni.kit.window.file.prompt_if_unsaved_stage(new_stage)
        else:
            new_stage()

    def _set_base_stage(self, stage):
        stage.SetTimeCodesPerSecond(60)

    def _on_stage_opened(self, demo_instance, res, err):
        stage = self._usd_context.get_stage()
        current_params = {key: model.get_value() for key, model in self._config_params.items()}
        self._set_base_stage(stage)
        demo_instance.create(stage, **current_params)

        self._demo_instance = demo_instance
        self._first_update = True
        self._add_sub_to_update()

    def _on_update(self, e):
        if self._demo_instance is None:
            return

        stage = self._usd_context.get_stage()
        if stage is None:
            return

        if self._first_update:
            self._first_update = False
            # backup and set kit settings
            if self._apply_kit_settings and self._demo_instance.kit_settings:
                settingsInterface = carb.settings.acquire_settings_interface()
                for key, value in self._demo_instance.kit_settings.items():
                    self._kit_settings_backup[key] = settingsInterface.get(key)
                    settingsInterface.set(key, value)
            # set active demo camera:
            if self._demo_instance.demo_camera:
                cam_path = Sdf.Path(self._demo_instance.demo_camera)  # support both Sdf.Paths and strings
                vp_utils.get_active_viewport().set_active_camera(cam_path.pathString)
            if self._demo_instance.autofocus:
                resolution = vp_utils.get_active_viewport().resolution
                omni.kit.commands.execute(
                    'FramePrimsCommand',
                    prim_to_move="/OmniverseKit_Persp",
                    prims_to_frame=None,
                    time_code=Usd.TimeCode.Default(),
                    aspect_ratio=resolution[0]/resolution[1],
                    zoom=self._demo_instance.autofocus_zoom
                )

        dt = e.payload["dt"]
        self._demo_instance.update(stage, dt, None, get_physx_interface())

    def _on_stage_event(self, event):
        if self._demo_instance is None:
            return

        if event.type is int(omni.usd.StageEventType.CLOSING):
            # Check stage closing while demo is running. Code reorg made opening a stage during create() call safe,
            # so this essentialy guards against fooling with stages during update. We might want to add a util
            # for switching stage during update and not running on_shutdown by mistake.
            import inspect
            stack = inspect.stack()
            for i in stack:
                if isinstance(i.frame.f_locals.get("self"), Base):
                    carb.log_error("Demo is unexpectedly closing stage!")

            self._demo_instance.on_shutdown()
            self._demo_instance = None
            self._update_sub = None

            # restore kit settings from backup:
            if self._kit_settings_backup:
                settingsInterface = carb.settings.acquire_settings_interface()
                for key, value in self._kit_settings_backup.items():
                    settingsInterface.set(key, value)
                self._kit_settings_backup.clear()


class Categories:
    SNIPPETS = TUTORIALS = "Uncategorized"
    SAMPLES = DEMOS = "Uncategorized"
    PSCL = "PSCL"
    INTERNAL = INTERNAL_SAMPLES = INTERNAL_DEMOS = "Internal"
    PREVIEW = "Previews"
    ###
    NONE = "None"
    BASICS = "Basics"
    RIGID_BODIES = "Rigid Bodies"
    MATERIALS = "Materials"
    SIMULATION_PART = "Simulation Partitioning"
    CONTACTS = "Contacts"
    TRIGGERS = "Triggers"
    SCENE_QUERY = "Scene Query"
    JOINTS = "Joints"
    ARTICULATIONS = "Articulations"
    CCT = "Character Controller"
    VEHICLES = "Vehicles"
    DEFORMABLES = "Deformables"
    PARTICLES = "Particles"
    COMPLEX_SHOWCASES = "Complex Showcases"
    FORCE_FIELDS = "Force Fields"

CATEGORY_ORDER = [
    Categories.BASICS,
    Categories.RIGID_BODIES,
    Categories.MATERIALS,
    Categories.SIMULATION_PART,
    Categories.CONTACTS,
    Categories.TRIGGERS,
    Categories.SCENE_QUERY,
    Categories.JOINTS,
    Categories.ARTICULATIONS,
    Categories.CCT,
    Categories.VEHICLES,
    Categories.DEFORMABLES,
    Categories.PARTICLES,
    Categories.FORCE_FIELDS,
    Categories.COMPLEX_SHOWCASES,
]


class Base:
    title = ""
    category = Categories.NONE
    short_description = ""
    description = ""
    params = {}
    tags = []

    """
    Configurable params are defined in a dictionary as e.g.
    params = {"length": IntParam(4, 0, 20, 1)}
    and then need to be added to the create method
    def create(self, stage, length)
    """

    kit_settings = {}

    """
    Dictionary of demo-specific kit settings that are applied through the carb.settings interface
    in the first stage update after the demo's create method is called.

    The kit settings are automatically reset after the demo's on_shutdown is called.

    Example:
    import omni.physx.bindings._physx as physx_settings_bindings
    class SomeDemo(demo.Base):
        title = "Some Demo"
        ...

        kit_settings = {
            "persistent/app/viewport/displayOptions": demo.get_viewport_minimal_display_options_int(),
            physx_settings_bindings.SETTING_UPDATE_VELOCITIES_TO_USD: False,
            "rtx/post/dlss/execMode": 0,  # set DLSS to performance
        }
    """

    demo_camera = ""


    """
    Invoke kit's autofocus at the first update to center the scene on whatever was created and with a custom zoom
    """
    autofocus = False
    autofocus_zoom = 0.45

    """
    Sdf.Path or path string to UsdGeom.Camera to set the viewport active camera to.

    The camera is set in the first stage update after the demo's create method is called.
    (Kit cannot handle the camera change in the create method.)
    """

    demo_base_usd_url = ""

    """
    Path / url to base USD layer to load instead of empty new stage. The base layer may provide scene-specific render/physics parameters in its metadata.
    """

    """
    Main create function called after a new stage is created.
    """
    def create(self, stage):
        pass

    """
    Update called with each Kit update.
    """
    def update(self, stage, dt, viewport, physxIFace):
        pass

    """
    Called before a new stage is created for the demo, and before create.
    """
    def on_startup(self):
        pass

    """
    Called on shutdown.
    """
    def on_shutdown(self):
        pass


class _Param():
    def __init__(self, val, name=None):
        self.val = val
        self.name = name


class _RangeParam(_Param):
    def __init__(self, val, min, max, step, name=None):
        _Param.__init__(self, val, name)
        self.min = min
        self.max = max
        self.step = step


class _ImplicitBoolModel(ui.SimpleBoolModel):
    def __init__(self, val):
        ui.SimpleBoolModel.__init__(self, val)

    def get_value(self):
        return self.get_value_as_bool()


class _ImplicitIntModel(ui.SimpleIntModel):
    def __init__(self, val):
        ui.SimpleIntModel.__init__(self, val)

    def get_value(self):
        return self.get_value_as_int()


class _ImplicitFloatModel(ui.SimpleFloatModel):
    def __init__(self, val):
        ui.SimpleFloatModel.__init__(self, val)

    def get_value(self):
        return self.get_value_as_float()


class _ImplicitStringModel(ui.SimpleStringModel):
    def __init__(self, val):
        ui.SimpleStringModel.__init__(self, val)

    def get_value(self):
        return self.get_value_as_string()


class FloatParam(_RangeParam):
    def __init__(self, val, min, max, step, name=None):
        _RangeParam.__init__(self, val, min, max, step, name)

    def build_control(self):
        model = _ImplicitFloatModel(self.val)
        model.set_min(self.min)
        model.set_max(self.max)
        ui.FloatDrag(model, min=self.min, max=self.max, step=self.step)
        return model


class IntParam(_RangeParam):
    def __init__(self, val, min, max, step, name=None):
        _RangeParam.__init__(self, val, min, max, step, name)

    def build_control(self):
        model = _ImplicitIntModel(self.val)
        model.set_min(self.min)
        model.set_max(self.max)
        ui.IntDrag(model, min=self.min, max=self.max, step=self.step)
        return model


class CheckboxParam(_Param):
    def build_control(self):
        model = _ImplicitBoolModel(self.val)
        with ui.HStack():
            ui.Spacer(width=ui.Fraction(1))
            ui.CheckBox(model, width=ui.Fraction(0.1))
            ui.Spacer(width=ui.Fraction(1))
        return model

class FileParam(_Param):
    def build_control(self):
        with ui.HStack(height=20):
            model = _ImplicitStringModel(self.val)
            ui.StringField(model)

            def on_open(dialog: FilePickerDialog, filename: str, dirname: str):
                dialog.hide()
                fullpath = f"{dirname}/{filename}" if dirname else filename
                model.set_value(fullpath)
                cleanup_fp_dialog(dialog)

            def on_choose():
                item_filter_options = ["USD Files (*.usd, *.usda, *.usdc, *.usdz)", "All Files (*)"]
                dialog = FilePickerDialog(
                    "Open File",
                    apply_button_label="Open",
                    click_apply_handler=lambda filename, dirname: on_open(dialog, filename, dirname),
                    item_filter_options=item_filter_options,
                )

            ui.Button("Choose", width=100, clicked_fn=on_choose)
            return model

class BoolParam(CheckboxParam):
    ...


class AsyncDemoBase(Base):
    """
    Base class for demos that use async sim and might need to run physics step callbacks that interface with the sim
    through the omni.physics.tensor API.

    The base class automatically subscribes to physics step, physics event, and timeline callbacks.

    The demo may override the public methods below, and may configure enabling the omni.physx.tensors and
    omni.physx.fabric extensions by passing flags to the constructor.

    Important notes:
    - Make sure not to forget to call this base class constructor in your derived demo using super().__init__(...)
    - In the demo on_shutdown method:
        1. specifically release any views that you may create in on_tensor_start with self._some_view = None
        2. call this base class shutdown to cleanup properly with super().on_shutdown() at the end of your method
    - Be careful not to write to USD from the async called on_physics_step. Use the class attribute queue to communicate
    between threads.
    """

    def on_physics_step(self, dt):
        """
        This method is called on each physics step callback, and the first callback is issued
        after the on_tensor_start method is called if the tensor API is enabled.
        """
        pass

    def on_tensor_start(self, tensorApi: types.ModuleType):
        """
        This method is called when
            1. the tensor API is enabled, and
            2. when the simulation data is ready for the user to setup views using the tensor API.
        """
        pass

    def on_timeline_event(self, e):
        """
        This method is called on timeline events. Note that in async sim, the STOP event is issued before the end
        of the simulation is awaited. Use on_simualtion_event and checking for

          e.type == int(omni.physx.bindings._physx.SimulationEvent.STOPPED)

        instead if you need to do operations that are illegal during simulation (e.g. actor removal).
        """
        pass

    def on_simulation_event(self, e):
        """
        This method is called on simulation events. See omni.physx.bindings._physx.SimulationEvent.
        """
        pass

    def on_shutdown(self):
        """
        Make sure to call this from your optional on_shutdown override with super().on_shutdown() for proper cleanup.
        """
        # unsubscribe
        self._timeline_sub = None
        self._physics_update_sub = None
        self._simulation_event_subscription = None

        # disable/enable tensor and fabric ext if needed
        manager = omni.kit.app.get_app().get_extension_manager()
        manager.set_extension_enabled_immediate("omni.physx.tensors", self._tensorapi_was_enabled)
        self._tensor_api = None
        manager.set_extension_enabled_immediate("omni.physx.fabric", self._fabric_was_enabled)

    def __init__(self, enable_tensor_api=False, enable_fabric=False, fabric_compatible=True):
        """
        Use the constructor arguments to configure what additional extensions are loaded
        and made available to the demo. If fabric_compatible=False then enable_fabric=True is ignored.
        If fabric_compatible=True and enable_fabric=False, the fabric extension is not unloaded.

        Call from your derived class constructor, for example like this:
            def __init__(self):
                super().__init__(enable_tensor_api=True, enable_fabric=False)
        """
        super().__init__()
        self._is_stopped = True
        self._tensor_started = False
        self._tensor_api = None
        self._fabric_was_enabled = False
        self._tensorapi_was_enabled = False
        self.queue = queue.Queue()

        # setup subscriptions:
        self._setup_callbacks()

        if enable_tensor_api:
            self._enable_tensor_api()

        if not fabric_compatible:
            enable_fabric = False

        self._enable_fabric(enable_fabric, fabric_compatible)

    @staticmethod
    def flush_fifo_queue(fifo_queue: queue.Queue):
        """
        Flush the demo Python FIFO queue.Queue (self.demo_queue) and return last element and number of elements that
        were in the queue. (A queue is suitable for passing data between the async called physics step callback and
        callbacks that are on the main thread)

        Returns:
            last_element, num_elements
        """
        last_element = None
        num_elements = 0
        try:
            while True:
                last_element = fifo_queue.get(block=False)
                num_elements += 1
        except queue.Empty:
            pass  # do nothing, exception is just signaling queue empty after getting all elements

        return last_element, num_elements

    @property
    def tensor_api(self):
        return self._tensor_api

    # "PRIVATE" METHODS #
    def _can_callback_physics_step(self) -> bool:
        if self._is_stopped:
            return False

        if self._tensor_started or self._tensor_api is None:
            return True

        self._tensor_started = True
        self.on_tensor_start(self._tensor_api)
        return True

    def _on_timeline_event(self, e):
        if e.type == int(omni.timeline.TimelineEventType.STOP):
            self._is_stopped = True
            self._tensor_started = False
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            self._is_stopped = False

        # call user implementation
        self.on_timeline_event(e)

    def _on_physics_step(self, dt):
        if not self._can_callback_physics_step():
            return

        # call user implementation
        self.on_physics_step(dt)

    def _setup_callbacks(self):
        stream = omni.timeline.get_timeline_interface().get_timeline_event_stream()
        self._timeline_sub = stream.create_subscription_to_pop(self._on_timeline_event)
        # subscribe to Physics updates:
        self._physics_update_sub = omni.physx.get_physx_interface().subscribe_physics_step_events(self._on_physics_step)
        events = omni.physx.get_physx_interface().get_simulation_event_stream_v2()
        self._simulation_event_subscription = events.create_subscription_to_pop(self.on_simulation_event)

    def _enable_tensor_api(self):
        manager = omni.kit.app.get_app().get_extension_manager()
        self._tensorapi_was_enabled = manager.is_extension_enabled("omni.physx.tensors")
        if not self._tensorapi_was_enabled:
            manager.set_extension_enabled_immediate("omni.physx.tensors", True)
        self._tensor_api = importlib.import_module("omni.physics.tensors")

    def _enable_fabric(self, enable_fabric, fabric_compatible):
        manager = omni.kit.app.get_app().get_extension_manager()
        self._fabric_was_enabled = manager.is_extension_enabled("omni.physx.fabric")
        if enable_fabric and not self._fabric_was_enabled:
            manager.set_extension_enabled_immediate("omni.physx.fabric", True)
        if not fabric_compatible and self._fabric_was_enabled:
            manager.set_extension_enabled_immediate("omni.physx.fabric", False)

def get_demo_asset_path(resource_relative_path: str) -> str:
    """
    Helper to construct an asset path to the demo asset location based on setting '/physics/demoAssetsPath'

    Args:
        path: String path relative to root folder of the demo assets.

    Example:
        Get path to sphere_high.usd:
        asset_path = get_demo_asset_path("common/sphere_high.usd")
    """
    assets_path_setting = carb.settings.get_settings().get(pb.SETTING_DEMO_ASSETS_PATH)
    assert assets_path_setting, "Empty string in setting /physics/demoAssetsPath!"
    return assets_path_setting + resource_relative_path

def get_viewport_minimal_display_options_int() -> int:
    """
    Helper that returns viewport options for max. FPS performance.
    Disables all viewport viz options except showing meshes, fps, and gpu mem
    """
           # meshes  | gpu mem   | fps
    return (1 << 10) | (1 << 13) | 1

def get_demo_room(demoInstance, stage, **kwargs):
    return RoomHelper(demoInstance, stage, **kwargs)

def get_room_instancer(stage):
    return RoomInstancer(stage)

def get_room_helper_class():
    return RoomHelper

def get_hit_color():
    return Gf.Vec3f(0.0, 1.0, 0.0)

def get_static_color(index = 0.0):
    colors = [
        Gf.Vec3f(165.0, 21.0, 21.0)/255.0,
        Gf.Vec3f(165.0, 80.0, 21.0)/255.0
    ]

    return colors[0]*(1.0-index) + colors[1]*index

def get_primary_color(index = 0.0):
    colors = [
        Gf.Vec3f(30.0, 60.0, 255.0)/255.0,
        Gf.Vec3f(200.0, 25.0, 255.0)/255.0
    ]

    return colors[0]*(1.0-index) + colors[1]*index

def setup_physics_scene(demoInstance, stage, primPathAsString = True, metersPerUnit = 0.01, gravityMod = 1.0, upAxis = UsdGeom.Tokens.z):
    try:
        currentDemoParams = demoInstance.demoParams
    except AttributeError:
        currentDemoParams = None

    defaultPrimPath = stage.GetDefaultPrim().GetPath()
    if currentDemoParams:
        defaultPrimPath = defaultPrimPath.AppendPath(currentDemoParams["rootPath"])

    UsdGeom.SetStageUpAxis(stage, upAxis)
    UsdGeom.SetStageMetersPerUnit(stage, metersPerUnit)

    gravityDir = Gf.Vec3f(0.0, 0.0, -1.0)
    if upAxis == UsdGeom.Tokens.y:
        gravityDir = Gf.Vec3f(0.0, -1.0, 0.0)
    if upAxis == UsdGeom.Tokens.x:
        gravityDir = Gf.Vec3f(-1.0, 0.0, 0.0)

    scene = UsdPhysics.Scene.Define(stage, defaultPrimPath.AppendPath("physicsScene"))
    scene.CreateGravityDirectionAttr().Set(gravityDir)
    scene.CreateGravityMagnitudeAttr().Set(9.81 * gravityMod / metersPerUnit)

    if primPathAsString:
        defaultPrimPath = str(defaultPrimPath)

    return (defaultPrimPath, scene)

def animate_attributes(demoInstance, stage, timeStep=0):
    if not getattr(demoInstance, "_animationData", None):
        return

    # if we want to animate the scene independent of the timeline, set manualAnimation "True"

    manualAnimation = demoInstance._animationData["manualAnimation"]

    if "maxStep" in demoInstance._animationData:
        maxStep = demoInstance._animationData["maxStep"]
    else:
        maxStep = 0

    if "timeCodesPerSecond" in demoInstance._animationData:
        timeCodesPerSecond = demoInstance._animationData["timeCodesPerSecond"]
    else:
        timeCodesPerSecond = 0

    keyframes = demoInstance._animationData["keyframes"]

    if timeCodesPerSecond > 0:
        timeStepScaled = (timeStep*timeCodesPerSecond/60.0)
    else:
        timeStepScaled = timeStep

    if maxStep > 0:
        curStep = timeStepScaled % (maxStep + 1)
    else:
        curStep = timeStepScaled

    if manualAnimation:
        for item in keyframes:
            op = item["op"]
            totalItems = len(item["times"])
            for i in range(totalItems):
                itemTime = item["times"][i]
                itemValue = item["values"][i]

                if i == (totalItems - 1):
                    nextIndex = i
                else:
                    nextIndex = i + 1

                nextItemTime = item["times"][nextIndex]
                nextItemValue = item["values"][nextIndex]

                if (curStep >= itemTime) and (curStep < nextItemTime):
                    lerpVal = (curStep - itemTime) / (nextItemTime - itemTime)
                    if type(itemValue) == type(True): # Booleans cannot be interpolated
                        newVal = itemValue if (lerpVal < 1.0) else nextItemValue
                    else:
                        newVal = (1.0-lerpVal)*itemValue + lerpVal*nextItemValue

                    op.Set(newVal)
    else:
        if timeCodesPerSecond > 0:
            stage.SetTimeCodesPerSecond(timeCodesPerSecond)
        for item in keyframes:
            op = item["op"]
            for i in range(len(item["times"])):
                itemTime = item["times"][i]
                itemValue = item["values"][i]
                op.Set(time=itemTime, value=itemValue)