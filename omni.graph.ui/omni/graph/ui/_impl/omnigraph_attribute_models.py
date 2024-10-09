# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import copy
from typing import List

import omni.ui as ui
from omni.kit.property.usd.usd_attribute_model import FloatModel, IntModel
from pxr import Gf, Sdf, Tf, Usd

from .omnigraph_attribute_base import OmniGraphBase  # noqa: PLE0402

# =============================================================================


class OmniGraphAttributeModel(ui.AbstractValueModel, OmniGraphBase):
    """The value model that is reimplemented in Python to watch an OmniGraph attribute path"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=False,
        **kwargs,
    ):
        OmniGraphBase.__init__(self, stage, attribute_paths, self_refresh, metadata, change_on_edit_end, **kwargs)
        ui.AbstractValueModel.__init__(self)

    def clean(self):
        OmniGraphBase.clean(self)

    def begin_edit(self):
        OmniGraphBase.begin_edit(self)
        ui.AbstractValueModel.begin_edit(self)

    def end_edit(self):
        OmniGraphBase.end_edit(self)
        ui.AbstractValueModel.end_edit(self)

    def get_value_as_string(self, elide_big_array=True) -> str:
        self._update_value()
        if self._value is None:
            return ""
        if self._is_big_array and elide_big_array:
            return "[...]"
        return str(self._value)

    def get_value_as_float(self) -> float:
        self._update_value()
        if self._value is None:
            return 0.0

        if hasattr(self._value, "__len__"):
            return float(self._value[self._channel_index])
        return float(self._value)

    def get_value_as_bool(self) -> bool:
        self._update_value()
        if self._value is None:
            return False

        if hasattr(self._value, "__len__"):
            return bool(self._value[self._channel_index])
        return bool(self._value)

    def get_value_as_int(self) -> int:
        self._update_value()
        if self._value is None:
            return 0

        if hasattr(self._value, "__len__"):
            return int(self._value[self._channel_index])
        return int(self._value)

    def set_value(self, value):  # noqa: PLW0221  FIXME: reconcile with base class calls
        if OmniGraphBase.set_value(self, value):
            self._value_changed()

    def _on_dirty(self):
        self._value_changed()  # AbstractValueModel


# =============================================================================
# OmniGraph Attribute Models need to use OmniGraphBase for their super class state rather than UsdBase

# -----------------------------------------------------------------------------


class OmniGraphTfTokenAttributeModel(ui.AbstractItemModel, OmniGraphBase):
    class AllowedTokenItem(ui.AbstractItem):
        def __init__(self, item):
            super().__init__()
            self.token = item
            self.model = ui.SimpleStringModel(item)

    def __init__(self, stage: Usd.Stage, attribute_paths: List[Sdf.Path], self_refresh: bool, metadata: dict):
        OmniGraphBase.__init__(self, stage, attribute_paths, self_refresh, metadata)
        ui.AbstractItemModel.__init__(self)

        self._allowed_tokens = []

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(self._current_index_changed)

        self._updating_value = False

        self._has_index = False
        self._update_value()
        self._has_index = True

    def clean(self):
        OmniGraphBase.clean(self)

    def get_item_children(self, item):
        self._update_value()
        return self._allowed_tokens

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index

        return item.model

    def begin_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        OmniGraphBase.begin_edit(self)

    def end_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        OmniGraphBase.end_edit(self)

    def _current_index_changed(self, model):
        if not self._has_index:
            return

        # if we're updating from USD notice change to UI, don't call set_value
        if self._updating_value:
            return

        index = model.as_int
        if self.set_value(self._allowed_tokens[index].token):
            self._item_changed(None)

    def _get_allowed_tokens(self, attr):
        return attr.GetMetadata("allowedTokens")

    def _update_allowed_token(self, token_item=AllowedTokenItem):
        self._allowed_tokens = []

        # For multi prim editing, the allowedTokens should all be the same
        attributes = self._get_attributes()
        attr = attributes[0] if len(attributes) > 0 else None
        if attr:
            for t in self._get_allowed_tokens(attr):
                self._allowed_tokens.append(token_item(t))

    def _update_value(self, force=False):
        was_updating_value = self._updating_value
        self._updating_value = True
        if OmniGraphBase._update_value(self, force):
            # TODO don't have to do this every time. Just needed when "allowedTokens" actually changed
            self._update_allowed_token()

            index = self._update_index()
            if index not in (-1, self._current_index.as_int):
                self._current_index.set_value(index)
                self._item_changed(None)
        self._updating_value = was_updating_value

    def _on_dirty(self):
        self._item_changed(None)

    def _update_index(self):
        index = -1
        for i, allowed_token in enumerate(self._allowed_tokens):
            if allowed_token.token == self._value:
                index = i
        return index

    def get_value_as_token(self):
        index = self._current_index.as_int
        return self._allowed_tokens[index].token

    def is_allowed_token(self, token):
        return token in [allowed.token for allowed in self._allowed_tokens]


# -----------------------------------------------------------------------------


class OmniGraphGfVecAttributeModel(ui.AbstractItemModel, OmniGraphBase):
    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        comp_count: int,
        tf_type: Tf.Type,
        self_refresh: bool,
        metadata: dict,
        **kwargs,
    ):
        OmniGraphBase.__init__(self, stage, attribute_paths, self_refresh, metadata, **kwargs)
        ui.AbstractItemModel.__init__(self)
        self._comp_count = comp_count
        self._data_type_name = "Vec" + str(self._comp_count) + tf_type.typeName[-1]
        self._data_type = getattr(Gf, self._data_type_name)

        class UsdVectorItem(ui.AbstractItem):
            def __init__(self, model):
                super().__init__()
                self.model = model

        # Create root model
        self._root_model = ui.SimpleIntModel()
        self._root_model.add_value_changed_fn(lambda a: self._item_changed(None))

        # Create three models per component
        if self._data_type_name.endswith("i"):
            self._items = [UsdVectorItem(IntModel(self)) for i in range(self._comp_count)]
        else:
            self._items = [UsdVectorItem(FloatModel(self)) for i in range(self._comp_count)]
        for item in self._items:
            item.model.add_value_changed_fn(lambda a, item=item: self._on_value_changed(item))

        self._edit_mode_counter = 0

    def clean(self):
        OmniGraphBase.clean(self)

    def _construct_vector_from_item(self):
        if self._data_type_name.endswith("i"):
            data = [item.model.get_value_as_int() for item in self._items]
        else:
            data = [item.model.get_value_as_float() for item in self._items]
        return self._data_type(data)

    def _on_value_changed(self, item):
        """Called when the submodel is changed"""

        if self._edit_mode_counter > 0:
            vector = self._construct_vector_from_item()
            index = self._items.index(item)
            if vector and self.set_value(vector, index):
                # Read the new value back in case hard range clamped it
                item.model.set_value(self._value[index])
                self._item_changed(item)
            else:
                # If failed to update value in model, revert the value in submodel
                item.model.set_value(self._value[index])

    def _update_value(self, force=False):
        if OmniGraphBase._update_value(self, force):
            if self._value is None:
                for i in range(len(self._items)):  # noqa: PLC0200
                    self._items[i].model.set_value(0.0)
                return
            for i in range(len(self._items)):  # noqa: PLC0200
                self._items[i].model.set_value(self._value[i])

    def _on_dirty(self):
        self._item_changed(None)

    def get_item_children(self, item):
        """Reimplemented from the base class"""
        self._update_value()
        return self._items

    def get_item_value_model(self, item, column_id):
        """Reimplemented from the base class"""
        if item is None:
            return self._root_model
        return item.model

    def begin_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user starts editing.
        """
        self._edit_mode_counter += 1
        OmniGraphBase.begin_edit(self)

    def end_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user finishes editing.
        """
        OmniGraphBase.end_edit(self)
        self._edit_mode_counter -= 1


# -----------------------------------------------------------------------------


class OmniGraphGfVecAttributeSingleChannelModel(OmniGraphAttributeModel):
    """Specialize version of GfVecAttributeSingleChannelModel"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        channel_index: int,
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=False,
        **kwargs,
    ):
        self._channel_index = channel_index
        super().__init__(stage, attribute_paths, self_refresh, metadata, change_on_edit_end, **kwargs)

    def get_value_as_string(self, **kwargs) -> str:  # noqa: PLW0221  FIXME: reconcile with base class calls
        self._update_value()
        if self._value is None:
            return ""

        return str(self._value[self._channel_index])

    def get_value_as_float(self) -> float:
        self._update_value()
        if self._value is None:
            return 0.0

        if hasattr(self._value, "__len__"):
            return float(self._value[self._channel_index])
        return float(self._value)

    def get_value_as_bool(self) -> bool:
        self._update_value()
        if self._value is None:
            return False

        if hasattr(self._value, "__len__"):
            return bool(self._value[self._channel_index])
        return bool(self._value)

    def get_value_as_int(self) -> int:
        self._update_value()
        if self._value is None:
            return 0

        if hasattr(self._value, "__len__"):
            return int(self._value[self._channel_index])
        return int(self._value)

    def set_value(self, value):
        if self._real_type is None:
            # FIXME: This Attribute does not have a corresponding OG attribute
            return
        vec_value = copy.copy(self._value)
        vec_value[self._channel_index] = value

        # Skip over our base class impl, because that is specialized for scaler
        if OmniGraphBase.set_value(self, vec_value, self._channel_index):
            self._value_changed()

    def is_different_from_default(self):
        """Override to only check channel"""
        if super().is_different_from_default() and self._channel_index < len(self._comp_different_from_default):
            return self._comp_different_from_default[self._channel_index]
        return False


# -----------------------------------------------------------------------------


class OmniGraphGfQuatAttributeModel(ui.AbstractItemModel, OmniGraphBase):
    def __init__(
        self, stage: Usd.Stage, attribute_paths: List[Sdf.Path], tf_type: Tf.Type, self_refresh: bool, metadata: dict
    ):
        OmniGraphBase.__init__(self, stage, attribute_paths, self_refresh, metadata)
        ui.AbstractItemModel.__init__(self)
        data_type_name = "Quat" + tf_type.typeName[-1]
        self._data_type = getattr(Gf, data_type_name)

        class UsdQuatItem(ui.AbstractItem):
            def __init__(self, model):
                super().__init__()
                self.model = model

        # Create root model
        self._root_model = ui.SimpleIntModel()
        self._root_model.add_value_changed_fn(lambda a: self._item_changed(None))

        # Create four models per component
        self._items = [UsdQuatItem(FloatModel(self)) for i in range(4)]
        for item in self._items:
            item.model.add_value_changed_fn(lambda a, item=item: self._on_value_changed(item))

        self._edit_mode_counter = 0

    def clean(self):
        OmniGraphBase.clean(self)

    def _on_value_changed(self, item):
        """Called when the submodel is chaged"""
        if self._edit_mode_counter > 0:
            quat = self._construct_quat_from_item()
            if quat and self.set_value(quat, self._items.index(item)):
                self._item_changed(item)

    def _update_value(self, force=False):
        if OmniGraphBase._update_value(self, force):
            for i in range(len(self._items)):  # noqa: PLC0200
                if i == 0:
                    self._items[i].model.set_value(self._value.real)
                else:
                    self._items[i].model.set_value(self._value.imaginary[i - 1])

    def _on_dirty(self):
        self._item_changed(None)

    def get_item_children(self, item):
        """Reimplemented from the base class"""
        self._update_value()
        return self._items

    def get_item_value_model(self, item, column_id):
        """Reimplemented from the base class"""
        if item is None:
            return self._root_model
        return item.model

    def begin_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user starts editing.
        """
        self._edit_mode_counter += 1
        OmniGraphBase.begin_edit(self)

    def end_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user finishes editing.
        """
        OmniGraphBase.end_edit(self)
        self._edit_mode_counter -= 1

    def _construct_quat_from_item(self):
        data = [item.model.get_value_as_float() for item in self._items]

        return self._data_type(data[0], data[1], data[2], data[3])


# -----------------------------------------------------------------------------


class OmniGraphGfMatrixAttributeModel(ui.AbstractItemModel, OmniGraphBase):
    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        comp_count: int,
        tf_type: Tf.Type,
        self_refresh: bool,
        metadata: dict,
    ):
        OmniGraphBase.__init__(self, stage, attribute_paths, self_refresh, metadata)
        ui.AbstractItemModel.__init__(self)
        self._comp_count = comp_count
        data_type_name = "Matrix" + str(self._comp_count) + tf_type.typeName[-1]
        self._data_type = getattr(Gf, data_type_name)

        class UsdMatrixItem(ui.AbstractItem):
            def __init__(self, model):
                super().__init__()
                self.model = model

        # Create root model
        self._root_model = ui.SimpleIntModel()
        self._root_model.add_value_changed_fn(lambda a: self._item_changed(None))

        # Create three models per component
        self._items = [UsdMatrixItem(FloatModel(self)) for i in range(self._comp_count * self._comp_count)]
        for item in self._items:
            item.model.add_value_changed_fn(lambda a, item=item: self._on_value_changed(item))

        self._edit_mode_counter = 0

    def clean(self):
        OmniGraphBase.clean(self)

    def _on_value_changed(self, item):
        """Called when the submodel is chaged"""

        if self._edit_mode_counter > 0:
            matrix = self._construct_matrix_from_item()
            if matrix and self.set_value(matrix, self._items.index(item)):
                self._item_changed(item)

    def _update_value(self, force=False):
        if OmniGraphBase._update_value(self, force):
            for i in range(len(self._items)):  # noqa: PLC0200
                self._items[i].model.set_value(self._value[i // self._comp_count][i % self._comp_count])  # noqa: S001

    def _on_dirty(self):
        self._item_changed(None)
        # it's still better to call _value_changed for all child items
        for child in self._items:
            child.model._value_changed()  # noqa: PLW0212

    def get_item_children(self, item):
        """Reimplemented from the base class."""
        self._update_value()
        return self._items

    def get_item_value_model(self, item, column_id):
        """Reimplemented from the base class."""
        if item is None:
            return self._root_model
        return item.model

    def begin_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user starts editing.
        """
        self._edit_mode_counter += 1
        OmniGraphBase.begin_edit(self)

    def end_edit(self, item):  # noqa: PLW0221  FIXME: reconcile with base class calls
        """
        Reimplemented from the base class.
        Called when the user finishes editing.
        """
        OmniGraphBase.end_edit(self)
        self._edit_mode_counter -= 1

    def _construct_matrix_from_item(self):
        data = [item.model.get_value_as_float() for item in self._items]
        matrix = []
        for i in range(self._comp_count):
            matrix_row = []
            for j in range(self._comp_count):
                matrix_row.append(data[i * self._comp_count + j])
            matrix.append(matrix_row)
        return self._data_type(matrix)


# -----------------------------------------------------------------------------


class OmniGraphSdfTimeCodeModel(OmniGraphAttributeModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prev_real_values = None

    def _save_real_values_as_prev(self):
        # SdfTimeCode cannot be inited from another SdfTimeCode, only from float (double in C++)..
        self._prev_real_values = [Sdf.TimeCode(float(value)) for value in self._real_values]


# -----------------------------------------------------------------------------


class OmniGraphTfTokenNoAllowedTokensModel(OmniGraphAttributeModel):
    """Model for token attributes that are actually file-paths. This is a workaround for OG lack of `asset` type"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=True,  # We don't want continuous updates on tokens
        **kwargs,
    ):
        super().__init__(stage, attribute_paths, self_refresh, metadata, change_on_edit_end, **kwargs)

    def get_resolved_path(self) -> str:
        """This method exists on SdfAssetPathAttributeModel, but since we aren't an "asset", we are just providing it.
        See `show_asset_file_picker`
        """
        # Note: This is only called in the context of the file picker, so we don't need to verify our attribute type
        # IE: customData { uiType="filePath" }
        val = self.get_value_as_string()
        layer = self._stage.GetEditTarget().GetLayer()
        if layer:
            val = layer.ComputeAbsolutePath(val)
        return str(val)

    def is_valid_path(self) -> bool:
        """This method exists on SdfAssetPathAttributeModel, but since we aren't an "asset", we are just providing it."""
        return bool(self.get_value_as_string())


# -----------------------------------------------------------------------------


class OmniGraphStringAttributeModel(OmniGraphAttributeModel):
    """Model for string attributes, only exists to turn off change_on_edit_end"""

    def __init__(
        self,
        stage: Usd.Stage,
        attribute_paths: List[Sdf.Path],
        self_refresh: bool,
        metadata: dict,
        change_on_edit_end=True,  # We don't want continuous updates on strings
        **kwargs,
    ):
        super().__init__(stage, attribute_paths, self_refresh, metadata, change_on_edit_end, **kwargs)
