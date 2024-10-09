"""
this file is full of prototypes/modification of external classes that would be impossible to
readably modify with inheritance, all of this would eventually be re/moved and replaced by
proper external depedency
"""


def get_bound_material(prim, material_purpose):
    binding = UsdShade.MaterialBindingAPI(prim).GetDirectBinding(material_purpose)
    return binding.GetMaterial(), binding.GetBindingRel()

# #################################################################################################
# support for externals, might stay in this ext, might be moved to omni.kit or to omni.physx later

import omni.kit.commands
from typing import Union
from pxr import UsdShade, UsdPhysics

PERSISTENT_SETTINGS_PREFIX = "/persistent"


class BindMaterialExtCommand(omni.kit.commands.Command):
    def __init__(self, prim_path: Union[str, list], material_path: str, strength=None, material_purpose=""):
        self._prim_path = prim_path
        self._material_path = material_path
        self._material_purpose = material_purpose

        self._strength = strength
        if self._strength == None:
            settings = carb.settings.get_settings()
            strengthSetting = settings.get(PERSISTENT_SETTINGS_PREFIX + "/app/stage/materialStrength")
            self._strength = (
                UsdShade.Tokens.strongerThanDescendants
                if strengthSetting == "strongerThanDescendants"
                else UsdShade.Tokens.weakerThanDescendants
            )
        self._prev_material = None
        self._prev_strength = None

    def _bind(self, binding_api, material_prim, strength):
        if material_prim:
            material = UsdShade.Material(material_prim)
            binding_api.Bind(material, strength, self._material_purpose)
        else:
            binding_api.UnbindDirectBinding(self._material_purpose)

    # list of prims, so there could be parent problems due to material inheritance
    def _bind_material_list(self, prim_paths, material_path, material_strength):
        stage = omni.usd.get_context().get_stage()
        if stage:
            prev_mat_path = []
            prev_mat_strength = []

            if not isinstance(material_path, list):
                material_path = [material_path] * len(prim_paths)
            if not isinstance(material_strength, list):
                material_strength = [material_strength] * len(prim_paths)

            # get list of previous values
            for prim_path in prim_paths:
                prim = stage.GetPrimAtPath(prim_path)
                if prim:
                    binding_api = UsdShade.MaterialBindingAPI(prim)
                    mat, rel = get_bound_material(prim, self._material_purpose)
                    mat_path = mat.GetPath() if mat else None

                    # ignore inherited materials
                    if rel and rel.GetPrim() != prim:
                        mat_path = None
                    prev_mat_path.append(mat_path)
                    prev_mat_strength.append(
                        UsdShade.MaterialBindingAPI.GetMaterialBindingStrength(rel) if rel else self._strength
                    )

            # apply new material
            index = 0
            for prim_path in prim_paths:
                prim = stage.GetPrimAtPath(prim_path)
                if prim:
                    material_prim = stage.GetPrimAtPath(material_path[index]) if material_path[index] and material_path[index] is not Constant.SDF_PATH_INVALID else None
                    binding_api = UsdShade.MaterialBindingAPI(prim)
                    self._bind(binding_api, material_prim, material_strength[index])
                    index = index + 1
            return prev_mat_path, prev_mat_strength
        return None

    def _bind_material(self, material_path, strength):
        if isinstance(self._prim_path, list):
            return self._bind_material_list(self._prim_path, material_path, strength)
        return self._bind_material_list([self._prim_path], material_path, strength)

    def do(self):
        self._prev_material, self._prev_strength = self._bind_material(self._material_path, self._strength)

    def undo(self):
        self._bind_material(self._prev_material, self._prev_strength)


omni.kit.commands.register_all_commands_in_module(__name__)

# #################################################################################################
# src: usd_binding_widget.py, material_utils.py

from omni.kit.window.property.templates import SimplePropertyWidget, LABEL_HEIGHT
from omni.kit.property.material.scripts.material_utils import Constant
from functools import partial
from pxr import Usd, UsdShade
from omni.usd import PrimCaching

import copy
import carb
import omni.ui as ui
import omni.usd


def default_stage_filter(p):
    return p.IsA(UsdShade.Material) and not omni.usd.is_hidden_type(p)


class MaterialUtils:
    def __init__(self):
        self._stage = None
        self._usd_material_cache = None
        self._prim_caching = None

    def __del__(self):
        self._stage = None
        self._usd_material_cache = None
        if self._prim_caching:
            del self._prim_caching
            self._prim_caching = None

    def set_payload(self, payload):
        if self._stage == payload.get_stage():
            return
        self._stage = payload.get_stage()
        self._prim_caching = PrimCaching(UsdShade.Material, self._stage)

    def get_materials_from_stage(self, stage_filter_fn=default_stage_filter):
        if self._stage is None:
            carb.log_verbose(f"get_materials_from_stage error stage isn't initalized")
            return
        materials = self._usd_material_cache
        if materials is None or self._prim_caching.get_cache_state() == False:
            materials = [Constant.SDF_PATH_INVALID]
            for p in self._stage.Traverse():
                if stage_filter_fn(p):
                    mat_path = p.GetPath().pathString
                    if mat_path not in materials:
                        if not p.GetMetadata("ignore_material_updates"):
                            materials.append(mat_path)
            self._usd_material_cache = materials
            self._prim_caching.set_cache_state(True)
        return materials

    def get_material_strength(self, prim, material_purpose=""):
        strength = None
        material, relationship = get_bound_material(prim, material_purpose)
        if relationship:
            strength = UsdShade.MaterialBindingAPI.GetMaterialBindingStrength(relationship)
        return strength

    def get_binding_from_prims(self, prim_paths, material_purpose=""):
        def update_strength(value, strength):
            if value is None:
                value = strength
            elif value != strength:
                value = Constant.MIXED
            return value

        if self._stage is None:
            carb.log_verbose(f"get_binding_from_prims error stage isn't initalized")
            return

        prims = {"material": {}, "bound": set(), "bound_info": set(), "relationship": set(), "strength": None}
        strength_default = carb.settings.get_settings().get(
            Constant.PERSISTENT_SETTINGS_PREFIX + "/app/stage/materialStrength"
        )
        if strength_default is None:
            strength_default = UsdShade.Tokens.weakerThanDescendants 

        for prim_path in prim_paths:
            prim = self._stage.GetPrimAtPath(prim_path)
            inherited = False
            strength = strength_default
            material_name = Constant.SDF_PATH_INVALID
            if prim:
                material, relationship = get_bound_material(prim, material_purpose)
                if material:
                    if (
                        material
                        and relationship
                        and prim.GetPath().pathString != relationship.GetPrim().GetPath().pathString
                    ):
                        inherited = True
                    if relationship:
                        strength = UsdShade.MaterialBindingAPI.GetMaterialBindingStrength(relationship)
                    material_name = material.GetPrim().GetPath().pathString

                if not material_name in prims["material"]:
                    prims["material"][material_name] = {
                        "bound": set(),
                        "inherited": set(),
                        "bound_info": set(),
                        "inherited_info": set(),
                        "relationship": set(),
                        "strength": None,
                    }

                if inherited:
                    prims["material"][material_name]["inherited"].add(prim)
                    prims["material"][material_name]["inherited_info"].add(
                        (prim.GetPath().pathString, material_name, strength)
                    )
                else:
                    prims["material"][material_name]["bound"].add(prim)
                    prims["material"][material_name]["bound_info"].add(
                        (prim.GetPath().pathString, material_name, strength)
                    )
                    prims["bound"].add(prim)
                    prims["bound_info"].add((prim.GetPath().pathString, material_name, strength))

                if relationship:
                    prims["relationship"].add(relationship)
                    prims["material"][material_name]["relationship"].add(relationship)

                if strength is not None:
                    prims["material"][material_name]["strength"] = update_strength(
                        prims["material"][material_name]["strength"], strength
                    )
                    prims["strength"] = update_strength(prims["strength"], strength)
        return prims


class UsdBindingAttributeWidget(SimplePropertyWidget):
    def __init__(self, stage_filter_fn=default_stage_filter, title="Materials on selected models", material_command="BindMaterial", material_purpose=""):
        super().__init__(title, collapsed=False)
        self._strengths = {
            "Weaker than Descendants": UsdShade.Tokens.weakerThanDescendants,
            "Stronger than Descendants": UsdShade.Tokens.strongerThanDescendants,
        }
        self._material_utils = MaterialUtils()
        self._material_command = material_command
        self._material_purpose = material_purpose
        self._stage_filter_fn = stage_filter_fn
        self._sub_to_undo_redo()

    def clean(self):
        super().clean()
        self._unsub_to_undo_redo()
        del self._material_utils

    def _get_prim(self, prim_path):
        if prim_path:
            stage = self._payload.get_stage()
            if stage:
                return stage.GetPrimAtPath(prim_path)
        return None

    def _undo_redo_on_change(self, cmds):
        if any(item in [self._material_command, "SetMaterialStrength", "SetMaterialStrengthCommand"] for item in cmds):
            if self._collapsable_frame:
                self._collapsable_frame.rebuild()

    def _sub_to_undo_redo(self):
        omni.kit.undo.subscribe_on_change(self._undo_redo_on_change)

    def _unsub_to_undo_redo(self):
        omni.kit.undo.unsubscribe_on_change(self._undo_redo_on_change)

    def on_new_payload(self, payload):
        """
        See PropertyWidget.on_new_payload
        """
        if not super().on_new_payload(payload):
            return False

        if len(self._payload) == 0:
            return False

        for prim_path in self._payload:
            prim = self._get_prim(prim_path)
            if not prim or not omni.usd.is_prim_material_supported(prim):
                return False

        self._material_utils.set_payload(payload)

        return True

    def _get_index(self, items: list, value: str, default_value: int = 0):
        index = default_value
        try:
            index = items.index(value)
        except:
            pass
        return index

    def _build_combo(self, combo_list: list, combo_index: int, on_fn: callable):
        def set_visible(widget, visible):
            widget.visible = visible

        with ui.ZStack():
            combo = ui.ComboBox(combo_index, *combo_list, style={"ComboBox": {"font_size": Constant.FONT_SIZE}})
            combo.model.add_item_changed_fn(on_fn)
            if combo_index == -1:
                placeholder = ui.Label(
                    "Mixed",
                    height=LABEL_HEIGHT,
                    style={
                        "font_size": Constant.FONT_SIZE,
                        "background_color": 0xFFFF0000,
                        "color": Constant.MIXED_COLOR,
                        "margin_width": 5,
                    },
                )
                self._combo_subscription.append(
                    combo.model.get_item_value_model().subscribe_value_changed_fn(
                        lambda m, w=placeholder: set_visible(w, m.as_int < 0)
                    )
                )
            return combo

    def _build_binding_info(
        self,
        inherited: bool,
        icon_name: str,
        material_list: list,
        material_path: str,
        strength_value: str,
        bound_prim_list: list,
        on_material_fn: callable,
        on_strength_fn: callable,
        on_goto_fn: callable,
    ):
        default_style = {"font_size": Constant.FONT_SIZE}
        prim_style = default_style

        ## fixup Constant.SDF_PATH_INVALID vs "None"
        material_list = copy.copy(material_list)
        if material_list[0] == Constant.SDF_PATH_INVALID:
            material_list[0] = "None"
        if material_path == Constant.SDF_PATH_INVALID:
            material_path = "None"

        if len(bound_prim_list) == 1:
            if isinstance(bound_prim_list[0], Usd.Prim):
                bound_prims = bound_prim_list[0].GetPath().pathString
            else:
                bound_prims = bound_prim_list[0]
        elif len(bound_prim_list) > 1:
            bound_prims = Constant.MIXED
            prim_style = copy.copy(default_style)
            prim_style["color"] = Constant.MIXED_COLOR
        else:
            bound_prims = "None"

        if not self._first_row:
            ui.Separator(height=10)
        self._first_row = False

        with ui.HStack():
            ui.Image(
                icon_name,
                width=Constant.ICON_SIZE,
                height=Constant.ICON_SIZE,
                fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                style={"margin": 10},
            )
            with ui.VStack(spacing=10):
                with ui.HStack():
                    ui.Label(
                        "Prim",
                        width=Constant.BOUND_LABEL_WIDTH,
                        height=LABEL_HEIGHT,
                        style={"font_size": Constant.FONT_SIZE},
                    )
                    ui.StringField(name="prims", height=LABEL_HEIGHT, style=prim_style, enabled=False).model.set_value(
                        bound_prims
                    )

                with ui.HStack():
                    index = self._get_index(material_list, material_path, -1)
                    if index != -1 and inherited:
                        inherited_list = copy.copy(material_list)
                        inherited_list[index] = f"{inherited_list[index]} (inherited)"
                        combo = self._build_combo(inherited_list, index, on_material_fn)
                    else:
                        combo = self._build_combo(material_list, index, on_material_fn)

                    if index != -1:
                        ui.Spacer(width=4)
                        ui.Button(
                            "",
                            width=20,
                            height=20,
                            fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT,
                            clicked_fn=lambda c=combo: on_goto_fn(c.model),
                            style={"image_url": "resources/icons/find.png", "Button": {"background_color": 0x0}},
                        )

                with ui.HStack():
                    ui.Label(
                        "Strength",
                        width=Constant.BOUND_LABEL_WIDTH,
                        height=LABEL_HEIGHT,
                        style={"font_size": Constant.FONT_SIZE},
                    )
                    index = self._get_index(list(self._strengths.values()), strength_value, -1)
                    self._build_combo(list(self._strengths.keys()), index, on_strength_fn)

    def build_items(self):
        material_list = self._material_utils.get_materials_from_stage(self._stage_filter_fn)
        binding = self._material_utils.get_binding_from_prims(self._payload, self._material_purpose)
        strengths = self._strengths

        def on_strength_changed(model, item, relationships):
            index = model.get_item_value_model().as_int
            if index < 0:
                carb.log_error(f"on_strength_changed with invalid index {index}")
                return
            bind_strength = list(strengths.values())[index]
            omni.kit.undo.begin_group()
            for relationship in relationships:
                omni.kit.commands.execute("SetMaterialStrength", rel=relationship, strength=bind_strength)
            omni.kit.undo.end_group()

            if self._collapsable_frame:
                self._collapsable_frame.rebuild()

        def on_material_changed(model, item, items):
            index = model.get_item_value_model().as_int
            if index < 0:
                carb.log_error(f"on_material_changed with invalid index {index}")
                return
            bind_material_path = material_list[index] if material_list[index] != "None" else None

            prim_path_list = []
            strength_list = []
            for prim_path, material_name, strength in items:
                if material_name != bind_material_path:
                    prim_path_list.append(prim_path)
                    strength_list.append(strength)

            omni.kit.commands.execute(
                self._material_command,
                material_path=bind_material_path,
                prim_path=prim_path_list,
                strength=strength_list,
                material_purpose=self._material_purpose,
            )
            if self._collapsable_frame:
                self._collapsable_frame.rebuild()

        def on_material_goto(model):
            index = model.get_item_value_model().as_int
            if index > 0:
                prim_path = material_list[model.get_item_value_model().as_int]
                omni.usd.get_context().get_selection().set_prim_path_selected(
                    material_list[index], True, True, True, True
                )

        self._combo_subscription = []
        self._first_row = True

        data = binding["material"]

        # show mixed material for all selected prims
        if len(data) > 1:
            self._build_binding_info(
                inherited=False,
                icon_name="resources/icons/material_mixed.png",
                material_list=material_list,
                material_path=Constant.MIXED,
                strength_value=binding["strength"],
                bound_prim_list=list(binding["bound"]),
                on_material_fn=partial(on_material_changed, items=list(binding["bound_info"])),
                on_strength_fn=partial(on_strength_changed, relationships=list(binding["relationship"])),
                on_goto_fn=None,
            )

        for material_path in data:
            if data[material_path]["bound"]:
                self._build_binding_info(
                    inherited=False,
                    icon_name="resources/icons/material_placeholder.png",
                    material_list=material_list,
                    material_path=material_path,
                    strength_value=data[material_path]["strength"],
                    bound_prim_list=list(data[material_path]["bound"]),
                    on_material_fn=partial(on_material_changed, items=list(data[material_path]["bound_info"])),
                    on_strength_fn=partial(
                        on_strength_changed, relationships=list(data[material_path]["relationship"])
                    ),
                    on_goto_fn=on_material_goto,
                )

        for material_path in data:
            if data[material_path]["inherited"]:
                self._build_binding_info(
                    inherited=True,
                    icon_name="resources/icons/material_placeholder.png",
                    material_list=material_list,
                    material_path=material_path,
                    strength_value=data[material_path]["strength"],
                    bound_prim_list=list(data[material_path]["inherited"]),
                    on_material_fn=partial(on_material_changed, items=list(data[material_path]["inherited_info"])),
                    on_strength_fn=partial(
                        on_strength_changed, relationships=list(data[material_path]["relationship"])
                    ),
                    on_goto_fn=on_material_goto,
                )


# #################################################################################################
# src: widget for testing out jihui's ideas

from omni.kit.property.usd.usd_attribute_widget import UsdAttributesWidget


class PrototypeWidget(UsdAttributesWidget):
    def __init__(self, title: str, schema, is_api_schema, include_inherited: bool):
        super().__init__()
        self._title = title
        self._schema = schema
        self._include_inherited = include_inherited

    def on_new_payload(self, payload):
        if not super().on_new_payload(payload):
            return False
        if not self._payload or len(self._payload) == 0:
            return False
        for prim_path in self._payload:
            prim = self._get_prim(prim_path)
            if not prim:
                return False
            is_api_schema = Usd.SchemaRegistry().IsAppliedAPISchema(self._schema)
            if not (
                is_api_schema and prim.HasAPI(self._schema) or not is_api_schema and prim.IsA(self._schema)
            ):
                return False
        return True

    def _filter_attrs_to_build(self, attrs):
        if len(attrs) == 0:
            return attrs
        if Usd.SchemaRegistry().IsMultipleApplyAPISchema(self._schema):
            prim = attrs[0].GetPrim()
            schema_type_name = Usd.SchemaRegistry().GetSchemaTypeName(self._schema)
            schema_instances = {schema[len(schema_type_name) + 1:] for schema in prim.GetAppliedSchemas() if schema.startswith(schema_type_name)}
            filtered_attrs = []
            api_path_func_name = f"Is{schema_type_name}Path"
            api_path_func = getattr(self._schema, api_path_func_name)
            schema_attr_names = self._schema.GetSchemaAttributeNames(self._include_inherited, "")
            for attr in attrs:
                attr_path = attr.GetPath().pathString
                for instance_name in schema_instances:
                    instance_seg = attr_path.find(instance_name)
                    if instance_seg != -1:
                        api_path = attr_path[0:instance_seg + len(instance_name)]
                        if api_path_func(api_path):
                            base_name = attr_path[instance_seg + len(instance_name) + 1:]
                            if base_name in schema_attr_names:
                                filtered_attrs.append(attr)
                                break
            return filtered_attrs
        else:
            schema_attr_names = self._schema.GetSchemaAttributeNames(self._include_inherited)
            return [attr for attr in attrs if attr.GetName() in schema_attr_names]

# #################################################################################################
# src: omni.kit.widget.layers.prompt
# layers ext is crashing our tests, so ...


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

    def __exit__(self, type, value, trace):
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
        self._window = omni.ui.Window(
            self._title, visible=False, height=0, dockPreference=omni.ui.DockPreference.DISABLED
        )
        self._window.flags = (
            omni.ui.WINDOW_FLAGS_NO_COLLAPSE
            | omni.ui.WINDOW_FLAGS_NO_RESIZE
            | omni.ui.WINDOW_FLAGS_NO_SCROLLBAR
            | omni.ui.WINDOW_FLAGS_NO_RESIZE
            | omni.ui.WINDOW_FLAGS_NO_MOVE
        )

        if self._modal:
            self._window.flags = self._window.flags | omni.ui.WINDOW_FLAGS_MODAL

        with self._window.frame:
            with omni.ui.VStack(height=0):
                omni.ui.Spacer(width=0, height=10)
                with omni.ui.HStack(height=0):
                    omni.ui.Spacer()
                    self._text_label = omni.ui.Label(self._text, word_wrap=True, width=self._window.width - 80, height=0)
                    omni.ui.Spacer()
                omni.ui.Spacer(width=0, height=10)
                with omni.ui.HStack(height=0):
                    omni.ui.Spacer(height=0)
                    if self._ok_button_text:
                        ok_button = omni.ui.Button(self._ok_button_text, width=60, height=0)
                        ok_button.set_clicked_fn(self._on_ok_button_fn)
                    if self._middle_button_text:
                        middle_button = omni.ui.Button(self._middle_button_text, width=60, height=0)
                        middle_button.set_clicked_fn(self._on_middle_button_fn)
                    if self._cancel_button_text:
                        cancel_button = omni.ui.Button(self._cancel_button_text, width=60, height=0)
                        cancel_button.set_clicked_fn(self._on_cancel_button_fn)
                    omni.ui.Spacer(height=0)
                omni.ui.Spacer(width=0, height=10)
