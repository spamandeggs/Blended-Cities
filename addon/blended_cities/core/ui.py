##\file
# ui.py
# core and shared user interface components
print('ui.py')
import bpy
from blended_cities.utils.meshes_io import *

# ###################
# COMMON UI OPERATORS 
# ###################
# should call a xxx.method rateher than be clever. the least code in it
# methods could return some value or False/None to obtain the {'CANCELLED'}
# or {'FINISHED'} status

## this operator links the gui buttons to any city methods
# example city.init() is called from here by the ui : ops.city.method(action = 'init')
class OP_BC_cityMethods(bpy.types.Operator) :
    bl_idname = 'city.method'
    bl_label = 'city method'

    action = bpy.props.StringProperty()

    def execute(self, context) :
        city = bpy.context.scene.city
        act = objs = tags = elms = ''
        args = self.action.split(' ')
        if len(args) == 1 : act = args[0]
        elif len(args) == 2 : act, objs = args
        elif len(args) == 3 : act, objs, tags = args
        else : act, objs, tags, elms = args

        print('\nact : %s / objs : %s / tags : %s/ elms : %s\n'%(act,objs,tags,elms))

        if act == 'init' :
            city.init()
            return {'FINISHED'}

        elif act == 'build' :
            objs = city.build(objs,tags)
            print('builded %s objects'%(len(objs)))
            return {'FINISHED'}

        elif act == 'list' :
            city.list(objs,tags)
            return {'FINISHED'}

        elif act == 'stack' :
            new_objs = city.elementStack(objs,tags)
            print('stacked %s new %s'%(len(new_objs),tags))
            # list & select them
            return {'FINISHED'}

        elif act == 'add' :
            new_objs = city.elementAdd(objs,tags)
            print('created %s new %s'%(len(new_objs),tags))
            # list & select them
            return {'FINISHED'}

        elif act == 'remove' :
            del_objs = city.elementRemove(objs,tags,eval(elms))
            print('removed %s objects from %s'%(len(del_objs),tags))
            # list them
            return {'FINISHED'} 

        else : return {'CANCELLED'}


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

## set of common methods for operators (actually just one atm :)
# 'add above' allows to stack a new outline and a new member of the current class above an existing element.
# it takes the higher vert of the parent element and construct from here a new outline, based on the data of his parent.
# its cares about elements relationships and parenting of the objects

class OP_BC_buildingWipe(bpy.types.Operator) :
   
    bl_idname = 'buildings.wipe'
    bl_label = 'remove all'
    
    removetag = bpy.props.BoolProperty()
    
    def execute(self,context) :
        city = bpy.context.scene.city
        for b in city.builders.buildings :
            wipeOutObject(b.name)
        if self.removetag :
            while len(city.builders.buildings) > 0 :
                name=city.builders.buildings[0].name
                elm = city.elements[name].index()
                city.builders.buildings.remove(0)
                city.elements.remove(elm)
            while len(city.outlines) > 0 :
                name=city.outlines[0].name
                elm = city.elements[name].index()
                city.outlines.remove(0)
                city.elements.remove(elm)
                # but we keep the objects
        return {'FINISHED'}


# ########################################################
# set of generic update functions used in builders classes
# ########################################################

## can be used by the update function of the panel properties of a builder
#
# to rebuild the selected element. it's a 'link' function to the build() function
#
# defined in the builders class element
def updateBuild(self,context='') :
    self.build(True)

# ###################################################
# COMMON UIs PANEL
# ###################################################

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

## draw start/stop modal buttons
def drawModal(layout) :
    modal = bpy.context.window_manager.modal
    row = layout.row()
    row.label(text = 'AutoRefresh :')
    if modal.status :
        row.operator('wm.modal_stop',text='Stop')
    else :
        row.operator('wm.modal_start',text='Start')
    row.operator('wm.modal',text='test')

## depending on the user selection in the 3d view, display the corresponding builder panel
# if the selection exists in the elements class
# the function is called from the builders guis poll() function, like buildings_ui.py
# @param classname String. the name of the builder as in the dropdown.
def pollBuilders(context, classname, obj_mode = 'OBJECT') :
    city = bpy.context.scene.city
    if bpy.context.mode == obj_mode and \
    len(bpy.context.selected_objects) == 1 and \
    type(bpy.context.active_object.data) == bpy.types.Mesh :
        elm, otl = city.elementGet(bpy.context.active_object)
        if elm :
            #print(elm.name,elm.className(),elm.peer().className(),classname)
            if ( elm.className() == 'outlines' and elm.peer().className() == classname) or \
            elm.className() == classname :
                #print('True')
                return True
    return False

#
# some functions that remove/recreate globally the objects of the city. (tests)
def drawMainbuildingsTool(layout) :
    scene = bpy.context.scene

    row = layout.row()
    row.prop(scene.unit_settings,'scale_length')
    
    row = layout.row()
    row.operator('city.method',text = 'Rebuild All').action = 'build all'    

    row = layout.row()
    row.operator('city.method',text = 'Initialise').action = 'init'

    row = layout.row()
    row.operator('city.method',text = 'List Elements').action = 'list all'
    
    row = layout.row()
    row.operator('city.method',text = 'Remove objects').action = 'remove all all False'

    row = layout.row()
    row.operator('city.method',text = 'Remove obj. and tags').action = 'remove all all True'

def drawOutlinesTools(layout) :
    wm = bpy.context.window_manager

    row = layout.row()
    row.operator('city.method',text = 'Stack a new element').action='stack selected %s'%wm.city_builders_dropdown

    row = layout.row()
    row.operator('city.method',text = 'Remove').action='remove selected all True'


####################################################
## the main Blended Cities panel
####################################################
class BC_main_panel(bpy.types.Panel) :
    bl_label = 'Blended Cities'
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

        drawModal(layout)

####################################################
## the main Blended Cities panel (OBJECT MODE)
####################################################
class BC_outlines_panel(bpy.types.Panel) :
    bl_label = 'Outlines'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'outlines_ops'

    @classmethod
    def poll(self,context) :
        city = bpy.context.scene.city
        if bpy.context.mode == 'OBJECT' and \
        len(bpy.context.selected_objects) >= 1 :
            return True
        return False

    def draw_header(self, context):
        drawHeader(self,'outlines')
   
    def draw(self, context):
        scene  = bpy.context.scene
        wm = bpy.context.window_manager
        city = scene.city
        ob = bpy.context.active_object
        elm, otl = city.elementGet(ob)

        layout  = self.layout
        layout.alignment  = 'CENTER'

        # displays info about element if current selection
        # is already an element
        if elm :
            row = layout.row()
            row.label('%s as %s'%(ob.name,elm.className()))
            row = layout.row()
            row.label('known as %s'%(elm.name))

            drawOutlinesTools(layout)
            
            row = layout.row()
            row.label('Redefine Selected as :')

        # add new element to create from the selected outline
        # or an existing one to change
        else :
            row = layout.row()
            row.label('Define Selected as :')
        row = layout.row()
        row.prop(wm,'city_builders_dropdown',text='')
        row.operator('city.method',text = '',icon='FILE_TICK').action='add selected %s'%wm.city_builders_dropdown

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