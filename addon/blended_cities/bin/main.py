'''
city = bpy.context.scene.city

 dir(self)
['__dict__', '__doc__', '__module__', '__weakref__', 'action', 'bl_description', 'bl_idname', 'bl_label', 'bl_options',
'bl_rna', 'cancel', 'check', 'draw', 'execute', 'has_reports', 'invoke', 'layout', 'modal', 'name', 'order', 'poll', 'pr
operties', 'report', 'rna_type'] 

layers = 20*[False]
layers[0] = True
bpy.ops.mesh.primitive_cube_add(view_align=False, enter_editmode=False, location=(-0.364221, 6.65412, 6.06772), rotation=(0, 0, 0), layers=layers )
bpy.ops.object.modifier_add(type='CAST')
bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Cast')

'''
import bpy
import blf
import copy
#from copy import deepcopy
import mathutils
from mathutils import *
import collections
debug = False
# class_import is responsible for loading the builders classes and guis from the builder folder
# this id done now before the city main class to register
# in order to give pointers towards builders to the main class
from blended_cities.bin.ui import *
from blended_cities.bin.class_import import *

# should be somewhere else
def dprint(str,level=1) :
    city = bpy.context.scene.city
    if level <= city.debuglevel :
        print(str)


# ######################################
# MAIN CITY CLASS bpy.context.scene.city
# ######################################

class BlendedCities(bpy.types.PropertyGroup) :
    elements = bpy.props.CollectionProperty(type=BC_elements)
    outlines = bpy.props.CollectionProperty(type=BC_outlines)
    builders = bpy.props.PointerProperty(type=BC_builders)
    tagitems = ( ('buildings','building lot','a building lot'),('child','child','a child element') )
    tagmenu  = bpy.props.EnumProperty( items = tagitems,  default = 'buildings', name = "Tag",  description = "" )
    debuglevel = bpy.props.IntProperty(default=1)
    builders_info = {} # should be a collection

    go = bpy.props.BoolProperty()
    go_once = bpy.props.BoolProperty()

    def elementNew(self,elm, outlineOb=False,outlineName='outlines') :
        # a class name is given :
        if type(elm) == str :
            elementClassName=elm.split('.')[0]
            elementName=elm
            isChild = False
        # or a parent element is given (when creating child elements):
        else :
            elementClassName=elm.className()
            elementName=elm.nameMain()
            otl_dad = elm.peer()
            outlineName=otl_dad.nameMain()
            isChild = True
            print('dad : %s %s'%(otl_dad,otl_dad.name))
        print('class : %s'%(elementClassName))

        print('ischild : %s'%(isChild))
        # check if the class exist
        try : elmclass = eval('bpy.context.scene.city.builders.%s'%elementClassName)
        except :
            print('class %s not found.'%elementClassName)
            return False, False

        city = bpy.context.scene.city

        # create a new outline as element 
        otl_elm = city.elements.add()
        otl_elm.nameNew(outlineName)
        otl_elm.type = 'outlines'
        if outlineOb : otl_elm.pointer = str(outlineOb.as_pointer())
        else : otl_elm.pointer = '-1'  # todo : spawn a primitive of the elm class

        # a new outline in its class
        otl = city.outlines.add()
        otl.name = otl_elm.name
        otl.type = elementClassName
        if otl_elm.pointer != '-1' :
            otl.dataRead()
        elif isChild :
            # otl.data['perimeters'].extend(otl_dad.data['perimeters']) # pointer...
            #otl.data = otl_dad.data.copy() # pointer...
            #otl.data['perimeters'] = [0,0,0]
            #otl.data = deepupdate(otl.data,otl_dad.data)
            otl.data = otl_dad.data

        # the new object as element
        new_elm = city.elements.add()
        new_elm.nameNew(elementName)
        new_elm.type = elementClassName

        # and in its class
        new  = elmclass.add()
        new.name  = new_elm.name

        # link the new elm and the new outline
        new.attached  = otl.name
        otl.attached = new.name

        # link parent and child
        if isChild :
            otl.parent = otl_dad.name
            otl_dad.childAdd(otl.name)
            print('parented to %s'%(otl.parent))

        # don't build if child element, a specific func
        # will handle that, depending on other factors
        else :
            new.build()

        return new, otl

    # modal. called from watchdog addon
    def modalBuilder(self,self_mdl,context,event) :
            print('modal')
            city = bpy.context.scene.city
            if bpy.context.mode == 'OBJECT' and \
            len(bpy.context.selected_objects) == 1 and \
            type(bpy.context.active_object.data) == bpy.types.Mesh :
                elm = city.elementGet(bpy.context.active_object)
                if elm.className() == 'buildings' or elm.peer().className() == 'buildings' :
                    print('rebuild0')
                    if elm.className() == 'buildings' :
                        blg = elm
                    else :
                        blg = elm.peer()
                    print('rebuild')
                    blg.build(True)
            '''
            if event.type in ['TAB','SPACE'] :
                self.go_once = True

            if event.type in ['G','S','R'] :
                self.go=False
                
                if bpy.context.mode == 'OBJECT' and \
                len(bpy.context.selected_objects) == 1 and \
                type(bpy.context.active_object.data) == bpy.types.Mesh :
                    elm = city.elementGet(bpy.context.active_object)
                    if elm : self.go=True

            elif event.type in ['ESC','LEFTMOUSE','RIGHTMOUSE'] :
                    self.go=False
                    self.go_once=False
                    #print('modal paused.')
                    #mdl.log = 'paused.'
                    #context.region.callback_remove(self._handle)

            if event.type == 'TIMER' and (self.go or self.go_once) :
                        #self_mdl.log = 'updating...'

                        #print('event %s'%(event.type))
                        elm = city.elementGet(bpy.context.active_object)
                        #print('modal acting')

                        if elm.className() == 'buildings' or elm.peer().className() == 'buildings' :
                            if elm.className() == 'buildings' :
                                blg = elm
                            else :
                                blg = elm.peer()
                            print('rebuild')
                            blg.build(True)
            #bpy.ops.object.select_name(name=self.name)
                        self.go_once = False
                        #if self.go == False : mdl.log = 'paused.'
            '''
    # given an object or its name, returns a city element (from its class)
    # false if not found
    def elementGet(self,ob) :
        if type(ob) == str :
            ob = bpy.data.objects[ob]
        pointer = str(ob.as_pointer())
        for elm in self.elements :
            if elm.pointer == pointer :
                return elm.inClass()
        return False



class OP_BC_buildingParts(bpy.types.Operator) :
    
    bl_idname = 'buildings.part'
    bl_label = 'add a part'
    
    action = bpy.props.StringProperty()
    
    def execute(self, context) :
        city = bpy.context.scene.city
        # selected object lookup
        elm = city.elementGet(bpy.context.active_object)
        if elm.className() == 'outlines' :
            otl_parent = elm
            blg_parent = elm.peer()
        else :
            otl_parent = elm.peer()
            blg_parent = elm
        blg_name = blg_parent.nameMain()
        otl_name = otl_parent.nameMain()

        print('build : %s outl : %s'%(blg_name,otl_name))

        if self.action == 'add above' :
            blg_child, otl_child = city.elementNew(blg_parent)
            print( otl_child.name)
            print( otl_child.data)
 
            data = otl_child.dataGet()
            z = max(zcoords(data['perimeters']))
            z += blg_parent.height()
            print('height %s'%z)
            for perimeter in data['perimeters'] :
                for vert in perimeter :
                    vert[2] = z
            otl_child.dataSet(data)
            otl_child.dataWrite()
            print('changed height.')

            blg_child.inherit = True
            blg_child.build()
            blg_child.select()

            
        return {'FINISHED'}
        
    
class OP_BC_tag(bpy.types.Operator) :
    
    bl_idname = 'perimeter.tag'
    bl_label = 'tag add/remove'
    
    action = bpy.props.StringProperty()
    
    def execute(self, context) :
        city = bpy.context.scene.city
        outlineOb = bpy.context.active_object
        if self.action != '' :
            act,tag = self.action.split(' ')
            if act == 'add' :
                print(tag,outlineOb.name)
                new, otl = city.elementNew(tag,outlineOb)
                new.select()

                print('attached %s to outline %s (ob current name : %s)'%(new.name,otl.name,new.objectName() ))
        #else :
        #    city.building.remove(outlineOb['citytag_id'])
        #    del outlineOb['citytag']
        #    del outlineOb['citytag_id']
                        
        return {'FINISHED'}


class OP_BC_buildinglist(bpy.types.Operator) :
   
    bl_idname = 'buildings.list'
    bl_label = 'list building in console'
    
    def execute(self,context) :
        print('buildings list :')
        for bi,b in enumerate(bpy.context.scene.city.builders.buildings) :
            if b.parent == '' :
                print(' %s %s / %s'%(bi,b.name,b.attached)) 
        return {'FINISHED'}


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


class OP_BC_buildingBuild(bpy.types.Operator) :
   
    bl_idname = 'buildings.build'
    bl_label = 'rebuild all'
    
    removetag = bpy.props.BoolProperty()
    
    def execute(self,context) :
        buildings = bpy.context.scene.city.builders.buildings
        for b in buildings :
            buildBox(b)
        return {'FINISHED'}


#class OP_BC_floors(bpy.types.Operator) :
#    
#   bl_idname = 'building.floor_number'
#    bl_label = 'modify floor number - modal'
def init() :
    scene = bpy.context.scene
    city = scene.city
    while len(city.elements) > 0 :
        city.elements.remove(0)
    while len(city.builders.buildings) > 0 :
        city.builders.buildings.remove(0)
    while len(city.outlines) > 0 :
        city.outlines.remove(0)
    #bpy.context.scene.modal.status = True
    #bpy.ops.wm.modal_timer_operator()
    mdl = bpy.context.window_manager.modal
    mdl.func = 'bpy.context.scene.city.modalBuilder(self,context,event)'


# register_class() for BC_builders and builders classes are made before
# the BlendedCities definition class_import
# else every module is register here



def register() :
    # operators
    bpy.utils.register_class(OP_BC_tag)
    bpy.utils.register_class(OP_BC_buildinglist)
    bpy.utils.register_class(OP_BC_buildingBuild)
    bpy.utils.register_class(OP_BC_buildingWipe)
    bpy.utils.register_class(OP_BC_buildingParts)
    # ui
    bpy.utils.register_class(OP_BC_Selector)
    bpy.utils.register_class(BC_main_panel)
    bpy.utils.register_class(BC_outlines_panel)
    # class_main
    bpy.utils.register_class(BC_outlines)
    bpy.utils.register_class(BC_elements)
    bpy.utils.register_class(BlendedCities)
    bpy.types.Scene.city = bpy.props.PointerProperty(type=BlendedCities)
    init()

def unregister() :
    # operators
    bpy.utils.unregister_class(OP_BC_tag)
    bpy.utils.unregister_class(OP_BC_buildinglist)
    bpy.utils.unregister_class(OP_BC_buildingBuild)
    bpy.utils.unregister_class(OP_BC_buildingWipe)
    bpy.utils.unregister_class(OP_BC_buildingParts)
    # ui
    bpy.utils.unregister_class(OP_BC_Selector)
    bpy.utils.unregister_class(BC_main_panel)
    bpy.utils.unregister_class(BC_outlines_panel)
    # builders classes unregister_class loop here
    bpy.utils.unregister_class(BC_buildings)   
    bpy.utils.unregister_class(BC_buildings_panel)   
    # class main + the builders class
    bpy.utils.unregister_class(BC_builders)
    bpy.utils.unregister_class(BC_outlines)
    bpy.utils.unregister_class(BC_elements)
    bpy.utils.unregister_class(BlendedCities)
    del bpy.types.Scene.city

if __name__ == "__main__" :
    print('B.C. wip')
    register()