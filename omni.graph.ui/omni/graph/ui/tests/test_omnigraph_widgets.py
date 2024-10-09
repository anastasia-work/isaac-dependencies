# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import pathlib
from typing import List

import omni.kit.app
import omni.kit.commands
import omni.kit.test
import omni.ui as ui
from omni.kit import ui_test
from omni.kit.test_suite.helpers import get_test_data_path, wait_stage_loading
from omni.ui.tests.test_base import OmniUiTest


class TestOmniWidgets(OmniUiTest):
    """
    Test class for testing omnigraph related widgets
    """

    async def setUp(self):
        await super().setUp()

        usd_path = pathlib.Path(get_test_data_path(__name__))
        self._golden_img_dir = usd_path.absolute().joinpath("golden_img").absolute()
        self._usd_path = usd_path.absolute()

        import omni.kit.window.property as p

        self._w = p.get_window()

    async def tearDown(self):
        await super().tearDown()

    async def __widget_image_test(
        self,
        file_path: str,
        prims_to_select: List[str],
        golden_img_name: str,
        width=450,
        height=500,
    ):
        """Helper to do generate a widget comparison test on a property panel"""
        usd_context = omni.usd.get_context()

        await self.docked_test_window(
            window=self._w._window,  # noqa: PLE0211,PLW0212
            width=width,
            height=height,
            restore_window=ui.Workspace.get_window("Layer") or ui.Workspace.get_window("Stage"),
            restore_position=ui.DockPosition.BOTTOM,
        )

        test_file_path = self._usd_path.joinpath(file_path).absolute()
        await usd_context.open_stage_async(str(test_file_path))
        await wait_stage_loading()

        # Select the prim.
        usd_context.get_selection().set_selected_prim_paths(prims_to_select, True)

        # Need to wait for an additional frames for omni.ui rebuild to take effect
        await ui_test.human_delay(10)

        await self.finalize_test(golden_img_dir=self._golden_img_dir, golden_img_name=golden_img_name, threshold=0.15)

        # Close the stage to avoid dangling references to the graph. (OM-84680)
        await omni.usd.get_context().close_stage_async()

    async def test_compound_node_type_widget_ui(self):
        """Tests the compound node type property pane matches the expected image"""
        await self.__widget_image_test(
            file_path="compound_node_test.usda",
            prims_to_select=["/World/Compounds/TestCompound"],
            golden_img_name="test_compound_widget.png",
            height=600,
        )

    async def test_graph_with_variables_widget(self):
        """Tests the variable property pane on a graph prim"""
        await self.__widget_image_test(
            file_path="test_variables.usda",
            prims_to_select=["/World/ActionGraph"],
            golden_img_name="test_graph_variables.png",
            height=300,
        )

    async def test_instance_with_variables_widget(self):
        """Tests the variable property pane on an instance prim"""
        await self.__widget_image_test(
            file_path="test_variables.usda",
            prims_to_select=["/World/Instance"],
            golden_img_name="test_instance_variables.png",
            height=450,
        )
