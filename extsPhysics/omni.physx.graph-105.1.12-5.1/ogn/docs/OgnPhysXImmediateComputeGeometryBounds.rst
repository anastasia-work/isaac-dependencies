.. _omni_physx_graph_ImmediateComputeGeometryBounds_1:

.. _omni_physx_graph_ImmediateComputeGeometryBounds:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Compute Geometry Bounds
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-compute-geometry-bounds


Compute Geometry Bounds
=======================

.. <description>

Computes bounding boxes for the input geometries (and cache cooking for future intersection tests)

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
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Currently only meshes prim are supported (sourcePrimType == 'Mesh'). From each Mesh prim child reads:  - 'sourecePrimPath'  - 'sourcePrimType'  - 'points'  - 'faceVertexIndices'  - 'faceVertexCounts'  - 'worldMatrix' and (optionally) 'meshHash', 'physics:approximation'", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:primsBundle", "``bundle``", "The same bundle passed as input with the following attributes added:  - bboxMaxCorner  - bboxMinCorner  - meshHash", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateComputeGeometryBounds"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,immediate"
    "uiName", "Compute Geometry Bounds"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateComputeGeometryBoundsDatabase"
    "Python Module", "omni.physxgraph"

