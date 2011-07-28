##@mainpage Blended Cities internal documentation
# v0.6 for Blender 2.5.8a
#
# this is the continuation of a project begun with 2.4x releases of blender :
#
# http://jerome.le.chat.free.fr/index.php/en/city-engine
#
# the version number starts after the last blended cities release for 2.49b \
# but this is tests stage for now (july 2011)

##@file
# main.py
# the main city class
# bpy.context.scene.city
# the file calls the other modules and holds the main city methods

# class_import is responsible for loading the builders classes and guis from the builder folder
# this id done now before the city main class to register
# in order to give pointers towards builders to the main class

#from blended_cities.core.ui import *
#from blended_cities.core.class_import import *
from blended_cities.core.class_main import *
from blended_cities import BC_builders
from blended_cities.utils.meshes_io import *
#buildersRegister()

import bpy
import blf
import sys
import copy
#from copy import deepcopy
import mathutils
from mathutils import *
import collections
debug = False


# should be somewhere else
def dprint(str,level=1) :
    city = bpy.context.scene.city
    if level <= city.debuglevel :
        print(str)


## bpy.context.scene.city
# main class, main methods. holds all the pointers to element collections
class BlendedCities(bpy.types.PropertyGroup) :
    elements = bpy.props.CollectionProperty(type=BC_elements)
    outlines = bpy.props.CollectionProperty(type=BC_outlines)
    builders = bpy.props.PointerProperty(type=BC_builders)
    #tagitems = ( ('buildings','building lot','a building lot'),('child','child','a child element') )
    #tagmenu  = bpy.props.EnumProperty( items = tagitems,  default = 'buildings', name = "Tag",  description = "" )
    debuglevel = bpy.props.IntProperty(default=1)
    builders_info = {} # should be a collection

    bc_go = bpy.props.BoolProperty()
    bc_go_once = bpy.props.BoolProperty()

    ## create a new element
    # @return elm, otl (the new element in its class, and its outline)
    def elementAdd(self,elm, outlineOb=False,outlineName='outlines') :
        print('** element add')
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
        # don't build if child element, the caller function will handle that, 
        # depending on other factors (object parenting ? build above existing ? deform outline ? etc)
        # it depends on the builder methods and where the caller want to locate the child 
        if isChild :
            otl.parent = otl_dad.name
            otl_dad.childsAdd(otl.name)
            print('parented to %s'%(otl.parent))
        else :
            new.build()
        print('* element add done')
        return new, otl

    ## remove an existing element given an object or an element of any kind
    # will only let the outline object
    def elementRemove(self,object=False) :
        print('** element Remove')
        print(object,type(object))
        if object :
            blr, otl = self.elementGet(object)
            if blr :
                print('removing..')
                # remove the outline, checks if there's childs/parent before
                iblr = blr.index()
                blrclass = blr.elementClass()
                iotl = otl.index()
                otlname = otl.name
                parent = otl.parent
                childs = otl.childsList()
                for child in childs :
                    self.outlines[child].parent = parent
                if parent != '' :
                    self.outlines[parent].childsRemove(otlname)
                    for child in childs :
                        self.outlines[parent].childsAdd(child)
                    self.outlines[parent].asBuilder().build(True) # this will update the childs outlines
                # remove the attached builder object
                wipeOutObject(object)
                # we keep main outlines, but not their childs
                if parent != '' : wipeOutObject(otl.object())

                # remove elements from collections.
                ielm  = otl.asElement().index()
                self.elements.remove(ielm)
                self.outlines.remove(iotl)
                ielm  = blr.asElement().index()
                self.elements.remove(ielm)
                blrclass.remove(iblr)
        print('** element Remove done')


    ## given an object or its name, returns a city element (in its class)
    # @return elm, otl (the new element in its class, and its outline). false if does not exists
    def elementGet(self,ob) :
        # given an object or its name, returns a city element (in its class)
        if type(ob) == str :
            try : ob = bpy.data.objects[ob]
            except :
                print('object with name %s not found'%ob)
                return False
        pointer = str(ob.as_pointer())
        for elm in self.elements :
            if elm.pointer == pointer :
                return [elm.asBuilder(),elm.asOutline()]
        return [False,False]


    def modalConfig(self) :
        mdl = bpy.context.window_manager.modal
        mdl.func = 'bpy.context.scene.city.modalBuilder(self,context,event)'

    # modal. called from watchdog addon
    def modalBuilder(self,self_mdl,context,event) :
            print('modal')
            city = bpy.context.scene.city
            if bpy.context.mode == 'OBJECT' and \
            len(bpy.context.selected_objects) == 1 and \
            type(bpy.context.active_object.data) == bpy.types.Mesh :
                elm,otl = city.elementGet(bpy.context.active_object)
                if elm : elm.build(True)
            '''
                if elm.className() == 'buildings' or elm.peer().className() == 'buildings' :
                    print('rebuild')
                    if elm.className() == 'buildings' :
                        blg = elm
                    else :
                        blg = elm.peer()
                    print('rebuild')
                    blg.build(True)

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

    ## clean everything, restore the defaults
    # configure also the modal (it won't if BC is enabled by default, for now must be started by hand with city.modalConfig() )
    def init(self) :
        scene = bpy.context.scene
        city = scene.city
        while len(city.elements) > 0 :
            city.elements.remove(0)
        while len(city.builders.buildings) > 0 :
            city.builders.buildings.remove(0)
        while len(city.outlines) > 0 :
            city.outlines.remove(0)
        bpy.context.scene.city.modalConfig()

        # scale
        bpy.context.scene.unit_settings.system = 'METRIC'
        
# register_class() for BC_builders and builders classes are made before
# the BlendedCities definition class_import
# else every module is register here



def register() :
    # operators
    pass

def unregister() :
    pass
if __name__ == "__main__" :
    print('B.C. wip')
    register()