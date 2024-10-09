.. _omni_physx_graph_SceneQueryOverlapPrimAny_1:

.. _omni_physx_graph_SceneQueryOverlapPrimAny:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Overlap, Prim, Any
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-overlap-prim-any


Overlap, Prim, Any
==================

.. <description>

Checks whether any colliders overlap the query input Prim.

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
    "Prim Path (*inputs:primPath*)", "``token``", "Prim path to check against. This must be a geometric type (UsdGeom)", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlap", "``bool``", "Returns true if any colliders overlap with the input Prim.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryOverlapPrimAny"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Overlap, Prim, Any"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryOverlapPrimAnyDatabase"
    "Python Module", "omni.physxgraph"

