"""
Common functions used by all of the OmniGraph Node Editor implementation classes

Exports:
    Callback
    callback_name
    ComboBoxOptions
    DestructibleButton
    FileCallback
    FileCallbackNested
    find_unique_name
    ghost_int
    ghost_text
    OptionalCallback
    PatternedStringModel
    set_widget_visible
    show_wip
    SubscriptionManager
"""
import asyncio
import os
from typing import Callable, Dict, Optional, Tuple

import omni.graph.tools as ogt
from carb import log_warn
from omni import ui
from omni.kit.app import get_app
from omni.kit.ui import get_custom_glyph_code

from ..style import STYLE_GHOST, name_value_label  # noqa: PLE0402

# Imports from other places that look like they are coming from here
from ..utils import DestructibleButton  # noqa

# ======================================================================
OGN_WIP = os.getenv("OGN_WIP")


def show_wip() -> bool:
    """Returns True if work in progress should be visible"""
    return OGN_WIP


# ======================================================================
# Glyph paths
GLYPH_EXCLAMATION = f'{get_custom_glyph_code("${glyphs}/exclamation.svg")}'


# ======================================================================
# Default values for initializing new data
OGN_NEW_NODE_NAME = "NewNode"
OGN_DEFAULT_CONTENT = {OGN_NEW_NODE_NAME: {"version": 1, "description": "", "language": "Python"}}


# ======================================================================
# Typing information for callback functions
Callback = Callable[[], None]
OptionalCallback = [None, Callable[[], None]]
FileCallback = [None, Callable[[str], None]]
FileCallbackNested = [None, Callable[[str, Optional[Callable]], None]]


# ======================================================================
def callback_name(job: Callable):
    """Return a string representing the possible None callback function"""
    return "No callback" if job is None else f"callback - {job.__name__}"


# ======================================================================
def find_unique_name(base_name: str, names_taken: Dict):
    """Returns the base_name with a suffix that guarantees it does not appear as a key in the names_taken
    find_unique_name("fred", ["fred": "flintsone", "fred0": "mercury"]) -> "fred1"
    """
    if base_name not in names_taken:
        return base_name
    index = 0
    while f"{base_name}{index}" in names_taken:
        index += 1
    return f"{base_name}{index}"


# =====================================================================
def set_widget_visible(widget: ui.Widget, visible) -> bool:
    """
    Utility for using in lambdas, changes the visibility of a widget.
    Returns True so that it can be combined with other functions in a lambda:
        lambda m: set_widget_visible(widget, not m.as_string) and callback(m.as_string)
    """
    widget.visible = visible
    return True


# ======================================================================
class GhostedWidgetInfo:
    """Container for the UI information pertaining to text with ghosted prompt text

    Attributes:
        begin_subscription: Subscription for callback when editing begins
        end_subscription: Subscription for callback when editing ends
        model: Main editing model
        prompt_widget: Widget that is layered above the main one to show the ghosted prompt text
        widget: Main editing widget
    """

    def __init__(self):
        """Initialize the members"""
        self.begin_subscription = None
        self.end_subscription = None
        self.widget = None
        self.prompt_widget = None
        self.model = None


# ======================================================================
def ghost_text(
    label: str,
    tooltip: str,
    widget_id: str,
    initial_value: str,
    ghosted_text: str,
    change_callback: Optional[Callable],
    validation: Optional[Tuple[Callable, str]] = None,
) -> GhostedWidgetInfo:
    """
    Creates a Label/StringField value entry pair with ghost text to prompt the user when the field is empty.

    Args:
        label: Text for the label of the field
        tooltip: Tooltip for the label
        widget_id: Base ID for the string entry widget (append "_prompt" for the ghost prompt overlay)
        initial_value: Initial value for the string field
        ghosted_text: Text to appear when the string is empty
        change_callback: Function to call when the string changes
        validation: Optional function and string pattern used to check if the entered string is valid
        (no validation if None)

    Returns:
        4-tuple (subscription, model, widget, prompt_widget)
            subscription: Subscription object for active callback
            model: The model managing the editable string
            widget: The widget containing the editable string
            prompt_widget: The widget containing the overlay shown when the string is empty
    """
    prompt_widget_id = f"{widget_id}_prompt"
    name_value_label(label, tooltip)
    ghost_info = GhostedWidgetInfo()
    if validation is None:
        ghost_info.model = ui.SimpleStringModel(initial_value)
    else:
        ghost_info.model = ValidatedStringModel(initial_value, validation[0], validation[1])

    def ghost_edit_begin(model, label_widget):
        """Called to hide the prompt label"""
        label_widget.visible = False

    def ghost_edit_end(model, label_widget, callback):
        """Called to show the prompt label and process the field edit"""
        if not model.as_string:
            label_widget.visible = True
        if callback is not None:
            callback(model.as_string)

    with ui.ZStack(height=0):
        ghost_info.widget = ui.StringField(model=ghost_info.model, name=widget_id, tooltip=tooltip)

        # Add a ghosted input prompt that only shows up when the attribute name is empty
        ghost_info.prompt_widget = ui.Label(
            ghosted_text, name=prompt_widget_id, style_type_name_override=STYLE_GHOST, visible=not initial_value
        )

        ghost_info.begin_subscription = ghost_info.model.subscribe_begin_edit_fn(
            lambda model, widget=ghost_info.prompt_widget: ghost_edit_begin(model, widget)
        )
        ghost_info.end_subscription = ghost_info.model.subscribe_end_edit_fn(
            lambda model: ghost_edit_end(model, ghost_info.prompt_widget, change_callback)
        )

    if label:
        ghost_info.prompt_widget.visible = False

    return ghost_info


# ======================================================================
def ghost_int(
    label: str, tooltip: str, widget_id: str, initial_value: int, ghosted_text: str, change_callback: Optional[Callable]
) -> GhostedWidgetInfo:
    """
    Creates a Label/IntField value entry pair with ghost text to prompt the user when the field is empty.

    Args:
        label: Text for the label of the field
        tooltip: Tooltip for the label
        widget_id: Base ID for the integer entry widget (append "_prompt" for the ghost prompt overlay)
        initial_value: Initial value for the integer field
        ghosted_text: Text to appear when the integer is empty
        change_callback: Function to call when the integer changes

    Returns:
        4-tuple (subscription, model, widget, prompt_widget)
            subscription: Subscription object for active callback
            model: The model managing the editable integer
            widget: The widget containing the editable integer
            prompt_widget: The widget containing the overlay shown when the integer is empty
    """
    ghost_info = GhostedWidgetInfo()
    prompt_widget_id = f"{widget_id}_prompt"
    name_value_label(label, tooltip)
    ghost_info.model = ui.SimpleIntModel(initial_value)

    def ghost_edit_begin(model, label_widget):
        """Called to hide the prompt label"""
        label_widget.visible = False

    def ghost_edit_end(model, label_widget, callback):
        """Called to show the prompt label and process the field edit"""
        if not model.as_string:
            label_widget.visible = True
        if callback is not None:
            callback(model.as_int)

    with ui.ZStack(height=0):
        ghost_info.widget = ui.IntField(model=ghost_info.model, name=widget_id, tooltip=tooltip)

        # Add a ghosted input prompt that only shows up when the value is empty
        ghost_info.prompt_widget = ui.Label(
            ghosted_text, name=prompt_widget_id, style_type_name_override=STYLE_GHOST, visible=not initial_value
        )
        ghost_info.begin_subscription = ghost_info.model.subscribe_begin_edit_fn(
            lambda model, widget=ghost_info.prompt_widget: ghost_edit_begin(model, widget)
        )
        ghost_info.end_subscription = ghost_info.model.subscribe_end_edit_fn(
            lambda model: ghost_edit_end(model, ghost_info.prompt_widget, change_callback)
        )

    return ghost_info


# ======================================================================
class ComboBoxOptions(ui.AbstractItem):
    """Class that provides a conversion from simple text to a StringModel to use in ComboBox options"""

    def __init__(self, text: str):
        """Initialize the internal model to the string"""
        super().__init__()
        self.model = ui.SimpleStringModel(text)

    def destroy(self):
        """Called when the combobox option is being destroyed"""
        ogt.dbg_ui(f"destroy::{self.__class__.__name__}")
        self.model = None


# ======================================================================
class SubscriptionManager:
    """Class that manages an AbstractValueModel subscription callback, allowing enabling and disabling.

    One potential use is to temporarily disable subscriptions when a change is being made in a callback that
    might recursively trigger that same callback.

    class ChangeMe:
        def __init__(self, model):
            self.model = model
            self.mgr = SubscriptionManager(model, SubscriptionManager.CHANGE, on_change)
        def on_change(self, new_value):
            if new_value.as_int > 5:
                # Resetting the value to clamp it to a range would recursively trigger this callback so shut it off
                self.mgr.disable()
                self.model.set_value(5)
                self.mgr.enable()
    """

    # Enumeration of the different types of subscriptions available
    CHANGE = 0
    BEGIN_EDIT = 1
    END_EDIT = 2
    # Model functions corresponding to the above subscription types
    FUNCTION_NAMES = ["subscribe_value_changed_fn", "subscribe_begin_edit_fn", "subscribe_end_edit_fn"]

    # ----------------------------------------------------------------------
    def __init__(self, model: ui.AbstractValueModel, subscription_type: int, callback: callable):
        """Create an initial subscription to a model change"""
        ogt.dbg_ui(f"Create subscription manager on {model} of type {subscription_type} for callback {callback}")
        self.__model = model
        self.__subscription_type = subscription_type
        self.__callback = callback
        self.__subscription = None
        # On creation the subscription will be activated
        self.enable()

    # ----------------------------------------------------------------------
    async def __do_enable(self):
        """Turn on the subscription of the given type"""
        ogt.dbg_ui("__do_enable")
        await get_app().next_update_async()
        try:
            self.__subscription = getattr(self.__model, self.FUNCTION_NAMES[self.__subscription_type])(self.__callback)
            assert self.__subscription
        except (KeyError, AttributeError, TypeError) as error:
            log_warn(f"Failed to create subscription type {self.__subscription_type} on {self.__model} - {error}")

    # ----------------------------------------------------------------------
    def enable(self):
        """Turn on the subscription of the given type, syncing first to make sure no pending updates exist"""
        ogt.dbg_ui("Enable")
        asyncio.ensure_future(self.__do_enable())

    # ----------------------------------------------------------------------
    def disable(self):
        """Turn off the subscription of the given type"""
        ogt.dbg_ui("Disable")
        self.__subscription = None


# ======================================================================
class ValidatedStringModel(ui.AbstractValueModel):
    """String model that insists the values entered match a certain pattern"""

    def __init__(self, initial_value: str, verify: Callable[[str], bool], explanation: str):
        """Initialize the legal values of the string, and human-readable explanation of the pattern

        Args:
            initial_value: Initial value of the string, nulled out if it is not legal
            verify: Function to call to check for validity of the string
            explanation: Human readable explanation of the RegEx
        """
        super().__init__()
        self.__verify = verify
        self.__explanation = explanation
        self.__value = ""
        self.__initial_value = None
        self.set_value(initial_value)

    def get_value_as_string(self):
        """Get the internal value that has been filtered"""
        ogt.dbg_ui(f"Get value as string = {self.__value}")
        return self.__value

    def set_value(self, new_value):
        """Implementation of the value setting that filters new values based on the pattern

        Args:
            new_value: Potential new value of the string
        """
        self.__value = str(new_value)
        self._value_changed()

    def begin_edit(self):
        """Called when the user starts editing."""
        self.__initial_value = self.get_value_as_string()

    def end_edit(self):
        """Called when the user finishes editing."""
        new_value = self.get_value_as_string()
        if not self.__verify(new_value):
            self.__value = self.__initial_value
            self._value_changed()
            log_warn(f"'{new_value}' is not legal - {self.__explanation.format(new_value)}")
