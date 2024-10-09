# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import tempfile
from pathlib import Path

import omni.graph.core as og
import omni.graph.tools.ogn as ogn
import omni.graph.ui._impl.omnigraph_attribute_base as ogab
import omni.graph.ui._impl.omnigraph_attribute_models as ogam
import omni.kit.app
import omni.kit.commands
import omni.kit.test
import omni.ui as ui
import omni.usd
from omni.kit import ui_test
from omni.ui.tests.test_base import OmniUiTest
from pxr import Sdf, Usd

_MATRIX_DIMENSIONS = {4: 2, 9: 3, 16: 4}

# ----------------------------------------------------------------------


class TestOmniGraphWidget(OmniUiTest):
    """
    Tests for OmniGraphBase and associated models in this module, the custom widget for the kit property panel uses
    these models which are customized for OmniGraphNode prims.
    """

    TEST_GRAPH_PATH = "/World/TestGraph"

    # Before running each test
    async def setUp(self):
        await super().setUp()

        # Ensure we have a clean stage for the test
        await omni.usd.get_context().new_stage_async()
        # Give OG a chance to set up on the first stage update
        await omni.kit.app.get_app().next_update_async()

        og.Controller.edit({"graph_path": self.TEST_GRAPH_PATH, "evaluator_name": "execution"})

        extension_root_folder = Path(
            omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        )

        self._golden_img_dir = extension_root_folder.joinpath("data/tests/golden_img")

        import omni.kit.window.property as p

        self._w = p.get_window()

    # After running each test
    async def tearDown(self):
        # Close the stage to avoid dangling references to the graph. (OM-84680)
        await omni.usd.get_context().close_stage_async()
        await super().tearDown()

    def __attribute_type_to_name(self, attribute_type: og.Type) -> str:
        """Converts an attribute type into the canonical attribute name used by the test nodes.
        The rules are:
            - prefix of a_
            - followed by name of attribute base type
            - followed by optional _N if the component count N is > 1
            - followed by optional '_array' if the type is an array

        Args:
            type: OGN attribute type to deconstruct

        Returns:
            Canonical attribute name for the attribute with the given type
        """
        attribute_name = f"a_{og.Type(attribute_type.base_type, 1, 0, attribute_type.role).get_ogn_type_name()}"
        attribute_name = attribute_name.replace("prim", "bundle")
        if attribute_type.tuple_count > 1:
            if attribute_type.role in [og.AttributeRole.TRANSFORM, og.AttributeRole.FRAME, og.AttributeRole.MATRIX]:
                attribute_name += f"_{_MATRIX_DIMENSIONS[attribute_type.tuple_count]}"
            else:
                attribute_name += f"_{attribute_type.tuple_count}"
        array_depth = attribute_type.array_depth
        while array_depth > 0 and attribute_type.role not in [og.AttributeRole.TEXT, og.AttributeRole.PATH]:
            attribute_name += "_array"
            array_depth -= 1
        return attribute_name

    async def test_target_attribute(self):
        """
        Exercise the target-attribute customizations for Property Panel. The related code is in
        omnigraph_attribute_builder.py and targets.py
        """
        usd_context = omni.usd.get_context()

        keys = og.Controller.Keys
        controller = og.Controller()

        (_, (get_parent_prims,), _, _) = controller.edit(
            self.TEST_GRAPH_PATH,
            {
                keys.CREATE_NODES: [
                    ("GetParentPrims", "omni.graph.nodes.GetParentPrims"),
                ],
            },
        )

        # The OG attribute-base UI should refreshes every frame
        ogab.AUTO_REFRESH_PERIOD = 0

        # Select the node.
        usd_context.get_selection().set_selected_prim_paths([get_parent_prims.get_prim_path()], True)

        # Wait for property panel to converge
        await ui_test.human_delay(5)

        # Click the Add-Relationship button
        attr_name = "inputs:prims"
        await ui_test.find(
            f"Property//Frame/**/Button[*].identifier=='sdf_relationship_array_{attr_name}.add_relationships'"
        ).click()

        # Wait for dialog to show up
        await ui_test.human_delay(5)

        # push the select-graph-target button and wait for dialog to close
        await ui_test.find("Select Targets//Frame/**/Button[*].identifier=='select_graph_target'").click()
        await ui_test.human_delay(5)

        # Resize to fit the property panel, and take a snapshot
        await self.docked_test_window(
            window=self._w._window,  # noqa: PLW0212
            width=450,
            height=500,
            restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
            restore_position=ui.DockPosition.BOTTOM,
        )
        await ui_test.human_delay(5)
        await self.finalize_test(golden_img_dir=self._golden_img_dir, golden_img_name="test_target_attribute.png")

    # ----------------------------------------------------------------------

    async def test_target_attribute_browse(self):
        """
        Test the changing an existing selection via the dialog works
        """
        usd_context = omni.usd.get_context()

        keys = og.Controller.Keys
        controller = og.Controller()

        prim_paths = ["/World/Prim"]

        (_, (read_prims_node,), _, _) = controller.edit(
            self.TEST_GRAPH_PATH,
            {
                keys.CREATE_NODES: [
                    ("ReadPrims", "omni.graph.nodes.ReadPrimsV2"),
                ],
                keys.CREATE_PRIMS: [(prim_path, {}) for prim_path in prim_paths],
            },
        )
        attr_name = "inputs:prims"

        usd_context.get_stage().GetPrimAtPath(read_prims_node.get_prim_path()).GetRelationship(attr_name).AddTarget(
            prim_paths[0]
        )

        # The OG attribute-base UI should refreshes every frame
        ogab.AUTO_REFRESH_PERIOD = 0

        # Select the node.
        usd_context.get_selection().set_selected_prim_paths([read_prims_node.get_prim_path()], True)

        # Wait for property panel to converge
        await ui_test.human_delay(5)

        # Click the Browse button
        model_index = 0
        await ui_test.find(
            f"Property//Frame/**/Button[*].identifier=='sdf_browse_relationship_{attr_name}[{model_index}]'"
        ).click()

        # Wait for dialog to show up
        await ui_test.human_delay(5)

        # push the select-graph-target button and wait for dialog to close
        await ui_test.find("Select Targets//Frame/**/Button[*].identifier=='select_graph_target'").click()
        await ui_test.human_delay(5)

        # Resize to fit the property panel, and take a snapshot
        await self.docked_test_window(
            window=self._w._window,  # noqa: PLW0212
            width=450,
            height=500,
            restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
            restore_position=ui.DockPosition.BOTTOM,
        )
        await ui_test.human_delay(5)
        try:
            await self.capture_and_compare(
                golden_img_dir=self._golden_img_dir, golden_img_name="test_target_attribute_browse.png"
            )
            # Now edit the path to verify it displays as expected
            test_path = f"{og.INSTANCING_GRAPH_TARGET_PATH}/foo"
            # FIXME: This input call doesn't work - set with USD instead
            # await ui_test.find(
            #     f"Property//Frame/**/StringField[*].identifier=='sdf_relationship_{attr_name}[{model_index}]'"
            # ).input(test_path)
            usd_context.get_stage().GetPrimAtPath(read_prims_node.get_prim_path()).GetRelationship(
                attr_name
            ).SetTargets([Sdf.Path(f"{read_prims_node.get_prim_path()}/{test_path}")])

            await ui_test.human_delay(5)
            # Check the USD path has the token after the prim path, before the relative path
            self.assertEqual(
                usd_context.get_stage()
                .GetPrimAtPath(read_prims_node.get_prim_path())
                .GetRelationship(attr_name)
                .GetTargets()[0],
                Sdf.Path(f"{read_prims_node.get_prim_path()}/{test_path}"),
            )
            # Check that the composed path from OG is relative to the graph path
            self.assertEqual(
                str(og.Controller.get(f"{read_prims_node.get_prim_path()}.{attr_name}")[0]),
                f"{self.TEST_GRAPH_PATH}/foo",
            )
            # Verify the widget display
            await self.capture_and_compare(
                golden_img_dir=self._golden_img_dir, golden_img_name="test_target_attribute_edit.png"
            )
        finally:
            await self.finalize_test_no_image()

    # ----------------------------------------------------------------------
    async def test_prim_node_template(self):
        """
        Tests the prim node template under different variations of selected
        prims to validate the the user does not get into a state
        where the attribute name cannot be edited
        """
        usd_context = omni.usd.get_context()

        keys = og.Controller.Keys
        controller = og.Controller()

        (graph, nodes, _, _) = controller.edit(
            self.TEST_GRAPH_PATH,
            {
                keys.CREATE_NODES: [
                    ("ReadPrim_Path_ValidTarget", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Path_InvalidTarget", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Path_Connected", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Prim_ValidTarget", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Prim_InvalidTarget", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Prim_Connected", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ReadPrim_Prim_OGTarget", "omni.graph.nodes.ReadPrimAttribute"),
                    ("ConstPrims", "omni.graph.nodes.ConstantPrims"),
                    ("ConstToken", "omni.graph.nodes.ConstantToken"),
                ],
                keys.CONNECT: [
                    ("ConstToken.inputs:value", "ReadPrim_Path_Connected.inputs:primPath"),
                    ("ConstPrims.inputs:value", "ReadPrim_Prim_Connected.inputs:prim"),
                ],
                keys.SET_VALUES: [
                    ("ConstToken.inputs:value", "/World/Target"),
                    ("ReadPrim_Path_ValidTarget.inputs:usePath", True),
                    ("ReadPrim_Path_ValidTarget.inputs:primPath", "/World/Target"),
                    ("ReadPrim_Path_ValidTarget.inputs:name", "xformOp:rotateXYZ"),
                    ("ReadPrim_Path_InvalidTarget.inputs:usePath", True),
                    ("ReadPrim_Path_InvalidTarget.inputs:primPath", "/World/MissingTarget"),
                    ("ReadPrim_Path_InvalidTarget.inputs:name", "xformOp:rotateXYZ"),
                    ("ReadPrim_Path_Connected.inputs:usePath", True),
                    ("ReadPrim_Path_Connected.inputs:name", "xformOp:rotateXYZ"),
                    ("ReadPrim_Prim_ValidTarget.inputs:name", "xformOp:rotateXYZ"),
                    ("ReadPrim_Prim_InvalidTarget.inputs:name", "xformOp:rotateXYZ"),
                    ("ReadPrim_Prim_Connected.inputs:name", "size"),
                    ("ReadPrim_Prim_OGTarget.inputs:name", "fileFormatVersion"),
                ],
                keys.CREATE_PRIMS: [
                    ("/World/Target", "Xform"),
                    ("/World/Cube", "Cube"),
                    ("/World/MissingTarget", "Xform"),
                ],
            },
        )

        # Change the pipeline stage to On demand to prevent the graph from running and producing errors
        og.cmds.ChangePipelineStage(graph=graph, new_pipeline_stage=og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND)

        # The OG attribute-base UI should refreshes every frame
        ogab.AUTO_REFRESH_PERIOD = 0

        # add relationships to all
        graph_path = self.TEST_GRAPH_PATH
        stage = omni.usd.get_context().get_stage()
        rel = stage.GetPropertyAtPath(f"{graph_path}/ReadPrim_Prim_ValidTarget.inputs:prim")
        omni.kit.commands.execute("AddRelationshipTarget", relationship=rel, target="/World/Target")

        rel = stage.GetPropertyAtPath(f"{graph_path}/ReadPrim_Prim_OGTarget.inputs:prim")
        omni.kit.commands.execute("AddRelationshipTarget", relationship=rel, target=og.INSTANCING_GRAPH_TARGET_PATH)

        rel = stage.GetPropertyAtPath(f"{graph_path}/ReadPrim_Prim_InvalidTarget.inputs:prim")
        omni.kit.commands.execute("AddRelationshipTarget", relationship=rel, target="/World/MissingTarget")

        rel = stage.GetPropertyAtPath(f"{graph_path}/ConstPrims.inputs:value")
        omni.kit.commands.execute("AddRelationshipTarget", relationship=rel, target="/World/Cube")
        omni.kit.commands.execute("AddRelationshipTarget", relationship=rel, target="/World/Target")

        # avoids an error by removing the invalid prim after the graph is created
        omni.kit.commands.execute("DeletePrims", paths=["/World/MissingTarget"])

        # Go through all the ReadPrim variations and validate that the image is expected.
        # In the case of a valid target the widget for the attribute should be a dropdown
        # Otherwise it should be a text field
        for node in nodes:
            node_name = node.get_prim_path().split("/")[-1]

            if not node_name.startswith("ReadPrim"):
                continue

            with self.subTest(node_name=node_name):
                test_img_name = f"test_{node_name.lower()}.png"

                # Select the node.
                usd_context.get_selection().set_selected_prim_paths([node.get_prim_path()], True)

                # Wait for property panel to converge
                await ui_test.human_delay(5)

                # Resize to fit the property panel, and take a snapshot
                await self.docked_test_window(
                    window=self._w._window,  # noqa: PLW0212
                    width=450,
                    height=500,
                    restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
                    restore_position=ui.DockPosition.BOTTOM,
                )

                await self.finalize_test(golden_img_dir=self._golden_img_dir, golden_img_name=test_img_name)

    # ----------------------------------------------------------------------

    async def test_extended_attributes(self):
        """
        Exercise the OG properties widget with extended attributes
        """
        usd_context = omni.usd.get_context()

        await self.docked_test_window(
            window=self._w._window,  # noqa: PLW0212
            width=450,
            height=500,
            restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
            restore_position=ui.DockPosition.BOTTOM,
        )

        keys = og.Controller.Keys
        controller = og.Controller()

        # OGN Types that we will test resolving the inputs:value to
        supported_types = [
            "half",
            "timecode",
            "half[]",
            "timecode[]",
            "double[2]",
            "double[3]",
            "double[4]",
            "double[2][]",
            "double[3][]",
            "double[4][]",
            "float[2]",
            "float[3]",
            "float[4]",
            "float[2][]",
            "float[3][]",
            "float[4][]",
            "half[2]",
            "half[3]",
            "half[4]",
            "half[2][]",
            "half[3][]",
            "half[4][]",
            "int[2]",
            "int[3]",
            "int[4]",
            "int[2][]",
            "int[3][]",
            "int[4][]",
            "matrixd[2]",
            "matrixd[3]",
            "matrixd[4]",
            "matrixd[2][]",
            "matrixd[3][]",
            "matrixd[4][]",
            "double",
            "double[]",
            "frame[4]",
            "frame[4][]",
            "quatd[4]",
            "quatf[4]",
            "quath[4]",
            "quatd[4][]",
            "quatf[4][]",
            "quath[4][]",
            "colord[3]",
            "colord[3][]",
            "colorf[3]",
            "colorf[3][]",
            "colorh[3]",
            "colorh[3][]",
            "colord[4]",
            "colord[4][]",
            "colorf[4]",
            "colorf[4][]",
            "colorh[4]",
            "colorh[4][]",
            "normald[3]",
            "normald[3][]",
            "normalf[3]",
            "normalf[3][]",
            "normalh[3]",
            "normalh[3][]",
            "pointd[3]",
            "pointd[3][]",
            "pointf[3]",
            "pointf[3][]",
            "pointh[3]",
            "pointh[3][]",
            "vectord[3]",
            "vectord[3][]",
            "vectorf[3]",
            "vectorf[3][]",
            "vectorh[3]",
            "vectorh[3][]",
            "texcoordd[2]",
            "texcoordd[2][]",
            "texcoordf[2]",
            "texcoordf[2][]",
            "texcoordh[2]",
            "texcoordh[2][]",
            "texcoordd[3]",
            "texcoordd[3][]",
            "texcoordf[3]",
            "texcoordf[3][]",
            "texcoordh[3]",
            "texcoordh[3][]",
            "string",
            "token[]",
            "token",
        ]

        attribute_names = [
            self.__attribute_type_to_name(og.AttributeType.type_from_ogn_type_name(type_name))
            for type_name in supported_types
        ]

        expected_values = [
            ogn.get_attribute_manager_type(type_name).sample_values()[0:2] for type_name in supported_types
        ]

        (graph, (_, write_node,), _, _) = controller.edit(
            self.TEST_GRAPH_PATH,
            {
                keys.CREATE_PRIMS: [
                    (
                        "/World/Prim",
                        {
                            attrib_name: (usd_type, expected_value[0])
                            for attrib_name, usd_type, expected_value in zip(
                                attribute_names, supported_types, expected_values
                            )
                        },
                    )
                ],
                keys.CREATE_NODES: [
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("Write", "omni.graph.nodes.WritePrimAttribute"),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "Write.inputs:execIn"),
                ],
                keys.SET_VALUES: [
                    ("Write.inputs:name", "acc"),
                    ("Write.inputs:primPath", "/World/Prim"),
                    ("Write.inputs:usePath", True),
                ],
            },
        )
        await controller.evaluate(graph)

        # Select the prim.
        usd_context.get_selection().set_selected_prim_paths([write_node.get_prim_path()], True)

        # The UI should refreshes every frame
        ogab.AUTO_REFRESH_PERIOD = 0

        # Test for attrib types that use OmniGraphAttributeValueModel
        async def test_numeric(name, value1, value2):
            controller.edit(self.TEST_GRAPH_PATH, {keys.SET_VALUES: [("Write.inputs:name", name)]})
            # Need to wait for an additional frames for omni.ui rebuild to take effect
            await ui_test.human_delay(2)
            for base in ogab.OmniGraphBase._instances:  # noqa: PLW0212
                if base._object_paths[0].name == "inputs:value" and (  # noqa: PLW0212
                    isinstance(base, (ogam.OmniGraphGfVecAttributeSingleChannelModel, ogam.OmniGraphAttributeModel))
                ):
                    base.begin_edit()
                    base.set_value(value1)
                    await ui_test.human_delay(1)
                    base.set_value(value2)
                    await ui_test.human_delay(1)
                    base.end_edit()
                    await ui_test.human_delay(1)
                    break

        # Test for attrib types that use ui.AbstractItemModel
        async def test_item(name, value1, value2):
            controller.edit(self.TEST_GRAPH_PATH, {keys.SET_VALUES: [("Write.inputs:name", name)]})
            # Need to wait for an additional frames for omni.ui rebuild to take effect
            await ui_test.human_delay(2)
            for base in ogab.OmniGraphBase._instances:  # noqa: PLW0212
                if base._object_paths[0].name == "inputs:value":  # noqa: PLW0212
                    base.begin_edit()
                    base.set_value(value1)
                    await ui_test.human_delay(1)
                    base.set_value(value2)
                    await ui_test.human_delay(1)
                    base.end_edit()
                    await ui_test.human_delay(1)
                    break

        # Test for read-only array value - just run the code, no need to verify anything
        async def test_array(name, val):
            controller.edit(self.TEST_GRAPH_PATH, {keys.SET_VALUES: [("Write.inputs:name", name)]})
            # Need to wait for an additional frames for omni.ui rebuild to take effect
            await ui_test.human_delay(2)

        for attrib_name, test_values in zip(attribute_names, expected_values):
            if attrib_name.endswith("_array"):
                await test_array(attrib_name, test_values[1])
            elif attrib_name in ("string", "token"):
                await test_item(attrib_name, test_values[1], test_values[0])
            else:
                # The set_value for some types take a component, others take the whole vector/matrix
                if isinstance(test_values[0], tuple) and not (
                    attrib_name.startswith("a_matrix")
                    or attrib_name.startswith("a_frame")
                    or attrib_name.startswith("a_quat")
                ):
                    await test_numeric(attrib_name, test_values[1][0], test_values[0][0])
                else:
                    await test_numeric(attrib_name, test_values[1], test_values[0])

        # Sanity check the final widget state display
        await self.finalize_test(golden_img_dir=self._golden_img_dir, golden_img_name="test_extended_attributes.png")

    async def test_extended_output_attributes(self):
        """
        Exercise the OG properties widget with extended attributes on read nodes
        """
        usd_context = omni.usd.get_context()

        await self.docked_test_window(
            window=self._w._window,  # noqa: PLW0212
            width=450,
            height=500,
            restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
            restore_position=ui.DockPosition.BOTTOM,
        )

        keys = og.Controller.Keys
        controller = og.Controller()

        (graph, (_, read_node, _,), _, _) = controller.edit(
            self.TEST_GRAPH_PATH,
            {
                keys.CREATE_PRIMS: [(("/World/Prim", {"a_token": ("token", "Ahsoka")}))],
                keys.CREATE_NODES: [
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("Read", "omni.graph.nodes.ReadPrimAttribute"),
                    ("Write", "omni.graph.nodes.WritePrimAttribute"),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "Write.inputs:execIn"),
                    ("Read.outputs:value", "Write.inputs:value"),
                ],
                keys.SET_VALUES: [
                    ("OnTick.inputs:onlyPlayback", False),
                    ("Read.inputs:name", "a_token"),
                    ("Read.inputs:primPath", "/World/Prim"),
                    ("Read.inputs:usePath", True),
                    ("Write.inputs:name", "a_token"),
                    ("Write.inputs:primPath", "/World/Prim"),
                    ("Write.inputs:usePath", True),
                ],
            },
        )
        await controller.evaluate(graph)

        # Select the prim.
        usd_context.get_selection().set_selected_prim_paths([read_node.get_prim_path()], True)
        await ui_test.human_delay(5)

        # The UI should refreshes every frame
        ogab.AUTO_REFRESH_PERIOD = 0

        # Sanity check the final widget state display
        await self.finalize_test(
            golden_img_dir=self._golden_img_dir, golden_img_name="test_extended_output_attributes.png"
        )

    async def test_layer_identifier_resolver(self):
        """
        Test layer identifier resolver using WritePrimsV2 node

        /root.usda
        /sub/sublayer.usda (as a sublayer of root.usda)

        The OG graph will be created on /sub/sublayer.usda with layer identifier set to "./sublayer.usda"

        Then open /root.usda to test the relative path is successfully resolved relative to root.usda instead
        """

        with tempfile.TemporaryDirectory() as tmpdirname:
            usd_context = omni.usd.get_context()
            controller = og.Controller()
            keys = og.Controller.Keys

            await self.docked_test_window(
                window=self._w._window,  # noqa: PLW0212
                width=450,
                height=500,
                restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
                restore_position=ui.DockPosition.BOTTOM,
            )

            sub_dir = os.path.join(tmpdirname, "sub")
            sublayer_fn = os.path.join(sub_dir, "sublayer.usda")
            sublayer = Sdf.Layer.CreateNew(sublayer_fn)
            sublayer.Save()

            root_fn = os.path.join(tmpdirname, "root.usda")
            root_layer = Sdf.Layer.CreateNew(root_fn)
            root_layer.subLayerPaths.append("./sub/sublayer.usda")
            root_layer.Save()

            success, error = await usd_context.open_stage_async(str(root_fn))
            self.assertTrue(success, error)

            stage = usd_context.get_stage()

            # put the graph on sublayer
            # only need WritePrimsV2 node for UI tests
            with Usd.EditContext(stage, sublayer):
                (_, [write_prims_node], _, _) = controller.edit(
                    self.TEST_GRAPH_PATH,
                    {
                        keys.CREATE_NODES: [
                            ("Write", "omni.graph.nodes.WritePrimsV2"),
                        ],
                        keys.SET_VALUES: [
                            ("Write.inputs:layerIdentifier", "./sublayer.usda"),
                        ],
                    },
                )

            # exit the "with" and switch edit target back to root layer
            usd_context.get_selection().set_selected_prim_paths([write_prims_node.get_prim_path()], True)
            await ui_test.human_delay(5)

            # Check the final widget state display
            # The "Layer Identifier" section should show "./sub/sublayer.usda" without any "<Invalid Layer>"" tag
            await self.finalize_test(
                golden_img_dir=self._golden_img_dir, golden_img_name="test_layer_identifier_resolver.png"
            )
