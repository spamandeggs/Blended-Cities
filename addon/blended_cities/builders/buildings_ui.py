import bpy
from blended_cities.bin.ui import *

# a city element panel
class BC_buildings_panel(bpy.types.Panel) :
    bl_label = 'Building ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'building_ops'


    #def draw_header(self, context):
    #    layout = self.layout
    #   row = layout.row(align = True)
    #    row.label(icon = 'SEQ_PREVIEW')
    @classmethod
    def poll(self,context) :
        city = bpy.context.scene.city
        if bpy.context.mode == 'OBJECT' and \
        len(bpy.context.selected_objects) == 1 and \
        type(bpy.context.active_object.data) == bpy.types.Mesh :
            elm = city.elementGet(bpy.context.active_object)
            if elm :
                #print(elm.className())
                if ( elm.className() == 'outlines' and city.elements[elm.attached].type == 'buildings') or \
                elm.className() == 'buildings' :
                    return True
                    #tagClass = eval('city.%s'%city.element[ob.name].type)
                    #print(tagClass[ob.name].outline)
                    #bpy.ops.object.select_name(name=tagClass[ob.name].outline)
                #'citytag' in  and bpy.context.active_object['citytag'] == 'building_lot' : 
                # use poll to create the mesh if does not exists ?
                #return True
        
        
    def draw(self, context):
        city = bpy.context.scene.city
        modal = bpy.context.window_manager.modal
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

        drawElementSelector(layout,otl)

        row = layout.row()
        row.label(text = 'AutoRefresh :')
        if modal.status :
            row.operator('wm.modal_stop',text='Stop')
        else :
            row.operator('wm.modal_start',text='Start')
        row.operator('wm.modal',text='test')

        layout.separator()

        drawRemoveTag(layout)


def register() :
    bpy.utils.register_class(BC_buildings_panel)

def unregister() :
    bpy.utils.unregister_class(BC_buildings_panel)
    