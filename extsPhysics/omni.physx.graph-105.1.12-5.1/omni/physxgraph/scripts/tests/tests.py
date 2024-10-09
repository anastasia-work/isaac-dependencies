from omni.physxtests.utils.physicsBase import TestCategory
import omni.usd
import omni.physx
import omni.kit.test
import omni.graph.core as og
import omni.graph.core.tests as ogts
import os
from pxr import PhysxSchema, Gf

class PhysGraphTest(ogts.OmniGraphTestCase):

    category = TestCategory.Core
    async def setUp(self):
        await super().setUp()

    async def tearDown(self):
        await super().tearDown()
 
    async def _load_usd(self, filename):
        data_path = "../../../../../data/tests"
        tests_folder = os.path.abspath(os.path.normpath(os.path.join(__file__, data_path)))
        tests_folder = tests_folder.replace("\\", "/") + "/"
        filepath = tests_folder + filename + ".usda"
        await omni.usd.get_context().open_stage_async(filepath)
        self._usd_context = omni.usd.get_context()
        self.assertIn(filename, self._usd_context.get_stage_url())
        self._stage = self._usd_context.get_stage()    

    async def _timeline_play_steps(self, num_frames):

        omni.timeline.get_timeline_interface().play()
        for _ in range(num_frames):
            await omni.kit.app.get_app().next_update_async()
        # stop, check for reset and prep for next run
        omni.timeline.get_timeline_interface().stop()

    async def _test_raycast_any(self):
        test_error_msg_prefix = "Test failed for node \"Raycast, any\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryRaycastAny"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_range.inputs:value", "physxogn.inputs:raycastRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 150.0, 0.0]),
                    ("physxogn.inputs:bothSides", False)
                ]
            }
        )

        out_hit = og.Controller(ogController.attribute("outputs:hit", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        hit = out_hit.get()
        self.assertFalse(hit, test_error_msg_prefix + "expected to find no hit.")

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        hit = out_hit.get()
        self.assertTrue(hit, test_error_msg_prefix + "expected to find hit.")

        ogController.delete_node(test_nodes)

    async def _test_raycast_closest(self):
        test_error_msg_prefix = "Test failed for node \"Raycast, Closest\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryRaycastClosest"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_range.inputs:value", "physxogn.inputs:raycastRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 150.0, 0.0]),
                    ("physxogn.inputs:bothSides", False)
                ]
            }
        )

        out_prim = og.Controller(ogController.attribute("outputs:bodyPrimPath", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prim = out_prim.get()
        self.assertEqual(prim, "", test_error_msg_prefix + "unexpected prim: "+prim)

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prim = out_prim.get()
        self.assertEqual(prim, "/World/Cube", test_error_msg_prefix + "unexpected prim: "+prim)
        
        out_material = og.Controller(ogController.attribute("outputs:materialPath", test_nodes[0]))
        material = out_material.get()
        self.assertEqual(material, "/World/PhysicsMaterial", test_error_msg_prefix + "unexpected physics material: "+material)

        out_face_index = og.Controller(ogController.attribute("outputs:faceIndex", test_nodes[0]))
        face_index = out_face_index.get()
        self.assertEqual(face_index, 0, test_error_msg_prefix + "unexpected face index: "+str(face_index))

        out_normal = og.Controller(ogController.attribute("outputs:normal", test_nodes[0]))
        normal = out_normal.get()
        self.assertEqual([*normal], [0.0, 1.0, 0.0], test_error_msg_prefix + "unexpected hit normal: "+str(normal))

        ogController.delete_node(test_nodes)

    async def _test_raycast_all(self):
        test_error_msg_prefix = "Test failed for node \"Raycast, All\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryRaycastAll"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_range.inputs:value", "physxogn.inputs:raycastRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 50.0, 0.0]),
                    ("physxogn.inputs:bothSides", True),
                    ("physxogn.inputs:sortByDistance", True)
                ]
            }
        )

        out_prims = og.Controller(ogController.attribute("outputs:bodyPrimPaths", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 1, test_error_msg_prefix + "expected to find 1 prim in but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + "unexpected prim")

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 2, test_error_msg_prefix + "expected to find 2 prim but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + " unexpected prim sort order, expected \"/World/Cube\" but found "+prims[0])
        self.assertEqual(prims[1], "/World/GroundPlane/CollisionPlane", test_error_msg_prefix + " unexpected prim sort order, expected \"/GroundPlane/CollisionPlane\" but found "+prims[1])
   
        ogController.delete_node(test_nodes)

    async def _test_sweep_sphere_any(self):
        test_error_msg_prefix = "Test failed for node \"Sweep, Sphere, any\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQuerySweepSphereAny"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_radius", "omni.graph.nodes.ConstantFloat"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_radius.inputs:value", "physxogn.inputs:radius"),
                    ("const_range.inputs:value", "physxogn.inputs:sweepRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_radius.inputs:value", 10.0),
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 150.0, 0.0]),
                    ("physxogn.inputs:bothSides", False)
                ]
            }
        )

        out_hit = og.Controller(ogController.attribute("outputs:hit", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        hit = out_hit.get()
        self.assertFalse(hit, test_error_msg_prefix + "expected to find no hit.")

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        hit = out_hit.get()
        self.assertTrue(hit, test_error_msg_prefix + "expected to find hit.")

        ogController.delete_node(test_nodes)

    async def _test_sweep_sphere_closest(self):
        test_error_msg_prefix = "Test failed for node \"Sweep, Sphere, Closest\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQuerySweepSphereClosest"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_radius", "omni.graph.nodes.ConstantFloat"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_radius.inputs:value", "physxogn.inputs:radius"),
                    ("const_range.inputs:value", "physxogn.inputs:sweepRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_radius.inputs:value", 10.0),
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 150.0, 0.0]),
                    ("physxogn.inputs:bothSides", False)
                ]
            }
        )

        out_prim = og.Controller(ogController.attribute("outputs:bodyPrimPath", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prim = out_prim.get()
        self.assertEqual(prim, "", test_error_msg_prefix + "unexpected prim: "+prim)

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prim = out_prim.get()
        self.assertEqual(prim, "/World/Cube", test_error_msg_prefix + "unexpected prim: "+prim)

        ogController.delete_node(test_nodes)

    async def _test_sweep_sphere_all(self):
        test_error_msg_prefix = "Test failed for node \"Sweep, Sphere, All\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQuerySweepSphereAll"),
                    ("const_direction", "omni.graph.nodes.ConstantFloat3"),
                    ("const_origin", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_radius", "omni.graph.nodes.ConstantFloat"),
                    ("const_range", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_origin.inputs:value", "physxogn.inputs:origin"),
                    ("const_radius.inputs:value", "physxogn.inputs:radius"),
                    ("const_range.inputs:value", "physxogn.inputs:sweepRange"),
                    ("const_direction.inputs:value", "physxogn.inputs:direction"),                    
                ],
                keys.SET_VALUES: [
                    ("const_radius.inputs:value", 10.0),
                    ("const_range.inputs:value", 100.0),
                    ("const_origin.inputs:value", [0.0, 50.0, 0.0]),
                    ("physxogn.inputs:bothSides", True),
                    ("physxogn.inputs:sortByDistance", True)
                ]
            }
        )

        out_prims = og.Controller(ogController.attribute("outputs:bodyPrimPaths", test_nodes[0]))
        in_direction = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_direction.set([0.0, 1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 1, test_error_msg_prefix + "expected to find 1 prim in but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + "unexpected prim")

        in_direction.set([0.0, -1.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 2, test_error_msg_prefix + "expected to find 2 prim but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + " unexpected prim sort order, expected \"/World/Cube\" but found "+prims[0])
        self.assertEqual(prims[1], "/World/GroundPlane/CollisionPlane", test_error_msg_prefix + " unexpected prim sort order, expected \"/GroundPlane/CollisionPlane\" but found "+prims[1])
   
        ogController.delete_node(test_nodes)

    async def _test_overlap_prim_any(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Prim, Any\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapPrimAny"),
                    ("tick", "omni.graph.action.OnTick")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn")
                ],
                keys.SET_VALUES: [
                    ("physxogn.inputs:primPath", "/World/Cube")
                ]
            }
        )

        out_overlap = og.Controller(ogController.attribute("outputs:overlap", test_nodes[0]))

        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        overlaps = out_overlap.get()
        self.assertTrue(overlaps, test_error_msg_prefix + "expected to find overlapping.")

        ogController.delete_node(test_nodes)

    async def _test_overlap_prim_all(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Prim, All\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapPrimAll"),
                    ("tick", "omni.graph.action.OnTick")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn")
                ],
                keys.SET_VALUES: [
                    ("physxogn.inputs:primPath", "/World/Cube")
                ]
            }
        )

        out_prims = og.Controller(ogController.attribute("outputs:bodyPrimPaths", test_nodes[0]))

        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 1, test_error_msg_prefix + "expected to find 1 prim in but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + "unexpected prim")

        ogController.delete_node(test_nodes)

    async def _test_overlap_sphere_any(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Sphere, Any\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapSphereAny"),
                    ("const_position", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_radius", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_position.inputs:value", "physxogn.inputs:position"),
                    ("const_radius.inputs:value", "physxogn.inputs:radius")
                ],
                keys.SET_VALUES: [
                    ("const_radius.inputs:value", 50.0)
                ]
            }
        )

        out_overlap = og.Controller(ogController.attribute("outputs:overlap", test_nodes[0]))
        in_position = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_position.set([0.0, 151.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        overlaps = out_overlap.get()
        self.assertFalse(overlaps, test_error_msg_prefix + "expected to find no overlapping.")

        in_position.set([0.0, 50.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        overlaps = out_overlap.get()
        self.assertTrue(overlaps, test_error_msg_prefix + "expected to find overlapping.")

        ogController.delete_node(test_nodes)

    async def _test_overlap_sphere_all(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Sphere, All\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapSphereAll"),
                    ("const_position", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_radius", "omni.graph.nodes.ConstantFloat")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_position.inputs:value", "physxogn.inputs:position"),
                    ("const_radius.inputs:value", "physxogn.inputs:radius")
                ],
                keys.SET_VALUES: [
                    ("const_radius.inputs:value", 50.0)
                ]
            }
        )

        out_prims = og.Controller(ogController.attribute("outputs:bodyPrimPaths", test_nodes[0]))
        in_position = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_position.set([0.0, 51.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 1, test_error_msg_prefix + "expected to find 1 prim in but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + "unexpected prim")

        in_position.set([0.0, 49.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 2, test_error_msg_prefix + "expected to find 2 prim but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/GroundPlane/CollisionPlane")
        self.assertEqual(prims[1], "/World/Cube")
       
        ogController.delete_node(test_nodes)

    async def _test_overlap_box_any(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Box, Any\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapBoxAny"),
                    ("const_position", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_dimensions", "omni.graph.nodes.ConstantFloat3"),
                    ("const_rotation", "omni.graph.nodes.ConstantFloat3")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_dimensions.inputs:value", "physxogn.inputs:dimensions"),
                    ("const_position.inputs:value", "physxogn.inputs:position"),
                    ("const_rotation.inputs:value", "physxogn.inputs:rotation")
                ],
                keys.SET_VALUES: [
                    ("const_dimensions.inputs:value", [100.0, 100.0, 100.0]),
                    ("const_rotation.inputs:value", [0.0, 0.0, 0.0])
                ]
            }
        )

        out_overlap = og.Controller(ogController.attribute("outputs:overlap", test_nodes[0]))
        in_position = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))

        in_position.set([0.0, 151.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        overlaps = out_overlap.get()
        self.assertFalse(overlaps, test_error_msg_prefix + "expected to find no overlapping.")

        in_position.set([0.0, 50.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        overlaps = out_overlap.get()
        self.assertTrue(overlaps, test_error_msg_prefix + "expected to find overlapping.")

        ogController.delete_node(test_nodes)

    async def _test_overlap_box_all(self):
        test_error_msg_prefix = "Test failed for node \"Overlap, Box, All\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.SceneQueryOverlapBoxAll"),
                    ("const_position", "omni.graph.nodes.ConstantPoint3f"),
                    ("tick", "omni.graph.action.OnTick"),
                    ("const_dimensions", "omni.graph.nodes.ConstantFloat3"),
                    ("const_rotation", "omni.graph.nodes.ConstantFloat3")
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn"),
                    ("const_dimensions.inputs:value", "physxogn.inputs:dimensions"),
                    ("const_position.inputs:value", "physxogn.inputs:position"),
                    ("const_rotation.inputs:value", "physxogn.inputs:rotation")
                ],
                keys.SET_VALUES: [
                    ("const_dimensions.inputs:value", [100.0, 100.0, 100.0]),
                    ("const_rotation.inputs:value", [0.0, 0.0, 0.0])
                ]
            }
        )

        out_prims = og.Controller(ogController.attribute("outputs:bodyPrimPaths", test_nodes[0]))

        in_position = og.Controller(ogController.attribute("inputs:value", test_nodes[1]))
        in_position.set([0.0, 51.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 1, test_error_msg_prefix + "expected to find 1 prim in but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/Cube", test_error_msg_prefix + "unexpected prim")

        in_position.set([0.0, 49.0, 0.0])
        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prims = out_prims.get()
        self.assertEqual(len(prims), 2, test_error_msg_prefix + "expected to find 2 prim but found "+str(len(prims)))
        self.assertEqual(prims[0], "/World/GroundPlane/CollisionPlane")
        self.assertEqual(prims[1], "/World/Cube")
       
        ogController.delete_node(test_nodes)

    async def test_scene_query(self):

        await self._load_usd("TestScene")

        og.Controller.edit({
                "evaluator_name": "execution",
                "graph_path": "/TestGraph",
            })

        await self._test_overlap_prim_all()
        await self._test_overlap_prim_any()
        await self._test_overlap_sphere_all()
        await self._test_overlap_sphere_any()
        await self._test_overlap_box_all()
        await self._test_overlap_box_any()
        await self._test_sweep_sphere_all()
        await self._test_sweep_sphere_closest()
        await self._test_sweep_sphere_any()    
        await self._test_raycast_all()
        await self._test_raycast_closest()
        await self._test_raycast_any()

        await omni.usd.get_context().close_stage_async()

    async def test_contact_generation(self):

        await self._load_usd("TestScene")

        og.Controller.edit({
                "evaluator_name": "execution",
                "graph_path": "/TestGraph",
            })

        test_error_msg_prefix = "Test failed for node \"Generate Contacts\": "
        ogController = og.Controller()
        keys = ogController.Keys
        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn", "omni.physx.graph.GenerateContacts"),
                    ("tick", "omni.graph.action.OnTick"),
                ],
                keys.CONNECT: [
                    ("tick.outputs:tick", "physxogn.inputs:execIn")
                ],
                keys.SET_VALUES: [
                    ("physxogn.inputs:shape0", "/World/Cube"),
                    ("physxogn.inputs:shape1", "/World/GroundPlane/CollisionPlane"),
                    ("physxogn.inputs:contactDistance", 0.01),
                    ("physxogn.inputs:meshContactMargin", 0.01),
                    ("physxogn.inputs:toleranceLength", 0.1)
                ]
            }
        )

        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)

        out_contactCount = og.Controller(ogController.attribute("outputs:contactCount", test_nodes[0]))
        contactCount = out_contactCount.get()
        self.assertEqual(contactCount, 4)

        out_contactNormals = og.Controller(ogController.attribute("outputs:contactNormals", test_nodes[0]))
        contactNormals = out_contactNormals.get()
        self.assertAlmostEqual(contactNormals[0][1], 1.0, delta=0.0001)

        await omni.usd.get_context().close_stage_async()

    async def _test_contact_event(self, prim, advanced):
        test_error_msg_prefix = "Test failed for node \"On Contact Event\" " + ("Advanced" if advanced else "") + ":"
        ogController = og.Controller()
        keys = ogController.Keys
        nodetype = "omni.physx.graph.OnContactEventAdvanced" if advanced else "omni.physx.graph.OnContactEventBasic"

        (graph, test_nodes, _, _) = ogController.edit("/TestGraph",
            {
                keys.CREATE_NODES: [
                    ("physxogn_found", nodetype),
                    ("physxogn_persists", nodetype),
                    ("physxogn_lost", nodetype),
                    ("physxogn_found_target", "omni.graph.action.Branch"),
                    ("physxogn_persists_target", "omni.graph.action.Branch"),
                    ("physxogn_lost_target", "omni.graph.action.Branch")
                ],
                keys.CONNECT: [
                    ("physxogn_found.outputs:foundExecOut", "physxogn_found_target.inputs:execIn"),
                    ("physxogn_persists.outputs:persistsExecOut", "physxogn_persists_target.inputs:execIn"),
                    ("physxogn_lost.outputs:lostExecOut", "physxogn_lost_target.inputs:execIn")
                ],
                keys.SET_VALUES: [
                    ("physxogn_found.inputs:bodyPaths", ["/World/Cube"]),
                    ("physxogn_persists.inputs:bodyPaths", ["/World/Cube"]),
                    ("physxogn_lost.inputs:bodyPaths", ["/World/Cube"])
                ]
            }
        )

        prim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(0.0, 0.0, 50.0))
        out_prim_found = og.Controller(ogController.attribute("outputs:contactingBody", test_nodes[0]))
        out_prim_persists = og.Controller(ogController.attribute("outputs:contactingBody", test_nodes[1]))
        out_prim_lost = og.Controller(ogController.attribute("outputs:contactingBody", test_nodes[2]))

        await ogController.evaluate(graph)

        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)

        prim_path = out_prim_found.get()
        self.assertEqual(prim_path, "/World/GroundPlane/CollisionPlane", test_error_msg_prefix + f"unexpected or missing prim for found contact event: {prim_path}")

        prim_path = out_prim_found.set("")
        prim_path = out_prim_persists.set("")
        prim_path = out_prim_lost.set("")

        await self._timeline_play_steps(1)
        await ogController.evaluate(graph)
        prim_path = out_prim_found.get()
        self.assertEqual(prim_path, "", test_error_msg_prefix + f"unexpected prim for found contact event: {prim_path}")
        prim_path = out_prim_persists.get()
        self.assertEqual(prim_path, "/World/GroundPlane/CollisionPlane", test_error_msg_prefix + f"unexpected or missing prim for persists contact event: {prim_path}")
        prim_path = out_prim_lost.get()
        self.assertEqual(prim_path, "", test_error_msg_prefix + "unexpected prim lost contact")

        prim.GetAttribute("physics:velocity").Set(Gf.Vec3f(0.0, 1000.0, 0.0))

        await self._timeline_play_steps(10)
        await ogController.evaluate(graph)

        prim_path = out_prim_lost.get()
        self.assertEqual(prim_path, "/World/GroundPlane/CollisionPlane", test_error_msg_prefix + f"unexpected or missing prim for lost contact event: {prim_path}")

        prim_path = out_prim_found.set("")
        prim_path = out_prim_persists.set("")
        prim_path = out_prim_lost.set("")

        await self._timeline_play_steps(5)
        await ogController.evaluate(graph)

        prim_path = out_prim_found.get()
        self.assertEqual(prim_path, "", test_error_msg_prefix + f"unexpected prim for found contact event: {prim_path}")
        prim_path = out_prim_persists.get()
        self.assertEqual(prim_path, "", test_error_msg_prefix + f"unexpected prim for persists contact event: {prim_path}")
        prim_path = out_prim_lost.get()
        self.assertEqual(prim_path, "", test_error_msg_prefix + f"unexpected prim for lost contact event: {prim_path}")

        prim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(0.0, 0.0, 50.0))
        prim.GetAttribute("physics:velocity").Set(Gf.Vec3f(0.0, 0.0, 0.0))
        ogController.delete_node(test_nodes)

    async def test_contact_events(self):

        await self._load_usd("TestScene")

        cube_prim = self._stage.GetPrimAtPath("/World/Cube")

        contact_report_API = PhysxSchema.PhysxContactReportAPI.Apply(cube_prim)
        contact_report_API.CreateThresholdAttr().Set(0)

        og.Controller.edit({
                "evaluator_name": "execution",
                "graph_path": "/TestGraph",
            })

        await self._test_contact_event(cube_prim, False)
        await self._test_contact_event(cube_prim, True)
        await omni.usd.get_context().close_stage_async()
