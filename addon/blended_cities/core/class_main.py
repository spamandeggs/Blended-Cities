##\file
# class_main.py
# contains the main collection classes :
# the elements class that stores every city element
# the outlines class that store each outline element
# methods used by builders classes are also inherited from here
print('class_main.py')
import bpy
import mathutils
from mathutils import *
from blended_cities.utils.meshes_io import *

##\brief the main city elements collection
#
# store any element of the city, including outlines. allows 'real' object / element lookups
# @param name used internally as key for parenting and element lookup ! shouldn't be modified !
# @param type used for lookup between the element as element and the same element as builder or outline. I don't think it's useful anymore, since the name gives the info about the class of the element.
# @param pointer is the pointer to the real object. set to -1 if the object is missing. i fact it correspond to the obj.as_pointer() function. it allows to change the name of the real object without breaking the relation-ship between the element and the object.
class BC_elements(bpy.types.PropertyGroup) :
    name  = bpy.props.StringProperty()
    type  = bpy.props.StringProperty()
    pointer = bpy.props.StringProperty(default='-1')
    
    ## given the element name, returns its id in its collection
    #
    # warning : indexes of the same element in elements, in outlines, or in builders can differs, so be sure of the className() of the element.
    def index(self) :
        return int(self.path_from_id().split('[')[1].split(']')[0])

    ## given any kind of element, returns it as member of the main elements collection
    def asElement(self) :
        return bpy.context.scene.city.elements[self.name]

    ## given any kind of element, returns the outline of it
    def asOutline(self) :
        city = bpy.context.scene.city
        self = self.asElement()
        elmclass = self.elementClass()
        self = elmclass[self.name]
        if self.className() != 'outlines' : return self.peer()
        else : return self

    ## given any kind of element, returns the element in its builder class
    def asBuilder(self) :
        city = bpy.context.scene.city
        elmclass = self.elementClass()
        self = elmclass[self.name]
        if self.className() == 'outlines' : return self.peer()
        else : return self

    ## returns the class of the element as string : 'elements', 'outlines', or builder name
    def className(self) :
        return self.__class__.__name__[3:]

    ## returns the class of the element itself. 
    # ! resolved by its name, get rid of type
    def elementClass(self) :
        city = bpy.context.scene.city
        if 'outlines' in self.name  : return eval('city.outlines')
        else :
            builder = self.name.split('.')[0]
            return eval('city.builders.%s'%builder)

    ## returns the outline if the element is a builder or an Element, returns the builder if the element is an outline
    def peer(self) :
        city = bpy.context.scene.city
        if self.className() == 'elements' :
            elmclass = self.elementClass()
            self = elmclass[self.name]
        if self.className() == 'outlines' : 
            self = city.elements[self.attached]
            elmclass = self.elementClass()
            return elmclass[self.name]
        else :
            self = city.elements[self.attached]
            return city.outlines[self.name]

    ## from an element, returns and select the object
    def select(self,attached=False) :
        #print('select %s %s %s'%(self.name,self.className(),attached))
        if attached :
            ob = self.peer().object()
        else :
            ob = self.object()
        if ob :
            bpy.ops.object.select_all(action='DESELECT')
            ob.select = True
            bpy.context.scene.objects.active = ob
        else : return False

    ## from an element, returns the object
    def object(self) :
        elm = bpy.context.scene.city.elements[self.name]
        if elm.pointer == '-1' : return False
        for ob in bpy.context.scene.objects :
            if ob.as_pointer() == int(elm.pointer) :
                return ob
        else : return False

    ## detach the object of the element
    def objectDetach(self) :
        self = self.asElement()
        if self.pointer != '-1' :
            ob = self.object()
            if ob.name == self.name :
                ob.name = ob.name.split('.')[0] + '_free.' + ob.name.split('.')[1]
            ob.data.name = ob.name
            ob.parent = None
            self.pointer = '-1'

    ## attach an object to an outline element
    # @param object an object or its name
    # @return True if the object has been attached
    def objectAttach(self,object) :
        city = bpy.context.scene.city
        if type(object) == str :
            try : object = bpy.data.objects[object]
            except :
                dprint('object named %s not found'%object)
                return False
        test = city.elementGet(object)
        if  test == [False,False] :
            elm = self.asOutline().asElement()
            if elm.pointer != '-1' :
                elm.objectDetach()
            elm.pointer = str(object.as_pointer())
            elm.asOutline().dataRead()
            elm.asBuilder().build()
            return True
        else :
            print('object %s already attached (%s)'%(object.name,test[0].name))
        return False

    ## Delete the object of the element
    def objectDelete(self) :
        elm = elm.asElement()
        if elm.pointer != '-1' :
            ob = elm.object()
            wipeOutObject(ob)
            elm.pointer = '-1'

    ## from an element, returns the object name
    def objectName(self) :
        ob = self.object()
        if ob : return ob.name
        else : return False

    ## change the object and the mesh names of the element object to its own name (if the object exists)
    def objectNameSet(self,name=False) :
        ob = self.object()
        if name == False : name = self.name
        if ob : 
            ob.name = name
            ob.data.name = name
            return name
        else : return False

    ## name a new element in the element class.
    def nameNew(self,tag,id=0) :
        name = '%s.%1.5d'%(tag,id)
        while name in bpy.context.scene.city.elements :
            id += 1
            name = '%s.%1.5d'%(tag,id)
        self.name = name
        return name

    ## returns the name of the root element in a family of element
    # not sure about this one : should really the name of child elements have two numeric fields ?
    # internally almost useless.
    def nameMain(self) :
        n = self.name.split('.')
        if len(n) > 2 : 
            return n[0]+'.'+n[1]
        else :
            return self.name


    ## selects the parent object of the current element
    # @param attached (default False) if True returns always the builder object and not the outline
    def selectParent(self,attached=False) :
        if self.className() == 'elements' : self = self.asBuilder()
        if self.className() != 'outlines' :
            self = self.peer()
            attached = True
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            self = outlines[self.parent]
        self.select(attached)

    ## returns the first child or None
    def Child(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        childs = self.childsGet()
        if len(childs) > 0 :
            if attached : outlines[childs[0]].peer()
            return outlines[childs[0]]
        return None

    ## returns the next sibling
    def Next(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        if self.asOutline().parent :
            siblings = outlines[self.parent].childsGet()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                try : sibling = outlines[siblings[si+1]]
                except : return None
                if attached : return sibling.peer()
                else : return sibling
        return None

    def selectChild(self,attached=False) :
        child = self.Child()
        if child : child.select(attached)

    def selectNext(self,attached=False) :
        if self.className() == 'elements' : self = self.asBuilder()
        if self.className() != 'outlines' :
            self = self.peer()
            attached = True
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            siblings = outlines[self.parent].childsGet()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outlines[siblings[(si+1)%len(siblings)]]
                sibling.select(attached)


    def selectPrevious(self,attached=False) :
        if self.className() == 'elements' : self = self.asBuilder()
        if self.className() != 'outlines' :
            self = self.peer()
            attached = True
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            siblings = outlines[self.parent].childsGet()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outlines[siblings[(si-1)%len(siblings)]]
                sibling.select(attached)

    ## add a child outline to this outline. otl.childs helper
    # @param childname the outline name (string)
    def childsAdd(self,childname) :
        self = self.asOutline()
        if self.childs == '' :
            self.childs = childname
        elif childname not in self.childs :
            self.childs += ',%s'%childname

    ## delete a child outline of this outline. otl.childs helper
    # @param childname the outline name (string)
    def childsRemove(self,childname) :
        self = self.asOutline()
        print('removing %s from %s : %s'%(childname,self.name,self.childs))
        if childname in self.childs :
            childs = self.childsGet()
            del childs[childs.index(childname)]
            newchilds = ''
            for child in childs : newchilds += child+','
            self.childs = newchilds[:-1]
        print('child list now : %s'%self.childs)

    ## returns outlines parented to this one (its childs) and mentionned in otl.childs, but as a list and not a string
    # @return a list of string (outline names) or an empty list
    def childsGet(self) :
        self = self.asOutline()
        if self.childs == '' :
            return []
        else :
            return self.childs.split(',')

##\brief the outlines collection
#
# this collection stores retionship between elements, and the geometry data of the outline. an outline is always attached to a builder element, and reciproquely.
#
# @param type not sure it's useful anymore... 
# @param attached (string) the name of the builder object attached to it
# @param data (dictionnary as string)stores the geometry, outline oriented, of the outline object
# @param childs (list as string) store outlines parented to the outline element "child1,child2,.."
# @param parent  the parent outline name if any (else '')

class BC_outlines(BC_elements,bpy.types.PropertyGroup) :
    type   = bpy.props.StringProperty() # its tag
    attached = bpy.props.StringProperty() # its attached object name (the real mesh)
    data = bpy.props.StringProperty(default="{'perimeters':[], 'lines':[], 'dots':[], 'matrix':Matrix() }") # global. if the outline object is missing, create from this
    childs = bpy.props.StringProperty(default='')
    parent = bpy.props.StringProperty(default='')

    ## given an outline, retrieves its geometry in meters as a dictionnary from the otl.data string field :
    # @param what 'perimeters', 'lines', 'dots', 'matrix', or 'all' default is 'perimeters'
    # @return a nested lists of vertices, or the world matrix, or all fields in a dict.
    def dataGet(self,what='perimeters',meters=True) :
        data = eval(self.data)
        if meters :
            print('dataGet returns %s %s datas in Meters'%(self.name,what))
            data['perimeters'] = buToMeters(data['perimeters'])
            data['lines'] = buToMeters(data['lines'])
            data['dots'] = buToMeters(data['dots'])
        else : print('dataGet returns %s %s datas in B.U.'%(self.name,what))          
        data['matrix'] = Matrix(data['matrix'])
        if what == 'all' : return data
        return data[what]

    ## set or modify the geometry of an outline
    # @param what 'perimeters', 'lines', 'dots', 'matrix', or 'all' default is 'perimeters'
    # @param data a list with nested list of vertices or a complete dictionnary conaining the four keys
    def dataSet(self,data,what='perimeters',meters=True) :
        pdata = self.dataGet('all',meters)
        if what == 'all' : pdata = data
        pdata[what] = data
        if meters :
            print('dataSet received %s %s datas in meters :'%(self.name,what)) 
            pdata['perimeters'] = metersToBu(pdata['perimeters'])
            pdata['lines'] = metersToBu(pdata['lines'])
            pdata['dots'] = metersToBu(pdata['dots'])
        else :
            print('dataSet received %s %s datas in BU :'%(self.name,what))
        self.data = '{ "perimeters": ' + str(pdata['perimeters']) + ', "lines":' + str(pdata['lines']) + ', "dots":' + str(pdata['dots']) + ', "matrix":' + matToString(pdata['matrix']) +'}'

    ## read the geometry of the outline object and sets its data (dataSet call)
    # @return False if object does not exists
    def dataRead(self) :
        print('dataRead outline object of %s'%self.name)
        obsource=self.object()
        if obsource :
            # data extracted are in BU no meter so dataSet boolean is False
            mat, perim = outlineRead(obsource)
            self.dataSet(perim,'perimeters',False)
            self.dataSet(mat,'matrix',False)
            return True
        else :
            print('no object ! regenerate')
            self.dataWrite()
            print('done regenerate')
            return False
        print('dataReaddone')
    ## write the geometry in the outline object from its data field (dataGet call)
    # inputs and outputs are in meters
    def dataWrite(self) :
        print('dataWrite outline ob for %s'%self.name)
        data = self.dataGet()
        verts = []
        edges = []
        ofs = 0
        for perimeter in data :
            print('>',len(perimeter))
            for vi,v in enumerate(perimeter) :
                print(vi,v)
                verts.append(v)
                if vi < len(perimeter)-1 :
                    edges.append([ofs+vi,ofs+vi+1])
            edges.append([ofs+vi,ofs])
            ofs += len(perimeter)
        print('>',verts,edges)
        print(len(verts),len(edges))
        ob = objectBuild(self,verts,edges)
        ob.matrix_world = Matrix()
        print('dataWrite done')
        #self.asElement().pointer = str(ob.as_pointer())

    ## rename an outline, rewrite relationships, update element
    # not sure that's a good idea.. though it could be used by elementRemove(), wait and see
    def rename(self,name) :
        city = bpy.context.scene.city
        oldname = self.name
        self.name = name
        if self.parent != '' :
            city.outlines[self.parent].childRemove(oldname)
            city.outlines[self.parent].childsAdd(name)
        for child in self.childslist() :
            city.outlines[child].parent = name
        self.asElement().name = name