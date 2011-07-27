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

# ########################################################
# set of generic update functions used in builders classes
# ########################################################

#
# this link to the build() method of the current class
def updateBuild(self,context='') :
    self.build(True)

##\brief the main city elements collection
#
# store any element of the city, including outlines. allows 'real' object / element lookups
# @param name used internally as key for parenting and element lookup ! shouldn't be modified !
# @param type used for lookup between the element as element and the same element as builder or outline. I don't think it's useful anymore, since the name gives the info about the class of the element.
# @param pointer is the pointer to the real object. set to -1 if the object is missing. i fact it correspond to the obj.as_pointer() function. it allows to change the name of the real object without breaking the relation-ship between the element and the object.
class BC_elements(bpy.types.PropertyGroup):
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

    ## from an element, returns the object name
    def objectName(self) :
        ob = self.object()
        if ob : return ob.name
        else : return False

    ## change the object and the mesh names of the element object to its own name (if the object exists)
    def objectNameSet(self) :
        ob = self.object()
        if ob : 
            ob.name = self.name
            ob.data.name = self.name
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

    def isChild(self) :
        return len(self.name.split('.')) > 2

    def parent(self) :
        pass

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
     
    def selectChild(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        childs = self.childsList()
        if len(childs) > 0 :
            child = outlines[childs[0]]
            child.select(attached)

    def selectNext(self,attached=False) :
        if self.className() == 'elements' : self = self.asBuilder()
        if self.className() != 'outlines' :
            self = self.peer()
            attached = True
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            siblings = outlines[self.parent].childsList()
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
            siblings = outlines[self.parent].childsList()
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
            childs = self.childsList()
            del childs[childs.index(childname)]
            newchilds = ''
            for child in childs : newchilds += child+','
            self.childs = newchilds[:-1]
        print('child list now : %s'%self.childs)

    ## returns outlines parented to this one (its childs) and mentionned in otl.childs, but as a list and not a string
    # @return a list of string (outline names) or an empty list
    def childsList(self) :
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

class BC_outlines(BC_elements,bpy.types.PropertyGroup):
    type   = bpy.props.StringProperty() # its tag
    attached = bpy.props.StringProperty() # its attached object name (the real mesh)
    data = bpy.props.StringProperty(default="{'perimeters':[], 'lines':[], 'dots':[], 'matrix':Matrix() }") # global. if the outline object is missing, create from this
    childs = bpy.props.StringProperty(default='')
    parent = bpy.props.StringProperty(default='')

    ## given an outline, retrieves its geometry as a dictionnary from the otl.data string field :
    # @param what 'perimeters', 'lines', 'dots', 'matrix', or 'all' default is 'perimeters'
    # @return a nested lists of vertices, or the world matrix, or all fields in a dict.
    def dataGet(self,what='perimeters') :
        data = eval(self.data)
        #print('out %s'%str(data['matrix']))
        data['matrix'] = Matrix(data['matrix'])
        if what == 'all' : return data
        return data[what]

    ## set or modify the geometry of an outline
    # @param what 'perimeters', 'lines', 'dots', 'matrix', or 'all' default is 'perimeters'
    # @param data a list with nested list of vertices or a complete dictionnary conaining the four keys
    def dataSet(self,data,what='perimeters') :
        pdata = self.dataGet('all')
        if what == 'all' : pdata = data
        pdata[what] = data
        self.data = '{ "perimeters": ' + str(pdata['perimeters']) + ', "lines":' + str(pdata['lines']) + ', "dots":' + str(pdata['dots']) + ', "matrix":' + matToString(pdata['matrix']) +'}'

    ## read the geometry of the outline object and sets its data (dataSet call)
    # @return False if object does not exists
    def dataRead(self) :

        obsource=self.object()
        if obsource :
            mat, perim = outlineRead(obsource)
            '''
            mat=obsource.matrix_world
            if len(obsource.modifiers) :
                sce = bpy.context.scene
                source = obsource.to_mesh(sce, True, 'PREVIEW')
            else :
                source=obsource.data
            verts=[ v.co for v in source.vertices[:] ]
            edges=[ e.vertices for e in source.edges[:] ]
            if len(obsource.modifiers) :
                bpy.data.meshes.remove(source)

            for vi,v in enumerate(verts) :
                x,y,z = v * mat
                x = int(x * 1000000) / 1000000
                y = int(y * 1000000) / 1000000
                z = int(z * 1000000) / 1000000
                verts[vi]=Vector((x,y,z))

            neighList=[[] for v in range(len(verts))]
            for e in edges :
                neighList[e[0]].append(e[1])
                neighList[e[1]].append(e[0])
           # todo some tests to check if it's a perimeter : closed, only 2 neighbours/verts, no intersection, only one perimeter..
            # assuming the user if someone kind for now, shut up greg.
            # retrieve all perimeters in the outline
            lst = [ i for i in range(len(verts)) ]
            vertcount = 0
            perim = [ ]
            perimz = [ ]

            while vertcount < len(verts) :
                for i,startvert in enumerate(lst) :
                    if startvert != -1 :
                        lst[i] = -1
                        break
                        
                vi = startvert
                pvi = startvert
                vertcount += 1
                #perimid = 0
                go=True

                newperim = [ verts[startvert] ]
                newperimz = collections.Counter()
                while go :
                    nvi = neighList[vi][0] if neighList[vi][0] != pvi else neighList[vi][1]
                    if nvi != startvert : 
                        newperim.append( verts[nvi] )
                        newperimz[verts[nvi][2]] += 1
                        lst[nvi] = -1
                        pvi = vi
                        vi = nvi
                        vertcount += 1
                    else :
                        perim.append(newperim)
                        perimz.append(newperimz)
                        go=False
            '''
            #data = { 'matrix':[], 'perimeters':[], 'lines':[], 'dots':[] }
            #data['matrix'] = mat
            #data['perimeters'] = perim
            self.dataSet(perim)
            #print('send %s'%mat)
            self.dataSet(mat,'matrix')
            return True
        else : return False

    ## write the geometry in the outline object from its data field (dataGet call)
    def dataWrite(self) :
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
        ob = createMeshObject(self.name,verts,edges)
        ob.matrix_world = Matrix()
        self.asElement().pointer = str(ob.as_pointer())

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


##\brief the builders registered
#
# By default this is empty and will be populated with builder collections

class BC_builders(bpy.types.PropertyGroup):
	builders_list = bpy.props.StringProperty()