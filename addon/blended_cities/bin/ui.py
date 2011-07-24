import bpy

# ###################################################
# COMMON OPERATORS
# ###################################################

class OP_BC_Selector(bpy.types.Operator) :
    '''next camera'''
    bl_idname = 'city.selector'
    bl_label = 'Next'

    action = bpy.props.StringProperty()

    def execute(self, context) :
        city = bpy.context.scene.city
        otl, action = self.action.split(' ')
        otl = city.outlines[otl]
        print(self)
        if action == 'child' :
            otl.selectChild(True)
        elif action == 'parent' :
            otl.selectParent(True)
        elif action == 'next' :
            otl.selectNext(True)
        elif action == 'previous' :
            otl.selectPrevious(True)
        elif action == 'edit' :
            otl.select()
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

# ###################################################
# COMMON UIs
# ###################################################

# common ui elements
def drawRemoveTag(layout) :
    row = layout.row()
    row.operator('perimeter.tag',text = 'Remove tag')

def drawMainbuildingsTool(layout) :
    
    row = layout.row()
    row.operator('buildings.list',text = 'List Building in console')
    
    row = layout.row()
    row.operator('buildings.wipe',text = 'Wipe buildings')      

    row = layout.row()
    row.operator('buildings.wipe',text = 'Wipe Tags and buildings').removetag = True

    row = layout.row()
    row.operator('buildings.build',text = 'Rebuild tagged')     

def drawElementSelector(layout,otl) :
    row = layout.row(align = True)
    row.operator( "city.selector", text='', icon = 'TRIA_DOWN').action='%s parent'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_UP' ).action='%s child'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_LEFT' ).action='%s previous'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_RIGHT' ).action='%s next'%otl.name
    row.operator( "city.selector",text='Edit', icon = 'TRIA_RIGHT' ).action='%s edit'%otl.name
        
# main panel
class BC_main_panel(bpy.types.Panel) :
    bl_label = 'City ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'main_ops'

    def draw(self, context):
        scene  = bpy.context.scene
        city = scene.city
        layout  = self.layout
        layout.alignment  = 'CENTER'
        drawMainbuildingsTool(layout)

# element tagger
class BC_outlines_panel(bpy.types.Panel) :
    bl_label = 'outlines ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'outlines_ops'


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
            if city.elementGet(bpy.context.active_object) == False : return True
        
        
    def draw(self, context):
        scene  = bpy.context.scene
        city = scene.city
        layout  = self.layout
        layout.alignment  = 'CENTER'
        # main boxes
    
        # PGN BOX
        row = layout.row()
        row.label('Tag List :')
        pgnbox = layout.box()
        row = layout.row()
        row.prop(city,'tagmenu',text='Define outline as :')
        row = layout.row()
        row.label('Type a new tag :')
        row = layout.row()
        #row.alignment = 'CENTER'
        row.operator('perimeter.tag',text = 'Tag it').action='add %s'%city.tagmenu


def register() :
    bpy.utils.register_class(OP_BC_Selector)
    bpy.utils.register_class(BC_main_panel)
    bpy.utils.register_class(BC_outlines_panel)

def unregister() :
    bpy.utils.unregister_class(OP_BC_Selector)
    bpy.utils.unregister_class(BC_main_panel)
    bpy.utils.unregister_class(BC_outlines_panel)

    
if __name__ == '__main__' :
    register()