from omni.physx.scripts.physicsUtils import *
from pxr import Usd, UsdLux, UsdGeom, UsdShade, Sdf, Gf, Tf, Vt, UsdPhysics, PhysxSchema
from omni.physx import get_physx_interface, get_physx_simulation_interface
from omni.physx.bindings._physx import SimulationEvent
from random import seed
from random import random
import omni.physxdemos as demo


class ContactReportDemo(demo.Base):
    title = "Contact Report Callback"
    category = demo.Categories.CONTACTS
    short_description = "Demo showing contact report callback listening"
    description = "Demo showing contact report listening. Press play (space) to run the simulation, the received contact information can be seen in the console."

    def create(self, stage):
        seed(1)
        # subscribe to physics contact report event, this callback issued after each simulation step
        self._contact_report_sub = None

        defaultPrimPath, scene = demo.setup_physics_scene(self, stage)

        room = demo.get_demo_room(self, stage, staticDynamicRestitution = Gf.Vec3f(0.0, 0.0, 1.0))

        # Sphere material
        materialPath = defaultPrimPath + "/sphereMaterial"
        UsdShade.Material.Define(stage, materialPath)
        material = UsdPhysics.MaterialAPI.Apply(stage.GetPrimAtPath(materialPath))
        material.CreateStaticFrictionAttr().Set(0.5)
        material.CreateDynamicFrictionAttr().Set(0.5)
        material.CreateRestitutionAttr().Set(0.9)
        material.CreateDensityAttr().Set(0.001)

        # Spheres
        spherePath = defaultPrimPath + "/sphere"

        radius = 30.0
        position = Gf.Vec3f(0.0, 0.0, 400.0)
        orientation = Gf.Quatf(1.0)
        color = demo.get_primary_color()
        density = 0.001
        linvel = Gf.Vec3f(0.0)

        add_rigid_sphere(stage, spherePath, radius, position, orientation, color, density, linvel, Gf.Vec3f(0.0))

        # Add material        
        add_physics_material_to_prim(stage, stage.GetPrimAtPath(Sdf.Path(spherePath)), Sdf.Path(materialPath))

        # apply contact report
        spherePrim = stage.GetPrimAtPath(spherePath)
        contactReportAPI = PhysxSchema.PhysxContactReportAPI.Apply(spherePrim)
        contactReportAPI.CreateThresholdAttr().Set(200000)

    def on_shutdown(self):
        self._contact_report_sub = None

    def on_stop(self):
        self._contact_report_sub = None

    def update(self, stage, dt, viewport, physxIFace):
        if not self._contact_report_sub:
            self._contact_report_sub = get_physx_simulation_interface().subscribe_contact_report_events(self._on_contact_report_event)
        
    def _on_contact_report_event(self, contact_headers, contact_data):
        for contact_header in contact_headers:
            print("Got contact header type: " + str(contact_header.type))
            print("Actor0: " + str(PhysicsSchemaTools.intToSdfPath(contact_header.actor0)))
            print("Actor1: " + str(PhysicsSchemaTools.intToSdfPath(contact_header.actor1)))
            print("Collider0: " + str(PhysicsSchemaTools.intToSdfPath(contact_header.collider0)))
            print("Collider1: " + str(PhysicsSchemaTools.intToSdfPath(contact_header.collider1)))
            print("StageId: " + str(contact_header.stage_id))
            print("Number of contacts: " + str(contact_header.num_contact_data))
            
            contact_data_offset = contact_header.contact_data_offset
            num_contact_data = contact_header.num_contact_data
            
            for index in range(contact_data_offset, contact_data_offset + num_contact_data, 1):
                print("Contact:")
                print("Contact position: " + str(contact_data[index].position))
                print("Contact normal: " + str(contact_data[index].normal))
                print("Contact impulse: " + str(contact_data[index].impulse))
                print("Contact separation: " + str(contact_data[index].separation))
                print("Contact faceIndex0: " + str(contact_data[index].face_index0))
                print("Contact faceIndex1: " + str(contact_data[index].face_index1))
                print("Contact material0: " + str(PhysicsSchemaTools.intToSdfPath(contact_data[index].material0)))
                print("Contact material1: " + str(PhysicsSchemaTools.intToSdfPath(contact_data[index].material1)))
