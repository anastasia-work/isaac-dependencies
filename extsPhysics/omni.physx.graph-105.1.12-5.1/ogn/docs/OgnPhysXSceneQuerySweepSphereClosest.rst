.. _omni_physx_graph_SceneQuerySweepSphereClosest_1:

.. _omni_physx_graph_SceneQuerySweepSphereClosest:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Sweep, Sphere, Closest
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-sweep-sphere-closest


Sweep, Sphere, Closest
======================

.. <description>

Finds the closest collider that is hit by the input sweep.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Both sides (*inputs:bothSides*)", "``bool``", "Sets whether backfaces of colliders should be included in checks.", "False"
    "Direction (*inputs:direction*)", "``['vectord[3]', 'vectorf[3]']``", "Sweep direction vector", "None"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Origin (*inputs:origin*)", "``['pointd[3]', 'pointf[3]']``", "Sweep origin", "None"
    "Radius (*inputs:radius*)", "``['double', 'float']``", "Sphere radius", "None"
    "Distance (*inputs:sweepRange*)", "``['double', 'float']``", "Sweep maximum distance. Use negative for infinite. If omitted, infinity is used.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:bodyPrimPath", "``token``", "Path of the associated body prim of the closest collider prim hit by the sweep.", "None"
    "Collider Prim path (*outputs:colliderPrimPath*)", "``token``", "Path of the closest collider prim that is hit by the sweep.", "None"
    "Hit Distance (*outputs:distance*)", "``float``", "The distance from the origin to the point hit.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:faceIndex", "``int``", "The face index of the point hit.", "None"
    "outputs:hit", "``bool``", "Returns true if any colliders are hit by the sweep.", "None"
    "outputs:materialPath", "``token``", "Path of the material at the points hit.", "None"
    "outputs:normal", "``normalf[3]``", "The surface normal of the point hit.", "None"
    "outputs:position", "``pointf[3]``", "The position of the point hit.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQuerySweepSphereClosest"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Sweep, Sphere, Closest"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQuerySweepSphereClosestDatabase"
    "Python Module", "omni.physxgraph"

