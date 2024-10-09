import math
import typing

import carb
import omni.usd
from omni.physx.bindings._physx import SimulationEvent
from pxr import Gf, PhysicsSchemaTools, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

HALF_PI = 1.57079632679489662
MAX_FLOAT = 3.40282347e38


def compute_bounding_box_diagonal(points):
    v_min_x = MAX_FLOAT
    v_min_y = MAX_FLOAT
    v_min_z = MAX_FLOAT
    v_max_x = -MAX_FLOAT
    v_max_y = -MAX_FLOAT
    v_max_z = -MAX_FLOAT
    for v in points:
        if v.x < v_min_x:
            v_min_x = v.x
        if v.x > v_max_x:
            v_max_x = v.x
        if v.y < v_min_y:
            v_min_y = v.y
        if v.y > v_max_y:
            v_max_y = v.y
        if v.z < v_min_z:
            v_min_z = v.z
        if v.z > v_max_z:
            v_max_z = v.z
    return math.sqrt((v_max_x - v_min_x) ** 2 + (v_max_y - v_min_y) ** 2 + (v_max_z - v_min_z) ** 2)


def create_mesh(stage, path, points, normals, indices, vertexCounts):
    mesh = UsdGeom.Mesh.Define(stage, path)

    # Fill in VtArrays
    mesh.CreateFaceVertexCountsAttr().Set(vertexCounts)
    mesh.CreateFaceVertexIndicesAttr().Set(indices)
    mesh.CreatePointsAttr().Set(points)
    mesh.CreateDoubleSidedAttr().Set(False)
    mesh.CreateNormalsAttr().Set(normals)

    return mesh


def create_mesh_square_axis(stage, path, axis, halfSize):
    if axis == "X":
        points = [
            Gf.Vec3f(0.0, -halfSize, -halfSize),
            Gf.Vec3f(0.0, halfSize, -halfSize),
            Gf.Vec3f(0.0, halfSize, halfSize),
            Gf.Vec3f(0.0, -halfSize, halfSize),
        ]
        normals = [Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0)]
        indices = [0, 1, 2, 3]
        vertexCounts = [4]

        # Create the mesh
        return create_mesh(stage, path, points, normals, indices, vertexCounts)
    elif axis == "Y":
        points = [
            Gf.Vec3f(-halfSize, 0.0, -halfSize),
            Gf.Vec3f(halfSize, 0.0, -halfSize),
            Gf.Vec3f(halfSize, 0.0, halfSize),
            Gf.Vec3f(-halfSize, 0.0, halfSize),
        ]
        normals = [Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0)]
        indices = [3, 2, 1, 0]
        vertexCounts = [4]

        # Create the mesh
        return create_mesh(stage, path, points, normals, indices, vertexCounts)

    points = [
        Gf.Vec3f(-halfSize, -halfSize, 0.0),
        Gf.Vec3f(halfSize, -halfSize, 0.0),
        Gf.Vec3f(halfSize, halfSize, 0.0),
        Gf.Vec3f(-halfSize, halfSize, 0.0),
    ]
    normals = [Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1)]
    indices = [0, 1, 2, 3]
    vertexCounts = [4]

    # Create the mesh
    mesh = create_mesh(stage, path, points, normals, indices, vertexCounts)

    # text coord
    texCoords = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    texCoords.Set([(0, 0), (1, 0), (1, 1), (0, 1)])

    return mesh

def create_mesh_concave(stage, path, halfSize):
    points = [
        Gf.Vec3f(halfSize, -halfSize, -halfSize),
        Gf.Vec3f(halfSize, halfSize, -halfSize),
        Gf.Vec3f(halfSize, halfSize, halfSize),
        Gf.Vec3f(halfSize, -halfSize, halfSize),
        Gf.Vec3f(0.0, -halfSize, halfSize * 0.2),
        Gf.Vec3f(0.0, halfSize, halfSize * 0.2),
        Gf.Vec3f(-halfSize, -halfSize, -halfSize),
        Gf.Vec3f(-halfSize, halfSize, -halfSize),
        Gf.Vec3f(-halfSize, halfSize, halfSize),
        Gf.Vec3f(-halfSize, -halfSize, halfSize),
    ]
    normals = [Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0),
        Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1),
        Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0)]
    indices = [
        0, 1, 2, 3,
        1, 7, 8, 5, 2,
        3, 2, 5, 4,
        4, 5, 8, 9,
        9, 8, 7, 6,
        0, 6, 7, 1,
        0, 3, 4, 9, 6]
    vertexCounts = [4, 5, 4, 4, 4, 4, 5]

    # Create the mesh
    return create_mesh(stage, path, points, normals, indices, vertexCounts)


def create_mesh_cube(stage, path, halfSize):
    points = [
        Gf.Vec3f(halfSize, -halfSize, -halfSize),
        Gf.Vec3f(halfSize, halfSize, -halfSize),
        Gf.Vec3f(halfSize, halfSize, halfSize),
        Gf.Vec3f(halfSize, -halfSize, halfSize),
        Gf.Vec3f(-halfSize, -halfSize, -halfSize),
        Gf.Vec3f(-halfSize, halfSize, -halfSize),
        Gf.Vec3f(-halfSize, halfSize, halfSize),
        Gf.Vec3f(-halfSize, -halfSize, halfSize),
    ]
    normals = [
        Gf.Vec3f(1, 0, 0),
        Gf.Vec3f(1, 0, 0),
        Gf.Vec3f(1, 0, 0),
        Gf.Vec3f(1, 0, 0),
        Gf.Vec3f(-1, 0, 0),
        Gf.Vec3f(-1, 0, 0),
        Gf.Vec3f(-1, 0, 0),
        Gf.Vec3f(-1, 0, 0),
    ]
    indices = [0, 1, 2, 3, 1, 5, 6, 2, 3, 2, 6, 7, 0, 3, 7, 4, 1, 0, 4, 5, 5, 4, 7, 6]
    vertexCounts = [4, 4, 4, 4, 4, 4]

    # Create the mesh
    return create_mesh(stage, path, points, normals, indices, vertexCounts)

def create_mesh_cylinder(stage, path, height, radius, tesselation = 32):
    points = []
    normals = []
    indices = []
    angle = 0.0

    for i in range(tesselation):
        angle = 2.0 * math.pi * i / tesselation
        angle_cos = math.cos(angle)
        angle_sin = math.sin(angle)
        side_normal = Gf.Vec3f(angle_cos, angle_sin, 0)
        # Top facing upwards.
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                + height / 2
            ))
        normals.append(Gf.Vec3f(0, 0, 1))
        # Top facing sideways.
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                + height / 2
            ))
        normals.append(side_normal)
        # Bottom facing downwards
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                - height / 2
            ))
        normals.append(Gf.Vec3f(0, 0, -1))
        # Bottom facing sideways
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                - height / 2
            ))
        normals.append(side_normal)

        # Top
        indices.append(i * 4) # Edge
        indices.append((tesselation) * 4) # Top center
        # Previous edge
        if i > 0:
            indices.append((i - 1) * 4)
        else:
            indices.append((tesselation - 1) * 4)

        # Upper sideways
        indices.append(i * 4 + 1)
        indices.append(i * 4 + 3) # Edge
        # Previous edge
        if i > 0:
            indices.append((i - 1) * 4 + 1)
        else:
            indices.append((tesselation - 1) * 4 + 1)

        # Bottom
        indices.append((tesselation) * 4 + 1) # Bottom center
        indices.append(i * 4 + 2) # Edge
        # Previous edge
        if i > 0:
            indices.append((i - 1) * 4 + 2)
        else:
            indices.append((tesselation - 1) * 4 + 2)

        # Lower sideways
        indices.append(i * 4 + 3) # Edge
        # Previous edge
        if i > 0:
            indices.append((i - 1) * 4 + 3)
            indices.append((i - 1) * 4 + 1)
        else:
            indices.append((tesselation - 1) * 4 + 3)
            indices.append((tesselation - 1) * 4 + 1)

    # Top center vertex.
    points.append(Gf.Vec3f(0, 0, height / 2))
    normals.append(Gf.Vec3f(0, 0, 1))
    # Bottom center vertex.
    points.append(Gf.Vec3f(0, 0, -height / 2))
    normals.append(Gf.Vec3f(0, 0, -1))

    vertexCounts = [3] * 4 * tesselation

    # Create the mesh
    return create_mesh(stage, path, points, normals, indices, vertexCounts)

def create_mesh_cone(stage, path, height, radius, tesselation = 64):
    points = []
    normals = []
    indices = []

    intersection_offset = 1 / 3
    normal_z = math.sin(math.atan(radius / height))
    normal_xy = math.sqrt(1.0 - normal_z * normal_z)

    for i in range(tesselation):
        angle = 2.0 * math.pi * i / tesselation
        angle_cos = math.cos(angle)
        angle_sin = math.sin(angle)

        # Tip vertex.
        points.append(Gf.Vec3f(0, 0, height / 2))
        normal = Gf.Vec3f(angle_cos * normal_xy, angle_sin * normal_xy, normal_z)
        normals.append(normal)

        # Intersection point vertex
        points.append(
            Gf.Vec3f(
                angle_cos * radius * intersection_offset,
                angle_sin * radius * intersection_offset,
                height / 2 - height * intersection_offset
            ))

        normals.append(normal)

        # Base vertex sideways
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                - height / 2
            ))

        normals.append(normal)

        # Base vertex downwards.
        points.append(
            Gf.Vec3f(
                angle_cos * radius,
                angle_sin * radius,
                - height / 2
            ))

        normal = Gf.Vec3f(0, 0, -1)
        normals.append(normal)

        # Tip section
        indices.append(i * 4 + 1)
        indices.append(i * 4) # Tip vertex
        # Previous vertex
        if i > 0:
            indices.append((i - 1) * 4 + 1)
        else:
            indices.append((tesselation - 1) * 4 + 1)

        # Upper sideways
        indices.append(i * 4 + 2) # Base vertex
        indices.append(i * 4 + 1) # Intersection vertex
        # Previous vertex
        if i > 0:
            indices.append((i - 1) * 4 + 1)
        else:
            indices.append((tesselation - 1) * 4 + 1)

        # Base sideways
        indices.append(i * 4 + 2) # Base vertex
        # Previous vertex
        if i > 0:
            indices.append((i - 1) * 4 + 1)
            indices.append((i - 1) * 4 + 2)
        else:
            indices.append((tesselation - 1) * 4 + 1)
            indices.append((tesselation - 1) * 4 + 2)

        # Base downwards
        indices.append(tesselation * 4) # Base center
        indices.append(i * 4 + 3) # Base vertex
        # Previous
        if i > 0:
            indices.append((i - 1) * 4 + 3)
        else:
            indices.append((tesselation - 1) * 4 + 3)

    # Base center vertex.
    points.append(Gf.Vec3f(0, 0, -height / 2))
    normals.append(Gf.Vec3f(0, 0, -1))

    vertexCounts = [3] * 4 * tesselation

    # Create the mesh
    return create_mesh(stage, path, points, normals, indices, vertexCounts)

def add_density(stage, path, value):
    rbPrim = stage.GetPrimAtPath(Sdf.Path(path))
    densityAPI = UsdPhysics.MassAPI.Apply(rbPrim)
    densityAPI.CreateDensityAttr().Set(value)

def add_mass(stage, path: typing.Union["str", Sdf.Path], mass: float = 1.0):
    rbPrim = stage.GetPrimAtPath(Sdf.Path(path))
    massAPI = UsdPhysics.MassAPI.Apply(rbPrim)
    massAPI.CreateMassAttr().Set(mass)

def add_force_torque(stage,
                     path: typing.Union["str", Sdf.Path],
                     force: Gf.Vec3f = Gf.Vec3f(0.0),
                     torque: Gf.Vec3f = Gf.Vec3f(0.0),
                     mode: str = "acceleration",
                     isEnabled: bool = True,
                     isWorldSpace: bool = False):

    rbPrim = stage.GetPrimAtPath(Sdf.Path(path))
    physx_force_api = PhysxSchema.PhysxForceAPI.Apply(rbPrim)
    physx_force_api.CreateForceAttr().Set(force)
    physx_force_api.CreateTorqueAttr().Set(torque)
    physx_force_api.CreateModeAttr().Set(mode)
    physx_force_api.CreateForceEnabledAttr().Set(isEnabled)
    physx_force_api.CreateWorldFrameEnabledAttr().Set(isWorldSpace)

def add_physics_material_to_prim(stage, prim, materialPath):
    bindingAPI = UsdShade.MaterialBindingAPI.Apply(prim)
    materialPrim = UsdShade.Material(stage.GetPrimAtPath(materialPath))
    bindingAPI.Bind(materialPrim, UsdShade.Tokens.weakerThanDescendants, "physics")


def _get_collision_group_includes(stage, collisionGroupPath):
    collisionGroup = stage.GetPrimAtPath(collisionGroupPath)
    if collisionGroup:
        collisionToken = "colliders"
        collectionAPI = Usd.CollectionAPI.Get(collisionGroup, collisionToken)
        if collectionAPI:
            return collectionAPI.GetIncludesRel()

    return None


def add_collision_to_collision_group(stage, collisionPath, collisionGroupPath):
    includesRel = _get_collision_group_includes(stage, collisionGroupPath)
    if includesRel:
        includesRel.AddTarget(collisionPath)


def remove_collision_from_collision_group(stage, collisionPath, collisionGroupPath):
    includesRel = _get_collision_group_includes(stage, collisionGroupPath)
    if includesRel:
       includesRel.RemoveTarget(collisionPath)


def is_in_collision_group(stage, collisionPath, collisionGroupPath):
    includesRel = _get_collision_group_includes(stage, collisionGroupPath)
    if includesRel:
        targets = includesRel.GetTargets()
        for t in targets:
            if (t == collisionPath):
                return True

    return False


def add_ground_plane(stage, planePath, axis, size, position, color):
    # plane xform, so that we dont nest geom prims
    planePath = omni.usd.get_stage_next_free_path(stage, planePath, True)
    planeXform = UsdGeom.Xform.Define(stage, planePath)
    planeXform.AddTranslateOp().Set(position)
    planeXform.AddOrientOp().Set(Gf.Quatf(1.0))
    planeXform.AddScaleOp().Set(Gf.Vec3f(1.0))

    # (Graphics) Plane mesh
    geomPlanePath = planePath + "/CollisionMesh"
    entityPlane = create_mesh_square_axis(stage, geomPlanePath, axis, size)
    entityPlane.CreateDisplayColorAttr().Set([color])

    # (Collision) Plane
    colPlanePath = planePath + "/CollisionPlane"
    planeGeom = UsdGeom.Plane.Define(stage, colPlanePath)
    planeGeom.CreatePurposeAttr().Set("guide")
    planeGeom.CreateAxisAttr().Set(axis)

    prim = stage.GetPrimAtPath(colPlanePath)
    UsdPhysics.CollisionAPI.Apply(prim)

    return planePath


def add_quad_plane(stage, quadPath, axis, size, position, color):
    # Plane quad mesh
    planePath = omni.usd.get_stage_next_free_path(stage, quadPath, True)
    entityPlane = create_mesh_square_axis(stage, planePath, axis, size)
    entityPlane.CreateDisplayColorAttr().Set([color])
    entityPlane.AddTranslateOp().Set(position)
    entityPlane.AddOrientOp().Set(Gf.Quatf(1.0))
    entityPlane.AddScaleOp().Set(Gf.Vec3f(1.0))

    UsdPhysics.CollisionAPI.Apply(entityPlane.GetPrim())


def add_cube_ground_plane(stage, cubePath, axis, size, position, color):
    cubePath = omni.usd.get_stage_next_free_path(stage, cubePath, True)
    cubeGeom = UsdGeom.Cube.Define(stage, cubePath)
    cubeGeom.AddTranslateOp().Set(position)
    cubeGeom.AddOrientOp().Set(Gf.Quatf(1.0))
    cubeGeom.CreateDisplayColorAttr().Set([color])
    cubeGeom.CreateSizeAttr(size)
    half_extent = size / 2
    cubeGeom.CreateExtentAttr([(-half_extent, -half_extent, -half_extent), (half_extent, half_extent, half_extent)])

    if axis == "X":
        cubeGeom.AddScaleOp().Set(Gf.Vec3f(0.01, 1.0, 1.0))
    elif axis == "Y":
        cubeGeom.AddScaleOp().Set(Gf.Vec3f(1.0, 0.01, 1.0))
    elif axis == "Z":
        cubeGeom.AddScaleOp().Set(Gf.Vec3f(1.0, 1.0, 0.01))
    UsdPhysics.CollisionAPI.Apply(cubeGeom.GetPrim())


def _add_transformation(xform_geom, position, orientation, scale=Gf.Vec3f(1.0)):
    xform_geom.AddTranslateOp().Set(position)
    xform_geom.AddOrientOp().Set(orientation)
    xform_geom.AddScaleOp().Set(scale)


def _add_rigid(xform_prim, density, lin_velocity, ang_velocity):
    UsdPhysics.CollisionAPI.Apply(xform_prim)
    if density != 0.0:
        rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(xform_prim)
        rigid_body_api.CreateVelocityAttr().Set(lin_velocity)
        rigid_body_api.CreateAngularVelocityAttr().Set(ang_velocity)
        mass_api = UsdPhysics.MassAPI.Apply(xform_prim)
        mass_api.CreateDensityAttr(density)


def add_box(stage, path, size=Gf.Vec3f(1.0), position=Gf.Vec3f(0.0), orientation=Gf.Quatf(1.0), color=Gf.Vec3f(1.0)):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    cube_geom = UsdGeom.Cube.Define(stage, path)
    cube_size = 1.0
    half_extent = cube_size / 2
    cube_geom.CreateSizeAttr(cube_size)
    cube_geom.CreateExtentAttr([(-half_extent, -half_extent, -half_extent), (half_extent, half_extent, half_extent)])
    cube_geom.CreateDisplayColorAttr().Set([color])

    # make it possible to define size as float/int
    if not isinstance(size, Gf.Vec3f):
        size = Gf.Vec3f(size)

    _add_transformation(cube_geom, position, orientation, size)
    return stage.GetPrimAtPath(path)


def add_rigid_box(
    stage,
    path,
    size=Gf.Vec3f(1.0),
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    cube_prim = add_box(stage, path, size, position, orientation, color)
    _add_rigid(cube_prim, density, lin_velocity, ang_velocity)
    return cube_prim


def add_cube(stage, path, size=Gf.Vec3f(1.0), position=Gf.Vec3f(0.0), orientation=Gf.Quatf(1.0), color=Gf.Vec3f(1.0)):
    return add_box(stage, path, size, position, orientation, color)


def add_rigid_cube(
    stage,
    path,
    size=Gf.Vec3f(1.0),
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    return add_rigid_box(stage, path, size, position, orientation, color, density, lin_velocity, ang_velocity)


def add_sphere(stage, path, radius=1.0, position=Gf.Vec3f(0.0), orientation=Gf.Quatf(1.0), color=Gf.Vec3f(1.0)):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    sphere_geom = UsdGeom.Sphere.Define(stage, path)
    sphere_geom.CreateRadiusAttr(radius)
    sphere_geom.CreateExtentAttr([(-radius, -radius, -radius), (radius, radius, radius)])
    sphere_geom.CreateDisplayColorAttr().Set([color])
    _add_transformation(sphere_geom, position, orientation)
    return stage.GetPrimAtPath(path)


def add_rigid_sphere(
    stage,
    path,
    radius=1.0,
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    sphere_prim = add_sphere(stage, path, radius, position, orientation, color)
    UsdPhysics.CollisionAPI.Apply(sphere_prim)
    _add_rigid(sphere_prim, density, lin_velocity, ang_velocity)
    return sphere_prim


def add_capsule(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    capsule_geom = UsdGeom.Capsule.Define(stage, path)
    capsule_geom.CreateRadiusAttr(radius)
    capsule_geom.CreateHeightAttr(height)
    capsule_geom.CreateExtentAttr([(-radius, -radius, -height), (radius, radius, height)])
    capsule_geom.CreateAxisAttr(axis)
    capsule_geom.CreateDisplayColorAttr().Set([color])
    _add_transformation(capsule_geom, position, orientation)
    return stage.GetPrimAtPath(path)


def add_rigid_capsule(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    capsule_prim = add_capsule(stage, path, radius, height, axis, position, orientation, color)
    _add_rigid(capsule_prim, density, lin_velocity, ang_velocity)
    return capsule_prim


def add_cylinder(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    cylinder_geom = UsdGeom.Cylinder.Define(stage, path)
    cylinder_geom.CreateRadiusAttr(radius)
    cylinder_geom.CreateHeightAttr(height)
    cylinder_geom.CreateExtentAttr([(-radius, -radius, -height), (radius, radius, height)])
    cylinder_geom.CreateAxisAttr(axis)
    cylinder_geom.CreateDisplayColorAttr().Set([color])
    _add_transformation(cylinder_geom, position, orientation)
    return stage.GetPrimAtPath(path)


def add_rigid_cylinder(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    cylinder_prim = add_cylinder(stage, path, radius, height, axis, position, orientation, color)
    _add_rigid(cylinder_prim, density, lin_velocity, ang_velocity)
    return cylinder_prim


def add_cone(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    cone_geom = UsdGeom.Cone.Define(stage, path)
    cone_geom.CreateRadiusAttr(radius)
    cone_geom.CreateHeightAttr(height)
    cone_geom.CreateExtentAttr([(-radius, -radius, -height), (radius, radius, height)])
    cone_geom.CreateAxisAttr(axis)
    cone_geom.CreateDisplayColorAttr().Set([color])
    _add_transformation(cone_geom, position, orientation)
    return stage.GetPrimAtPath(path)


def add_rigid_cone(
    stage,
    path,
    radius=1.0,
    height=1.0,
    axis="Y",
    position=Gf.Vec3f(0.0),
    orientation=Gf.Quatf(1.0),
    color=Gf.Vec3f(1.0),
    density=1.0,
    lin_velocity=Gf.Vec3f(0.0),
    ang_velocity=Gf.Vec3f(0.0),
):
    cone_prim = add_cone(stage, path, radius, height, axis, position, orientation, color)
    _add_rigid(cone_prim, density, lin_velocity, ang_velocity)
    return cone_prim


def add_xform(stage, path, position=Gf.Vec3f(0.0), orientation=Gf.Quatf(1.0), scale=Gf.Vec3f(1.0)):
    path = omni.usd.get_stage_next_free_path(stage, path, True)
    xform_geom = UsdGeom.Xform.Define(stage, path)
    _add_transformation(xform_geom, position, orientation, scale)
    return stage.GetPrimAtPath(path)


def add_rigid_xform(stage, path, position=Gf.Vec3f(0.0), orientation=Gf.Quatf(1.0), scale=Gf.Vec3f(1.0)):
    xform_prim = add_xform(stage, path, position, orientation, scale)
    physicsAPI = UsdPhysics.RigidBodyAPI.Apply(xform_prim)
    physicsAPI.CreateRigidBodyEnabledAttr(True)
    return xform_prim


def get_translation(prim):
    return prim.GetAttribute("xformOp:translate").Get()


def add_joint_fixed(
    stage, jointPath, actor0, actor1, localPos0, localRot0, localPos1, localRot1, breakForce, breakTorque
):
    # D6 fixed joint
    jointPath = omni.usd.get_stage_next_free_path(stage, jointPath, True)
    d6FixedJoint = UsdPhysics.FixedJoint.Define(stage, jointPath)

    d6FixedJoint.CreateBody0Rel().SetTargets([actor0])
    d6FixedJoint.CreateBody1Rel().SetTargets([actor1])

    d6FixedJoint.CreateLocalPos0Attr().Set(localPos0)
    d6FixedJoint.CreateLocalRot0Attr().Set(localRot0)

    d6FixedJoint.CreateLocalPos1Attr().Set(localPos1)
    d6FixedJoint.CreateLocalRot1Attr().Set(localRot1)

    d6FixedJoint.CreateBreakForceAttr().Set(breakForce)
    d6FixedJoint.CreateBreakTorqueAttr().Set(breakTorque)


def set_or_add_scale_op(
    xformable: UsdGeom.Xformable, scale: typing.Union[Gf.Vec3f, Gf.Vec3d, Gf.Vec3h]
) -> UsdGeom.XformOp:
    """
    Sets or adds the scale XformOp on the input Xformable to provided scale value.

    Note that:
        - The precision of an added attribute is UsdGeom.XformOp.PrecisionFloat.

    Args:
        xformable:  The Xformable to modify.
        scale:      The scale vector
    Returns:
        The set or added XformOp
    """
    prim = xformable.GetPrim()
    if not (prim.IsA(UsdGeom.Xformable)):
        carb.log_warn(f"{__name__}.set_or_add_scale_op: Provided prim is not an Xformable")
        return False
    xformOp = _get_or_create_xform_op(xformable, "xformOp:scale", UsdGeom.XformOp.TypeScale)
    if xformOp.Get() is None:
        xformOp.Set(Gf.Vec3f(scale))
    else:
        typeName = type(xformOp.Get())
        xformOp.Set(typeName(scale))
    return xformOp


def set_or_add_translate_op(
    xformable: UsdGeom.Xformable, translate: typing.Union[Gf.Vec3f, Gf.Vec3d, Gf.Vec3h]
) -> UsdGeom.XformOp:
    """
    Sets or adds the translate XformOp on the input Xformable to provided translate value.

    Note that:
        - The precision of an added attribute is UsdGeom.XformOp.PrecisionFloat.

    Args:
        xformable:  The Xformable to modify.
        translate:      The translate vector
    Returns:
        The set or added XformOp
    """
    prim = xformable.GetPrim()
    if not (prim.IsA(UsdGeom.Xformable)):
        carb.log_warn(f"{__name__}.set_or_add_translate_op: Provided prim is not an Xformable")
        return False
    xformOp = _get_or_create_xform_op(xformable, "xformOp:translate", UsdGeom.XformOp.TypeTranslate)
    if xformOp.Get() is None:
        xformOp.Set(Gf.Vec3f(translate))
    else:
        typeName = type(xformOp.Get())
        xformOp.Set(typeName(translate))
    return xformOp


def set_or_add_orient_op(
    xformable: UsdGeom.Xformable, orient: typing.Union[Gf.Vec3f, Gf.Vec3d, Gf.Vec3h]
) -> UsdGeom.XformOp:
    """
    Sets or adds the orient XformOp on the input Xformable to provided orient value.

    Note that:
        - The precision of an added attribute is UsdGeom.XformOp.PrecisionFloat.

    Args:
        xformable:  The Xformable to modify.
        orient:      The orient quaternion
    Returns:
        The set or added XformOp
    """
    prim = xformable.GetPrim()
    if not (prim.IsA(UsdGeom.Xformable)):
        carb.log_warn(f"{__name__}.set_or_add_orient_op: Provided prim is not an Xformable")
        return None
    xformOp = _get_or_create_xform_op(xformable, "xformOp:orient", UsdGeom.XformOp.TypeOrient)
    if xformOp.Get() is None:
        xformOp.Set(Gf.Quatf(orient))
    else:
        typeName = type(xformOp.Get())
        xformOp.Set(typeName(orient))
    return xformOp


def set_or_add_scale_orient_translate(
    xformable: UsdGeom.Xformable,
    scale: typing.Union[Gf.Vec3f, Gf.Vec3d, Gf.Vec3h],
    orient: typing.Union[Gf.Quatf, Gf.Quatd, Gf.Quath],
    translate: typing.Union[Gf.Vec3f, Gf.Vec3d, Gf.Vec3h],
) -> typing.List[UsdGeom.XformOp]:
    """
    Sets or adds scale, orient, and translate XformOps of xformable.

    Note that:
        - The precision of created attributes is UsdGeom.XformOp.PrecisionFloat.

    Args:
        xformable:  The Xformable to modify.
        scale:      The scale vector
        orient:     The orientation quaternion
        translate:  The translation vector
    Returns:
        List of set and created xform ops that will be [translate, orient, scale]
    """
    prim = xformable.GetPrim()
    if not (prim.IsA(UsdGeom.Xformable)):
        carb.log_warn(f"{__name__}.set_or_add_scale_orient_translate: Provided prim is not an Xformable")
        return False
    tosOps = []
    tosOps.append(set_or_add_translate_op(xformable, translate))
    tosOps.append(set_or_add_orient_op(xformable, orient))
    tosOps.append(set_or_add_scale_op(xformable, scale))
    return tosOps


def setup_transform_as_scale_orient_translate(xformable: UsdGeom.Xformable):
    """
    Changes the local transform (ops) to the physics default scale->orient->translate stack.

    Note that:
        - Any skew in the transform will be lost.
        - A resetXformStack is preserved, but not the XformOps that are ignored due to the reset.
        - The transform attribute precision is set to UsdGeom.XformOp.PrecisionFloat.
        - Obsolete xformOp: namespace attributes are not removed (and cannot be for layers)

    Args:
        xformable: The Xformable to modify.
    """
    prim = xformable.GetPrim()
    if not (prim.IsA(UsdGeom.Xformable)):
        carb.log_warn(f"{__name__}.setup_transform_as_scale_orient_translate: Provided prim is not an Xformable")
        return
    # make sure we are working with an Xformable (e.g. if just a prim was passed in)
    xformable = UsdGeom.Xformable(xformable)
    hasReset = xformable.GetResetXformStack()
    with Sdf.ChangeBlock():  # batch the transform changes:
        tf = Gf.Transform(xformable.GetLocalTransformation())
        scale = Gf.Vec3d(tf.GetScale())
        translation = Gf.Vec3d(tf.GetTranslation())
        quat = Gf.Quatd(tf.GetRotation().GetQuat())
        newOps = set_or_add_scale_orient_translate(xformable, scale, quat, translation)
        xformable.SetXformOpOrder(newOps, hasReset)


def copy_transform_as_scale_orient_translate(src: UsdGeom.Xformable, dst: UsdGeom.Xformable):
    """
    Copies the local transforms from one Xformable to another as a default scale->orient->translate stack.

    Note that:
        - Any skew in the src transform will be lost.
        - A resetXformStack is preserved, but not the XformOps that are ignored due to the reset.
        - The transform attribute precision of added XformOps is set to UsdGeom.XformOp.PrecisionFloat.
        - Obsolete xformOp: namespace attributes in dst are not removed (and cannot be for layers)

    Args:
        src: The source Xformable.
        dst: The destination Xformable.
    """
    srcPrim = src.GetPrim()
    dstPrim = dst.GetPrim()
    if not (srcPrim.IsA(UsdGeom.Xformable) and dstPrim.IsA(UsdGeom.Xformable)):
        carb.log_warn(
            f"{__name__}.copy_transform_as_scale_orient_translate: Either the src or dst Xformable parameter is not an Xformable"
        )
        return
    srcXformable = UsdGeom.Xformable(src)
    dstXformable = UsdGeom.Xformable(dst)
    hasReset = srcXformable.GetResetXformStack()
    with Sdf.ChangeBlock():  # batch the transform changes:
        tf = Gf.Transform(srcXformable.GetLocalTransformation())
        scale = Gf.Vec3d(tf.GetScale())
        translation = Gf.Vec3d(tf.GetTranslation())
        quat = Gf.Quatd(tf.GetRotation().GetQuat())
        newOps = set_or_add_scale_orient_translate(dstXformable, scale, quat, translation)
        dstXformable.SetXformOpOrder(newOps, hasReset)


def resolveContactEventPaths(event):
    contactDict = {}
    if event.type != int(SimulationEvent.CONTACT_DATA):
        contactDict["actor0"] = PhysicsSchemaTools.decodeSdfPath(event.payload["actor0"][0], event.payload["actor0"][1])
        contactDict["actor1"] = PhysicsSchemaTools.decodeSdfPath(event.payload["actor1"][0], event.payload["actor1"][1])
        contactDict["collider0"] = PhysicsSchemaTools.decodeSdfPath(
            event.payload["collider0"][0], event.payload["collider0"][1]
        )
        contactDict["collider1"] = PhysicsSchemaTools.decodeSdfPath(
            event.payload["collider1"][0], event.payload["collider1"][1]
        )

    return contactDict


def _get_or_create_xform_op(
    xformable: UsdGeom.Xformable, opName: str, opType: str, opPrecisionIfCreate=UsdGeom.XformOp.PrecisionFloat
) -> UsdGeom.XformOp:
    """
    Gets or creates an XformOp of an Xformable.

    Note that:
        - Any skew in the transform will be lost.
        - A resetXformStack is preserved, but not the XformOps that are ignored due to the reset.
        - The transform attribute precision is set to UsdGeom.XformOp.PrecisionFloat.

    Args:
        xformable:  The Xformable to modify.
        opName:     The XformOp attribute name, e.g. "xformOp:translate"
        opType:     The XformOp type, e.g. UsdGeom.XformOp.TypeScale
    """
    dstOp = UsdGeom.XformOp(xformable.GetPrim().GetAttribute(opName))
    if not dstOp:
        # create op
        dstOp = xformable.AddXformOp(opType, opPrecisionIfCreate)
    return dstOp
