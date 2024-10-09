.. _omni_physx_graph_GenerateContacts_1:

.. _omni_physx_graph_GenerateContacts:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: (Deprecated) Generate Contacts
    :keywords: lang-en omnigraph node PhysX Contacts graph generate-contacts


(Deprecated) Generate Contacts
==============================

.. <description>

DEPRECATED - Use 'Generate Geometry Contacts'

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
    "Shape 0 (*inputs:shape0*)", "``token``", "Shape 0.", ""
    "Shape 1 (*inputs:shape1*)", "``token``", "Shape 1.", ""
    "Tolerance Length (*inputs:toleranceLength*)", "``float``", "Tolerance Length.", "0.1"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:contactCount", "``int``", "The number of contacts.", "None"
    "outputs:contactDepths", "``float[]``", "Contact depths.", "None"
    "outputs:contactNormals", "``normalf[3][]``", "Contact normals.", "None"
    "outputs:contactPoints", "``pointf[3][]``", "Contact positions.", "None"
    "outputs:execOut", "``execution``", "Output execution", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.GenerateContacts"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "hidden", "true"
    "tags", "physics,physx,simulation,collision"
    "uiName", "(Deprecated) Generate Contacts"
    "__tokens", "{}"
    "Categories", "PhysX Contacts"
    "Generated Class Name", "OgnPhysXGenerateContactsDatabase"
    "Python Module", "omni.physxgraph"

