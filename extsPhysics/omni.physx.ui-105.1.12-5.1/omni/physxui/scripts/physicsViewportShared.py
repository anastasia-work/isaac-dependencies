from pxr import Gf
import carb
from omni.ui_scene import scene as sc
from omni.ui import color as cl
import math
from math import isinf, isnan

MAIN_LINE_THICKNESS = 2.0
HOVER_LINE_THICKNESS = 3.5

# This color is useful for when wanting to have shapes invisible yet still react to gestures, like for hovering.
COLOR_INVISIBLE = cl("#00000000")
COLOR_HIGHLIGHT = cl("#FFFF66FF")

AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2
AXIS_NUM = 3

AXIS_DIRECTION_X_POS = AXIS_X * 2
AXIS_DIRECTION_X_NEG = AXIS_X * 2 + 1
AXIS_DIRECTION_Y_POS = AXIS_Y * 2
AXIS_DIRECTION_Y_NEG = AXIS_Y * 2 + 1
AXIS_DIRECTION_Z_POS = AXIS_Z * 2
AXIS_DIRECTION_Z_NEG = AXIS_Z * 2 + 1
AXIS_DIRECTION_NUM = 6

AXIS_VECTOR_X = Gf.Vec3f(1.0, 0.0, 0.0)
AXIS_VECTOR_Y = Gf.Vec3f(0.0, 1.0, 0.0)
AXIS_VECTOR_Z = Gf.Vec3f(0.0, 0.0, 1.0)
AXIS_VECTOR = [AXIS_VECTOR_X, AXIS_VECTOR_Y, AXIS_VECTOR_Z]

COLOR_AXIS = [cl("#FF4444FF"), cl("#22DD22FF"), cl("#4466FFFF")] # Roughly matches luma values between channels.
COLOR_AXIS_SHADED = [cl("#D93A3AFF"), cl("#1DBC1DFF"), cl("#3A57D9FF")] # Darker variant.

BOX_CORNER_X_POS_Y_POS_Z_POS = 0
BOX_CORNER_X_POS_Y_POS_Z_NEG = 1
BOX_CORNER_X_POS_Y_NEG_Z_POS = 2
BOX_CORNER_X_POS_Y_NEG_Z_NEG = 3
BOX_CORNER_X_NEG_Y_POS_Z_POS = 4
BOX_CORNER_X_NEG_Y_POS_Z_NEG = 5
BOX_CORNER_X_NEG_Y_NEG_Z_POS = 6
BOX_CORNER_X_NEG_Y_NEG_Z_NEG = 7
BOX_CORNER_NUM = 8

g_active_hover = None
g_active_gesture = None

def get_active_gesture():
    global g_active_gesture
    return g_active_gesture

def set_active_gesture(gesture):
    global g_active_gesture
    g_active_gesture = gesture

def get_active_hover():
    global g_active_hover
    return g_active_hover

def set_active_hover(hover):
    global g_active_hover
    g_active_hover = hover

FLOAT_EPSILON = 1.0e-16

def sqr(value):
    return value * value

def float_to_string(value, max_decimals = 8):
    if value is None or not isinstance(value, float):
        return "-"
    elif isnan(value):
        return "NaN"
    elif isinf(value):
        if value > 0.0:
            return "Inf"
        else:
            return "-Inf"
    elif value == 0.0:
        # Prevents -0.0 output.
        value = 0.0
        decimals = 1
    else:
        decimals = 1
        limit = 10.0
        abs_value = math.fabs(value)
        while(abs_value < limit and decimals < max_decimals):
            decimals += 1
            limit *= 0.1

    return ("{:,."+str(decimals)+"f}").format(value)

def direction_to_axis(direction):
    return int(direction / 2)

def axis_angle_to_quaternion(axis, angle):
    return Gf.Quatf(math.cos(angle / 2), axis * math.sin(angle / 2))

def axis_to_string(axis):
    if axis == AXIS_X:
        return "X"
    if axis == AXIS_Y:
        return "Y"
    if axis == AXIS_Z:
        return "Z"
    return ""

class PhysicsGestureManager(sc.GestureManager):
    def __init__(self, viewport_overlay):
        super().__init__()
        self._viewport_overlay = viewport_overlay

    def should_prevent(self, gesture, preventer):
        if ((gesture.state == sc.GestureState.POSSIBLE or gesture.state == sc.GestureState.BEGAN or gesture.state == sc.GestureState.CHANGED)):

            active_hover = get_active_hover()
            active_gesture = get_active_gesture()

            if not isinstance(gesture, PhysicsDragGesture) and not isinstance(gesture, PhysicsHoverGesture):
                if active_gesture or active_hover:
                    return True
                else:
                    return False

            if active_gesture:
                if active_gesture == gesture:
                    return False
                else:
                    return True

            # If we are hovering a gesture and the manipulator or toggle group differs, prevent.
            if active_hover:
                if (active_hover._manipulator != gesture._manipulator or 
                                active_hover._toggle_group != gesture._toggle_group):
                    return True
                else:
                    return False

        # This seem to block all gestures (?)
        # return super().should_prevent(gesture, preventer)
        return False 

class VisualToggle():
    def __init__(self, ui_toggle_object):
        self._ui_object = ui_toggle_object

    def toggle(self, enabled):
        pass

class VisibilityToggle(VisualToggle):
    def __init__(self, ui_toggle_object):
        super().__init__(ui_toggle_object)
        self._ui_object.visible = False

    def toggle(self, enabled):
        super().toggle(enabled)
        self._ui_object.visible = enabled

class ImageToggle(VisualToggle):
    def __init__(self, ui_toggle_object, enabled_image, disabled_image):
        super().__init__(ui_toggle_object)
        self._enabled_image = enabled_image
        self._disabled_image = disabled_image
        self._ui_object.source_url = disabled_image

    def toggle(self, enabled):
        super().toggle(enabled)
        self._ui_object.source_url = self._enabled_image if enabled else self._disabled_image

class ColorToggle(VisualToggle):
    def __init__(self, ui_toggle_object, enabled_color, disabled_color = COLOR_INVISIBLE):
        super().__init__(ui_toggle_object)
        self._enabled_color = enabled_color
        self._disabled_color = disabled_color
        self._ui_object.color = disabled_color

    def toggle(self, enabled):
        super().toggle(enabled)
        self._ui_object.color = self._enabled_color if enabled else self._disabled_color

# Just a shorthand for ColorToggle with the shared highlight color.
class HighlightToggle(ColorToggle):
    def __init__(self, ui_toggle_object):
        super().__init__(ui_toggle_object, COLOR_HIGHLIGHT)

# Handles hover toggle for view toggle. If subgroup is not -1, it only toggles members of this subgroup. Otherwise
# it toggles members of the general toggle group.
class PhysicsHoverGesture(sc.HoverGesture):
    def __init__(self, manipulator, toggle_group):
        self._manipulator = manipulator
        self._toggle_group = toggle_group
        super().__init__(manager=manipulator.get_viewport_overlay().get_gesture_manager())

    def on_began(self):
        set_active_hover(self)
        self._manipulator.refresh()

    def on_changed(self):
        pass

    def on_ended(self):
        if get_active_hover() == self:
            set_active_hover(None)
        self._manipulator.refresh()

class PhysicsDragGesture(sc.DragGesture):
    def __init__(self, manipulator):
        super().__init__(manager=manipulator.get_viewport_overlay().get_gesture_manager())
        self._manipulator = manipulator
        self._toggle_group = None
        self._gesture = None

    def on_began(self):
        set_active_gesture(self)
        self._manipulator.refresh()

    def on_changed(self):
        pass

    def on_ended(self):
        if get_active_gesture() == self:
            set_active_gesture(None)
        self._manipulator.refresh()

class PhysicsManipulator(sc.Manipulator):
    def __init__(self, viewport_overlay):
        super().__init__()
        self._viewport_overlay = viewport_overlay
        self._toggle_groups = []

    def get_viewport_overlay(self):
        return self._viewport_overlay

    def add_to_toggles(self, item, group = 0):
        if group < 0 or not isinstance(group, int):
            carb.log_error(f"Fatal error - invalid visual toggle group: {group}")
        while len(self._toggle_groups) <= group:
            self._toggle_groups.append([])
        self._toggle_groups[group].append(item)

    def refresh(self):
        global g_active_hover
        global g_active_gesture
        enable = False
        toggle_group = -1
        # Active gesture has precedence over hovering.
        if g_active_gesture is not None:
            if isinstance(g_active_gesture, PhysicsDragGesture):
                if g_active_gesture._manipulator == self:
                    toggle_group = g_active_gesture._toggle_group
                    enable = True
        elif g_active_hover is not None:
            if isinstance(g_active_hover, PhysicsHoverGesture):
                if g_active_hover._manipulator == self:
                    toggle_group = g_active_hover._toggle_group
                    enable = True

        if len(self._toggle_groups) == 1:
            for object in self._toggle_groups[0]:
                object.toggle(enable)
        elif len(self._toggle_groups) > 1:
            # If having multiple, first set all to invisible, then switch on the relevant. 
            # This approach is necessary as some objects may be present in several groups.
            for group in range(len(self._toggle_groups)):
                for object in self._toggle_groups[group]:
                    object.toggle(False)
            if toggle_group >= 0:
                if toggle_group >= len(self._toggle_groups):
                    carb.log_error(f"Fatal error: visibility group exceeding available: {toggle_group} (+1) vs {len(self._toggle_groups)}")
                for object in self._toggle_groups[toggle_group]:
                    object.toggle(True)

        if self._viewport_overlay:
            self.get_viewport_overlay().refresh_clipping_state()

    def on_build(self):
        self._toggle_groups.clear()

        if get_active_gesture() is not None and get_active_gesture()._manipulator == self:
            set_active_gesture(None)
        
        if get_active_hover() is not None and get_active_hover()._manipulator == self:
            set_active_hover(None)

    def destroy(self):
        if get_active_gesture() is not None and get_active_gesture()._manipulator == self:
            set_active_gesture(None)

        if get_active_hover() is not None and get_active_hover()._manipulator == self:
            set_active_hover(None)

        self.get_viewport_overlay().refresh_clipping_state()
        self._viewport_overlay = None
        self.invalidate()

    def __del__(self):
        self.destroy()

class PhysicsViewportOverlay:
    def __init__(self, main_viewport_overlay):
        self._main_viewport_overlay = main_viewport_overlay
        self._gesture_manager = PhysicsGestureManager(self)

    def get_gesture_manager(self):
        return self._gesture_manager

    def refresh_clipping_state(self):
        self._main_viewport_overlay.refresh_clipping_state()

    def destroy(self):
        self._gesture_manager = None

    def __del__(self):
        self.destroy()
