"""pybind11 omni.physx.cooking bindings"""
from __future__ import annotations
import omni.physxcooking.bindings._physxCooking
import typing

__all__ = [
    "PhysxCookingServicePrivate",
    "acquire_physx_cooking_service_private",
    "release_physx_cooking_service_private",
    "release_physx_cooking_service_private_scripting"
]


class PhysxCookingServicePrivate():
    pass
def acquire_physx_cooking_service_private(plugin_name: str = None, library_path: str = None) -> PhysxCookingServicePrivate:
    pass
def release_physx_cooking_service_private(arg0: PhysxCookingServicePrivate) -> None:
    pass
def release_physx_cooking_service_private_scripting(arg0: PhysxCookingServicePrivate) -> None:
    pass
