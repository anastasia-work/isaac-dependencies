.. _omni_physx_graph_SceneQueryOverlapBoxAny_1:

.. _omni_physx_graph_SceneQueryOverlapBoxAny:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Overlap, Box, Any
    :keywords: lang-en omnigraph node PhysX Scene Queries graph scene-query-overlap-box-any


Overlap, Box, Any
=================

.. <description>

Checks whether any colliders overlap the query input box.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.graph<ext_omni_physx_graph>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Dimensions (*inputs:dimensions*)", "``['double[3]', 'float[3]']``", "Box dimensions", "None"
    "inputs:execIn", "``execution``", "Input execution", "None"
    "Position (*inputs:position*)", "``['pointd[3]', 'pointf[3]']``", "Box center position.", "None"
    "Rotation (*inputs:rotation*)", "``['double[3]', 'float[3]']``", "Box rotation in XYZ order Euler angles", "None"


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:execOut", "``execution``", "Output execution", "None"
    "outputs:overlap", "``bool``", "Returns true if any colliders overlap with the input box.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.graph.SceneQueryOverlapBoxAny"
    "Version", "1"
    "Extension", "omni.physx.graph"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "python, tests"
    "tags", "physics,physx,simulation,collision"
    "uiName", "Overlap, Box, Any"
    "__tokens", "{}"
    "Categories", "PhysX Scene Queries"
    "Generated Class Name", "OgnPhysXSceneQueryOverlapBoxAnyDatabase"
    "Python Module", "omni.physxgraph"

