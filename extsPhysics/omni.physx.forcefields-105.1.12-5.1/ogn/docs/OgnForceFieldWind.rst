.. _omni_physx_forcefields_ForceFieldWind_1:

.. _omni_physx_forcefields_ForceFieldWind:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Force Field: Wind
    :keywords: lang-en omnigraph node forcefields force-field-wind


Force Field: Wind
=================

.. <description>

A force field that simulates an unsteady wind that pushes rigid bodies.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.forcefields<ext_omni_physx_forcefields>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "inputs:averageDirection", "``normalf[3]``", "The initial direction of the wind in the world coordinate system. Wind direction \t\tchanges are added to this base direction.", "[0.0, 0.0, 0.0]"
    "inputs:averageSpeed", "``float``", "The average speed of the wind. Speed changes are added to this base speed, but \t\tthe net speed can never drop below zero.", "0.0"
    "inputs:directionVariation", "``normalf[3]``", "The magnitude of the random changes of the wind direction in the world coordinate system.", "[0.0, 0.0, 0.0]"
    "inputs:directionVariationFrequency", "``vectorf[3]``", "The frequency of the random variations of the wind direction in the world coordinate system.", "[0.0, 0.0, 0.0]"
    "inputs:drag", "``float``", "The drag coefficient determines how quickly the body moves along with the wind. \t\tSmaller values cause the body to react more slowly.", "0.0"
    "inputs:enabled", "``bool``", "Enable or disable this ForceField. Overrides all other settings.", "True"
    "inputs:execution", "``execution``", "Connection to evaluate this node.", "0"
    "inputs:position", "``pointd[3]``", "The location of the force field.", "[0.0, 0.0, 0.0]"
    "inputs:primPaths", "``token[]``", "Apply forces to this list of Prims. Must be rigid bodies for the forces to have any effect.", "[]"
    "inputs:range", "``float[2]``", "Forces are not applied when the distance to the force field is outside of this (minimum, maximum) range. Each force field can have a different definition of distance, e.g. for a spherical fore field, the distance is to the center, for a plane, the distance is to the closest point on the surface, for a line, it is to the closest point on the line. The minimum or maximum range is ignored if the value is negative.", "[-1.0, -1.0]"
    "inputs:shape", "``token[]``", "Derive the position input from this prim instead.", "[]"
    "inputs:speedVariation", "``float``", "The magnitude of the random changes of the wind speed.", "0.0"
    "inputs:speedVariationFrequency", "``float``", "The frequency of the random changes of the wind speed.", "0.0"
    "inputs:surfaceAreaScaleEnabled", "``bool``", "Enable or disable scaling of forces by the surface area that faces in the direction of the applied force.", "True"
    "inputs:surfaceSampleDensity", "``float``", "Number of rays to cast per square unit of cross sectional area. When Surface Sample Density is disabled, by setting this value to 0, all forces act through the Center of Mass of the Rigid Body and no rotational torques will be applied. Any positive value will enable Surface Sampling. Ray casts are performed against the Collision Object of the Rigid Body in order to apply forces on the surface along the direction of the surface normal. This will apply torques on the Rigid Body that will induce rotation. Higher densities will cast more rays over the surface and spread the same force over the surface area. More ray casts will generate more accurate forces and torques, but will take additional compute time.", "0.0"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.forcefields.ForceFieldWind"
    "Version", "1"
    "Extension", "omni.physx.forcefields"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests, usd"
    "tags", "force,fields,wind,physx,simulation"
    "uiName", "Force Field: Wind"
    "Generated Class Name", "OgnForceFieldWindDatabase"
    "Python Module", "omni.physxforcefields"

