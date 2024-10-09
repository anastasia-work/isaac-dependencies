.. _omni_physx_cct_OgnControlsSettings_2:

.. _omni_physx_cct_OgnControlsSettings:

.. ================================================================================
.. THIS PAGE IS AUTO-GENERATED. DO NOT MANUALLY EDIT.
.. ================================================================================

:orphan:

.. meta::
    :title: Controls Settings
    :keywords: lang-en omnigraph node Physx Character Controller cct ogn-controls-settings


Controls Settings
=================

.. <description>

Setup control rebinds and settings for the Character Controller

.. </description>


Installation
------------

To use this node enable :ref:`omni.physx.cct<ext_omni_physx_cct>` in the Extension Manager.


Inputs
------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "Move Backward (*inputs:backward*)", "``token``", "Move Backward", "S"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""
    "Move Down (*inputs:down*)", "``token``", "Move Down", "Q"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""
    "Move Forward (*inputs:forward*)", "``token``", "Move Forward", "W"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""
    "Sensitivity - Gamepad (*inputs:gamepadSensitivity*)", "``float``", "Gamepad Sensitivity Multiplier", "25"
    "Move Left (*inputs:left*)", "``token``", "Move Left", "A"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""
    "Sensitivity - Mouse (*inputs:mouseSensitivity*)", "``float``", "Mouse Sensitivity Multiplier", "25"
    "Move Right (*inputs:right*)", "``token``", "Move Right", "D"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""
    "Move Up or Jump (*inputs:up*)", "``token``", "Move Up or Jump (depending if gravity is enabled for this Character Controller)", "E"
    "", "*allowedTokens*", "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,Apostrophe,Backslash,Backspace,CapsLock,Comma,Del,Down,End,Enter,Equal,Escape,F1,F10,F11,F12,F2,F3,F4,F5,F6,F7,F8,F9,GraveAccent,Home,Insert,Key0,Key1,Key2,Key3,Key4,Key5,Key6,Key7,Key8,Key9,Left,LeftAlt,LeftBracket,LeftControl,LeftShift,LeftSuper,Menu,Minus,NumLock,Numpad0,Numpad1,Numpad2,Numpad3,Numpad4,Numpad5,Numpad6,Numpad7,Numpad8,Numpad9,NumpadAdd,NumpadDel,NumpadDivide,NumpadEnter,NumpadEqual,NumpadMultiply,NumpadSubtract,PageDown,PageUp,Pause,Period,PrintScreen,Right,RightAlt,RightBracket,RightControl,RightShift,RightSuper,ScrollLock,Semicolon,Slash,Space,Tab,Up", ""


Outputs
-------
.. csv-table::
    :header: "Name", "Type", "Descripton", "Default"
    :widths: 20, 20, 50, 10

    "outputs:control_settings", "``bundle``", "Bundle with control settings to connect to the Character Controller node's Controls Settings input.", "None"


Metadata
--------
.. csv-table::
    :header: "Name", "Value"
    :widths: 30,70

    "Unique ID", "omni.physx.cct.OgnControlsSettings"
    "Version", "2"
    "Extension", "omni.physx.cct"
    "Has State?", "False"
    "Implementation Language", "Python"
    "Default Memory Type", "cpu"
    "Generated Code Exclusions", "None"
    "uiName", "Controls Settings"
    "Categories", "Physx Character Controller"
    "Generated Class Name", "OgnControlsSettingsDatabase"
    "Python Module", "omni.physxcct"

