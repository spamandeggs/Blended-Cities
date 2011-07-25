##\file
# a builder user interface file, the one of the buildings class 
# file naming convention : 
#
# xxxxxx_ui.py where xxxxxx is the name of the builder as it appears in the user interface
#
# buildings_ui.py should act as a reference for new builders ui. builders ui can use existing methods (operators, buttons, panels..) defined in ui.py 

import bpy
from blended_cities.bin.ui import *

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
        elm = city.elementGet(bpy.context.active_object)
        if elm.className() == 'outlines' : 
            building = elm.peer()
            otl  = elm
        else :
            building = elm
            otl = elm.peer()

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

        row = layout.row()
        row.operator('buildings.part',text='Add a part above this').action='add above'


def register() :
    bpy.utils.register_class(BC_buildings_panel)

def unregister() :
    bpy.utils.unregister_class(BC_buildings_panel)
    