.. _omni_physx_graph_OnTriggerCollider_1:

.. _omni_physx_graph_OnTriggerCollider:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Trigger
    :keywords: lang-en omnigraph node PhysX Triggers compute-on-request graph on-trigger-collider


On Trigger
==========

.. <description>

Emits an event when a collider enters or leaves the volume of a Trigger.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Listen To All Triggers (*inputs:listenToAllTriggers*)", "``bool``", "If True the node will trigger whenever a trigger events happens, ignoring the list of provided paths in ""Triggers Relationships"" and ""Triggers Paths""", "None"
    "", "*literalOnly*", "1", ""
    "Triggers Paths (*inputs:triggersPaths*)", "``token[]``", "Specify one or more paths to Prims with applied TriggerAPI to monitor their trigger events", "None"
    "", "*literalOnly*", "1", ""
    "Triggers Relationships (*inputs:triggersRelationships*)", "``target``", "Specify one or more Prims with an applied TriggerAPI to monitor their trigger events", "None"
    "", "*literalOnly*", "1", ""
    "", "*allowMultiInputs*", "1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:enterExecOut", "``execution``", "Output execution when enter event is emitted", "None"
    "outputs:leaveExecOut", "``execution``", "Output execution when leave event is emitted", "None"
    "Other Body (*outputs:otherBody*)", "``token``", "Path of Body containing the Collider Prim that has entered the volume of the Collider Prim marked as trigger. It will not be updated if none of the two execution pins are wired.", "None"
    "Other Collider (*outputs:otherCollider*)", "``token``", "Path of the Collider Prim that has entered the volume of the Collider Prim marked as trigger. It will not be updated if none of the two execution pins are wired.", "None"
    "Trigger Body (*outputs:triggerBody*)", "``token``", "Path of Body containing Collider Prim that has emitted the trigger event. It will not be updated if none of the two execution pins are wired.", "None"
    "Trigger Collider (*outputs:triggerCollider*)", "``token``", "Path of Collider Prim containing the TriggerAPI that has emitted the trigger event. It will not be updated if none of the two execution pins are wired.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.OnTriggerCollider"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,trigger"
    "uiName", "On Trigger"
    "__tokens", "{}"
    "Categories", "PhysX Triggers"
    "Generated Class Name", "OgnPhysXOnTriggerColliderDatabase"
    "Python Module", "omni.physxgraph"

