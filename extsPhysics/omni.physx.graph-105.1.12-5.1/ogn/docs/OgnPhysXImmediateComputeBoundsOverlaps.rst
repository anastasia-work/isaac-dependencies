.. _omni_physx_graph_ImmediateComputeBoundsOverlaps_1:

.. _omni_physx_graph_ImmediateComputeBoundsOverlaps:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Compute Bounds Overlaps
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-compute-bounds-overlaps


Compute Bounds Overlaps
=======================

.. <description>

Computes overlaps between pairs of axis aligned bounding boxes (broadphase)

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
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Connect with 'Compute Bounding Boxes' or with 'Read Prims' checking 'Compute bounding box'. For each child prim reads the:  - 'sourcePrimPath'  - 'bboxMinCorner'  - 'bboxMaxCorner' (and optionally 'bboxTransform' and 'worldMatrix') attributes.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlapsPair0", "``token[]``", "Array of tokens where the one at a given index is the first body in an identified overlap pair (the second is at corresponding index in 'overlapsPair1' output).", "None"
    "outputs:overlapsPair1", "``token[]``", "Array of tokens where the one at a given index is the second body in an identified overlap pair (the first is at corresponding index in 'overlapsPair0' output).", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateComputeBoundsOverlaps"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,broadphase,bounding,aabb,extents,bounds"
    "uiName", "Compute Bounds Overlaps"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateComputeBoundsOverlapsDatabase"
    "Python Module", "omni.physxgraph"

