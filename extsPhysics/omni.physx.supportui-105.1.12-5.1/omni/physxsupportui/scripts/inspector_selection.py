import omni.ui as ui
import carb.settings
import omni.kit.app
import weakref
from pxr import Sdf
from omni.physxsupportui.bindings._physxSupportUi import PhysXInspectorModel

class InspectorSelectionHandler():
    def __init__(self, model_inspector : PhysXInspectorModel, inspector):
        self._model_inspector = model_inspector
        self._inspector = inspector
        self._settings = carb.settings.get_settings()
        self._last_selected_prim_paths = []
        self._selection = None
        self._ui_tree_views : set[ui.TreeView] = set()
        self._disable_selection_listening = False
        usdcontext = omni.usd.get_context()
        if usdcontext is not None:
            self._selection = usdcontext.get_selection()
            self._sub_stage_event = usdcontext.get_stage_event_stream().create_subscription_to_pop(self._on_stage_event, name="InspectorSelectionHandler")
    
    def clean(self):
        self._inspector = None
        self._model_inspector = None
        self._settings = None
        self._last_selected_prim_paths = None
        self._selection = None
        self._ui_tree_views : set[ui.TreeView] = set()
        self._selection = None
        self._sub_stage_event = None

    def add_tree_view(self, tree_view):
        self._ui_tree_views.add(weakref.ref(tree_view))
        # Setup initial selection
        selection = self._model_inspector.get_items_matching_paths(self._selection.get_selected_prim_paths())
        self._disable_selection_listening = True
        tree_view.selection = selection
        self._disable_selection_listening = False

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self.pull_view_selection_from_stage()

    def pull_view_selection_from_stage(self):
        if not len(self._ui_tree_views) or self._disable_selection_listening:
            return

        prim_paths = self._selection.get_selected_prim_paths()
        if prim_paths == self._last_selected_prim_paths:
            return

        self._last_selected_prim_paths = prim_paths
        self._disable_selection_listening = True
        selection = self._model_inspector.get_items_matching_paths(prim_paths)
        to_remove = []
        for weak_tree_view in self._ui_tree_views:
            tree_view = weak_tree_view()
            if tree_view:
                tree_view.selection = selection
                # TODO: we could implement "expand all parent nodes" leading to selected ones, similar to stage widget
            else:
                to_remove.append(weak_tree_view)
        for weak_tree_view in to_remove:
            self._ui_tree_views.remove(weak_tree_view)

        self._disable_selection_listening = False

    def push_view_selection_to_stage(self, selection, current_tree_view):
        if self._disable_selection_listening:
            return
        self._inspector.lock_all_inspector_windows()
        prim_paths = [self._model_inspector.get_item_value_model(item, 1).as_string 
                        for item in selection 
                            if (item and Sdf.Path.IsValidPathString(self._model_inspector.get_item_value_model(item, 1).as_string))]

        if prim_paths == self._last_selected_prim_paths:
            return

        self._last_selected_prim_paths = prim_paths
        
        self._disable_selection_listening = True
        for weak_tree_view in self._ui_tree_views:
            tree_view = weak_tree_view()
            if tree_view is not None and tree_view != current_tree_view:
                tree_view.selection = []
        self._selection.set_selected_prim_paths(prim_paths, False)
        self._disable_selection_listening = False
                