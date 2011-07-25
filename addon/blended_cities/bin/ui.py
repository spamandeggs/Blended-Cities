##\file
# ui.py
# core and shared user interface components

import bpy

# ###################################################
# COMMON OPERATORS
# ###################################################

## Operator called by drawElementSelector
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

## can be used by the update function of the panel properties of a builder
#
# to rebuild the selected element. it's a 'link' function to the build() function
#
# defined in the builders class element
def updateBuild(self,context='') :
    self.build(True)

## common ui elements
def drawRemoveTag(layout) :
    row = layout.row()
    row.operator('perimeter.tag',text = 'Remove tag')

## can be called from panel a draw() function
#
# some functions that remove/recreate globally the objects of the city. (tests)
def drawMainbuildingsTool(layout) :
    
    row = layout.row()
    row.operator('buildings.list',text = 'List Building in console')
    
    row = layout.row()
    row.operator('buildings.wipe',text = 'Wipe buildings')      

    row = layout.row()
    row.operator('buildings.wipe',text = 'Wipe Tags and buildings').removetag = True

    row = layout.row()
    row.operator('buildings.build',text = 'Rebuild tagged')     


## can be called from panel a draw() function
#
# to navigate into parts (elements) of an object.
# it dispplays navigation buttons that can select an element related to the selected one : parent, child or sibling element.
def drawHeader(self,classtype) :
    if classtype == 'builders'   : icn = 'OBJECT_DATAMODE'
    elif classtype == 'outlines' : icn = 'MESH_DATA'
    elif classtype == 'elements' : icn = 'WORDWRAP_ON'
    elif classtype == 'main'     : icn = 'SCRIPTWIN'
    layout = self.layout
    row = layout.row(align = True)
    row.label(icon = icn )


## can be called from panel a draw() function
#
# to navigate into parts (elements) of an object.
# it dispplays navigation buttons that can select an element related to the selected one : parent, child or sibling element.
def drawElementSelector(layout,otl) :
    row = layout.row(align = True)
    row.operator( "city.selector", text='', icon = 'TRIA_DOWN').action='%s parent'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_UP' ).action='%s child'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_LEFT' ).action='%s previous'%otl.name
    row.operator( "city.selector",text='', icon = 'TRIA_RIGHT' ).action='%s next'%otl.name
    row.operator( "city.selector",text='Edit', icon = 'TRIA_RIGHT' ).action='%s edit'%otl.name


## depending on the user selection in the 3d view, display the corresponding builder panel
# if the selection exists in the elements class
# the function is called from the builders guis poll() function, like buildings_ui.py
# @param classname String. the name of the builder as in the dropdown.
def pollBuilders(context, classname, obj_mode = 'OBJECT') :
    city = bpy.context.scene.city
    if bpy.context.mode == obj_mode and \
    len(bpy.context.selected_objects) == 1 and \
    type(bpy.context.active_object.data) == bpy.types.Mesh :
        elm = city.elementGet(bpy.context.active_object)
        if elm :
            #print(elm.name,elm.className(),elm.peer().className(),classname)
            if ( elm.className() == 'outlines' and elm.peer().className() == classname) or \
            elm.className() == classname :
                #print('True')
                return True
    return False
 

## the main Blended Cities panel
class BC_main_panel(bpy.types.Panel) :
    bl_label = 'City ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'main_ops'

    def draw_header(self, context):
        drawHeader(self,'main')

    def draw(self, context):
        scene  = bpy.context.scene
        city = scene.city
        layout  = self.layout
        layout.alignment  = 'CENTER'
        drawMainbuildingsTool(layout)

        # modal
        modal = bpy.context.window_manager.modal
        row = layout.row()
        row.label(text = 'AutoRefresh :')
        if modal.status :
            row.operator('wm.modal_stop',text='Stop')
        else :
            row.operator('wm.modal_start',text='Start')
        row.operator('wm.modal',text='test')

## the Outlines panel
#
# Dedicated to outlines functions (OBJECT MODE)
class BC_outlines_panel(bpy.types.Panel) :
    bl_label = 'Outlines'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'outlines_ops'

    @classmethod
    def poll(self,context) :
        city = bpy.context.scene.city
        if bpy.context.mode == 'OBJECT' and \
        len(bpy.context.selected_objects) == 1 and \
        type(bpy.context.active_object.data) == bpy.types.Mesh :
            return True
        return False

    def draw_header(self, context):
        drawHeader(self,'outlines')
   
    def draw(self, context):
        scene  = bpy.context.scene
        wm = bpy.context.window_manager
        city = scene.city
        ob = bpy.context.active_object
        elm = city.elementGet(ob)

        layout  = self.layout
        layout.alignment  = 'CENTER'

        # displays info about element if current selection
        # is already an element
        if elm :
            row = layout.row()
            row.label('%s is in the %s collection'%(ob.name,elm.className()))
            row = layout.row()
            row.label('known as %s'%(elm.name))
            #elm.className() elm.name() ob
            row = layout.row()
            row.label('Define Selected as :')

        # add new element to create from the selected outline
        # or an existing one to change
        else :
            row = layout.row()
            row.label('Redefine Selected as :')
        row = layout.row()
        row.prop(wm,'city_builders_dropdown',text='')
        #row = layout.row()
        row.operator('perimeter.tag',text = '',icon='FILE_TICK').action='add %s'%wm.city_builders_dropdown


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