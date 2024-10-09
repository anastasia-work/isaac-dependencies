"""Support for simplified access to data on nodes of type omni.physx.forcefields.ForceFieldSpherical

A spherical force field that attracts and/or repels rigid bodies from a central point depending on the function coefficients.
Positive values attract and negative values repel. The net force on the rigid body is calculated using f = constant + linear
* r + inverseSquare / r^2, where r is the distance to the center.
"""

import numpy

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnForceFieldSphericalDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.physx.forcefields.ForceFieldSpherical

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.constant
            inputs.enabled
            inputs.execution
            inputs.inverseSquare
            inputs.linear
            inputs.position
            inputs.primPaths
            inputs.range
            inputs.shape
            inputs.surfaceAreaScaleEnabled
            inputs.surfaceSampleDensity
    """

    # Imprint the generator and target ABI versions in the file for JIT generation
    GENERATOR_VERSION = (1, 41, 3)
    TARGET_VERSION = (2, 139, 8)

    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}

    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata,
    #     Is_Required, DefaultValue, Is_Deprecated, DeprecationMsg
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface([
        ('inputs:constant', 'float', 0, None, 'constant applies a steady force.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('inputs:enabled', 'bool', 0, None, 'Enable or disable this ForceField. Overrides all other settings.', {ogn.MetadataKeys.DEFAULT: 'true'}, True, True, False, ''),
        ('inputs:execution', 'execution', 0, None, 'Connection to evaluate this node.', {ogn.MetadataKeys.DEFAULT: '0'}, True, 0, False, ''),
        ('inputs:inverseSquare', 'float', 0, None, 'inverseSquare sets a force that varies with the reciprocal of the square of the distance to the center.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('inputs:linear', 'float', 0, None, 'linear sets a force that varies with distance to the center.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
        ('inputs:position', 'point3d', 0, None, 'The location of the force field.', {ogn.MetadataKeys.DEFAULT: '[0.0, 0.0, 0.0]'}, True, [0.0, 0.0, 0.0], False, ''),
        ('inputs:primPaths', 'token[]', 0, None, 'Apply forces to this list of Prims. Must be rigid bodies for the forces to have any effect.', {}, True, [], False, ''),
        ('inputs:range', 'float2', 0, None, 'Forces are not applied when the distance to the force field is outside\nof this (minimum, maximum) range. Each force field can have a different\ndefinition of distance, e.g. for a spherical fore field, the distance is\nto the center, for a plane, the distance is to the closest point on the\nsurface, for a line, it is to the closest point on the line. The minimum\nor maximum range is ignored if the value is negative.', {ogn.MetadataKeys.DEFAULT: '[-1.0, -1.0]'}, True, [-1.0, -1.0], False, ''),
        ('inputs:shape', 'token[]', 0, None, 'Derive position input from this prim instead.', {}, True, [], False, ''),
        ('inputs:surfaceAreaScaleEnabled', 'bool', 0, None, 'Enable or disable scaling of forces by the surface area that faces\nin the direction of the applied force.', {ogn.MetadataKeys.DEFAULT: 'true'}, True, True, False, ''),
        ('inputs:surfaceSampleDensity', 'float', 0, None, 'Number of rays to cast per square unit of cross sectional area.\nWhen Surface Sample Density is disabled, by setting this value to 0,\nall forces act through the Center of Mass of the Rigid Body and\nno rotational torques will be applied. Any positive value will\nenable Surface Sampling. Ray casts are performed against the\nCollision Object of the Rigid Body in order to apply forces on\nthe surface along the direction of the surface normal. This will\napply torques on the Rigid Body that will induce rotation. Higher\ndensities will cast more rays over the surface and spread the same\nforce over the surface area. More ray casts will generate more accurate\nforces and torques, but will take additional compute time.', {ogn.MetadataKeys.DEFAULT: '0.0'}, True, 0.0, False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.execution = og.AttributeRole.EXECUTION
        role_data.inputs.position = og.AttributeRole.POSITION
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = []
            self._batchedReadValues = []

        @property
        def constant(self):
            data_view = og.AttributeValueHelper(self._attributes.constant)
            return data_view.get()

        @constant.setter
        def constant(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.constant)
            data_view = og.AttributeValueHelper(self._attributes.constant)
            data_view.set(value)

        @property
        def enabled(self):
            data_view = og.AttributeValueHelper(self._attributes.enabled)
            return data_view.get()

        @enabled.setter
        def enabled(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.enabled)
            data_view = og.AttributeValueHelper(self._attributes.enabled)
            data_view.set(value)

        @property
        def execution(self):
            data_view = og.AttributeValueHelper(self._attributes.execution)
            return data_view.get()

        @execution.setter
        def execution(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.execution)
            data_view = og.AttributeValueHelper(self._attributes.execution)
            data_view.set(value)

        @property
        def inverseSquare(self):
            data_view = og.AttributeValueHelper(self._attributes.inverseSquare)
            return data_view.get()

        @inverseSquare.setter
        def inverseSquare(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.inverseSquare)
            data_view = og.AttributeValueHelper(self._attributes.inverseSquare)
            data_view.set(value)

        @property
        def linear(self):
            data_view = og.AttributeValueHelper(self._attributes.linear)
            return data_view.get()

        @linear.setter
        def linear(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.linear)
            data_view = og.AttributeValueHelper(self._attributes.linear)
            data_view.set(value)

        @property
        def position(self):
            data_view = og.AttributeValueHelper(self._attributes.position)
            return data_view.get()

        @position.setter
        def position(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.position)
            data_view = og.AttributeValueHelper(self._attributes.position)
            data_view.set(value)

        @property
        def primPaths(self):
            data_view = og.AttributeValueHelper(self._attributes.primPaths)
            return data_view.get()

        @primPaths.setter
        def primPaths(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.primPaths)
            data_view = og.AttributeValueHelper(self._attributes.primPaths)
            data_view.set(value)
            self.primPaths_size = data_view.get_array_size()

        @property
        def range(self):
            data_view = og.AttributeValueHelper(self._attributes.range)
            return data_view.get()

        @range.setter
        def range(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.range)
            data_view = og.AttributeValueHelper(self._attributes.range)
            data_view.set(value)

        @property
        def shape(self):
            data_view = og.AttributeValueHelper(self._attributes.shape)
            return data_view.get()

        @shape.setter
        def shape(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.shape)
            data_view = og.AttributeValueHelper(self._attributes.shape)
            data_view.set(value)
            self.shape_size = data_view.get_array_size()

        @property
        def surfaceAreaScaleEnabled(self):
            data_view = og.AttributeValueHelper(self._attributes.surfaceAreaScaleEnabled)
            return data_view.get()

        @surfaceAreaScaleEnabled.setter
        def surfaceAreaScaleEnabled(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.surfaceAreaScaleEnabled)
            data_view = og.AttributeValueHelper(self._attributes.surfaceAreaScaleEnabled)
            data_view.set(value)

        @property
        def surfaceSampleDensity(self):
            data_view = og.AttributeValueHelper(self._attributes.surfaceSampleDensity)
            return data_view.get()

        @surfaceSampleDensity.setter
        def surfaceSampleDensity(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.surfaceSampleDensity)
            data_view = og.AttributeValueHelper(self._attributes.surfaceSampleDensity)
            data_view.set(value)

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedWriteValues = { }

        def _commit(self):
            _og._commit_output_attributes_data(self._batchedWriteValues)
            self._batchedWriteValues = { }

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = OgnForceFieldSphericalDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnForceFieldSphericalDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnForceFieldSphericalDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)
