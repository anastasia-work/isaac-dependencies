# Copyright (c) 2022-2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Iterator, List, Optional

import omni.graph.core as og
import omni.graph.tools.ogn as ogn
import omni.ui as ui
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel
from omni.kit.property.usd.usd_property_widget_builder import UsdPropertiesWidgetBuilder
from omni.kit.window.property.templates import HORIZONTAL_SPACING
from pxr import Sdf, Tf, Usd

from .omnigraph_attribute_base import get_model_cls  # noqa: PLE0402
from .omnigraph_attribute_models import (  # noqa: PLE0402
    OmniGraphAttributeModel,
    OmniGraphGfVecAttributeModel,
    OmniGraphGfVecAttributeSingleChannelModel,
    OmniGraphSdfTimeCodeModel,
    OmniGraphStringAttributeModel,
    OmniGraphTfTokenAttributeModel,
    OmniGraphTfTokenNoAllowedTokensModel,
)
from .targets import OmniGraphSdfRelationshipArraySingleEntryModel, OmniGraphTargetPicker  # noqa: PLE0402
from .token_array_edit_widget import build_token_array_prop  # noqa: PLE0402

# =============================================================================


def attributes_from_nodes(prim_paths: List[Sdf.Path], attr_name: str) -> Iterator[og.Attribute]:
    """Generates the matching attribute from the given nodes"""
    for prim_path in prim_paths:
        node = og.get_node_by_path(prim_path.pathString)
        if node and node.get_attribute_exists(attr_name):
            yield node.get_attribute(attr_name)


# =============================================================================


def find_first_node_with_attrib(prim_paths: List[Sdf.Path], attr_name: str) -> Optional[og.Node]:
    """Returns the first node in the paths that has the given attrib name"""
    node_with_attr = None
    for prim_path in prim_paths:
        node = og.get_node_by_path(prim_path.pathString)
        if node and node.get_attribute_exists(attr_name):
            node_with_attr = node
            break
    return node_with_attr


# =============================================================================


class OmniGraphPropertiesWidgetBuilder(UsdPropertiesWidgetBuilder):
    """OmniGraph specialization of USD widget factory based on OG API instead of USD"""

    OVERRIDE_TYPENAME_KEY = "OGTypeName"
    UNRESOLVED_TYPENAME = "OGUnresolvedType"

    tf_gf_matrix2d = Sdf.ValueTypeNames.Matrix2d
    tf_gf_matrix3d = Sdf.ValueTypeNames.Matrix3d
    tf_gf_matrix4d = Sdf.ValueTypeNames.Matrix4d
    tf_tf_tokenarray = Sdf.ValueTypeNames.TokenArray.type

    @classmethod
    def init_builder_table(cls):
        # Make our own list of builder functions because we need `cls` to be us for the
        # classmethod callstack
        cls.widget_builder_table = {
            cls.tf_half: cls._floating_point_builder,
            cls.tf_float: cls._floating_point_builder,
            cls.tf_double: cls._floating_point_builder,
            cls.tf_uchar: cls._integer_builder,
            cls.tf_uint: cls._integer_builder,
            cls.tf_int: cls._integer_builder,
            cls.tf_int64: cls._integer_builder,
            cls.tf_uint64: cls._integer_builder,
            cls.tf_bool: cls._bool_builder,
            cls.tf_string: cls._string_builder,
            cls.tf_gf_vec2i: cls._vec2_per_channel_builder,
            cls.tf_gf_vec2h: cls._vec2_per_channel_builder,
            cls.tf_gf_vec2f: cls._vec2_per_channel_builder,
            cls.tf_gf_vec2d: cls._vec2_per_channel_builder,
            cls.tf_gf_vec3i: cls._vec3_per_channel_builder,
            cls.tf_gf_vec3h: cls._vec3_per_channel_builder,
            cls.tf_gf_vec3f: cls._vec3_per_channel_builder,
            cls.tf_gf_vec3d: cls._vec3_per_channel_builder,
            cls.tf_gf_vec4i: cls._vec4_per_channel_builder,
            cls.tf_gf_vec4h: cls._vec4_per_channel_builder,
            cls.tf_gf_vec4f: cls._vec4_per_channel_builder,
            cls.tf_gf_vec4d: cls._vec4_per_channel_builder,
            # FIXME: nicer matrix handling
            cls.tf_gf_matrix2d: cls._floating_point_builder,
            cls.tf_gf_matrix3d: cls._floating_point_builder,
            cls.tf_gf_matrix4d: cls._floating_point_builder,
            cls.tf_tf_token: cls._tftoken_builder,
            cls.tf_tf_tokenarray: cls._tftokenarray_builder,
            cls.tf_sdf_asset_path: cls._sdf_asset_path_builder,
            cls.tf_sdf_time_code: cls._time_code_builder,
            Tf.Type.Unknown: cls._unresolved_builder,
        }

        vec_model_dict = {
            "model_cls": OmniGraphGfVecAttributeModel,
            "single_channel_model_cls": OmniGraphGfVecAttributeSingleChannelModel,
        }

        cls.default_model_table = {
            # _floating_point_builder
            cls.tf_half: OmniGraphAttributeModel,
            cls.tf_float: OmniGraphAttributeModel,
            cls.tf_double: OmniGraphAttributeModel,
            # _integer_builder
            cls.tf_uchar: OmniGraphAttributeModel,
            cls.tf_uint: OmniGraphAttributeModel,
            cls.tf_int: OmniGraphAttributeModel,
            cls.tf_int64: OmniGraphAttributeModel,
            cls.tf_uint64: OmniGraphAttributeModel,
            # _bool_builder
            cls.tf_bool: OmniGraphAttributeModel,
            # _string_builder
            cls.tf_string: OmniGraphStringAttributeModel,
            # _vec2_per_channel_builder
            cls.tf_gf_vec2i: vec_model_dict,
            cls.tf_gf_vec2h: vec_model_dict,
            cls.tf_gf_vec2f: vec_model_dict,
            cls.tf_gf_vec2d: vec_model_dict,
            # _vec3_per_channel_builder
            cls.tf_gf_vec3i: vec_model_dict,
            cls.tf_gf_vec3h: vec_model_dict,
            cls.tf_gf_vec3f: vec_model_dict,
            cls.tf_gf_vec3d: vec_model_dict,
            # _vec4_per_channel_builder
            cls.tf_gf_vec4i: vec_model_dict,
            cls.tf_gf_vec4h: vec_model_dict,
            cls.tf_gf_vec4f: vec_model_dict,
            cls.tf_gf_vec4d: vec_model_dict,
            # FIXME: matrix models
            cls.tf_gf_matrix2d: OmniGraphAttributeModel,
            cls.tf_gf_matrix3d: OmniGraphAttributeModel,
            cls.tf_gf_matrix4d: OmniGraphAttributeModel,
            cls.tf_tf_token: {
                "model_cls": OmniGraphTfTokenAttributeModel,
                "no_allowed_tokens_model_cls": OmniGraphTfTokenNoAllowedTokensModel,
            },
            cls.tf_tf_tokenarray: OmniGraphAttributeModel,
            cls.tf_sdf_time_code: OmniGraphSdfTimeCodeModel,
            # FIXME: Not converted yet
            # cls.tf_sdf_asset_path: cls._sdf_asset_path_builder,
        }

    @classmethod
    def startup(cls):
        cls.init_builder_table()

    @classmethod
    def _generate_tooltip_string(cls, attr_name, metadata):
        """Override tooltip to specialize extended types"""
        doc_string = metadata.get(Sdf.PropertySpec.DocumentationKey)
        type_name = metadata.get(OmniGraphPropertiesWidgetBuilder.OVERRIDE_TYPENAME_KEY, cls._get_type_name(metadata))
        tooltip = f"{attr_name} ({type_name})" if not doc_string else f"{attr_name} ({type_name})\n\t\t{doc_string}"
        return tooltip

    # -------------------------------------------------------------------------

    @staticmethod
    def _update_target_widget_kwargs(
        attr_name: str, ogn_attr: og.Attribute, prim_paths: List[Sdf.Path], additional_widget_kwargs=None
    ):
        """Helper to update the widget kwargs for an OG target input in the supplied dict"""
        # target attributes use our custom model
        additional_widget_kwargs = additional_widget_kwargs or {}
        additional_widget_kwargs[
            "relationship_array_single_value_model_cls"
        ] = OmniGraphSdfRelationshipArraySingleEntryModel
        additional_widget_kwargs["target_picker_cls"] = OmniGraphTargetPicker
        if "tooltip" not in additional_widget_kwargs:
            additional_widget_kwargs[
                "tooltip"
            ] = f"""The target prim path.
    When the graph is instanced, the special path {og.INSTANCING_GRAPH_TARGET_PATH} can be used to indicate the targeted prim"""

        allow_multi_inputs = ogn_attr.get_metadata(ogn.MetadataKeys.ALLOW_MULTI_INPUTS)
        if not allow_multi_inputs or (not int(allow_multi_inputs)):
            additional_widget_kwargs["targets_limit"] = 1

        if ogn_attr.get_port_type() != og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT or any(
            (a.get_upstream_connection_count() > 0 for a in attributes_from_nodes(prim_paths, attr_name))
        ):
            additional_widget_kwargs["enabled"] = False

    # -------------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        stage,
        attr_name,
        metadata,
        property_type,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        if property_type == Usd.Attribute:
            type_name = cls._get_type_name(metadata)
            tf_type = type_name.type

            # Lookup the build func
            build_func = cls.widget_builder_table.get(tf_type, cls._fallback_builder)

            # Check for override the default attribute model(s)
            default_model = cls.default_model_table.get(tf_type, None)
            additional_widget_kwargs = additional_widget_kwargs or {}
            if isinstance(default_model, dict):
                additional_widget_kwargs.update(default_model)
            elif default_model:
                additional_widget_kwargs["model_cls"] = default_model

            # Output attributes should be read-only
            node_with_attr = find_first_node_with_attrib(prim_paths, attr_name)
            if node_with_attr:
                ogn_attr = node_with_attr.get_attribute(attr_name)
                if ogn_attr.get_port_type() == og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT:
                    additional_widget_kwargs["enabled"] = False

            return build_func(
                stage, attr_name, type_name, metadata, prim_paths, additional_label_kwargs, additional_widget_kwargs
            )
        if property_type == Usd.Relationship:
            # if it's a relationship, check if it's a single target type and
            # limit the number of targets to 1
            node_with_attr = find_first_node_with_attrib(prim_paths, attr_name)
            if node_with_attr:
                ogn_attr = node_with_attr.get_attribute(attr_name)
                if ogn_attr.get_extended_type() == og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_REGULAR:
                    og_type = ogn_attr.get_resolved_type()
                    if og_type == og.Type(og.BaseDataType.RELATIONSHIP, 1, 0, og.AttributeRole.TARGET):
                        OmniGraphPropertiesWidgetBuilder._update_target_widget_kwargs(
                            attr_name, ogn_attr, prim_paths, additional_widget_kwargs
                        )
                    elif og_type == og.Type(og.BaseDataType.RELATIONSHIP, 1, 0, og.AttributeRole.BUNDLE):
                        # OM-97171, OM-97172 bundle is hidden until we have a widget allowing inspecting its content.
                        return None

            if additional_widget_kwargs and not additional_widget_kwargs.get("enabled", True):
                type_name = cls._get_type_name(metadata)
                return cls._fallback_builder(
                    stage, attr_name, type_name, metadata, prim_paths, additional_label_kwargs, additional_widget_kwargs
                )
            return cls._relationship_builder(
                stage, attr_name, metadata, prim_paths, additional_label_kwargs, additional_widget_kwargs
            )
        return None

    # -------------------------------------------------------------------------
    # Builder function overrides

    @classmethod
    def _tftokenarray_builder(
        cls,
        stage,
        attr_name,
        type_name,
        metadata,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        # Only use the token array widget for disconnected inputs
        if additional_widget_kwargs.get("enabled", True):
            is_connected = og.Controller.attribute(f"{prim_paths[0]}.{attr_name}").get_upstream_connection_count() > 0
            if not is_connected:
                value_widget = build_token_array_prop(
                    stage, attr_name, metadata, None, prim_paths, additional_label_kwargs, additional_widget_kwargs
                )
                return value_widget

        # Use the fallback widget otherwise
        return cls._fallback_builder(
            stage, attr_name, type_name, metadata, prim_paths, additional_label_kwargs, additional_widget_kwargs
        )

    # -------------------------------------------------------------------------

    @classmethod
    def _unresolved_builder(
        cls,
        stage,
        attr_name,
        type_name,
        metadata,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        label_txt = attr_name
        node_with_attr = find_first_node_with_attrib(prim_paths, attr_name)
        if node_with_attr:
            ogn_attr = node_with_attr.get_attribute(attr_name)
            extended_type = (
                "any" if ogn_attr.get_extended_type() == og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_ANY else "union"
            )
            label_txt = f"<unresolved {extended_type}>"

        model_cls = UsdAttributeModel
        model = model_cls(stage, [path.AppendProperty(attr_name) for path in prim_paths], False, metadata)

        kwargs = {
            "name": "models_unresolved",
            "model": model,
            "enabled": False,
            "tooltip": label_txt,
        }
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            label = cls._create_label(attr_name, metadata, additional_label_kwargs)
            ui.Label(label_txt, name="typetext", style={"alignment": ui.Alignment.LEFT_CENTER, "color": 0xFF809095})
            cls._create_control_state(value_widget=None, mixed_overlay=None, **kwargs, label=label)

        return []

    # -------------------------------------------------------------------------

    @classmethod
    def _fallback_builder(
        cls,
        stage,
        attr_name,
        type_name,
        metadata,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            model_cls = get_model_cls(OmniGraphAttributeModel, additional_widget_kwargs)
            model = model_cls(stage, [path.AppendProperty(attr_name) for path in prim_paths], False, metadata)
            label = cls._create_label(attr_name, metadata, additional_label_kwargs)
            kwargs = {
                "name": "models_readonly",
                "model": model,
                "enabled": False,
                "tooltip": model.get_value_as_string(),
            }
            if additional_widget_kwargs:
                kwargs.update(additional_widget_kwargs)
            with ui.ZStack():
                value_widget = ui.StringField(**kwargs)
                value_widget.identifier = f"fallback_{attr_name}"
                mixed_overlay = cls._create_mixed_text_overlay()
            cls._create_control_state(value_widget=value_widget, mixed_overlay=mixed_overlay, **kwargs, label=label)
            return model
