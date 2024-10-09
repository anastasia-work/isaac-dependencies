# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import weakref
from functools import partial

import omni.ui as ui
from omni.graph.core import INSTANCING_GRAPH_TARGET_PATH
from omni.kit.property.usd.relationship import (
    RelationshipTargetPicker,
    SdfRelationshipArraySingleEntryModel,
    SelectionWatch,
)
from omni.kit.widget.stage import StageWidget

# =============================================================================


class OmniGraphTargetPicker(RelationshipTargetPicker):
    """A modified version of omni.kit.property.usd.RelationshipTargetPicker for OmniGraph target inputs. We need
    to provide a way to select the path "." in addition to selecting existing prims"""

    def __init__(self, stage, filter_type_list, filter_lambda, additional_widget_kwargs):
        self._weak_stage = weakref.ref(stage)
        self._filter_lambda = filter_lambda
        self._selected_paths = []
        self._filter_type_list = filter_type_list
        self._on_targets_selected = None
        self._additional_widget_kwargs = additional_widget_kwargs if additional_widget_kwargs else {}
        self._target_name = additional_widget_kwargs.get("target_name", "Target")
        self._target_plural_name = additional_widget_kwargs.get("target_plural_name", "Targets")

        def on_window_visibility_changed(visible):
            if not visible:
                self._stage_widget.open_stage(None)
            else:
                # Only attach the stage when picker is open. Otherwise the Tf notice listener in StageWidget kills perf
                self._stage_widget.open_stage(self._weak_stage())

        def _on_select_graph_target(weak_self) -> None:
            """Pressing the graph target button overrides whatever other selection they have made"""
            weak_self = weak_self()
            if not weak_self:
                return
            weak_self._on_targets_selected([INSTANCING_GRAPH_TARGET_PATH])  # noqa: PLW0212
            weak_self._window.visible = False  # noqa: PLW0212

        self._window = ui.Window(
            f"Select {self._target_plural_name}",
            width=400,
            height=400,
            visible=False,
            flags=0,
            visibility_changed_fn=on_window_visibility_changed,
        )
        with self._window.frame:
            with ui.VStack():
                with ui.Frame():
                    self._stage_widget = StageWidget(None, columns_enabled=["Type"])
                    self._selection_watch = SelectionWatch(
                        stage=stage,
                        on_selection_changed_fn=self._on_selection_changed,
                        filter_type_list=filter_type_list,
                        filter_lambda=filter_lambda,
                    )
                    self._stage_widget.set_selection_watch(self._selection_watch)

                with ui.VStack(
                    height=0, style={"Button.Label:disabled": {"color": 0xFF606060}}
                ):  # TODO consolidate all styles
                    with ui.HStack():
                        self._graph_target_checkbox = ui.Button(
                            "Select Graph Target Prim",
                            height=10,
                            clicked_fn=partial(_on_select_graph_target, weak_self=weakref.ref(self)),
                            identifier="select_graph_target",
                            tooltip=f"For OmniGraph instancing: Set the target to be the prim which is the target of instancing ({INSTANCING_GRAPH_TARGET_PATH})",
                        )
                    self._label = ui.Label(f"Selected {self._target_name}:\n\tNone")
                    self._button = ui.Button(
                        "Select",
                        height=10,
                        clicked_fn=partial(OmniGraphTargetPicker._on_select, weak_self=weakref.ref(self)),
                        enabled=False,
                        identifier="select_button",
                    )


# -------------------------------------------------------------------------


class OmniGraphSdfRelationshipArraySingleEntryModel(SdfRelationshipArraySingleEntryModel):
    def get_value_as_string(self):
        """override to show paths relative to instancing token"""
        path = self._paths[0]
        prim_path = path.GetPrimPath()
        relationships = self._stage.GetPrimAtPath(prim_path).GetRelationship(path.name)
        if relationships:
            targets = relationships.GetTargets()
            if self.index < len(targets):
                target_path = targets[self.index]
                if target_path.HasPrefix(prim_path):
                    return str(target_path.MakeRelativePath(prim_path))
                return str(targets[self.index])
        return ""
