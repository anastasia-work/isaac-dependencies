"""Support for simplified access to data on nodes of type omni.physx.graph.VehicleGetDriveState

Retrieving drive related simulation state of an omni.physx vehicle
"""


import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class OgnVehicleGetDriveStateDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.physx.graph.VehicleGetDriveState

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.vehiclePath
        Outputs:
            outputs.accelerator
            outputs.automaticTransmission
            outputs.brake0
            outputs.brake1
            outputs.currentGear
            outputs.engineRotationSpeed
            outputs.steer
            outputs.targetGear
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
        ('inputs:vehiclePath', 'token', 0, 'Vehicle USD Path', 'The USD path of the vehicle prim to get the drive state for', {}, True, "", False, ''),
        ('outputs:accelerator', 'float', 0, 'Accelerator', 'The state of the accelerator pedal (in range [0, 1])', {}, True, None, False, ''),
        ('outputs:automaticTransmission', 'bool', 0, 'Automatic Transmission', 'The state of the automatic transmission', {}, True, None, False, ''),
        ('outputs:brake0', 'float', 0, 'Brake0', 'The state of the brake0 control (in range [0, 1])', {}, True, None, False, ''),
        ('outputs:brake1', 'float', 0, 'Brake1', 'The state of the brake1 control (in range [0, 1])', {}, True, None, False, ''),
        ('outputs:currentGear', 'int', 0, 'Current Gear', 'The current gear', {}, True, None, False, ''),
        ('outputs:engineRotationSpeed', 'float', 0, 'Engine Rotation Speed', 'The engine rotation speed in radians per second', {}, True, None, False, ''),
        ('outputs:steer', 'float', 0, 'Steer', 'The state of the steering wheel (in range [-1, 1])', {}, True, None, False, ''),
        ('outputs:targetGear', 'int', 0, 'Target Gear', 'The target gear', {}, True, None, False, ''),
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
        def vehiclePath(self):
            data_view = og.AttributeValueHelper(self._attributes.vehiclePath)
            return data_view.get()

        @vehiclePath.setter
        def vehiclePath(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.vehiclePath)
            data_view = og.AttributeValueHelper(self._attributes.vehiclePath)
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

        @property
        def accelerator(self):
            data_view = og.AttributeValueHelper(self._attributes.accelerator)
            return data_view.get()

        @accelerator.setter
        def accelerator(self, value):
            data_view = og.AttributeValueHelper(self._attributes.accelerator)
            data_view.set(value)

        @property
        def automaticTransmission(self):
            data_view = og.AttributeValueHelper(self._attributes.automaticTransmission)
            return data_view.get()

        @automaticTransmission.setter
        def automaticTransmission(self, value):
            data_view = og.AttributeValueHelper(self._attributes.automaticTransmission)
            data_view.set(value)

        @property
        def brake0(self):
            data_view = og.AttributeValueHelper(self._attributes.brake0)
            return data_view.get()

        @brake0.setter
        def brake0(self, value):
            data_view = og.AttributeValueHelper(self._attributes.brake0)
            data_view.set(value)

        @property
        def brake1(self):
            data_view = og.AttributeValueHelper(self._attributes.brake1)
            return data_view.get()

        @brake1.setter
        def brake1(self, value):
            data_view = og.AttributeValueHelper(self._attributes.brake1)
            data_view.set(value)

        @property
        def currentGear(self):
            data_view = og.AttributeValueHelper(self._attributes.currentGear)
            return data_view.get()

        @currentGear.setter
        def currentGear(self, value):
            data_view = og.AttributeValueHelper(self._attributes.currentGear)
            data_view.set(value)

        @property
        def engineRotationSpeed(self):
            data_view = og.AttributeValueHelper(self._attributes.engineRotationSpeed)
            return data_view.get()

        @engineRotationSpeed.setter
        def engineRotationSpeed(self, value):
            data_view = og.AttributeValueHelper(self._attributes.engineRotationSpeed)
            data_view.set(value)

        @property
        def steer(self):
            data_view = og.AttributeValueHelper(self._attributes.steer)
            return data_view.get()

        @steer.setter
        def steer(self, value):
            data_view = og.AttributeValueHelper(self._attributes.steer)
            data_view.set(value)

        @property
        def targetGear(self):
            data_view = og.AttributeValueHelper(self._attributes.targetGear)
            return data_view.get()

        @targetGear.setter
        def targetGear(self, value):
            data_view = og.AttributeValueHelper(self._attributes.targetGear)
            data_view.set(value)

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
        self.inputs = OgnVehicleGetDriveStateDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnVehicleGetDriveStateDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnVehicleGetDriveStateDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)
