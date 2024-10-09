.. _omni_physx_graph_ImmediateGenerateGeometryContacts_1:

.. _omni_physx_graph_ImmediateGenerateGeometryContacts:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Generate Geometry Contacts
    :keywords: lang-en omnigraph node PhysX Immediate Queries graph immediate-generate-geometry-contacts


Generate Geometry Contacts
==========================

.. <description>

Returns a list of contact points.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Contact Distance (*inputs:contactDistance*)", "``float``", "Contact Distance.", "0.01"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Mesh Contact Margin (*inputs:meshContactMargin*)", "``float``", "Mesh Contact Margin.", "0.01"
    "inputs:overlapsPair0", "``token[]``", "Path of the first geometry from the Prims Bundle to check for contactwith corresponding item at same index in overlapsPair1 input attribute.", "[]"
    "inputs:overlapsPair1", "``token[]``", "Path of the second geometry from the Prims Bundle to check for contactwith corresponding item at same index in overlapsPair0 input attribute", "[]"
    "inputs:primsBundle", "``bundle``", "The prims of interest. It must be a bundle with one or more prim children. Currently only meshes prim are supported (sourcePrimType == 'Mesh'). From each Mesh prim child reads:  - 'sourecePrimPath'  - 'sourcePrimType'  - 'points'  - 'faceVertexIndices'  - 'faceVertexCounts'  - 'worldMatrix'  - 'sourcePrimPath' (and optionally 'holeIndices', 'orientation', 'meshKey' and 'physics:approximation') attributes", "None"
    "Tolerance Length (*inputs:toleranceLength*)", "``float``", "Tolerance Length.", "0.1"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:contacts", "``bundle``", "Bundle of Child bundles containg contacts for each pair. Child Bundles are named prim0...primN that can be extracted with 'Extract Prim'. Each child bundle has 'points', 'normals' and 'depths' attributes. ", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.ImmediateGenerateGeometryContacts"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision,contacts"
    "uiName", "Generate Geometry Contacts"
    "__tokens", "{}"
    "Categories", "PhysX Immediate Queries"
    "Generated Class Name", "OgnPhysXImmediateGenerateGeometryContactsDatabase"
    "Python Module", "omni.physxgraph"

