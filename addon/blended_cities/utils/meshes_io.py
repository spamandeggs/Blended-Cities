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

## like tesselate but with an optional index offset giving the first vert index
# @param list of vertices. vertices are in Vector format.
# @offset index of the first vertex
# @return list of faces
def fill(vertlist,offset=0) :
    faces = geometry.tesselate_polygon([vertlist])
    for i,f in enumerate(faces) : faces[i] = ( f[0] + offset, f[1] + offset, f[2] + offset )
    return faces

## check if there's nested lists in a list. used by functions that need
# list(s) of vertices/faces/edges etc as input
# @param lst a list or a list of list
# @returns always nested list(s)
# a boolean True if was nested, False if was not
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

            # RETRIEVING

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

            # DISCOVERING

            # for each vert, store its neighbour(s) or nothing for dots
            neighList=[[] for v in range(len(verts))]
            for e in edges :
                neighList[e[0]].append(e[1])
                neighList[e[1]].append(e[0])

            # lst is used to know if a vert has been 'analysed' ( = -1 ) or not.
            lst = [ i for i in range(len(verts)) ]
            perims = [ ]
            dots = [ ]
            lines = [ ]
            routers = {}

            # dots : verts with no neighbours
            for i,neighs in enumerate(neighList) :
                if neighs == [] :
                    dots.append(verts[i])
                    lst[i] = -1

            # lines/network
            for vi,neighs in enumerate(neighList) :
                if len(neighs) == 1 or len(neighs) >= 3 : #and lst[i] != -1 :
                    for ni in neighs :
                        if lst[ni] != -1 :
                            line, rm, closed = readLine(vi,ni,verts,neighList)
                            for off in rm : lst[off] = -1
                            if closed : perims.append(line)
                            else : lines.append(line)
                    lst[vi] = -1
                    # this vi is a router with len(neigh) road
                    # ...
                    # ...

            # perimeters
            for vi,neighs in enumerate(neighList) :
                if len(neighs) == 2 and lst[vi] != -1 :
                    ni = neighs[0] if neighs[0] != vi else neighs[1]
                    perim, rm, closed = readLine(vi,ni,verts,neighList)
                    for off in rm : lst[off] = -1
                    lst[vi] = -1
                    perims.append(perim)
                    print('\n%s\n'%perim)
                    # should add a router for closed perimeter
                    # ...
                    # ...
            # check
            for vi,l in enumerate(lst) :
               if l != -1 : print(verts[vi])

            return mat, perims, lines, dots

def readLine(pvi,vi,verts,neigh) :
    start = pvi
    line = [ verts[pvi], verts[vi] ]
    go = True
    rm = []
    while go and len(neigh[vi]) == 2 :
        nvi = neigh[vi][0] if neigh[vi][0] != pvi else neigh[vi][1]
        rm.append(vi)
        if nvi == start : go = False
        else :
            line.append( verts[nvi] )
            pvi = vi
            vi = nvi
    if len(neigh[vi]) == 1 :  rm.append(neigh[vi][0])
    return line, rm, not(go)

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
 
# returns faces from a loop of vertices
# @param offset int index of the first vertex
# @param length int number of verts defining a line or a poly
# @param line bool True if is a line, False (default) if is a poly
# @param loop TODO number of layers of faces
# @return quad faces
def facesLoop(offset,length,line=False,loop=1) :
    faces = []
    for v1 in range(length) :
        if v1 == length - 1 :
            if line : return faces
            v2 = 0
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

