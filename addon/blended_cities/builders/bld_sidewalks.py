import bpy
import mathutils
from mathutils import *
from blended_cities.core.class_main import *
from blended_cities.utils.meshes_io import *
from blended_cities.core.ui import *
from blended_cities.utils import  geo

class BC_sidewalks(BC_elements,bpy.types.PropertyGroup) :
    bc_label = 'Sidewalk'
    bc_description = 'a simple sidewalk'
    bc_collection = 'sidewalks'
    bc_element = 'sidewalk'

    #name = bpy.props.StringProperty()
    attached = bpy.props.StringProperty()   # the perimeter object
    blockHeight = bpy.props.FloatProperty(
        default = 0.2,
        min=0.1,
        max=0.4,
        update=updateBuild
        )
    sidewalkWidth = bpy.props.FloatProperty(
        default = 1.5,
        min=0.0,
        max=10.0,
        update=updateBuild
        )
    materialslots = ['floor','inter']
    materials = ['floor','inter']


    def build(self,refreshData=True) :

        city = bpy.context.scene.city
        otl = self.peer()

        # the objects generated here will be contained in :
        elements = []

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
        z = self.blockHeight
        for perimeter in perimeters :
            fpf = len(perimeter)
            ground = []
            for c in perimeter :
                verts.append( Vector(( c[0],c[1],c[2] )) )
            for c in perimeter :
                ground.append( Vector(( c[0],c[1],c[2] + z )) )
            verts.extend(ground)
            faces.extend( geo.facesLoop(fof,fpf) )
            faces.extend( geo.fill(verts[-fpf:],fof+fpf) )
            fof += fpf*2

            #outline_verts = []
            #outline_verts.extend(ground)
            outline_verts = polyIn(ground,-self.sidewalkWidth,'coord')
            #print('polyin: %s'%pol)
            outline_edges = edgesLoop(0, len(outline_verts))
            elements.append( ['outline', outline_verts, outline_edges, [], [], [] ] )

        sidewalks = [ verts, [], faces, [], [] ]
        elements.append(sidewalks)

        return elements

    def height(self,offset=0) :
        return self.blockHeight

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
        row.prop(sdw,'blockHeight')

        row = layout.row()
        row.label(text = 'Sidewalk Width:')
        row.prop(sdw,'sidewalkWidth')

        layout.separator()