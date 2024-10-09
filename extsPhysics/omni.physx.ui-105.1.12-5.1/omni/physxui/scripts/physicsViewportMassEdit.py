from operator import mod
import omni.kit.commands
import omni.usd
from omni.usd._impl.utils import get_prim_at_path
from pxr import UsdGeom, UsdUtils, UsdPhysics, Gf, PhysicsSchemaTools, Tf, Usd
import carb
from omni.physx import get_physx_property_query_interface
from omni.timeline import get_timeline_interface
from omni.ui_scene import scene as sc
import omni.ui as ui
from omni.ui import color as cl
from omni.physx.bindings._physx import PhysxPropertyQueryRigidBodyResponse, PhysxPropertyQueryColliderResponse, PhysxPropertyQueryResult, PhysxPropertyQueryMode
from omni.kit.manipulator.tool.snap import settings_constants as snap_c
from omni.kit.manipulator.transform.settings_listener import SnapSettingsListener
import omni.kit.window.property
import math
import collections.abc
from pathlib import Path
from .physicsViewportShared import *
from cmath import inf
from omni.physx.scripts import utils
from omni.physx.bindings._physx import SETTING_MASS_DISTRIBUTION_MANIPULATOR, SETTING_DISPLAY_MASS_PROPERTIES

"""
Mass distribution visualization. 

Allows conveniently viewing and manipulating mass properties of a body. Computes the diagonal inertia based on a cuboid 
approximation shape with a potentially non-uniform internal distribution of mass.

TODO/possible future additions:
- Add noise to mass distribution points to reduce patterning.
- Add ellipsoid approximation shape.
- Scale the amount of points with prim dimensions.

"""

DRAG_SMOOTHNESS_FACTOR = 3.0
DRAG_SMOOTHNESS_MODIFIER = 1.0 / (1.0 + DRAG_SMOOTHNESS_FACTOR)

# If true, consider off-center center of mass as expression of non-uniform density.
VISUAL_MASS_DISTRIBUTION_NONUNIFORM = False

# If true, adjust point distribution in an exponential way.
VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL = False

# If true, draws the bounding box of the collider.
VISUAL_MASS_DISTRIBUTION_COLLIDER_BOUNDING_BOX = False

# If true, draws a box signifying the midpoint of axial distributions.
VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX = False

# If true, renders a point cloud that hints at the mass distribution density.
VISUAL_MASS_DISTRIBUTION_POINT_CLOUD = False

# If true, renders subdivision markers on rulers.
VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS = False

# When scaling shapes to screen with ui.scene, it multiplies pixels with this.
UI_SCENE_SCREEN_SCALE_MODIFIER = 2

# Always be applied by kit, doesn't seem like there's any way to truly fetch this value.
UI_FONT_PADDING = 1

INERTIA_POINTS_RESOLUTION = 6

GESTURE_SCALE = 0
GESTURE_TRANSLATE = 1
GESTURE_ROTATE = 2
GESTURE_NUM = 3

COLOR_BBOX = cl("#FF66FFFF")

BBOX_LINE_THICKNESS = 2.0

MASS_DISTRIBUTION_COLOR = cl("#66FFFF00")
MASS_DISTRIBUTION_BOX_COLOR = cl("#000000FF") + MASS_DISTRIBUTION_COLOR
MASS_DISTRIBUTION_BOX_LINE_THICKNESS = 2
MASS_DISTRIBUTION_MIDPOINT_BOX_COLOR = cl("#000000AA") + MASS_DISTRIBUTION_COLOR
MASS_DISTRIBUTION_MIDPOINT_BOX_LINE_THICKNESS = 2
MASS_DISTRIBUTION_MIDPOINT_BOX_LINE_STIPPLES = 9
MASS_DISTRIBUTION_CUTOUT_BOX_COLOR = cl("#000000AA") + MASS_DISTRIBUTION_COLOR
MASS_DISTRIBUTION_CUTOUT_BOX_LINE_THICKNESS = 2
MASS_DISTRIBUTION_POINTS_MAX_ALPHA = 0xAA # Separate value since we fade it in.
MASS_DISTRIBUTION_POINTS_THICKNESS = 2
MASS_DISTRIBUTION_HANDLE_SIZE = 25
MASS_DISTRIBUTION_HANDLE_RECTANGLE = False
MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE = 40
MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_COUNT = 0
MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_ALPHA = 0xAA # Separate value since we fade it in.
MASS_DISTRIBUTION_HANDLE_ARROW = False
MASS_DISTRIBUTION_HANDLE_ARROW_SIZE = 20
CENTER_OF_MASS_AXIS_ARROW_LENGTH = 30
CENTER_OF_MASS_AXIS_ARROW_RADIUS= 12
CENTER_OF_MASS_AXIS_HALF_LENGTH = 150.0

PRINCIPAL_AXIS_ROTATION_ARC_TESSELATION = 64

GESTURE_TEXT_ENABLED = False
GESTURE_TEXT_OFFSET = Gf.Vec2f(0.0, -10.0)
GESTURE_TEXT_FONT_SIZE = 15
GESTURE_TEXT_FONT_COLOR = cl("#ADF138")

MASS_INFO_TEXT_ENTRY_PRIM_PATH = 0
MASS_INFO_TEXT_ENTRY_MASS = 1
MASS_INFO_TEXT_ENTRY_CENTER_OF_MASS = 2
MASS_INFO_TEXT_ENTRY_PRINCIPAL_AXIS = 3
MASS_INFO_TEXT_ENTRY_DIAGONAL_INERTIA = 4
MASS_INFO_TEXT_ENTRY_NUM = 5

MASS_INFO_TEXT_BOX_BACKGROUND_COLOR = cl("#1E212399")
MASS_INFO_TEXT_MARGIN = Gf.Vec2f(20.0, 20.0)
MASS_INFO_TEXT_FONT_SIZE = 14
MASS_INFO_TEXT_FONT_LINE_SPAN = MASS_INFO_TEXT_FONT_SIZE + UI_FONT_PADDING * 2
MASS_INFO_TEXT_FONT_COLOR = cl("#ADF138")
MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT = cl("#FEFFFC")
MASS_INFO_TEXT_FONT_COLOR_WARNING = cl("#FFFF38")
MASS_INFO_TEXT_BOX_WIDTH = 540.0

INFO_BOX_NUM = 2
INFO_BOX_MASS_VIEW = 0
INFO_BOX_MASS_EDIT = 1

# This calculates dimensions if the body is a cuboid and matches how the PhysX debug visualization works. Unused but left here for reference.
def physx_diagonal_inertia_to_axial_mass_midpoints(mass, diagonal_inertia):
    scale_mod = 0.0 if mass <= 0.0 else 6.0 / mass 
    dimensions = Gf.Vec3f(            
        math.sqrt(scale_mod * math.fabs(-diagonal_inertia[0] + diagonal_inertia[1] + diagonal_inertia[2])),
        math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] - diagonal_inertia[1] + diagonal_inertia[2])),
        math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] + diagonal_inertia[1] - diagonal_inertia[2]))
    )
    return dimensions

# This calculates the inertia if the body is a cuboid and matches how the PhysX debug visualization works. Unused but left here for reference.
def physx_axial_mass_midpoints_to_diagonal_inertia(mass, dimensions):
    # Square the dimensions so we only have to do it once.
    diagonal = Gf.Vec3f(dimensions[0] * dimensions[0], dimensions[1] * dimensions[1], dimensions[2] * dimensions[2])

    # By some simple algebra, we get:
    # diagonal inertia base = Gf.Vec3f((diagonal[1] + diagonal[2]) / 2, (diagonal[0] + diagonal[2]) / 2, (diagonal[0] + diagonal[1]) / 2)

    # and with the modifiers, we get 
    diagonal_inertia_modifier = mass / 12.0
    diagonal_inertia = Gf.Vec3f((diagonal[1] + diagonal[2]) * diagonal_inertia_modifier, (diagonal[0] + diagonal[2]) * diagonal_inertia_modifier, (diagonal[0] + diagonal[1]) * diagonal_inertia_modifier)
    
    return diagonal_inertia

# Gets the relative mass cutout from the axial mass midpoint. This is determined by the highest calculated relative cutout of all axes.
def get_relative_mass_cutout_dimensions_from_axial_mass_midpoint(body_bbox, axial_mass_midpoints):
    relative_cutout = 0.0
    for axis in range(AXIS_NUM):
        if body_bbox[axis] > 0.0:
            relative_cutout = max(relative_cutout, 2.0 * axial_mass_midpoints[axis] / body_bbox[axis] - 1.0)
    return relative_cutout

# Gets the relative mass cutout from the virtual dimensions. This is determined by the highest calculated relative cutout of all axes.
def get_relative_mass_cutout_dimensions_from_virtual_dimensions(body_bbox, virtual_dimensions):
    relative_cutout = 0.0
    for axis in range(AXIS_NUM):
        if virtual_dimensions[axis] > body_bbox[axis] and body_bbox[axis] > 0.0:
            relative_cutout = max(relative_cutout, math.sqrt(max(0.0, sqr(virtual_dimensions[axis] / body_bbox[axis])-1.0) / 0.6667))
    return relative_cutout

# Gets the inner dimensions of the approximated max box.
def get_mass_inner_dimensions_from_axial_mass_midpoint(body_bbox, axial_mass_midpoints, relative_cutout):
    inner_dimensions = Gf.Vec3f(0.0) 
    for axis in range(AXIS_NUM):
        inner_dimensions[axis] = min(relative_cutout * axial_mass_midpoints[axis], body_bbox[axis])
    return inner_dimensions

# Gets the outer dimensions of the approximated max box.
def get_mass_outer_dimensions_from_axial_mass_midpoint(body_bbox, axial_mass_midpoints, relative_cutout):
    outer_dimensions = Gf.Vec3f(0.0) 
    for axis in range(AXIS_NUM):
        outer_dimensions[axis] = min(axial_mass_midpoints[axis] / (relative_cutout * 0.5 + 0.5), body_bbox[axis])
    return outer_dimensions

# Returns the relative offset of the center of mass in relation to the body center and bounding box
def get_relative_center_of_mass(center_of_mass, body_center, body_bbox):
    return Gf.Vec3f(0.0 if body_bbox[0] == 0.0 else 2.0 * (center_of_mass[0] - body_center[0]) / body_bbox[0],
                    0.0 if body_bbox[1] == 0.0 else 2.0 * (center_of_mass[1] - body_center[1]) / body_bbox[1],
                    0.0 if body_bbox[2] == 0.0 else 2.0 * (center_of_mass[2] - body_center[2]) / body_bbox[2])

# This converts axial midpoint to virtual dimensions we can directly use in diagonal inertia computations as if it was a 
# solid/continuous body. For downscaling, it uses the input value unmodified, but for upscaling, it reinterprets it the 
# dimensions as a cutout at center, approximating inner ~= outer (thin walled box) to x1.6667 and doing appropriate 
# non-linear scaling between the two to represent it as if it was a solid mass. Note that 1.6667 is only exact for 
# boxes with uniform dimensions, but it should be good enough for making visuals cues.
def get_axial_mass_midpoints_to_virtual_dimensions(body_bbox, axial_mass_midpoints):
    virtual_dimensions = Gf.Vec3f(0.0)
    relative_cutout_dimensions = get_relative_mass_cutout_dimensions_from_axial_mass_midpoint(body_bbox, axial_mass_midpoints)
    rescale_value = math.sqrt(1.0 + 0.6667 * sqr(relative_cutout_dimensions))

    for n in range(AXIS_NUM):
        if relative_cutout_dimensions == 0.0:
            virtual_dimensions[n] = axial_mass_midpoints[n] * 2.0
        else:
            virtual_dimensions[n] =  min(body_bbox[n], axial_mass_midpoints[n] * 2.0 / (relative_cutout_dimensions + 1.0)) * rescale_value

    return virtual_dimensions

# Simply the inverse of the above function.
def get_virtual_dimensions_to_axial_mass_midpoints(body_bbox, virtual_dimensions):
    axial_mass_midpoints = Gf.Vec3f(0.0)
    relative_cutout_dimensions = get_relative_mass_cutout_dimensions_from_virtual_dimensions(body_bbox, virtual_dimensions)
    rescale_value = math.sqrt(1.0 + 0.6667 * sqr(relative_cutout_dimensions))

    for n in range(AXIS_NUM):
        if relative_cutout_dimensions == 0.0:
            axial_mass_midpoints[n] = virtual_dimensions[n] * 0.5
        else:
            axial_mass_midpoints[n] = (0.5 * relative_cutout_dimensions + 0.5) * virtual_dimensions[n] / rescale_value

    return axial_mass_midpoints

# Calculates the diagonal inertia tensor based on the axial midpoints, which signifies the midpoint of mass
# in a given dimension.
def axial_mass_midpoints_to_diagonal_inertia(mass, axial_mass_midpoints, center_of_mass, body_bbox, body_bbox_center):
    # Standard modifier for cuboids.
    diagonal_inertia_modifier = mass / 12.0

    # Rescale the midpoints to give us virtual dimensions with linear values.
    virtual_dimensions = get_axial_mass_midpoints_to_virtual_dimensions(body_bbox, axial_mass_midpoints)

    diagonal_axial_basis = Gf.Vec3f(0.0)
    if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
        # Gets the relation per axis.
        relative_center_of_mass = get_relative_center_of_mass(center_of_mass, body_bbox_center, body_bbox)

        # This calculates the inertia if the body is a cuboid with an offset center of mass, where  the assumption is
        # that this is due to nonuniform mass distribution/density within the cuboid.
        diagonal_axial_basis = Gf.Vec3f(virtual_dimensions[0] * virtual_dimensions[0] * max(0.001, 1.0 - relative_center_of_mass[0] * relative_center_of_mass[0]), 
                                virtual_dimensions[1] * virtual_dimensions[1] * max(0.001, 1.0 - relative_center_of_mass[1] * relative_center_of_mass[1]),
                                virtual_dimensions[2] * virtual_dimensions[2] * max(0.001, 1.0 - relative_center_of_mass[2] * relative_center_of_mass[2]))
    else:
        diagonal_axial_basis = Gf.Vec3f(virtual_dimensions[0] * virtual_dimensions[0], 
                                virtual_dimensions[1] * virtual_dimensions[1],
                                virtual_dimensions[2] * virtual_dimensions[2])

    diagonal_inertia = Gf.Vec3f(
        diagonal_inertia_modifier * (diagonal_axial_basis[1] + diagonal_axial_basis[2]),
        diagonal_inertia_modifier * (diagonal_axial_basis[0] + diagonal_axial_basis[2]),
        diagonal_inertia_modifier * (diagonal_axial_basis[0] + diagonal_axial_basis[1]))

    return diagonal_inertia

# The inverse of the above function.
def diagonal_inertia_to_axial_mass_midpoints(mass, diagonal_inertia, center_of_mass, body_bbox, body_bbox_center):
    scale_mod = 0.0 if mass <= 0.0 else 12.0 / mass 
    scale_mod *= 0.5 
    dimensions = Gf.Vec3f(0.0)

    if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
        # Gets the relation per axis.
        relative_center_of_mass = get_relative_center_of_mass(center_of_mass, body_bbox_center, body_bbox)
        dimensions = Gf.Vec3f(            
            math.sqrt(scale_mod * math.fabs(-diagonal_inertia[0] + diagonal_inertia[1] + diagonal_inertia[2]) / (max(0.001, 1.0 - relative_center_of_mass[0] * relative_center_of_mass[0]))),
            math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] - diagonal_inertia[1] + diagonal_inertia[2]) / (max(0.001, 1.0 - relative_center_of_mass[1] * relative_center_of_mass[1]))),
            math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] + diagonal_inertia[1] - diagonal_inertia[2]) / (max(0.001, 1.0 - relative_center_of_mass[2] * relative_center_of_mass[2])))
            )
    else:
        dimensions = Gf.Vec3f(            
            math.sqrt(scale_mod * math.fabs(-diagonal_inertia[0] + diagonal_inertia[1] + diagonal_inertia[2])),
            math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] - diagonal_inertia[1] + diagonal_inertia[2])),
            math.sqrt(scale_mod * math.fabs(diagonal_inertia[0] + diagonal_inertia[1] - diagonal_inertia[2]))
            )

    axial_mass_midpoints = get_virtual_dimensions_to_axial_mass_midpoints(body_bbox, dimensions)

    return axial_mass_midpoints

# Handles hover highlighting etc. for manipulation gestures.
class PhysicsMassEditHoverGesture(PhysicsHoverGesture):
    def __init__(self, manipulator, gesture, direction):
        super().__init__(manipulator, gesture * AXIS_DIRECTION_NUM + direction)
        self._gesture = gesture

    def on_began(self):
        if get_active_hover() is not None:
            return
        super().on_began()
        self._manipulator.update_info_text()
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

    def on_changed(self):
        super().on_changed()
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

    def on_ended(self):
        super().on_ended()
        self._manipulator.update_info_text()
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

# Scales the axial mass midpoints.
class PhysicsMassEditGestureScale(PhysicsDragGesture):
    def __init__(self, manipulator, direction):
        super().__init__(manipulator)
        self._direction = direction
        self._origin = None
        self._gesture = GESTURE_SCALE
        self._scale_link_limit = None
        self._toggle_group = PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction)

    def on_began(self):
        super().on_began()
        self._manipulator.update_info_text()
        axis = direction_to_axis(self._direction)
        if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            # When we have a cutout, the scaling for all axes will link if scaling the greatest of the three in terms of the
            # cutout generated. Linking in this way makes scaling appear linear even if having a cutout. We store the
            # limit scale at which this axis will be determining on began.
            self._scale_link_limit = self._manipulator._body_bbox_dimensions[axis] * 0.5
            axis_scale = ( 0.0 if self._manipulator._body_bbox_dimensions[axis] == 0.0 else self._manipulator._scale_inertia[axis] / self._manipulator._body_bbox_dimensions[axis])
            for other_axis in range(AXIS_NUM):
                if other_axis != axis and self._manipulator._body_bbox_dimensions[other_axis] > 0.0 and (self._manipulator._scale_inertia[other_axis] / self._manipulator._body_bbox_dimensions[other_axis]) > axis_scale + 0.001 :
                    self._scale_link_limit = max(self._scale_link_limit, (self._manipulator._scale_inertia[other_axis] / self._manipulator._body_bbox_dimensions[other_axis]) * self._manipulator._body_bbox_dimensions[axis])

    def on_changed(self):
        if get_active_gesture() is not self:
            return
        super().on_changed()
        # The current transform of our scaling handle.
        transform = self._manipulator._transform_pose.transform * self._manipulator._transform_center_of_mass.transform * self._manipulator._transform_principal_rotate.transform * self._manipulator._shape_transform_scale_inertia_handle[self._direction].transform
        axis = direction_to_axis(self._direction)
        position = Gf.Vec4f(0.0, 0.0, 0.0, 1.0) * Gf.Matrix4f(*transform)
        offset_dir = Gf.Vec4f()
        for n in range(3):
            offset_dir[n] = (self.sender.gesture_payload.ray_closest_point[n] - position[n])
        offset_dir[3] = 0.0

        normal_dir = Gf.Vec4f(0.0)
        normal_dir[axis] = 1.0 if mod(self._direction, 2) == 0.0 else -1.0
        normal_dir = normal_dir * Gf.Matrix4f(*transform)

        # Finds the offset and normals in view space.
        offset_view = offset_dir * Gf.Matrix4f(*self.sender.scene_view.view)
        normal_view = normal_dir * Gf.Matrix4f(*self.sender.scene_view.view)

        # Make offset parallel to the normal on screen.
        offset_view_screen = Gf.Vec2f(offset_view[0], offset_view[1])
        normal_view_screen = Gf.Vec2f(normal_view[0], normal_view[1])
        normal_view_screen =  normal_view_screen.GetNormalized()
        n_dot_o_screen = normal_view_screen.GetDot(offset_view_screen)
        offset_view_screen = normal_view_screen * n_dot_o_screen
        offset_view[0] = offset_view_screen[0]
        offset_view[1] = offset_view_screen[1]

        # Pull offset towards the screen until it becomes fully parallel with normal but with the proper dimensions.
        # This is essentially |offset| / cos(offset to normal).
        offset_mag_sq = (offset_view[0]*offset_view[0] + offset_view[1]*offset_view[1] + offset_view[2]*offset_view[2]) 
        dot_on_view = offset_view.GetDot(normal_view)

        # Prevent divide by zero.
        scale_inertia_modifier = 0.0 if dot_on_view == 0.0 else 2.0 * offset_mag_sq / dot_on_view
        
        # Apply snap if relevant.
        if self._manipulator._snap_settings_listener.snap_enabled and self._manipulator._snap_settings_listener.snap_scale > 0.0:
            scale_inertia_modifier = round(scale_inertia_modifier / self._manipulator._snap_settings_listener.snap_scale) * self._manipulator._snap_settings_listener.snap_scale
        else:
            scale_inertia_modifier *= DRAG_SMOOTHNESS_MODIFIER

        scale_inertia_modifier = min(scale_inertia_modifier, self._manipulator._body_bbox_dimensions[axis]-self._manipulator._scale_inertia[axis])
        scale_inertia_modifier = max(scale_inertia_modifier, -self._manipulator._scale_inertia[axis] + FLOAT_EPSILON)

        if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            # Determine the scaling modifier for linked axes by limiting the modifier to the relevant range.
            scale_link_offset = 0.0
            if scale_inertia_modifier > 0.0:
                # If positive, add difference to cut if offset is negative.
                scale_link_offset = scale_inertia_modifier + min(0.0, self._manipulator._scale_inertia[axis] - self._scale_link_limit)
            else:
                # If negative, limit to difference to cut. 
                scale_link_offset = min(0.0, max(scale_inertia_modifier, -self._manipulator._scale_inertia[axis]+self._scale_link_limit))
            
            if self._manipulator._scale_inertia[axis] > self._scale_link_limit or scale_link_offset > 0.0:
                # If linked, apply scale modifier to other axes.
                for other_axis in range(AXIS_NUM):
                    if other_axis != axis:
                        # Prevent from exceeding boundaries or going into negative scale.
                        self._manipulator._scale_inertia[other_axis] = max(FLOAT_EPSILON, self._manipulator._scale_inertia[other_axis]+scale_link_offset * self._manipulator._scale_inertia[other_axis] / self._manipulator._scale_inertia[axis])
                        self._manipulator._scale_inertia[other_axis] = min(self._manipulator._body_bbox_dimensions[other_axis], self._manipulator._scale_inertia[other_axis])
        
        self._manipulator._scale_inertia[axis] += scale_inertia_modifier

        # Prevent from exceeding boundaries or going into negative scale.
        self._manipulator._scale_inertia[axis] = max(FLOAT_EPSILON, self._manipulator._scale_inertia[axis])
        self._manipulator._scale_inertia[axis] = min(self._manipulator._body_bbox_dimensions[axis], self._manipulator._scale_inertia[axis])

        self._manipulator._body_diagonal_inertia = axial_mass_midpoints_to_diagonal_inertia(self._manipulator._body_mass, self._manipulator._scale_inertia, Gf.Vec4f(*self._manipulator._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform).GetTranspose(), self._manipulator._body_bbox_dimensions, self._manipulator._body_bbox_center)

        # Update transforms based on our new values.
        self._manipulator.rebuild_inertia_scale()
        self._manipulator.rebuild_shape_transforms()

        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

        self._manipulator.update_info_text()

    def on_ended(self):
        super().on_ended()

        self._manipulator._body_diagonal_inertia = axial_mass_midpoints_to_diagonal_inertia(self._manipulator._body_mass, self._manipulator._scale_inertia, Gf.Vec4f(*self._manipulator._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform).GetTranspose(), self._manipulator._body_bbox_dimensions, self._manipulator._body_bbox_center)
        self._manipulator.write_to_usd([UsdPhysics.Tokens.physicsDiagonalInertia], [self._manipulator._body_diagonal_inertia])

        self._manipulator.rebuild_inertia_scale()
        self._manipulator.rebuild_shape_transforms()
        
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text()
        
        self._manipulator.update_info_text()

# Moves around the center of mass.
class PhysicsMassEditGestureTranslate(PhysicsDragGesture):
    def __init__(self, manipulator, axis):
        super().__init__(manipulator)
        self._axis = axis
        self._translate_offset = None
        self._initial_position = None
        self._gesture = GESTURE_TRANSLATE
        self._toggle_group = PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_TRANSLATE, axis)

    def _set_translation(self):
        transform = self._manipulator._transform_pose.transform * self._manipulator._transform_center_of_mass.transform * self._manipulator._transform_principal_rotate.transform * self._manipulator._shape_transform_axis[self._axis].transform
        pose_rotate = Gf.Matrix4f(*self._manipulator._transform_pose.transform).ExtractRotationMatrix()
        pose_rotate = Gf.Matrix4f(pose_rotate, Gf.Vec3f(0.0))
        translate_direction = Gf.Vec4f(*AXIS_VECTOR[self._axis],0.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform)
        position = Gf.Vec4f(0.0, 0.0, 0.0, 1.0) * Gf.Matrix4f(*transform)
        offset_dir = Gf.Vec4f()
        for n in range(3):
            offset_dir[n] = (self.sender.gesture_payload.ray_closest_point[n]) - position[n]
        offset_dir[3] = 0.0
        offset_dir = offset_dir * pose_rotate.GetInverse()

        if self._translate_offset is None:
            self._translate_offset = offset_dir.GetDot(translate_direction)
        else:
            translate_modifier = offset_dir.GetDot(translate_direction) - self._translate_offset

            if self._manipulator._snap_settings_listener.snap_enabled:
                if self._axis == AXIS_X and self._manipulator._snap_settings_listener.snap_move_x > 0.0:
                    translate_modifier = round(translate_modifier /  self._manipulator._snap_settings_listener.snap_move_x) * self._manipulator._snap_settings_listener.snap_move_x
                elif self._axis == AXIS_Y and self._manipulator._snap_settings_listener.snap_move_y > 0.0:
                    translate_modifier = round(translate_modifier /  self._manipulator._snap_settings_listener.snap_move_y) * self._manipulator._snap_settings_listener.snap_move_y
                elif self._axis == AXIS_Z and self._manipulator._snap_settings_listener.snap_move_z > 0.0:
                    translate_modifier = round(translate_modifier /  self._manipulator._snap_settings_listener.snap_move_z) * self._manipulator._snap_settings_listener.snap_move_z
            else: 
                translate_modifier *= DRAG_SMOOTHNESS_MODIFIER

            if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                # Limit to collider bounding box.
                if translate_modifier > 0.0:
                    for axis in range (AXIS_NUM):
                        if translate_direction[axis] > 0.0:
                            translate_modifier = min(translate_modifier, (0.5 * self._manipulator._body_bbox_dimensions[axis] - self._manipulator._body_center_of_mass[axis]) / translate_direction[axis])
                        elif translate_direction[axis] < 0.0:
                            translate_modifier = min(translate_modifier, (-0.5 * self._manipulator._body_bbox_dimensions[axis] - self._manipulator._body_center_of_mass[axis]) / translate_direction[axis])
                else:
                    for axis in range (AXIS_NUM):
                        if translate_direction[axis] > 0.0:
                            translate_modifier = max(translate_modifier, (-0.5 * self._manipulator._body_bbox_dimensions[axis] - self._manipulator._body_center_of_mass[axis]) / translate_direction[axis])
                        elif translate_direction[axis] < 0.0:
                            translate_modifier = max(translate_modifier, (0.5 * self._manipulator._body_bbox_dimensions[axis] - self._manipulator._body_center_of_mass[axis]) / translate_direction[axis])

            self._manipulator._body_center_of_mass += Gf.Vec3f(translate_direction[0], translate_direction[1], translate_direction[2]) * translate_modifier

        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

        self._manipulator._body_diagonal_inertia = axial_mass_midpoints_to_diagonal_inertia(self._manipulator._body_mass, self._manipulator._scale_inertia, Gf.Vec4f(*self._manipulator._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform).GetTranspose(), self._manipulator._body_bbox_dimensions, self._manipulator._body_bbox_center)

    def on_began(self):
        super().on_began()
        self._manipulator.update_info_text()
        self._set_translation()

    def on_changed(self):
        if get_active_gesture() is not self:
            return
        super().on_changed()
        self._set_translation()
        self._manipulator.rebuild_center_of_mass_translate()
        self._manipulator.rebuild_shape_transforms()
        self._manipulator.update_info_text()

    def on_ended(self):
        super().on_ended()
        self._manipulator.update_info_text()
        
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text()

        self._translate_offset = None
        self._manipulator._body_diagonal_inertia = axial_mass_midpoints_to_diagonal_inertia(self._manipulator._body_mass, self._manipulator._scale_inertia, Gf.Vec4f(*self._manipulator._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform).GetTranspose(), self._manipulator._body_bbox_dimensions, self._manipulator._body_bbox_center)
        self._manipulator.write_to_usd([UsdPhysics.Tokens.physicsCenterOfMass, UsdPhysics.Tokens.physicsDiagonalInertia, UsdPhysics.Tokens.physicsPrincipalAxes], [Gf.Vec3f(self._manipulator._body_center_of_mass), self._manipulator._body_diagonal_inertia, self._manipulator._body_principal_axes])

# Rotates the principal axes.
class PhysicsMassEditGestureRotate(PhysicsDragGesture):
    def __init__(self, manipulator, axis):
        super().__init__(manipulator)
        self._axis = axis
        self._angle_origin = None
        self._angle_moved = None
        self._gesture = GESTURE_ROTATE
        self._toggle_group = PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_ROTATE, axis)

    def _set_rotation(self):
        transform = self._manipulator._transform_pose.transform * self._manipulator._transform_center_of_mass.transform * self._manipulator._transform_principal_rotate.transform * self._manipulator._shape_transform_circle[self._axis].transform
        axis = AXIS_VECTOR[self._axis]
        position = Gf.Vec4f(0.0, 0.0, 0.0, 1.0) * Gf.Matrix4f(*transform)
        offset_dir = Gf.Vec4f()
        for n in range(3):
            offset_dir[n] = (self.sender.gesture_payload.ray_closest_point[n] - position[n])
        offset_dir[3] = 0.0
        offset_dir = offset_dir.GetNormalized()
        offset_dir_local = offset_dir * Gf.Matrix4f(*transform).GetInverse()
        offset_dir_local = offset_dir_local.GetNormalized()

        angle = math.acos(offset_dir_local[0])
        if offset_dir_local[1] < 0:
            angle = - angle
        angle = Gf.RadiansToDegrees(angle)

        if self._angle_origin is None:
            self._angle_origin = angle
            self._angle_moved = 0.0
        else:
            if self._manipulator._snap_settings_listener.snap_enabled:
                self._angle_moved = angle - self._angle_origin + self._angle_moved
                self._angle_moved += self._manipulator._snap_settings_listener.snap_rotate / 2
                self._angle_moved -= math.fmod(self._angle_moved, self._manipulator._snap_settings_listener.snap_rotate)
            else: 
                self._angle_moved += DRAG_SMOOTHNESS_MODIFIER * (angle - self._angle_origin)

            self._manipulator._rotation_modifier = axis_angle_to_quaternion(axis, math.radians(self._angle_moved))
       
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text(self.sender.gesture_payload.ray_closest_point)

    def on_began(self):
        super().on_began()
        self._manipulator.update_info_text()
        self._set_rotation()

    def on_changed(self):
        if get_active_gesture() is not self:
            return
        super().on_changed()
        self._set_rotation()
        self._manipulator.rebuild_principal_rotate()
        self._manipulator._body_diagonal_inertia = axial_mass_midpoints_to_diagonal_inertia(self._manipulator._body_mass, self._manipulator._scale_inertia, Gf.Vec4f(*self._manipulator._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._manipulator._transform_principal_rotate.transform).GetTranspose(), self._manipulator._body_bbox_dimensions, self._manipulator._body_bbox_center)
        self._manipulator.rebuild_shape_transforms()
        self._manipulator.update_info_text()

    def on_ended(self):
        super().on_ended()

        self._manipulator._body_principal_axes = self._manipulator._body_principal_axes*Gf.Quatf(self._manipulator._rotation_modifier)
        self._manipulator._rotation_modifier = Gf.Quatf.GetIdentity()
        self._angle_origin = None
        self._manipulator.update_info_text()
        
        if GESTURE_TEXT_ENABLED:
            self._manipulator.update_gesture_text()

        self._manipulator.write_to_usd([UsdPhysics.Tokens.physicsPrincipalAxes, UsdPhysics.Tokens.physicsDiagonalInertia], [self._manipulator._body_principal_axes, self._manipulator._body_diagonal_inertia])

class PhysicsMassManipulator(PhysicsManipulator):
    def __init__(self, viewport_overlay, prim):
        super().__init__(viewport_overlay)
        self._prim = prim
        self._stage = None
        self._active = False

        self._body_mass = 0.0
        self._body_diagonal_inertia = Gf.Vec3f(0.0)
        self._body_principal_axes = Gf.Quatf.GetIdentity()
        self._body_center_of_mass = Gf.Vec3f(0.0)
        self._body_bbox_dimensions = Gf.Vec3f(0.0)
        self._body_bbox_center = Gf.Vec3f(0.0)

        self._scale_inertia = None
        self._rotation_modifier = Gf.Quatf.GetIdentity()

        self._transform_scale = Gf.Vec3f(0.0)
        self._transform_pose = None
        self._transform_center_of_mass=None
        self._transform_principal_rotate = None

        self._shape_transform_bbox=None
        self._shape_transform_center_of_mass_visualization=None
        self._shape_transform_inertia_distribution_outer_box=None

        if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            self._shape_transform_inertia_distribution_cutout_box=None

        if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX:
            self._shape_transform_inertia_distribution_midpoint_box=None
        
        if VISUAL_MASS_DISTRIBUTION_POINT_CLOUD:
            self._shape_transform_inertia_distribution_corner=[]

    def rebuild_principal_rotate(self):
        rotate_matrix = Gf.Matrix4f()
        rotate_matrix.SetRotate(self._body_principal_axes * self._rotation_modifier)
        self._transform_principal_rotate.transform = sc.Matrix44(*rotate_matrix[0], *rotate_matrix[1], *rotate_matrix[2], *rotate_matrix[3])

    def rebuild_center_of_mass_translate(self):
        translate = Gf.Vec3f(0.0)
        for axis in range(AXIS_NUM):
           translate[axis] = self._body_center_of_mass[axis] * self._transform_scale[axis]
        self._transform_center_of_mass.transform = sc.Matrix44.get_translation_matrix(*translate) 

    def rebuild_inertia_scale(self):
        self._scale_inertia = diagonal_inertia_to_axial_mass_midpoints(self._body_mass, self._body_diagonal_inertia, Gf.Vec4f(*self._body_center_of_mass, 1.0) * Gf.Matrix4f(*self._transform_principal_rotate.transform).GetTranspose(), self._body_bbox_dimensions, self._body_bbox_center)

    def rebuild_shape_transforms(self):
        center_of_mass_local = Gf.Vec4f(self._transform_center_of_mass.transform[12], self._transform_center_of_mass.transform[13], self._transform_center_of_mass.transform[14], 0.0) * Gf.Matrix4f(*self._transform_principal_rotate.transform).GetTranspose()
        center_local = Gf.Vec4f(*self._body_bbox_center, 0.0) * Gf.Matrix4f(*self._transform_principal_rotate.transform).GetTranspose()

        relative_cutout = 0.0
        inner_dimensions = Gf.Vec3f(0.0)
        outer_dimensions = Gf.Vec3f(0.0)

        if VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            scaling_power = []
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_X] / float(self._body_bbox_dimensions[0])) / math.log(0.5) + 1.0)
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_Y] / float(self._body_bbox_dimensions[1])) / math.log(0.5) + 1.0)
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_Z] / float(self._body_bbox_dimensions[2])) / math.log(0.5) + 1.0)
        else:
            relative_cutout = get_relative_mass_cutout_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia)
            inner_dimensions = get_mass_inner_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)
            outer_dimensions =  get_mass_outer_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)


        # Returns the visual scale of an offset from center derived from the midpoints.
        def dimensions_to_scale(offset):
            scale = Gf.Vec3f(0.0)
            if VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
                if offset > 0.0:
                    for axis in range(AXIS_NUM):
                        scale[axis] = math.pow(offset, scaling_power[axis]) * self._body_bbox_dimensions[axis]
            else:
                for axis in range(AXIS_NUM):
                    scale[axis] = (inner_dimensions[axis] + (outer_dimensions[axis] - inner_dimensions[axis]) * offset)
            return scale


        # center_of_mass_local_normalized = center_of_mass_local.GetNormalized()
        # Returns the visual translate of an offset from center derived from the midpoints, center of mass and dimensions.
        def dimensions_to_translate(scale_factor):
            translate = Gf.Vec3f(0.0)
            if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                for axis in range(AXIS_NUM):
                    translate[axis] = (center_local[axis] - center_of_mass_local[axis]) * scale_factor[axis] / self._body_bbox_dimensions[axis]
            # else:
            #     translate = 
            return translate

        if VISUAL_MASS_DISTRIBUTION_POINT_CLOUD:
                
            direction_scale_factor = Gf.Vec3f(1.0)
            rel_com = get_relative_center_of_mass(center_of_mass_local, center_local, self._body_bbox_dimensions)
            for corner in range(BOX_CORNER_NUM):
                if corner == BOX_CORNER_X_POS_Y_POS_Z_POS:
                    direction_scale_factor = Gf.Vec3f(1.0)
                elif corner == BOX_CORNER_X_POS_Y_POS_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(1.0, 1.0, -1.0)
                elif corner == BOX_CORNER_X_POS_Y_NEG_Z_POS:
                    direction_scale_factor = Gf.Vec3f(1.0, -1.0, 1.0)
                elif corner == BOX_CORNER_X_POS_Y_NEG_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(1.0, -1.0, -1.0)
                elif corner == BOX_CORNER_X_POS_Y_POS_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(1.0, 1.0, -1.0)
                elif corner == BOX_CORNER_X_NEG_Y_POS_Z_POS:
                    direction_scale_factor = Gf.Vec3f(-1.0, 1.0, 1.0)
                elif corner == BOX_CORNER_X_NEG_Y_POS_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(-1.0, 1.0, -1.0)
                elif corner == BOX_CORNER_X_NEG_Y_NEG_Z_POS:
                    direction_scale_factor = Gf.Vec3f(-1.0, -1.0, 1.0)
                elif corner == BOX_CORNER_X_NEG_Y_NEG_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(-1.0, -1.0, -1.0)
                elif corner == BOX_CORNER_X_NEG_Y_POS_Z_NEG:
                    direction_scale_factor = Gf.Vec3f(-1.0, 1.0, -1.0)

                # Adjust each corner to center of mass so that they properly visualize distribution.
                for axis in range(AXIS_NUM):
                    if direction_scale_factor[axis] < 0.0:
                        direction_scale_factor[axis] *= 1.0 + rel_com[axis]
                    else:
                        direction_scale_factor[axis] *= 1.0 - rel_com[axis]
                    direction_scale_factor[axis] *= 0.5

                for n in range(INERTIA_POINTS_RESOLUTION):
                    scale = dimensions_to_scale((n*(0.95 if VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL else 1.0)+1.0) / float(INERTIA_POINTS_RESOLUTION))
                    scale = Gf.Vec3f(scale[0] * direction_scale_factor[0], scale[1] * direction_scale_factor[1], scale[2] * direction_scale_factor[2])
                    self._shape_transform_inertia_distribution_corner[corner][n].transform = sc.Matrix44.get_scale_matrix(*scale)


        scale_outer = dimensions_to_scale(1.0)
        translate_outer = dimensions_to_translate(scale_outer)
        self._shape_transform_inertia_distribution_outer_box.transform = sc.Matrix44.get_translation_matrix(*translate_outer) * sc.Matrix44.get_scale_matrix(*scale_outer)

        if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX:
            scale_midpoint = dimensions_to_scale(0.5)
            translate_midpoint = dimensions_to_translate(scale_midpoint)

        if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            scale_inner = dimensions_to_scale(0.0)
            translate_inner = dimensions_to_translate(scale_inner)
            self._shape_transform_inertia_distribution_cutout_box.transform = sc.Matrix44.get_translation_matrix(*translate_inner) * sc.Matrix44.get_scale_matrix(*scale_inner)

        if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX:
            self._shape_transform_inertia_distribution_midpoint_box.transform = sc.Matrix44.get_translation_matrix(*translate_midpoint) * sc.Matrix44.get_scale_matrix(*scale_midpoint)

        if VISUAL_MASS_DISTRIBUTION_COLLIDER_BOUNDING_BOX:
            self._shape_transform_bbox.transform = sc.Matrix44.get_scale_matrix(*self._body_bbox_dimensions)

    def update_info_text(self):
        return

    def refresh(self):
        super().refresh()

    def populate(self, force_update_all = False):
        usd_context = omni.usd.get_context()
        if not usd_context or not self._stage or usd_context.get_stage() != self._stage:
            if self._active:
                self.invalidate()
            return

        if not self._prim or self._prim is None or not self._prim.HasAPI(UsdPhysics.RigidBodyAPI):
            if self._active:
                self.invalidate()
            return

        if not self._active:
            self.invalidate()
            return

        # Helper functions for sanity checks against USD and PhysX property returns.
        def validate_output_array(output, desired_length):
            if output is None:
                return False
            if not isinstance(output, collections.abc.Sized) or len(output) != desired_length:
                return False
            return True

        def validate_output_quaternion(output):
            if output is None:
                return False
            if (not isinstance(output, Gf.Quatd) and not isinstance(output, Gf.Quatf) and not isinstance(output, Gf.Quaternion)):
                return False
            return True

        def validate_output_float(output):
            if output is None:
                return False
            if not isinstance(output, float):
                return False
            return True

        xfCache = UsdGeom.XformCache()
        xform = Gf.Transform(xfCache.GetLocalToWorldTransform(self._prim))
        self._transform_scale = xform.GetScale()

        xform.SetScale(Gf.Vec3d(1.0))
        xform_mat = xform.GetMatrix()

        body_mass_new = self._body_mass
        body_diagonal_inertia_new = Gf.Vec3f(self._body_diagonal_inertia)
        body_center_of_mass_new = Gf.Vec3f(self._body_center_of_mass)
        body_principal_axes_new = Gf.Quatf(self._body_principal_axes)

        self._transform_pose.transform = sc.Matrix44(*xform_mat[0], *xform_mat[1], *xform_mat[2], *xform_mat[3])
        physx_property_query_timeout = False
        physx_property_query_fail = False

        if (force_update_all or not get_timeline_interface().is_playing()):
            bbox_min = Gf.Vec3f(inf)
            bbox_max = Gf.Vec3f(-inf)
            # Fetch mass properties from PhysX.
            def rigid_info_received(rigid_info : PhysxPropertyQueryRigidBodyResponse):
                nonlocal body_mass_new
                nonlocal body_diagonal_inertia_new
                nonlocal body_center_of_mass_new
                nonlocal body_principal_axes_new
                if rigid_info.result == PhysxPropertyQueryResult.VALID:
                    if validate_output_float(rigid_info.mass):
                        body_mass_new = rigid_info.mass
                    if validate_output_array(rigid_info.inertia, 3):
                        body_diagonal_inertia_new = Gf.Vec3f(*rigid_info.inertia)
                    if validate_output_array(rigid_info.center_of_mass, 3):
                        body_center_of_mass_new = Gf.Vec3f(*rigid_info.center_of_mass )
                        for axis in range(AXIS_NUM):
                            body_center_of_mass_new[axis] /= self._transform_scale[axis]
                    if validate_output_array(rigid_info.principal_axes, 4):
                        body_principal_axes_new = Gf.Quatf(rigid_info.principal_axes[3], rigid_info.principal_axes[0], rigid_info.principal_axes[1], rigid_info.principal_axes[2])
                else:
                    carb.log_error(f"Error while waiting for query to finish code={rigid_info.result}")
                    if rigid_info.result == PhysxPropertyQueryResult.ERROR_TIMEOUT:
                        nonlocal physx_property_query_timeout
                        physx_property_query_timeout = True
                    else:
                        nonlocal physx_property_query_fail
                        physx_property_query_fail = True

            def report_collider(collider_info : PhysxPropertyQueryColliderResponse):
                nonlocal bbox_min
                nonlocal bbox_max
                if collider_info.result == PhysxPropertyQueryResult.VALID:
                    collider_path = PhysicsSchemaTools.intToSdfPath(collider_info.path_id)
                    if not validate_output_array(collider_info.aabb_local_min, 3) or not validate_output_array(collider_info.aabb_local_max, 3):
                        return
                    elif collider_path != self._prim.GetPrimPath():
                        # If child, we have to translate the local bounding box into the parent space.
                        collider_prim = get_prim_at_path(collider_path)
                        collider_xform = xfCache.ComputeRelativeTransform(collider_prim, self._prim)
                        for n in range(BOX_CORNER_NUM):
                            corner = Gf.Vec4d(0.0, 0.0, 0.0, 1.0)
                            if n < 4:
                                corner[2] = collider_info.aabb_local_min[2]
                            else:
                                corner[2] = collider_info.aabb_local_max[2]
                            if n % 2 == 0:
                                corner[1] = collider_info.aabb_local_min[1]
                            else: 
                                corner[1] = collider_info.aabb_local_max[1]
                            if n < 2 or (n > 3 and n < 6):
                                corner[0] = collider_info.aabb_local_min[0]
                            else: 
                                corner[0] = collider_info.aabb_local_max[0]
                            corner = corner * collider_xform[0]
                            for axis in range(AXIS_NUM):
                                bbox_min[axis] = min(bbox_min[axis], corner[axis])
                                bbox_max[axis] = max(bbox_max[axis], corner[axis])
                    else:
                        for axis in range(AXIS_NUM):
                            bbox_min[axis] = min(bbox_min[axis], collider_info.aabb_local_min[axis])
                            bbox_max[axis] = max(bbox_max[axis], collider_info.aabb_local_max[axis])
                else:
                    carb.log_error(f"Error while waiting for query to finish code={collider_info.result}")
                    if collider_info.result == PhysxPropertyQueryResult.ERROR_TIMEOUT:
                        nonlocal physx_property_query_timeout
                        physx_property_query_timeout = True
                    else:
                        nonlocal physx_property_query_fail
                        physx_property_query_fail = True

            body_path = PhysicsSchemaTools.sdfPathToInt(self._prim.GetPrimPath())
            stage_id = UsdUtils.StageCache.Get().Insert(self._stage).ToLongInt()
            get_physx_property_query_interface().query_prim(stage_id = stage_id, 
                                                            prim_id = body_path,
                                                            query_mode = PhysxPropertyQueryMode.QUERY_RIGID_BODY_WITH_COLLIDERS,
                                                            rigid_body_fn = rigid_info_received,
                                                            collider_fn = report_collider,
                                                            timeout_ms = 2000) # Timeout after 2 sec

            if physx_property_query_timeout:
                # This triggers re-attempting next draw.
                self.invalidate()
                return
            if physx_property_query_fail:
                return

            self._body_bbox_dimensions = bbox_max - bbox_min
            for axis in range(AXIS_NUM):
                self._body_bbox_dimensions[axis] *= self._transform_scale[axis]

            self._body_bbox_center = Gf.Vec3f(0.0)
            for axis in range(AXIS_NUM):
                self._body_bbox_center[axis] = bbox_max[axis] * 0.5 + bbox_min[axis] * 0.5

        # Read USD attributes if present. These have higher priority than what we get from PhysX.
        active_gesture = get_active_gesture()

        mass_api = UsdPhysics.MassAPI(self._prim)
        if (force_update_all or not active_gesture or active_gesture._manipulator != self or active_gesture._gesture is not GESTURE_ROTATE):
            attribute = mass_api.GetPrincipalAxesAttr()
            if attribute.HasAuthoredValue():
                value = attribute.Get()
                if validate_output_quaternion(value):
                    if (value.GetReal() != 0.0 or value.GetImaginary() != Gf.Vec3f(0.0)):
                        body_principal_axes_new = value
                else:
                    carb.log_error(f"Invalid USD value for principal axis: {value}")

            if force_update_all or body_principal_axes_new != self._body_principal_axes:
                self._body_principal_axes = body_principal_axes_new
                self.rebuild_principal_rotate()

        if (force_update_all or not active_gesture or active_gesture._manipulator != self or active_gesture._gesture is not GESTURE_TRANSLATE):
            attribute = mass_api.GetCenterOfMassAttr()
            if attribute.HasAuthoredValue():
                value = attribute.Get()
                if validate_output_array(value, 3):
                    if (value[0] != -inf and value[1] != -inf or value[2] != -inf):
                        body_center_of_mass_new = Gf.Vec3f(*value)
                else:
                    carb.log_error(f"Invalid USD value for center of mass: {value}")

            if force_update_all or body_center_of_mass_new != self._body_center_of_mass:
                self._body_center_of_mass = body_center_of_mass_new
                self.rebuild_center_of_mass_translate()

        if (force_update_all or not active_gesture or active_gesture._manipulator != self or active_gesture._gesture is not GESTURE_SCALE):
            attribute = mass_api.GetMassAttr()
            if attribute.HasAuthoredValue():
                value = attribute.Get()
                if validate_output_float(value):
                    if value != 0.0:
                        body_mass_new = value
                else:
                    carb.log_error(f"Invalid USD value for mass: {value}")

            attribute = mass_api.GetDiagonalInertiaAttr()
            if attribute.HasAuthoredValue():
                value = attribute.Get()
                if validate_output_array(value, 3):
                    if (value[0] != 0.0 or value[0] != 0.0 or value[0] != 0.0):
                        body_diagonal_inertia_new = Gf.Vec3f(*value)
                else:
                    carb.log_error(f"Invalid USD value for diagonal inertia: {value}")

            if force_update_all or body_diagonal_inertia_new != self._body_diagonal_inertia or body_mass_new != self._body_mass:
                self._body_diagonal_inertia = body_diagonal_inertia_new
                self._body_mass = body_mass_new
                self.rebuild_inertia_scale()

        self.rebuild_shape_transforms()

    def _make_shapes(self):

        def draw_box(color, thickness):
            """
            sc.Curve([[0.5, -0.5, -0.5],
                    [-0.5, -0.5, -0.5],
                    [-0.5, -0.5, 0.5],
                    [0.5, -0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, -0.5],
                    [0.5, -0.5, -0.5],
                    [0.5, -0.5, 0.5],
                    [-0.5, -0.5, 0.5],
                    [-0.5, 0.5, 0.5],
                    [0.5, 0.5, 0.5],
                    [0.5, 0.5, -0.5],
                    [-0.5, 0.5, -0.5],
                    [-0.5, -0.5, -0.5],
                    [-0.5, 0.5, -0.5],
                    [-0.5, 0.5, 0.5]],
                    thicknesses=[thickness],
                    colors=[color],
                    curve_type=sc.Curve.CurveType.LINEAR)
            """
            sc.Line([-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], color=color, thickness=thickness)
            sc.Line([-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], color=color, thickness=thickness)
            sc.Line([-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], color=color, thickness=thickness)
            sc.Line([0.5, -0.5, -0.5], [0.5, 0.5, -0.5], color=color, thickness=thickness)
            sc.Line([-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], color=color, thickness=thickness)
            sc.Line([-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], color=color, thickness=thickness)
            sc.Line([-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], color=color, thickness=thickness)
            sc.Line([0.5, -0.5, 0.5], [0.5, 0.5, 0.5], color=color, thickness=thickness)
            sc.Line([-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], color=color, thickness=thickness)
            sc.Line([0.5, -0.5, 0.5], [0.5, -0.5, -0.5], color=color, thickness=thickness)
            sc.Line([-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5], color=color, thickness=thickness)
            sc.Line([0.5, 0.5, 0.5], [0.5, 0.5, -0.5], color=color, thickness=thickness)

        self._transform_pose = sc.Transform(transform=sc.Matrix44.get_scale_matrix(0.0, 0.0, 0.0))
        with self._transform_pose:
            if VISUAL_MASS_DISTRIBUTION_COLLIDER_BOUNDING_BOX:
                self._shape_transform_bbox=sc.Transform()
                with self._shape_transform_bbox:
                    draw_box(COLOR_BBOX, BBOX_LINE_THICKNESS)

            self._transform_center_of_mass = sc.Transform()
            with self._transform_center_of_mass:
                self._transform_principal_rotate = sc.Transform()
                with self._transform_principal_rotate:
                    self._shape_transform_center_of_mass_visualization = sc.Transform(scale_to=sc.Space.SCREEN, look_at=sc.Transform.LookAt.CAMERA)
                    with self._shape_transform_center_of_mass_visualization:
                        size = 45.0
                        subdivisions = 4
                        steps = 3
                        arc_length = 0.75
                        for step in range(steps):
                            for n in range(subdivisions):
                                length = (2 + step) / (steps + 1)
                                angle = math.radians((float(n) + step / 2 - arc_length * 0.5 + 0.5) * 360.0 / subdivisions)
                                angle_end = angle + arc_length * math.radians(360.0 / subdivisions)
                                sc.Arc(size * length, sector=0, begin=angle, end=angle_end, tesselation=(4 + step), color=MASS_DISTRIBUTION_BOX_COLOR, wireframe=True, thickness=1)

                        sc.Line([-size / (steps + 1), 0.0, 0.0], [size / (steps + 1), 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MASS_DISTRIBUTION_BOX_LINE_THICKNESS)
                        sc.Line([0.0, -size / (steps + 1), 0.0], [0.0, size / (steps + 1), 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MASS_DISTRIBUTION_BOX_LINE_THICKNESS)

                    self._shape_transform_inertia_distribution_outer_box = sc.Transform()
                    with self._shape_transform_inertia_distribution_outer_box:
                        draw_box(MASS_DISTRIBUTION_BOX_COLOR, MASS_DISTRIBUTION_BOX_LINE_THICKNESS)

                    if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
                        self._shape_transform_inertia_distribution_cutout_box = sc.Transform()
                        with self._shape_transform_inertia_distribution_cutout_box:
                            draw_box(MASS_DISTRIBUTION_CUTOUT_BOX_COLOR, MASS_DISTRIBUTION_CUTOUT_BOX_LINE_THICKNESS)

                    if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX:
                        self._shape_transform_inertia_distribution_midpoint_box=sc.Transform()
                        with self._shape_transform_inertia_distribution_midpoint_box:
                            draw_box(MASS_DISTRIBUTION_MIDPOINT_BOX_COLOR, MASS_DISTRIBUTION_MIDPOINT_BOX_LINE_THICKNESS)

                    if VISUAL_MASS_DISTRIBUTION_POINT_CLOUD:
                        # Draw inertia point cloud as half cuboids at each corner. This allows adjusting better to center of mass.
                        # Generate points for point cloud visualization.
                        grids_points = []
                        grids_sizes = []
                        grids_colors = []

                        for n in range(INERTIA_POINTS_RESOLUTION):
                            grid_point_count = n + 1
                            grid_point_spacing = 1.0 / float(grid_point_count)
                            grid_points = []
                            grid_sizes = []
                            grid_colors = []

                            for axis in range(AXIS_NUM):
                                if axis == AXIS_X:
                                    axes = [2, 1, 0]
                                elif axis == AXIS_Y:
                                    axes = [0, 2, 1]
                                else:
                                    axes = [0, 1, 2]

                                for x in range(int(grid_point_count)):
                                    # This mysteriously makes the entire inner grid disappear. UI scene bug? Investigate later.
                                    # for y in range(grid_point_count):                    
                                    for y in range(int(grid_point_count + 1)):
                                        grid_point = [0.0, 0.0, 0.0]
                                        grid_point[axes[0]] = (float(x) + 0.5*((y+n)%2)) * grid_point_spacing + grid_point_spacing * 0.25
                                        grid_point[axes[1]] = (float(y) + 0.5*((x)%2)) * grid_point_spacing + grid_point_spacing * 0.25
                                        grid_point[axes[2]] = 1.0 - 0.5 * float((y + x + n)%2) / float(n + 1)
                                    
                                        grid_points.append(grid_point)
                                        color = MASS_DISTRIBUTION_COLOR + 256 * 256 * 256 * int(MASS_DISTRIBUTION_POINTS_MAX_ALPHA * (1.0 - ((sqr(grid_point[axes[0]]) + sqr(grid_point[axes[1]]) + sqr(n / INERTIA_POINTS_RESOLUTION)) / 3.0)))

                                        # For debugging:
                                        #if n < INERTIA_POINTS_RESOLUTION - 1: 
                                        #    color = 0
                                        # else:
                                        #    color = MASS_DISTRIBUTION_COLOR + (256 * 256 * 256 * 255)

                                        if y == grid_point_count:
                                            color = 0
                                        grid_colors.append(color)
                                        grid_sizes.append(MASS_DISTRIBUTION_POINTS_THICKNESS)

                                        if y == grid_point_count:
                                            color = 0

                            grids_points.append(grid_points)
                            grids_sizes.append(grid_sizes)
                            grids_colors.append(grid_colors)

                        self._shape_transform_inertia_distribution_corner.clear()
                        for n in range(BOX_CORNER_NUM):
                            point_distributions = []
                            for _ in range(INERTIA_POINTS_RESOLUTION):
                                point_distributions.append(sc.Transform())
                            self._shape_transform_inertia_distribution_corner.append(point_distributions)

                        for corner in range(BOX_CORNER_NUM):
                            for n in range(INERTIA_POINTS_RESOLUTION):
                                with self._shape_transform_inertia_distribution_corner[corner][n]:
                                    sc.Points(grids_points[n], colors=grids_colors[n], sizes=grids_sizes[n])
                                    # For debugging:
                                    """                        
                                    sc.Line([1.0, 0.0, 1.0], [1.0, 1.0, 1.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([1.0, 1.0, 1.0], [0.0, 1.0, 1.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([0.0, 1.0, 1.0], [0.0, 0.0, 1.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        
                                    sc.Line([0.0, 0.0, 1.0], [1.0, 0.0, 1.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        

                                    sc.Line([1.0, 0.0, 0.0], [1.0, 1.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([1.0, 1.0, 0.0], [0.0, 1.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([0.0, 1.0, 0.0], [0.0, 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        
                                    sc.Line([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        

                                    sc.Line([1.0, 1.0, 1.0], [1.0, 1.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([1.0, 0.0, 1.0], [1.0, 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)
                                    sc.Line([0.0, 1.0, 1.0], [0.0, 1.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        
                                    sc.Line([0.0, 0.0, 1.0], [0.0, 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=1.0)                        
                                    """

    def on_build(self):
        super().on_build()

        if self._viewport_overlay is None:
            self._active = False
            return

        if not self._prim or self._prim is None:
            self._prim = None
            self._active = False
            return

        usd_context = omni.usd.get_context()
        if not usd_context:
            self._active = False
            return

        self._stage=usd_context.get_stage()
        if not self._stage:
            self._active = False
            return

        if not self._prim.HasAPI(UsdPhysics.RigidBodyAPI):
            self._active = False
            return

        self._active = True

        self._rotation_modifier = Gf.Quatf.GetIdentity()

        self._scale_inertia = Gf.Vec3f(0.0)
        self._translate = Gf.Vec3f(0.0)

        self._make_shapes()

        self.populate(True)
        self.refresh()
        self.update_info_text()

    def destroy(self):
        self._prim = None
        super().destroy()

class PhysicsMassDistributionEditManipulator(PhysicsMassManipulator):
    def __init__(self, viewport_overlay, prim):
        super().__init__(viewport_overlay, prim)

        self._snap_settings_listener = None
        self._edit_enabled = True
        self._writing_to_usd = False

        if GESTURE_TEXT_ENABLED:
            self._gesture_text = None
            self._gesture_text_transform = None

        self._shape_transform_scale_inertia_handle = []
        self._shape_transform_scale_inertia_ruler = []

        self._shape_transform_axis = []
        if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
            self._shape_transform_axis_ruler = []
        self._shape_transform_circle = []
        if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS:
            self._shape_transform_circle_ruler = []

    @staticmethod
    def get_toggle_group_by_gesture_direction(gesture, direction):
        return gesture * AXIS_DIRECTION_NUM + direction

    @staticmethod
    def get_toggle_group_by_gesture_axis(gesture, axis):
        return gesture * AXIS_DIRECTION_NUM + axis * 2

    class ApplyMassAPICommand(omni.kit.commands.Command):
        def __init__(self, prim, mass, center_of_mass, diagonal_inertia, principal_axes):
            super().__init__()
            self._prim = prim
            self._mass = mass
            self._center_of_mass = center_of_mass
            self._diagonal_inertia = diagonal_inertia
            self._principal_axes = principal_axes

        def do(self):
            massAPI = UsdPhysics.MassAPI.Apply(self._prim)
            massAPI.GetMassAttr().Set(self._mass)
            massAPI.GetCenterOfMassAttr().Set(self._center_of_mass)
            massAPI.GetDiagonalInertiaAttr().Set(self._diagonal_inertia)
            massAPI.GetPrincipalAxesAttr().Set(self._principal_axes)
            property_window = omni.kit.window.property.get_window()
            if property_window:
                property_window._window.frame.rebuild()            

        def undo(self):
            self._prim.RemoveAPI(UsdPhysics.MassAPI)
            utils.removeAPISchemaProperties(UsdPhysics.MassAPI, self._prim)
            property_window = omni.kit.window.property.get_window()
            if property_window:
                property_window._window.frame.rebuild()            

    def write_to_usd(self, attribute_names, values):
        if not self._prim:
            return

        self._writing_to_usd = True
        omni.kit.undo.begin_group()
        if not self._prim.HasAPI(UsdPhysics.MassAPI):
            omni.kit.commands.execute('ApplyMassAPICommand', prim=self._prim, mass=self._body_mass, 
                center_of_mass=self._body_center_of_mass, diagonal_inertia=self._body_diagonal_inertia, 
                principal_axes=self._body_principal_axes)
        else:
            for n in range(min(len(attribute_names), len(values))):
                attribute = self._prim.GetAttribute(attribute_names[n])
                omni.kit.commands.execute('ChangePropertyCommand', prop_path=attribute.GetPath(), value=values[n],
                    prev=attribute.Get() if attribute else None)
        omni.kit.undo.end_group()
        self._writing_to_usd = False

    def update_gesture_text(self, gesture_coords = None):
        if not GESTURE_TEXT_ENABLED:
            return

        if not self._edit_enabled:
            return

        if self._gesture_text_transform is not None:
            if gesture_coords is None:
                self._gesture_text_transform.visible = False
                return

            active_hover = get_active_hover()
            active_gesture = get_active_gesture()
            gesture = -1

            # Active gesture has precedence over hovering.
            if active_gesture is not None:
                gesture = active_gesture._gesture
            elif active_hover is not None and isinstance(active_hover, PhysicsMassEditHoverGesture):
                gesture = active_hover._gesture

            if gesture == -1:
                self._gesture_text_transform.visible = False
                return

            self._gesture_text_transform.visible = True
            self._gesture_text_transform.transform = sc.Matrix44.get_translation_matrix(*gesture_coords)

            if gesture == GESTURE_SCALE:
                axis = direction_to_axis(active_hover._direction)
                relative_cutout = get_relative_mass_cutout_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia)
                inner_dimensions = get_mass_inner_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)
                outer_dimensions =  get_mass_outer_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)
                self._gesture_text.text = axis_to_string(axis)+": ("+ float_to_string(100.0 * inner_dimensions[axis] / self._body_bbox_dimensions[axis]) +"% / "+float_to_string(100.0 * outer_dimensions[axis] / self._body_bbox_dimensions[axis])+"%)"
            elif gesture == GESTURE_ROTATE:
                matrix = Gf.Matrix4d()
                matrix.SetRotate(self._body_principal_axes*self._rotation_modifier)
                decomposed = Gf.Rotation.DecomposeRotation3(matrix, Gf.Vec3d(*AXIS_VECTOR_X), Gf.Vec3d(*AXIS_VECTOR_Y), Gf.Vec3d(*AXIS_VECTOR_Z), 1.0)
                self._gesture_text.text = axis_to_string(active_hover._axis)+": "+ float_to_string(math.degrees(decomposed[active_hover._axis]))+"°"
            elif gesture == GESTURE_TRANSLATE:
                self._gesture_text.text = float_to_string(self._body_center_of_mass[0]) + "; " + float_to_string(self._body_center_of_mass[1]) + "; " + float_to_string(self._body_center_of_mass[2])

    def update_info_text(self):
        super().update_info_text()
        self._viewport_overlay.refresh_info_box(INFO_BOX_MASS_EDIT)

    def refresh(self):
        super().refresh()

    def rebuild_principal_rotate(self):
        super().rebuild_principal_rotate()

        if not self._edit_enabled:
            return

        if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS:
            decomposed = Gf.Rotation.DecomposeRotation3(Gf.Matrix4d(*self._transform_principal_rotate.transform), Gf.Vec3d(*AXIS_VECTOR_X), Gf.Vec3d(*AXIS_VECTOR_Y), Gf.Vec3d(*AXIS_VECTOR_Z), 1.0)
            self._shape_transform_circle_ruler[AXIS_X].transform =  sc.Matrix44.get_rotation_matrix(-decomposed[0], 0.0, 0.0, False) * sc.Matrix44.get_rotation_matrix(0.0, 90.0, 0.0, True)
            decomposed = Gf.Rotation.DecomposeRotation3(Gf.Matrix4d(*self._transform_principal_rotate.transform), Gf.Vec3d(*AXIS_VECTOR_Y), Gf.Vec3d(*AXIS_VECTOR_Z), Gf.Vec3d(*AXIS_VECTOR_X), 1.0)
            self._shape_transform_circle_ruler[AXIS_Y].transform =  sc.Matrix44.get_rotation_matrix(0.0, -decomposed[0], 0.0, False) * sc.Matrix44.get_rotation_matrix(-90.0, 0.0, 0.0, True)
            decomposed = Gf.Rotation.DecomposeRotation3(Gf.Matrix4d(*self._transform_principal_rotate.transform), Gf.Vec3d(*AXIS_VECTOR_Z), Gf.Vec3d(*AXIS_VECTOR_Y), Gf.Vec3d(*AXIS_VECTOR_X), 1.0)
            self._shape_transform_circle_ruler[AXIS_Z].transform =  sc.Matrix44.get_rotation_matrix(0.0, 0.0, -decomposed[0], False)        

    def rebuild_shape_transforms(self):
        super().rebuild_shape_transforms()

        if not self._edit_enabled:
            return

        if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
            center_of_mass_local = Gf.Vec4f(self._transform_center_of_mass.transform[12], self._transform_center_of_mass.transform[13], self._transform_center_of_mass.transform[14], 0.0) * Gf.Matrix4f(*self._transform_principal_rotate.transform).GetTranspose()
            center_local = Gf.Vec4f(*self._body_bbox_center, 0.0) * Gf.Matrix4f(*self._transform_principal_rotate.transform).GetTranspose()

        relative_cutout = 0.0
        inner_dimensions = Gf.Vec3f(0.0)
        outer_dimensions = Gf.Vec3f(0.0)

        if VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
            scaling_power = []
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_X] / float(self._body_bbox_dimensions[0])) / math.log(0.5) + 1.0)
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_Y] / float(self._body_bbox_dimensions[1])) / math.log(0.5) + 1.0)
            scaling_power.append(math.log(2.0 * self._scale_inertia[AXIS_Z] / float(self._body_bbox_dimensions[2])) / math.log(0.5) + 1.0)
        else:
            relative_cutout = get_relative_mass_cutout_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia)
            inner_dimensions = get_mass_inner_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)
            outer_dimensions =  get_mass_outer_dimensions_from_axial_mass_midpoint(self._body_bbox_dimensions, self._scale_inertia, relative_cutout)

        # Returns the visual scale of an offset from center derived from the midpoints.
        def dimensions_to_scale(offset):
            scale = Gf.Vec3f(0.0)
            if VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
                if offset > 0.0:
                    for axis in range(AXIS_NUM):
                        scale[axis] = math.pow(offset, scaling_power[axis]) * self._body_bbox_dimensions[axis]
            else:
                for axis in range(AXIS_NUM):
                    scale[axis] = (inner_dimensions[axis] + (outer_dimensions[axis] - inner_dimensions[axis]) * offset)
            return scale

        # center_of_mass_local_normalized = center_of_mass_local.GetNormalized()
        # Returns the visual translate of an offset from center derived from the midpoints, center of mass and dimensions.
        def dimensions_to_translate(scale_factor):
            translate = Gf.Vec3f(0.0)
            if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                for axis in range(AXIS_NUM):
                    translate[axis] = (center_local[axis] - center_of_mass_local[axis]) * scale_factor[axis] / self._body_bbox_dimensions[axis]
            return translate

        scale_midpoint = dimensions_to_scale(0.5)
        translate_midpoint = dimensions_to_translate(scale_midpoint)

        translation = Gf.Vec3f(0.0)
        translation_ruler = Gf.Vec3f(0.0)

        # Scaling gesture
        for direction in range(AXIS_DIRECTION_NUM):
            axis = direction_to_axis(direction)
            translate_dir = Gf.Vec3f(0.0)
            translate_dir[axis] = 0.5 * scale_midpoint[axis] if mod(direction, 2) == 0 else -0.5 * scale_midpoint[axis]
            
            # Midpoint handles.
            translation = Gf.Vec3f(0.0) # center_of_mass_local[0:3]
            translation[axis] = translate_midpoint[axis]
            self._shape_transform_scale_inertia_handle[direction].transform = sc.Matrix44.get_translation_matrix(*translation) * sc.Matrix44.get_translation_matrix(*translate_dir) # sc.Matrix44.get_translation_matrix(*translate_midpoint) * sc.Matrix44.get_translation_matrix(*translation_handle)
        
            if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX and False:
                translation_ruler = translation
                translation_ruler[axis] = center_of_mass_local[axis]
            else:
                translation_ruler = Gf.Vec3f(0.0)

            # Midpoint scaling rulers.
            self._shape_transform_scale_inertia_ruler[direction].transform= sc.Matrix44.get_translation_matrix(*translation_ruler)
            scaling_ruler = Gf.Vec3f(1.0)
            if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                scaling_ruler[axis] = 0.5 * self._body_bbox_dimensions[axis] + (center_of_mass_local[axis] - center_local[axis]) * ( 1.0 if mod(direction, 2) == 1.0 else -1.0)
            else:
                scaling_ruler[axis] = 0.5 * self._body_bbox_dimensions[axis]
            self._shape_transform_scale_inertia_ruler[direction].transform *= sc.Matrix44.get_scale_matrix(*scaling_ruler)

        # Translation gesture
        if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
            for axis in range(AXIS_NUM):
                if axis == 0:
                    rotation = Gf.Vec3f(90.0, 0.0, 0.0)
                    axes = [0, 1, 2]
                elif axis == 1:
                    rotation = Gf.Vec3f(0.0, 0.0, -90.0)
                    axes = [1, 2, 0]                
                else:
                    rotation = Gf.Vec3f(0.0, 90.0, 0.0)
                    axes = [2, 1, 0]

                mat44_direction_rotate = sc.Matrix44.get_rotation_matrix(*rotation, True)
                translation = Gf.Vec3f(0.0)
                translation[axis] = -center_of_mass_local[axis] + center_local[axis]
                self._shape_transform_axis_ruler[axis].transform = sc.Matrix44.get_translation_matrix(*translation) * mat44_direction_rotate * sc.Matrix44.get_scale_matrix(self._body_bbox_dimensions[axes[0]] * 0.5, 1.0, 1.0)

    def set_edit_enabled(self, enabled):
        if enabled != self._edit_enabled:
            self._edit_enabled = enabled
            self.invalidate()

    def _make_shapes(self):
        super()._make_shapes()

        if not self._edit_enabled:
            return

        with self._transform_pose:
            if GESTURE_TEXT_ENABLED:
                self._gesture_text_transform = sc.Transform()
                with self._gesture_text_transform:
                    with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                        with sc.Transform(transform=sc.Matrix44.get_translation_matrix(*GESTURE_TEXT_OFFSET, 0.01)):                    
                            self._gesture_text = sc.Label(
                            " ",
                                alignment=ui.Alignment.CENTER,
                                color=GESTURE_TEXT_FONT_COLOR,
                                size=GESTURE_TEXT_FONT_SIZE
                            )

            self._snap_settings_listener = SnapSettingsListener(
                enabled_setting_path=None,
                move_x_setting_path=snap_c.SNAP_TRANSLATE_SETTING_PATH,
                move_y_setting_path=snap_c.SNAP_TRANSLATE_SETTING_PATH,
                move_z_setting_path=snap_c.SNAP_TRANSLATE_SETTING_PATH,
                rotate_setting_path=snap_c.SNAP_ROTATE_SETTING_PATH,
                scale_setting_path=snap_c.SNAP_SCALE_SETTING_PATH,
                provider_setting_path=snap_c.SNAP_PROVIDER_NAME_SETTING_PATH,
            )

            # Generate data for arrowheads.
            translate_arrow_face_count = 24
            translate_arrow_vertex_indices = []
            translate_arrow_points_front = [[0, 0, CENTER_OF_MASS_AXIS_HALF_LENGTH]]
            translate_arrow_faces_vertex_count = []
            angle = 0.0
            angle_cos = 1.0
            angle_sin = 0.0
            translate_arrow_points_front.append(
                [
                    angle_cos * CENTER_OF_MASS_AXIS_ARROW_RADIUS,
                    angle_sin * CENTER_OF_MASS_AXIS_ARROW_RADIUS,
                    CENTER_OF_MASS_AXIS_HALF_LENGTH - CENTER_OF_MASS_AXIS_ARROW_LENGTH
                ])
            for i in range(translate_arrow_face_count):
                angle += 2.0 * math.pi / translate_arrow_face_count
                angle_cos = math.cos(angle)
                angle_sin = math.sin(angle)
                translate_arrow_points_front.append(                    
                    [
                        angle_cos * CENTER_OF_MASS_AXIS_ARROW_RADIUS,
                        angle_sin * CENTER_OF_MASS_AXIS_ARROW_RADIUS,
                        CENTER_OF_MASS_AXIS_HALF_LENGTH - CENTER_OF_MASS_AXIS_ARROW_LENGTH
                    ])
                translate_arrow_vertex_indices.append(0)
                translate_arrow_vertex_indices.append(len(translate_arrow_points_front) - 2)
                translate_arrow_vertex_indices.append(len(translate_arrow_points_front) - 1)

                translate_arrow_faces_vertex_count.append(3)

            translate_arrow_points_back = translate_arrow_points_front.copy()
            translate_arrow_points_back[0] = [0, 0, CENTER_OF_MASS_AXIS_HALF_LENGTH - CENTER_OF_MASS_AXIS_ARROW_LENGTH]

            if MASS_DISTRIBUTION_HANDLE_ARROW:
                scale_arrow_face_count = 4
                scale_arrow_vertex_indices = []
                scale_arrow_faces_vertex_count = []
                scale_arrow_points_front = [[0, 0, MASS_DISTRIBUTION_HANDLE_ARROW_SIZE]]
                angle = math.radians(45.0)
                angle_cos = math.cos(angle)
                angle_sin = math.sin(angle)
                scale_arrow_points_front.append(
                    [
                        angle_cos * MASS_DISTRIBUTION_HANDLE_ARROW_SIZE * 0.707,
                        angle_sin * MASS_DISTRIBUTION_HANDLE_ARROW_SIZE * 0.707,
                        0.0
                    ])
                for i in range(scale_arrow_face_count):
                    angle += 2.0 * math.pi / scale_arrow_face_count
                    angle_cos = math.cos(angle)
                    angle_sin = math.sin(angle)
                    scale_arrow_points_front.append(                    
                        [
                            angle_cos * MASS_DISTRIBUTION_HANDLE_ARROW_SIZE * 0.707,
                            angle_sin * MASS_DISTRIBUTION_HANDLE_ARROW_SIZE * 0.707,
                            0.0
                        ])
                    scale_arrow_vertex_indices.append(0)
                    scale_arrow_vertex_indices.append(len(scale_arrow_points_front) - 2)
                    scale_arrow_vertex_indices.append(len(scale_arrow_points_front) - 1)

                    scale_arrow_faces_vertex_count.append(3)

            self._shape_transform_scale_inertia_handle.clear()
            self._shape_transform_scale_inertia_ruler.clear()

            for direction in range(AXIS_DIRECTION_NUM):

                if direction == AXIS_DIRECTION_X_POS:
                    rotation = Gf.Vec3f(0.0, 90.0, 0.0)
                elif direction == AXIS_DIRECTION_X_NEG:
                    rotation = Gf.Vec3f(0.0, -90.0, 0.0)
                elif direction == AXIS_DIRECTION_Y_POS:
                    rotation = Gf.Vec3f(-90.0, 0.0, 0.0)
                elif direction == AXIS_DIRECTION_Y_NEG:
                    rotation = Gf.Vec3f(90.0, 0.0, 0.0)
                elif direction == AXIS_DIRECTION_Z_POS:
                    rotation = Gf.Vec3f(0.0, 0.0, -90.0)
                elif direction == AXIS_DIRECTION_Z_NEG:
                    rotation = Gf.Vec3f(180.0, 0.0, 90.0)
                mat44_direction_rotate = sc.Matrix44.get_rotation_matrix(*rotation, True)
                
                with self._transform_center_of_mass:
                    with self._transform_principal_rotate:
                        self._shape_transform_scale_inertia_handle.append(sc.Transform())
                        with self._shape_transform_scale_inertia_handle[direction]:
                            visibility = sc.Transform(visible=False)
                            self.add_to_toggles(VisibilityToggle(visibility), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction))
                            with visibility:
                                with sc.Transform(scale_to=sc.Space.SCREEN, transform=mat44_direction_rotate):
                                    cross_size = MASS_DISTRIBUTION_HANDLE_SIZE * 4.0
                                    sc.Line([-cross_size * 0.5, 0.0, 0.0], [cross_size * 0.5, 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MAIN_LINE_THICKNESS)
                                    sc.Line([0.0, -cross_size * 0.5, 0.0], [0.0, cross_size * 0.5, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MAIN_LINE_THICKNESS)

                            if MASS_DISTRIBUTION_HANDLE_RECTANGLE:
                                with sc.Transform(scale_to=sc.Space.SCREEN):
                                    for n in range(MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_COUNT):
                                        color = MASS_DISTRIBUTION_COLOR + 256 * 256 * 256 * int(MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_ALPHA * (1.0 - n / (MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_COUNT)))
                                        z = - 0.65 * MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE * (n + 1) / (MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_COUNT)
                                        size = MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE * ( 1.0  - 0.35 * (n + 1 )/ (MASS_DISTRIBUTION_HANDLE_RECTANGLE_TRAIL_COUNT))
                                        with sc.Transform(transform = mat44_direction_rotate):
                                            sc.Line([-size * 0.5, -size * 0.5, z], [size * 0.5, -size * 0.5, z], color=color, thickness=1.0)
                                            sc.Line([size * 0.5, -size * 0.5, z], [size * 0.5, size * 0.5, z], color=color, thickness=1.0)
                                            sc.Line([size * 0.5, size * 0.5, z], [-size * 0.5, size * 0.5, z], color=color, thickness=1.0)
                                            sc.Line([-size * 0.5, size * 0.5, z], [-size * 0.5, -size * 0.5, z], color=color, thickness=1.0)
                                    with sc.Transform(transform = mat44_direction_rotate):
                                        shape = sc.Rectangle(wireframe=True, thickness=HOVER_LINE_THICKNESS, width=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE + HOVER_LINE_THICKNESS * 2, height=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE + HOVER_LINE_THICKNESS, color=COLOR_INVISIBLE)
                                        self.add_to_toggles(HighlightToggle(shape), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction))
                                        sc.Rectangle(width=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE, height=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE, color=COLOR_AXIS_SHADED[direction_to_axis(direction)])
                                        with sc.Transform(transform=sc.Matrix44.get_translation_matrix(0.0, 0.0, 0.01)):
                                            sc.Rectangle(width=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE, height=MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE, color=COLOR_AXIS[direction_to_axis(direction)])

                                # Invisible handle for the actual interaction.
                                with sc.Transform(look_at=sc.Transform.LookAt.CAMERA, scale_to=sc.Space.SCREEN):
                                    sc.Arc(MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE / 2 + HOVER_LINE_THICKNESS, color=COLOR_INVISIBLE, gesture=[PhysicsMassEditGestureScale(self, direction), PhysicsMassEditHoverGesture(self, GESTURE_SCALE, direction)])
                            else:
                                with sc.Transform(look_at=sc.Transform.LookAt.CAMERA, scale_to=sc.Space.SCREEN):
                                    # Always render this behind:
                                    with sc.Transform(transform=sc.Matrix44.get_translation_matrix(0.0, 0.0, -0.01)):
                                        shape = sc.Arc(MASS_DISTRIBUTION_HANDLE_SIZE / 2 + HOVER_LINE_THICKNESS, color=COLOR_INVISIBLE, gesture=[PhysicsMassEditGestureScale(self, direction), PhysicsMassEditHoverGesture(self, GESTURE_SCALE, direction)])
                                        self.add_to_toggles(HighlightToggle(shape), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction))
                                    sc.Arc(MASS_DISTRIBUTION_HANDLE_SIZE / 2, color=COLOR_AXIS[direction_to_axis(direction)])

                            if MASS_DISTRIBUTION_HANDLE_ARROW:
                                with sc.Transform(scale_to=sc.Space.SCREEN):
                                    with sc.Transform(transform = mat44_direction_rotate):
                                        with sc.Transform(transform=sc.Matrix44.get_translation_matrix(0.0, 0.0, (MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE / 2 if MASS_DISTRIBUTION_HANDLE_RECTANGLE else MASS_DISTRIBUTION_HANDLE_SIZE))):
                                            sc.Rectangle(width=MASS_DISTRIBUTION_HANDLE_ARROW_SIZE, height=MASS_DISTRIBUTION_HANDLE_ARROW_SIZE, color=COLOR_AXIS_SHADED[direction_to_axis(direction)])
                                            sc.PolygonMesh(scale_arrow_points_front, ([COLOR_AXIS[direction_to_axis(direction)]] * 3 + [COLOR_AXIS_SHADED[direction_to_axis(direction)]] * 3) * int(scale_arrow_face_count / 2), scale_arrow_faces_vertex_count, scale_arrow_vertex_indices)
                                        with sc.Transform(transform = sc.Matrix44.get_rotation_matrix(0.0, 180.0, 0.0, True)):
                                            with sc.Transform(transform=sc.Matrix44.get_translation_matrix(0.0, 0.0, (MASS_DISTRIBUTION_HANDLE_RECTANGLE_SIZE / 2 if MASS_DISTRIBUTION_HANDLE_RECTANGLE else MASS_DISTRIBUTION_HANDLE_SIZE))):
                                                sc.Rectangle(width=MASS_DISTRIBUTION_HANDLE_ARROW_SIZE, height=MASS_DISTRIBUTION_HANDLE_ARROW_SIZE, color=COLOR_AXIS[direction_to_axis(direction)])
                                                sc.PolygonMesh(scale_arrow_points_front, ([COLOR_AXIS[direction_to_axis(direction)]] * 3 + [COLOR_AXIS_SHADED[direction_to_axis(direction)]] * 3) * int(scale_arrow_face_count / 2), scale_arrow_faces_vertex_count, scale_arrow_vertex_indices)

                        self._shape_transform_scale_inertia_ruler.append(sc.Transform())
                        with self._shape_transform_scale_inertia_ruler[direction]:
                            visibility = sc.Transform(visible=False)
                            self.add_to_toggles(VisibilityToggle(visibility), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, int(direction / 2) * 2))
                            self.add_to_toggles(VisibilityToggle(visibility), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, int(direction / 2) * 2 + 1))
                            with visibility:
                                with sc.Transform(transform = mat44_direction_rotate):
                                    ruler_line_thickness = 1.0
                                    sc.Line([0.0, 0.0, 0.0], [0.0, 0.0, 1.0], color=COLOR_AXIS_SHADED[direction_to_axis(direction)], thickness=ruler_line_thickness)
                                    ruler_segments = 2
                                    ruler_width = MASS_DISTRIBUTION_HANDLE_SIZE * 4.0
                                    for n in range(ruler_segments + 1):
                                        offset = float(n) / float(ruler_segments)
                                        if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS or offset == 1.0:
                                            with sc.Transform(transform=sc.Matrix44.get_translation_matrix(0.0, 0.0, offset)):
                                                with sc.Transform(scale_to=sc.Space.SCREEN):
                                                    sc.Line([-ruler_width * 0.5, 0.0, 0.0], [ruler_width * 0.5, 0.0, 0.0], color=COLOR_AXIS_SHADED[direction_to_axis(direction)], thickness=ruler_line_thickness)
                                                    sc.Line([0.0, -ruler_width * 0.5, 0.0], [ 0.0, ruler_width * 0.5, 0.0], color=COLOR_AXIS_SHADED[direction_to_axis(direction)], thickness=ruler_line_thickness)

                        with sc.Transform(transform = mat44_direction_rotate):
                            with sc.Transform(scale_to=sc.Space.SCREEN):
                                sc.PolygonMesh(translate_arrow_points_front, [COLOR_AXIS[direction_to_axis(direction)]] * 3 * translate_arrow_face_count, translate_arrow_faces_vertex_count, translate_arrow_vertex_indices)
                                sc.PolygonMesh(translate_arrow_points_back, [COLOR_AXIS_SHADED[direction_to_axis(direction)]] * 3 * translate_arrow_face_count, translate_arrow_faces_vertex_count, translate_arrow_vertex_indices)

            self._shape_transform_axis.clear()
            if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                self._shape_transform_axis_ruler.clear()
            self._shape_transform_circle.clear()
            if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS:
                self._shape_transform_circle_ruler.clear()

            for axis in range(AXIS_NUM):
                if axis == AXIS_X:
                    rotation_circle = Gf.Vec3f(0.0, 90.0, 0.0)
                    rotation_axis = Gf.Vec3f(90.0, 0.0, 0.0)
                elif axis == AXIS_Y:
                    rotation_circle = Gf.Vec3f(-90.0, 0.0, 0.0)
                    rotation_axis = Gf.Vec3f(0.0, 0.0, -90.0)
                elif axis == AXIS_Z:
                    rotation_circle = Gf.Vec3f(0.0, 0.0, 0.0)
                    rotation_axis = Gf.Vec3f(0.0, 90.0, 0.0)

                with self._transform_center_of_mass:
                    with self._transform_principal_rotate:                    
                        self._shape_transform_axis.append(sc.Transform(transform=sc.Matrix44.get_rotation_matrix(*rotation_axis, True)))
                        with self._shape_transform_axis[axis]:
                            with sc.Transform(scale_to=sc.Space.SCREEN):
                                shape = sc.Line([-CENTER_OF_MASS_AXIS_HALF_LENGTH+CENTER_OF_MASS_AXIS_ARROW_LENGTH, 0.0, 0.0], [CENTER_OF_MASS_AXIS_HALF_LENGTH-CENTER_OF_MASS_AXIS_ARROW_LENGTH, 0.0, 0.0], color=COLOR_INVISIBLE, thickness=MAIN_LINE_THICKNESS+HOVER_LINE_THICKNESS, gesture=[PhysicsMassEditGestureTranslate(self, axis), PhysicsMassEditHoverGesture(self, GESTURE_TRANSLATE, axis * 2)])
                                self.add_to_toggles(HighlightToggle(shape), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_TRANSLATE, axis))
                                sc.Line([-CENTER_OF_MASS_AXIS_HALF_LENGTH+CENTER_OF_MASS_AXIS_ARROW_LENGTH, 0.0, 0.0], [CENTER_OF_MASS_AXIS_HALF_LENGTH-CENTER_OF_MASS_AXIS_ARROW_LENGTH, 0.0, 0.0], color=COLOR_AXIS[axis], thickness=MAIN_LINE_THICKNESS)

                        if VISUAL_MASS_DISTRIBUTION_NONUNIFORM:
                            self._shape_transform_axis_ruler.append(sc.Transform())
                            with self._shape_transform_axis_ruler[axis]:
                                visibility = sc.Transform(visible=False)
                                self.add_to_toggles(VisibilityToggle(visibility), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_TRANSLATE, axis))
                                ruler_line_thickness = 1.0
                                ruler_segments = 4
                                ruler_width = MASS_DISTRIBUTION_HANDLE_SIZE * 4.0
                                with visibility:
                                    sc.Line([-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], color=COLOR_AXIS_SHADED[axis], thickness=ruler_line_thickness)
                                    for n in range(ruler_segments + 1):
                                        offset = 2.0 * float(n) / float(ruler_segments) - 1.0
                                        if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS or offset == 1.0 or offset == -1.0:
                                            with sc.Transform(transform=sc.Matrix44.get_translation_matrix(offset, 0.0, 0.0)):
                                                with sc.Transform(scale_to=sc.Space.SCREEN):
                                                    sc.Line([0.0, -ruler_width * 0.5, 0.0], [0.0, ruler_width * 0.5, 0.0], color=COLOR_AXIS_SHADED[axis], thickness=ruler_line_thickness)
                                                    sc.Line([0.0, 0.0, -ruler_width * 0.5], [0.0, 0.0, ruler_width * 0.5], color=COLOR_AXIS_SHADED[axis], thickness=ruler_line_thickness)

                        self._shape_transform_circle.append(sc.Transform(transform=sc.Matrix44.get_rotation_matrix(*rotation_circle, True)))
                        with self._shape_transform_circle[axis]:
                            with sc.Transform(scale_to=sc.Space.SCREEN):
                                shape = sc.Arc(CENTER_OF_MASS_AXIS_HALF_LENGTH, tesselation=PRINCIPAL_AXIS_ROTATION_ARC_TESSELATION, color=COLOR_INVISIBLE, wireframe=True, thickness=MAIN_LINE_THICKNESS+HOVER_LINE_THICKNESS, gesture=[PhysicsMassEditGestureRotate(self, axis), PhysicsMassEditHoverGesture(self, GESTURE_ROTATE, axis * 2)])
                                self.add_to_toggles(HighlightToggle(shape), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_ROTATE, axis))
                                sc.Arc(CENTER_OF_MASS_AXIS_HALF_LENGTH, tesselation=PRINCIPAL_AXIS_ROTATION_ARC_TESSELATION, color=COLOR_AXIS[axis], wireframe=True, thickness=MAIN_LINE_THICKNESS)

                        if VISUAL_MASS_DISTRIBUTION_RULER_SUBDIVISION_MARKERS:
                            self._shape_transform_circle_ruler.append(sc.Transform())
                            with self._shape_transform_circle_ruler[axis]:
                                with sc.Transform(scale_to=sc.Space.SCREEN):
                                    for n in range(16):
                                        length = 0.1
                                        if mod(n, 4) == 0:
                                            length = 0.3
                                        elif mod(n, 2) == 0:
                                            length = 0.2
                                        angle = math.radians(float(n) * 22.5)
                                        x = CENTER_OF_MASS_AXIS_HALF_LENGTH * math.cos( angle)
                                        y = CENTER_OF_MASS_AXIS_HALF_LENGTH * math.sin( angle)
                                        sc.Line([x, y, 0.0], [x * (1.0 - length), y * (1.0 - length), 0.0], color=COLOR_AXIS_SHADED[axis], thickness=1)

    def destroy(self):
        if self._snap_settings_listener is not None:
            self._snap_settings_listener = None
        super().destroy()


VISUAL_MASS_DISTRIBUTION_VIEW_ICON_SIZE = Gf.Vec2f(40.0, 50.0)

# Handles hover highlighting etc. for manipulation gestures.
class PhysicsMassViewInfoHoverGesture(PhysicsHoverGesture):

    def __init__(self, manipulator):
        super().__init__(manipulator, 0)

    def on_began(self):
        if get_active_hover() is not None:
            return
        super().on_began()
        self._manipulator.populate(True)
        self._manipulator.get_viewport_overlay().set_info_box_target(INFO_BOX_MASS_VIEW, self._manipulator)

    def on_ended(self):
        super().on_ended()
        if self._manipulator.get_viewport_overlay().get_info_box_target(INFO_BOX_MASS_VIEW) == self._manipulator:
            self._manipulator.get_viewport_overlay().set_info_box_target(INFO_BOX_MASS_VIEW, None)

class GestureAlwaysPassClick(sc.GestureManager):
    def can_be_prevented(self, gesture):
        return False

    def should_prevent(self, gesture, preventer):
        return False

class PhysicsMassViewInfoClickGesture(sc.ClickGesture):

    def __init__(self, manipulator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manipulator = manipulator

    def on_ended(self):
        active_gesture = get_active_gesture()
        if active_gesture is not None:
            if active_gesture._manipulator != self._manipulator:
                return
        active_hover = get_active_hover()
        if active_hover is not None:
            if active_hover._manipulator != self._manipulator:
                return False

        path = self._manipulator._prim.GetPrimPath().pathString
        input = self._manipulator.get_viewport_overlay()._main_viewport_overlay._input
        keyboard = self._manipulator.get_viewport_overlay()._main_viewport_overlay._keyboard
        if (input.get_keyboard_value(keyboard, carb.input.KeyboardInput.LEFT_CONTROL) 
            or input.get_keyboard_value(keyboard, carb.input.KeyboardInput.RIGHT_CONTROL)):
            self._manipulator.get_viewport_overlay().toggle_in_selection(path)
        elif (input.get_keyboard_value(keyboard, carb.input.KeyboardInput.LEFT_SHIFT) 
            or input.get_keyboard_value(keyboard, carb.input.KeyboardInput.RIGHT_SHIFT)):
            self._manipulator.get_viewport_overlay().add_to_selection(path)
        else:
            self._manipulator.get_viewport_overlay().set_selection(path)


class PhysicsMassPropertiesViewManipulator(PhysicsMassManipulator):

    def __init__(self, viewport_overlay, prim):
        super().__init__(viewport_overlay, prim)

    def update_info_text(self):
        super().update_info_text()
        self._viewport_overlay.refresh_info_box(INFO_BOX_MASS_VIEW)

    def _make_shapes(self):
        super()._make_shapes()
        with self._transform_pose:
            with sc.Transform(scale_to=sc.Space.SCREEN, look_at=sc.Transform.LookAt.CAMERA):
                CURRENT_PATH = Path(__file__).parent.joinpath("../../../icons/physicsMass")
                filename = f"{CURRENT_PATH}/mass_info_weight_on.png"
                image_shape = sc.Image(filename, width=VISUAL_MASS_DISTRIBUTION_VIEW_ICON_SIZE[0], height=VISUAL_MASS_DISTRIBUTION_VIEW_ICON_SIZE[1], gesture=[PhysicsMassViewInfoClickGesture(self, manager=GestureAlwaysPassClick()), PhysicsMassViewInfoHoverGesture(self)])
                filename_off = f"{CURRENT_PATH}/mass_info_weight_off.png"
                self.add_to_toggles(ImageToggle(image_shape, filename, filename_off))

            self.add_to_toggles(VisibilityToggle(self._shape_transform_center_of_mass_visualization))
            self.add_to_toggles(VisibilityToggle(self._shape_transform_inertia_distribution_outer_box))

            if not VISUAL_MASS_DISTRIBUTION_SCALING_EXPONENTIAL:
                self.add_to_toggles(VisibilityToggle(self._shape_transform_inertia_distribution_cutout_box))

            if VISUAL_MASS_DISTRIBUTION_MIDPOINT_BOX:
                self.add_to_toggles(VisibilityToggle(self._shape_transform_inertia_distribution_midpoint_box))

            if VISUAL_MASS_DISTRIBUTION_COLLIDER_BOUNDING_BOX:
                self.add_to_toggles(VisibilityToggle(self._shape_transform_bbox))

            if VISUAL_MASS_DISTRIBUTION_POINT_CLOUD:
                for corner in self._shape_transform_inertia_distribution_corner:
                    for offset in corner:
                        self.add_to_toggles(VisibilityToggle(offset))

    def populate(self, force_update_all = False):
        if not self._active:
            self.invalidate()
            return

        if not self._prim.HasAPI(UsdPhysics.RigidBodyAPI):
            self.invalidate()
            return

        if not self._shape_transform_center_of_mass_visualization.visible:
            if not self._prim:
                return
            # Only update Xform:
            xfCache = UsdGeom.XformCache()
            xform = Gf.Transform(xfCache.GetLocalToWorldTransform(self._prim))
            xform.SetScale(Gf.Vec3d(1.0))
            xform_mat = xform.GetMatrix()
            self._transform_pose.transform = sc.Matrix44(*xform_mat[0], *xform_mat[1], *xform_mat[2], *xform_mat[3])
            return

        super().populate(force_update_all)


VISUAL_MASS_DISTRIBUTION_VIEW_INFO_BOX_OFFSET = Gf.Vec3f(VISUAL_MASS_DISTRIBUTION_VIEW_ICON_SIZE[0] * 0.5 + 20.0, -(VISUAL_MASS_DISTRIBUTION_VIEW_ICON_SIZE[0] * 0.5) -20.0, 0.0)

class PhysicsMassInfoBoxManipulator(sc.Manipulator):

    def __init__(self, viewport_overlay):
        super().__init__()
        self._viewport_overlay = viewport_overlay
        self._stage = None
        self._mass_info_text_header = None
        self._mass_info_text_title = [None] * MASS_INFO_TEXT_ENTRY_NUM
        self._mass_info_text_value = [None] * MASS_INFO_TEXT_ENTRY_NUM
        self._mass_info_text_footer = None
        self._mass_info_text_transform_outer = None
        self._mass_info_text_transform_inner_offset_world = None
        self._mass_info_text_transform_inner_offset_screen = None
        self._mass_info_text_transform_header = None
        self._mass_info_text_transform_titles = None
        self._mass_info_text_transform_values = None
        self._mass_info_text_transform_footer = None
        self._mass_info_background = None
        self._mass_info_background_transform = None
        self._accumulated_center_of_mass = None
        self._mass_manipulators = None

    def refresh(self):
        if self._mass_info_text_transform_outer is None:
            self.invalidate()
            return
        if self._mass_manipulators is None:
            self._mass_info_text_transform_outer.visible = False
            return

        mass_manipulators = self._mass_manipulators
        # Even if only being tied to a single manipulator, put it into an array for code simplicity below.
        if not isinstance(self._mass_manipulators, collections.abc.Sized):
            mass_manipulators = [self._mass_manipulators]
        elif len(self._mass_manipulators) < 1:
            self._mass_info_text_transform_outer.visible = False
            return

        self._mass_info_text_transform_outer.visible = True
        multiple_prims = True if len(mass_manipulators) > 1 else False

        # For accumulating when multiple prims are selected.
        total_mass = 0.0
        bbox_min = Gf.Vec3f(inf)
        bbox_max = Gf.Vec3f(-inf)

        txt_center_of_mass = "-"
        txt_principal_axis = "-"
        txt_diagonal_inertia = "-"

        xfCache = UsdGeom.XformCache()
        info_box_offset_mod = 0.0

        txt_footer = []

        if multiple_prims:
            prim_path = "Multiple selected"
            self._accumulated_center_of_mass = Gf.Vec3f(0.0)
            for manipulator in mass_manipulators:
                prim = manipulator._prim
                xform_mat = xfCache.GetLocalToWorldTransform(prim)

                prim_bbox_min = manipulator._body_bbox_center - 0.5 * manipulator._body_bbox_dimensions
                prim_bbox_max = manipulator._body_bbox_center + 0.5 * manipulator._body_bbox_dimensions

                info_box_offset_mod += (Gf.Vec3f(prim_bbox_max[0:3]) - Gf.Vec3f(prim_bbox_min[0:3])).GetLength()

                # Estimate combined bounding box.
                for n in range(BOX_CORNER_NUM):
                    corner = Gf.Vec4d(0.0, 0.0, 0.0, 1.0)
                    if n < 4:
                        corner[2] = prim_bbox_min[2]
                    else:
                        corner[2] = prim_bbox_max[2]
                    if n % 2 == 0:
                        corner[1] = prim_bbox_min[1]
                    else: 
                        corner[1] = prim_bbox_max[1]
                    if n < 2 or (n > 3 and n < 6):
                        corner[0] = prim_bbox_min[0]
                    else: 
                        corner[0] = prim_bbox_max[0]
                    corner = corner * xform_mat
                    for axis in range(AXIS_NUM):
                        bbox_min[axis] = min(bbox_min[axis], corner[axis])
                        bbox_max[axis] = max(bbox_max[axis], corner[axis])

                total_mass += manipulator._body_mass
                prim_center_of_mass = Gf.Vec4d(*manipulator._body_center_of_mass, 1.0) * xform_mat
                self._accumulated_center_of_mass += Gf.Vec3f(*prim_center_of_mass[0:3]) * manipulator._body_mass

            if total_mass > 0.0:
                self._accumulated_center_of_mass = self._accumulated_center_of_mass * (1.0 / total_mass)

            info_box_offset_mod = min(info_box_offset_mod, (Gf.Vec3f(bbox_max[0:3]) - Gf.Vec3f(bbox_min[0:3])).GetLength())
            info_box_offset_mod = 0.5 * info_box_offset_mod
            info_box_position = Gf.Vec3f(bbox_max[0:3]) * 0.5 + Gf.Vec3f(bbox_min[0:3]) * 0.5
            self._mass_info_text_transform_inner_offset_world.transform = sc.Matrix44.get_translation_matrix(0.0, info_box_offset_mod * 0.5, 0.0)
            info_box_offset = Gf.Vec3f(-MASS_INFO_TEXT_BOX_WIDTH / 2, 0, 0)
            self._mass_info_text_transform_inner_offset_screen.transform = sc.Matrix44.get_translation_matrix(*info_box_offset)

        else: # Single prim
            prim_path = str(mass_manipulators[0]._prim.GetPrimPath())
            # Truncate if exceeding 20 characters. Note: since the font is not monotype, the actual width may vary.
            if len(prim_path) > 20:
                prim_path = "..."+prim_path[-17:]
            txt_center_of_mass = (float_to_string(mass_manipulators[0]._body_center_of_mass[0], 1)+"; "+
                                float_to_string(mass_manipulators[0]._body_center_of_mass[1], 1)+"; " + 
                                float_to_string(mass_manipulators[0]._body_center_of_mass[2], 1))
            matrix = Gf.Matrix4d()
            matrix.SetRotate(mass_manipulators[0]._body_principal_axes*mass_manipulators[0]._rotation_modifier)
            decomposed = Gf.Rotation.DecomposeRotation3(matrix, Gf.Vec3d(*AXIS_VECTOR_X), Gf.Vec3d(*AXIS_VECTOR_Y), Gf.Vec3d(*AXIS_VECTOR_Z), 1.0)
            txt_principal_axis = float_to_string(math.degrees(decomposed[0]))+"°; "+float_to_string(math.degrees(decomposed[1]))+"°; " + float_to_string(math.degrees(decomposed[2]))+"°"
            txt_diagonal_inertia = "X: "+float_to_string(mass_manipulators[0]._body_diagonal_inertia[0])+"\nY: "+float_to_string(mass_manipulators[0]._body_diagonal_inertia[1])+"\nZ: " + float_to_string(mass_manipulators[0]._body_diagonal_inertia[2])

            total_mass = mass_manipulators[0]._body_mass

            if isinstance(self, PhysicsMassEditInfoBoxManipulator):
                info_box_offset_mod = (mass_manipulators[0]._body_bbox_dimensions * 0.5).GetLength()
                info_box_offset = Gf.Vec3f(*([info_box_offset_mod] * 2), -1.0)
                self._mass_info_text_transform_inner_offset_world.transform = sc.Matrix44.get_translation_matrix(*info_box_offset)
                self._mass_info_text_transform_inner_offset_screen.transform = sc.Matrix44() # Reset in case we had multiple selected last refresh.
                info_box_position = (Gf.Vec4d(*mass_manipulators[0]._body_bbox_center, 1.0) * xfCache.GetLocalToWorldTransform(mass_manipulators[0]._prim))[0:3]
            else:
                info_box_position = (xfCache.GetLocalToWorldTransform(mass_manipulators[0]._prim)).ExtractTranslation() # Gf.Vec3f(0.0) # manipulator._body_center_of_mass # Gf.Vec3f(bbox_max[0:3]) * 0.5 + Gf.Vec3f(bbox_min[0:3]) * 0.5 
                self._mass_info_text_transform_inner_offset_screen.transform = sc.Matrix44.get_translation_matrix(*VISUAL_MASS_DISTRIBUTION_VIEW_INFO_BOX_OFFSET)

            if mass_manipulators[0]._prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                collision_API = UsdPhysics.MeshCollisionAPI(mass_manipulators[0]._prim)
                approximation = collision_API.GetApproximationAttr().Get()

                if approximation == UsdPhysics.Tokens.none:
                    txt_footer.append("WARNING:")
                    txt_footer.append("Triangle Mesh collider approximation is")
                    txt_footer.append("unsupported for rigid bodies. Convex Hull")
                    txt_footer.append("will be used instead.")
                    self._mass_info_text_footer.color = MASS_INFO_TEXT_FONT_COLOR_WARNING
                elif approximation == UsdPhysics.Tokens.meshSimplification:
                    txt_footer.append("WARNING:")
                    txt_footer.append("Mesh Simplification collider approximation")
                    txt_footer.append("is unsupported for rigid bodies. Convex Hull")
                    txt_footer.append("will be used instead.")
                    self._mass_info_text_footer.color = MASS_INFO_TEXT_FONT_COLOR_WARNING

        self._mass_info_text_transform_outer.transform = sc.Matrix44.get_translation_matrix(*info_box_position)

        line_offset = 2
        self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_PRIM_PATH].text="\n" * line_offset + prim_path
        line_offset += 1
        self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_MASS].text="\n" * line_offset + float_to_string(total_mass)
        line_offset += 1
        self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_CENTER_OF_MASS].text="\n" * line_offset + txt_center_of_mass
        line_offset += 1
        self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_PRINCIPAL_AXIS].text="\n" * line_offset + txt_principal_axis
        line_offset += 1
        self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_DIAGONAL_INERTIA].text="\n" * line_offset + txt_diagonal_inertia
        line_offset += 3

        if len(txt_footer) > 0:
            self._mass_info_text_transform_footer.visible = True
            self._mass_info_text_footer.text = "\n" * line_offset
            line_offset+=1
            for line in range(len(txt_footer)):
                self._mass_info_text_footer.text += "\n" + txt_footer[line]
                line_offset+=1
        else:
            self._mass_info_text_transform_footer.visible = False

        width = MASS_INFO_TEXT_BOX_WIDTH
        height = (UI_SCENE_SCREEN_SCALE_MODIFIER * 
                      MASS_INFO_TEXT_FONT_LINE_SPAN * line_offset + 
                    + MASS_INFO_TEXT_MARGIN[1] * 2) # Translates are not scaled
        self._mass_info_background_transform.transform=sc.Matrix44.get_translation_matrix(width * 0.5, -height * 0.5, 0.0)*sc.Matrix44.get_scale_matrix(width, height, 0.0)
        self._mass_info_text_transform_header.transform=sc.Matrix44.get_translation_matrix(width * 0.5, -MASS_INFO_TEXT_MARGIN[1], 0.0)
        self._mass_info_text_transform_titles.transform=sc.Matrix44.get_translation_matrix(MASS_INFO_TEXT_MARGIN[0], -MASS_INFO_TEXT_MARGIN[1], 0.0)
        self._mass_info_text_transform_values.transform=sc.Matrix44.get_translation_matrix(width - MASS_INFO_TEXT_MARGIN[0], -MASS_INFO_TEXT_MARGIN[1], 0.0)
        self._mass_info_text_transform_footer.transform=sc.Matrix44.get_translation_matrix(MASS_INFO_TEXT_MARGIN[0], -MASS_INFO_TEXT_MARGIN[1], 0.0)

    def _make_shapes(self):
        # Draw mass info box.
        titles = ["Prim:", "Total mass:", "Center of mass:", "Principal axis:", "Diagonal inertia:"]

        self._mass_info_text_transform_outer = sc.Transform(transform=sc.Matrix44.get_translation_matrix(0, 0, 0))
        self._mass_info_text_transform_outer.visible = False
        with self._mass_info_text_transform_outer:
            with sc.Transform(look_at=sc.Transform.LookAt.CAMERA):
                self._mass_info_text_transform_inner_offset_world = sc.Transform()
                with self._mass_info_text_transform_inner_offset_world:
                    self._mass_info_text_transform_inner_offset_screen = sc.Transform(scale_to=sc.Space.SCREEN)
                    with self._mass_info_text_transform_inner_offset_screen:
                        self._mass_info_text_transform_header = sc.Transform()
                        with self._mass_info_text_transform_header:
                            self._mass_info_text_header = sc.Label(
                            "MASS PROPERTIES INFO",
                                alignment=ui.Alignment.CENTER_TOP,
                                color=MASS_INFO_TEXT_FONT_COLOR,
                                size=MASS_INFO_TEXT_FONT_SIZE
                                )
                        self._mass_info_text_transform_titles = sc.Transform()
                        with self._mass_info_text_transform_titles:
                            for entry in range(MASS_INFO_TEXT_ENTRY_NUM):
                                self._mass_info_text_title[entry] = sc.Label(
                                "\n" * (entry + 2) + titles[entry],
                                    alignment=ui.Alignment.LEFT,
                                    color=MASS_INFO_TEXT_FONT_COLOR,
                                    size=MASS_INFO_TEXT_FONT_SIZE
                                    )
                        self._mass_info_text_transform_values = sc.Transform()
                        with self._mass_info_text_transform_values:
                            for entry in range(MASS_INFO_TEXT_ENTRY_NUM):
                                self._mass_info_text_value[entry] = sc.Label(
                                " ",
                                    alignment=ui.Alignment.RIGHT,
                                    color=MASS_INFO_TEXT_FONT_COLOR,
                                    size=MASS_INFO_TEXT_FONT_SIZE
                                    )
                        self._mass_info_text_transform_footer = sc.Transform(visible=False)
                        with self._mass_info_text_transform_footer:
                            self._mass_info_text_footer = sc.Label("",
                                alignment=ui.Alignment.LEFT,
                                color=MASS_INFO_TEXT_FONT_COLOR,
                                size=MASS_INFO_TEXT_FONT_SIZE
                                )
                        self._mass_info_background_transform =  sc.Transform()
                        with self._mass_info_background_transform:
                            self._mass_info_background = sc.Rectangle(1, 1, color=MASS_INFO_TEXT_BOX_BACKGROUND_COLOR)        

    def on_build(self):
        super().on_build()

        if self._viewport_overlay is None:
            return

        self._make_shapes()
        self.refresh()

    def set_target(self, manipulators):
        self._mass_manipulators = manipulators
        self.refresh()

    def get_target(self):
        return self._mass_manipulators

    def destroy(self):
        self._mass_manipulators = None
        self._viewport_overlay = None
        self.invalidate()

    def __del__(self):
        self.destroy()

class PhysicsMassEditInfoBoxManipulator(PhysicsMassInfoBoxManipulator):
    def __init__(self, viewport_overlay):
        super().__init__(viewport_overlay)
        self._toggle_groups = []
        self._accumulated_center_of_mass_transform = None

    def add_to_toggles(self, item, group = 0):
        if group < 0 or not isinstance(group, int):
            carb.log_error(f"Fatal error - invalid visual toggle group: {group}")
        while len(self._toggle_groups) <= group:
            self._toggle_groups.append([])
        self._toggle_groups[group].append(item)

    def refresh(self):
        super().refresh()

        if self._mass_info_text_transform_outer is None:
            self.invalidate()
            return
        if not self._mass_info_text_transform_outer.visible:
            self._accumulated_center_of_mass_transform.visible = False
            return

        if len(self._mass_manipulators) > 1:
            self._accumulated_center_of_mass_transform.visible = True
            self._accumulated_center_of_mass_transform.transform = sc.Matrix44.get_translation_matrix(*self._accumulated_center_of_mass)
        else:
            self._accumulated_center_of_mass_transform.visible = False

        active_hover = get_active_hover()
        active_gesture = get_active_gesture()
        enable = False
        toggle_group = -1
        if active_gesture is not None:
            if active_gesture._manipulator in self._mass_manipulators:# self._mass_manipulators.count(active_gesture._manipulator) > 0:
                toggle_group = active_gesture._toggle_group
                enable = True
        elif active_hover is not None and active_hover._manipulator in self._mass_manipulators: # self._mass_manipulators.count(active_hover._manipulator) > 0:
            toggle_group = active_hover._toggle_group
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

    def _make_shapes(self):
        super()._make_shapes()
        
        self._accumulated_center_of_mass_transform = sc.Transform(visible = False)

        # Highlights text entries when gestures are active.
        for axis in range(AXIS_NUM):
            self.add_to_toggles(ColorToggle(self._mass_info_text_title[MASS_INFO_TEXT_ENTRY_CENTER_OF_MASS], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_TRANSLATE, axis))
            self.add_to_toggles(ColorToggle(self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_CENTER_OF_MASS], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_TRANSLATE, axis))
            self.add_to_toggles(ColorToggle(self._mass_info_text_title[MASS_INFO_TEXT_ENTRY_PRINCIPAL_AXIS], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_ROTATE, axis))
            self.add_to_toggles(ColorToggle(self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_PRINCIPAL_AXIS], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_axis(GESTURE_ROTATE, axis))

        for direction in range(AXIS_DIRECTION_NUM):
            self.add_to_toggles(ColorToggle(self._mass_info_text_title[MASS_INFO_TEXT_ENTRY_DIAGONAL_INERTIA], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction))
            self.add_to_toggles(ColorToggle(self._mass_info_text_value[MASS_INFO_TEXT_ENTRY_DIAGONAL_INERTIA], MASS_INFO_TEXT_FONT_COLOR_HIGHLIGHT, MASS_INFO_TEXT_FONT_COLOR), PhysicsMassDistributionEditManipulator.get_toggle_group_by_gesture_direction(GESTURE_SCALE, direction))

        with self._accumulated_center_of_mass_transform:
            with sc.Transform(look_at=sc.Transform.LookAt.CAMERA, scale_to=sc.Space.SCREEN):
                size = 100.0
                subdivisions = 4
                steps = 4
                arc_length = 0.75
                for step in range(steps):
                    for n in range(subdivisions):
                        length = (2 + step) / (steps + 1)
                        angle = math.radians((float(n) + step / 2 - arc_length * 0.5 + 0.5) * 360.0 / subdivisions)
                        angle_end = angle + arc_length * math.radians(360.0 / subdivisions)
                        sc.Arc(size * length, sector=0, begin=angle, end=angle_end, tesselation=(4 + step), color=MASS_DISTRIBUTION_BOX_COLOR, wireframe=True, thickness=MAIN_LINE_THICKNESS)

                sc.Line([-size / (steps + 1), 0.0, 0.0], [size / (steps + 1), 0.0, 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MAIN_LINE_THICKNESS)
                sc.Line([0.0, -size / (steps + 1), 0.0], [0.0, size / (steps + 1), 0.0], color=MASS_DISTRIBUTION_BOX_COLOR, thickness=MAIN_LINE_THICKNESS)


SETTING_DISPLAY_MASS_PROPERTIES_NONE = 0
SETTING_DISPLAY_MASS_PROPERTIES_SELECTED = 1
SETTING_DISPLAY_MASS_PROPERTIES_ALL = 2

MASS_PROPERTIES_VIEW_MAX_NUM = 1000
MASS_DISTRIBUTION_EDIT_MAX_NUM = 100


# import cProfile as profile
# import pstats
# import re
class PhysicsMassViewportOverlay(PhysicsViewportOverlay):
    def __init__(self, main_viewport_overlay):
        super().__init__(main_viewport_overlay)
        self._info_boxes = []

        self._mass_properties_view_manipulators = []
        self._mass_properties_view_manipulators_setting = None

        self._mass_distribution_edit_manipulators = []
        self._mass_distribution_edit_manipulators_setting = None

        self._usd_object_changed_listener = None
        self._usd_context = None
        self._settings = None
        self._selection = None
        self._stage_event_sub = None

        self._usd_context = omni.usd.get_context()
        self._settings = carb.settings.get_settings()
        self._mass_properties_view_manipulators_setting = self._settings.subscribe_to_node_change_events(
            SETTING_DISPLAY_MASS_PROPERTIES, self._on_mass_distribution_view_setting_changed
        )
        self._mass_distribution_edit_manipulators_setting = self._settings.subscribe_to_node_change_events(
            SETTING_MASS_DISTRIBUTION_MANIPULATOR, self._on_mass_distribution_edit_setting_changed
        )
        if self._usd_context is not None:
            self._selection = self._usd_context.get_selection()
            self._stage_event_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)

        self._gesture_manager = PhysicsGestureManager(self)
        self._create_info_boxes()
        self._update_mass_properties_view_manipulators()
        self._update_mass_distribution_edit_manipulators()
        self._manage_usd_change_listener()

    def set_selection(self, prim_paths, update_stage_window = True):
        if self._selection:
            if not isinstance(prim_paths, list):
                prim_paths = [prim_paths]
            self._selection.set_selected_prim_paths(prim_paths, update_stage_window)

    def toggle_in_selection(self, prim_paths):
        if self._selection:
            selected_prim_paths = self._selection.get_selected_prim_paths()
            selected_prim_paths_new = selected_prim_paths.copy()
            added = False
            changed = False
            if not isinstance(prim_paths, list):
                prim_paths = [prim_paths]
            for prim_path in prim_paths:
                changed = True
                if not prim_path in selected_prim_paths:
                    selected_prim_paths_new.append(prim_path)
                    added = True
                else:
                    selected_prim_paths_new.remove(prim_path)

            if changed:
                self.set_selection(selected_prim_paths_new, added)

    def add_to_selection(self, prim_paths):
        if self._selection:
            selected_prim_paths = self._selection.get_selected_prim_paths()
            changed = False
            if not isinstance(prim_paths, list):
                prim_paths = [prim_paths]
            for prim_path in prim_paths:
                if not prim_path in selected_prim_paths:
                    selected_prim_paths.append(prim_path)
                    changed = True
            if changed:
                self.set_selection(selected_prim_paths)

    def remove_from_selection(self, prim_paths):
        if self._selection:
            selected_prim_paths = self._selection.get_selected_prim_paths()
            changed = False
            if not isinstance(prim_paths, list):
                prim_paths = [prim_paths]
            for prim_path in prim_paths:
                if prim_path in selected_prim_paths:
                    selected_prim_paths.remove(prim_path)
                    changed = True
            if changed:
                self.set_selection(selected_prim_paths, False)

    def _create_info_boxes(self):
        for n in range(INFO_BOX_NUM):
            with self._main_viewport_overlay.get_overlay_scene_view().scene:
                if n == INFO_BOX_MASS_VIEW:
                    info_box = PhysicsMassInfoBoxManipulator(self)
                elif n == INFO_BOX_MASS_EDIT:
                    info_box = PhysicsMassEditInfoBoxManipulator(self)
            self._info_boxes.append(info_box)

    def _destroy_info_boxes(self):
        for info_box in self._info_boxes:
            info_box.destroy()
        self._info_boxes.clear()

    def set_info_box_target(self, index, target):
        if index < len(self._info_boxes):
            self._info_boxes[index].set_target(target)

    def get_info_box_target(self, index):
        if index < len(self._info_boxes):
            return self._info_boxes[index].get_target()
        else:
            return None

    def refresh_info_box(self, index):
        if index < len(self._info_boxes):
            self._info_boxes[index].refresh()
        
    def _clear_mass_properties_view_manipulators(self):
        for manipulator in self._mass_properties_view_manipulators:
            manipulator.destroy()
        self._mass_properties_view_manipulators.clear()
        self.set_info_box_target(INFO_BOX_MASS_VIEW, None)

    def _clear_mass_distribution_edit_manipulators(self):
        for manipulator in self._mass_distribution_edit_manipulators:
            manipulator.destroy()
        self._mass_distribution_edit_manipulators.clear()
        self.set_info_box_target(INFO_BOX_MASS_EDIT, None)

    def _revoke_usd_change_listener(self):
        if self._usd_object_changed_listener is not None:
            self._usd_object_changed_listener.Revoke()
            self._usd_object_changed_listener = None

    def _manage_usd_change_listener(self):
        if(self._usd_context and self._usd_context.get_stage() and
            (self._settings.get_as_bool(SETTING_MASS_DISTRIBUTION_MANIPULATOR) or 
            self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) != SETTING_DISPLAY_MASS_PROPERTIES_NONE)):
            if self._usd_object_changed_listener is None:
                self._usd_object_changed_listener = Tf.Notice.Register(
                        Usd.Notice.ObjectsChanged, self._on_usd_objects_changed, 
                        self._usd_context.get_stage())
        else:
            self._revoke_usd_change_listener()

    # NB: Using Usd.Notice is not ideal for performance so we should consider changing the following to something
    # that does not rely on it.
    def _on_usd_objects_changed(self, notice, stage):
        # Check if we're the one writing.
        for manipulator in self._mass_distribution_edit_manipulators:
            if manipulator._writing_to_usd:
                return

        # prof = profile.Profile()
        # prof.enable()

        # Use set for quicker lookup.
        changed_paths = set()
        changed_paths_without_api = set()
        # In case that prims have been added API. Note that this is the exception, so most of the related code below
        # is only run rarely.
        edit_prims_to_add = []
        for changed_path in (notice.GetChangedInfoOnlyPaths() + notice.GetResyncedPaths()):
            if 'apiSchemas' in notice.GetChangedFields(changed_path):
                # This may indicated than the RigidBody API have just been added or removed. 
                # We need to make sure to update these.
                # Note that in this case, the changed path is the prim path.
                if stage.GetPrimAtPath(changed_path).HasAPI(UsdPhysics.RigidBodyAPI):
                    # Always add to the list of prims to add. We will filter out as relevant below.
                    edit_prims_to_add.append(changed_path)
                    changed_paths.add(changed_path)
                else:
                    changed_paths_without_api.add(changed_path)
            else:
                changed_paths.add(changed_path.GetPrimPath())

        view_prims_to_add = edit_prims_to_add.copy()

        if self._settings.get_as_bool(SETTING_MASS_DISTRIBUTION_MANIPULATOR):
            manipulators_to_remove = []
            refresh_info_box = False
            for manipulator in self._mass_distribution_edit_manipulators:
                if manipulator._prim:
                    prim_path = manipulator._prim.GetPrimPath()
                    if prim_path in changed_paths_without_api:
                        refresh_info_box = True
                        manipulators_to_remove.append(manipulator)
                    elif prim_path in changed_paths:
                        refresh_info_box = True
                        manipulator.populate()
                        if prim_path in edit_prims_to_add:
                            # A manipulator for this prim already exists so we don't need to add it.
                            edit_prims_to_add.remove(prim_path)

            for manipulator in manipulators_to_remove:
                self._mass_distribution_edit_manipulators.remove(manipulator)
                manipulator.destroy()
                del manipulator

            if len(edit_prims_to_add) > 0:
                with self._main_viewport_overlay.get_overlay_scene_view().scene:
                    # Prim must also be part of the selection.
                    selection = self._selection.get_selected_prim_paths()
                    for prim in edit_prims_to_add:
                        if not prim in selection:
                            continue
                        if len(self._mass_distribution_edit_manipulators) >= MASS_DISTRIBUTION_EDIT_MAX_NUM:
                            break
                        manipulator = PhysicsMassDistributionEditManipulator(self, stage.GetPrimAtPath(prim))
                        self._mass_distribution_edit_manipulators.append(manipulator)
                        refresh_info_box = True

            if refresh_info_box:
                self.refresh_info_box(INFO_BOX_MASS_EDIT)

        if self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) != SETTING_DISPLAY_MASS_PROPERTIES_NONE:
            # Repeat the above process for views as relevant.
            manipulators_to_remove = []
            refresh_info_box = False
            info_box_target = self.get_info_box_target(INFO_BOX_MASS_VIEW)
            for manipulator in self._mass_properties_view_manipulators:
                if manipulator._prim:
                    prim_path = manipulator._prim.GetPrimPath()
                    if prim_path in changed_paths_without_api:
                        manipulators_to_remove.append(manipulator)
                        if manipulator == info_box_target:
                            refresh_info_box = True
                    elif prim_path in changed_paths:
                        manipulator.populate()
                        if manipulator == info_box_target:
                            refresh_info_box = True
                        if prim_path in view_prims_to_add:
                            view_prims_to_add.remove(prim_path)

            for manipulator in manipulators_to_remove:
                self._mass_properties_view_manipulators.remove(manipulator)
                manipulator.destroy()
                del manipulator

            if len(view_prims_to_add) > 0:
                selection = None
                if self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) == SETTING_DISPLAY_MASS_PROPERTIES_SELECTED:
                    selection = self._selection.get_selected_prim_paths()
                with self._main_viewport_overlay.get_overlay_scene_view().scene:
                    for prim in view_prims_to_add:
                        if selection:
                            # Prim must also be part of the selection.
                            if not prim in selection:
                                continue
                        if len(self._mass_properties_view_manipulators) >= MASS_PROPERTIES_VIEW_MAX_NUM:
                            break
                        manipulator = PhysicsMassPropertiesViewManipulator(self, stage.GetPrimAtPath(prim))
                        self._mass_properties_view_manipulators.append(manipulator)
                        refresh_info_box = True

            if refresh_info_box:
                self.refresh_info_box(INFO_BOX_MASS_VIEW)

        # prof.disable()
        # stats = pstats.Stats(prof).strip_dirs().sort_stats("cumtime")
        # stats.print_stats(20)

    def _on_mass_distribution_view_setting_changed(self, item, event_type):
        self._update_mass_properties_view_manipulators()
        self._manage_usd_change_listener()

    def _on_mass_distribution_edit_setting_changed(self, item, event_type):
        self._update_mass_distribution_edit_manipulators()
        self._manage_usd_change_listener()

    def _update_mass_properties_view_manipulators(self):
        if (self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) == SETTING_DISPLAY_MASS_PROPERTIES_NONE or
            not self._usd_context):
            self._clear_mass_properties_view_manipulators()
            return
        stage = self._usd_context.get_stage()
        if not stage:
            self._clear_mass_properties_view_manipulators()
            return

        prims_to_add = []
        if self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) == SETTING_DISPLAY_MASS_PROPERTIES_SELECTED:
            manipulators_to_remove = self._mass_properties_view_manipulators.copy()

            if self._selection:
                selected_prim_paths = self._selection.get_selected_prim_paths()
                for selected_prim_path in selected_prim_paths:
                    prim = stage.GetPrimAtPath(selected_prim_path)
                    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                        exists = False
                        for manipulator in self._mass_properties_view_manipulators:
                            if manipulator._prim == prim:
                                manipulators_to_remove.remove(manipulator)
                                manipulator.populate()
                                exists = True
                                break
                        if not exists:
                            prims_to_add.append(prim)
                
            for manipulator in manipulators_to_remove:
                self._mass_properties_view_manipulators.remove(manipulator)
                manipulator.destroy()
                del manipulator
        else:
            self._clear_mass_properties_view_manipulators()
            prims_to_add = []
            for prim in stage.Traverse():
                if (prim.HasAPI(UsdPhysics.RigidBodyAPI)):
                    prims_to_add.append(prim)

        if len(prims_to_add) > 0:
            if (len(self._mass_properties_view_manipulators) + len( prims_to_add)
                    > MASS_PROPERTIES_VIEW_MAX_NUM):
                carb.log_warn(f"Exceeding maximum prims for mass view - " + 
                    f"{(len(self._mass_properties_view_manipulators) + len( prims_to_add))}" + 
                    f" vs {MASS_PROPERTIES_VIEW_MAX_NUM}")
                prims_to_add = prims_to_add[0:max(0, (MASS_PROPERTIES_VIEW_MAX_NUM-len(self._mass_properties_view_manipulators)))]
            with self._main_viewport_overlay.get_overlay_scene_view().scene:
                for prim in prims_to_add:
                    manipulator = PhysicsMassPropertiesViewManipulator(self, prim)
                    self._mass_properties_view_manipulators.append(manipulator)

        self.refresh_info_box(INFO_BOX_MASS_VIEW)

    def _update_mass_distribution_edit_manipulators(self):
        if (not self._settings.get_as_bool(SETTING_MASS_DISTRIBUTION_MANIPULATOR) or
            not self._usd_context):
            self._clear_mass_distribution_edit_manipulators()
            return
        stage = self._usd_context.get_stage()
        if not stage:
            self._clear_mass_distribution_edit_manipulators()
            return

        manipulators_to_remove = self._mass_distribution_edit_manipulators.copy()

        prims_to_add = []
        if self._selection:
            selected_prim_paths = self._selection.get_selected_prim_paths()
            for selected_prim_path in selected_prim_paths:
                prim = stage.GetPrimAtPath(selected_prim_path)
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    exists = False
                    for manipulator in self._mass_distribution_edit_manipulators:
                        if manipulator._prim == prim:
                            manipulators_to_remove.remove(manipulator)
                            manipulator.populate()
                            exists = True
                            break
                    if not exists:
                        prims_to_add.append(prim)

        for manipulator in manipulators_to_remove:
            self._mass_distribution_edit_manipulators.remove(manipulator)
            manipulator.destroy()
            del manipulator

        if len(prims_to_add) > 0:
            if (len(self._mass_distribution_edit_manipulators) + len( prims_to_add)
                    > MASS_DISTRIBUTION_EDIT_MAX_NUM):
                carb.log_warn(f"Exceeding maximum prims for mass distribution edit - " + 
                    f"{(len(self._mass_distribution_edit_manipulators) + len(prims_to_add))}" + 
                    f" vs {MASS_DISTRIBUTION_EDIT_MAX_NUM}")
                prims_to_add = prims_to_add[0:max(0, (MASS_DISTRIBUTION_EDIT_MAX_NUM-len(self._mass_distribution_edit_manipulators)))]
            with self._main_viewport_overlay.get_overlay_scene_view().scene:
                for prim in prims_to_add:
                    manipulator = PhysicsMassDistributionEditManipulator(self, prim)
                    self._mass_distribution_edit_manipulators.append(manipulator)

        for manipulator in self._mass_distribution_edit_manipulators:
            manipulator.set_edit_enabled(False if len(self._mass_distribution_edit_manipulators) > 1 else True)
        self.set_info_box_target(INFO_BOX_MASS_EDIT, self._mass_distribution_edit_manipulators)

    def _on_stage_event(self, event):
        if self._settings.get_as_bool(SETTING_MASS_DISTRIBUTION_MANIPULATOR):
            if event.type is int(omni.usd.StageEventType.SELECTION_CHANGED):
                self._update_mass_distribution_edit_manipulators()
            elif event.type is int(omni.usd.StageEventType.OPENED):
                self._manage_usd_change_listener()
            elif event.type is int(omni.usd.StageEventType.CLOSING):
                self._clear_mass_distribution_edit_manipulators()
                self._revoke_usd_change_listener()

        if self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) != SETTING_DISPLAY_MASS_PROPERTIES_NONE:
            if (event.type is int(omni.usd.StageEventType.SELECTION_CHANGED) 
                and self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) == SETTING_DISPLAY_MASS_PROPERTIES_SELECTED):
                self._update_mass_properties_view_manipulators()
            elif event.type is int(omni.usd.StageEventType.OPENED):
                self._manage_usd_change_listener()
                if self._settings.get_as_int(SETTING_DISPLAY_MASS_PROPERTIES) == SETTING_DISPLAY_MASS_PROPERTIES_ALL:
                    self._update_mass_properties_view_manipulators()
            elif event.type is int(omni.usd.StageEventType.CLOSING):
                self._clear_mass_properties_view_manipulators()
                self._revoke_usd_change_listener()

    def destroy(self):
        self._clear_mass_properties_view_manipulators()
        self._clear_mass_distribution_edit_manipulators()
        self._destroy_info_boxes()
        self._revoke_usd_change_listener()

        super().destroy()