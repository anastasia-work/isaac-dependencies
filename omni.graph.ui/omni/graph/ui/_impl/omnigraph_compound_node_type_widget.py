import re
from typing import List

import omni.graph.core as og
import omni.ui as ui
from omni.kit.property.usd.usd_property_widget import SchemaPropertiesWidget, UiDisplayGroup, UsdPropertyUiEntry
from pxr import OmniGraphSchema, Sdf

from .token_array_edit_widget import build_token_array_prop  # noqa: PLE0402

INPUTS_PREFIX = "omni:graph:input"
OUTPUTS_PREFIX = "omni:graph:output"
INPUT_GROUP_TITLE = "Inputs"
OUTPUT_GROUP_TITLE = "Outputs"
DEFAULT_GROUP_TITLE = "Properties"

# -------------------------------------------------------------------------------------------

_split_camel_reg = re.compile(r"[A-Z](?:[a-z0-9]+|[A-Z]*(?=[A-Z]|$))")


def camel_case_split(name: str) -> List[str]:
    """Return a list of camel-case delimited parts of the given name"""
    if not name:
        return []
    name_part = name[0].upper() + name[1:]
    return _split_camel_reg.findall(name_part)


def make_title_case(name: str) -> str:
    """Convert a camel-case name to a title-case equivalent"""
    return " ".join(camel_case_split(name))


def make_category(name: str) -> str:
    split = name.split(":")
    return ":".join([make_title_case(s) for s in split])


# -------------------------------------------------------------------------------------------


class OmniGraphCompoundNodeTypePropertiesWidget(SchemaPropertiesWidget):
    """Property widget for Compound Node Type"""

    def __init__(self, title: str):
        super().__init__(title, schema=OmniGraphSchema.OmniGraphCompoundNodeType, include_inherited=True)
        self._compound_props = None
        self._input_props = None
        self._output_props = None
        categories = og.get_node_categories_interface().get_all_categories()
        default_categories = []
        if categories is not None:
            default_categories = list(categories.keys())
        self._default_categories = default_categories
        self._formatted_categories = [(make_category(s), s) for s in self._default_categories]
        self._formatted_categories.sort(key=lambda s: s[0].lower())

    def __get_display_name(self, name: str) -> str:
        """Nicify the display name"""

        # remove prefix
        name = name.split(":")[-1]
        # capitialize the first letter
        name = name[0:1].upper() + name[1:]
        # aplpy custom replacements
        name = name.replace("UiName", "Display Name")

        return name

    def _customize_props_layout(self, props):
        """Overridden to customize property layout"""
        for prop in props:
            prop.override_display_name(self.__get_display_name(prop.attr_name))
            if prop.attr_name.startswith(INPUTS_PREFIX):
                prop.override_display_group(INPUT_GROUP_TITLE)
            elif prop.attr_name.startswith(OUTPUTS_PREFIX):
                prop.override_display_group(OUTPUT_GROUP_TITLE)

        return props

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        """Customize property building"""
        metadata = ui_prop.metadata
        type_name = metadata.get(Sdf.PrimSpec.TypeNameKey, "unknown type")
        sdf_type_name = Sdf.ValueTypeNames.Find(type_name)
        if sdf_type_name.type == Sdf.ValueTypeNames.TokenArray.type:
            ui_prop.build_fn = build_token_array_prop

        return super().build_property_item(stage, ui_prop, prim_paths)

    def get_additional_kwargs(self, ui_prop: UsdPropertyUiEntry):
        """
        Overrides to supply additional kwargs. For this widget, input and outputs are limited to a single
        entry
        """

        additional_label_kwargs, additional_widget_kwargs = super().get_additional_kwargs(ui_prop)
        if ui_prop.prop_name.startswith(INPUTS_PREFIX) or ui_prop.prop_name.startswith(OUTPUTS_PREFIX):
            additional_widget_kwargs = dict(additional_widget_kwargs or [])
            additional_widget_kwargs["targets_limit"] = 1

        if ui_prop.prop_name == str(OmniGraphSchema.Tokens.omniGraphCategories):
            additional_widget_kwargs = dict(additional_widget_kwargs or [])
            additional_widget_kwargs["allowed_tokens"] = self._formatted_categories

        return additional_label_kwargs, additional_widget_kwargs

    def _filter_props_to_build(self, props):
        """Filters which properties to build. Listens for input and output props as well as schema properties"""

        input_props = list(filter(lambda prop: prop.GetName().startswith(INPUTS_PREFIX), props))
        output_props = list(filter(lambda prop: prop.GetName().startswith(OUTPUTS_PREFIX), props))
        filtered_props = list(
            filter(
                lambda prop: prop.GetName() != str(OmniGraphSchema.Tokens.omniGraphTags),
                super()._filter_props_to_build(props),
            )
        )

        return filtered_props + input_props + output_props

    def build_nested_group_frames(self, stage, display_group: UiDisplayGroup):
        """
        Overridden to draw the input and output groups after the main properties
        """
        if self._multi_edit:
            prim_paths = self._payload.get_paths()
        else:
            prim_paths = self._payload[-1:]

        def build_props(props):
            collapse_frame = len(props) > 0
            # we need to build those property in 2 different possible locations
            for prop in props:
                self.build_property_item(stage, prop, prim_paths)
                collapse_frame &= prop.display_group_collapsed

            return collapse_frame

        def build_nested(display_group: UiDisplayGroup, prefix: str):
            header_id = prefix + ":" + display_group.name
            frame = ui.CollapsableFrame(
                title=display_group.name,
                build_header_fn=lambda collapsed, text, id=header_id: self._build_frame_header(
                    collapsed, text, header_id
                ),
                name="subFrame",
            )

            with frame:
                with ui.VStack(height=0, spacing=5, name="frame_v_stack"):
                    collapse = build_props(display_group.props)
                    if collapse and isinstance(frame, ui.CollapsableFrame):
                        frame.collapsed = collapse

                # if level is 0, this is the root level group, and we use the self._title for its name
                self._build_header_context_menu(
                    group_name=display_group.name, group_id=header_id, props=display_group.props
                )

        with ui.VStack(height=0, spacing=5, name="frame_v_stack"):
            build_props(display_group.props)
            for _, sub_group in display_group.sub_groups.items():
                if sub_group.props:
                    build_nested(sub_group, self._title)

    def destroy(self):
        pass
