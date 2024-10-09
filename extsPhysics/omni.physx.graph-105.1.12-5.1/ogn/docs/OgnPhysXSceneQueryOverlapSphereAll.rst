.. _omni_physx_graph_SceneQueryOverlapSphereAll_1:

.. _omni_physx_graph_SceneQueryOverlapSphereAll:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Overlap, Sphere, All
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-overlap-sphere-all


Overlap, Sphere, All
====================

.. <description>

Returns a list of prim paths of all colliders that overlap the input sphere.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "inputs:execIn", "``execution``", "Input execution", "None"
    "Position (*inputs:position*)", "``['pointd[3]', 'pointf[3]']``", "Sphere center position.", "None"
    "Radius (*inputs:radius*)", "``['double', 'float']``", "Sphere radius", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:bodyPrimPaths", "``token[]``", "A list of paths of the associated body prims for the collider prims that overlap the input sphere.", "None"
    "Collider Prim paths (*outputs:colliderPrimPaths*)", "``token[]``", "A list of paths of the collider prims that overlap the input sphere.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryOverlapSphereAll"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Overlap, Sphere, All"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryOverlapSphereAllDatabase"
    "Python Module", "omni.physxgraph"

