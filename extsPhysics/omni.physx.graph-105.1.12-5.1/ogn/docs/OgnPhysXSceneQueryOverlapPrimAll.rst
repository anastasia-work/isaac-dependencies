.. _omni_physx_graph_SceneQueryOverlapPrimAll_1:

.. _omni_physx_graph_SceneQueryOverlapPrimAll:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Overlap, Prim, All
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-overlap-prim-all


Overlap, Prim, All
==================

.. <description>

Returns a list of prim paths of all colliders that overlap the input Prim.

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
    "Prim Path (*inputs:primPath*)", "``token``", "Prim path to check against. This must be a geometric type (UsdGeom).", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:bodyPrimPaths", "``token[]``", "A list of paths of the associated body prims for the collider prims that overlap the input Prim.", "None"
    "Collider Prim paths (*outputs:colliderPrimPaths*)", "``token[]``", "A list of paths of the collider prims that overlap the input Prim.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryOverlapPrimAll"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Overlap, Prim, All"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryOverlapPrimAllDatabase"
    "Python Module", "omni.physxgraph"

