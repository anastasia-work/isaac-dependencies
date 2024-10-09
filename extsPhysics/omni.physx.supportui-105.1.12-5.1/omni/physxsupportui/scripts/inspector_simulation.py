import asyncio
import weakref
from pxr import Tf, Usd
from typing import List
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModel
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModelState
from omni.physxsupportui import get_physx_supportui_private_interface
import omni.kit.undo


class InspectorSimulation:
    def __init__(self):
        super().__init__()
        self._delta_time = 1/60
        self.__usd_models : List[UsdAttributeModel] = []
        self.__ui_controls_to_disable = []
        self._undo_change_subs = omni.kit.undo.subscribe_on_change_detailed(self._on_kit_undo_change)
        self._sub_async_sim_run = None
        self._supportui_private = get_physx_supportui_private_interface()
        self._sub_model_event = self._supportui_private.get_inspector_event_stream().create_subscription_to_pop(self._on_inspector_event, name="Inspector Simulation")

    def _on_inspector_event(self, e):
        if type == PhysXInspectorModelState.DISABLED:
            self._enable_usd_notice_handlers(False)
        elif type == PhysXInspectorModelState.AUTHORING:
            self._enable_usd_notice_handlers(True)
        elif type == PhysXInspectorModelState.RUNNING_SIMULATION:
            self._enable_usd_notice_handlers(False)

    def clean(self):
        self.__ui_controls_to_disable = []
        self._clean_usd_models()
        self._supportui_private = None
        self._sub_async_sim_run = None
        self._sub_model_event = None
        omni.kit.undo.unsubscribe_on_change_detailed(self._on_kit_undo_change)
        self._undo_change_subs = None
        self.stop_authoring_simulation()

    def add_control_to_disable(self, control):
        self.__ui_controls_to_disable.append(weakref.ref(control))

    def add_usd_model(self, model : UsdAttributeModel):
        self.__usd_models.append(model)

    def remove_usd_model(self, model : UsdAttributeModel):
        if model in self.__usd_models:
            self.__usd_models.remove(model)

    def _on_kit_undo_change(self, cmds):
        try:
            cmd = cmds[0]
            if cmd.name == "ChangeProperty":
                path = cmd[1]['prop_path']
                if (path.name == "drive:angular:physics:targetPosition" or
                    path.name == "drive:linear:physics:targetPosition" or
                    path.name == "state:angular:physics:position" or
                    path.name == "state:linear:physics:position"
                    ):
                    self.start_authoring_simulation(time = 3)
        except:
            pass

    def _clean_usd_models(self):
        for model in self.__usd_models:
            model.clean()
        self.__usd_models = []

    def _enable_usd_notice_handlers(self, enable):
        if enable:
            omni.physxui.get_physicsui_instance().mouse_interaction_override_toggle(omni.physxui.PhysxUIMouseInteraction.DEFAULT)
        else:
            omni.physxui.get_physicsui_instance().mouse_interaction_override_toggle(omni.physxui.PhysxUIMouseInteraction.DISABLED)
        if enable:
            # When re-enabling, we force update to get latest values
            for model in self.__usd_models:
                model._set_dirty()
        to_remove = []
        for control_weak in self.__ui_controls_to_disable:
            control = control_weak()
            if control:
                control.enabled = enable
            else:
                to_remove.append(control_weak)
        for control_weak in to_remove:
            self.__ui_controls_to_disable.remove(control_weak)

        for model in self.__usd_models:
            if enable:
                if not model._listener:
                    model._listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, model._on_usd_changed, model._stage)
            else:
                if model._listener:
                    model._listener.Revoke()
                    model._listener = None
            # Alternative method could be to set this flag but we would still get the python callbacks
            # model._ignore_notice = not enable

    async def authoring_simulation_run(self):
        await asyncio.sleep(self._delta_time)
        self._enable_usd_notice_handlers(False)
        while True:
            if self._supportui_private is None:
                self.stop_authoring_simulation()
                await asyncio.sleep(self._delta_time)
            else:
                if self._supportui_private.get_inspector_state() != PhysXInspectorModelState.AUTHORING:
                    self.stop_authoring_simulation()
                    await asyncio.sleep(self._delta_time)
                self._supportui_private.step_inspector_simulation(self._delta_time)
                self._remaining_time = self._remaining_time - self._delta_time
                if self._remaining_time > 0:
                    await asyncio.sleep(self._delta_time)
                else:
                    self.stop_authoring_simulation()
                    await asyncio.sleep(self._delta_time)

    def start_authoring_simulation(self, time = 100):
        self._enable_usd_notice_handlers(False)
        self._remaining_time = time
        if self._sub_async_sim_run is None:
            self._sub_async_sim_run = asyncio.ensure_future(self.authoring_simulation_run())

    def stop_authoring_simulation(self):
        if self._sub_async_sim_run is not None:
            self._enable_usd_notice_handlers(True)
            self._sub_async_sim_run.cancel()
            self._sub_async_sim_run = None
