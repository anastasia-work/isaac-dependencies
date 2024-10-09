from omni.physxtestsvisual.utils import TestCase
from omni.physxtests.utils.physicsBase import TestCategory
import omni.usd
import omni.physxdemos as demo
import carb
import omni.physx
import omni.kit.test
import unittest
import os


class BlockworldVisualTest(TestCase):
    category = TestCategory.Core

    async def setUp(self):
        self._assets_loaded = False

        def _on_stage_event(event):
            if event.type == int(omni.usd.StageEventType.ASSETS_LOADED):
                print("Completed loading of stage assets.")
                self._assets_loaded = True
            elif event.type == int(omni.usd.StageEventType.ASSETS_LOADING):
                print("Assets are loading.")
            elif event.type == int(omni.usd.StageEventType.ASSETS_LOAD_ABORTED):
                print("Asset load aborted.")

        print("Subscribing to stage event.")
        stage_event_stream = omni.usd.get_context().get_stage_event_stream()
        self._stage_event_sub = stage_event_stream.create_subscription_to_pop(_on_stage_event)

    async def tearDown(self):
        self._stage_event_sub = None

    async def wait_for_assets(self):
        wait_repeats = 600
        for _ in range(0, wait_repeats):
            await self.wait(10)
            if self._assets_loaded:
                break

        if not self._assets_loaded:
            carb.log_warn("Failed to load stage assets.")

    # main visual test (backup non-visual test below)
    @unittest.skipUnless(os.name == "nt", "visual test, flaky on linux")
    async def test_blockworld_visual(self):
        res = False

        async def do_prepare(_):
            await self.setup_viewport_test()

        async def do_test(_):
            await self.wait_for_assets()
            self.assertTrue(self._assets_loaded)

            await self.step(200, stop_timeline_after=False)
            nonlocal res
            res = await self.do_visual_test(
                img_name="",
                img_suffix="_test_physics_visual_blockworld",
                use_distant_light=False,
                skip_assert=True,
                threshold=0.0025
            )

        await demo.test("omni.blockworld", do_prepare, do_test)
        self.assertTrue(res)

    # backup non-visual test that just loads the level and tries to simulate it to check for errors
    # disable when the above visual test is not skipped
    @unittest.skipIf(os.name == "nt", "backup test, replacement on linux")
    async def test_blockworld(self):
        async def do_test(_):
            await self.wait_for_assets()
            await self.step(20)

        await demo.test("omni.blockworld", after_stage_async_fn=do_test)
