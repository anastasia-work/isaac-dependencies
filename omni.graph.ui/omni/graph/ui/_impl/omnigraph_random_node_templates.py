# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import random
from functools import partial

import carb
import omni.ui as ui
from omni.kit.property.usd.custom_layout_helper import CustomLayoutFrame, CustomLayoutGroup, CustomLayoutProperty
from omni.kit.property.usd.usd_attribute_widget import UsdPropertyUiEntry

from .omnigraph_attribute_builder import OmniGraphPropertiesWidgetBuilder as PropertiesWidgetBuilder

ATTRIB_LABEL_STYLE = {"alignment": ui.Alignment.RIGHT_TOP}


def dict_deep_merge(dict1: dict, dict2: dict):
    def loop(dst, src):
        for key in src:
            if key in dst and isinstance(dst[key], dict) and isinstance(src[key], dict):  # noqa
                loop(dst[key], src[key])
            else:
                dst[key] = src[key]

    dest = dict1.copy()
    loop(dest, dict2)
    return dest


# Base class that makes building OGN custom layouts easier,
# more declarative, encapsulated, and without copy/pasting.
class DeclarativeCustomLayoutBase:
    def __init__(self, compute_node_widget, widget_descriptors: dict):
        self.enable = True
        self.compute_node_widget = compute_node_widget
        self.widgets = {}
        self.widget_descriptors = widget_descriptors

        # If a property is enabled by another "subject" property,
        # we make the subject refresh the UI when it changes.
        for group_desc in self.widget_descriptors.values():
            for prop_desc in group_desc.values():
                enabled_by = prop_desc.get("enabled_by", None)
                shown_by = prop_desc.get("shown_by", None)
                if enabled_by or shown_by:
                    group_desc[enabled_by]["is_refresher"] = True

    def apply(self, props):
        frame = CustomLayoutFrame(hide_extra=True)
        with frame:
            # Iterate over the property groups (typically inputs, maybe outputs)
            for group_desc_name, group_desc in self.widget_descriptors.items():
                with CustomLayoutGroup(group_desc_name.capitalize()):
                    # Iterate over the property descriptors in the group
                    for sub_name, prop_desc in group_desc.items():
                        # Add CustomLayoutProperty for the property descriptor
                        prop_name = group_desc_name + ":" + sub_name

                        try:
                            # Find prop, it *must* exist
                            prop = next((p for p in props if p.prop_name == prop_name))
                        except StopIteration:
                            carb.log_error(f"Property {sub_name} not found in {group_desc_name} ")
                            continue

                        # HACK: For some reason, union properties (like min/max)
                        # doesn't work when using the build_fn code below.
                        # Added default_ui to work around this for now, but should figure out why.
                        if group_desc_name == "outputs" or prop_desc.get("default_ui", False):
                            CustomLayoutProperty(prop.prop_name, prop_desc["display_name"])
                            continue

                        def build_fn(group_name, desc, ui_prop: UsdPropertyUiEntry, *_):
                            display_name = desc["display_name"]
                            on_change = desc.get("on_change", None)
                            is_enabled = desc.get("is_enabled", None)
                            is_visible = desc.get("is_visible", None)
                            is_refresher = desc.get("is_refresher", False)
                            enabled_by = desc.get("enabled_by", None)
                            shown_by = desc.get("shown_by", None)
                            label_props = desc.get("label_props", {}).copy()
                            widget_props = desc.get("widget_props", {}).copy()

                            label_props["style"] = ATTRIB_LABEL_STYLE

                            def set_bool_prop(primary_predicate, secondary_source, key):
                                secondary_predicate = None

                                if secondary_source:
                                    subject_name = group_name + ":" + secondary_source
                                    secondary_predicate = lambda *_: self._get_prim_attr_value(  # noqa: PLC3001
                                        subject_name
                                    )

                                if primary_predicate or secondary_predicate:
                                    value = True
                                    if primary_predicate:
                                        value = value and primary_predicate()
                                    if secondary_predicate:
                                        value = value and secondary_predicate()
                                    label_props[key] = value
                                    widget_props[key] = value

                            set_bool_prop(is_enabled, enabled_by, "enabled")
                            set_bool_prop(is_visible, shown_by, "visible")

                            on_refresh = self._refresh_ui if is_refresher else None

                            stage = self.compute_node_widget.stage
                            node_prim_path = self.compute_node_widget.payload[-1]
                            ui_prop.override_display_name(display_name)

                            self.widgets[ui_prop.prop_name] = widget = PropertiesWidgetBuilder.build(
                                stage,
                                ui_prop.prop_name,
                                ui_prop.metadata,
                                ui_prop.property_type,
                                [node_prim_path],
                                label_props,
                                widget_props,
                            )

                            if hasattr(widget, "add_value_changed_fn"):
                                if on_change:
                                    widget.add_value_changed_fn(on_change)
                                if on_refresh:
                                    widget.add_value_changed_fn(on_refresh)
                            elif hasattr(widget, "add_item_changed_fn"):
                                if on_change:
                                    widget.add_item_changed_fn(on_change)
                                if on_refresh:
                                    widget.add_item_changed_fn(on_refresh)
                            else:
                                raise Exception(f"{widget} does not provide a method to observe changes")

                        CustomLayoutProperty(None, None, build_fn=partial(build_fn, group_desc_name, prop_desc, prop))

        return frame.apply(props)

    def _get_prim_attr_value(self, input_attr_name):
        stage = self.compute_node_widget.stage
        node_prim_path = self.compute_node_widget.payload[-1]
        prim = stage.GetPrimAtPath(node_prim_path)
        value = prim.GetAttribute(input_attr_name).Get()
        return value

    def _refresh_ui(self, _):
        self.compute_node_widget.request_rebuild()


# Base class for random node widget templates
class RandomNodeCustomLayoutBase(DeclarativeCustomLayoutBase):
    def __init__(self, compute_node_widget, widget_descriptors: dict):
        default_descriptors = {
            "inputs": {
                "seed": {
                    "display_name": "Seed",
                    "enabled_by": "useSeed",
                },
                "useSeed": {
                    "display_name": "Use Seed?",
                    "on_change": self.on_use_seed_changed,
                },
            },
            "outputs": {
                "random": {
                    "display_name": "Random Output",
                }
            },
        }
        widget_descriptors = dict_deep_merge(default_descriptors, widget_descriptors)
        super().__init__(compute_node_widget, widget_descriptors)

    def on_use_seed_changed(self, _):
        # When the user changes the use_seed from False to True,
        # we copy the generated random seed in Fabric to USD.
        # The toggled from True to False, we generated a new random seed.
        stage = self.compute_node_widget.stage
        node_prim_path = self.compute_node_widget.payload[-1]
        prim = stage.GetPrimAtPath(node_prim_path)
        if prim:
            use_seed = prim.GetAttribute("inputs:useSeed").Get()
            usd_seed_attr = prim.GetAttribute("inputs:seed")
            if use_seed:
                node = self.compute_node_widget.node
                mem_seed_attr = node.get_attribute("inputs:seed")
                if mem_seed_attr and usd_seed_attr:
                    seed = mem_seed_attr.get()
                    usd_seed_attr.Set(seed)
            else:
                # TODO: We need to figure out why 64-bits doesn't work, I guess signed vs unsigned?
                seed = random.getrandbits(63)
                usd_seed_attr.Set(seed)
