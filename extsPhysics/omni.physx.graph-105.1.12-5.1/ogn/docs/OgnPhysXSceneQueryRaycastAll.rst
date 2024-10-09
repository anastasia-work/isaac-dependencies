.. _omni_physx_graph_SceneQueryRaycastAll_1:

.. _omni_physx_graph_SceneQueryRaycastAll:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Raycast, All
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-raycast-all


Raycast, All
============

.. <description>

Returns a list of prim paths of all colliders that are hit by the input ray.

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
    "Direction (*inputs:direction*)", "``['vectord[3]', 'vectorf[3]']``", "Ray direction vector", "None"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Origin (*inputs:origin*)", "``['pointd[3]', 'pointf[3]']``", "Ray origin", "None"
    "Distance (*inputs:raycastRange*)", "``['double', 'float']``", "Raycast distance. Use negative for infinite. If omitted, infinity is used.", "None"
    "Sort by distance (*inputs:sortByDistance*)", "``bool``", "Enable to sort outputs by distance.", "False"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:bodyPrimPaths", "``token[]``", "A list of paths of the associated body prims for the collider prims that are hit by the input ray.", "None"
    "Collider Prim paths (*outputs:colliderPrimPaths*)", "``token[]``", "A list of paths of the collider prims that are hit by the input ray.", "None"
    "Hit distances (*outputs:distances*)", "``float[]``", "A list of distances from the origin to the points hit.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:faceIndexes", "``int[]``", "A list of the face indexes of the points hit.", "None"
    "outputs:materialPaths", "``token[]``", "A list of paths of the physics materials at the points hit.", "None"
    "outputs:normals", "``normalf[3][]``", "A list of surface normals of the points hit.", "None"
    "outputs:positions", "``pointf[3][]``", "A list of positions of the points hit.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryRaycastAll"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Raycast, All"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryRaycastAllDatabase"
    "Python Module", "omni.physxgraph"

