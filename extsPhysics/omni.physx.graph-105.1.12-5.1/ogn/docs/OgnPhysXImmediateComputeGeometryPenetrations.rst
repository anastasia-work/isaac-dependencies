.. _omni_physx_graph_ImmediateComputeGeometryPenetrations_1:

.. _omni_physx_graph_ImmediateComputeGeometryPenetrations:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Compute Geometry Penetrations
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-compute-geometry-penetrations


Compute Geometry Penetrations
=============================

.. <description>

Compute penetration depth and direction between geometries (currently supports meshes prims)

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
    "inputs:overlapsPair0", "``token[]``", "Path of the first geometry from the Prims Bundle to check for penetration with corresponding item at same index in overlapsPair1 input attribute.", "[]"
    "inputs:overlapsPair1", "``token[]``", "Path of the second geometry from the Prims Bundle to check for penetration with corresponding item at same index in overlapsPair0 input attribute", "[]"
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Currently only meshes prim are supported (sourcePrimType == 'Mesh'). Penetration vectors are not computed when both sides of a pair use triangle mesh approximation. Penetration computation only works if the (optional) 'physics:approximation' of one of the two overlap pair to check is not 'triangle mesh' (can be 'convex mesh'). From each Mesh prim child reads:  - 'sourecePrimPath'  - 'sourcePrimType'  - 'points'  - 'faceVertexIndices'  - 'faceVertexCounts'  - 'worldMatrix'  - 'sourcePrimPath' (and optionally 'holeIndices', 'orientation', 'meshKey' and 'physics:approximation') attributes", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlaps", "``bool[]``", "Array of booleans where 'True' value signals that a corresponding pair of meshes in overlapsPair0 and overlapsPair1 input arrays at the same index do actually overlap.", "None"
    "outputs:penetrationDepths", "``float[]``", "Array of penetration depths values of the corresponding pair of meshes in overlapsPair0 and overlapsPair1 input arrays at the same index.", "None"
    "outputs:penetrationVectors", "``normalf[3][]``", "Array of penetration normals of the corresponding pair of meshes in overlapsPair0 and overlapsPair1 input arrays at the same index.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateComputeGeometryPenetrations"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,broadphase,bounding,immediate"
    "uiName", "Compute Geometry Penetrations"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateComputeGeometryPenetrationsDatabase"
    "Python Module", "omni.physxgraph"

