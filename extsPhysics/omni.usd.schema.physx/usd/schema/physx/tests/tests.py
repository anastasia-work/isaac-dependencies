import omni.kit.test
from pxr import Plug, Tf, PhysxSchema

class PhysxSchemaTests(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_prim_types(self):
        physics_plugin = Plug.Registry().GetPluginWithName("physxSchema")
        self.assertTrue(physics_plugin != None)

        expected_prim_types = [ 
            PhysxSchema.PhysxPhysicsGearJoint, 
            PhysxSchema.PhysxPhysicsRackAndPinionJoint, 
        ]
        
        for prim_type in expected_prim_types:
            ret_val = physics_plugin.DeclaresType(Tf.Type(prim_type))            
            self.assertTrue(ret_val)
            
    async def test_schema_api_types(self):
        physics_plugin = Plug.Registry().GetPluginWithName("physxSchema")
        self.assertTrue(physics_plugin != None)

        expected_schema_api_types = [ 
            PhysxSchema.PhysxSceneAPI, 
            PhysxSchema.PhysxRigidBodyAPI,
            PhysxSchema.PhysxContactReportAPI,
            PhysxSchema.PhysxCollisionAPI,
            PhysxSchema.PhysxMaterialAPI,
            PhysxSchema.PhysxJointAPI,
            PhysxSchema.PhysxArticulationAPI,
            PhysxSchema.JointStateAPI,
            ]
        
        for prim_type in expected_schema_api_types:
            ret_val = physics_plugin.DeclaresType(Tf.Type(prim_type))            
            self.assertTrue(ret_val)
