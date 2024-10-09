# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb.settings
import omni.ui as ui
from omni.kit.widget.settings.deprecated import SettingType
from omni.kit.window.preferences import PERSISTENT_SETTINGS_PREFIX, PreferenceBuilder

SETTING_PAGE_NAME = "Visual Scripting"


class OmniGraphSettingsEditor(PreferenceBuilder):
    def __init__(self):
        super().__init__(SETTING_PAGE_NAME)
        self._settings = carb.settings.get_settings()

    def destroy(self):
        self._settings = None

    def build(self):
        """Updates"""
        with ui.VStack(height=0):
            with self.add_frame("Update Settings"):
                with ui.VStack():
                    self.create_setting_widget(
                        "Update mesh points to Hydra",
                        f"{PERSISTENT_SETTINGS_PREFIX}/omnigraph/updateMeshPointsToHydra",
                        SettingType.BOOL,
                        tooltip="When this setting is enabled, mesh points will be not be written back to USD",
                    )
                    self.create_setting_widget(
                        "Default graph evaluator",
                        f"{PERSISTENT_SETTINGS_PREFIX}/omnigraph/defaultEvaluator",
                        SettingType.STRING,
                        tooltip="The evaluator to use for new Graphs when not specified",
                    )
                    self.create_setting_widget(
                        "Enable deprecated Node.pathChanged callback",
                        f"{PERSISTENT_SETTINGS_PREFIX}/omnigraph/enablePathChangedCallback",
                        SettingType.BOOL,
                        tooltip="(deprecated) - When this setting is enabled the callback is enabled"
                        " which will affect performance.",
                    )
                    self.create_setting_widget(
                        "Escalate all deprecation warnings to be errors",
                        f"{PERSISTENT_SETTINGS_PREFIX}/omnigraph/deprecationsAreErrors",
                        SettingType.BOOL,
                        tooltip="When this setting is enabled any deprecation warnings that a code path"
                        " encounters are escalated to log errors in C++ or raise exceptions in Python. This"
                        " provides a preview of what needs to be fixed when hard deprecation of a code path happens.",
                    )
                    self.create_setting_widget(
                        "Enable auto instancing",
                        f"{PERSISTENT_SETTINGS_PREFIX}/omnigraph/autoInstancingEnabled",
                        SettingType.BOOL,
                        tooltip="When this setting is enabled, similar graph will be merged together as instances,"
                        " which will allow their computation to happen in a vectorized way."
                        " This global setting is used to initialize all newly created graph,"
                        " but this behavior can also be controlled on a per graph basis using the ABI",
                    )
