import omni.kit.test
from pxr import Plug, Sdf, Tf, ForceFieldSchema

class ForceFieldSchemaTests(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_forcefield_types(self):
        physics_plugin = Plug.Registry().GetPluginWithName("forceFieldSchema")
        self.assertTrue(physics_plugin != None)

        expected_joint_types = [ 
            ForceFieldSchema.PhysxForceFieldSphericalAPI, 
            ForceFieldSchema.PhysxForceFieldConicalAPI, 
            ForceFieldSchema.PhysxForceFieldPlanarAPI, 
            ForceFieldSchema.PhysxForceFieldLinearAPI, 
            ForceFieldSchema.PhysxForceFieldDragAPI, 
            ForceFieldSchema.PhysxForceFieldNoiseAPI, 
            ForceFieldSchema.PhysxForceFieldWindAPI, 
            ForceFieldSchema.PhysxForceFieldSpinAPI, 
            ForceFieldSchema.PhysxForceFieldRingAPI,            
            ]

        for joint_type in expected_joint_types:
            ret_val = physics_plugin.DeclaresType(Tf.Type(joint_type))
            self.assertTrue(ret_val)
            api_schemas = joint_type().GetSchemaClassPrimDefinition().GetAppliedAPISchemas()
            self.assertTrue(any(api_schema.startswith("PhysxForceFieldAPI") for api_schema in api_schemas))
            
    async def test_schema_api_types(self):
        physics_plugin = Plug.Registry().GetPluginWithName("forceFieldSchema")
        self.assertTrue(physics_plugin != None)

        expected_schema_api_types = [ 
            ForceFieldSchema.PhysxForceFieldAPI, 
            ]
        
        for prim_type in expected_schema_api_types:
            ret_val = physics_plugin.DeclaresType(Tf.Type(prim_type))            
            self.assertTrue(ret_val)
