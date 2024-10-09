.. _omni_physx_graph_SceneQueryOverlapSphereAny_1:

.. _omni_physx_graph_SceneQueryOverlapSphereAny:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Overlap, Sphere, Any
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-overlap-sphere-any


Overlap, Sphere, Any
====================

.. <description>

Checks whether any colliders overlap the query input sphere.

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
    "Position (*inputs:position*)", "``['pointd[3]', 'pointf[3]']``", "Sphere center position.", "None"
    "Radius (*inputs:radius*)", "``['double', 'float']``", "Sphere radius", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlap", "``bool``", "Returns true if any colliders overlap with the input sphere.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryOverlapSphereAny"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Overlap, Sphere, Any"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryOverlapSphereAnyDatabase"
    "Python Module", "omni.physxgraph"

