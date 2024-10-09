import omni.ext
import omni.physx
from omni.physxcamera.bindings import _physxCamera
import omni.physxdemos as demo
from omni.physxui import PhysicsMenu

from .propertyWidgetManager import PropertyWidgetManager


DEMO_SCENES = "omni.physxcamera.scripts.samples"


class PhysxCameraExtension(omni.ext.IExt):
    def __init__(self):
        super().__init__()
        
    def on_startup(self):
        self._physxCameraInterface = _physxCamera.acquire_physx_camera_interface()        
        self._cameraPropertyWidgetManager = PropertyWidgetManager(self._physxCameraInterface)
        self._cameraPropertyWidgetManager.set_up()

        demo.register(DEMO_SCENES)

    def on_shutdown(self):
        if self._cameraPropertyWidgetManager is not None:
            self._cameraPropertyWidgetManager.tear_down()
            self._cameraPropertyWidgetManager = None

        if self._physxCameraInterface is not None:
            _physxCamera.release_physx_camera_interface(self._physxCameraInterface)
            _physxCamera.release_physx_camera_interface_scripting(self._physxCameraInterface) # OM-60917
            self._physxCameraInterface = None

        demo.unregister(DEMO_SCENES)
