# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import json
import weakref
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import carb
import carb.settings
import omni.graph.core as og
import omni.graph.tools.ogn as ogn
import omni.kit
from omni.kit.property.usd.control_state_manager import ControlStateManager
from omni.kit.property.usd.placeholder_attribute import PlaceholderAttribute
from pxr import Sdf, Usd


def get_ui_style():
    return carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"


def get_model_cls(cls, args, key="model_cls"):
    if args:
        return args.get(key, cls)
    return cls


AUTO_REFRESH_PERIOD = 0.33  # How frequently to poll for held node compute for refresh
BIG_ARRAY_MIN = 17  # The minimum number of elements to be considered a big-array
PLAY_COMPUTEGRAPH_SETTING = "/app/player/playComputegraph"
# =============================================================================


class PlaceholderOmniGraphAttribute:
    """Standin when a held Node does not have the given Attribute"""

    def __init__(self, name: str, node: str):
        self._name = name
        self._node = node


HELD_ATTRIB = Union[og.Attribute, PlaceholderOmniGraphAttribute]


# =============================================================================


class OmniGraphBase:
    """Mixin base for OmniGraph attribute models"""

    # Static refresh callback - shared among all instances
    _update_sub = None
    _update_counter: float = 0
    _instances = weakref.WeakSet()  # Set of all OmniGraphBase instances, for update polling
    _compute_counts: Dict[str, int] = {}  # Keep track of last compute count for each node by path.
    # FIXME: Would be nicer to have an Attribute.get_change_num() to know if it
    # has actually changed, rather than just if the node computed.

    @staticmethod
    def _on_update(event):
        """Called by kit update event - refreshes OG-based attribute models at a fixed interval."""
        # FIXME: In an action graph is probably more efficient to listen for a compute event instead of polling.
        # likewise in a push graph we should just refresh every N frames.
        OmniGraphBase._update_counter += event.payload["dt"]  # noqa: PLR1702
        if OmniGraphBase._update_counter > AUTO_REFRESH_PERIOD:  # noqa: PLR1702
            OmniGraphBase._update_counter = 0
            # If we find one of our nodes has computed since the last check we want to dirty all output and connected
            # inputs attribute bases
            dirty_nodes: Set[int] = set()
            dirty_bases: Set[OmniGraphBase] = set()

            for base in OmniGraphBase._instances:
                for attrib in base._get_og_attributes():  # noqa: PLW0212
                    if isinstance(attrib, og.Attribute):
                        port_type = attrib.get_port_type()
                        if (port_type == og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT) and (
                            attrib.get_upstream_connection_count() == 0
                        ):
                            # Special case - unconnected inputs don't ever have to be polled because they only
                            # change when set externally
                            continue
                        # Check if this attribute's node was computed since last update. If so mark it as dirty so
                        # that we don't have to do the check again in this pass.
                        node = attrib.get_node()
                        node_hash = hash(node)
                        want_dirty = node_hash in dirty_nodes
                        if not want_dirty:
                            node_path = node.get_prim_path()
                            cc = node.get_compute_count()
                            cached_cc = OmniGraphBase._compute_counts.get(node_path, -1)
                            if cached_cc != cc:
                                OmniGraphBase._compute_counts[node_path] = cc
                                dirty_nodes.add(node_hash)
                                want_dirty = True

                        if want_dirty and (base not in dirty_bases):
                            dirty_bases.add(base)

            for base in dirty_bases:
                base._set_dirty()  # noqa: PLW0212

    def __init__(
        self,
        stage: Usd.Stage,
        object_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict = None,
        change_on_edit_end=False,
        **kwargs,
    ):
        self._control_state_mgr = ControlStateManager.get_instance()
        self._stage = stage
        self._object_paths = object_paths
        self._object_paths_set = set(object_paths)
        self._metadata = metadata if metadata is not None else {}
        self._change_on_edit_end = change_on_edit_end
        self._dirty = True
        self._value = None  # The value to be displayed on widget
        self._has_default_value = False
        self._default_value = None
        self._real_values = []  # The actual values in usd, might be different from self._value if ambiguous.
        self._real_type: og.Type = None
        self._connections = []
        self._is_big_array = False
        self._prev_value = None
        self._prev_real_values = []
        self._editing = 0
        self._ignore_notice = False
        self._ambiguous = False
        self._comp_ambiguous = []
        self._might_be_time_varying = False  # Inaccurate named. It really means if timesamples > 0

        self._soft_range_min = None
        self._soft_range_max = None

        # get soft_range userdata settings
        # FIXME: We need an OG equivalent
        # attributes = self._get_attributes()
        # if attributes:
        #    attribute = attributes[-1]
        #    if isinstance(attribute, Usd.Attribute):
        #        soft_range = attribute.GetCustomDataByKey("omni:kit:property:usd:soft_range_ui")
        #        if soft_range:
        #            self._soft_range_min = soft_range[0]
        #            self._soft_range_max = soft_range[1]

        # Hard range for the value. For vector type, range value is a float/int that compares against each component
        self._min = kwargs.get("min", None)
        self._max = kwargs.get("max", None)

        # Override with node-specified
        # FIXME: minimum/maximum metadata isn't processed
        # for attrib in self._get_og_attributes():
        #    if isinstance(attrib, og.Attribute):
        #        self._max = attrib.get_metadata(ogn.MetaDataKeys.MAXIMUM)
        #        self._min = attrib.get_metadata(ogn.MetaDataKeys.MINIMUM)
        #        break

        # Invalid range
        if self._min is not None and self._max is not None and self._min >= self._max:
            self._min = self._max = None

        # The state of the icon on the right side of the line with widgets
        self._control_state = 0
        # Callback when the control state is changing. We use it to redraw UI
        self._on_control_state_changed_fn = None
        # Callback when the value is reset. We use it to redraw UI
        self._on_set_default_fn = None
        # True if the attribute has the default value and the current value is not default
        self._different_from_default: bool = False
        # Per component different from default
        self._comp_different_from_default: List[bool] = []

        # We want to keep updating when OG is evaluating
        self._last_compute_count = 0
        settings = carb.settings.get_settings()
        if settings.get(PLAY_COMPUTEGRAPH_SETTING):
            OmniGraphBase._instances.add(self)
            if len(OmniGraphBase._instances) == 1 and (OmniGraphBase._update_sub is None):
                OmniGraphBase._update_sub = (
                    omni.kit.app.get_app()
                    .get_update_event_stream()
                    .create_subscription_to_pop(OmniGraphBase._on_update, name="OG prop-panel ui update")
                )

    def is_editing(self) -> bool:
        # This method can be called when uiType == filePath
        return self._editing

    @property
    def control_state(self):
        """Returns the current control state, it's the icon on the right side of the line with widgets"""
        return self._control_state

    @property
    def stage(self):
        return self._stage

    @property
    def metadata(self):
        return self._metadata

    def update_control_state(self):
        control_state, force_refresh = self._control_state_mgr.update_control_state(self)

        # Redraw control state icon when the control state is changed
        if self._control_state != control_state or force_refresh:
            self._control_state = control_state
            if self._on_control_state_changed_fn:
                self._on_control_state_changed_fn()

    def set_on_control_state_changed_fn(self, fn):
        """Callback that is called when control state is changed"""
        self._on_control_state_changed_fn = fn

    def set_on_set_default_fn(self, fn):
        """Callback that is called when value is reset"""
        self._on_set_default_fn = fn

    def clean(self):
        self._stage = None
        OmniGraphBase._instances.discard(self)
        if not OmniGraphBase._instances:
            OmniGraphBase._update_sub = None  # unsubscribe from app update stream
            OmniGraphBase._compute_counts.clear()

    @carb.profiler.profile
    def _get_default_value(self, attrib: HELD_ATTRIB) -> Tuple[bool, Any]:
        if isinstance(attrib, og.Attribute):
            default_str = attrib.get_metadata(ogn.MetadataKeys.DEFAULT)
            og_tp = attrib.get_resolved_type()
            if default_str is not None:
                py_val = json.loads(default_str)
                val = og.python_value_as_usd(og_tp, py_val)
                return True, val

            # If we still don't find default value, use type's default value
            val_base = 0
            if og_tp.array_depth > 0:
                # Special case string, path vs uchar[]
                if (og_tp.base_type == og.BaseDataType.UCHAR) and (
                    og_tp.role in [og.AttributeRole.TEXT, og.AttributeRole.PATH]
                ):
                    val_base = ""
                else:
                    return True, []
            elif og_tp.base_type == og.BaseDataType.BOOL:
                val_base = False
            elif og_tp.base_type == og.BaseDataType.TOKEN:
                val_base = ""

            py_val = val_base
            if og_tp.tuple_count > 1:
                if og_tp.role in [og.AttributeRole.FRAME, og.AttributeRole.MATRIX, og.AttributeRole.TRANSFORM]:
                    dim = 2 if og_tp.tuple_count == 4 else 3 if og_tp.tuple_count == 9 else 4
                    py_val = [[1 if i == j else 0 for j in range(dim)] for i in range(dim)]
                else:
                    py_val = [val_base] * og_tp.tuple_count

            val = og.python_value_as_usd(og_tp, py_val)
            return True, val

        return False, None

    def is_different_from_default(self):
        """Returns True if the attribute has the default value and the current value is not default"""
        self._update_value()
        # soft_range has been overridden
        if self._soft_range_min is not None and self._soft_range_max is not None:
            return True
        return self._different_from_default

    def might_be_time_varying(self):
        self._update_value()
        return self._might_be_time_varying

    def is_ambiguous(self):
        self._update_value()
        return self._ambiguous

    def is_comp_ambiguous(self, index: int):
        self._update_value()
        comp_len = len(self._comp_ambiguous)
        if comp_len == 0 or index < 0:
            return self.is_ambiguous()
        if index < comp_len:
            return self._comp_ambiguous[index]
        return False

    def get_value_by_comp(self, comp: int):
        self._update_value()
        if comp == -1:
            return self._value

        return self._get_value_by_comp(self._value, comp)

    def _save_real_values_as_prev(self):
        # It's like copy.deepcopy but not all USD types support pickling (e.g. Gf.Quat*)
        self._prev_real_values = [type(value)(value) for value in self._real_values]

    def _get_value_by_comp(self, value, comp: int):
        if value.__class__.__module__ == "pxr.Gf":
            if value.__class__.__name__.startswith("Quat"):
                if comp == 0:
                    return value.real
                return value.imaginary[comp - 1]
            if value.__class__.__name__.startswith("Matrix"):
                dimension = len(value)
                row = comp // dimension
                col = comp % dimension  # noqa: S001
                return value[row, col]
            if value.__class__.__name__.startswith("Vec") and comp < len(value):
                return value[comp]
        elif comp < len(value):
            return value[comp]
        return None

    def _update_value_by_comp(self, value, comp: int):
        if self._value.__class__.__module__ == "pxr.Gf":
            if self._value.__class__.__name__.startswith("Quat"):
                if comp == 0:
                    value.real = self._value.real
                else:
                    imaginary = self._value.imaginary
                    imaginary[comp - 1] = self._value.imaginary[comp - 1]
                    value.SetImaginary(imaginary)
            elif self._value.__class__.__name__.startswith("Matrix"):
                dimension = len(self._value)
                row = comp // dimension
                col = comp % dimension  # noqa: S001
                value[row, col] = self._value[row, col]
            elif self._value.__class__.__name__.startswith("Vec"):
                value[comp] = self._value[comp]
        else:
            value[comp] = self._value[comp]
        return value

    def _compare_value_by_comp(self, val1, val2, comp: int):
        return self._get_value_by_comp(val1, comp) == self._get_value_by_comp(val2, comp)

    def _get_comp_num(self):
        """Returns the number of components in the value type"""
        if self._real_type:
            # For OG scalers have tuple_count == 1, but here we expect 0
            return self._real_type.tuple_count if self._real_type.tuple_count > 1 else 0
        return 0

    def _on_dirty(self):
        pass

    def _set_dirty(self):
        if self._editing > 0:
            return

        self._dirty = True
        self._on_dirty()

    def _get_type_name(self, obj: Usd.Object):
        if hasattr(obj, "GetTypeName"):
            return obj.GetTypeName()
        if hasattr(obj, "typeName"):
            return obj.typeName
        return None

    def _is_array_type(self, obj: HELD_ATTRIB):
        if isinstance(obj, og.Attribute):
            attr_type = obj.get_resolved_type()
            is_array_type = attr_type.array_depth > 0 and attr_type.role not in [
                og.AttributeRole.TEXT,
                og.AttributeRole.PATH,
            ]
            return is_array_type
        return False

    def _get_resolved_attribute_path(self, attribute: og.Attribute) -> str:
        """Return the path to the given attribute, considering resolved extended attributes"""
        return f"{attribute.get_node().get_prim_path()}.{og.Attribute.resolved_prefix}{attribute.get_name()}"

    def get_attribute_paths(self) -> List[Sdf.Path]:
        return self._object_paths

    def get_property_paths(self) -> List[Sdf.Path]:
        return self.get_attribute_paths()

    def get_connections(self):
        return self._connections

    def set_default(self, comp=-1):
        """Set the og.Attribute default value if it exists in metadata"""
        # FIXME
        # self.set_soft_range_userdata(None, None)
        if self.is_different_from_default() is False or self._has_default_value is False:
            if self._soft_range_min is not None and self._soft_range_max is not None:
                if self._on_set_default_fn:
                    self._on_set_default_fn()
                self.update_control_state()
            return

        with omni.kit.undo.group():
            for attribute in self._get_og_attributes():
                if isinstance(attribute, og.Attribute):
                    current_value = self._read_value(attribute)
                    if comp >= 0:
                        default_value = current_value
                        default_value[comp] = self._default_value[comp]
                    else:
                        default_value = self._default_value

                    self._change_property(attribute, default_value, current_value)

        # We just set all the properties to the same value, it's no longer ambiguous
        self._ambiguous = False
        self._comp_ambiguous.clear()

        self._different_from_default = False
        self._comp_different_from_default.clear()

        if self._on_set_default_fn:
            self._on_set_default_fn()

    def set_value(self, value, comp=-1) -> bool:
        if not self._stage:
            return False

        if self._min is not None:
            if hasattr(value, "__len__"):
                for i in range(len(value)):  # noqa: PLC0200
                    if value[i] < self._min:
                        value[i] = self._min
            else:
                if value < self._min:
                    value = self._min

        if self._max is not None:
            if hasattr(value, "__len__"):
                for i in range(len(value)):  # noqa: PLC0200
                    if value[i] > self._max:
                        value[i] = self._max
            else:
                if value > self._max:
                    value = self._max

        if not self._ambiguous and not any(self._comp_ambiguous) and (value == self._value):
            return False

        if self.is_locked():
            carb.log_warn("Setting locked attribute is not supported yet")
            self._update_value(True)  # reset value
            return False

        if self._might_be_time_varying:
            carb.log_warn("Setting time varying attribute is not supported yet")
            self._update_value(True)  # reset value
            return False

        self._value = value
        attributes = self._get_og_attributes()

        if len(attributes) == 0:
            return False

        # FIXME: Here we normally harden placeholders into real attributes. For OG we don't do that.
        # This is because all OG attributes are 'real', IE there are no attributes inherited from a 'type' that
        # are un-instantiated. However there could be real (dynamic) USD attributes for which there are no
        # OG attributes. In that case we want to allow editing of those values...
        # self._create_placeholder_attributes(attributes)

        if self._editing:
            for i, attribute in enumerate(attributes):
                set_value = False
                self._ignore_notice = True
                if comp == -1:
                    self._real_values[i] = self._value
                    if not self._change_on_edit_end:
                        set_value = True
                else:
                    # Only update a single component of the value (for vector type)
                    value = self._real_values[i]
                    self._real_values[i] = self._update_value_by_comp(value, comp)
                    if not self._change_on_edit_end:
                        set_value = True

                if set_value:
                    # Directly set the value on the attribute, not through a command.
                    # FIXME: Due to the TfNotice issue - we use USD API here.
                    is_extended_attr = (
                        attribute.get_extended_type() != og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_REGULAR
                    )
                    usd_attr = self._stage.GetAttributeAtPath(attribute.get_path())
                    if is_extended_attr:
                        # But the resolved attrib is not in USD, so we need to set the value using OG, but then
                        # trigger a tfnotice so that the system will know that the attrib has changed
                        og.Controller.set(attribute, value)
                        # The USD attrib is actually a token, so the hack here is to change the token value
                        # so that the node will get the onValueChanged callback. FIXME: Obviously not ideal
                        # to be tokenizing the value
                        usd_attr.Set(str(value))
                    else:
                        usd_attr.Set(self._value)
                self._ignore_notice = False
        else:
            with omni.kit.undo.group():
                for i, attribute in enumerate(attributes):
                    self._ignore_notice = True

                    # begin_edit is not called for certain widget (like Checkbox), issue the command directly
                    if comp == -1:
                        self._change_property(attribute, self._value, None)
                    else:
                        # Only update a single component of the value (for vector type)
                        value = self._real_values[i]
                        self._real_values[i] = self._update_value_by_comp(value, comp)
                        self._change_property(attribute, value, None)
                    self._ignore_notice = False

        if comp == -1:
            # We just set all the properties to the same value, it's no longer ambiguous
            self._ambiguous = False
            self._comp_ambiguous.clear()
        else:
            self._comp_ambiguous[comp] = False
            self._ambiguous = any(self._comp_ambiguous)

        if self._has_default_value:
            self._comp_different_from_default = [False] * self._get_comp_num()
            if comp == -1:
                self._different_from_default = value != self._default_value
                if self._different_from_default:
                    for comp_non_default in range(len(self._comp_different_from_default)):  # noqa: PLC0200
                        self._comp_different_from_default[comp_non_default] = not self._compare_value_by_comp(
                            value, self._default_value, comp_non_default
                        )
            else:
                self._comp_different_from_default[comp] = not self._compare_value_by_comp(
                    value, self._default_value, comp
                )
                self._different_from_default = any(self._comp_different_from_default)
        else:
            self._different_from_default = False
            self._comp_different_from_default.clear()

        self.update_control_state()

        return True

    def _is_prev_same(self):
        return self._prev_real_values == self._real_values

    def begin_edit(self):
        self._editing = self._editing + 1
        self._prev_value = self._value
        self._save_real_values_as_prev()

    def end_edit(self):
        self._editing = self._editing - 1

        if self._is_prev_same():
            return

        attributes = self._get_og_attributes()

        omni.kit.undo.begin_group()
        self._ignore_notice = True
        for i, attribute in enumerate(attributes):
            self._change_property(attribute, self._real_values[i], self._prev_real_values[i])
        self._ignore_notice = False
        omni.kit.undo.end_group()

        # Set flags. It calls _on_control_state_changed_fn when the user finished editing
        self._update_value(True)

    def _change_property(self, attribute: og.Attribute, new_value, old_value):
        """Change the given attribute via a command"""
        path = Sdf.Path(attribute.get_path())
        # Set the value on the attribute, called to "commit" the value
        # FIXME: Due to the TfNotice issue - we use USD API here.
        is_extended_attr = attribute.get_extended_type() != og.ExtendedAttributeType.EXTENDED_ATTR_TYPE_REGULAR
        if is_extended_attr:
            # But the resolved attrib is not in USD, so we need to set the value using OG, but then
            # trigger a tfnotice so that the system will know that the attrib has changed
            og.Controller.set(attribute, new_value)
            # The USD attrib is actually a token, so the hack here is to change the token value
            # so that the node will get the onValueChanged callback. FIXME: Obviously not ideal
            # to be tokenizing the value + Undo doesn't work
            omni.kit.commands.execute("ChangeProperty", prop_path=path, value=str(new_value), prev=str(old_value))
        else:
            # FIXME: The UI widgets seem to rely on USD notices (eg color control), so we must set values through
            # USD until we can refactor things to not require the notices.
            omni.kit.commands.execute("ChangeProperty", prop_path=path, value=new_value, prev=old_value)

    def get_value(self):
        self._update_value()
        return self._value

    def get_current_time_code(self):
        # FIXME: Why are we being asked this
        return Usd.TimeCode.Default()

    def _update_value(self, force=False):
        """Pull the current value of the attributes into this object"""
        return self._update_value_objects(force, self._get_og_attributes())

    def _update_value_objects(self, force: bool, objects: List[HELD_ATTRIB]):
        if (self._dirty or force) and self._stage:  # noqa: PLR1702
            carb.profiler.begin(1, "OmniGraphBase._update_value_objects")
            self._might_be_time_varying = False
            self._value = None
            self._has_default_value = False
            self._default_value = None
            self._real_values.clear()
            self._real_type = None
            self._connections.clear()
            self._ambiguous = False
            self._comp_ambiguous.clear()
            self._different_from_default = False
            self._comp_different_from_default.clear()
            for index, attr_object in enumerate(objects):
                value, tp = self._read_value_and_type(attr_object)
                if value is None:
                    continue
                self._real_values.append(value)
                self._real_type = tp
                #
                if isinstance(attr_object, og.Attribute):
                    # FIXME: Can OG attributes be 'time varying'?
                    # self._might_be_time_varying = self._might_be_time_varying or attr_object.GetNumTimeSamples() > 0
                    self._connections.append(
                        [
                            Sdf.Path(conn.get_node().get_prim_path()).AppendProperty(conn.get_name())
                            for conn in attr_object.get_upstream_connections()
                        ]
                    )
                #  only need to check the first prim. All other prims attributes are ostensibly the same
                if index == 0:
                    self._value = value
                    if (
                        (self._value is not None)
                        and self._is_array_type(attr_object)
                        and len(self._value) >= BIG_ARRAY_MIN
                    ):
                        self._is_big_array = True
                    comp_num = self._get_comp_num()
                    self._comp_ambiguous = [False] * comp_num
                    self._comp_different_from_default = [False] * comp_num
                    # Loads the default value
                    self._has_default_value, self._default_value = self._get_default_value(attr_object)
                elif self._value != value:
                    self._value = value
                    self._ambiguous = True
                    comp_num = len(self._comp_ambiguous)
                    if comp_num > 0:
                        for i in range(comp_num):
                            if not self._comp_ambiguous[i]:
                                self._comp_ambiguous[i] = not self._compare_value_by_comp(
                                    value, self._real_values[0], i
                                )

                if self._has_default_value:
                    comp_num = len(self._comp_different_from_default)
                    if comp_num > 0 and (not self._is_array_type(attr_object)):
                        for i in range(comp_num):
                            if not self._comp_different_from_default[i]:
                                self._comp_different_from_default[i] = not self._compare_value_by_comp(
                                    value, self._default_value, i
                                )
                        self._different_from_default |= any(self._comp_different_from_default)
                    elif not self._is_array_type(attr_object) or value or self._default_value:
                        # empty arrays may compare unequal
                        self._different_from_default |= value != self._default_value

            self._dirty = False
            self.update_control_state()
            carb.profiler.end(1)
            return True
        return False

    def _get_attributes(self):
        """
        Gets the list of managed USD Attributes
        NOTE: Only returns attributes for which there are corresponding OG Attributes
        """
        attributes = []
        if not self._stage:
            return attributes

        for path in self._object_paths:
            prim = self._stage.GetPrimAtPath(path.GetPrimPath())
            if prim:
                attr = prim.GetAttribute(path.name)
                if attr:
                    # Hidden attributes don't get placeholders
                    if not attr.IsHidden():
                        try:
                            _ = og.Controller.attribute(path.pathString)
                        except og.OmniGraphError:
                            # No corresponding OG Attribute
                            pass
                        else:
                            attributes.append(attr)
                else:
                    attr = PlaceholderAttribute(name=path.name, prim=prim, metadata=self._metadata)
                    attributes.append(attr)
        return attributes

    def _get_og_attributes(self) -> List[HELD_ATTRIB]:
        """Returns the held attributes object wrappers"""
        attributes = []
        for path in self._object_paths:
            attrib = None
            try:
                attrib = og.Controller.attribute(path.pathString)
                attributes.append(attrib)
            except og.OmniGraphError:
                # Invalid attribute for whatever reason, put in a placeholder
                pass
            if not attrib:
                attributes.append(PlaceholderOmniGraphAttribute(path.name, path.GetPrimPath().pathString))
        return attributes

    @carb.profiler.profile
    def _read_value_and_type(self, attr_object: HELD_ATTRIB) -> Tuple[Any, Optional[og.Type]]:
        """Reads the value and type of the given object
        Args:
            attr_object The object to be read
        Returns:
            The value
            The og.Type if the value is read from OG
        """
        val = None
        if not isinstance(attr_object, PlaceholderOmniGraphAttribute):
            # The ui expects USD attr_objects, so we must convert data
            # here.
            # FIXME: Could optimize by wrapping numpy in compatible shim classes
            #
            try:
                if attr_object.is_valid():
                    og_val = og.Controller(attr_object).get()
                    og_tp = attr_object.get_resolved_type()
                    # Truncate big arrays to limit copying between numpy/USD types
                    val = og.attribute_value_as_usd(og_tp, og_val, BIG_ARRAY_MIN)
                    return (val, og_tp)
            except og.OmniGraphError:
                carb.log_warn(f"Failed to read {attr_object.get_path()}")
        return (val, None)

    def _read_value(self, attr_object: HELD_ATTRIB):
        """Returns the current USD value of the given attribute object"""
        val, _ = self._read_value_and_type(attr_object)
        return val

    def set_locked(self, locked):
        pass

    def is_locked(self):
        return False

    def has_connections(self):
        return self._connections[-1]
