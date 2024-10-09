import asyncio
import os
import types
from functools import partial
from pathlib import Path
from typing import List

import omni.graph.core as og
import omni.kit.ui
import omni.ui as ui
import omni.usd
from omni.kit.property.usd.prim_selection_payload import PrimSelectionPayload
from omni.kit.property.usd.usd_attribute_model import FloatModel, IntModel
from omni.kit.property.usd.usd_model_base import UsdBase
from omni.kit.property.usd.usd_property_widget import (
    UsdPropertiesWidget,
    UsdPropertiesWidgetBuilder,
    UsdPropertyUiEntry,
)
from omni.kit.property.usd.widgets import ICON_PATH
from omni.kit.window.property.templates import HORIZONTAL_SPACING
from pxr import Gf, OmniGraphSchema, Sdf, Tf, Usd

from .omnigraph_compound_node_type_widget import OmniGraphCompoundNodeTypePropertiesWidget
from .stage_picker_dialog import StagePickerDialog  # noqa: PLE0402
from .token_array_edit_widget import build_token_array_prop  # noqa: PLE0402
from .utils import Prompt, get_icons_dir  # noqa: PLE0402

REMOVE_BUTTON_STYLE = style = {"image_url": str(Path(ICON_PATH).joinpath("remove.svg")), "margin": 0, "padding": 0}

AUTO_REFRESH_PERIOD = 0.33  # How frequently to poll for variable refreshes

WARN_ICON = os.path.join(get_icons_dir(), "warn.svg")

GRAPH_VARIABLE_ATTR_PREFIX = "graph:variable:"
OMNIGRAPHS_REL_ATTR = "omniGraphs"
COMPUTEGRAPH_TYPE_NAME = "OmniGraph"

# Keys for metadata dictionary that the vector variable runtime model will lookup
VARIABLE_ATTR = "variable_attr"
VARIABLE_GRAPH_PATH = "variable_graph_path"
VARIABLE_INSTANCE_PATH = "variable_instance_path"

# Used to determine if we need a single channel model builder or not
VECTOR_TYPES = {
    UsdPropertiesWidgetBuilder.tf_gf_vec2i,
    UsdPropertiesWidgetBuilder.tf_gf_vec2h,
    UsdPropertiesWidgetBuilder.tf_gf_vec2f,
    UsdPropertiesWidgetBuilder.tf_gf_vec2d,
    UsdPropertiesWidgetBuilder.tf_gf_vec3i,
    UsdPropertiesWidgetBuilder.tf_gf_vec3h,
    UsdPropertiesWidgetBuilder.tf_gf_vec3f,
    UsdPropertiesWidgetBuilder.tf_gf_vec3d,
    UsdPropertiesWidgetBuilder.tf_gf_vec4i,
    UsdPropertiesWidgetBuilder.tf_gf_vec4h,
    UsdPropertiesWidgetBuilder.tf_gf_vec4f,
    UsdPropertiesWidgetBuilder.tf_gf_vec4d,
}


class OmniGraphProperties:
    def __init__(self):
        self._api_widget = None
        self._variables_widget = None
        self._compound_node_type_widget = None
        self.on_startup()

    def on_startup(self):
        import omni.kit.window.property as p

        w = p.get_window()
        if w:
            self._api_widget = OmniGraphAPIPropertiesWidget("Visual Scripting")
            w.register_widget("prim", "omni_graph_api", self._api_widget)
            self._variables_widget = OmniGraphVariablesPropertiesWidget("Variables")
            w.register_widget("prim", "omni_graph_variables", self._variables_widget)
            self._compound_node_type_widget = OmniGraphCompoundNodeTypePropertiesWidget("Compound Node Type")
            w.register_widget("prim", "omni_graph_compound_node_type", self._compound_node_type_widget)

    def on_shutdown(self):
        import omni.kit.window.property as p

        w = p.get_window()
        if w:
            if self._api_widget is not None:
                w.unregister_widget("prim", "omni_graph_api")
                self._api_widget.destroy()
                self._api_widget = None
            if self._variables_widget is not None:
                w.unregister_widget("prim", "omni_graph_variables")
                self._variables_widget.destroy()
                self._variables_widget = None
            if self._compound_node_type_widget is not None:
                w.unregister_widget("prim", "omni_graph_compound_node_type")
                self._compound_node_type_widget.destroy()
                self._compound_node_type_widget = None


# ----------------------------------------------------------------------------------------
def is_different_from_default_override(self) -> bool:
    """Override for USDBase.is_different_from_default"""
    # Values that are backed by real attributes _always_ override the default value.
    # Values that are backed by placeholders never override the default value.
    attributes = self._get_attributes()  # noqa: PLW0212
    return any(isinstance(attribute, Usd.Attribute) for attribute in attributes)


class OmniGraphAPIPropertiesWidget(UsdPropertiesWidget):
    """Widget for graph instances"""

    def __init__(self, title: str):
        super().__init__(title, collapsed=False)
        self._title = title
        from omni.kit.property.usd import PrimPathWidget

        self._add_button_menus = []
        self._add_button_menus.append(
            PrimPathWidget.add_button_menu_entry(
                "Visual Scripting",
                show_fn=self._button_show,
                onclick_fn=self._button_onclick,
            )
        )
        self._omnigraph_vars = []
        self._omnigraph_vars_props = []
        self._graph_targets = set()
        self._stage_picker = None
        self._stage_picker_selected_graph = None
        self._pending_rebuild_task = None

    def destroy(self):
        from omni.kit.property.usd import PrimPathWidget

        for menu in self._add_button_menus:
            PrimPathWidget.remove_button_menu_entry(menu)
        self._add_button_menus = []

    def _button_show(self, objects: dict):
        if "prim_list" not in objects or "stage" not in objects:
            return False
        stage = objects["stage"]
        if not stage:
            return False
        prim_list = objects["prim_list"]
        if len(prim_list) < 1:
            return False
        for item in prim_list:
            if isinstance(item, Sdf.Path):
                prim = stage.GetPrimAtPath(item)
            elif isinstance(item, Usd.Prim):
                prim = item
            type_name = prim.GetTypeName()
            if "Graph" in type_name or prim.HasAPI(OmniGraphSchema.OmniGraphAPI):
                return False
        return True

    def _on_stage_picker_select_graph(self, selected_prim):
        omni.kit.commands.execute(
            "ApplyOmniGraphAPICommand", paths=self._apply_prim_paths, graph_path=selected_prim.GetPath()
        )
        self._refresh_window()
        return True

    def _button_onclick(self, payload: PrimSelectionPayload):
        if payload is None:
            return Sdf.Path.emptyPath
        if self._stage_picker:
            self._stage_picker.clean()

        self._stage_picker = StagePickerDialog(
            omni.usd.get_context().get_stage(),
            lambda p: self._on_stage_picker_select_graph(p),  # noqa: PLW0108
            "Select Graph",
            "Select",
            [],
            lambda p: self._filter_target_lambda(p),  # noqa: PLW0108
        )
        self._stage_picker.show()
        self._apply_prim_paths = payload.get_paths()  # noqa: PLW0201
        return self._apply_prim_paths

    def on_new_payload(self, payload):
        self._omnigraph_vars.clear()
        self._omnigraph_vars_props.clear()
        self._graph_targets.clear()
        if not super().on_new_payload(payload):
            return False
        if not self._payload or len(self._payload) == 0:
            return False
        for prim_path in payload:  # noqa: PLR1702
            prim = self._get_prim(prim_path)
            if not prim:
                return False
            attrs = prim.GetProperties()
            for attr in attrs:
                attr_name_str = attr.GetName()
                if attr_name_str == OMNIGRAPHS_REL_ATTR:
                    targets = attr.GetTargets()
                    for target in targets:
                        self._graph_targets.add(target)
                        target_prim = self._get_prim(target)
                        target_attrs = target_prim.GetAttributes()
                        for target_attr in target_attrs:
                            target_attr_name = target_attr.GetName()
                            if target_attr_name.startswith(GRAPH_VARIABLE_ATTR_PREFIX):
                                self._omnigraph_vars.append(target_attr_name)
                                self._omnigraph_vars_props.append(target_attr)
                    return True
            return False
        return False

    def _filter_props_to_build(self, props):
        return [
            prop
            for prop in props
            if prop.GetName().startswith(OMNIGRAPHS_REL_ATTR)
            or (prop.GetName().startswith(GRAPH_VARIABLE_ATTR_PREFIX) and prop.GetName() in self._omnigraph_vars)
        ]

    def _filter_target_lambda(self, target_prim):
        return target_prim.GetTypeName() == COMPUTEGRAPH_TYPE_NAME

    def get_additional_kwargs(self, ui_attr):
        random_prim = Usd.Prim()
        if self._payload:
            prim_paths = self._payload.get_paths()
            for prim_path in prim_paths:
                prim = self._get_prim(prim_path)
                if not prim:
                    continue
                if not random_prim:
                    random_prim = prim
                elif random_prim.GetTypeName() != prim.GetTypeName():
                    break
        if ui_attr.prop_name == OMNIGRAPHS_REL_ATTR:
            return None, {"target_picker_filter_lambda": self._filter_target_lambda}
        return None, None

    def _get_default_value(self, attr_name):
        """Retreives the default value from the backing attribute"""
        for graph_prop in self._omnigraph_vars_props:
            prop_name = graph_prop.GetName()
            if prop_name == attr_name:
                if graph_prop.HasValue():
                    return graph_prop.Get()
                return graph_prop.GetTypeName().defaultValue

        return None

    def _customize_props_layout(self, attrs):
        variable_group = "Variables"
        instance_props = set()
        for attr in attrs:
            if attr.attr_name == OMNIGRAPHS_REL_ATTR:
                attr.override_display_group("Graphs")
                attr.override_display_name("Graphs")
            if attr.attr_name in self._omnigraph_vars:
                instance_props.add(attr.attr_name)
                var_offset = attr.attr_name.rindex(":") + 1
                display_group = variable_group
                display_name = attr.attr_name[var_offset:]
                attr.override_display_name(display_name)
                attr.override_display_group(display_group)
                attr.add_custom_metadata("default", self._get_default_value(attr.attr_name))

        # append the graph properties that don't appear in the list
        for graph_prop in self._omnigraph_vars_props:
            prop_name = graph_prop.GetName()
            if prop_name in instance_props:
                continue
            value = graph_prop.GetTypeName().defaultValue
            if graph_prop.HasValue():
                value = graph_prop.Get()
            ui_prop = UsdPropertyUiEntry(
                prop_name,
                variable_group,
                {Sdf.PrimSpec.TypeNameKey: str(graph_prop.GetTypeName()), "customData": {"default": value}},
                Usd.Attribute,
            )

            var_offset = prop_name.rindex(":") + 1
            ui_prop.override_display_name(prop_name[var_offset:])
            attrs.append(ui_prop)

        # sort by name to keep the ordering consistent as placeholders are
        # modified and become actual properies
        def sort_key(elem):
            return elem.attr_name

        attrs.sort(key=sort_key)

        def build_header(*args):
            with ui.HStack(spacing=HORIZONTAL_SPACING):
                ui.Label("Initial", alignment=ui.Alignment.RIGHT)
                ui.Label("Runtime", alignment=ui.Alignment.RIGHT)

        header_prop = UsdPropertyUiEntry("header", variable_group, {}, Usd.Property, build_fn=build_header)
        attrs.insert(0, header_prop)

        return attrs

    def _is_placeholder_property(self, ui_prop: UsdPropertyUiEntry) -> bool:
        """Returns false if this property represents a graph target property that has not
        been overwritten
        """
        if not ui_prop.attr_name.startswith(GRAPH_VARIABLE_ATTR_PREFIX):
            return False

        if self._payload:
            prim_paths = self._payload.get_paths()
            for prim_path in prim_paths:
                prim = self._get_prim(prim_path)
                if prim and prim.HasAttribute(ui_prop.attr_name):
                    return True

        return False

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        metadata = ui_prop.metadata
        type_name = metadata.get(Sdf.PrimSpec.TypeNameKey, "unknown type")
        sdf_type_name = Sdf.ValueTypeNames.Find(type_name)
        if sdf_type_name.type == Sdf.ValueTypeNames.TokenArray.type:
            ui_prop.build_fn = build_token_array_prop
        elif ui_prop.attr_name.startswith(GRAPH_VARIABLE_ATTR_PREFIX):
            ui_prop.build_fn = build_variable_prop

        # override the build function to make modifications to the model
        build_fn = ui_prop.build_fn if ui_prop.build_fn else UsdPropertiesWidgetBuilder.build
        ui_prop.build_fn = partial(self.__build_fn_intercept, build_fn)

        return super().build_property_item(stage, ui_prop, prim_paths)

    def _on_remove_with_prompt(self):
        def on_remove_omnigraph_api():
            selected_paths = omni.usd.get_context().get_selection().get_selected_prim_paths()
            omni.kit.commands.execute("RemoveOmniGraphAPICommand", paths=selected_paths)

        prompt = Prompt(
            "Remove Visual Scripting?",
            "Are you sure you want to remove the 'Visual Scripting' component?",
            "Yes",
            "No",
            ok_button_fn=on_remove_omnigraph_api,
            modal=True,
        )
        prompt.show()

    def _build_frame_header(self, collapsed, text, id_str: str = None):
        if id_str is not None:
            # only override root frame header, not UsdPropertiesWidget's subframes
            return super()._build_frame_header(collapsed, text, id_str)

        if collapsed:
            alignment = ui.Alignment.RIGHT_CENTER
            width = 5
            height = 7
        else:
            alignment = ui.Alignment.CENTER_BOTTOM
            width = 7
            height = 5

        with ui.HStack(spacing=8):
            with ui.VStack(width=0):
                ui.Spacer()
                ui.Triangle(
                    style_type_name_override="CollapsableFrame.Header", width=width, height=height, alignment=alignment
                )
                ui.Spacer()
            ui.Label(text, style_type_name_override="CollapsableFrame.Header")
            with ui.HStack(width=0):
                ui.Spacer(width=8)
                with ui.VStack(width=0):
                    ui.Spacer(height=5)
                    ui.Button(style=REMOVE_BUTTON_STYLE, height=16, width=16).set_mouse_pressed_fn(
                        lambda *_: self._on_remove_with_prompt()
                    )
                ui.Spacer(width=5)
        return None

    def _on_usd_changed(self, notice, stage):
        """Overrides the base case USD listener to request a rebuild if the graph target attributes change"""
        targets = notice.GetChangedInfoOnlyPaths()
        if any(p.GetPrimPath() in self._graph_targets for p in targets):
            self._refresh_window()
        else:
            super()._on_usd_changed(notice, stage)

    def _delay_refresh_window(self):
        self._pending_rebuild_task = asyncio.ensure_future(self._refresh_window())

    def _refresh_window(self):
        """Refreshes the entire property window"""
        selection = omni.usd.get_context().get_selection()
        selected_paths = selection.get_selected_prim_paths()
        window = omni.kit.window.property.get_window()._window  # noqa: PLW0212

        selection.clear_selected_prim_paths()
        window.frame.rebuild()
        selection.set_selected_prim_paths(selected_paths, True)
        window.frame.rebuild()

    def __on_set_default_callback(self, paths: List[Sdf.Path], attr_name: str):
        """
        Callback triggered when a model is set to the default value. Instead of reverting
        to a default value, this will remove the property instead
        """
        stage = omni.usd.get_context().get_stage()
        for p in paths:
            prop_path = p.AppendProperty(attr_name)
            if stage.GetAttributeAtPath(prop_path).IsValid():
                omni.kit.commands.execute("RemoveProperty", prop_path=prop_path)

    def __build_fn_intercept(
        self,
        src_build_fn,
        stage,
        attr_name,
        metadata,
        property_type,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        """Build function that leverages an existing build function and sets the model default value callback"""
        models = src_build_fn(
            stage, attr_name, metadata, property_type, prim_paths, additional_label_kwargs, additional_widget_kwargs
        )

        # Set a callback when the default is set so that it will do the same operation as remove
        # Replace the is_different_from_default method to change the behaviour of the reset to default widget
        if models:
            if issubclass(type(models), UsdBase):
                models.set_on_set_default_fn(partial(self.__on_set_default_callback, prim_paths, attr_name))
                models.is_different_from_default = types.MethodType(is_different_from_default_override, models)
            elif hasattr(models, "__iter__"):
                for model in models:
                    if issubclass(type(model), UsdBase):
                        model.set_on_set_default_fn(partial(self.__on_set_default_callback, prim_paths, attr_name))
                        model.is_different_from_default = types.MethodType(is_different_from_default_override, model)

        return models


class OmniGraphVariablesPropertiesWidget(UsdPropertiesWidget):
    """Widget for the graph"""

    def __init__(self, title: str):
        super().__init__(title, collapsed=False)
        self._title = title
        self._graph_event = None

    def destroy(self):
        self._graph_event = None

    def on_new_payload(self, payload):
        self._graph_event = None
        if not super().on_new_payload(payload):
            return False
        if not self._payload or len(self._payload) == 0:
            return False
        for prim_path in payload:
            prim = self._get_prim(prim_path)
            if not prim:
                return False
            is_graph_type = prim.GetTypeName() == COMPUTEGRAPH_TYPE_NAME
            attrs = prim.GetProperties()
            for attr in attrs:
                attr_name_str = attr.GetName()
                if is_graph_type and attr_name_str.startswith(GRAPH_VARIABLE_ATTR_PREFIX):
                    graph = og.get_graph_by_path(str(prim_path))
                    if graph.is_valid():
                        self._graph_event = graph.get_event_stream().create_subscription_to_pop(self._on_graph_event)
                    return True
            return False
        return False

    def _filter_props_to_build(self, props):
        return [prop for prop in props if prop.GetName().startswith(GRAPH_VARIABLE_ATTR_PREFIX)]

    def _filter_target_lambda(self, target_prim):
        return target_prim.GetTypeName() == COMPUTEGRAPH_TYPE_NAME

    def get_additional_kwargs(self, ui_attr):
        random_prim = Usd.Prim()
        if self._payload:
            prim_paths = self._payload.get_paths()
            for prim_path in prim_paths:
                prim = self._get_prim(prim_path)
                if not prim:
                    continue
                if not random_prim:
                    random_prim = prim
                elif random_prim.GetTypeName() != prim.GetTypeName():
                    break
        return None, None

    def _customize_props_layout(self, attrs):
        for attr in attrs:
            if attr.attr_name.startswith(GRAPH_VARIABLE_ATTR_PREFIX):
                var_offset = attr.attr_name.rindex(":") + 1
                display_name = attr.attr_name[var_offset:]
                attr.override_display_name(display_name)
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            ui.Label("Initial", alignment=ui.Alignment.RIGHT)
            ui.Label("Runtime", alignment=ui.Alignment.RIGHT)
        return attrs

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        metadata = ui_prop.metadata
        type_name = metadata.get(Sdf.PrimSpec.TypeNameKey, "unknown type")
        sdf_type_name = Sdf.ValueTypeNames.Find(type_name)
        if sdf_type_name.type == Sdf.ValueTypeNames.TokenArray.type:
            ui_prop.build_fn = build_token_array_prop
        else:
            ui_prop.build_fn = build_variable_prop
        super().build_property_item(stage, ui_prop, prim_paths)

    def _on_graph_event(self, event: og.GraphEvent):
        """
        Callback that is invoked when a graph event occurs
        """
        if (
            event.type == int(og.GraphEvent.CREATE_VARIABLE)
            or event.type == int(og.GraphEvent.REMOVE_VARIABLE)
            or event.type == int(og.GraphEvent.VARIABLE_TYPE_CHANGE)
        ):
            self._refresh_window()

    def _refresh_window(self):
        """Refreshes the entire property window"""
        selection = omni.usd.get_context().get_selection()
        selected_paths = selection.get_selected_prim_paths()
        window = omni.kit.window.property.get_window()._window  # noqa: PLW0212

        selection.clear_selected_prim_paths()
        window.frame.rebuild()
        selection.set_selected_prim_paths(selected_paths, True)
        window.frame.rebuild()


class OmniGraphVariableBase:
    """Mixin base for OmnGraph variable runtime models"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=False,
        **kwargs,
    ):
        self._soft_range_min = None
        self._soft_range_max = None
        self._variable = None
        self._value = None
        self._context = None
        self._event_sub = None
        self._dirty = True

        graph_path = kwargs.get(VARIABLE_GRAPH_PATH, None)
        self._graph_path = graph_path.pathString
        attr = kwargs.get(VARIABLE_ATTR, None)
        self._variable_name = attr.GetBaseName()
        self._instance = kwargs.get(VARIABLE_INSTANCE_PATH, None)

        self._update_counter: float = 0
        self._update_sub = (
            omni.kit.app.get_app()
            .get_update_event_stream()
            .create_subscription_to_pop(self._on_update, name="OmniGraph Variable Runtime Properties")
        )

    def _on_update(self, event):
        # Ideally, we would have fabric level notifications when a variable has been changed. But for now, just poll at
        # a fixed interval since variables can be set at any time, not just when a node computes
        self._update_counter += event.payload["dt"]
        if self._update_counter > AUTO_REFRESH_PERIOD:
            self._update_counter = 0
            self._set_dirty()

    def clean(self):
        self._update_sub = None  # unsubscribe from app update stream

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def _update_value(self, force=False):
        if self._dirty or force:
            if not self._variable:
                graph = og.get_graph_by_path(self._graph_path)
                if graph is not None:
                    self._context = graph.get_default_graph_context()
                    self._variable = graph.find_variable(self._variable_name)
            if self._variable:
                self.set_value(
                    self._variable.get(self._context)
                    if self._instance is None
                    else self._variable.get(self._context, self._instance.pathString)
                )
            self._dirty = False

    def _on_dirty(self):
        pass

    def _set_dirty(self):
        self._dirty = True
        self._on_dirty()


class OmniGraphVariableRuntimeModel(ui.AbstractValueModel, OmniGraphVariableBase):
    """Model for variable values at runtime"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=False,
        **kwargs,
    ):
        OmniGraphVariableBase.__init__(
            self, stage, attribute_paths, self_refresh, metadata, change_on_edit_end, **kwargs
        )
        ui.AbstractValueModel.__init__(self)

    def clean(self):
        OmniGraphVariableBase.clean(self)

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def get_value_as_float(self) -> float:
        self._update_value()
        return float(self._value) if self._variable is not None else 0.0

    def get_value_as_bool(self) -> bool:
        self._update_value()
        return bool(self._value) if self._variable is not None else False

    def get_value_as_int(self) -> int:
        self._update_value()
        return int(self._value) if self._variable is not None else 0

    def get_value_as_string(self) -> str:
        self._update_value()
        return str(self._value) if self._variable is not None else ""

    def _on_dirty(self):
        self._value_changed()  # tell widget that model value has changed


class OmniGraphVectorVariableRuntimeModel(ui.AbstractItemModel, OmniGraphVariableBase):
    """Model for vector variable values at runtime"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        comp_count: int,
        tf_type: Tf.Type,
        self_refresh: bool,
        metadata: dict,
        **kwargs,
    ):
        OmniGraphVariableBase.__init__(self, stage, attribute_paths, self_refresh, metadata, False, **kwargs)
        ui.AbstractItemModel.__init__(self)
        self._comp_count = comp_count
        self._data_type_name = "Vec" + str(self._comp_count) + tf_type.typeName[-1]
        self._data_type = getattr(Gf, self._data_type_name)

        class UsdVectorItem(ui.AbstractItem):
            def __init__(self, model):
                super().__init__()
                self.model = model

        # Create root model
        self._root_model = ui.SimpleIntModel()
        self._root_model.add_value_changed_fn(lambda a: self._item_changed(None))

        # Create three models per component
        if self._data_type_name.endswith("i"):
            self._items = [UsdVectorItem(IntModel(self)) for i in range(self._comp_count)]
        else:
            self._items = [UsdVectorItem(FloatModel(self)) for i in range(self._comp_count)]
        for item in self._items:
            item.model.add_value_changed_fn(lambda a, item=item: self._on_value_changed(item))

        self._edit_mode_counter = 0

    def clean(self):
        OmniGraphVariableBase.clean(self)

    def _construct_vector_from_item(self):
        if self._data_type_name.endswith("i"):
            data = [item.model.get_value_as_int() for item in self._items]
        else:
            data = [item.model.get_value_as_float() for item in self._items]
        return self._data_type(data)

    def _on_value_changed(self, item):
        """Called when the submodel is changed"""

        if self._edit_mode_counter > 0:
            vector = self._construct_vector_from_item()
            index = self._items.index(item)
            if vector and self.set_value(vector, index):
                # Read the new value back in case hard range clamped it
                item.model.set_value(self._value[index])
                self._item_changed(item)
            else:
                # If failed to update value in model, revert the value in submodel
                item.model.set_value(self._value[index])

    def _update_value(self, force=False):
        if OmniGraphVariableBase._update_value(self, force):
            if self._value is None:
                for i in range(len(self._items)):  # noqa: PLC0200
                    self._items[i].model.set_value(0.0)
                return
            for i in range(len(self._items)):  # noqa: PLC0200
                self._items[i].model.set_value(self._value[i])

    def set_value(self, value, comp=-1):
        pass

    def _on_dirty(self):
        self._item_changed(None)

    def get_item_children(self, item):
        """Reimplemented from the base class"""
        self._update_value()
        return self._items

    def get_item_value_model(self, item, column_id):
        """Reimplemented from the base class"""
        if item is None:
            return self._root_model
        return item.model

    def begin_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user starts editing.
        """
        self._edit_mode_counter += 1

    def end_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user finishes editing.
        """
        self._edit_mode_counter -= 1


class OmniGraphSingleChannelVariableRuntimeModel(OmniGraphVariableRuntimeModel):
    """Model for per-channel vector variable values at runtime"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        channel_index: int,
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=False,
        **kwargs,
    ):
        self._channel_index = channel_index
        self._soft_range_min = None
        self._soft_range_max = None
        super().__init__(stage, attribute_paths, self_refresh, metadata, False, **kwargs)

    def set_value(self, value, comp=-1):
        if comp == -1:
            super().set_value(value)
        elif hasattr(self._value, "__len__"):
            self._value[comp] = value

    def get_value_as_string(self, **kwargs) -> str:
        self._update_value()
        if self._value is None:
            return ""

        return str(self._value[self._channel_index])

    def get_value_as_float(self) -> float:
        self._update_value()
        if self._value is None:
            return 0.0

        if hasattr(self._value, "__len__"):
            return float(self._value[self._channel_index])
        return float(self._value)

    def get_value_as_bool(self) -> bool:
        self._update_value()
        if self._value is None:
            return False

        if hasattr(self._value, "__len__"):
            return bool(self._value[self._channel_index])
        return bool(self._value)

    def get_value_as_int(self) -> int:
        self._update_value()
        if self._value is None:
            return 0

        if hasattr(self._value, "__len__"):
            return int(self._value[self._channel_index])
        return int(self._value)


def build_variable_prop(
    stage,
    attr_name,
    metadata,
    property_type,
    prim_paths: List[Sdf.Path],
    additional_label_kwargs=None,
    additional_widget_kwargs=None,
):
    """Variable widget that displays both initial (USD) and runtime (Fabric) values. This customized widget will be used
    for both the graph and graph instance on a prim. Make sure we return the models, since the UsdPropertiesWidget will
    listen for usd notices and update its models accordingly"""

    # For instanced graph, prim_path is the prim that the instance is on. For non-instanced graphs, prim is the graph
    # path. See which one we have
    prims = [stage.GetPrimAtPath(path) for path in prim_paths]
    attrs = [prim.GetAttribute(attr_name) for prim in prims]
    models = []
    for idx, attr in enumerate(attrs):
        # if prim is an instance, need to get the graph path from the relationship and verify that a variable with
        # the given name is on the graph. Also handle the case where multiple graphs have the same variable (this is
        # not well supported at the moment, but the intention is for it to work)
        graphs = []
        instances = []
        mismatched_types = []
        if prims[idx].IsA(OmniGraphSchema.OmniGraph):
            graphs.append(attr.GetPrimPath())
            instances.append(None)
        else:
            for g in prims[idx].GetProperty(OMNIGRAPHS_REL_ATTR).GetTargets():
                graph = og.get_graph_by_path(g.pathString)
                var = graph.find_variable(attr.GetBaseName())
                if var:
                    if not attr or var.type == og.AttributeType.type_from_sdf_type_name(str(attr.GetTypeName())):
                        graphs.append(g)
                        instances.append(attr.GetPrimPath())
                    else:
                        mismatched_types.append((g, attr.GetPath()))

        # TODO: if the graph is instanced, and the evaluation mode is automatic or instanced, then the runtime value
        # on the graph itself won't update. Only the value on the instance will. So grey out the runtime column
        for graph, instance in zip(graphs, instances):
            with ui.HStack(spacing=HORIZONTAL_SPACING):
                # Build the initial value widget that reads from USD
                model = UsdPropertiesWidgetBuilder.build(
                    stage,
                    attr_name,
                    metadata,
                    property_type,
                    prim_paths,
                    additional_label_kwargs,
                    additional_widget_kwargs,
                )
                if isinstance(model, list):
                    models = models + model
                else:
                    models.append(model)

                # Build runtime value widget which reads from fabric
                widget_kwargs = {"no_control_state": True}
                model_kwargs = {VARIABLE_ATTR: attr, VARIABLE_GRAPH_PATH: graph, VARIABLE_INSTANCE_PATH: instance}
                type_key = metadata.get(Sdf.PrimSpec.TypeNameKey, "unknown type")
                type_name = Sdf.ValueTypeNames.Find(type_key)
                if type_name.type in VECTOR_TYPES:  # type_name.type is the tf_type
                    widget_kwargs["model_cls"] = OmniGraphVectorVariableRuntimeModel
                    widget_kwargs["single_channel_model_cls"] = OmniGraphSingleChannelVariableRuntimeModel
                else:
                    widget_kwargs["model_cls"] = OmniGraphVariableRuntimeModel
                widget_kwargs["model_kwargs"] = model_kwargs
                model = UsdPropertiesWidgetBuilder.build(
                    stage, attr_name, metadata, property_type, prim_paths, {"visible": False}, widget_kwargs
                )
                if isinstance(model, list):
                    models = models + model
                else:
                    models.append(model)

        # display the variables that have a type mismatch. Disable the control to indicate there is something incorrect
        mismatched_widget_kwargs = {"enabled": False}
        tooltip = f"Variable {attr_name} has a type mismatch between the variable defined on the instance and the graph.\nTo fix the mismatch, reset the value to its default value."
        if additional_widget_kwargs:
            mismatched_widget_kwargs.update(additional_widget_kwargs)
        for (_graph, instance) in mismatched_types:
            with ui.HStack(spacing=HORIZONTAL_SPACING):
                model = UsdPropertiesWidgetBuilder.build(
                    stage,
                    attr_name,
                    metadata,
                    property_type,
                    [instance.GetPrimPath()],
                    additional_label_kwargs,
                    mismatched_widget_kwargs,
                )
                # display the warning icon
                with ui.VStack(width=14):
                    ui.Spacer()
                    ui.ImageWithProvider(
                        WARN_ICON,
                        width=12,
                        height=12,
                        tooltip=tooltip,
                    )
                    ui.Spacer()

            if isinstance(model, list):
                models = models + model
            else:
                models.append(model)

    return models
