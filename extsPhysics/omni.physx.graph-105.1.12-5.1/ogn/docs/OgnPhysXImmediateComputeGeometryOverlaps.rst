.. _omni_physx_graph_ImmediateComputeGeometryOverlaps_1:

.. _omni_physx_graph_ImmediateComputeGeometryOverlaps:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Compute Geometry Overlaps
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-compute-geometry-overlaps


Compute Geometry Overlaps
=========================

.. <description>

Compute overlaps between geometries (currently supports meshes prims)

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
    "inputs:overlapsPair0", "``token[]``", "Path of the first geometry from the Prims Bundle to check for overlap with corresponding item at same index in overlapsPair1 input attribute.", "[]"
    "inputs:overlapsPair1", "``token[]``", "Path of the second geometry from the Prims Bundle to check for overlap with corresponding item at same index in overlapsPair0 input attribute.", "[]"
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Currently only meshes prim are supported (sourcePrimType == 'Mesh'). Overlap check is always executed with trianagle mesh approximation for both items of a pair unless the (optional) 'physics:approximation' is set to different type (can be 'convex mesh' for example). From each Mesh prim child reads:  - 'sourecePrimPath'  - 'sourcePrimType'  - 'points'  - 'faceVertexIndices'  - 'faceVertexCounts'  - 'worldMatrix'  - 'sourcePrimPath' (and optionally 'holeIndices', 'orientation', 'meshKey' and 'physics:approximation') attributes", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlaps", "``bool[]``", "Array of booleans where 'True' value signals that a corresponding pair of meshes in overlapsPair0 and overlapsPair1 input arrays at the same index do actually overlap.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateComputeGeometryOverlaps"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,broadphase,bounding,immediate"
    "uiName", "Compute Geometry Overlaps"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateComputeGeometryOverlapsDatabase"
    "Python Module", "omni.physxgraph"

