import weakref
from functools import partial
from typing import List, Tuple, Union

import omni.ui as ui
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel
from omni.kit.property.usd.usd_property_widget_builder import UsdPropertiesWidgetBuilder
from pxr import Sdf, Vt

from .omnigraph_attribute_base import get_model_cls  # noqa: PLE0402


class TokenArrayModel(ui.AbstractItemModel):
    """Model for handling the token array drop down menu"""

    class AllowedTokenItem(ui.AbstractItem):
        def __init__(self, item):
            super().__init__()
            self.token = item
            self.model = ui.SimpleStringModel(item)

    def __init__(
        self, model: ui.AbstractItemModel, index: int, allowed_tokens: Union[List[str], List[Tuple[str, str]]]
    ):
        ui.AbstractItemModel.__init__(self)
        self._model = model
        self._index = index  # index into the token array

        # if it's a list of strings, the tokens are used as is.
        if isinstance(allowed_tokens[0], str):
            self._allowed_tokens = [TokenArrayModel.AllowedTokenItem(token) for token in allowed_tokens]
            self._actual_tokens = allowed_tokens
        # if it's a list of tuples, the first item is the displayed value, the second is the actual value
        elif isinstance(allowed_tokens[1], tuple):
            self._allowed_tokens = [TokenArrayModel.AllowedTokenItem(token[0]) for token in allowed_tokens]
            self._actual_tokens = [token[1] for token in allowed_tokens]
        else:
            raise TypeError("allowed_tokens must be a list of strings or list of string pairs")

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(self._current_index_changed)
        current = self._get_value_from_model()

        # set the current item
        if self._is_actual_token(current):
            self._current_index.set_value(self._get_item_index(current))
        else:
            self._allowed_tokens.insert(0, TokenArrayModel.AllowedTokenItem(current))
            self._actual_tokens.insert(0, current)
            self._current_index.set_value(0)

    def get_item_children(self, item):
        return self._allowed_tokens

    def _current_index_changed(self, model):
        """Called when the current selection is changed"""
        self._update_value()

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model

    def get_value_as_token(self):
        index = self._current_index.as_int
        return self._allowed_tokens[index].token

    def is_allowed_token(self, token):
        """Checks if a display token is valid"""
        return token in [allowed.token for allowed in self._allowed_tokens]

    def _is_actual_token(self, token):
        """Checks if an actual token is listed"""
        return token in self._actual_tokens

    def _get_value_from_model(self):
        """Gets the current value of the model"""
        # The model returns the tokens as list
        items = [item.strip() for item in self._model.get_value_as_string()[1:-1].split(",")]
        if self._index < len(items):
            return items[self._index]
        return ""

    def _get_item_index(self, item: str):
        """Get the index of the actual token"""
        return self._actual_tokens.index(item)

    def _update_value(self):
        new_value = self._actual_tokens[self._current_index.as_int]
        items = [item.strip() for item in self._model.get_value_as_string()[1:-1].split(",")]
        if self._index < len(items) and items[self._index] != new_value:
            items[self._index] = new_value
            self._model.set_value(Vt.TokenArray(items))
            self._item_changed(None)


class TokenArrayEditWidget:
    """Custom widget for editing token arrays"""

    def __init__(self, stage, attr_name, prim_paths, metadata, additional_widget_kwargs):
        model_cls = get_model_cls(UsdAttributeModel, additional_widget_kwargs)
        self._model = model_cls(stage, [path.AppendProperty(attr_name) for path in prim_paths], False, metadata)
        self._metadata = metadata
        self._token_array_attrs = [stage.GetPrimAtPath(path).GetAttribute(attr_name) for path in prim_paths]
        self._additional_widget_kwargs = additional_widget_kwargs
        self._enabled = self._additional_widget_kwargs.get("enabled", True) if self._additional_widget_kwargs else True
        self._frame = ui.Frame()
        self._frame.set_build_fn(self._build)

    def clean(self):
        self._model.clean()
        self._frame = None

    def _build_remove_button(self, index: int):
        """Draw the remove button at the end of the item"""

        def on_remove_element(weak_self, index):
            weak_self = weak_self()
            if weak_self:
                token_array = list(weak_self._token_array_attrs[0].Get())  # noqa: PLW0212
                token_array.pop(index)
                weak_self._model.set_value(Vt.TokenArray(token_array))  # noqa: PLW0212

        ui.Button(
            "-",
            width=ui.Pixel(14),
            clicked_fn=partial(on_remove_element, weak_self=weakref.ref(self), index=index),
            enable=self._enabled,
        )

    def _build_combo_style_view(self, shared_tokens, allowed_tokens):
        """Build a combo box style view"""
        widget_kwargs = {"name": "choices"}
        if self._additional_widget_kwargs is not None:
            widget_kwargs.update(self._additional_widget_kwargs)
        for i, _ in enumerate(shared_tokens):
            with ui.HStack(spacing=2):
                combo_model = TokenArrayModel(self._model, i, allowed_tokens)
                ui.ComboBox(combo_model, **widget_kwargs)
                self._build_remove_button(i)

    def _build_list_style_view(self, shared_tokens):
        """Build a list style view using simple string entry"""
        for i, token in enumerate(shared_tokens):
            with ui.HStack(spacing=2):
                token_model = ui.StringField(name="models").model
                token_model.set_value(token)

                def on_edit_element(value_model, weak_self, index):
                    weak_self = weak_self()
                    if weak_self:
                        token_array = list(weak_self._token_array_attrs[0].Get())  # noqa: PLW0212
                        token_array[index] = value_model.as_string
                        weak_self._model.set_value(Vt.TokenArray(token_array))  # noqa: PLW0212

                token_model.add_end_edit_fn(partial(on_edit_element, weak_self=weakref.ref(self), index=i))
                self._build_remove_button(i)

    def _build(self):
        shared_tokens = None

        for attr in self._token_array_attrs:
            if attr.HasValue():
                tokens = list(attr.Get())
            else:
                tokens = []

            if shared_tokens is None:
                shared_tokens = tokens
            elif shared_tokens != tokens:
                shared_tokens = None
                break

        allowed_tokens = None
        if self._additional_widget_kwargs is not None:
            allowed_tokens = self._additional_widget_kwargs.get("allowed_tokens", None)

        with ui.VStack(spacing=2):
            if shared_tokens is not None:
                if allowed_tokens is not None and len(allowed_tokens) > 0:
                    self._build_combo_style_view(shared_tokens, allowed_tokens)
                else:
                    self._build_list_style_view(shared_tokens)

                def on_add_element(weak_self):
                    weak_self = weak_self()
                    if weak_self:
                        token_array_attr = weak_self._token_array_attrs[0]  # noqa: PLW0212
                        if token_array_attr.HasValue():
                            token_array = list(token_array_attr.Get())
                        else:
                            token_array = []

                        token_array.append("")
                        weak_self._model.set_value(Vt.TokenArray(token_array))  # noqa: PLW0212

                ui.Button(
                    "Add Element",
                    width=ui.Pixel(30),
                    clicked_fn=partial(on_add_element, weak_self=weakref.ref(self)),
                    enabled=self._enabled,
                )
            else:
                ui.StringField(name="models", read_only=True).model.set_value("Mixed")

    def _set_dirty(self):
        self._frame.rebuild()


def build_token_array_prop(
    stage,
    attr_name,
    metadata,
    property_type,
    prim_paths: List[Sdf.Path],
    additional_label_kwargs=None,
    additional_widget_kwargs=None,
):
    with ui.HStack(spacing=4):
        UsdPropertiesWidgetBuilder._create_label(attr_name, metadata, additional_label_kwargs)  # noqa: PLW0212
        return TokenArrayEditWidget(stage, attr_name, prim_paths, metadata, additional_widget_kwargs)
