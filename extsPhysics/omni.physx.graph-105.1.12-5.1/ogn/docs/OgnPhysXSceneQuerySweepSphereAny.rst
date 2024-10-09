.. _omni_physx_graph_SceneQuerySweepSphereAny_1:

.. _omni_physx_graph_SceneQuerySweepSphereAny:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Sweep, Sphere, Any
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-sweep-sphere-any


Sweep, Sphere, Any
==================

.. <description>

Returns whether any colliders are hit by the input sweep.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Both Sides (*inputs:bothSides*)", "``bool``", "Sets whether backfaces of colliders should be included in checks.", "False"
    "Direction (*inputs:direction*)", "``['vectord[3]', 'vectorf[3]']``", "Sweep direction vector", "None"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Origin (*inputs:origin*)", "``['pointd[3]', 'pointf[3]']``", "Sweep origin", "None"
    "Radius (*inputs:radius*)", "``['double', 'float']``", "Sphere radius", "None"
    "Distance (*inputs:sweepRange*)", "``['double', 'float']``", "Sweep distance. Use negative for infinite. If omitted, infinity is used.", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:hit", "``bool``", "Returns true if any colliders are hit by the input sweep.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQuerySweepSphereAny"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Sweep, Sphere, Any"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQuerySweepSphereAnyDatabase"
    "Python Module", "omni.physxgraph"

