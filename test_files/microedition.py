'''
city = bpy.context.scene.city
Hello,

here's a first test I'm doing about micro-edition.
for my script. nothing spectacular, it's just about
user interface, collection and property management tests.

this is to give you a better idea of the directions I intend
to take from my side, and also about this perimeter object
in/out thing between our work :)

alt-P then :
. select a 'perimeter' object and tag it
  (atm it only tags as a 'building lot' but there would be
  a list of tags)
. the dedicated ui show up and you can transform stuff
  (nothing yet visually, but the properties,
  and element collection lookup)

the same code could also be used for massive generation
with an autotag option for the tag operator.
one could have something similar for trafficways,
road elements could be build, or only defined and referenced
in a props_xxx collection to avoid blender lags.

also in the console or from another script you can :
 city = bpy.context.scene.city
 city.building['building.003'].floorHeight
 city.building[0].floorNumber = 3

 dir(self)
['__dict__', '__doc__', '__module__', '__weakref__', 'action', 'bl_description', 'bl_idname', 'bl_label', 'bl_options',
'bl_rna', 'cancel', 'check', 'draw', 'execute', 'has_reports', 'invoke', 'layout', 'modal', 'name', 'order', 'poll', 'pr
operties', 'report', 'rna_type'] 

modifiers

import bpy

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


def dprint(str,level=1) :
    city = bpy.context.scene.city
    if level <= city.debuglevel :
        print(str)

def elementAdd(name,tag) :
    # update the main city objects repository
    element = bpy.context.scene.city.element.add()
    element.name = name
    element.type = tag

def defineName(tag,id=0) :
    name = '%s.%1.5d'%(tag,id)
    while name in bpy.context.scene.city.element :
        id += 1
        name = '%s.%1.5d'%(tag,id)
    return name

def updateChildHeight(outline,height) :
    print('update childs of %s : %s'%(outline.name,outline.childs ))
    city = bpy.context.scene.city
    childs=outline.childList()
    for childname in childs :
        print(' . %s'%childname)
        #verts, edges, edgesW , bounds = readMeshMap(childname,True,1)
        otl_child = city.outline[childname]
        data = otl_child.dataGet()
        for perimeter in data['perimeters'] :
            for vert in perimeter :
                vert[2] = height
        otl_child.dataSet(data)

        bld_child = otl_child.peer()
        bld_child.build(False)

def createMeshObject(name, verts, edges=[], faces=[], matslots=[], mats=[] ) :

    # naming consistency for mesh w/ one user
    if name in bpy.data.objects :
        mesh = bpy.data.objects[name].data
        if mesh.users == 1 : mesh.name = name

    # update mesh/object
    if name in bpy.data.meshes :
        mesh = bpy.data.meshes[name]
        mesh.user_clear()
        wipeOutData(mesh)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    mesh.update()
    '''
    mesh.vertices.add(len(verts))
    for vi,v in enumerate(verts) :
        mesh.vertices[vi].co = v
    mesh.edges.add(len(edges))
    for ei,e in enumerate(edges) :
        mesh.edges[ei].vertices = e
    mesh.faces.add(len(faces))
    for fi,f in enumerate(faces) :
        mesh.faces[fi].vertices_raw = f
    mesh.update()
    '''
    # material slots
    for matname in matslots :
        mat = bpy.data.materials[matname]
        mesh.materials.append(mat)

    # map a material to each face
    for fi,f in enumerate(mesh.faces) :
        f.material_index = mats[fi]

    # uv
    # ...

    if name not in bpy.data.objects :
        ob = bpy.data.objects.new(name=name, object_data=mesh)
        bpy.context.scene.objects.link(ob)
    else :
        ob = bpy.data.objects[name]
        ob.data = mesh
    return ob
    
def wipeOutObject(ob,and_data=True) :
    if type(ob) == str :
        try : ob = bpy.data.objects[ob]
        except : return

    data = bpy.data.objects[ob.name].data
    #and_data=False
    # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
    # so if there's more than one user for this data, never wipeOutData. will be done with the last user
    # if in the list
    try :
        if data.users > 1 :
            and_data=False
    except :
        and_data=False # empties have no user
    # odd :
    ob=bpy.data.objects[ob.name]
    # if the ob (board) argument comes from bpy.data.groups['aGroup'].objects,
    #  bpy.data.groups['board'].objects['board'].users_scene

    for sc in ob.users_scene :
        ob.name = '_dead'#print(sc.name)
        #ob.location = [-1000,0,0]
        sc.objects.unlink(ob)

    try : bpy.data.objects.remove(ob)
    except : print('data.objects.remove issue with %s'%ob.name)

    # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
    if and_data :
        wipeOutData(data)


def wipeOutData(data) :
    if data.users == 0 :
        try :
            data.user_clear()

            # mesh
            if type(data) == bpy.types.Mesh :
                bpy.data.meshes.remove(data)
            # lamp
            elif type(data) in [bpy.types.PointLamp,bpy.types.SpotLamp,bpy.types.HemiLamp,bpy.types.AreaLamp,bpy.types.SunLamp] :
                bpy.data.lamps.remove(data)
            # camera
            elif type(data) == bpy.types.Camera :
                bpy.data.cameras.remove(data)
            # Text, Curve
            elif type(data) in [ bpy.types.Curve, bpy.types.TextCurve ] :
                bpy.data.curves.remove(data)
            # metaball
            elif type(data) == bpy.types.MetaBall :
                bpy.data.metaballs.remove(data)
            # lattice
            elif type(data) == bpy.types.Lattice :
                bpy.data.lattices.remove(data)
            # armature
            elif type(data) == bpy.types.Armature :
                bpy.data.armatures.remove(data)
            else :
                print('data still here : forgot %s'%type(data))

        except :
            # empty, field
            print('%s has no user_clear attribute.'%data.name)
    else :
        print('%s has %s user(s) !'%(data.name,data.users))

def readMeshMap(objectSourceName,atLocation,scale,what='readall') :
    global debug
    pdeb=debug
    scale=float(scale)

    obsource=bpy.data.objects[objectSourceName]
    mat=obsource.matrix_world
    #scaleX, scaleY, scaleZ = obsource.scale
    #rmat=mat.rotationPart().resize4x4()
    #if atLocation :
    #    rmat[3][0]=mat[3][0]/scale
    #    rmat[3][1]=mat[3][1]/scale
    #   rmat[3][2]=mat[3][2]/scale

    # modifiers in outline case :
    # read verts loc from a dupli (1/2 removed below)
    if len(obsource.modifiers) :
        sce = bpy.context.scene
        source = obsource.to_mesh(sce, True, 'PREVIEW')
    else :
        source=obsource.data

    # output :
    coordsList=[]            # list of verts
    edgesList=[]            # list of edges
    edgesWList=[]            # edge width
 
    # COORDSLIST - scaled + obj global param.
    for v in source.vertices :
        x,y,z = v.co * mat
        x = int(x * 1000000) / 1000000
        y = int(y * 1000000) / 1000000
        z = int(z * 1000000) / 1000000
        #y = int(round(y*scale,6) * 1000000)
        #z = int(round(z*scale,6) * 1000000)
        #coordsList.append(Vector([x,y,z]))
        coordsList.append([x,y,z])
        if len(coordsList)==1 :
            xmin=xmax=x
            ymin=ymax=y
            zmin=zmax=z
        else :
            xmin=min(xmin,x)
            ymin=min(ymin,y)
            zmin=min(zmin,z)
            xmax=max(xmax,x)
            ymax=max(ymax,y)
            zmax=max(zmax,z)

    # mods in outline (2/2)
    obsource=bpy.data.objects[objectSourceName]
    if len(obsource.modifiers) :
        #wipeOutObject(bpy.context.scene.objects.active.name)
        #print(selected.name)
        #bpy.ops.object.select_name(name=selected.name)
        bpy.data.meshes.remove(source)

    if what == 'readall' :
        # EDGELIST - raw
        # map road category to each edge
        for e in source.edges :
            edgesList.append([e.vertices[0],e.vertices[1]])
            edgesWList.append(e.crease)
        if pdeb :
            print("RAW :\ncoords :")   
            for i,v in enumerate(coordsList) :print(i,v)
            print("\nedges :")    
            for i,v in enumerate(edgesList) : print(i,v)

        return coordsList,edgesList,edgesWList,[ [xmin,xmax], [ymin,ymax], [zmin,zmax] ]
    else :
        return Vector([xmin,ymin,0]),Vector([xmax-xmin,ymax-ymin,0])

def buildingParts(self,context) :     
    coordsList, edgesList, edgesW , bounds = readMeshMap(self.outline,True,1)
    
    createMeshObject(self.name, verts, [], faces)
 
def zcoords(vertslists,offset=0) :
    try : test = vertslists[0][0][0]
    except : vertslists = [vertslists]
    zlist = collections.Counter()
    for vertslist in vertslists :
        for v in vertslist :
            zlist[ v[2] + offset ] += 1
    return zlist

# update functions.
def updateBuild(self,context='') :
    self.build(True)
    #buildBox(self,context,True)

def buildBox(self,refreshData=True) :
    city = bpy.context.scene.city
    outline = self.peer()
    print('build box %s (outline %s)'%(self.name,outline.name))

    matslots = ['floor','inter'] 
    mat_floor = 0
    mat_inter = 1

    if refreshData :
        print('refresh data')
        print(outline.dataRead())
    perimeter = outline.dataGet()['perimeters']
    zlist = zcoords(perimeter)
    print('perim %s'%(perimeter))
    print('max height %s'%max(zlist))
    

    verts = []
    faces = []
    mats  = []

    fof = 0 # 'floor' vertex id offset

    for id in range(len(perimeter)) :

        fpf = len(perimeter[id]) # nb of faces per floor

        # non planar outlines : add simple fundation. todo : should be part of floors
        if max(zlist) - min(zlist) > 0.000001 :
            verts.extend( perimeter[id] )
            faces.extend( facesLoop(fof,fpf) )
            mats.extend( mat_floor for i in range(fpf) )
            fof += fpf

        zs = self.heights(max(zlist))#bounds[2][0])
        for zi,z in enumerate(zs) :
            for c in perimeter[id] :
                verts.append( Vector(( c[0],c[1],z )) )
            
            # while roof not reached, its a floor so add faces and mats
            if z != zs[-1] : 
                faces.extend( facesLoop(fof,fpf) )
                mat_id = zi%2
                mats.extend( mat_id for i in range(fpf) )
            fof += fpf
    
    obname = self.objectName()
    if obname == False :
        obname = self.name
    #    print('created %s'%obname)
    #else : print('found object %s'%obname)

    ob = createMeshObject(obname, verts, [], faces, matslots, mats)
    
    city.element[self.name].pointer = ob.as_pointer()
    
    height = self.height() + max(zlist)
    
    updateChildHeight(outline,height)
 
# build faces between ordered 'lines' of vertices of a closed shape
# offset : first vertex id, length : nb of verts per line
def facesLoop(offset,length,loop=1) :
    faces = []
    for v1 in range(length) :
        if v1 == length - 1 : v2 = 0
        else : v2 = v1 + 1
        faces.append( ( offset + v1 , offset + v1 + length , offset + v2 + length, offset + v2  ) )
    return faces

# ###################################################
# PROPERTY CLASSES
# ###################################################

class BC_elements(bpy.types.PropertyGroup) :
    name  = bpy.props.StringProperty() # object name
    type  = bpy.props.StringProperty() # outlines / buildings / sidewalks...
    pointer = bpy.props.IntProperty() # outlines / buildings / sidewalks...
    
    # element name to element id lookup
    def index(self) :
        return int(self.path_from_id().split('[')[1].split(']')[0])

    def inElement(self) :
        return bpy.context.scene.city.element[self.name]

    def inOutline(self) :
        elm = self.inClass()
        if elm.className() != 'outline' : return self.peer()
        else : return self

    def inClass(self) :
        if self.className() == 'elements' : 
            elmclass = eval('bpy.context.scene.city.%s'%self.type)
            return elmclass[self.name]
        else :
            return self

    # blender object <-> elements methods
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

    def object(self) :
        elm = bpy.context.scene.city.element[self.name]
        if elm.pointer == -1 : return False
        for ob in bpy.context.scene.objects :
            if ob.as_pointer() == elm.pointer :
                return ob
        else : return False

    def objectName(self) :
        ob = self.object()
        if ob : return ob.name
        else : return False

    def objectNameSet(self) :
        ob = self.object()
        if ob : 
            ob.name = self.name
            ob.data.name = self.name
        else : return False

    # name of a NEW element
    def nameNew(self,tag,id=0) :
        name = '%s.%1.5d'%(tag,id)
        while name in bpy.context.scene.city.element :
            id += 1
            name = '%s.%1.5d'%(tag,id)
        self.name = name
        return name

    def className(self) :
        return self.__class__.__name__[3:]

    def peer(self) :
        city = bpy.context.scene.city
        elm=self.inClass()
        elm = city.element[elm.attached]
        elmClass = eval('bpy.context.scene.city.%s'%elm.type)
        elm = elmClass[elm.name]
        return elm

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
        elm = self.inClass()
        if elm.className() != 'outline' :
            elm = elm.peer()
            attached = True
        outline = bpy.context.scene.city.outline
        if elm.parent != '' :
            elm = outline[elm.parent]
        elm.select(attached)
     
    def selectChild(self,attached=False) :
        outline = bpy.context.scene.city.outline
        childs = self.inOutline().childList()
        if len(childs) > 0 :
            child = outline[childs[0]]
            child.select(attached)

    def selectNext(self,attached=False) :
        outline = bpy.context.scene.city.outline
        if self.parent != '' :
            siblings = outline[self.parent].childList()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outline[siblings[(si+1)%len(siblings)]]
                sibling.select(attached)

    def selectPrevious(self,attached=False) :
        outline = bpy.context.scene.city.outline
        if self.parent != '' :
            siblings = outline[self.parent].childList()
            if len(siblings) > 1 :
                si = siblings.index(self.name)
                sibling = outline[siblings[(si-1)%len(siblings)]]
                sibling.select(attached)

class BC_outline(BC_elements,bpy.types.PropertyGroup) :
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
            for vi,v in enumerate(perimeter) :
                verts.append(v)
                if vi-ofs < len(perimeter)-1 :
                    edges.append([ofs+vi,ofs+vi+1])
            edges.append([ofs+vi,ofs])
            ofs += len(perimeter)
        print(verts,edges)
        ob = createMeshObject(self.name,verts,edges)
        self.inElement().pointer = ob.as_pointer()

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

        
    #def select(self,attached=False) :
    #    if attached :
    #        bpy.ops.object.select_name(name=self.attached)
    #    else :
    #        bpy.ops.object.select_name(name=self.name)

class BC_props_builder(BC_elements,bpy.types.PropertyGroup) :

    # common methods for element sub classes #

    def something(self) :
        pass


class BC_building(BC_props_builder,bpy.types.PropertyGroup) :
    #name = bpy.props.StringProperty()
    attached = bpy.props.StringProperty()   # the perimeter object
    inherit = bpy.props.BoolProperty(default=False,update=updateBuild)
    floorNumber = bpy.props.IntProperty(
        default = 3,
        min=1,
        max=30,
        update=updateBuild
        )
    floorHeight = bpy.props.FloatProperty(
        default = 2.4,
        min=2.2,
        max=5.0,
        update=updateBuild
        )
    firstFloorHeight = bpy.props.FloatProperty(
        default = 3,
        min=2.2,
        max=5,
        update=updateBuild
        )
    firstFloor = bpy.props.BoolProperty(update=updateBuild)
    interFloorHeight = bpy.props.FloatProperty(
        default = 0.3,
        min=0.1,
        max=1.0,
        update=updateBuild
        )
    roofHeight = bpy.props.FloatProperty(
        default = 0.5,
        min=0.1,
        max=1.0,
        update=updateBuild
        )
    materialslots = ['floor','inter']
    materials = ['floor','inter']

    def build(self,refreshData=True) :
        return buildBox(self,refreshData)

    def heights(self,offset=0) :
        city = bpy.context.scene.city
        this = self
        while this.inherit == True :
            print(this.name,this.inherit)
            outline = city.outline[this.attached]
            outline = city.outline[outline.parent]
            this = city.building[outline.attached]
        zs = [] # list of z coords of floors and ceilings
        for i in range( self.floorNumber ) :
            if i == 0 :
                zf = offset
                if self.firstFloor :
                    zc = offset + self.firstFloorHeight
                else :
                    zc = offset + this.floorHeight
            else :
                zf = zc + this.interFloorHeight
                zc = zf + this.floorHeight
            zs.append(zf)
            zs.append(zc)
        zs.append(zc + this.roofHeight) # roof

        return zs
 
    def height(self,offset=0) :
        return self.heights(offset)[-1]


class BC_props_main(bpy.types.PropertyGroup) :
    element = bpy.props.CollectionProperty(type=BC_elements)
    building = bpy.props.CollectionProperty(type=BC_building)
    outline = bpy.props.CollectionProperty(type=BC_outline)
    tagitems = ( ('building','building lot','a building lot'),('child','child','a child element') )
    tagmenu  = bpy.props.EnumProperty( items = tagitems,  default = 'building', name = "Tag",  description = "" )
    debuglevel = bpy.props.IntProperty(default=1)

    go = bpy.props.BoolProperty()
    go_once = bpy.props.BoolProperty()

    def elementNew(self,element, outlineOb=False,outlineName='outline') :
        # a class name is given :
        if type(element) == str :
            elementClassName=element.split('.')[0]
            elementName=element
            isChild = False
        # or a parent element is given (when creating child elements):
        else :
            elementClassName=element.className()
            elementName=element.nameMain()
            otl_dad = element.peer()
            outlineName=otl_dad.nameMain()
            isChild = True
            print('dad : %s %s'%(otl_dad,otl_dad.name))
        print('class : %s'%(elementClassName))

        print('ischild : %s'%(isChild))
        # check if the class exist
        try : elmclass = eval('bpy.context.scene.city.%s'%elementClassName)
        except :
            print('class %s not found.'%elementClassName)
            return False, False

        city = bpy.context.scene.city

        # create a new outline as element 
        otl_elm = city.element.add()
        otl_elm.nameNew(outlineName)
        otl_elm.type = 'outline'
        if outlineOb : otl_elm.pointer = outlineOb.as_pointer()
        else : otl_elm.pointer = -1  # todo : spawn a primitive of the elm class

        # a new outline in its class
        otl = city.outline.add()
        otl.name = otl_elm.name
        otl.type = elementClassName
        if otl_elm.pointer != -1 :
            otl.dataRead()
        elif isChild :
            # otl.data['perimeters'].extend(otl_dad.data['perimeters']) # pointer...
            #otl.data = otl_dad.data.copy() # pointer...
            #otl.data['perimeters'] = [0,0,0]
            #otl.data = deepupdate(otl.data,otl_dad.data)
            otl.data = otl_dad.data

        # the new object as element
        new_elm = city.element.add()
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

            city = bpy.context.scene.city
            # USER FUNC
            #print('event %s'%(event.type))

            #if event.type == 'MOUSEMOVE':
            #    self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

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

                        if elm.className() == 'building' or elm.peer().className() == 'building' :
                            if elm.className() == 'building' :
                                blg = elm
                            else :
                                blg = elm.peer()
                            blg.build()
            #bpy.ops.object.select_name(name=self.name)
                        self.go_once = False
                        #if self.go == False : mdl.log = 'paused.'

    # given an object or its name, returns a city element (from its class)
    # false if not found
    def elementGet(self,ob) :
        if type(ob) == str :
            ob = bpy.data.objects[ob]
        pointer = ob.as_pointer()
        for elm in self.element :
            if elm.pointer == pointer :
                elmclass = eval('bpy.context.scene.city.%s'%elm.type)
                return elmclass[elm.name]
        return False


# ###################################################
# UI
# ###################################################


# common ui elements
def drawRemoveTag(layout) :
    row = layout.row()
    row.operator('perimeter.tag',text = 'Remove tag')

    
def drawMainBuildingTool(layout) :
    
    row = layout.row()
    row.operator('building.list',text = 'List Building in console')
    
    row = layout.row()
    row.operator('building.wipe',text = 'Wipe buildings')      

    row = layout.row()
    row.operator('building.wipe',text = 'Wipe Tags and buildings').removetag = True

    row = layout.row()
    row.operator('building.build',text = 'Rebuild tagged')     

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
        drawMainBuildingTool(layout)

# tagger ui
class BC_outline_panel(bpy.types.Panel) :
    bl_label = 'Outline ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'outline_ops'


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

# a city element panel
class BC_building_panel(bpy.types.Panel) :
    bl_label = 'Building ops'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_idname = 'building_ops'


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
            elm = city.elementGet(bpy.context.active_object)
            if elm :
                #print(elm.className())
                if ( elm.className() == 'outline' and city.element[elm.attached].type == 'building') or \
                elm.className() == 'building' :
                    return True
                    #tagClass = eval('city.%s'%city.element[ob.name].type)
                    #print(tagClass[ob.name].outline)
                    #bpy.ops.object.select_name(name=tagClass[ob.name].outline)
                #'citytag' in  and bpy.context.active_object['citytag'] == 'building_lot' : 
                # use poll to create the mesh if does not exists ?
                #return True
        
        
    def draw(self, context):
        city = bpy.context.scene.city
        modal = bpy.context.window_manager.modal
        scene  = bpy.context.scene

        # either the building or its outline is selected : lookup
        elm = city.elementGet(bpy.context.active_object)
        if elm.className() == 'outline' : 
            building = city.building[elm.attached]
            outline  = elm
        else :
            building = elm
            outline = city.outline[elm.attached]

        layout  = self.layout
        layout.alignment  = 'CENTER'
        
        row = layout.row()
        row.label(text = 'Name : %s / %s'%(building.objectName(),building.name))
        
        row = layout.row()
        row.label(text = 'Floor Number:')
        row.prop(building,'floorNumber')

        row = layout.row()
        row.label(text = 'Build First Floor :')
        row.prop(building,'firstFloor')

        row = layout.row()
        row.label(text = 'Inherit Values :')
        row.prop(building,'inherit')

        if building.inherit : ena = False
        else : ena = True

        row = layout.row()
        row.active = ena
        row.label(text = 'Floor Height :')
        row.prop(building,'floorHeight')

        row = layout.row()
        row.active = building.firstFloor
        row.label(text = '1st Floor Height :')
        row.prop(building,'firstFloorHeight')

        row = layout.row()
        row.active = ena
        row.label(text = 'Inter Floor Height :')
        row.prop(building,'interFloorHeight')

        row = layout.row()
        row.active = ena
        row.label(text = 'Roof Height :')
        row.prop(building,'roofHeight')

        row = layout.row()
        row.operator('building.part',text='Add a part above this').action='add above'
        
        row = layout.row(align = True)
        row.operator( "city.selector", text='', icon = 'TRIA_DOWN').action='%s parent'%outline.name
        row.operator( "city.selector",text='', icon = 'TRIA_UP' ).action='%s child'%outline.name
        row.operator( "city.selector",text='', icon = 'TRIA_LEFT' ).action='%s previous'%outline.name
        row.operator( "city.selector",text='', icon = 'TRIA_RIGHT' ).action='%s next'%outline.name
        row.operator( "city.selector",text='Edit', icon = 'TRIA_RIGHT' ).action='%s edit'%outline.name
            
        row = layout.row()
        row.label(text = 'AutoRefresh :')
        if modal.status :
            row.operator('wm.modal_stop',text='Stop')
        else :
            row.operator('wm.modal_start',text='Start')
        row.operator('wm.modal',text='test')

        layout.separator()

        drawRemoveTag(layout)

# ###################################################
# OPERATORS
# ###################################################

class OP_BC_Selector(bpy.types.Operator) :
    '''next camera'''
    bl_idname = 'city.selector'
    bl_label = 'Next'

    action = bpy.props.StringProperty()

    def execute(self, context) :
        city = bpy.context.scene.city
        otl, action = self.action.split(' ')
        otl = city.outline[otl]
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

class OP_BC_buildingParts(bpy.types.Operator) :
    
    bl_idname = 'building.part'
    bl_label = 'add a part'
    
    action = bpy.props.StringProperty()
    
    def execute(self, context) :
        city = bpy.context.scene.city
        # selected object lookup
        elm = city.elementGet(bpy.context.active_object)
        if elm.className() == 'outline' :
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

                new, otl = city.elementNew(tag,outlineOb)
                new.select()

                print('attached %s to outline %s (ob current name : %s)'%(new.name,otl.name,new.objectName() ))
        #else :
        #    city.building.remove(outlineOb['citytag_id'])
        #    del outlineOb['citytag']
        #    del outlineOb['citytag_id']
                        
        return {'FINISHED'}


class OP_BC_buildinglist(bpy.types.Operator) :
   
    bl_idname = 'building.list'
    bl_label = 'list building in console'
    
    def execute(self,context) :
        print('building list :')
        for bi,b in enumerate(bpy.context.scene.city.building) :
            if b.parent == '' :
                print(' %s %s / %s'%(bi,b.name,b.attached)) 
        return {'FINISHED'}


class OP_BC_buildingWipe(bpy.types.Operator) :
   
    bl_idname = 'building.wipe'
    bl_label = 'remove all'
    
    removetag = bpy.props.BoolProperty()
    
    def execute(self,context) :
        city = bpy.context.scene.city
        for b in city.building :
            wipeOutObject(b.name)
        if self.removetag :
            while len(city.building) > 0 :
                name=city.building[0].name
                elm = city.element[name].index()
                city.building.remove(0)
                city.element.remove(elm)
            while len(city.outline) > 0 :
                name=city.outline[0].name
                elm = city.element[name].index()
                city.outline.remove(0)
                city.element.remove(elm)
                # but we keep the objects
        return {'FINISHED'}


class OP_BC_buildingBuild(bpy.types.Operator) :
   
    bl_idname = 'building.build'
    bl_label = 'rebuild all'
    
    removetag = bpy.props.BoolProperty()
    
    def execute(self,context) :
        building = bpy.context.scene.city.building
        for b in building :
            buildBox(b)
        return {'FINISHED'}


#class OP_BC_floors(bpy.types.Operator) :
#    
#   bl_idname = 'building.floor_number'
#    bl_label = 'modify floor number - modal'
def init() :
    scene = bpy.context.scene
    city = scene.city
    while len(city.element) > 0 :
        city.element.remove(0)
    while len(city.building) > 0 :
        city.building.remove(0)
    while len(city.outline) > 0 :
        city.outline.remove(0)
    #bpy.context.scene.modal.status = True
    #bpy.ops.wm.modal_timer_operator()
    mdl = bpy.context.window_manager.modal
    mdl.func = 'bpy.context.scene.city.modalBuilder(self,context,event)'

import bpy
import sys
import addon_utils


def register() :
    # propertygroups
    bpy.utils.register_class(BC_building)
    bpy.utils.register_class(BC_outline)
    bpy.utils.register_class(BC_props_builder)
    bpy.utils.register_class(BC_elements)
    bpy.utils.register_class(BC_props_main)
    bpy.types.Scene.city = bpy.props.PointerProperty(type=BC_props_main)

    # operators
    bpy.utils.register_class(OP_BC_tag)
    bpy.utils.register_class(OP_BC_Selector)
    bpy.utils.register_class(OP_BC_buildinglist)
    bpy.utils.register_class(OP_BC_buildingBuild)
    bpy.utils.register_class(OP_BC_buildingWipe)
    bpy.utils.register_class(OP_BC_buildingParts)

    # panels
    bpy.utils.register_class(BC_main_panel)
    bpy.utils.register_class(BC_building_panel)
    bpy.utils.register_class(BC_outline_panel)
    init()


def unregister() :
    bpy.utils.unregister_class(BC_objects)
    bpy.utils.unregister_class(BC_building)
    bpy.utils.unregister_class(BC_props_builder)
    bpy.utils.unregister_class(BC_outline)
    bpy.utils.unregister_class(BC_elements)
    bpy.utils.unregister_class(BC_props_main)

if __name__ == "__main__" :
    print('B.C. wip')
    register()