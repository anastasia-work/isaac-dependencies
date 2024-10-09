import omni.kit.commands
import carb
from pxr import UsdGeom, Sdf, Gf, Vt, Usd, UsdPhysics
import omni.physxdemos as demo
from omni.physx import get_physx_cooking_interface
from omni.debugdraw import get_debug_draw_interface


def to_world(point, world_matrix):
    gf_point = Gf.Vec3f(point.x, point.y, point.z)
    world_point = world_matrix.Transform(gf_point)
    return carb.Float3(world_point[0], world_point[1], world_point[2])

class ConvexMeshDatademo(demo.Base):
    title = "Convex Mesh Data"
    category = demo.Categories.SCENE_QUERY
    short_description = "Demo showing convex mesh data usage"
    description = "Demo showing convex mesh data usage. The convex mesh data from cooking is displayed when the simulation is running. Press play (space) to run the simulation."

    def create(self, stage):
        self._stage = stage
        self._debugDraw = get_debug_draw_interface()

        self.defaultPrimPath, scene = demo.setup_physics_scene(self, stage, upAxis = UsdGeom.Tokens.y)
        room = demo.get_demo_room(self, stage, zoom = 0.5, floorOffset = -100.0, hasTable = False, camYaw = 0.06)

        self._path = self.defaultPrimPath + "/convexActor"
        
        convexGeom = UsdGeom.Mesh.Define(stage, self._path)
        convexPrim = stage.GetPrimAtPath(self._path)

        faceVertexCounts = [4, 4, 4, 4, 4, 4]
        faceVertexIndices = [0, 1, 3, 2, 4, 5, 7, 6, 10, 11, 13, 12, 14, 15, 9, 8, 17, 23, 21, 19, 22, 16, 18, 20]
        convexSize = 50
        convexSize2 = 25
        points = [
            Gf.Vec3f(-convexSize, convexSize, -convexSize),   Gf.Vec3f(convexSize, convexSize, -convexSize),   Gf.Vec3f(-convexSize2, convexSize2, convexSize), Gf.Vec3f(convexSize2, convexSize2, convexSize),
            Gf.Vec3f(-convexSize2, -convexSize2, convexSize), Gf.Vec3f(convexSize2, -convexSize2, convexSize), Gf.Vec3f(-convexSize, -convexSize, -convexSize), Gf.Vec3f(convexSize, -convexSize, -convexSize),
            Gf.Vec3f(-convexSize, convexSize, -convexSize),   Gf.Vec3f(convexSize, convexSize, -convexSize),   Gf.Vec3f(-convexSize2, convexSize2, convexSize), Gf.Vec3f(convexSize2, convexSize2, convexSize),
            Gf.Vec3f(-convexSize2, -convexSize2, convexSize), Gf.Vec3f(convexSize2, -convexSize2, convexSize), Gf.Vec3f(-convexSize, -convexSize, -convexSize), Gf.Vec3f(convexSize, -convexSize, -convexSize),
            Gf.Vec3f(-convexSize, convexSize, -convexSize),   Gf.Vec3f(convexSize, convexSize, -convexSize),   Gf.Vec3f(-convexSize2, convexSize2, convexSize), Gf.Vec3f(convexSize2, convexSize2, convexSize),
            Gf.Vec3f(-convexSize2, -convexSize2, convexSize), Gf.Vec3f(convexSize2, -convexSize2, convexSize), Gf.Vec3f(-convexSize, -convexSize, -convexSize), Gf.Vec3f(convexSize, -convexSize, -convexSize),
        ]

        convexGeom.CreateFaceVertexCountsAttr(faceVertexCounts)
        convexGeom.CreateFaceVertexIndicesAttr(faceVertexIndices)
        convexGeom.CreatePointsAttr(points)
        convexGeom.CreateDisplayColorAttr().Set([demo.get_primary_color()])

        UsdPhysics.CollisionAPI.Apply(convexPrim)
        mesh_api = UsdPhysics.MeshCollisionAPI.Apply(convexPrim)
        mesh_api.CreateApproximationAttr(UsdPhysics.Tokens.convexHull)
        self._mesh_prim = convexPrim
    
    def update(self, stage, dt, viewport, physxIFace):        
        if not self._mesh_prim:
            return

        num_convex_hulls = get_physx_cooking_interface().get_nb_convex_mesh_data(str(self._path))
        source_to_world = UsdGeom.Xformable(self._mesh_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        for index in range(num_convex_hulls):
            convex_hull_data = get_physx_cooking_interface().get_convex_mesh_data(str(self._path), index)
            if convex_hull_data["num_polygons"] and convex_hull_data["num_polygons"] > 0:
                indices = convex_hull_data["indices"]
                vertices = convex_hull_data["vertices"]
                polygons = convex_hull_data["polygons"]
                for poly_index in range(convex_hull_data["num_polygons"]):
                    index_base = polygons[poly_index]["index_base"]
                    previous_index = -1
                    for vertex_index in range(polygons[poly_index]["num_vertices"]):
                        current_index = indices[index_base + vertex_index]
                        if previous_index != -1:
                            color = 0xffffff00
                            point0 = to_world(vertices[previous_index], source_to_world)
                            point1 = to_world(vertices[current_index], source_to_world)
                            self._debugDraw.draw_line(point0 ,color, point1, color)
                        previous_index = current_index
                    point0 = to_world(vertices[previous_index], source_to_world)
                    point1 = to_world(vertices[indices[index_base]], source_to_world)
                    self._debugDraw.draw_line(point0 ,color, 1.0, point1, color, 1.0)
