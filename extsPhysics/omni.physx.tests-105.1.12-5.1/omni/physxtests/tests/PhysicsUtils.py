import omni.physx.scripts.physicsUtils as physicsUtils
from omni.physxtests import utils
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Vt, UsdPhysics
from omni.physxtests.utils.physicsBase import PhysicsMemoryStageBaseAsyncTestCase, TestCategory


use_tri_mesh_as_ground_plane = False

def joint_transform(bodyPos, bodyRot, p):
    trRotInv = Gf.Rotation(bodyRot).GetInverse()
    return trRotInv.TransformDir(p - bodyPos)

def scene_setup(stage):
    # set up axis to z
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # light
    sphereLight = UsdLux.SphereLight.Define(stage, Sdf.Path("/SphereLight"))
    sphereLight.CreateRadiusAttr(150)
    sphereLight.CreateIntensityAttr(30000)
    sphereLight.AddTranslateOp().Set(Gf.Vec3f(650.0, 0.0, 1150.0))

    # Physics scene
    scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/physicsScene"))
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)

def ground_plane_setup(stage):
    if use_tri_mesh_as_ground_plane:
        # (Graphics) Plane mesh
        # Trimesh
        shapeColor = Gf.Vec3f(0.5)
        entityPlane = physicsUtils.create_mesh_square_axis(stage, Sdf.Path("/trimesh"), "Z", 1500.0)
        entityPlane.CreateDisplayColorAttr().Set([shapeColor])
        prim = stage.GetPrimAtPath(Sdf.Path("/trimesh"))
        collisionAPI = UsdPhysics.CollisionAPI.Apply(prim)
        collisionAPI.CreateApproximationShapeAttr("none")
    else:
        # Plane
        physicsUtils.add_ground_plane(stage, "/groundPlane", "Z", 750.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))

def rigid_box_setup(stage):
    size = 50.0
    density = 1000
    color = Gf.Vec3f(71.0 / 255.0, 165.0 / 255.0, 1.0)
    position = Gf.Vec3f(50.0, 50.0, 200.0)
    orientation = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
    linVelocity = Gf.Vec3f(0.0)
    angularVelocity = Gf.Vec3f(0.0)
    cubePath = "/boxActor"

    physicsUtils.add_rigid_box(
        stage,
        cubePath,
        Gf.Vec3f(size, size, size),
        position,
        orientation,
        color,
        density,
        linVelocity,
        angularVelocity,
    )

def rigid_sphere_setup(stage):
    radius = 25.0
    density = 1000.0
    color = Gf.Vec3f(71.0 / 255.0, 125.0 / 255.0, 1.0)
    position = Gf.Vec3f(-50.0, -50.0, 200.0)
    orientation = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
    linVelocity = Gf.Vec3f(0.0)
    angularVelocity = Gf.Vec3f(0.0)
    spherePath = "/sphereActor"

    physicsUtils.add_rigid_sphere(stage, spherePath, radius, position, orientation, color, density, linVelocity, angularVelocity)

def rigid_capsule_setup(stage):
    radius = 25.0
    height = 50.0
    density = 1000.0
    color = Gf.Vec3f(71.0 / 255.0, 85.0 / 255.0, 1.0)
    position = Gf.Vec3f(50.0, -50.0, 200.0)
    orientation = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
    linVelocity = Gf.Vec3f(0.0)
    angularVelocity = Gf.Vec3f(0.0)
    capsulePath = "/capsuleActor"

    physicsUtils.add_rigid_capsule(
        stage, capsulePath, radius, height, "Z", position, orientation, color, density, linVelocity, angularVelocity
    )

def rigid_cylinder_setup(stage):
    radius = 25.0
    height = 50.0
    density = 1.0
    color = Gf.Vec3f(1.0, 0.0, 0.0)
    position = Gf.Vec3f(-50.0, 50.0, 200.0)
    orientation = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
    linVelocity = Gf.Vec3f(0.0)
    angularVelocity = Gf.Vec3f(0.0)
    path = "/cylinder"

    physicsUtils.add_rigid_cylinder(
        stage, path, radius, height, "X", position, orientation, color, density, linVelocity, angularVelocity
    )

def rigid_cone_setup(stage):
    radius = 25.0
    height = 50.0
    density = 1000.0
    color = Gf.Vec3f(71.0 / 255.0, 85.0 / 255.0, 1.0)
    position = Gf.Vec3f(-100.0, 100.0, 200.0)
    orientation = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
    linVelocity = Gf.Vec3f(0.0)
    angularVelocity = Gf.Vec3f(0.0)
    conePath = "/coneActor"

    physicsUtils.add_rigid_cone(
        stage, conePath, radius, height, "Z", position, orientation, color, density, linVelocity, angularVelocity
    )

def create_mesh_face_subset(mesh, faceIndices):
    return UsdGeom.Subset.CreateGeomSubset(mesh, "mySubset", "face", Vt.IntArray(faceIndices))

def create_hair_basiscurves(stage, path, numStrands, numVertsPerStrand, strandOffset: Gf.Vec3f, vertexOffset: Gf.Vec3f):
    curves = UsdGeom.BasisCurves.Define(stage, path)

    points = []
    vtxCounts = []

    for strand in range(numStrands):
        rootPos = strand * strandOffset
        for vtx in range(numVertsPerStrand):
            points.append(rootPos + vtx * vertexOffset)
        vtxCounts.append(numVertsPerStrand)

    curves.CreateCurveVertexCountsAttr().Set(vtxCounts)
    curves.CreatePointsAttr().Set(points)

    curves.GetTypeAttr().Set("linear")

    return curves

# Hair mesh with two ribbon-style strands
def create_hair_mesh(stage, path):
    points = []
    normals = []
    indices = []
    vertexCounts = []

    strandDir = Gf.Vec3f(0, 1, 0)
    centerlineOffset = Gf.Vec3f(0.5, 0, 0)
    normal = Gf.Vec3f(0, 0, 1)
    numTriangles = 8
    numStrands = 2

    for strand in range(numStrands):
        root = strand * normal

        # Zig-zag strand
        indexOffset = len(points)
        for vtxInStrand in range(numTriangles + 2):
            points.append(root + vtxInStrand * strandDir + (-1 + 2 * (vtxInStrand % 2)) * centerlineOffset)
            normals.append(normal)

        # any three consecutive vertices should form a face
        vertexCounts.extend([3] * numTriangles)
        for i in range(numTriangles):
            idx = indexOffset + i
            indices.extend([idx, idx + 1, idx + 2])

    return physicsUtils.create_mesh(stage, path, points, normals, indices, vertexCounts)


def create_hair_mesh_subset(stage, path):
    # Assumes that there is an even number of strands and we can just take the first half of the face indices
    mesh = create_hair_mesh(stage, path)
    numFacesInSubset = len(mesh.GetFaceVertexCountsAttr().Get()) // 2
    subset = create_mesh_face_subset(mesh, list(range(numFacesInSubset)))

    return (mesh, subset)



class PhysicsUtilsTestMemoryStage(PhysicsMemoryStageBaseAsyncTestCase):
    category = TestCategory.Core
    
    async def test_physics_utils(self):
        stage = await self.new_stage()

        scene_setup(stage)

        # expect one static body with plane
        ground_plane_setup(stage)
        self.step()
        utils.check_stats(self, {"numPlaneShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 0 })

        # add dynamic box
        rigid_box_setup(stage)
        self.step()
        utils.check_stats(self, { "numPlaneShapes": 1, "numBoxShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 1 })

        # add dynamic sphere
        rigid_sphere_setup(stage)
        self.step()
        utils.check_stats(self, { "numPlaneShapes": 1, "numBoxShapes": 1, "numSphereShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 2 })

        # add dynamic capsule
        rigid_capsule_setup(stage)
        self.step()
        utils.check_stats(self, { "numPlaneShapes": 1, "numBoxShapes": 1, "numSphereShapes": 1, "numCapsuleShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 3 })

        # add dynamic cylinder
        rigid_cylinder_setup(stage)
        self.step()
        utils.check_stats(self, { "numPlaneShapes": 1, "numBoxShapes": 1, "numSphereShapes": 1, "numCapsuleShapes": 1, "numCylinderShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 4 })

        # add dynamic cone
        rigid_cone_setup(stage)
        self.step()
        utils.check_stats(self, { "numPlaneShapes": 1, "numBoxShapes": 1, "numSphereShapes": 1, "numCapsuleShapes": 1, "numCylinderShapes": 1, "numConeShapes": 1, "numStaticRigids": 1, "numDynamicRigids": 5 })
