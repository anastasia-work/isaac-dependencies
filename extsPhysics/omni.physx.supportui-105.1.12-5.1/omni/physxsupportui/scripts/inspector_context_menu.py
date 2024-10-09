import omni.ui as ui
import omni.kit.app
from pxr import Sdf
from pxr import UsdPhysics
import omni.physxsupportui.bindings._physxSupportUi as pxsupportui
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModel


class InspectorContextMenuHandler():
    def __init__(self):
        self._ui_context_menu = None

    def clean(self):
        self._ui_context_menu = None

    def build_context_menu(self, tree_view_selection, model_inspector : PhysXInspectorModel):
        num_joints = 0
        num_bodies = 0
        stage = omni.usd.get_context().get_stage()
        for item in tree_view_selection:
            usd_path = model_inspector.get_item_value_model(item, 1).as_string
            if not Sdf.Path.IsValidPathString(usd_path):
                continue
            prim = stage.GetPrimAtPath(usd_path)
            if prim:
                if prim.IsA(UsdPhysics.Joint):
                    num_joints = num_joints + 1
                elif prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.HasAPI(UsdPhysics.CollisionAPI):
                    num_bodies = num_bodies + 1
                if num_joints > 0 and num_bodies > 0:
                    break
        if num_joints == 0 and num_bodies == 0:
            return
        if self._ui_context_menu == None:
            self._ui_context_menu = ui.Menu("Context menu")

        self._ui_context_menu.clear()
        with self._ui_context_menu:
            if model_inspector.get_inspector_type() == pxsupportui.PhysXInspectorModelInspectorType.INSPECTOR_TYPE_JOINTS_LIST:
                ui.MenuItem("Select all connected joint colliders", triggered_fn=model_inspector.select_all_connected_joint_shapes)
                ui.MenuItem("Select all connected joint bodies", triggered_fn=model_inspector.select_all_connected_links)
            else:
                if num_joints > 0:
                    ui.MenuItem("Select all connected joint colliders", triggered_fn=model_inspector.select_all_connected_joint_shapes)
                    ui.MenuItem("Select all connected joint bodies", triggered_fn=model_inspector.select_all_connected_links)
                if num_bodies > 0:
                    ui.MenuItem("Select all connected body colliders", triggered_fn=model_inspector.select_all_connected_body_shapes)
                    ui.MenuItem("Select all connected body joints", triggered_fn=model_inspector.select_all_connected_body_joints)
        self._ui_context_menu.show()

