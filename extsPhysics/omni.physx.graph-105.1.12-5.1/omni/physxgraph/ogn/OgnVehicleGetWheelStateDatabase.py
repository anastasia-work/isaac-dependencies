"""Support for simplified access to data on nodes of type omni.physx.graph.VehicleGetWheelState

Retrieving wheel related simulation state of an omni.physx vehicle
"""

import numpy

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnVehicleGetWheelStateDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.physx.graph.VehicleGetWheelState

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.vehicleWheelAttachmentPaths
        Outputs:
            outputs.groundContactStates
            outputs.groundHitPositions
            outputs.groundPhysXActors
            outputs.groundPhysXMaterials
            outputs.groundPhysXShapes
            outputs.groundPlanes
            outputs.suspensionForces
            outputs.suspensionJounces
            outputs.tireForces
            outputs.tireFrictions
            outputs.tireLateralDirections
            outputs.tireLateralSlips
            outputs.tireLongitudinalDirections
            outputs.tireLongitudinalSlips
            outputs.wheelRotationAngles
            outputs.wheelRotationSpeeds
            outputs.wheelSteerAngles
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
        ('inputs:vehicleWheelAttachmentPaths', 'token[]', 0, 'Wheel Attachment USD Paths', 'The USD path of the vehicle prims to get the wheel state for', {}, True, [], False, ''),
        ('outputs:groundContactStates', 'bool[]', 0, 'Ground Contact State', 'True if the wheel touches the ground, false if not', {}, True, None, False, ''),
        ('outputs:groundHitPositions', 'float3[]', 0, 'Ground Hit Positions', 'The ground hit positions under the wheels stored in (x,y,z) format ', {}, True, None, False, ''),
        ('outputs:groundPhysXActors', 'token[]', 0, 'Ground Hit PhysX Actors', 'The physx actors under the wheels', {}, True, None, False, ''),
        ('outputs:groundPhysXMaterials', 'token[]', 0, 'Ground Hit PhysX Materials', 'The physx materials under the wheels', {}, True, None, False, ''),
        ('outputs:groundPhysXShapes', 'token[]', 0, 'Ground Hit PhysX Shapes', 'The physx shapes under the wheels', {}, True, None, False, ''),
        ('outputs:groundPlanes', 'float4[]', 0, 'Wheel Ground Planes', 'The ground planes under the wheels stored in [nx,ny,nz,d] format ', {}, True, None, False, ''),
        ('outputs:suspensionForces', 'float3[]', 0, 'Suspension Forces', 'The force developing on the suspensions', {}, True, None, False, ''),
        ('outputs:suspensionJounces', 'float[]', 0, 'Suspension Jounces', 'The jounce of the suspensions with zero meaning fully elongated', {}, True, None, False, ''),
        ('outputs:tireForces', 'float3[]', 0, 'Tire Forces', 'The forces developing on the tires', {}, True, None, False, ''),
        ('outputs:tireFrictions', 'float[]', 0, 'Tire Friction Values', 'The friction values applied to the tires', {}, True, None, False, ''),
        ('outputs:tireLateralDirections', 'float3[]', 0, 'Tire Lateral Directions', 'The lateral directions of the tires', {}, True, None, False, ''),
        ('outputs:tireLateralSlips', 'float[]', 0, 'Tire Lateral Slips', 'The tire lateral slips', {}, True, None, False, ''),
        ('outputs:tireLongitudinalDirections', 'float3[]', 0, 'Tire Longitudinal Directions', 'The longitudinal directions of the tires', {}, True, None, False, ''),
        ('outputs:tireLongitudinalSlips', 'float[]', 0, 'Tire Longitudinal Slips', 'The tire longitudinal slips', {}, True, None, False, ''),
        ('outputs:wheelRotationAngles', 'float[]', 0, 'Wheel Rotation Angles', 'The wheel rotation angles in radians', {}, True, None, False, ''),
        ('outputs:wheelRotationSpeeds', 'float[]', 0, 'Wheel Rotation Speeds', 'The wheel rotation speeds in radians per second', {}, True, None, False, ''),
        ('outputs:wheelSteerAngles', 'float[]', 0, 'Wheel Steer Angles', 'The wheel steer angles in radians', {}, True, None, False, ''),
    ])

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
        def vehicleWheelAttachmentPaths(self):
            data_view = og.AttributeValueHelper(self._attributes.vehicleWheelAttachmentPaths)
            return data_view.get()

        @vehicleWheelAttachmentPaths.setter
        def vehicleWheelAttachmentPaths(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.vehicleWheelAttachmentPaths)
            data_view = og.AttributeValueHelper(self._attributes.vehicleWheelAttachmentPaths)
            data_view.set(value)
            self.vehicleWheelAttachmentPaths_size = data_view.get_array_size()

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
            self.groundContactStates_size = None
            self.groundHitPositions_size = None
            self.groundPhysXActors_size = None
            self.groundPhysXMaterials_size = None
            self.groundPhysXShapes_size = None
            self.groundPlanes_size = None
            self.suspensionForces_size = None
            self.suspensionJounces_size = None
            self.tireForces_size = None
            self.tireFrictions_size = None
            self.tireLateralDirections_size = None
            self.tireLateralSlips_size = None
            self.tireLongitudinalDirections_size = None
            self.tireLongitudinalSlips_size = None
            self.wheelRotationAngles_size = None
            self.wheelRotationSpeeds_size = None
            self.wheelSteerAngles_size = None
            self._batchedWriteValues = { }

        @property
        def groundContactStates(self):
            data_view = og.AttributeValueHelper(self._attributes.groundContactStates)
            return data_view.get(reserved_element_count=self.groundContactStates_size)

        @groundContactStates.setter
        def groundContactStates(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundContactStates)
            data_view.set(value)
            self.groundContactStates_size = data_view.get_array_size()

        @property
        def groundHitPositions(self):
            data_view = og.AttributeValueHelper(self._attributes.groundHitPositions)
            return data_view.get(reserved_element_count=self.groundHitPositions_size)

        @groundHitPositions.setter
        def groundHitPositions(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundHitPositions)
            data_view.set(value)
            self.groundHitPositions_size = data_view.get_array_size()

        @property
        def groundPhysXActors(self):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXActors)
            return data_view.get(reserved_element_count=self.groundPhysXActors_size)

        @groundPhysXActors.setter
        def groundPhysXActors(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXActors)
            data_view.set(value)
            self.groundPhysXActors_size = data_view.get_array_size()

        @property
        def groundPhysXMaterials(self):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXMaterials)
            return data_view.get(reserved_element_count=self.groundPhysXMaterials_size)

        @groundPhysXMaterials.setter
        def groundPhysXMaterials(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXMaterials)
            data_view.set(value)
            self.groundPhysXMaterials_size = data_view.get_array_size()

        @property
        def groundPhysXShapes(self):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXShapes)
            return data_view.get(reserved_element_count=self.groundPhysXShapes_size)

        @groundPhysXShapes.setter
        def groundPhysXShapes(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundPhysXShapes)
            data_view.set(value)
            self.groundPhysXShapes_size = data_view.get_array_size()

        @property
        def groundPlanes(self):
            data_view = og.AttributeValueHelper(self._attributes.groundPlanes)
            return data_view.get(reserved_element_count=self.groundPlanes_size)

        @groundPlanes.setter
        def groundPlanes(self, value):
            data_view = og.AttributeValueHelper(self._attributes.groundPlanes)
            data_view.set(value)
            self.groundPlanes_size = data_view.get_array_size()

        @property
        def suspensionForces(self):
            data_view = og.AttributeValueHelper(self._attributes.suspensionForces)
            return data_view.get(reserved_element_count=self.suspensionForces_size)

        @suspensionForces.setter
        def suspensionForces(self, value):
            data_view = og.AttributeValueHelper(self._attributes.suspensionForces)
            data_view.set(value)
            self.suspensionForces_size = data_view.get_array_size()

        @property
        def suspensionJounces(self):
            data_view = og.AttributeValueHelper(self._attributes.suspensionJounces)
            return data_view.get(reserved_element_count=self.suspensionJounces_size)

        @suspensionJounces.setter
        def suspensionJounces(self, value):
            data_view = og.AttributeValueHelper(self._attributes.suspensionJounces)
            data_view.set(value)
            self.suspensionJounces_size = data_view.get_array_size()

        @property
        def tireForces(self):
            data_view = og.AttributeValueHelper(self._attributes.tireForces)
            return data_view.get(reserved_element_count=self.tireForces_size)

        @tireForces.setter
        def tireForces(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireForces)
            data_view.set(value)
            self.tireForces_size = data_view.get_array_size()

        @property
        def tireFrictions(self):
            data_view = og.AttributeValueHelper(self._attributes.tireFrictions)
            return data_view.get(reserved_element_count=self.tireFrictions_size)

        @tireFrictions.setter
        def tireFrictions(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireFrictions)
            data_view.set(value)
            self.tireFrictions_size = data_view.get_array_size()

        @property
        def tireLateralDirections(self):
            data_view = og.AttributeValueHelper(self._attributes.tireLateralDirections)
            return data_view.get(reserved_element_count=self.tireLateralDirections_size)

        @tireLateralDirections.setter
        def tireLateralDirections(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireLateralDirections)
            data_view.set(value)
            self.tireLateralDirections_size = data_view.get_array_size()

        @property
        def tireLateralSlips(self):
            data_view = og.AttributeValueHelper(self._attributes.tireLateralSlips)
            return data_view.get(reserved_element_count=self.tireLateralSlips_size)

        @tireLateralSlips.setter
        def tireLateralSlips(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireLateralSlips)
            data_view.set(value)
            self.tireLateralSlips_size = data_view.get_array_size()

        @property
        def tireLongitudinalDirections(self):
            data_view = og.AttributeValueHelper(self._attributes.tireLongitudinalDirections)
            return data_view.get(reserved_element_count=self.tireLongitudinalDirections_size)

        @tireLongitudinalDirections.setter
        def tireLongitudinalDirections(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireLongitudinalDirections)
            data_view.set(value)
            self.tireLongitudinalDirections_size = data_view.get_array_size()

        @property
        def tireLongitudinalSlips(self):
            data_view = og.AttributeValueHelper(self._attributes.tireLongitudinalSlips)
            return data_view.get(reserved_element_count=self.tireLongitudinalSlips_size)

        @tireLongitudinalSlips.setter
        def tireLongitudinalSlips(self, value):
            data_view = og.AttributeValueHelper(self._attributes.tireLongitudinalSlips)
            data_view.set(value)
            self.tireLongitudinalSlips_size = data_view.get_array_size()

        @property
        def wheelRotationAngles(self):
            data_view = og.AttributeValueHelper(self._attributes.wheelRotationAngles)
            return data_view.get(reserved_element_count=self.wheelRotationAngles_size)

        @wheelRotationAngles.setter
        def wheelRotationAngles(self, value):
            data_view = og.AttributeValueHelper(self._attributes.wheelRotationAngles)
            data_view.set(value)
            self.wheelRotationAngles_size = data_view.get_array_size()

        @property
        def wheelRotationSpeeds(self):
            data_view = og.AttributeValueHelper(self._attributes.wheelRotationSpeeds)
            return data_view.get(reserved_element_count=self.wheelRotationSpeeds_size)

        @wheelRotationSpeeds.setter
        def wheelRotationSpeeds(self, value):
            data_view = og.AttributeValueHelper(self._attributes.wheelRotationSpeeds)
            data_view.set(value)
            self.wheelRotationSpeeds_size = data_view.get_array_size()

        @property
        def wheelSteerAngles(self):
            data_view = og.AttributeValueHelper(self._attributes.wheelSteerAngles)
            return data_view.get(reserved_element_count=self.wheelSteerAngles_size)

        @wheelSteerAngles.setter
        def wheelSteerAngles(self, value):
            data_view = og.AttributeValueHelper(self._attributes.wheelSteerAngles)
            data_view.set(value)
            self.wheelSteerAngles_size = data_view.get_array_size()

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
        self.inputs = OgnVehicleGetWheelStateDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnVehicleGetWheelStateDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnVehicleGetWheelStateDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)
