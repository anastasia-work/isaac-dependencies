.. _omni_physx_graph_VehicleGetWheelState_1:

.. _omni_physx_graph_VehicleGetWheelState:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Get Wheel State
    :keywords: lang-en omnigraph node PhysX Scene Vehicles graph vehicle-get-wheel-state


Get Wheel State
===============

.. <description>

Retrieving wheel related simulation state of an omni.physx vehicle

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Wheel Attachment USD Paths (*inputs:vehicleWheelAttachmentPaths*)", "``token[]``", "The USD path of the vehicle prims to get the wheel state for", "[]"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Ground Contact State (*outputs:groundContactStates*)", "``bool[]``", "True if the wheel touches the ground, false if not", "None"
    "Ground Hit Positions (*outputs:groundHitPositions*)", "``float[3][]``", "The ground hit positions under the wheels stored in (x,y,z) format ", "None"
    "Ground Hit PhysX Actors (*outputs:groundPhysXActors*)", "``token[]``", "The physx actors under the wheels", "None"
    "Ground Hit PhysX Materials (*outputs:groundPhysXMaterials*)", "``token[]``", "The physx materials under the wheels", "None"
    "Ground Hit PhysX Shapes (*outputs:groundPhysXShapes*)", "``token[]``", "The physx shapes under the wheels", "None"
    "Wheel Ground Planes (*outputs:groundPlanes*)", "``float[4][]``", "The ground planes under the wheels stored in [nx,ny,nz,d] format ", "None"
    "Suspension Forces (*outputs:suspensionForces*)", "``float[3][]``", "The force developing on the suspensions", "None"
    "Suspension Jounces (*outputs:suspensionJounces*)", "``float[]``", "The jounce of the suspensions with zero meaning fully elongated", "None"
    "Tire Forces (*outputs:tireForces*)", "``float[3][]``", "The forces developing on the tires", "None"
    "Tire Friction Values (*outputs:tireFrictions*)", "``float[]``", "The friction values applied to the tires", "None"
    "Tire Lateral Directions (*outputs:tireLateralDirections*)", "``float[3][]``", "The lateral directions of the tires", "None"
    "Tire Lateral Slips (*outputs:tireLateralSlips*)", "``float[]``", "The tire lateral slips", "None"
    "Tire Longitudinal Directions (*outputs:tireLongitudinalDirections*)", "``float[3][]``", "The longitudinal directions of the tires", "None"
    "Tire Longitudinal Slips (*outputs:tireLongitudinalSlips*)", "``float[]``", "The tire longitudinal slips", "None"
    "Wheel Rotation Angles (*outputs:wheelRotationAngles*)", "``float[]``", "The wheel rotation angles in radians", "None"
    "Wheel Rotation Speeds (*outputs:wheelRotationSpeeds*)", "``float[]``", "The wheel rotation speeds in radians per second", "None"
    "Wheel Steer Angles (*outputs:wheelSteerAngles*)", "``float[]``", "The wheel steer angles in radians", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.VehicleGetWheelState"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests, usd"
    "tags", "physics"
    "uiName", "Get Wheel State"
    "Categories", "PhysX Scene Vehicles"
    "Generated Class Name", "OgnVehicleGetWheelStateDatabase"
    "Python Module", "omni.physxgraph"

