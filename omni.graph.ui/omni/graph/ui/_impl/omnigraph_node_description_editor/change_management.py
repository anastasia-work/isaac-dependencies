"""
Collection of classes to use for managing reactions to changes to models
"""
from typing import Callable, List, Optional, Union

import omni.graph.tools as ogt


# ======================================================================
class ChangeMessage:
    """Message packet to send when a change is encountered.

    Created as a class so that other messages can override it and add more information.

    External Properties:
        caller: Object that triggered the change
    """

    def __init__(self, caller):
        """Set up the basic message information"""
        self.caller = caller

    def __str__(self) -> str:
        """Return a string with the contents of the message"""
        return str(self.caller.__class__.__name__)


# ================================================================================
class RenameMessage(ChangeMessage):
    """Encapsulation of a message sent when an attribute name changes"""

    def __init__(self, caller, old_name: str, new_name: str):
        """Set up a message with information needed to indicate a name change"""
        super().__init__(caller)
        self.old_name = old_name
        self.new_name = new_name

    def __str__(self) -> str:
        """Returns a human-readable representation of the name change information"""
        caller_info = super().__str__()
        return f"Name change {self.old_name} -> {self.new_name} (from {caller_info})"


# ======================================================================
class ChangeManager:
    """Base class to provide the ability to set and react to value changes

    External Properties:
        callback_forwarders: List of change manager whose callbacks are also to be executed
        change_callbacks: List of callbacks to invoke when a change happens
    """

    def __init__(self, change_callbacks: Optional[Union[List, Callable]] = None):
        """Initialize the callback list"""
        self.change_callbacks = []
        self.callback_forwarders = []
        if change_callbacks is not None:
            self.add_change_callback(change_callbacks)

    def destroy(self):
        """Called when the manager is being destroyed, usually from the derived class's destroy"""
        self.change_callbacks = []
        self.callback_forwarders = []

    # ----------------------------------------------------------------------
    def on_change(self, change_message=None):
        """Called when the controller has modified some data"""
        ogt.dbg_ui(f"on_change({change_message})")
        message = ChangeMessage(self) if change_message is None else change_message
        # By passing in the caller we facilitate more intelligent responses with callback sharing
        for callback in self.change_callbacks:
            callback(message)
        # Call all of the forwarded change callbacks as well, specifying this manager as the initiator
        message.caller = self
        for callback_forwarder in self.callback_forwarders:
            ogt.dbg_ui(f"...forwarding change to {callback_forwarder.__class__.__name__}")
            callback_forwarder.on_change(message)

    # ----------------------------------------------------------------------
    def add_change_callback(self, callback: Union[Callable, List[Callable]]):
        """Add a function to be called when the controller modifies some data"""
        if isinstance(callback, list):
            self.change_callbacks = callback
        elif isinstance(callback, Callable):
            self.change_callbacks.append(callback)

    # ----------------------------------------------------------------------
    def remove_change_callback(self, callback: Callable):
        """Remove a function to be called when the controller modifies some data"""
        try:
            if isinstance(callback, list):
                _ = [self.remove_change_callback(child) for child in callback]
            else:
                self.change_callbacks.remove(callback)
        except ValueError:
            ogt.dbg_ui(f"Tried to remove non-existent callback {callback.name}")

    # ----------------------------------------------------------------------
    def forward_callbacks_to(self, parent_manager):
        """Set the callbacks on this change manager to include those existing on the parent

        This is done lazily so that any new callbacks added later will also be handled.

        Args:
            parent_manager: ChangeManager whose callbacks are also to be executed by this manager
        """
        self.callback_forwarders.append(parent_manager)
