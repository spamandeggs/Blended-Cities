import bpy
import mathutils
from mathutils import *
from blended_cities.core.class_main import *
from blended_cities.utils.meshes_io import *
from blended_cities.core.ui import *

class BC_sidewalks(BC_elements,bpy.types.PropertyGroup) :
    bl_description = 'Sidewalk'
    bl_label = 'Sidewalk'
    bl_idname = 'sidewalks'

    #name = bpy.props.StringProperty()
    attached = bpy.props.StringProperty()   # the perimeter object
    height = bpy.props.FloatProperty(
        default = 0.2,
        min=0.1,
        max=0.4,
        update=updateBuild
        )
    materialslots = ['floor','inter']
    materials = ['floor','inter']
    def build(self,refreshData=True) :
        return buildBox(self,refreshData)


def buildBox(self,refreshData=True) :
    city = bpy.context.scene.city
    otl = self.peer()
    print('build sidewalk %s (outline %s)'%(self.name,otl.name))

    matslots = ['floor','inter'] 
    mat_floor = 0
    mat_inter = 1

    if refreshData :
        print('refresh data')
        print(otl.dataRead())
    perimeters = otl.dataGet()

    verts = []
    faces = []
    mats  = []

    fof = 0
    z = self.height
    for perimeter in perimeters :
        fpf = len(perimeter)

        for c in perimeter :
            verts.append( Vector(( c[0],c[1],c[2] )) )
        for c in perimeter :
            verts.append( Vector(( c[0],c[1],c[2]+z )) )
        faces.extend( facesLoop(0,fpf) )
        fof += fpf

    #self.selectObject()
    #bpy.ops.object.mode_set(mode='EDIT')
    #bpy.ops.mesh.fill()
    #bpy.ops.object.mode_set(mode='OBJECT')


    ob = ObjectBuild(self, verts, [], faces, [], [])
    city.elements[self.name].pointer = str(ob.as_pointer())


# a city element panel
class BC_sidewalks_panel(bpy.types.Panel) :
    bl_label = 'Sidewalks'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'sidewalks'

    @classmethod
    def poll(self,context) :
        return pollBuilders(context,'sidewalks')


    def draw_header(self, context):
        drawHeader(self,'builders')


    def draw(self, context):
        city = bpy.context.scene.city
        modal = bpy.context.window_manager.modal
        scene  = bpy.context.scene
        ob = bpy.context.active_object
        # either the building or its outline is selected : lookup
        sdw, otl = city.elementGet(ob)

        layout  = self.layout
        layout.alignment  = 'CENTER'

        row = layout.row()
        row.label(text = 'Name : %s / %s'%(sdw.objectName(),sdw.name))

        row = layout.row()
        row.label(text = 'Sidewalk Height:')
        row.prop(sdw,'height')


        layout.separator()
