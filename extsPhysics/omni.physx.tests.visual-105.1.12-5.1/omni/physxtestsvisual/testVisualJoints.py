from pathlib import Path
from omni.physx.scripts import physicsUtils
from omni.physx.scripts import utils as baseUtils
from omni.physxtests import utils
from omni.physxtestsvisual.utils import TestCase
from omni.physxtests.utils.physicsBase import TestCategory
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema
import carb.input
import carb.tokens
from omni.kit.viewport.utility import frame_viewport_selection
import omni.kit.app
from omni.physx.bindings._physx import (
    SETTING_DISPLAY_JOINTS,
)


class PhysxVisualJointsTest(TestCase):
    category = TestCategory.Core

    def setup_joint_scenario(self, stage, jointType):
        # create a joint with two bodies
        size = Gf.Vec3f(25.0)
        position = Gf.Vec3f(0.0, -100.0, 0.0)
        cube0 = physicsUtils.add_rigid_cube(stage, "/cubeActor0", size, position)
        rigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(cube0.GetPrim())
        rigidBodyAPI.CreateRigidBodyEnabledAttr(False)
        position = Gf.Vec3f(0.0, 100.0, 0.0)
        cube1 = physicsUtils.add_rigid_cube(stage, "/cubeActor1", size, position)

        if jointType == "revolute":
            joint = UsdPhysics.RevoluteJoint.Define(self._stage, "/World/cubeActor0/revoluteJoint")
        elif jointType == "prismatic":
            joint = UsdPhysics.PrismaticJoint.Define(self._stage, "/World/cubeActor0/prismaticJoint")
        elif jointType == "fixed":
            joint = UsdPhysics.FixedJoint.Define(self._stage, "/World/cubeActor0/fixedJoint")
        elif jointType == "d6":
            joint = UsdPhysics.Joint.Define(self._stage, "/World/cubeActor0/d6Joint")
        elif jointType == "distance":
            joint = UsdPhysics.DistanceJoint.Define(self._stage, "/World/cubeActor0/distanceJoint")
        elif jointType == "spherical":
            joint = UsdPhysics.SphericalJoint.Define(self._stage, "/World/cubeActor0/sphericalJoint")
        elif jointType == "gear":
            joint = PhysxSchema.PhysxPhysicsGearJoint.Define(self._stage, "/World/cubeActor0/gearJoint")
        elif jointType == "rack":
            joint = PhysxSchema.PhysxPhysicsRackAndPinionJoint.Define(self._stage, "/World/cubeActor0/rackJoint")
        val1 = [cube0.GetPrim().GetPath()]
        val2 = [cube1.GetPrim().GetPath()]
        joint.CreateBody0Rel().SetTargets(val1)
        joint.CreateBody1Rel().SetTargets(val2)
        joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 4.0, 0.0))
        joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, -4.0, 0.0))

        self.joint = joint
        self.body0prim = cube0.GetPrim()

    async def test_physics_visual_joint_selection(self):
        stage = await self.new_stage()

        await self.setup_viewport_test()

        utils.physics_scene_setup(stage)
        self.setup_joint_scenario(stage, "revolute")

        await omni.kit.app.get_app().next_update_async()

        usdContext = omni.usd.get_context()
        usdContext.get_selection().set_selected_prim_paths(["/World/cubeActor0/revoluteJoint"], True) 

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()

        await self.do_visual_test()       
        await self.new_stage()

    async def physics_visual_joint_billboard(self, jointType):
        stage = await self.new_stage()

        await self.setup_viewport_test()

        utils.physics_scene_setup(stage)

        self.joint_vis = carb.settings.get_settings().get_as_bool(SETTING_DISPLAY_JOINTS)
        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, True)

        self.setup_joint_scenario(stage, jointType)

        await omni.kit.app.get_app().next_update_async()

        usdContext = omni.usd.get_context()
        usdContext.get_selection().set_selected_prim_paths([], True) 

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()

    async def test_physics_visual_joint_billboard_revolute(self):        
        await self.physics_visual_joint_billboard("revolute")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_prismatic(self):      
        await self.physics_visual_joint_billboard("prismatic")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_fixed(self):        
        await self.physics_visual_joint_billboard("fixed")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_d6(self):   
        await self.physics_visual_joint_billboard("d6")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_distance(self):
        await self.physics_visual_joint_billboard("distance")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_spherical(self):   
        await self.physics_visual_joint_billboard("spherical")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_gear(self):   
        await self.physics_visual_joint_billboard("gear")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)

    async def test_physics_visual_joint_billboard_rack(self):
        await self.physics_visual_joint_billboard("rack")
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, self.joint_vis)
        
    async def test_physics_visual_joint_billboard_visibility(self):
        stage = await self.new_stage()

        await self.setup_viewport_test()

        utils.physics_scene_setup(stage)

        joint_vis = carb.settings.get_settings().get_as_bool(SETTING_DISPLAY_JOINTS)
        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, True)

        self.setup_joint_scenario(stage, "revolute")

        await omni.kit.app.get_app().next_update_async()

        usdContext = omni.usd.get_context()
        usdContext.get_selection().set_selected_prim_paths([], True) 

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()

        imageable = UsdGeom.Imageable(self.joint)
        imageable.MakeInvisible()

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()

        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, joint_vis)

    async def test_physics_visual_joint_billboard_parent_visibility(self):
        stage = await self.new_stage()

        await self.setup_viewport_test()

        utils.physics_scene_setup(stage)

        joint_vis = carb.settings.get_settings().get_as_bool(SETTING_DISPLAY_JOINTS)
        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, True)

        self.setup_joint_scenario(stage, "revolute")

        await omni.kit.app.get_app().next_update_async()

        usdContext = omni.usd.get_context()
        usdContext.get_selection().set_selected_prim_paths([], True) 

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()

        print("Prim path: " + str(self.body0prim.GetPrimPath()))
        imageable = UsdGeom.Imageable(self.body0prim)
        imageable.MakeInvisible()

        for _ in range(20):
            await omni.kit.app.get_app().next_update_async()
            
        await self.do_visual_test()       
        await self.new_stage()

        carb.settings.get_settings().set_bool(SETTING_DISPLAY_JOINTS, joint_vis)