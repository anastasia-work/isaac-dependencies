import omni.ui as ui
import carb.settings
import omni.physxsupportui.bindings._physxSupportUi as pxsupportui
import asyncio
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorWidget 
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModelDataShapeType 
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModel
from .inspector_selection import InspectorSelectionHandler
from .inspector_context_menu import InspectorContextMenuHandler
from pxr import Sdf, Usd, UsdPhysics, Tf, PhysxSchema, UsdGeom
from typing import List
import omni.usd
import math, sys
import carb
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel
from .inspector_simulation import InspectorSimulation

class InspectorTreeDelegate(ui.AbstractItemDelegate):
    def __init__(self, 
                    model_inspector : PhysXInspectorModel,
                    inspector_simulation : InspectorSimulation): # Model used only for _is_joints_list
        super().__init__()
        self._model_inspector = model_inspector
        self._inspector_simulation = inspector_simulation
        self._usd_models : List[UsdAttributeModel] = []
        self._inside_change_selected = False
    
    def clean(self):
        self.clean_usd_models()
        self._model_inspector = None
        self._inspector_simulation = None
    
    def _add_usd_model(self, model : UsdAttributeModel):
        self._usd_models.append(model)
        self._inspector_simulation.add_usd_model(model)
        
    def clean_usd_models(self):
        for model in self._usd_models:
            model.clean()
            self._inspector_simulation.remove_usd_model(model)
        self._usd_models = []
    
    def is_supported_joint_type(self, prim: Usd.Prim) -> bool:
        if prim.IsA(UsdPhysics.RevoluteJoint):
            return True
        elif prim.IsA(UsdPhysics.PrismaticJoint):
            return True
        return False

    def get_default_slider_limit(self, prim: Usd.Prim) -> float:
        if prim.IsA(UsdPhysics.RevoluteJoint):
            return 460.0
        elif prim.IsA(UsdPhysics.PrismaticJoint):
            return 1000.0
        return False

    def get_unsupported_joint_description(self, prim: Usd.Prim) -> str:
        if prim.IsA(UsdPhysics.SphericalJoint):
            return "Spherical Joint"
        elif prim.IsA(UsdPhysics.FixedJoint):
            return "Fixed Joint"
        elif prim.IsA(UsdPhysics.DistanceJoint):
            return "Distance Joint"
        elif prim.IsA(PhysxSchema.PhysxPhysicsRackAndPinionJoint):
            return "Rack and Pinion Joint"
        elif prim.IsA(PhysxSchema.PhysxPhysicsGearJoint):
            return "Gear Joint"
        elif prim.IsA(UsdPhysics.Joint):
            return "D6 Joint"
        return "Unknown Joint Type"

    def get_value_attribute_path(self, prim : Usd.Prim) -> Sdf.Path:
        if prim.IsA(UsdPhysics.RevoluteJoint):
            if prim.HasAPI(UsdPhysics.DriveAPI):
                return prim.GetPath().AppendProperty("drive:angular:physics:targetPosition")
            else:
                return prim.GetPath().AppendProperty("state:angular:physics:position")
        elif prim.IsA(UsdPhysics.PrismaticJoint):
            if prim.HasAPI(UsdPhysics.DriveAPI):
                return prim.GetPath().AppendProperty("drive:linear:physics:targetPosition")
            else:
                return prim.GetPath().AppendProperty("state:linear:physics:position")

        raise Exception(f"Prim {prim.GetPath().GetText()} is not of a supported type or it doesn't have applied Drive or JointState API") 

    def get_velocity_attribute(self, prim : Usd.Prim) -> Sdf.Path:
        if prim.IsA(UsdPhysics.RevoluteJoint):
            if prim.HasAPI(PhysxSchema.JointStateAPI):
                return prim.GetPath().AppendProperty("state:angular:physics:velocity")
        elif prim.IsA(UsdPhysics.PrismaticJoint):
            if prim.HasAPI(PhysxSchema.JointStateAPI):
                return prim.GetPath().AppendProperty("state:linear:physics:velocity")
        return None

    def _build_min_max_item(self, prim, min_or_max: str, main_property : str, other_property: str, default_limit: float):
        stage : Usd.Stage = prim.GetStage()
        main_model = UsdAttributeModel(  stage=stage, attribute_paths=[prim.GetPath().AppendProperty(main_property)], 
                                            self_refresh=True, metadata={}, change_on_edit_end=False)
        other_model = UsdAttributeModel(  stage=stage, attribute_paths=[prim.GetPath().AppendProperty(other_property)], 
                                            self_refresh=True, metadata={}, change_on_edit_end=False)
        step = InspectorTreeDelegate._get_step_for_prim(prim)

        with ui.ZStack(style={":disabled": {"background_color":0xFF444444, "secondary_color":0xFF444444, "color" : 0xFF777777}}):
            min_max_drag = ui.FloatDrag(model=main_model, step=step, precision=3, style={"background_color":0xFF006600, "secondary_color":0xFF006600})
            min_max_label = ui.Button("Set Limit", style={"background_color":0xFF006666})

        def change_limit_main(min_model):
            if math.isinf(min_model.get_value_as_float()):
                min_max_label.visible = True
            else:
                min_max_label.visible = False
            min_max_drag.visible = not min_max_label.visible
            
        def on_changed_other(max_model):
            value = 1 if default_limit > 0 else -1
            if math.isinf(max_model.get_value_as_float()):
                setattr(min_max_drag, min_or_max, getattr(sys.float_info, min_or_max))
            else:
                setattr(min_max_drag, min_or_max, max_model.get_value_as_float() + value)
    
        self._inspector_simulation.add_control_to_disable(min_max_drag)
        min_max_label.set_clicked_fn(lambda: main_model.set_value(default_limit))
        main_model.add_value_changed_fn(change_limit_main)
        other_model.add_value_changed_fn(on_changed_other)
        main_model.add_value_changed_fn(self._change_selected)
        change_limit_main(main_model)
        on_changed_other(other_model)
        self._add_usd_model(main_model)
        self._add_usd_model(other_model)
   
    @staticmethod
    def _get_step_for_prim(prim : Usd.Prim) -> float:
        if prim.IsA(UsdPhysics.PrismaticJoint):
            meters_per_unit : float = UsdGeom.GetStageMetersPerUnit(prim.GetStage())
            millimeters_per_unit = meters_per_unit * 1000
            return 1 / millimeters_per_unit
        else:
            return 0.1

    def _build_value_item(self, prim):
        default_limit = self.get_default_slider_limit(prim)
        stage = prim.GetStage()
        min_usd_model = UsdAttributeModel(  stage=stage, attribute_paths=[prim.GetPath().AppendProperty("physics:lowerLimit")], 
                                            self_refresh=True, metadata={}, change_on_edit_end=False)
        max_usd_model = UsdAttributeModel(  stage=stage, attribute_paths=[prim.GetPath().AppendProperty("physics:upperLimit")], 
                                            self_refresh=True, metadata={}, change_on_edit_end=False)
        val_usd_model = UsdAttributeModel(  stage=stage, attribute_paths=[self.get_value_attribute_path(prim)],
                                            self_refresh=True, metadata={}, change_on_edit_end=False)
        step = InspectorTreeDelegate._get_step_for_prim(prim)
        with ui.ZStack():
            value_drag = ui.FloatDrag(model=val_usd_model, step=step, style={ "draw_mode":ui.SliderDrawMode.DRAG, "background_color":0xFFFF0000})
            value_slider = ui.FloatSlider(  width=ui.Fraction(1),
                                            model=val_usd_model,
                                            alignment=ui.Alignment.LEFT_CENTER,
                                            step=step,
                                            min=-360,
                                            max=+360,
                                            precision=3,
                                            style={ "draw_mode":ui.SliderDrawMode.FILLED,
                                                    "border_radius":0,
                                                    "secondary_color":0xFFFF0000,
                                                    "background_color":0xFF23211F })

        def choose_float_or_drag():
            # If we have no limits set, we can't show the slider
            if math.isinf(min_usd_model.get_value_as_float()) or math.isinf(max_usd_model.get_value_as_float()):
                value_slider.visible = False
                value_drag.visible = True
            else:
                value_drag.visible = False
                value_slider.visible = True

        def change_limit_min(min_model):
            if min_model.get_value_as_float() == float("-inf"):
                value_drag.min = -default_limit
                value_slider.min = -default_limit
            else:
                value_drag.min = min_model.get_value_as_float()
                value_slider.min = min_model.get_value_as_float()
            choose_float_or_drag()

        def change_limit_max(max_model):
            if max_model.get_value_as_float() == float("+inf"):
                value_drag.max = +default_limit
                value_slider.max = +default_limit
            else:
                value_drag.max = max_model.get_value_as_float()
                value_slider.max = max_model.get_value_as_float()
            choose_float_or_drag()

        velocity_attribute = self.get_velocity_attribute(prim)

        # We want to step the authoring simulation as long as user is pressing on the slider
        value_slider.set_mouse_pressed_fn(lambda x, y, b, m: self._inspector_simulation.start_authoring_simulation())
        value_drag.set_mouse_pressed_fn(lambda x, y, b, m: self._inspector_simulation.start_authoring_simulation())
        # value_slider.set_mouse_released_fn(lambda x, y, b, m: self.stop_authoring_simulation())
        if velocity_attribute:
            attr = prim.GetAttribute(velocity_attribute.name)
            def set_to_zero():
                attr.Set(0)
            val_usd_model.add_value_changed_fn(lambda a: set_to_zero())

        # We change slider min/max with upper and lower limits values
        min_usd_model.add_value_changed_fn(change_limit_min)
        max_usd_model.add_value_changed_fn(change_limit_max)
        change_limit_min(min_usd_model)
        change_limit_max(max_usd_model)
        choose_float_or_drag()
        self._add_usd_model(min_usd_model)
        self._add_usd_model(max_usd_model)
        self._add_usd_model(val_usd_model)

    def _build_joint_row_column(self, prim, column_id):
        if self.is_supported_joint_type(prim):
            default_limit = self.get_default_slider_limit(prim)                                                
            if column_id == 1:
                self._build_min_max_item(prim, 'max', "physics:lowerLimit", "physics:upperLimit", -default_limit)
            elif column_id == 2:
                self._build_value_item(prim)
            elif column_id == 3:
                self._build_min_max_item(prim, 'min', "physics:upperLimit", "physics:lowerLimit", +default_limit)
        elif column_id == 2:
            ui.Label(self.get_unsupported_joint_description(prim), style_type_name_override="TreeView.Item", width=0, tooltip=prim.GetPath().pathString)

    def _build_joint_row(self, prim):
        if self.is_supported_joint_type(prim):
            self._build_value_item(prim)
        else:
            ui.Label(self.get_unsupported_joint_description(prim), style_type_name_override="TreeView.Item", width=0, tooltip=prim.GetPath().pathString)

    def build_widget(self, model, item, column_id, level, expanded):
        if item is None: # OM-64107 and/or OM-52829: connected to other references to the issue in this file
            return
        stage = omni.usd.get_context().get_stage()
        usd_path_model = model.get_item_value_model(item, 1)

        if column_id == 0:
            name_model = model.get_item_value_model(item, 0)
            if name_model is not None:
                ui.Label(name_model.as_string, style_type_name_override="TreeView.Item", width=0, tooltip=usd_path_model.as_string)
        else:
            if usd_path_model is not None and Sdf.Path.IsValidPathString(usd_path_model.as_string):
                prim = stage.GetPrimAtPath(usd_path_model.as_string)
                if prim.IsValid() and prim.IsA(UsdPhysics.Joint):
                    if self._is_joints_list():
                        self._build_joint_row_column(prim, column_id)
                    else:
                        self._build_joint_row(prim)
                else:
                    ui.Label(usd_path_model.as_string, style_type_name_override="TreeView.Item", width=0, tooltip=usd_path_model.as_string)

    def _change_selected(self, model):
        if self._inside_change_selected:
            return
        self._inside_change_selected = True
        value = model.get_value_as_float()
        selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
        stage = omni.usd.get_context().get_stage()
        original_prop = stage.GetPropertyAtPath(model._object_paths[0])
        changed_token = model._object_paths[0].name
        props_to_change = []
        found_triggering_node = False
        for sel in selection:
            prop_path = Sdf.Path(sel).AppendProperty(changed_token)
            if prop_path != model._object_paths[0]:
                prop = stage.GetPropertyAtPath(prop_path)
                if prop.IsValid():
                    props_to_change.append(prop)
            else:
                found_triggering_node = True

        # We only change other properties if we are inside the selection
        if found_triggering_node:
            for prop in props_to_change:
                prop.Set(original_prop.Get(), Usd.TimeCode.Default())

        self._inside_change_selected = False

    def build_branch(self, model, item, column_id, level, expanded):
        if item is None:
            ui.Spacer(height=15) # OM-64107 and/or OM-52829: connected to other references to the issue in this file
            return
        if column_id == 0:
            with ui.HStack(height=0):
                ui.Spacer(width=4*level)
                ui.Label(self._get_branch_text(expanded, model.can_item_have_children(item)), style_type_name_override="TreeView.Item", width=15)

    def _get_branch_text(self, expanded, can_have_children):
        return ("-" if expanded else "+") if can_have_children else " "

    def _is_joints_list(self) -> bool:
        return self._model_inspector.get_inspector_type() == pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_LIST

    def build_header(self, column_id):
        style_type_name = "TreeView.Header"
        header_label = ""
        if self._is_joints_list():
            if column_id == 0:
                header_label = "Joint Name"
            elif column_id == 1:
                header_label = "Lower Limit"
            elif column_id == 2:
                header_label = "Drive Target / Position"
            elif column_id == 3:
                header_label = "Upper Limit"
        else:
            if column_id == 0:
                header_label = "Name"
            else:
                header_label = "Value"

        with ui.HStack():
            ui.Spacer(width=10)
            ui.Label(header_label, style_type_name_override=style_type_name)


class InspectorTreeModel(ui.AbstractItemModel):
    def __init__(self, model_inspector : PhysXInspectorModel, model_item):
        super().__init__()
        self._model_inspector = model_inspector
        self._model_item = model_item

    def get_item_value_model_count(self, item):
        if self._is_joints_list():
            return 4
        else:
            return self._model_inspector.get_item_value_model_count(item)
    
    def get_item_children(self, item):
        if item is None:
            children = self._model_inspector.get_item_children(self._model_item)
            # We add a "dummy" none item, to correct the height of the treeview due to (OM-64107 and/or OM-52829)
            children.append(None)
            return children
        return self._model_inspector.get_item_children(item)
        
    def get_item_value_model(self, item, column_id):
        return self._model_inspector.get_item_value_model(item, column_id)

    def _is_joints_list(self) -> bool:
        return self._model_inspector.get_inspector_type() == pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_LIST

class InspectorCategoryModel(ui.AbstractItemModel):
    def __init__(self, model_inspector : PhysXInspectorModel):
        super().__init__()
        self._flat_data_shape = False
        self._model_inspector = model_inspector
        self._inner_model_changed_id = model_inspector.add_item_changed_fn(self._inner_model_changed)

    def _is_joints_list(self) -> bool:
        return self._model_inspector.get_inspector_type() == pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_LIST

    def clean(self):
        self._model_inspector.remove_item_changed_fn(self._inner_model_changed_id)
        self._model_inspector = None

    def _inner_model_changed(self, model, item):
        self._item_changed(None)

    def set_flat_data_shape(self, value):
        self._flat_data_shape = PhysXInspectorModelDataShapeType(value) == PhysXInspectorModelDataShapeType.FLAT

    def is_flat_data_shape(self):
        return self._flat_data_shape
    
    def get_item_value_model_count(self, item):
        if self.is_flat_data_shape():
            if self._is_joints_list():
                return 4
            else:
                return self._model_inspector.get_item_value_model_count(item)
        return 1
    
    def get_item_children(self, item):
        if self.is_flat_data_shape():
            return self._model_inspector.get_item_children(item)
        if not item:
            return self._model_inspector.get_item_children(item)
        return []
        
    def get_item_value_model(self, item, column_id):
        return self._model_inspector.get_item_value_model(item, column_id)

class InspectorCategoryDelegate(ui.AbstractItemDelegate):
    def __init__(self,  delegate_tree : InspectorTreeDelegate, 
                        handler_selection : InspectorSelectionHandler, 
                        handler_context_menu : InspectorContextMenuHandler):
        super().__init__()
        self._delegate_tree = delegate_tree
        self._handler_selection = handler_selection
        self._handler_context_menu = handler_context_menu
        self._model_trees = []
    
    def clean(self):
        self._delegate_tree = None
        self._handler_selection = None
        self._handler_context_menu = None
        self._model_trees = []

    def build_branch(self, model : InspectorCategoryModel, item, column_id, level, expanded):
        if model.is_flat_data_shape():
            self._delegate_tree.build_branch(model._model_inspector, item, column_id, level, expanded)
        else:
            super().build_branch(model._model_inspector, item, column_id, level, expanded)
        
    def build_widget(self, model : InspectorCategoryModel, item, column_id, level, expanded):
        if model.is_flat_data_shape():
            self._delegate_tree.build_widget(model._model_inspector, item, column_id, level, expanded)
        else:
            style = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"
            if style == "NvidiaLight":
                tree_style = { "CollapsableFrame": {"background_color": 0xFF535354} }
            else:
                tree_style = { "CollapsableFrame": {"background_color": 0xFF23211F} }

            text_model = model.get_item_value_model(item, column_id)
            with ui.VStack(content_clipping=True): # Blocks clicks going to the underlying treeview
                with ui.CollapsableFrame(text_model.as_string, style=tree_style):
                    tree_model = InspectorTreeModel(model._model_inspector, item)
                    self._model_trees.append(tree_model)
                    tree_view = ui.TreeView(tree_model, 
                                            delegate=self._delegate_tree, 
                                            root_visible=False, 
                                            style={"margin": 0.5}, 
                                            columns_resizable=True, 
                                            header_visible=False,
                                            column_widths=[200, ui.Fraction(1)])
                    tree_view.set_selection_changed_fn(lambda sel: self._handler_selection.push_view_selection_to_stage(sel, tree_view))
                    tree_view.set_mouse_pressed_fn(lambda x,y,b,c: self._build_context_menu(b, tree_view, model))
                    self._handler_selection.add_tree_view(tree_view)

                    # OM-64107: we must set header_visible=True later in order to get correct treeview height
                    async def set_treeview_header_later():
                        await omni.kit.app.get_app().next_update_async()
                        tree_view.header_visible = True
                    # TODO: Figure out why we get error on the sliders
                    # Tried to call pure virtual function "AbstractValueModel::set_value"
                    asyncio.ensure_future(set_treeview_header_later())

    def _build_context_menu(self, button, tree_view, model):
        if button == 1:
            self._handler_context_menu.build_context_menu(tree_view.selection, model._model_inspector)

    def build_header(self, column_id):
        self._delegate_tree.build_header(column_id)


class InspectorPanel:
    def __init__(self,  model_inspector : PhysXInspectorModel, 
                        handler_selection : InspectorSelectionHandler,
                        handler_context_menu : InspectorContextMenuHandler):
        # Models
        self._model_inspector = model_inspector
        self._model_category = InspectorCategoryModel(self._model_inspector)
        self._model_category.set_flat_data_shape(self._model_inspector.get_data_shape_model().get_value_as_int())

        # UI Handlers
        self._handler_context_menu = handler_context_menu
        self._handler_selection = handler_selection

        # Delegates
        self._delegate_tree = InspectorTreeDelegate(self._model_inspector, handler_selection._inspector._inspector_simulation)
        self._delegate_category = InspectorCategoryDelegate(self._delegate_tree, self._handler_selection, self._handler_context_menu)

        # Subscriptions
        self._sub_data_shape = self._model_inspector.get_data_shape_model().add_value_changed_fn(self._on_data_shape_changed)

        # UI Elements
        self._ui_root_omniui_widget = None

        # Build UI
        with ui.ZStack():
            self._ui_root_omniui_widget = ui.TreeView(self._model_category, delegate=self._delegate_category, root_visible=False)
            self._set_treeview_properties()
            self._ui_root_imgui_widget = PhysXInspectorWidget()
            self._ui_root_imgui_widget.model = self._model_inspector

    def clean(self):
        # Subscriptions
        self._model_inspector.get_data_shape_model().remove_value_changed_fn(self._sub_data_shape)
        self._sub_path_changed = None
        self._sub_data_shape = None
        self._sub_settings_lock = None

        # Models
        self._model_inspector = None
        self._ui_root_imgui_widget.model = None
        self._model_category.clean()
        self._model_category = None

        # Delegates
        self._delegate_category.clean()
        self._delegate_category = None
        self._delegate_tree.clean()
        self._delegate_tree = None

        # UI Elements
        self._ui_root_omniui_widget = None
        self._ui_root_imgui_widget = None

        # UI Handlers
        self._handler_context_menu = None
        self._handler_selection = None

    def set_inspector_type(self, type):
        self._model_inspector.set_inspector_type(type)
        self._delegate_tree.clean_usd_models()
        self._ui_root_imgui_widget.inspector_type = type

    def set_use_omni_ui(self, use_omni_ui):
        self._ui_root_imgui_widget.visible = not use_omni_ui
        self._ui_root_omniui_widget.visible = use_omni_ui

    def _build_context_menu(self, button, tree_view, model):
        if button == 1:
            self._handler_context_menu.build_context_menu(tree_view.selection, model)

    def _set_treeview_properties(self):
        if self._model_category.is_flat_data_shape():
            self._ui_root_omniui_widget.columns_resizable = True
            self._ui_root_omniui_widget.header_visible = True
            if self._delegate_tree._is_joints_list():
                self._ui_root_omniui_widget.column_widths = [ui.Fraction(0.55), ui.Fraction(0.4), ui.Fraction(1), ui.Fraction(0.4)]
            else:
                self._ui_root_omniui_widget.column_widths = [ui.Fraction(0.5), ui.Fraction(1)]
            self._ui_root_omniui_widget.style = {"margin": 0.5}                                           
            self._ui_root_omniui_widget.set_selection_changed_fn(lambda sel: self._handler_selection.push_view_selection_to_stage(sel, self._ui_root_omniui_widget))
            self._ui_root_omniui_widget.set_mouse_pressed_fn(lambda x,y,b,c: self._build_context_menu(b, self._ui_root_omniui_widget, self._model_inspector))
            self._handler_selection.add_tree_view(self._ui_root_omniui_widget)
        else:
            self._ui_root_omniui_widget.columns_resizable = False
            self._ui_root_omniui_widget.header_visible = False
            self._ui_root_omniui_widget.column_widths = []
            self._ui_root_omniui_widget.style = {}
        
    def _on_data_shape_changed(self, model : ui.SimpleIntModel):
        self._handler_selection._inspector._inspector_simulation.stop_authoring_simulation()
        self._delegate_tree.clean_usd_models()
        self._model_category.set_flat_data_shape(self._model_inspector.get_data_shape_model().get_value_as_int())
        self._set_treeview_properties()
