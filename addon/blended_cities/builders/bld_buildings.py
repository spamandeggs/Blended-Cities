##\file
# the building builder file
#
# should act as a reference for other builders files.
#
# builders ui can use existing methods (operators, buttons, panels..)
# 
import bpy
import mathutils
from mathutils import *
from blended_cities.core.class_main import *
from blended_cities.utils.meshes_io import *
from blended_cities.core.ui import *

## building builder class
#
# should act as a reference for other builders class.
#
# builders ui can use existing methods (operators, buttons, panels..)
# each builder class define its own field, depending of the needed parametrics. but some field are mandatory
#
#
class BC_buildings(BC_elements,bpy.types.PropertyGroup) :
    bc_label = 'Building'
    bc_description = 'a simple building with multiple floors'
    bc_collection = 'buildings'

    #name = bpy.props.StringProperty()
    attached = bpy.props.StringProperty()   # the perimeter object
    inherit = bpy.props.BoolProperty(default=False,update=updateBuild)
    floorNumber = bpy.props.IntProperty(
        default = 3,
        min=1,
        max=30,
        update=updateBuild
        )
    floorHeight = bpy.props.FloatProperty(
        default = 2.4,
        min=2.2,
        max=5.0,
        update=updateBuild
        )
    firstFloorHeight = bpy.props.FloatProperty(
        default = 3,
        min=2.2,
        max=5,
        update=updateBuild
        )
    firstFloor = bpy.props.BoolProperty(update=updateBuild)
    interFloorHeight = bpy.props.FloatProperty(
        default = 0.3,
        min=0.1,
        max=1.0,
        update=updateBuild
        )
    roofHeight = bpy.props.FloatProperty(
        default = 0.5,
        min=0.1,
        max=1.0,
        update=updateBuild
        )
    materialslots = ['floor','inter']
    materials = ['floor','inter']

    ## every builder class must have a function named build().
    # this is were the shape attached to the outline is built
    def build(self,refreshData=True) :
        otl = self.peer()
        print('** build() %s (outline %s)'%(self.name,otl.name))

        matslots = ['floor','inter'] 
        mat_floor = 0
        mat_inter = 1

        if refreshData :
            print('ask for data read')
            otl.dataRead()
        perimeter = otl.dataGet('perimeters')
        zlist = zcoords(perimeter)
        print('highest vert is %s'%max(zlist))
        
        verts = []
        faces = []
        mats  = []

        fof = 0 # 'floor' vertex id offset

        for id in range(len(perimeter)) :

            fpf = len(perimeter[id]) # nb of faces per floor

            # non planar outlines : add simple fundations. todo : should be part of floors
            if max(zlist) - min(zlist) > 0.000001 :
                verts.extend( perimeter[id] )
                faces.extend( facesLoop(fof,fpf) )
                mats.extend( mat_floor for i in range(fpf) )
                fof += fpf

            zs = self.heights(max(zlist))#bounds[2][0])
            for zi,z in enumerate(zs) :
                for c in perimeter[id] :
                    verts.append( Vector(( c[0],c[1],z )) )
                
                # while roof not reached, its a floor so add faces and mats
                if z != zs[-1] : 
                    faces.extend( facesLoop(fof,fpf) )
                    mat_id = zi%2
                    mats.extend( mat_id for i in range(fpf) )
                fof += fpf

        ob = objectBuild(self, verts, [], faces, matslots, mats)

        height = self.height() + max(zlist)
        updateChildHeight(otl,height)
        print('* end build()')

    def heights(self,offset=0) :
        city = bpy.context.scene.city
        this = self
        while this.inherit == True :
            print(this.name,this.inherit)
            otl = this.Parent(True)
            if otl.className() != this.className() : this.inherit = False 
            else : this = otl.peer()
        zs = [] # list of z coords of floors and ceilings
        for i in range( self.floorNumber ) :
            if i == 0 :
                zf = offset
                if self.firstFloor :
                    zc = offset + self.firstFloorHeight
                else :
                    zc = offset + this.floorHeight
            else :
                zf = zc + this.interFloorHeight
                zc = zf + this.floorHeight
            zs.append(zf)
            zs.append(zc)
        zs.append(zc + this.roofHeight) # roof

        return zs
 
    def height(self,offset=0) :
        return self.heights(offset)[-1]


## building builder user interface class
class BC_buildings_panel(bpy.types.Panel) :
    bl_label = 'Buildings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'buildings'


    @classmethod
    def poll(self,context) :
        return pollBuilders(context,'buildings')


    def draw_header(self, context):
        drawHeader(self,'builders')


    def draw(self, context):
        city = bpy.context.scene.city
        scene  = bpy.context.scene

        # either the building or its outline is selected : lookup
        building, otl = city.elementGet(bpy.context.active_object)

        layout  = self.layout
        layout.alignment  = 'CENTER'

        drawElementSelector(layout,otl)

        row = layout.row()
        row.label(text = 'Name : %s / %s'%(building.objectName(),building.name))

        row = layout.row()
        row.label(text = 'Floor Number:')
        row.prop(building,'floorNumber')

        row = layout.row()
        row.label(text = 'Build First Floor :')
        row.prop(building,'firstFloor')

        row = layout.row()
        row.label(text = 'Inherit Values :')
        row.prop(building,'inherit')

        if building.inherit : ena = False
        else : ena = True

        row = layout.row()
        row.active = ena
        row.label(text = 'Floor Height :')
        row.prop(building,'floorHeight')

        row = layout.row()
        row.active = building.firstFloor
        row.label(text = '1st Floor Height :')
        row.prop(building,'firstFloorHeight')

        row = layout.row()
        row.active = ena
        row.label(text = 'Inter Floor Height :')
        row.prop(building,'interFloorHeight')

        row = layout.row()
        row.active = ena
        row.label(text = 'Roof Height :')
        row.prop(building,'roofHeight')