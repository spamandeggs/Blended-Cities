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
from blended_cities.utils import library
from blended_cities.utils.geo import *
from blended_cities.core.common import *

##\brief the main city elements collection
#
# store any element of the city, including outlines. allows 'real' object / element lookups
# @param name used internally as key for parenting and element lookup ! shouldn't be modified !
# @param type used for lookup between the element as element and the same element as builder or outline. I don't think it's useful anymore, since the name gives the info about the class of the element.
# @param pointer is the pointer to the real object. set to -1 if the object is missing. i fact it correspond to the obj.as_pointer() function. it allows to change the name of the real object without breaking the relation-ship between the element and the object.
class BC_elements(bpy.types.PropertyGroup) :
    bc_label = 'Element'
    bc_description = 'any city object'
    bc_collection = 'elements'
    bc_element = 'element'

    name  = bpy.props.StringProperty()
    collection  = bpy.props.StringProperty()
    pointer = bpy.props.StringProperty(default='-1')

    ###############################
    ## LOOKUPS METHODS
    ###############################

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
        #return self.__class__.__name__[3:]
        return self.bc_collection


    ## returns the class of the element itself. 
    def elementClass(self) :
        city = bpy.context.scene.city
        clname = self.className()
        if clname == 'elements' : clname = self.collection
        if clname == 'outlines' :
            return eval('city.%s'%clname)
        else :
            #builder = self.name.split('.')[0]
            return eval('city.builders.%s'%clname)


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


    ## from an element, returns the object or the list of objects
    def object(self) :
        elm = self.asElement()
        if elm.pointer == '-1' : return False
        elif elm.pointer in bpy.data.groups :
            return bpy.data.groups[elm.pointer].objects
        else :
            test = int(elm.pointer)
            for ob in bpy.context.scene.objects :
                if ob.as_pointer() == int(elm.pointer) :
                    return ob
            return False


    ## from an element, returns the object name / the object names in a list
    def objectName(self) :
        ob = self.object()
        if ob :
            if type(ob) == bpy.types.Object : return ob.name
            return ob.keys()
        else : return False


    ## change the object and the mesh names of the element object to the element name 
    # @return new name as string if done, else False (object missing or a group of objects is attached, not a single object)
    def objectNameSet(self,name=False) :
        ob = self.object()
        if name == False : name = self.name
        if ob : 
            if type(ob) == bpy.types.Object :
                ob.name = name
                ob.data.name = name
                return name
            return False
        else : return False


    ## name a new element in the element class.
    def nameNew(self,tag=False,id=0) :
        if tag == False :
             tag = self.bc_element
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


    ## rename an outline, rewrite relationships, update element
    # not sure that's a good idea.. though it could be used by elementRemove(), wait and see
    #def rename(self,name) :
    #    city = bpy.context.scene.city
    #    oldname = self.name
    #    self.name = name
    #    if self.parent != '' :
    #        city.outlines[self.parent].childRemove(oldname)
    #        city.outlines[self.parent].childsAddName(name)
    #    for child in self.childslist() :
    #        city.outlines[child].parent = name
    #    self.asElement().name = name



    ## returns the first child or None
    # @param id 0 (default) the child index -1 for last. id > len(childs) error free : returns last child
    # @param attached False (default) returns the outline parent. True returns the builder attached
    # @return the element or None
    def Child(self,id=0,attached=False) :
        outlines = bpy.context.scene.city.outlines
        childs = self.childsGet()
        if len(childs) > 0 :
            if id + 1 > len(childs) : id = -1
            if attached : return outlines[childs[id]].peer()
            return outlines[childs[id]]
        return None


    ## returns the parent element
    # @param attached False (default) returns the outline parent. True returns the builder attached
    # @return the element or None
    def Parent(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        self = self.asOutline()
        if self.parent :
            if attached : return outlines[self.parent].peer()
            return outlines[self.parent]
        return None


    ## returns the next sibling
    # @param attached False (default) returns the outline parent. True returns the builder attached
    # @return the element or None
    def Next(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        if self.asOutline().parent :
            siblings = self.Parent().childsGet()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                try : sibling = outlines[siblings[si+1]]
                except : return None
                return sibling.peer() if attached else sibling
        return None


    ## returns the previous sibling
    # @param attached False (default) returns the outline parent. True returns the builder attached
    # @return the element or None
    def Previous(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        if self.asOutline().parent :
            siblings = self.Parent().childsGet()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                if si > 0 : sibling = outlines[siblings[si-1]]
                else : return None
                return sibling.peer() if attached else sibling
        return None


    ## from an element, returns and select the object
    def select(self,attached=False) :
        #print('select %s %s %s'%(self.name,self.className(),attached))
        if attached :
            ob = self.peer().object()
        else :
            ob = self.object()
        if ob :
            bpy.ops.object.select_all(action='DESELECT')
            if type(ob) == bpy.types.Object : ob = [ob]
            for o in ob :
                o.select = True
            bpy.context.scene.objects.active = o
        else : return False


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


    ## selects the first child object of the current element
    # @param attached (default False) if True returns always the builder object and not the outline
    def selectChild(self,attached=False) :
        child = self.Child()
        if child : child.select(attached)


    ## selects the next sibling object of the current element
    # @param attached (default False) if True returns always the builder object and not the outline
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


    ## selects the previous sibling object of the current element
    # @param attached (default False) if True returns always the builder object and not the outline
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


    ## add a child outline reference to this outline.
    # @param childname the outline name (string)
    def childsAddName(self,childname) :
        self = self.asOutline()
        if self.childs == '' :
            self.childs = childname
        elif childname not in self.childs :
            self.childs += ',%s'%childname


    ## delete a child outline reference of this outline.
    # @param childname the outline name (string)
    def childsRemoveName(self,childname) :
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


    ###############################
    ## OUTLINES / BUILDERS OPERATION
    ###############################

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


    ## move a builder to another outline by moving the outline pointer to another object  
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
            otl_elm = self.asOutline().asElement()
            if otl_elm.pointer != '-1' :
                otl_elm.objectDetach()
            otl_elm.pointer = str(object.as_pointer())
            otl_elm.asOutline().dataRead()
            #otl_elm.asBuilder().build()
            city.builders.build(otl_elm.asBuilder())
            return True
        else :
            print('object %s already attached (%s)'%(object.name,test[0].name))
        return False


    ## Delete the generated object(s) of a builder
    def objectRemove(self,del_objs='all') :
        city = bpy.context.scene.city
        self = self.asBuilder().asElement()
        if self.pointer in bpy.data.groups :
            objs = bpy.data.groups[self.pointer].objects
        elif self.pointer != '-1' :
            objs = [ self.object() ]
        else : return

        for ob in  objs :
            if del_objs == 'all' or ob in del_objs :
                print('  removing %s'%ob.name)
                bld, otl = city.elementGet(ob)
                if bld :
                    print('  removing %s (ob as element)'%bld.name)
                    bld._rem()
                wipeOutObject(ob)

        if len(bpy.data.groups[self.pointer].objects) == 0 :
            bpy.data.groups.remove(bpy.data.groups[self.pointer])
            self.pointer = '-1'


    ## add an object(s) to a builder
    def objectAdd(self,ob) :
        city = bpy.context.scene.city
        self = self.asElement()
        otl = self.asOutline()
        bld = self.asBuilder()
        ob = returnObject(ob)

        # check if the new object already exists in collection as a builder
        # if not defined, add it in the objects collection
        elm = city.elementGet(ob,inclass=False)
        if elm == False :
            elm = city.builders.objects.add()
            #elm.nameNew(ob.name)
            elm.name = ob.name # named by the library module
            elm._add()
            elm.asElement().pointer = str(ob.as_pointer())
            elm.attached = otl.name
            print('  added %s in object'%(elm.name))

        # update the element.pointer prop
        if self.pointer in bpy.data.groups :
            objs =  bpy.data.groups[self.pointer].objects
            if ob not in objs.values() :
                objs.link(ob)
            grobs=objs.keys()
        elif self.pointer != '-1' :
            ob0 = self.object()
            if ob != ob0 :
                gr = bpy.data.groups.new(bld.name)
                objs = gr.objects
                #if ob0 not in objs.values() :
                objs.link(ob0)
                #if ob not in objs.values() :
                objs.link(ob)
                self.pointer = gr.name
                grobs=objs.keys()
            else : grobs=self.objectName()
        else :
            self.pointer = str(ob.as_pointer())
            #bpy.data.groups.new(bld.name)
            grobs=self.objectName()
        print('***********POINTER :\n %s\n %s\n %s'%(self.pointer,grobs,ob.name))

        # parent the object
        ob.parent = otl.object()

    ## add a new elm in Elements, used when creating a new otl or bld. its name is the caller name
    # @return the new element in Elements 
    def _add(self) :
        if self.className() != 'elements' :
            elm = bpy.context.scene.city.elements.add()
            elm.name = self.name
            elm.collection = self.className()
            return elm
        print('not done %s'%self)


    ## remove an elm from Elements and its class. does not care about anything else (relationship, objects..)
    def _rem(self) :
        iclass = self.index()
        selfclass = self.elementClass()
        ielm  = self.asElement().index()
        bpy.context.scene.city.elements.remove(ielm)
        selfclass.remove(iclass)

     ## remove the element and its generated object
    # cares about relationship
    # @param del_object (default True) delete the attached object
    def remove(self,del_object=True) :
        city = bpy.context.scene.city
        otl = self.asOutline()
        bld = self.asBuilder()
        if del_object : bld.objectRemove()
        # rebuild relationship
        parent = otl.parent
        childs = otl.childsGet()
        for child in childs :
            city.outlines[child].parent = parent
        if parent != '' :
            otl.Parent().childsRemoveName(otl.name)
            for child in childs :
                otl.Parent().childsAddName(child)
            #otl.Parent().asBuilder().build(True) # this to update the childs
            city.builders.build(otl.Parent().asBuilder()) 
        # remove elements from collections.
        otl._rem()
        bld._rem()

    ## stack an element above this one
    # @param what default False : outline of the new elm does not exist yet
    # @param builder (default 'same') the builderclass name of the new element. if not given, stack the same builder than the current element.
    def stack(self,what=False,builder='same') :
        city = bpy.context.scene.city
        bld_child, otl_child = self.childsAdd(what,builder) 

        data = otl_child.dataGet('perimeters')
        z = max(zcoords(data))
        if bld_child :
            z += bld_child.Parent(True).height()

        for perimeter in data :
            for vert in perimeter :
                vert[2] = z

        otl_child.dataSet(data)
        otl_child.dataWrite()
        otl_child.object().parent = otl_child.Parent().object()

        if bld_child :
            bld_child.inherit = True
            # bld_child.build()
            city.builders.build(bld_child)
            #bld_child.object().parent = otl_child.object()
        return bld_child, otl_child


    ## parent a new outline to the current one
    # @param builder (default 'same') the builderclass name of the new element. if not given, stack the same builder than the current element.
    def childsAdd(self,what=False,builder='same',build_it=False) :
        city = bpy.context.scene.city
        otl_parent = self.asOutline()
        bld_parent = self.asBuilder()
        if builder == 'same' : builder = bld_parent.className()

        # check if the given outline object is not already linked to smtg
        go = True
        if what :
            otl_exist, bld_exist = city.elementGet(what)
            if otl_exist :
                go = False
                print('otl %s already there, abort childadd'%otl_exist.name)
        if go :
            [ [bld_child, otl_child] ] = city.elementAdd(what,builder,build_it)
            otl_child.parent = otl_parent.name
            otl_parent.childsAddName(otl_child.name)

            if what :
                otl_child.object().parent = otl_parent.object()
            # if no outline object given, copy the data from the parent
            else :
                otl_child.data = otl_parent.data

            return bld_child, otl_child
        else : return False,False


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
    bc_label = 'Outline'
    bc_description = 'an outline object'
    bc_collection = 'outlines'
    bc_element = 'outline'
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
        #else : print('dataGet returns %s %s datas in B.U.'%(self.name,what))          
        data['matrix'] = Matrix(data['matrix'])
        if what == 'all' : return data
        return data[what]


    ## set or modify the geometry of an outline
    # @param what 'perimeters', 'lines', 'dots', 'matrix', or 'all' default is 'perimeters'
    # @param data a list with nested list of vertices or a complete dictionnary conaining the four keys
    def dataSet(self,data,what='perimeters',meters=True) :
        if what == 'all' : pdata = data
        else :
            pdata = self.dataGet('all',meters)
            pdata[what] = data
        if meters :
            print('dataSet received %s %s datas in meters :'%(self.name,what)) 
            pdata['perimeters'] = metersToBu(pdata['perimeters'])
            pdata['lines'] = metersToBu(pdata['lines'])
            pdata['dots'] = metersToBu(pdata['dots'])
        #else : print('dataSet received %s %s datas in BU :'%(self.name,what))
        self.data = '{ "perimeters": ' + str(pdata['perimeters']) + ', "lines":' + str(pdata['lines']) + ', "dots":' + str(pdata['dots']) + ', "matrix":' + matToString(pdata['matrix']) +'}'


    ## read the geometry of the outline object and sets its data (dataSet call)
    # @return False if object does not exists
    def dataRead(self) :
        print('dataRead outline object of %s'%self.name)
        obsource=self.object()
        if obsource :
            # data extracted are in BU no meter so dataSet boolean is False
            mat, perims, lines,dots = outlineRead(obsource)
            data = {'perimeters':perims, 'lines':lines, 'dots':dots, 'matrix':mat }
            self.dataSet(data,'all',False)
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
        data = self.dataGet('all')
        verts = []
        edges = []
        ofs = 0
        for perimeter in data['perimeters'] :
            verts.extend(perimeter)
            edges.extend( edgesLoop(ofs, len(perimeter)) )
            ofs += len(perimeter)
        for line in data['lines'] :
            verts.extend(line)
            edges.extend( edgesLoop(ofs, len(line),True) )
            ofs += len(line)
        for dot in data['dots'] :
            verts.append(dot)
        #print('>',verts,edges)
        #print(len(verts),len(edges))
        ob = objectBuild(self,verts,edges)
        self.asElement().pointer = str(ob.as_pointer())
        ob.matrix_local = Matrix()#data['matrix']
        print('dataWrite done')

## none collection
# used for cases when outilnes have no builder attached. its length gives the free outlines number and can list them
# the none elm of an otl is removed when otl is attached to a real builder
class BC_nones(BC_elements,bpy.types.PropertyGroup) :
    bc_label = 'Nones'
    bc_description = 'a null object. used to add a single outline'
    bc_collection = 'nones'
    bc_element = 'none'

    attached = bpy.props.StringProperty() # its attached outline
    group = bpy.props.StringProperty(default='') # name of a group if member

    def build(self,dummy) :
        return []
    def height(self) :
        return 0


## object collection
# used to store elements that come from the library, and that are used by a builder
class BC_objects(BC_elements,bpy.types.PropertyGroup) :
    bc_label = 'Objects'
    bc_description = 'a null object. used to add a single outline'
    bc_collection = 'objects'
    bc_element = 'obj'

    attached = bpy.props.StringProperty() # its attached outline
    group = bpy.props.StringProperty(default='') # name of a group if member

    def build(self,dummy) :
        return []
    def height(self) :
        return 0

bpy.utils.register_class(BC_nones)
bpy.utils.register_class(BC_objects)

##\brief the builder bpy pointer. builders are hooked there
# this will be populated with builder collections
# it handles the build() requests
class BC_builders(bpy.types.PropertyGroup):
    nones = bpy.props.CollectionProperty(type=BC_nones)
    objects = bpy.props.CollectionProperty(type=BC_objects)
    builders_list = bpy.props.StringProperty()

    def build(self,bld) :
        city = bpy.context.scene.city
        print('** build %s'%bld.name)
        otl = bld.asOutline()
        elm = bld.asElement()
        # when the builder has several attached object to it, remove them all before
        # else the single generated object will be reused or created
        #if bld.asElement().pointer not in bpy.data.groups :
        #    bld.objectRemove()
        objs = bld.build(True)
        print('  received %s objects :'%len(objs))
        if len(objs) > 0 :
            generated=[]
            # build returned objects
            for idx,ob in enumerate(objs) :
                obname = '%s.%1.3d'%(bld.name,idx)
                print('    %s'%obname)
                # a generated mesh
                if type(ob[0]) == list :
                    verts, edges, faces, matslots, mats = ob
                    ob = objectBuild(obname, verts, edges, faces, matslots, mats)
                    ob.name = obname
                    objectLock(ob)
                    bld.objectAdd(ob)
                # a generated outline
                elif type(ob[0]) == str and ob[0] == 'outline' :
                    dummy, verts, edges, faces, matslots, mats = ob
                    ob = objectBuild(obname, verts, edges, faces, matslots, mats)
                    bld_child, otl_child = otl.childsAdd(ob,'nones')
                    bld.objectAdd(ob)
                # an object from the library
                elif type(ob[0]) == str :
                    request, coord = ob
                    ob = library.objectAppend(otl, request, coord)
                    ob.name = obname
                    objectLock(ob)
                    bld.objectAdd(ob)
                generated.append(ob)

            # remove previous generated and non updated objects from scene and collections
            if elm.pointer in bpy.data.groups :
                objs = bpy.data.groups[elm.pointer].objects
            elif elm.pointer != '-1' :
                objs = [ elm.object() ]
            print('** removing ? %s %s'%(len(objs), len(generated)))
            if len(objs) != len(generated) :
                for ob in objs :
                    if ob not in generated :
                        bld.objectRemove([ob])

            # childs update
            if hasattr(bld,'height') :
                data = otl.dataGet('all')
                perimeter = data['perimeters']
                lines = data['lines']
                zlist = zcoords(perimeter+lines)
                height = bld.height() + max(zlist)
                updateChildHeight(otl,height)
        print('** end build %s'%bld.name)
# for reference
#BC_builders = type("BC_builders", (bpy.types.PropertyGroup, ), {})