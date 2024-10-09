.. _omni_physx_forcefields_ForceFieldNoise_1:

.. _omni_physx_forcefields_ForceFieldNoise:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Force Field: Noise
    :keywords: lang-en omnigraph node forcefields force-field-noise


Force Field: Noise
==================

.. <description>

A force field that adds randomized motion to a rigid body.

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.forcefields<ext_omni_physx_forcefields>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "inputs:amplitude", "``vectorf[3]``", "The magnitude of the oscillations along each of the three local axes.", "[0.0, 0.0, 0.0]"
    "inputs:drag", "``float``", "The drag coefficient determines how quickly the body moves along with the noise. Smaller values cause the body to react more slowly.", "0.0"
    "inputs:enabled", "``bool``", "Enable or disable this ForceField. Overrides all other settings.", "True"
    "inputs:execution", "``execution``", "Connection to evaluate this node.", "0"
    "inputs:frequency", "``vectorf[3]``", "The frequency of the oscillations for each of the three local axes.", "[0.0, 0.0, 0.0]"
    "inputs:position", "``pointd[3]``", "The location of the force field.", "[0.0, 0.0, 0.0]"
    "inputs:primPaths", "``token[]``", "Apply forces to this list of Prims. Must be rigid bodies for the forces to have any effect.", "[]"
    "inputs:range", "``float[2]``", "Forces are not applied when the distance to the force field is outside of this (minimum, maximum) range. Each force field can have a different definition of distance, e.g. for a spherical fore field, the distance is to the center, for a plane, the distance is to the closest point on the surface, for a line, it is to the closest point on the line. The minimum or maximum range is ignored if the value is negative.", "[-1.0, -1.0]"
    "inputs:shape", "``token[]``", "Derive position input from this prim instead.", "[]"
    "inputs:surfaceAreaScaleEnabled", "``bool``", "Enable or disable scaling of forces by the surface area that faces in the direction of the applied force.", "True"
    "inputs:surfaceSampleDensity", "``float``", "Number of rays to cast per square unit of cross sectional area. When Surface Sample Density is disabled, by setting this value to 0, all forces act through the Center of Mass of the Rigid Body and no rotational torques will be applied. Any positive value will enable Surface Sampling. Ray casts are performed against the Collision Object of the Rigid Body in order to apply forces on the surface along the direction of the surface normal. This will apply torques on the Rigid Body that will induce rotation. Higher densities will cast more rays over the surface and spread the same force over the surface area. More ray casts will generate more accurate forces and torques, but will take additional compute time.", "0.0"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.forcefields.ForceFieldNoise"
    "Version", "1"
    "Extension", "omni.physx.forcefields"
    "Has State?", "False"
    "Implementation Language", "C++"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "tests, usd"
    "tags", "force,fields,noise,physx,simulation"
    "uiName", "Force Field: Noise"
    "Generated Class Name", "OgnForceFieldNoiseDatabase"
    "Python Module", "omni.physxforcefields"

