import omni.ui as ui
import asyncio
import omni.kit.app
import carb
import omni.physxsupportui.bindings._physxSupportUi as pxsupportui
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModelState
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModel
from omni.physxsupportui import get_physx_supportui_private_interface
from .inspector_panel import InspectorPanel
from .inspector_selection import InspectorSelectionHandler
from .inspector_context_menu import InspectorContextMenuHandler

LABEL_WIDTH = 200
LINE_HEIGHT = 23

class PhysXInspectorWindow(ui.Window):
    def __init__(self, inspector, model : PhysXInspectorModel, works_on_selection : bool, title_stable_id : str, title_prefix : str):
        self._title_stable_id = title_stable_id
        self._title_prefix = title_prefix
        self._development_mode = carb.settings.get_settings().get("physics/developmentMode")
        self._supportui_private = get_physx_supportui_private_interface()

        self._inspector = inspector
        self._inspection_index = 1
        self._inspection_modes = ["Joints, bodies, materials", "Joints Only"]
        self._inspection_values = [ pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_BODIES_HIERARCHY, 
                                    pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_LIST]

        # Models
        self._model_inspector = model
        self._model_use_omni_ui = ui.SimpleBoolModel(True)
        self._model_lock = self._model_inspector.get_is_locked_model()
        self._model_lock.set_value(not works_on_selection)
        self._model_show_masses_and_inertia = self._model_inspector.get_show_masses_and_inertia_model()

        # Subscriptions
        self._sub_model_event = self._supportui_private.get_inspector_event_stream().create_subscription_to_pop(self._on_inspector_event, name="Inspector Window State")
        self._sub_path_changed = self._model_inspector.get_inspected_prim_string_model().add_value_changed_fn(self._on_path_changed)
        self._sub_lock_model = self._model_lock.add_value_changed_fn(self._on_lock_model_changed)
        self._sub_omni_ui_changed = self._model_use_omni_ui.add_value_changed_fn(self._on_use_omni_ui_changed)

        # UI Handlers
        self._handler_selection = InspectorSelectionHandler(self._model_inspector, self._inspector)
        self._handler_context_menu = InspectorContextMenuHandler()

        # UI Elements
        self._inspector_panel = None

        super().__init__(
            self._generate_title(),
            visible=True,
            position_x=420,
            position_y=200,
            width=300,
            height=300,
            auto_resize=False,
            margin=0,
        )
        self.set_visibility_changed_fn(self._on_window_closed)

        async def dock_inspector():
            await omni.kit.app.get_app().next_update_async()
            num_windows =  len(self._inspector._inspector_windows)
            if num_windows == 1:
                stage_window = ui.Workspace.get_window("Stage")
                if stage_window:
                    self.dock_in(stage_window, ui.DockPosition.BOTTOM)
            elif num_windows > 0:
                self.dock_in(self._inspector._inspector_windows[0] , ui.DockPosition.SAME)
        
        asyncio.ensure_future(dock_inspector())
        self._update_inspector_window()
    
    def _generate_title(self):
        selection = self._model_inspector.get_inspected_prim_string_model().get_value_as_string()
        title = f"{self._title_prefix}{selection}###{self._title_stable_id}"
        return title

    def _on_lock_model_changed(self, model):
        self._ui_lock_label.visible = self._model_lock.as_bool

    def _on_use_omni_ui_changed(self, model):
        self._inspector_panel.set_use_omni_ui(self._model_use_omni_ui.as_bool)

    def _on_window_closed(self, visible):
        if self._model_inspector is None:
            return
        if len(self._inspector._inspector_windows) <= 1:
            carb.settings.get_settings().set_bool(pxsupportui.SETTINGS_PHYSICS_INSPECTOR_ENABLED, False)
        else:
            self._inspector._inspector_windows.remove(self)
            self.clean()


    def _show_selected_container(self, type):
        if type == PhysXInspectorModelState.DISABLED:
            self._collapsible_frame.visible = False
            self._ui_container_running.visible = False
            self._ui_container_disabled.visible = True
            self._ui_container_authoring.visible = False
        elif type == PhysXInspectorModelState.AUTHORING:
            self._collapsible_frame.visible = True
            self._ui_container_running.visible = False
            self._ui_container_disabled.visible = False
            self._ui_container_authoring.visible = True
        elif type == PhysXInspectorModelState.RUNNING_SIMULATION:
            self._collapsible_frame.visible = False
            self._ui_container_running.visible = True
            self._ui_container_disabled.visible = False
            self._ui_container_authoring.visible = False

    def _on_inspector_event(self, e):
        self._show_selected_container(PhysXInspectorModelState(e.type))

    def _on_path_changed(self, model : ui.SimpleStringModel):
        self._ui_path_label.text = model.get_value_as_string()
        self.title = self._generate_title()

    def clean(self):
        # Subscriptions
        self._supportui_private = None
        self._model_inspector.get_inspected_prim_string_model().remove_value_changed_fn(self._sub_path_changed)
        self._model_lock.remove_value_changed_fn(self._sub_lock_model)
        self._model_use_omni_ui.remove_value_changed_fn(self._sub_omni_ui_changed)
        self._sub_model_event = None
        self._sub_path_changed = None
        self._sub_lock_model = None
        self._sub_omni_ui_changed = None

        # Models
        self._model_inspector = None
        self._model_show_masses_and_inertia = None
        self._model_use_omni_ui = None
        self._model_lock = None

        # UI Handlers
        self._handler_context_menu.clean()
        self._handler_context_menu = None
        self._handler_selection.clean()
        self._handler_selection = None

        # UI Elements
        self._ui_container_running = None
        self._ui_container_disabled = None
        self._ui_container_authoring = None
        self._ui_lock_label = None
        self._ui_path_label = None
        self._ui_main_stack = None
        if self._inspector_panel:
            self._inspector_panel.clean()
        self._inspector_panel = None

    def _update_inspector_window(self):

        with self.frame:
            with ui.VStack():
                self._build_options()
                ui.Spacer(height=5)

                self._ui_main_stack = ui.ZStack()
                with self._ui_main_stack:
                    self._ui_container_running = ui.VStack(visible=False, height=0)
                    self._ui_container_disabled = ui.VStack(visible=False, height=0)
                    self._ui_container_authoring = ui.VStack(visible=False)
                    with self._ui_container_authoring:
                        with ui.HStack(height=0):
                            self._ui_lock_label = ui.Label("[LOCKED TO] ", width=0, style={"color": 0xff0000ff}, 
                                                            visible = self._model_inspector.get_is_locked_model().as_bool)
                            self._ui_path_label = ui.Label(self._model_inspector.get_inspected_prim_string_model().as_string, word_wrap=True)                        
                        ui.Spacer(height=5)
                        with ui.ScrollingFrame( horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                                                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                                style_type_name_override="TreeView"):
                            self._inspector_panel = InspectorPanel(self._model_inspector, self._handler_selection, self._handler_context_menu)
                            self._inspector_panel.set_inspector_type(self._inspection_values[self._inspection_index])
                            self._on_use_omni_ui_changed(self._model_use_omni_ui)
                    with self._ui_container_running:
                        ui.Label("Inspector is disabled while running simulation")
                    with self._ui_container_disabled:
                        ui.Label("Changes detected in the scene, needs re-parsing scene to re-enable authoring", word_wrap=True)
                        ui.Button("Re-Enable authoring", width=0, height=0, clicked_fn=self._on_re_enable_authoring)
                self._show_selected_container(self._supportui_private.get_inspector_state())

    def _on_re_enable_authoring(self):
        self._supportui_private.enable_inspector_authoring_mode()

    def _on_reset_to_authoring_start(self):
        self._inspector._inspector_simulation.stop_authoring_simulation()
        self._supportui_private.reset_inspector_to_authoring_start()

    def _inspection_cb_item_changed(self, model, _):
        self._inspection_index = model.get_item_value_model().as_int
        self._inspector_panel.set_inspector_type(self._inspection_values[self._inspection_index])
        self._collapsible_frame.title = f"Options ({self._inspection_modes[self._inspection_index]})"

    def _build_options(self):
        self._collapsible_frame = ui.CollapsableFrame(f"Options ({self._inspection_modes[self._inspection_index]})", height=0, collapsed=True)
        with self._collapsible_frame:
            with ui.HStack():
                ui.Spacer(width=12)
                with ui.VStack():
                    with ui.HStack(height=LINE_HEIGHT):
                        ui.Label("Inspection Mode", width=LABEL_WIDTH)
                        self._inspection_mode = ui.ComboBox(self._inspection_index, *self._inspection_modes, width=200).model.add_item_changed_fn(self._inspection_cb_item_changed)
                    with ui.HStack(height=LINE_HEIGHT):
                        ui.Label("Show masses and inertia overlay", width=LABEL_WIDTH).set_tooltip(
                            "When enabled will show masses and inertia billboards in the viewport window")
                        with ui.VStack():
                            ui.Spacer()
                            ui.CheckBox(self._model_show_masses_and_inertia, height=0)
                            ui.Spacer()
                    with ui.HStack(height=LINE_HEIGHT):
                        ui.Label("Lock current inspector selection", width=LABEL_WIDTH).set_tooltip(
                            "When checked, the inspector will stop listening to stage selection changes events\n" \
                            "(so it will show information about the last usd prim that was previously selected)")
                        with ui.VStack():
                            ui.Spacer()
                            ui.CheckBox(self._model_lock, height=0)
                            ui.Spacer()
                    if self._development_mode:
                        with ui.HStack(height=LINE_HEIGHT):
                            ui.Label("Use omni.ui", width=LABEL_WIDTH).set_tooltip("Uses omni.ui for inspector panel")
                            with ui.VStack():
                                ui.Spacer()
                                ui.CheckBox(self._model_use_omni_ui, height=0)
                                ui.Spacer()
                    with ui.HStack(height=LINE_HEIGHT):
                        ui.Label("Actions", width=LABEL_WIDTH).set_tooltip(
                            "Actions to apply to current inspected selection")
                        with ui.VStack():
                            ui.Button("Reset to authoring start",  clicked_fn=self._on_reset_to_authoring_start)
                            ui.Button("New Inspector from selection",  clicked_fn=lambda: self._inspector.add_inspector_window())