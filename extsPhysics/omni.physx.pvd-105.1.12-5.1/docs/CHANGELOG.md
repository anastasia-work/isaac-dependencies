# Changelog
omni.physx.pvd Changelog

## 1.6.0-5.1 - 2023-05-15

**General**

- Added an OVD file import option from the main Composer menu
- Added compatibility with newest PhysX SDK exported OVD files with derived class support
- Added Initial multi-scene support
- Added the ability to record OVD files from the OmniPvd extension
- Changed the OmniPvd interface by dividing the import section into loading and recording of OVD files
- Added option to set the OVD import directory
- Fixed that the OVD import directory is updated when Omni Physics records an OVD file
- Fixed several selection tracking issues with the USD Stage and the OmniPvd Object Tree, now persist over time
- Fixed showstopper selection issues for large scenes when not an OVD scene
- Added that OVD recording is not possible to toggle while physics simulation is running or the scene is an OVD scene
- Updated gizmos to work with the new OVD derived class support
- Added that the OmniPvd Object Tree is set to focused on OVD file load
- Streamlined the UI for loading OVD files produced by either PhysX SDK unit and visual tests as well as Omni Physics Debug sessions
- Fixed various crash bugs


## 1.5.0-5.1 - 2022-05-??

**General**

- Changed return parameter of the OVD to USD converted ovdToUsd to bool
- Changed return parameter of the PhysX baking ovdToUsdOver to bool
- Added unit test for the ovdToUSD function
- Added in visualization Gizmos for OmniPVD
  - For now has bounding boxes and contact points
  - Added in selection of Prims affecting the Gizmos
  - Drop down menue selections are : None, Selected, All
- Added deduplication of OVD attributes
- Adds a new omni.pvd namespace for the attributes
- Various OVD to USD conversion fixes
- Property order depends on creation order

## Omni PhysX Preview 1.4.0-5.1 - 2021-11-???

**General**

- Renamed PhysXPvd interface to IPhysxPvd
- Renamed PhysXPvd::binToStage to IPhysxPvd::ovdToUsd
- Removed PhysXPvd::message
- Added option to export to USD
- Extended the capabilities of the automatic OmniPvd attribute to USD attribute conversions
- Changed to using the actors OmniPvd Attribute Set in the scene OmniPvd class to update the lifetime of PxActors
- Added initial PhysX reduced coordinate articulations import
- Added baking of PhysX transforms, changing the simulation into an animation, allowing to scrub through it
- UI streamlining
    - Mirroring of the recorded OVD file into the OmniPvd transformation tab
    - Increasing integers names for directories instead of date stamps
    - Console success message
    - Button alignment

## 1.4.0 - 2021-11-05

**General**

- Initial version
    - Record PhysX simulations in Kit into OmniPvd (.OVD) format.
        - Enabled using the "OmniPvd Enabled" check button in the PVD section of the Physics Debug window
    - Transform an OmniPvd recording (.OVD) into an OmniPvd USDA format time series
        - Choice of input (.OVD) file
        - Choice of up axis
        - Choice of USD/USDA (not yet functional, only USDA output)
    - Transform a single snapshot frame of an OmniPvd USDA stage into a Physics USDA stage
    - Allows for inspection of hierarchies and transforms
        - Scene/(Rigid dynamic or Rigid static)/Actor(s)/Shape(s)/Geometries
        - Separate referencable layer containing triangular meshes, convexes, heightfields and shared PhysX shapes
        - Time series of Actor and Shape transforms    