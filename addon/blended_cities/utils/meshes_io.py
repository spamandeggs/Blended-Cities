##\file
# meshes_io.py
# set of functions used by builders
print('meshes_io.py')
import bpy
import mathutils
import random
from mathutils import *
import collections

from blended_cities.core.class_main import *

## check if there's nested lists in a list. used by functions that need
# list(s) of vertices as input
# returns the given list always nested,
# and a bolean : True if was nested, False if was not
def nested(lst) :
    try :
        t = lst[0][0][0]
        return lst, True
    except :
        return [lst], False

def matToString(mat) :
    #print('*** %s %s'%(mat,type(mat)))
    return str(mat).replace('\n       ','')[6:]

def stringToMat(string) :
    return Matrix(eval(string))


def buToMeters(vertslists) :
    vertslists, nest = nested(vertslists)
    scale = bpy.context.scene.unit_settings.scale_length
    meterslists = []

    for verts in vertslists :
        meters = []
        for vert in verts :
            meters.append(Vector(vert) * scale)
        meterslists.append(meters)
        
    if nest : return meterslists
    else : return meterslists[0]

def metersToBu(vertslists) :
    vertslists, nest = nested(vertslists)
    scale = bpy.context.scene.unit_settings.scale_length
    meterslists = []

    for verts in vertslists :
        meters = []
        for vert in verts :
            meters.append(Vector(vert) / scale)
        meterslists.append(meters)
        
    if nest : return meterslists
    else : return meterslists[0]

## retrieve
def outlineRead(obsource) :
            
            mat=Matrix(obsource.matrix_local)
            #mat=Matrix(obsource.matrix_world)
            if len(obsource.modifiers) :
                sce = bpy.context.scene
                source = obsource.to_mesh(sce, True, 'PREVIEW')
            else :
                source=obsource.data

            verts=[ v.co for v in source.vertices[:] ]
            edges=[ e.vertices for e in source.edges[:] ]
            if len(obsource.modifiers) :
                bpy.data.meshes.remove(source)

            # apply world to verts and round them a bit
            for vi,v in enumerate(verts) :
                x,y,z = v# * mat # for global
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

            lst = [ i for i in range(len(verts)) ]
            vertcount = 0
            perim = [ ]

            # perimeters and lines
            while vertcount < len(verts) :
                for i,startvert in enumerate(lst) :
                    if startvert != -1 :
                        lst[i] = -1
                        break
                        
                vi = startvert
                pvi = startvert
                vertcount += 1
                go=True

                newperim = [ verts[startvert] ]
                while go :
                    nvi = neighList[vi][0] if neighList[vi][0] != pvi else neighList[vi][1]
                    if nvi != startvert : 
                        newperim.append( verts[nvi] )
                        lst[nvi] = -1
                        pvi = vi
                        vi = nvi
                        vertcount += 1
                    else :
                        perim.append(newperim)
                        go=False

            return mat, perim

def readMeshMap(objectSourceName,atLocation,scale,what='readall') :
    global debug
    pdeb=debug
    scale=float(scale)

    obsource=bpy.data.objects[objectSourceName]
    mat=obsource.matrix_local
    #mat=obsource.matrix_world

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


## lock or unlock an object matrix
# @param ob the object to lock/unlock
# @param state True to lock, False to unlock
def objectFreedom(ob,state) :
    for i in range(3) :
        ob.lock_rotation[i] = state
        ob.lock_location[i] = state
        ob.lock_scale[i] = state


def objectBuild(elm, verts, edges=[], faces=[], matslots=[], mats=[] ) :
    print('build element %s (%s)'%(elm,elm.className()))
    city = bpy.context.scene.city
    # apply current scale
    verts = metersToBu(verts)
    
    obname = elm.objectName()
    if obname == False :
        obname = elm.name
    ob = createMeshObject(obname, verts, edges, faces, matslots, mats)
    elm.asElement().pointer = str(ob.as_pointer())
    if elm.className() == 'outlines' :
        if elm.parent :
            ob.parent = city.outlines[elm.parent].object()
    else :
        objectFreedom(ob,False)
        otl = elm.asOutline()
        ob.parent = otl.object()
    #ob.matrix_local = Matrix() # not used
    #ob.matrix_world = Matrix() # world
    
    return ob



def createMeshObject(name, verts, edges=[], faces=[], matslots=[], mats=[] ) :

    warn = [] # log some event


    # naming consistency for mesh w/ one user
    if name in bpy.data.objects :
        mesh = bpy.data.objects[name].data
        if mesh :
            if mesh.users == 1 : mesh.name = name
        else : print('createMeshObject : no mesh found in %s'%name)
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
    if len(matslots) > 0 :
        for matname in matslots :
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                mat.use_fake_user = True
                warn.append('Created a missing material : %s'%matname)
            else :
                mat = bpy.data.materials[matname]
            mesh.materials.append(mat)

    # map a material to each face
    if len(mats) > 0 :
        for fi,f in enumerate(mesh.faces) :
            f.material_index = mats[fi]

    # uv
    # ...

    if name not in bpy.data.objects :
        ob = bpy.data.objects.new(name=name, object_data=mesh)
    else :
        ob = bpy.data.objects[name]
        ob.data = mesh
    if  ob.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(ob)
    return ob
 


def facesLoop(offset,length,loop=1) :
    '''from length, an int defining a number of verts of a perimeter outline
    offset, definins the vert ID of the first vert
    todo : loop, the number of layer
    build faces between ordered 'lines' of vertices of a closed shape
    '''
    faces = []
    for v1 in range(length) :
        if v1 == length - 1 : v2 = 0
        else : v2 = v1 + 1
        faces.append( ( offset + v1 , offset + v1 + length , offset + v2 + length, offset + v2  ) )
    return faces


## geometry
#  @param vertslists a list or a list of lists containing vertices coordinates
#  @param offset the first vert id of the first vertice
#  @return a Counter with z coordinates as key and the number of vertices which have that value as value
def zcoords(vertslists,offset=0) :
    try : test = vertslists[0][0][0]
    except : vertslists = [vertslists]
    zlist = collections.Counter()
    for vertslist in vertslists :
        for v in vertslist :
            zlist[ v[2] + offset ] += 1
    return zlist


def updateChildHeight(otl,height) :
    print('** update childs of %s : %s'%(otl.name,otl.childs ))
    city = bpy.context.scene.city
    childs=otl.childsGet()
    for childname in childs :
        print(' . %s'%childname)
        #verts, edges, edgesW , bounds = readMeshMap(childname,True,1)
        otl_child = city.outlines[childname]
        # force re-read of data
        otl_child.dataRead()
        data = otl_child.dataGet()
        for perimeter in data :
            for vert in perimeter :
                vert[2] = height
        otl_child.dataSet(data)
        otl_child.dataWrite()
        bld_child = otl_child.peer()
        bld_child.build(True)

