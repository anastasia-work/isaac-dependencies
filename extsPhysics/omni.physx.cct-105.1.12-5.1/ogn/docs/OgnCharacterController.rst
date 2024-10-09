.. _omni_physx_cct_OgnCharacterController_1:

.. _omni_physx_cct_OgnCharacterController:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Character Controller
    :keywords: lang-en omnigraph node Physx Character Controller WriteOnly ReadWrite cct ogn-character-controller


Character Controller
====================

.. <description>

Activate or deactivate a Character Controller on a Capsule prim

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.cct<ext_omni_physx_cct>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "inputs:activate", "``execution``", "Activate Character Controller on a Capsule. This can be done on e.g. Simulation Start Play event.", "None"
    "Capsule Path (*inputs:capsulePath*)", "``path``", "Connect a path of a capsule to use as a character controller. Use Spawn Capsule node to dynamically spawn a capsule for you if needed.", ""
    "inputs:controlsSettings", "``bundle``", "Use Controls Settings to rebind controls.", "None"
    "inputs:deactivate", "``execution``", "Deactivate Character Controller on a Capsule. This can be done on e.g. Simulation Stop Play event.", "None"
    "First Person Camera Path (*inputs:fpCameraPathToken*)", "``token``", "If a camera path is connected the character controller with use first person camera mode", "None"
    "Enable Gravity (*inputs:gravity*)", "``bool``", "Enable Gravity", "True"
    "Setup Controls (*inputs:setupControls*)", "``token``", "Setup controls: Auto will use default WASD/mouse/gamepad controls or Controls Settings keybinds if connected. Manual will skip control setup completely, leaving it to the user to do manually.", "Auto"
    "", "*allowedTokens*", "Auto,Manual", ""
    "Speed (*inputs:speed*)", "``int``", "Speed in units/s", "500"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Done (*outputs:done*)", "``execution``", "The output execution", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.cct.OgnCharacterController"
    "Version", "1"
    "Extension", "omni.physx.cct"
    "Has State?", "True"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "None"
    "uiName", "Character Controller"
    "Categories", "Physx Character Controller"
    "Generated Class Name", "OgnCharacterControllerDatabase"
    "Python Module", "omni.physxcct"

