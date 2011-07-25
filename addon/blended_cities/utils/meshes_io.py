##\file
# meshes_io.py
# set of functions used by builders

import bpy
import mathutils
from mathutils import *
import collections

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
    if len(matslots) > 0 :
        for matname in matslots :
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
        bpy.context.scene.objects.link(ob)
    else :
        ob = bpy.data.objects[name]
        ob.data = mesh
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
    print('update childs of %s : %s'%(otl.name,otl.childs ))
    city = bpy.context.scene.city
    childs=otl.childList()
    for childname in childs :
        print(' . %s'%childname)
        #verts, edges, edgesW , bounds = readMeshMap(childname,True,1)
        otl_child = city.outlines[childname]
        data = otl_child.dataGet()
        for perimeter in data['perimeters'] :
            for vert in perimeter :
                vert[2] = height
        otl_child.dataSet(data)

        bld_child = otl_child.peer()
        bld_child.build(False)

