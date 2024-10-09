import asyncio
import importlib.util
import pathlib
import re
import weakref
from contextlib import suppress
from typing import List, Optional, Tuple

import omni.graph.core as og
import omni.graph.tools.ogn as ogn
import omni.graph.ui as ogui
import omni.kit.window.property as p
import omni.ui as ui
import omni.usd
from omni.kit.property.usd.custom_layout_helper import CustomLayoutGroup, CustomLayoutProperty
from omni.kit.property.usd.usd_attribute_widget import UsdAttributeUiEntry, UsdPropertiesWidget, UsdPropertyUiEntry
from omni.kit.window.property.templates import HORIZONTAL_SPACING, LABEL_WIDTH
from pxr import Sdf, Usd

from .omnigraph_attribute_builder import OmniGraphPropertiesWidgetBuilder  # noqa: PLE0402
from .omnigraph_attribute_builder import find_first_node_with_attrib  # noqa: PLE0402

_compute_node_widget_instance = None


class ComputeNodeWidget(UsdPropertiesWidget):
    """Creates and registers a widget in the Property Window to display Compute Node contents"""

    # self.bundles : dict[bundle_name : str, tuple[omni::graph::core::Py_Bundle, list[attrib_name : str]]]
    BUNDLE_INDEX = 0
    ATTRIB_LIST_INDEX = 1

    def __init__(self, title="OmniGraph Node", collapsed=False):
        super().__init__(title=title, collapsed=collapsed)
        self.bundle_update_sub = None
        self.bundles = {}
        self.graph_context: og.GraphContext = None
        self.graph: og.Graph = None
        self.node: og.Node = None
        self.selection = omni.usd.get_context().get_selection()
        self.stage: Usd.Stage = None
        self.stage_update_sub = None
        self.template = None
        self.template_paths: List[pathlib.Path] = []
        self.time = 0
        self.window = None
        self.window_width_change = False
        self.window_width_change_fn_set = False
        self.node_type_name = None
        self.node_event_sub = None
        self._title = "OmniGraph Node"
        self._prop_convert_menu = None

        self._payload: list[Sdf.Path] = None  # The attribute path(s)

        w = p.get_window()
        w.register_widget("prim", "compute_node", self)
        global _compute_node_widget_instance
        _compute_node_widget_instance = weakref.ref(self)

        self._register_prop_convert_menu()

        OmniGraphPropertiesWidgetBuilder.startup()

    @staticmethod
    def get_instance():
        return _compute_node_widget_instance()

    @property
    def payload(self) -> list[Sdf.Path]:
        return self._payload

    def on_shutdown(self):
        w = p.get_window()
        w.unregister_widget("prim", "compute_node")
        self._prop_convert_menu = None

    def reset(self):
        super().reset()

        window = ui.Workspace.get_window("Property")
        if self.window != window:
            self.window_width_change_fn_set = False
        self.window = window
        self.window_width_change = False

    def __on_node_event(self, event):
        # Called when one of the node event happens
        self.request_rebuild()

    def _register_prop_convert_menu(self):
        """Registers a custom property panel context menu for OG properties"""

        def _is_convertible_attrib(obj):
            model = obj.get("model", None)
            if not model:
                return False

            paths = model.get_property_paths()
            if len(paths) > 1:
                return False

            attr = None
            try:
                attr = og.Controller.attribute(paths[0].pathString)
            except og.OmniGraphError:
                # The path may not point to a node attribute
                return False

            if not attr:
                return False

            port_type = attr.get_port_type()
            if port_type != og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT:
                return False

            if attr.get_upstream_connection_count() > 0:
                return False

            extended_type = attr.get_extended_type()
            if extended_type in (
                og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_ANY,
                og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_UNION,
            ):
                return True
            return False

        def _populate_menu(obj):
            model = obj.get("model", None)
            if not model:
                return
            paths = model.get_property_paths()
            ogui.build_port_type_convert_menu(paths[0])

        menu = {
            "name": "Convert to Type",
            "show_fn": _is_convertible_attrib,
            "populate_fn": _populate_menu,
        }
        self._prop_convert_menu = omni.kit.context_menu.add_menu(menu, "attribute", "omni.kit.property.usd")

    @staticmethod
    def _get_node_types_in_payload(payload: List[Sdf.Path]) -> List[str]:
        # Returns the list of node types in the given payload
        node_types = []
        for path in payload:
            node = og.get_node_by_path(path.pathString)
            if node and node.is_valid():
                try:
                    node_type = node.get_type_name()
                    if node_type:
                        node_types.append(node_type)
                except UnicodeDecodeError:
                    pass

        return node_types

    def _update_layout_title(self, node_types: List[str]):
        # Updates the title of the layout based on the given node types
        def pretty_name(name: str) -> str:
            # Returns a pretty name for the given property
            name = name.split(":")[-1]
            name = name[0].upper() + name[1:]
            name = re.sub(r"([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))", r"\1 ", name)
            return name

        name_set = []
        for node_type in node_types:
            node_type = node_type.split(".")[-1]
            node_type = pretty_name(node_type)
            if node_type not in name_set:
                name_set.append(node_type)

        # Set the title
        #  - If there is only one node type, use that
        #  - If there are multiple node types, use "Mixed Nodes"
        #  - If there are no node types, use "OmniGraph Node"
        if len(name_set) == 1:
            title = f"{list(name_set)[0]} Node"
        elif len(name_set) > 1:
            title = "Mixed Nodes"
        else:
            title = "OmniGraph Node"

        self._title = title

    def on_new_payload(self, payload: List[Sdf.Path]) -> bool:
        """
        See PropertyWidget.on_new_payload
        """
        if self.bundle_update_sub:
            self.bundle_update_sub = None
        if self.stage_update_sub:
            self.stage_update_sub = None
        if len(payload) == 0:
            return False
        self.stage = omni.usd.get_context().get_stage()
        self.node = None
        for path in reversed(payload):
            node = og.get_node_by_path(path.pathString)
            if (
                node
                and node.is_valid()
                and self.stage.GetPrimAtPath(node.get_prim_path()).GetTypeName() == "OmniGraphNode"
            ):
                self.node = node
                self.graph = self.node.get_graph()
                self.node_event_sub = node.get_event_stream().create_subscription_to_pop(
                    self.__on_node_event, name=f"{path.pathString} Event"
                )
                break
        if self.node is None:
            return False

        # Get the node type name. This can raise a UnicodeDecodeError if the node type name is not
        # valid UTF-8. In this case, we set the node type name to None.
        try:
            self.node_type_name = self.node.get_type_name()
        except UnicodeDecodeError:
            self.node_type_name = None

        node_types = self._get_node_types_in_payload(payload)
        self._update_layout_title(node_types)

        self._payload = payload
        self.graph_context = self.graph.get_default_graph_context() if self.graph.is_valid() else None

        self.bundles = {}
        return True

    def get_additional_kwargs(self, ui_attr: UsdAttributeUiEntry):
        additional_label_kwargs = {"alignment": ui.Alignment.RIGHT}
        additional_widget_kwargs = {"no_mixed": True}
        return additional_label_kwargs, additional_widget_kwargs

    def get_widget_prim(self):
        return self.stage.GetPrimAtPath(self._payload[-1])

    def add_template_path(self, file_path):
        """Makes a path from the file_path parameter and adds it to templates paths.
        So if there is a same kind of structure:
            /templates
                template_<ModuleName>.<NameOfComputeNodeType>.py
            <my_extension>.py

        then template path can be added by this line in the <my_extension>.py:
            omni.graph.ui.ComputeNodeWidget.get_instance().add_template_path(__file__)

        example of template filename:
            template_omni.particle.system.core.Emitter.py

        """
        template_path = pathlib.Path(file_path).parent.joinpath(pathlib.Path("templates"))

        if template_path not in self.template_paths:
            self.template_paths.append(template_path)

    def get_template_path(self, template_name: str) -> Optional[pathlib.Path]:
        """Deterimine the full path to the node template if it exists"""
        for path in self.template_paths:
            path = path / template_name
            if path.is_file():
                return path
        return None

    def load_template(self, props: List[UsdPropertyUiEntry]) -> Optional[List[UsdPropertyUiEntry]]:
        """Find a template for this node and apply it to our properties"""
        if not self.node_type_name:
            return None
        if self.node_type_name.startswith("omni.graph.ui."):
            template_name = f"template_{self.node_type_name[14:]}.py"
        else:
            template_name = f"template_{self.node_type_name}.py"
        path = self.get_template_path(template_name)
        if path is None:
            return None
        spec = importlib.util.spec_from_file_location(template_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.template = module.CustomLayout(self)
        if not self.template.enable:
            return None
        return self.template.apply(props)

    async def __delayed_build_layout(self):
        await omni.kit.app.get_app().next_update_async()
        self.window.frame.rebuild()

    def rebuild_window(self):
        asyncio.ensure_future(self.__delayed_build_layout())

    def _customize_props_metadata(
        self, props: list[UsdPropertyUiEntry]
    ) -> list[Tuple[UsdPropertyUiEntry, og.Attribute]]:
        """Update ui property metadata based on OG metadata
        Returns a list of props that correspond to OG attributes
        """
        all_props = []
        for prop in props:
            if self.node.get_attribute_exists(prop.prop_name):
                node_attr = self.node.get_attribute(prop.prop_name)
                all_props.append((prop, node_attr))
                description = node_attr.get_metadata(ogn.MetadataKeys.DESCRIPTION)
                if description:
                    prop.override_doc_string(description)
                # Copy all metadata from the attribute into the attrib customData
                for key, val in node_attr.get_all_metadata().items():
                    if key == "fileExts":
                        # Temp hack to get fileExts into expected dict format - see OM-93811
                        # "Python Scripts (*.py)" => {"*.py": "Python Scripts"}
                        parts = val.split("(")
                        if len(parts) == 2:
                            val = {parts[1].strip().rstrip(")"): parts[0].strip()}
                    prop.add_custom_metadata(key, val)
                ogn_display_name = node_attr.get_metadata(ogn.MetadataKeys.UI_NAME)
                if ogn_display_name is not None:
                    prop.override_display_name(ogn_display_name)
                else:
                    is_bundle = node_attr.get_resolved_type().role == og.AttributeRole.BUNDLE
                    prop_name = node_attr.remove_port_type_from_name(prop.prop_name, is_bundle)
                    prop.override_display_name(prop_name)
        return all_props

    def _customize_props_layout(self, props: List[UsdPropertyUiEntry]) -> List[UsdPropertyUiEntry]:
        """Override base to reorder/regroup properties to build"""
        if not self.node:
            return props

        # apply metadata which we want available to templates and the default widget, also do an
        # initial filter of the prim attributes
        filtered_props = self._customize_props_metadata(props)

        template = self.load_template(props)
        if template is not None:
            return template

        parameter_attrs = []
        relationship_attrs = []
        reordered_attrs = []

        # Do a second pass to filter props for the non-template widget presentation
        for prop, attribute in filtered_props:
            if attribute.get_metadata("displayGroup") == "parameters":
                prop.override_display_group("Parameters")
                parameter_attrs.append(prop)
                continue

            if attribute.get_metadata(ogn.MetadataKeys.HIDDEN) is not None:
                continue

            if attribute.get_resolved_type().role == og.AttributeRole.EXECUTION:
                continue

            if attribute.get_metadata(ogn.MetadataKeys.OBJECT_ID) is not None:
                continue

            port_type = og.Attribute.get_port_type_from_name(prop.prop_name)
            match port_type:
                case og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT:
                    if prop.property_type == Usd.Relationship:
                        relationship_attrs.append(prop)
                    prop.override_display_group("Inputs")
                case og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT:
                    prop.override_display_group("Outputs")
                case og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE:
                    prop.override_display_group("State", collapsed=True)
                case _:
                    # Don't display attributes that aren't input/output/state
                    continue

            # This one looks good
            reordered_attrs.append(prop)

        # Move props to the desired order: parameters -> relationships -> everything else
        self.move_elements_to_beginning(relationship_attrs, reordered_attrs)
        self.move_elements_to_beginning(parameter_attrs, reordered_attrs)
        return reordered_attrs

    def width_changed_subscribe(self):
        self.window = ui.Workspace.get_window("Property")
        self.window_width_change = True
        if not self.window_width_change_fn_set:
            self.window.set_width_changed_fn(self.width_changed)
            self.window_width_change_fn_set = True

    def list_diff(self, list_a, list_b):
        return [i for i in list_a + list_b if i not in list_a or i not in list_b]

    def move_elements_to_beginning(self, elements_list, target_list):
        elements_list.reverse()
        for element in elements_list:
            with suppress(ValueError):
                target_list.remove(element)
        for element in elements_list:
            target_list.insert(0, element)

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        """Override of base - intercepts all attribute widget building"""
        with ui.HStack():
            # override prim paths to build if UsdPropertyUiEntry specifies one
            if ui_prop.prim_paths:
                prim_paths = ui_prop.prim_paths

            # Use supplied build_fn or our customized builder
            build_fn = ui_prop.build_fn if ui_prop.build_fn else OmniGraphPropertiesWidgetBuilder.build
            additional_label_kwargs, additional_widget_kwargs = self.get_additional_kwargs(ui_prop)

            # highlight filter text
            if self._filter.name:
                if additional_label_kwargs is None:
                    additional_label_kwargs = {}
                additional_label_kwargs["highlight"] = self._filter.name

            # Handle extended attributes
            if ui_prop.property_type is Usd.Attribute:
                attr_name = ui_prop.attr_name

                # Find a selected node that actually has this attribute in order to interrogate it
                node_with_attr = find_first_node_with_attrib(prim_paths, attr_name)
                if node_with_attr:
                    ogn_attr = node_with_attr.get_attribute(attr_name)

                    is_extended_attribute = ogn_attr.get_extended_type() in (
                        og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_ANY,
                        og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_UNION,
                    )

                    if is_extended_attribute:
                        resolved_type = ogn_attr.get_resolved_type()
                        if resolved_type.base_type == og.BaseDataType.UNKNOWN:
                            # This is an unresolved attribute
                            extended_type = (
                                "any"
                                if ogn_attr.get_extended_type() == og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_ANY
                                else "union"
                            )
                            ui_prop.metadata[
                                OmniGraphPropertiesWidgetBuilder.OVERRIDE_TYPENAME_KEY
                            ] = f"unresolved {extended_type}"
                            ui_prop.metadata[Sdf.PrimSpec.TypeNameKey] = "unknown"
                        else:
                            # Resolved attribute - swap in the resolved type to the ui_prop
                            sdf_type = og.AttributeType.sdf_type_name_from_type(resolved_type)
                            ui_prop.metadata[Sdf.PrimSpec.TypeNameKey] = sdf_type

            models = build_fn(
                stage,
                ui_prop.prop_name,
                ui_prop.metadata,
                ui_prop.property_type,
                prim_paths,
                additional_label_kwargs,
                additional_widget_kwargs,
            )
            if models:
                if not isinstance(models, list):
                    models = [models]
                for model in models:
                    for prim_path in prim_paths:
                        self._models[prim_path.AppendProperty(ui_prop.prop_name)].append(model)

    def get_bundles(self):
        if self.graph_context is None:
            return
        inputs_particles_rel = self.stage.GetRelationshipAtPath(self._payload[-1].pathString + ".inputs:particles")
        if inputs_particles_rel.IsValid():
            input_prims = inputs_particles_rel.GetTargets()
            for input_prim in input_prims:
                self.bundles[input_prim.GetParentPath().name + ".inputs:particles"] = (
                    self.graph_context.get_bundle(input_prim.pathString),
                    [],
                )
        self.bundles["outputs:particles"] = (
            self.graph_context.get_bundle(self._payload[-1].pathString + "/outputs_particles"),
            [],
        )

    def bundle_elements_layout_fn(self, **kwargs):
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            ui.Label(kwargs["name"], name="label", style={"alignment": ui.Alignment.RIGHT_TOP}, width=LABEL_WIDTH)
            ui.Spacer(width=HORIZONTAL_SPACING)
            model = ui.StringField(name="models_readonly", read_only=True, enabled=False).model
            self.bundles[kwargs["bundle_name"]][self.ATTRIB_LIST_INDEX].append(model)

    def display_bundles_content(self):
        self.get_bundles()
        self.bundle_update_sub = (
            omni.kit.app.get_app()
            .get_update_event_stream()
            .create_subscription_to_pop(self.on_bundles_update, name="bundles ui update")
        )
        self.stage_update_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop(self.on_stage_update, name="bundles ui stage update")
        )

        for bundle_name, bundle_value in self.bundles.items():
            names, _ = bundle_value[self.BUNDLE_INDEX].get_attribute_names_and_types()
            data_count = bundle_value[self.BUNDLE_INDEX].get_attribute_data_count()
            if data_count == 0:
                continue

            with CustomLayoutGroup(bundle_name, collapsed=True):
                for i in range(0, data_count):
                    attr_name = names[i]

                    def fn(*args, n=attr_name, b=bundle_name):
                        self.bundle_elements_layout_fn(name=n, bundle_name=b)

                    CustomLayoutProperty(None, None, build_fn=fn)

    def set_bundle_models_values(self):
        if self.graph_context is None:
            return
        for _bundle_name, bundle_value in self.bundles.items():
            if not bundle_value[1]:
                continue

            _, types = bundle_value[self.BUNDLE_INDEX].get_attribute_names_and_types()
            data = bundle_value[self.BUNDLE_INDEX].get_attribute_data()
            for i, d in enumerate(data):
                with suppress(Exception):
                    attr_type_name = types[i].get_type_name()
                    try:
                        elem_count = og.Controller.get_array_size(d)
                    except AttributeError:
                        elem_count = 1
                    bundle_value[self.ATTRIB_LIST_INDEX][i].set_value(
                        attr_type_name + " " + str(elem_count) + " elements"
                    )
                    bundle_value[self.ATTRIB_LIST_INDEX][i]._value_changed()  # noqa: PLW0212

    def on_bundles_update(self, event):
        self.time += event.payload["dt"]
        if self.time > 0.25:
            self.set_bundle_models_values()
            self.time = 0

    def on_stage_update(self, event):
        if event.type == int(omni.usd.StageEventType.CLOSING) and self.bundle_update_sub:
            self.bundle_update_sub = None  # unsubscribe from app update stream
