.. _omni_physx_graph_ImmediateComputeMeshIntersectingFaces_1:

.. _omni_physx_graph_ImmediateComputeMeshIntersectingFaces:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Compute Mesh Intersecting Faces
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-compute-mesh-intersecting-faces


Compute Mesh Intersecting Faces
===============================

.. <description>

Computes indices of intersecting faces between pairs of Meshes.

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
    "inputs:overlapsPair0", "``token[]``", "Path of the first geometry from the Prims Bundle to check for intesection with corresponding item at same index in overlapsPair1 input attribute.", "[]"
    "inputs:overlapsPair1", "``token[]``", "Path of the second geometry from the Prims Bundle to check for intesection with corresponding item at same index in overlapsPair0 input attribute", "[]"
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Currently only meshes prim are supported (sourcePrimType == 'Mesh'). From each Mesh prim child reads:  - 'sourcePrimPath'  - 'sourcePrimType'  - 'points'  - 'faceVertexIndices'  - 'faceVertexCounts'  - 'worldMatrix'  - 'sourcePrimPath' (and optionally 'holeIndices', 'orientation', 'meshKey' and 'physics:approximation') attributes", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:faceIndices", "``bundle``", "Bundle of child prims with faces0 / faces1 attributes containing indices of faces in source meshes that intersect each other", "None"
    "outputs:overlaps", "``bool[]``", "Array of booleans where 'True' value signals that a corresponding pair of meshes in overlapsPair0 and overlapsPair1 input arrays at the same index do actually overlap.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateComputeMeshIntersectingFaces"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,faces,intersection,immediate"
    "uiName", "Compute Mesh Intersecting Faces"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateComputeMeshIntersectingFacesDatabase"
    "Python Module", "omni.physxgraph"

