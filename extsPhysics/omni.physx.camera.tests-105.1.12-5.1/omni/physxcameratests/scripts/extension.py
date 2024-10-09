import omni.ext
import omni.physxcameratests.scripts.tests as tests
from omni.physxtests import import_tests_auto

import_tests_auto("omni.physxcameratests.scripts", ["tests"])


class PhysxCameraTestsExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        self._physxCameraInterface = omni.physxcamera.get_physx_camera_interface()
        tests.setPhysxCameraInterface(self._physxCameraInterface)

        self._physxVehicleInterface = omni.physxvehicle.get_physx_vehicle_interface()
        tests.setPhysxVehicleInterface(self._physxVehicleInterface)

        self._physxInterface = omni.physx.get_physx_interface()
        tests.setPhysxInterface(self._physxInterface)

        self._physxSimInterface = omni.physx.get_physx_simulation_interface()
        tests.setPhysxSimInterface(self._physxSimInterface)

    def on_shutdown(self):
        tests.clearPhysxSimInterface()
        self._physxSimInterface = None

        tests.clearPhysxInterface()
        self._physxInterface = None

        tests.clearPhysxVehicleInterface()
        self._physxVehicleInterface = None

        tests.clearPhysxCameraInterface()
        self._physxCameraInterface = None

