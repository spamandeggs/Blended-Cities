import bpy
from blended_cities.bin.ui import *

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
        elm = city.elementGet(ob)
        if elm.className() == 'outlines' : 
            sdw = elm.peer()
            otl  = elm
        else :
            sdw = elm
            otl = elm.peer()

        layout  = self.layout
        layout.alignment  = 'CENTER'
        
        row = layout.row()
        row.label(text = 'Name : %s / %s'%(sdw.objectName(),sdw.name))
        
        row = layout.row()
        row.label(text = 'Sidewalk Height:')
        row.prop(sdw,'height')


        layout.separator()

        drawRemoveTag(layout)

