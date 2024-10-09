import omni.physx.scripts.utils as physxUtils
import omni.physx.scripts.physicsUtils as physicsUtils
from omni.physxtests.utils.physicsBase import PhysicsMemoryStageBaseAsyncTestCase, TestCategory
from omni.physxtests import utils
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema
import unittest
from omni.physxtests.testBases.articulationTestBase import ArticulationTestBase


class PhysxArticulationForceSensorAPITestMemoryStage(PhysicsMemoryStageBaseAsyncTestCase, ArticulationTestBase):
    category = TestCategory.Core

    async def setUp(self):
        await super().setUp()
        await self.articulation_stage_and_scene_setup()

        # create xform and 3 boxes
        self._boxes_parent_xform = UsdGeom.Xform.Define(self._stage, "/World/articulation")

        box_actor0_path = "/articulation/boxActor0"
        box_actor1_path = "/articulation/boxActor1"
        box_actor2_path = "/articulation/boxActor2"

        size = Gf.Vec3f(100.0)
        position = Gf.Vec3f(0.0, 0.0, 200.0)
        self._box0 = physicsUtils.add_box(self._stage, box_actor0_path, size, position)

        position = Gf.Vec3f(0.0, 0.0, 400.0)
        self._box1_rigid = physicsUtils.add_rigid_box(self._stage, box_actor1_path, size, position)

        position = Gf.Vec3f(0.0, 0.0, 600.0)
        self._box2_rigid = physicsUtils.add_rigid_box(self._stage, box_actor2_path, size, position)

    async def test_articulation_root_force_sensor_release(self):
        UsdPhysics.ArticulationRootAPI.Apply(self._boxes_parent_xform.GetPrim())
        UsdPhysics.RigidBodyAPI.Apply(self._box0.GetPrim())
        UsdPhysics.CollisionAPI.Apply(self._box0.GetPrim())
        
        forceSensorPath = self._box1_rigid.GetPrim().GetPrimPath().AppendPath("forceSensor")
        sensorXform = UsdGeom.Xform.Define(self._stage, forceSensorPath)
        PhysxSchema.PhysxArticulationForceSensorAPI.Apply(sensorXform.GetPrim())

        joint0 = physxUtils.createJoint(self._stage, "Revolute", self._box0.GetPrim(), self._box1_rigid.GetPrim())
        joint1 = physxUtils.createJoint(self._stage, "Revolute", self._box1_rigid.GetPrim(), self._box2_rigid.GetPrim())
        
        self.step()
        
        self._check_physx_object_counts({"numBoxShapes": 3, "numDynamicRigids": 3, "numStaticRigids": 0, "numArticulations": 1, "numConstraints": 0})

        self._stage.RemovePrim(self._boxes_parent_xform.GetPrim().GetPath())
        
        self.step()
        self._check_physx_object_counts({"numBoxShapes": 0, "numDynamicRigids": 0, "numStaticRigids": 0, "numArticulations": 0, "numConstraints": 0})
        
    async def test_articulation_first_force_sensor_second_release(self):
        UsdPhysics.ArticulationRootAPI.Apply(self._box0.GetPrim())
        UsdPhysics.RigidBodyAPI.Apply(self._box0.GetPrim())
        UsdPhysics.CollisionAPI.Apply(self._box0.GetPrim())
        
        forceSensorPath = self._box1_rigid.GetPrim().GetPrimPath().AppendPath("forceSensor")
        sensorXform = UsdGeom.Xform.Define(self._stage, forceSensorPath)
        PhysxSchema.PhysxArticulationForceSensorAPI.Apply(sensorXform.GetPrim())

        joint0 = physxUtils.createJoint(self._stage, "Revolute", self._box0.GetPrim(), self._box1_rigid.GetPrim())
        joint1 = physxUtils.createJoint(self._stage, "Revolute", self._box1_rigid.GetPrim(), self._box2_rigid.GetPrim())
        
        self.step()
        
        self._check_physx_object_counts({"numBoxShapes": 3, "numDynamicRigids": 3, "numStaticRigids": 0, "numArticulations": 1, "numConstraints": 0})

        # remove 
        self._stage.RemovePrim(self._box0.GetPrim().GetPath())            
        self._stage.RemovePrim(self._box1_rigid.GetPrim().GetPath())
        self.step()
        self._check_physx_object_counts({"numBoxShapes": 0, "numDynamicRigids": 0, "numStaticRigids": 0, "numArticulations": 0, "numConstraints": 0})        
        
    async def test_articulation_first_force_sensor_step_release(self):
        UsdPhysics.ArticulationRootAPI.Apply(self._box0.GetPrim())
        UsdPhysics.RigidBodyAPI.Apply(self._box0.GetPrim())
        UsdPhysics.CollisionAPI.Apply(self._box0.GetPrim())
        
        forceSensorPath = self._box1_rigid.GetPrim().GetPrimPath().AppendPath("forceSensor")
        sensorXform = UsdGeom.Xform.Define(self._stage, forceSensorPath)
        PhysxSchema.PhysxArticulationForceSensorAPI.Apply(sensorXform.GetPrim())

        joint0 = physxUtils.createJoint(self._stage, "Revolute", self._box0.GetPrim(), self._box1_rigid.GetPrim())
        joint1 = physxUtils.createJoint(self._stage, "Revolute", self._box1_rigid.GetPrim(), self._box2_rigid.GetPrim())
        
        self.step()
        
        self._check_physx_object_counts({"numBoxShapes": 3, "numDynamicRigids": 3, "numStaticRigids": 0, "numArticulations": 1, "numConstraints": 0})

        # remove 
        self._stage.RemovePrim(self._box0.GetPrim().GetPath())            
        
        # step to see if sensors are not updated
        self.step()
        self._check_physx_object_counts({"numBoxShapes": 0, "numDynamicRigids": 0, "numStaticRigids": 0, "numArticulations": 0, "numConstraints": 0})        
