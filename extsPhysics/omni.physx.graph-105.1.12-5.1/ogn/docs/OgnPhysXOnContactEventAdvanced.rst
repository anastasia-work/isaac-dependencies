.. _omni_physx_graph_OnContactEventAdvanced_1:

.. _omni_physx_graph_OnContactEventAdvanced:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: On Contact Event, Advanced
    :keywords: lang-en omnigraph node PhysX Contacts threadsafe ReadOnly compute-on-request graph on-contact-event-advanced


On Contact Event, Advanced
==========================

.. <description>

PhysX contact event triggered execution.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Body Paths (*inputs:bodyPaths*)", "``token[]``", "Body prim paths to check against.", "None"
    "", "*literalOnly*", "1", ""
    "Body Prims (*inputs:targetBodies*)", "``target``", "Body prims to check against.", "None"
    "", "*literalOnly*", "1", ""
    "", "*allowMultiInputs*", "1", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Depths (*outputs:contactDepths*)", "``float[]``", "Contact point depths.", "None"
    "Impulses (*outputs:contactImpulses*)", "``vectorf[3][]``", "Contact point impulses.", "None"
    "Normals (*outputs:contactNormals*)", "``normalf[3][]``", "Contact point normals.", "None"
    "Points (*outputs:contactPoints*)", "``pointf[3][]``", "Contact point positions.", "None"
    "Contacting Body (*outputs:contactingBody*)", "``token``", "Path of the physics body that came in contact with a node input body to trigger the contact event.", "None"
    "Contacting Collider (*outputs:contactingCollider*)", "``token``", "Path to the collider of the contacting physics body.", "None"
    "Contacting Faces (*outputs:contactingFaces*)", "``int[]``", "Contact face indexes for the contacting collider.", "None"
    "Contacting Materials (*outputs:contactingMaterials*)", "``int[]``", "Contact material indexes for the contacting collider.", "None"
    "outputs:foundExecOut", "``execution``", "Output execution trigger for contact found events. Note that the node only evaluates and triggers for contact events where one of the bodies have the Contact Report API applied.", "None"
    "Input Body (*outputs:inputBody*)", "``token``", "Path of the node input physics body that triggered the contact event.", "None"
    "Input Body Collider (*outputs:inputBodyCollider*)", "``token``", "Path to the collider of the input body.", "None"
    "Input Body Faces (*outputs:inputBodyFaces*)", "``int[]``", "Contact face indexes for the input body collider.", "None"
    "Input Body Materials (*outputs:inputBodyMaterials*)", "``int[]``", "Contact material indexes for input body collider.", "None"
    "outputs:lostExecOut", "``execution``", "Output execution trigger for contact lost events. Note that the node only evaluates and triggers for contact events where one of the bodies have the Contact Report API applied.", "None"
    "outputs:persistsExecOut", "``execution``", "Output execution trigger for contact persists events. Note that the node only evaluates and triggers for contact events where one of the bodies have the Contact Report API applied.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.OnContactEventAdvanced"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "On Contact Event, Advanced"
    "__tokens", "{}"
    "Categories", "PhysX Contacts"
    "Generated Class Name", "OgnPhysXOnContactEventAdvancedDatabase"
    "Python Module", "omni.physxgraph"

