
# Release Notes

## Omni PhysX 1.0.0-5.1


- Changed:

   * PhysX SDK 5.1 is used
   * Update UsdPhysics and PhysxSchema to use default values
   * Physics menu Add was renamed to Create
   * Physics settings updated to new omni.ui
   * Update USD velocities is enabled by default
   * Interfaces renamed:
      carb::physics::usd::Physics.h --> omni::physx::PhysxUsd.h
      carb::physics::IPhysicsAuthoring.h --> omni::physx::IPhysicsAuthoring.h
      carb::physics::IPhysicsSimulation.h --> omni::physx::IPhysicsSimulation.h
      carb::physics::IPhysicsUsdLoad.h --> omni::physx::IPhysxUsdLoad.h
      carb::physics::physx.h --> omni::physx::IPhysx.h      
      carb::physics::physxInternal.h --> omni::physx::IPhysxCooking.h
      carb::physics::physxSceneQuery.h --> omni::physx::IPhysxSceneQuery.h
      carb::physics::physxSceneQueryHit.h --> omni::physx::IPhysxSceneQuery.h      

- Added:

   * Added IPhysicsSimulation
   * Physics cooked meshes local cache
   * Asynchronous mesh cooking
   * Cached getters for omni.physx interfaces
   * Physics demos can be now opened with a double click
   * Exposed rigid body transformation through an API, exposed to Python
   * Added overlap_box and overlap_sphere functions, exposed to Python though new PhysXSceneQuery interface, demos added.
   * Pvd IP settings and profile/debug/memory instrumentation checkbox
   * New Conical Force Field that emits force from the apex. Forces can fall off with angluar distance from the central axis.
   * Force Field OmniGraph nodes now have a shape input that sets other geometrical inputs automatically from the shape.

- Fixed:

   * Regression in USD notice handlers when an API was applied in runtime
   * Fixed traversal to support scene graph instancing

- Removed:

   * Raycast_closest and sweep_closest from physx interface, moved into PhysXSceneQuery interface

## Python Bindings API

- Added:

   * New PhysXSceneQuery interface. Overlap_sphere, overlap_box together with existing raycast_closest and sweep_closest (the query functions on PhysX interface were marked as deprecated).
   * New get_steering_sensitivity, set_steering_sensitivity, get_steering_filter_time, set_steering_filter_time interfaces to tune steering when using the gamepad, mouse or keyboard to control the vehicle.


## C++ API

- Changed:

   * The vehicle object ID parameter has been removed from getWheelIndex() as it is no longer needed.
   * New getSteeringSensitivity, setSteeringSensitivity, getSteeringFilterTime and setSteeringFilterTime interfaces to tune steering when using the gamepad, mouse or keyboard to control the vehicle.
