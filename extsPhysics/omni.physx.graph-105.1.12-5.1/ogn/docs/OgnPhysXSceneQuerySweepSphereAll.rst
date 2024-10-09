.. _omni_physx_graph_SceneQuerySweepSphereAll_2:

.. _omni_physx_graph_SceneQuerySweepSphereAll:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Sweep, Sphere, All
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-sweep-sphere-all


Sweep, Sphere, All
==================

.. <description>

Returns a list of prim paths of all colliders that are hit by the input sweep.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Both Sides (*inputs:bothSides*)", "``bool``", "Sets whether backfaces of colliders should be included in checks.", "False"
    "Direction (*inputs:direction*)", "``['vectord[3]', 'vectorf[3]']``", "Ray direction vector", "None"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Origin (*inputs:origin*)", "``['pointd[3]', 'pointf[3]']``", "Ray origin", "None"
    "Radius (*inputs:radius*)", "``['double', 'float']``", "Sphere radius", "None"
    "Sort By Distance (*inputs:sortByDistance*)", "``bool``", "Enable to sort outputs by distance.", "False"
    "Distance (*inputs:sweepRange*)", "``['double', 'float']``", "Sweep distance. Use negative for infinite. If omitted, infinity is used.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Body Prim Paths (*outputs:bodyPrimPaths*)", "``token[]``", "A list of paths of the associated body prims for the collider prims that are hit by the input sweep.", "None"
    "Collider Prim Paths (*outputs:colliderPrimPaths*)", "``token[]``", "A list of paths of the collider prims that are hit by the input sweep.", "None"
    "Hit Distances (*outputs:distances*)", "``float[]``", "A list of distances from the origin to the points hit.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:faceIndexes", "``int[]``", "A list of the face indexes of the points hit.", "None"
    "outputs:materialPaths", "``token[]``", "A list of paths of the materials at the points hit.", "None"
    "outputs:normals", "``normalf[3][]``", "A list of surface normals of the points hit.", "None"
    "outputs:positions", "``pointf[3][]``", "A list of positions of the points hit.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQuerySweepSphereAll"
    "Version", "2"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Sweep, Sphere, All"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQuerySweepSphereAllDatabase"
    "Python Module", "omni.physxgraph"

