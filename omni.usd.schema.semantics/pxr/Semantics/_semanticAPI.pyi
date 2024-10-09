from __future__ import annotations
import pxr.Semantics._semanticAPI
import typing
import Boost.Python
import pxr.Usd

__all__ = [
    "SemanticsAPI"
]


class SemanticsAPI(pxr.Usd.APISchemaBase, pxr.Usd.SchemaBase, Boost.Python.instance):
    @staticmethod
    def Apply(*args, **kwargs) -> None: ...
    @staticmethod
    def CanApply(*args, **kwargs) -> None: ...
    @staticmethod
    def CreateSemanticDataAttr(*args, **kwargs) -> None: ...
    @staticmethod
    def CreateSemanticTypeAttr(*args, **kwargs) -> None: ...
    @staticmethod
    def Get(*args, **kwargs) -> None: ...
    @staticmethod
    def GetAll(*args, **kwargs) -> None: ...
    @staticmethod
    def GetSchemaAttributeNames(*args, **kwargs) -> None: ...
    @staticmethod
    def GetSemanticDataAttr(*args, **kwargs) -> None: ...
    @staticmethod
    def GetSemanticTypeAttr(*args, **kwargs) -> None: ...
    @staticmethod
    def IsSemanticsAPIPath(*args, **kwargs) -> None: ...
    @staticmethod
    def _GetStaticTfType(*args, **kwargs) -> None: ...
    __instance_size__ = 48
    pass
class _CanApplyResult(Boost.Python.instance):
    @property
    def whyNot(self) -> None:
        """
        :type: None
        """
    __instance_size__ = 56
    pass
__MFB_FULL_PACKAGE_NAME = 'semanticAPI'
