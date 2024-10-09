.. _omni_physx_cct_OgnSpawnCapsule_1:

.. _omni_physx_cct_OgnSpawnCapsule:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Spawn Capsule
    :keywords: lang-en omnigraph node Physx Character Controller WriteOnly ReadWrite cct ogn-spawn-capsule


Spawn Capsule
=============

.. <description>

Spawn a Capsule prim with stage-defined up axis to be used with a Character Controller

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.cct<ext_omni_physx_cct>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Height (*inputs:capsuleHeight*)", "``float``", "Capsule Height", "100"
    "Position (*inputs:capsulePos*)", "``float[3]``", "Capsule Position", "[0, 0, 0]"
    "Radius (*inputs:capsuleRadius*)", "``float``", "Capsule Radius", "50"
    "inputs:spawn", "``execution``", "Spawn", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Done (*outputs:done*)", "``execution``", "Activated after the capsule is spawned", "None"
    "Path (*outputs:path*)", "``path``", "Path", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.cct.OgnSpawnCapsule"
    "Version", "1"
    "Extension", "omni.physx.cct"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "None"
    "uiName", "Spawn Capsule"
    "Categories", "Physx Character Controller"
    "Generated Class Name", "OgnSpawnCapsuleDatabase"
    "Python Module", "omni.physxcct"

