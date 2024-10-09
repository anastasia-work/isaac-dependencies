import weakref
from functools import partial
from typing import Callable

import omni.ui as ui
from omni.kit.property.usd.relationship import SelectionWatch
from omni.kit.widget.stage import StageWidget
from pxr import Sdf, Usd


class StagePickerDialog:
    def __init__(
        self,
        stage,
        on_select_fn: Callable[[Usd.Prim], None],
        title=None,
        select_button_text=None,
        filter_type_list=None,
        filter_lambda=None,
    ):
        self._weak_stage = weakref.ref(stage)
        self._on_select_fn = on_select_fn

        if filter_type_list is None:
            self._filter_type_list = []
        else:
            self._filter_type_list = filter_type_list

        self._filter_lambda = filter_lambda
        self._selected_paths = []

        def on_window_visibility_changed(visible):
            if not visible:
                self._stage_widget.open_stage(None)
            else:
                # Only attach the stage when picker is open. Otherwise the Tf notice listener in StageWidget kills perf
                self._stage_widget.open_stage(self._weak_stage())

        self._window = ui.Window(
            title if title else "Select Prim",
            width=600,
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

                def on_select(weak_self):
                    weak_self = weak_self()
                    if not weak_self:
                        return

                    selected_prim = None
                    if len(weak_self._selected_paths) > 0:  # noqa: PLW0212
                        selected_prim = stage.GetPrimAtPath(Sdf.Path(weak_self._selected_paths[0]))  # noqa: PLW0212

                    if weak_self._on_select_fn:  # noqa: PLW0212
                        weak_self._on_select_fn(selected_prim)  # noqa: PLW0212

                    weak_self._window.visible = False  # noqa: PLW0212

                with ui.VStack(height=0, style={"Button.Label:disabled": {"color": 0xFF606060}}):
                    self._label = ui.Label("Selected Path(s):\n\tNone")
                    self._button = ui.Button(
                        select_button_text if select_button_text else "Select",
                        height=10,
                        clicked_fn=partial(on_select, weak_self=weakref.ref(self)),
                        enabled=False,
                    )

    def clean(self):
        self._window.set_visibility_changed_fn(None)
        self._window.destroy()
        self._window = None
        self._selection_watch = None
        self._stage_widget.open_stage(None)
        self._stage_widget.destroy()
        self._stage_widget = None
        self._filter_type_list = None
        self._filter_lambda = None
        self._selected_paths = None
        self._on_select_fn = None
        self._weak_stage = None
        self._label.destroy()
        self._label = None
        self._button.destroy()
        self._button = None

    def show(self):
        self._selection_watch.reset(1)
        self._window.visible = True
        if self._filter_lambda is not None:
            self._stage_widget._filter_by_lambda({"relpicker_filter": self._filter_lambda}, True)  # noqa: PLW0212
        if self._filter_type_list:
            self._stage_widget._filter_by_type(self._filter_type_list, True)  # noqa: PLW0212
            self._stage_widget.update_filter_menu_state(self._filter_type_list)

    def hide(self):
        self._window.visible = False

    def _on_selection_changed(self, paths):
        self._selected_paths = paths
        if self._button:
            self._button.enabled = len(self._selected_paths) > 0
        if self._label:
            text = "\n\t".join(self._selected_paths)
            label_text = "Selected Path"
            label_text += f":\n\t{text if text else 'None'}"
            self._label.text = label_text
