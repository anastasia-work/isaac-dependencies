# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from functools import partial
from typing import List

import omni.graph.core as og
import omni.graph.ui as ogui
import omni.ui as ui
from omni.kit.property.usd.custom_layout_helper import CustomLayoutFrame, CustomLayoutGroup, CustomLayoutProperty
from omni.kit.property.usd.usd_attribute_model import TfTokenAttributeModel
from omni.kit.property.usd.usd_attribute_widget import UsdPropertyUiEntry
from omni.kit.window.property.templates import HORIZONTAL_SPACING, LABEL_WIDTH
from pxr import Sdf, Usd

from .omnigraph_attribute_builder import OmniGraphPropertiesWidgetBuilder  # noqa: PLE0402

# Common functionality for get/set prim attribute templates


ATTRIB_LABEL_STYLE = {"alignment": ui.Alignment.RIGHT_TOP}


def get_use_path(stage: Usd.Stage, node_prim_path: Sdf.Path) -> bool:
    # Gets the value of the usePath input attribute
    if stage.GetPrimAtPath(node_prim_path):
        attr = og.Controller.attribute(f"{node_prim_path}.inputs:usePath")
        return attr.get()
    return False


def get_targeted_prim(stage: Usd.Stage, node_prim_path: Sdf.Path) -> Usd.Prim:
    """Returns the first targeted prim."""

    if not stage.GetPrimAtPath(node_prim_path):
        return None

    prim = None
    if get_use_path(stage, node_prim_path):
        attr = og.Controller.attribute(f"{node_prim_path}.inputs:primPath")
        path = attr.get()
        if Sdf.Path.IsValidPathString(path):
            prim = stage.GetPrimAtPath(path)
    else:
        attr = og.Controller.attribute(f"{node_prim_path}.inputs:prim")
        targets = attr.get()
        # We check that targets is a list to avoid bad call when a bundle is connected
        if isinstance(targets, list) and len(targets) > 0:
            # We have to use the string object here since the return type is a usdrt.Sdf.Path
            prim = stage.GetPrimAtPath(targets[0].GetText())
    return prim if prim is not None and prim.IsValid() else None


def is_usable(type_name: Sdf.ValueTypeName) -> bool:
    # Returns True if the given type can be used by OG
    return og.AttributeType.type_from_sdf_type_name(str(type_name)).base_type != og.BaseDataType.UNKNOWN


def get_filtered_attributes(prim: Usd.Prim) -> List[str]:
    # Return attributes that should be selectable for the given prim
    # FIXME: Ideally we only want to show attributes that are useful and can actually be sensibly set. We
    # will want to add customize logic here to handle pseudo-attributes that can only be manipulated using
    # USD function sets.
    return [p.GetName() for p in prim.GetAttributes() if not p.IsHidden() and is_usable(p.GetTypeName())]


class TargetPrimAttributeNameModel(TfTokenAttributeModel):
    """Model for selecting the target attribute for the write/read operation. We modify the list to show attributes
    which are available on the target prim.
    """

    class AllowedTokenItem(ui.AbstractItem):
        def __init__(self, item, label):
            """
            Args:
                item: the attribute name token to be shown
                label: the label to show in the drop-down
            """
            super().__init__()
            self.token = item
            self.model = ui.SimpleStringModel(label)

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        node_prim_path: Sdf.Path,
        target_prim: Usd.Prim,
    ):
        """
        Args:
            stage: The current stage
            attribute_paths: The list of full attribute paths
            self_refresh: ignored
            metadata: pass-through metadata for model
            node_prim_path: The path of the compute node
        """
        self._stage = stage
        self._node_prim_path = node_prim_path
        self._target_prim = target_prim
        self._max_attrib_name_length = 0
        super().__init__(stage, attribute_paths, self_refresh, metadata)

    def _get_allowed_tokens(self, _):
        # Override of TfTokenAttributeModel to specialize what tokens are to be shown
        return self._get_target_attribs_of_interest()

    def _update_value(self, force=False):
        # Override of TfTokenAttributeModel to refresh the allowed token cache
        self._update_allowed_token()
        super()._update_value(force)

    def _item_factory(self, item):
        # Construct the item for the model
        label = item
        # FIXME: trying to right-justify type in drop down doesn't work because
        # font is not fixed widget
        # if item and self._target_prim:
        #    prop = self._target_prim.GetProperty(item)
        #    if prop:
        #        spacing = 2 + (self._max_attrib_name_length - len(item))
        #        label = f"{item} {' '*spacing} {str(prop.GetTypeName())})"
        return TargetPrimAttributeNameModel.AllowedTokenItem(item, label)

    def _update_allowed_token(self):
        # Override of TfTokenAttributeModel to specialize the model items
        super()._update_allowed_token(token_item=self._item_factory)

    def _get_target_attribs_of_interest(self) -> List[str]:
        # Returns the attributes we want to let the user select from
        prim = self._stage.GetPrimAtPath(self._node_prim_path)
        attribs = []
        if prim:
            if self._target_prim:
                attribs = get_filtered_attributes(self._target_prim)
            self._max_attrib_name_length = max(len(s) for s in attribs) if attribs else 0
            name_attr = prim.GetAttribute("inputs:name")
            if len(attribs) > 0:
                current_value = name_attr.Get()
                if (current_value is not None) and (current_value != "") and (current_value not in attribs):
                    attribs.append(current_value)
                attribs.insert(0, "")
            else:
                name_attr.Set("")
        return attribs


class PrimAttributeCustomLayoutBase:
    """Base class for Read/WritePrimAttribute"""

    # Set by the derived class to customize the layout
    _value_is_output = True

    def __init__(self, compute_node_widget):
        self.enable = True
        self.compute_node_widget = compute_node_widget
        self.stage = compute_node_widget.stage
        self.node_prim_path: Sdf.Path = compute_node_widget._payload[-1]
        self.use_path = get_use_path(self.stage, self.node_prim_path)
        self.attribs = []
        self.target_attrib_name_model = None
        self.prim_path_model = None
        self.prim_rel_widget = None
        self.use_path_model = None
        self._inputs_prim_watcher = None
        self._inputs_usepath_watcher = None

    def _name_attrib_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the Attribute Name widget
        targeted_prim = get_targeted_prim(self.stage, self.node_prim_path)
        is_graph_target = targeted_prim and (self.node_prim_path.GetParentPath() == targeted_prim.GetPrimPath())
        if not targeted_prim or is_graph_target:
            # Build the simple token input for data-driven attribute name
            ui_prop.override_display_name("Attribute Name")
            self.target_attrib_name_model = OmniGraphPropertiesWidgetBuilder.build(
                self.stage,
                ui_prop.prop_name,
                ui_prop.metadata,
                ui_prop.property_type,
                [self.node_prim_path],
                {"enabled": True, "style": ATTRIB_LABEL_STYLE},
                {"enabled": True},
            )
            return self.target_attrib_name_model
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            ui.Label("Attribute Name", name="label", style=ATTRIB_LABEL_STYLE, width=LABEL_WIDTH)
            ui.Spacer(width=HORIZONTAL_SPACING)
            with ui.ZStack():
                attr_path = self.node_prim_path.AppendProperty("inputs:name")
                # Build the token-selection widget when prim is known
                self.target_attrib_name_model = TargetPrimAttributeNameModel(
                    self.stage, [attr_path], False, {}, self.node_prim_path, targeted_prim
                )
                ui.ComboBox(self.target_attrib_name_model)
        return self.target_attrib_name_model

    def _prim_path_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the token input prim path widget
        ui_prop.override_display_name("Prim Path")
        self.prim_path_model = OmniGraphPropertiesWidgetBuilder.build(
            self.stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [self.node_prim_path],
            {"enabled": self.use_path, "style": ATTRIB_LABEL_STYLE},
            {"enabled": self.use_path},
        )
        self.prim_path_model.add_value_changed_fn(self._on_target_prim_path_changed)
        return self.prim_path_model

    def _prim_rel_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the relationship input prim widget
        ui_prop.override_display_name("Prim")
        additional_widget_kwargs = {
            "on_remove_target": self._on_target_prim_rel_changed,
            "target_picker_on_add_targets": self._on_target_prim_rel_changed,
        }
        if self.use_path:
            additional_widget_kwargs["enabled"] = False

        self.prim_rel_widget = OmniGraphPropertiesWidgetBuilder.build(
            self.stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [self.node_prim_path],
            {"enabled": not self.use_path, "style": ATTRIB_LABEL_STYLE},
            additional_widget_kwargs,
        )
        if hasattr(self.prim_rel_widget, "value_model"):
            self.prim_rel_widget.value_model.add_value_changed_fn(self._on_target_prim_rel_changed)
        return self.prim_rel_widget

    def _use_path_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the boolean toggle for inputs:usePath
        ui_prop.override_display_name("Use Path")
        self.use_path_model = OmniGraphPropertiesWidgetBuilder.build(
            self.stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [self.node_prim_path],
            {"style": ATTRIB_LABEL_STYLE},
        )
        self.use_path_model.add_value_changed_fn(self._on_usepath_changed)
        return self.use_path_model

    def _on_target_prim_rel_changed(self, *args):
        # When the inputs:prim relationship changes
        # Dirty the attribute name list model because the prim may have changed
        self.target_attrib_name_model._set_dirty()  # noqa: PLW0212
        # need to rebuild so the attributes updates
        self.compute_node_widget.request_rebuild()

    def _on_target_prim_path_changed(self, *args):
        # When the inputs:primPath token changes
        # Dirty the attribute name list model because the prim may have changed
        self.target_attrib_name_model._set_dirty()  # noqa: PLW0212

    def _on_usepath_changed(self, _):
        # When the usePath toggle changes
        self.prim_rel_widget._set_dirty()  # noqa: PLW0212
        self.prim_path_model._set_dirty()  # noqa: PLW0212
        # FIXME: Not sure why _set_dirty doesn't trigger UI change, have to rebuild
        self.compute_node_widget.request_rebuild()

    def apply(self, props):
        # Called by compute_node_widget to apply UI when selection changes

        def build_fn_for_value(prop: UsdPropertyUiEntry):
            def build_fn(*args):
                # The resolved attribute is procedural and does not inherit the meta-data of the extended attribute
                # so we need to manually set the display name
                prop.override_display_name("Value")
                self.compute_node_widget.build_property_item(
                    self.compute_node_widget.stage, prop, self.compute_node_widget._payload  # noqa: PLW0212
                )

            return build_fn

        frame = CustomLayoutFrame(hide_extra=True)
        with frame:
            with CustomLayoutGroup("Inputs"):
                prop = ogui.find_prop(props, "inputs:prim")
                if prop:
                    CustomLayoutProperty(prop.prop_name, build_fn=partial(self._prim_rel_build_fn, prop))

                prop = ogui.find_prop(props, "inputs:usePath")
                if prop:
                    CustomLayoutProperty(None, None, build_fn=partial(self._use_path_build_fn, prop))

                prop = ogui.find_prop(props, "inputs:primPath")
                if prop:
                    CustomLayoutProperty(None, None, build_fn=partial(self._prim_path_build_fn, prop))

                prop = ogui.find_prop(props, "inputs:name")
                if prop:
                    CustomLayoutProperty(None, None, build_fn=partial(self._name_attrib_build_fn, prop))

                # Build the input/output value widget using the compute_node_widget logic so that
                # we get the automatic handling of extended attribute

                if not self._value_is_output:
                    prop = ogui.find_prop(props, "inputs:usdWriteBack")
                    if prop:
                        CustomLayoutProperty(prop.prop_name, "Persist To USD")
                    prop = ogui.find_prop(props, "inputs:value")
                    if prop:
                        CustomLayoutProperty(None, None, build_fn=build_fn_for_value(prop))
                else:
                    prop = ogui.find_prop(props, "inputs:usdTimecode")
                    if prop:
                        CustomLayoutProperty(prop.prop_name, "Time")

            if self._value_is_output:
                with CustomLayoutGroup("Outputs"):
                    prop = ogui.find_prop(props, "outputs:value")
                    if prop:
                        CustomLayoutProperty(None, None, build_fn=build_fn_for_value(prop))
        return frame.apply(props)


class ReadPrimsCustomLayoutBase:
    """Base class for ReadPrimsBundle and ReadPrims"""

    def __init__(self, compute_node_widget):
        self.enable = True
        self.compute_node_widget = compute_node_widget
        self.prims_rel_widget = None
        self.attr_names_to_import_widget = None
        self.usd_timecode_widget = None
        self.ATTRIB_LABEL_STYLE = ATTRIB_LABEL_STYLE

    def _find_prop(self, props, name):
        return ogui.find_prop(props, name)

    def _use_prims_rel(self, stage, node_prim_path):
        return True

    def _prims_rel_build_fn(self, ui_prop: UsdPropertyUiEntry, *args, enabled_by_use_rel: bool = True):
        # Build the relationship inputs:prims widget, override with no limit
        stage = self.compute_node_widget.stage
        node_prim_path = self.compute_node_widget.payload[-1]
        use_prim_rel = self._use_prims_rel(stage, node_prim_path)
        ui_prop.override_display_name("Prims")
        additional_widget_kwargs = {
            "on_remove_target": self._on_target_prims_rel_changed,
            "target_picker_on_add_targets": self._on_target_prims_rel_changed,
        }
        if enabled_by_use_rel and not use_prim_rel:
            additional_widget_kwargs["enabled"] = False
        self.prims_rel_widget = OmniGraphPropertiesWidgetBuilder.build(
            stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [node_prim_path],
            {
                "enabled": not enabled_by_use_rel or enabled_by_use_rel and use_prim_rel,
                "style": self.ATTRIB_LABEL_STYLE,
            },
            additional_widget_kwargs,
        )
        return self.prims_rel_widget

    def _on_target_prims_rel_changed(self, *args):
        # When the inputs:prims relationship changes
        # Dirty the attribute name list model because the prim may have changed
        self.prims_rel_widget._set_dirty()  # noqa: PLW0212

    def _attr_names_to_import_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build widget for attribute inputs:attrNamesToImport
        stage = self.compute_node_widget.stage
        node_prim_path = self.compute_node_widget.payload[-1]
        ui_prop.override_display_name("Attribute Name Pattern")
        self.attr_names_to_import_widget = OmniGraphPropertiesWidgetBuilder.build(
            stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [node_prim_path],
            {"style": self.ATTRIB_LABEL_STYLE},
        )
        return self.attr_names_to_import_widget

    def _usd_timecode_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the timecode inputs:usdTimecode widget
        stage = self.compute_node_widget.stage
        node_prim_path = self.compute_node_widget.payload[-1]
        ui_prop.override_display_name("Time")
        self.usd_timecode_widget = OmniGraphPropertiesWidgetBuilder.build(
            stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [node_prim_path],
            {"style": self.ATTRIB_LABEL_STYLE},
        )
        return self.usd_timecode_widget


class PrimPathCustomLayoutBase:
    """Base class for Nodes that use a Prim/PrimPath pair"""

    # Set the prim rel name to customize
    _prim_rel_name = "inputs:prim"

    def __init__(self, compute_node_widget):
        self.enable = True
        self.compute_node_widget = compute_node_widget
        self.prim_widget = None
        self.prim_path_widget = None
        self.ATTRIB_LABEL_STYLE = ATTRIB_LABEL_STYLE
        self.node_prim_path = compute_node_widget._payload[-1]  # noqa: PLW0212
        self.stage = compute_node_widget.stage

    def _find_prop(self, props, name):
        return ogui.find_prop(props, name)

    def _on_prim_changed(self, *args):
        # When the prim relationship changes
        self.prim_path_widget._set_dirty()  # noqa: PLW0212
        # FIXME: Not sure why _set_dirty doesn't trigger UI change, have to rebuild
        self.compute_node_widget.request_rebuild()

    def _rel_has_target(self, name: str) -> bool:
        # Returns True if prim relationship has targets
        prim = self.stage.GetPrimAtPath(self.node_prim_path)
        if prim:
            rel = prim.GetRelationship(name)
            if rel:
                return len(rel.GetTargets()) != 0
        return False

    def _prim_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the prim relationship widget
        self.prim_widget = OmniGraphPropertiesWidgetBuilder.build(
            self.stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [self.node_prim_path],
            {"style": self.ATTRIB_LABEL_STYLE},
            {
                "on_remove_target": self._on_prim_changed,
                "target_picker_on_add_targets": self._on_prim_changed,
            },
        )
        return self.prim_widget

    def _prim_path_build_fn(self, ui_prop: UsdPropertyUiEntry, *args):
        # Build the primPath attribute widget
        use_path = not self._rel_has_target(self._prim_rel_name)
        self.prim_path_widget = OmniGraphPropertiesWidgetBuilder.build(
            self.stage,
            ui_prop.prop_name,
            ui_prop.metadata,
            ui_prop.property_type,
            [self.node_prim_path],
            {"enabled": use_path, "style": self.ATTRIB_LABEL_STYLE},
            {"enabled": use_path},
        )
        return self.prim_path_widget
