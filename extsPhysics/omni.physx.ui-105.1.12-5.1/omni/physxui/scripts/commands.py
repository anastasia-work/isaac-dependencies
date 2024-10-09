from omni.kit.usd_undo import UsdLayerUndo
import omni.kit.commands
from .physxDebugView import remove_schema


class ClearPhysicsComponentsCommand(omni.kit.commands.Command):
    def __init__(self, stage, prim_paths):
        self._stage = stage
        self._prim_paths = prim_paths
        self._usd_undo = None

    def do(self):
        self._usd_undo = UsdLayerUndo(self._stage.GetEditTarget().GetLayer())
        for prim_path in self._prim_paths:
            self._usd_undo.reserve(prim_path)
        remove_schema(True, True, self._stage, self._prim_paths)
        return True

    def undo(self):
        self._usd_undo.undo()
