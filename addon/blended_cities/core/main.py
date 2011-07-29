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


import sys
import copy
import collections

import bpy
import blf
import mathutils
from mathutils import *

#from blended_cities.core.ui import *
#from blended_cities.core.class_import import *
from blended_cities.core.class_main import *
from blended_cities import BC_builders
from blended_cities.utils.meshes_io import *


## should be the system from script events with logger popup etc.
def dprint(str,level=1) :
    city = bpy.context.scene.city
    if level <= city.debuglevel :
        print(str)


## return the active builder classes in a list
def builderClass() :
    scene = bpy.context.scene
    city = scene.city
    buildersList = []
    for k in city.builders.keys() :
        if type(city.builders[k]) == list :
            dprint('found builder %s'%(k),2)
            builderCollection = eval('city.builders.%s'%k)
            buildersList.append(builderCollection)
    return buildersList


## bpy.context.scene.city
# main class, main methods. holds all the pointers to element collections
class BlendedCities(bpy.types.PropertyGroup) :
    elements = bpy.props.CollectionProperty(type=BC_elements)
    outlines = bpy.props.CollectionProperty(type=BC_outlines)
    builders = bpy.props.PointerProperty(type=BC_builders)
    debuglevel = bpy.props.IntProperty(default=1)
    builders_info = {} # info about builder authoring, should be a collection too. usage, could use bl_info..

    bc_go = bpy.props.BoolProperty()
    bc_go_once = bpy.props.BoolProperty()


    ## create a new element
    # @return elm, otl (the new element in its class, and its outline)
    def elementAdd(self,elm, outlineOb=False,outlineName='outlines') :
        dprint('** element add')
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
            dprint('dad : %s %s'%(otl_dad,otl_dad.name))
        dprint('class : %s'%(elementClassName))

        dprint('ischild : %s'%(isChild))
        # check if the class exist
        try : elmclass = eval('bpy.context.scene.city.builders.%s'%elementClassName)
        except :
            dprint('class %s not found.'%elementClassName)
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
            dprint('parented to %s'%(otl.parent))
        else :
            new.build()
        dprint('* element add done')
        return new, otl


    ## remove an existing element given an object or an element of any kind
    # will only let the outline object
    def elementRemove(self,object=False) :
        dprint('** element Remove')
        dprint(object,type(object))
        if object :
            blr, otl = self.elementGet(object)
            if blr :
                dprint('removing..')
                # remove the outline, checks if there's childs/parent before
                iblr = blr.index()
                blrclass = blr.elementClass()
                iotl = otl.index()
                otlname = otl.name
                parent = otl.parent
                childs = otl.childsGet()
                for child in childs :
                    self.outlines[child].parent = parent
                if parent != '' :
                    self.outlines[parent].childsRemove(otlname)
                    for child in childs :
                        self.outlines[parent].childsAdd(child)
                    self.outlines[parent].asBuilder().build(True) # this will update the childs outlines
                # remove the attached builder object
                blr.objectDelete()
                # we keep main outlines, but not their childs
                if parent != '' : otl.objectDelete()

                # remove elements from collections.
                ielm  = otl.asElement().index()
                self.elements.remove(ielm)
                self.outlines.remove(iotl)
                ielm  = blr.asElement().index()
                self.elements.remove(ielm)
                blrclass.remove(iblr)
        dprint('** element Remove done')

    def objectsRemove(self,what='all',tag=False) :
         for otl in self.outlines :
            if otl.parent : continue
            print(otl.asBuilder().name)
            childsIter(otl,'    ')       
        
        
        
    ## given an object or its name, returns the builder and the outline
    # @return [ elm, otl ] (the new element in its class, and its outline). [False,False] if does not exists
    def elementGet(self,ob) :
        # given an object or its name, returns a city element (in its class)
        if type(ob) == str :
            try : ob = bpy.data.objects[ob]
            except :
                dprint('object with name %s not found'%ob)
                return [None,None]
        pointer = str(ob.as_pointer())
        for elm in self.elements :
            if elm.pointer == pointer :
                return [elm.asBuilder(),elm.asOutline()]
        return [False,False]


    ## modal configuration of script events
    def modalConfig(self) :
        mdl = bpy.context.window_manager.modal
        mdl.func = 'bpy.context.scene.city.modal(self,context,event)'


    ## the HUD function called from script events (TO DO)
    def hud() :
        pass

    ## the modal function called from script events (TO DO)
    def modal(self,self_mdl,context,event) :
            dprint('modal')
            city = bpy.context.scene.city
            if bpy.context.mode == 'OBJECT' and \
            len(bpy.context.selected_objects) == 1 and \
            type(bpy.context.active_object.data) == bpy.types.Mesh :
                elm,otl = city.elementGet(bpy.context.active_object)
                if elm : elm.build(True)
            '''
                if elm.className() == 'buildings' or elm.peer().className() == 'buildings' :
                    dprint('rebuild')
                    if elm.className() == 'buildings' :
                        blg = elm
                    else :
                        blg = elm.peer()
                    dprint('rebuild')
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
                    #dprint('modal paused.')
                    #mdl.log = 'paused.'
                    #context.region.callback_remove(self._handle)

            if event.type == 'TIMER' and (self.go or self.go_once) :
                        #self_mdl.log = 'updating...'

                        #dprint('event %s'%(event.type))
                        elm = city.elementGet(bpy.context.active_object)
                        #dprint('modal acting')

                        if elm.className() == 'buildings' or elm.peer().className() == 'buildings' :
                            if elm.className() == 'buildings' :
                                blg = elm
                            else :
                                blg = elm.peer()
                            dprint('rebuild')
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
        # clean elements collections
        while len(city.elements) > 0 :
            city.elements.remove(0)
        while len(city.outlines) > 0 :
            city.outlines.remove(0)
        for buildclass in builderClass() :
            while len(buildclass) > 0 :
                buildclass.remove(0)

        # define default value
        city.modalConfig()
        scene.unit_settings.system = 'METRIC'


    ## rebuild everything from the collections (TO COMPLETE)
    # should support criterias filters etc like list should also
    def build(self,what='all') :
        dprint('\n** BUILD ALL\n')
        #scene = bpy.context.scene
        #city = scene.city
        for buildclass in builderClass() :
            for elm in buildclass :
                dprint(elm.name)
                elm.build()

    ## list all or some collection, filters, etc.., show parented element
    # should be able to generate a selection of elm in the ui,
    # in a search panel (TO COMPLETE)
    def list(self,what='all') :
        
        print('buildings list :')
        print('----------------')

        def childsIter(otl,tab) :
            elm = otl.Child()
            while elm :
                print('%s%s'%(tab,elm.asBuilder().name))
                childsIter(elm,tab + '    ')
                elm = elm.Next()

        for otl in self.outlines :
            if otl.parent : continue
            print(otl.asBuilder().name)
            childsIter(otl,'    ')


# register_class() for BC_builders and builders classes are made before
# the BlendedCities definition class_import
# else every module is register here
def register() :
    # operators
    pass

def unregister() :
    pass
if __name__ == "__main__" :
    dprint('B.C. wip')
    register()