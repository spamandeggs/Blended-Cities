##\file
# class_main.py
# contains the main collection classes :
# the elements class that stores every city element
# the outlines class that store each outline element
# methods used by builders classes are also inherited from here

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

#\brief the main city elements collection
#
# store any element
class BC_elements(bpy.types.PropertyGroup) :
    name  = bpy.props.StringProperty() # object name
    type  = bpy.props.StringProperty() # outlines / buildings / sidewalks...
    pointer = bpy.props.StringProperty(default='-1') # outlines / buildings / sidewalks...
    
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
        if self.type == 'outlines' : elmclass = eval('city.%s'%self.type)
        else : elmclass = eval('city.builders.%s'%self.type)
        self = elmclass[self.name]
        if self.className() != 'outlines' : return self.peer()
        else : return self

    ## given any kind of element, returns the element in its builder class
    def asBuilder(self) :
        city = bpy.context.scene.city
        self = self.asElement()
        if self.type == 'outlines' : elmclass = eval('city.%s'%self.type)
        else : elmclass = eval('city.builders.%s'%self.type)
        self = elmclass[self.name]
        if self.className() == 'outlines' : return self.peer()
        else : return self

    ## returns the class of the element as string : 'elements', 'outlines', or builder name
    def className(self) :
        return self.__class__.__name__[3:]

    ## returns the outline if the element is a builder or an Element, returns the builder if the element is an outline
    def peer(self) :
        city = bpy.context.scene.city
        if self.className() == 'elements' :
            if self.type == 'outlines' : 
                return city.outlines[self.name]
            else :
                elmclass = eval('city.builders.%s'%self.type)
                return elmclass[self.name]
        if self.className() == 'outlines' : 
            self = city.elements[self.attached]
            elmclass = eval('city.builders.%s'%self.type)
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

    def selectParent(self,attached=False) :
        elm = self.asBuilder()
        if elm.className() != 'outlines' :
            elm = elm.peer()
            attached = True
        outlines = bpy.context.scene.city.outlines
        if elm.parent != '' :
            elm = outlines[elm.parent]
        elm.select(attached)
     
    def selectChild(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        childs = self.asOutline().childList()
        if len(childs) > 0 :
            child = outlines[childs[0]]
            child.select(attached)

    def selectNext(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            siblings = outlines[self.parent].childList()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outlines[siblings[(si+1)%len(siblings)]]
                sibling.select(attached)

    def selectPrevious(self,attached=False) :
        outlines = bpy.context.scene.city.outlines
        if self.parent != '' :
            siblings = outlines[self.parent].childList()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outlines[siblings[(si-1)%len(siblings)]]
                sibling.select(attached)

# outlines class
class BC_outlines(BC_elements,bpy.types.PropertyGroup) :
    #name = bpy.props.StringProperty() # object name
    type   = bpy.props.StringProperty() # its tag
    attached = bpy.props.StringProperty() # its attached object name (the real mesh)
    data = bpy.props.StringProperty(default="'perimeters':[], 'lines':[], 'dots':[] }") # global. if the outline object is missing, create from this
    #object= bpy.props.StringProperty() # outlines / buildings / sidewalks...
    childs = bpy.props.StringProperty(default='')
    parent = bpy.props.StringProperty(default='')

    def dataGet(self) :
        return eval(self.data)

    def dataSet(self,data) :
        self.data = str(data)

    def dataRead(self) :

        obsource=self.object()
        if obsource :
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

            data = { 'perimeters':[], 'lines':[], 'dots':[] }
            #data['perimeters'] = [ perim, perimz ]
            data['perimeters'] = perim
            self.dataSet(data)
            return True
        else : return False

    def dataWrite(self) :
        data = self.dataGet()
        verts = []
        edges = []
        ofs = 0
        for perimeter in data['perimeters'] :
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
        self.asElement().pointer = str(ob.as_pointer())

    def childAdd(self,childname) :
        if self.childs == '' :
            self.childs = childname
        else :
            self.childs += ',%s'%childname
            
    def childList(self) :
        if self.childs == '' :
            return []
        else :
            return self.childs.split(',')


# builders classes inherit all methods from elements