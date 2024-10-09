"""Support for the toolkit widget that shows OmniGraph-related timing for all extensions.

The output is a dictionary of extension timing information with a legend:

.. code-block:: json

    {
        "Extension Processing Timing": {
            "legend": {
                "Key": "Extension ID",
                "Value": [
                    "Registration Of Python Nodes",
                    "Deregistration Of Python Nodes"
                ]
            },
            "timing": {
                "omni.graph.examples.python": [
                    12345,
                    12367
                ]
            }
        }
    }

"""
import json
from contextlib import suppress
from typing import Callable

import omni.graph.core as og
import omni.graph.tools as ogt

from ...style import BUTTON_WIDTH
from ...utils import DestructibleButton

__all__ = ["ToolkitWidgetExtensionTiming"]


# ==============================================================================================================
class ToolkitWidgetExtensionTiming:
    ID = "DumpExtensionTiming"
    LABEL = "Extension Processing Timing"
    TOOLTIP = "Dump information on timing of per-extension operations initiated by OmniGraph"
    RESULTS_TOOLTIP = "Timing information of per-extension operations initiated by OmniGraph - see 'legend' for details"

    # ----------------------------------------------------------------------
    def __init__(self, set_output_callback: Callable):
        self.__button = None
        self.__set_output = set_output_callback

    # ----------------------------------------------------------------------
    def destroy(self):
        """Called when the widgets are being deleted to provide clean removal and prevent leaks"""
        ogt.destroy_property(self, "__button")
        ogt.destroy_property(self, "__set_output")

    # ----------------------------------------------------------------------
    def build(self):
        """Build the UI section with the functionality to dump the extension information"""
        self.__button = DestructibleButton(
            self.LABEL,
            name=self.ID,
            width=BUTTON_WIDTH,
            tooltip=self.TOOLTIP,
            clicked_fn=self.__on_click,
        )
        assert self.__button

    # --------------------------------------------------------------------------------------------------------------
    def __on_click(self):
        """Callback executed when the Extensions All button is clicked"""
        try:
            ext_info = og._PublicExtension  # noqa: PLW0212
            ext_ids = set(ext_info.REGISTRATION_TIMING.keys()).union(set(ext_info.DEREGISTRATION_TIMING.keys()))
            extension_timing_information = {}
            for ext_id in ext_ids:
                registration_timing = None
                deregistration_timing = None
                with suppress(KeyError):
                    registration_timing = ext_info.REGISTRATION_TIMING[ext_id] / 1_000_000.0
                with suppress(KeyError):
                    deregistration_timing = ext_info.DEREGISTRATION_TIMING[ext_id] / 1_000_000.0
                extension_timing_information[ext_id] = [registration_timing, deregistration_timing]
            text = json.dumps(
                {
                    self.LABEL: {
                        "legend": {
                            "Key": "Extension ID",
                            "Value": ["Registration Of Python Nodes (ms)", "Deregistration Of Python Nodes (ms)"],
                        },
                        "timing": extension_timing_information,
                    }
                },
                indent=4,
            )
        except Exception as error:  # pylint: disable=broad-except
            text = str(error)
        self.__set_output(text, self.RESULTS_TOOLTIP)
