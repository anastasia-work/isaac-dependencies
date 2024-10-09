.. _omni_physx_graph_VehicleGetDriveState_1:

.. _omni_physx_graph_VehicleGetDriveState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Get Vehicle Drive State
    :keywords: lang-en omnigraph node PhysX Scene Vehicles graph vehicle-get-drive-state


Get Vehicle Drive State
=======================

.. <description>

Retrieving drive related simulation state of an omni.physx vehicle

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Vehicle USD Path (*inputs:vehiclePath*)", "``token``", "The USD path of the vehicle prim to get the drive state for", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Accelerator (*outputs:accelerator*)", "``float``", "The state of the accelerator pedal (in range [0, 1])", "None"
    "Automatic Transmission (*outputs:automaticTransmission*)", "``bool``", "The state of the automatic transmission", "None"
    "Brake0 (*outputs:brake0*)", "``float``", "The state of the brake0 control (in range [0, 1])", "None"
    "Brake1 (*outputs:brake1*)", "``float``", "The state of the brake1 control (in range [0, 1])", "None"
    "Current Gear (*outputs:currentGear*)", "``int``", "The current gear", "None"
    "Engine Rotation Speed (*outputs:engineRotationSpeed*)", "``float``", "The engine rotation speed in radians per second", "None"
    "Steer (*outputs:steer*)", "``float``", "The state of the steering wheel (in range [-1, 1])", "None"
    "Target Gear (*outputs:targetGear*)", "``int``", "The target gear", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.VehicleGetDriveState"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests, usd"
    "tags", "physics"
    "uiName", "Get Vehicle Drive State"
    "Categories", "PhysX Scene Vehicles"
    "Generated Class Name", "OgnVehicleGetDriveStateDatabase"
    "Python Module", "omni.physxgraph"

