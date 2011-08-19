##\file
# meshes_io.py
# set of functions used by builders
print('meshes_io.py')
import bpy
import mathutils
import random
from mathutils import *

from blended_cities.core.class_main import *
from blended_cities.core.common import *
from blended_cities.utils.geo import *
  
    
def matToString(mat) :
    #print('*** %s %s'%(mat,type(mat)))
    return str(mat).replace('\n       ','')[6:]

def stringToMat(string) :
    return Matrix(eval(string))


## retrieve
def outlineRead(obsource) :

            # RETRIEVING

            mat_ori = Matrix(obsource.matrix_world).copy()
            loc, rot, scale = mat_ori.decompose()
            mat = Matrix()
            mat[0][0] *= scale[0]
            mat[1][1] *= scale[1]
            mat[2][2] *= scale[2]
            mat *= rot.to_matrix().to_4x4()

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
                x,y,z = v * mat #  as global coords
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
                    #print('\n%s\n'%perim)
                    # should add a router for closed perimeter
                    # ...
                    # ...
            # check
            #for vi,l in enumerate(lst) :
            #   if l != -1 : print(verts[vi])

            return mat_ori, perims, lines, dots


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

## lock or unlock an object matrix
# @param ob the object to lock/unlock
# @param state True to lock, False to unlock
def objectLock(ob,state=True) :
    for i in range(3) :
        ob.lock_rotation[i] = state
        ob.lock_location[i] = state
        ob.lock_scale[i] = state


def objectBuild(elm, verts, edges=[], faces=[], matslots=[], mats=[] ) :
    #print('build element %s (%s)'%(elm,elm.className()))
    print('object build')
    city = bpy.context.scene.city
    # apply current scale
    verts = metersToBu(verts)
    
    if type(elm) != str :
        obname = elm.objectName()
        if obname == False :
            obname = elm.name
    else : obname= elm

    obnew = createMeshObject(obname, verts, edges, faces, matslots, mats)
    #elm.asElement().pointer = str(ob.as_pointer())
    if type(elm) != str :
        if elm.className() == 'outlines' :
            obnew.lock_scale[2] = True
            if elm.parent :
                obnew.parent = elm.Parent().object()
        else :
            #otl = elm.asOutline()
            #ob.parent = otl.object()
            objectLock(obnew,True)
        #ob.matrix_local = Matrix() # not used
        #ob.matrix_world = Matrix() # world
    return obnew


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
                warn.append('Created missing material : %s'%matname)
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
        dprint('  create object %s'%ob.name)
    else :
        ob = bpy.data.objects[name]
        ob.data = mesh
        ob.parent = None
        ob.matrix_local = Matrix()
        dprint('  reuse object %s'%ob.name)
    if  ob.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(ob)
    return ob
 
def materialsCheck(bld) :
    if hasattr(bld,'materialslots') == False :
        #print(bld.__class__.__name__)
        builderclass = eval('bpy.types.%s'%(bld.__class__.__name__))
        builderclass.materialslots=[bld.className()]

    matslots = bld.materialslots
    if len(matslots) > 0 :
        for matname in matslots :
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.use_fake_user = True
                if hasattr(bld,'mat_%s'%(matname)) :
                    method = 'defined in builder'
                    matdef = eval('bld.mat_%s'%(matname))
                    mat.diffuse_color = matdef['diffuse_color']
                else :
                    method = 'random'
                    mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                dprint('Created missing material %s (%s)'%(matname,method))



def updateChildHeight(otl,height) :
    print('** update childs of %s : %s'%(otl.name,otl.childs ))
    city = bpy.context.scene.city
    for otl_child in otl.Childs() :
        print(' . %s'%otl_child.name)
        #verts, edges, edgesW , bounds = readMeshMap(childname,True,1)
        #otl_child = city.outlines[child.name]
        # force re-read of data
        otl_child.dataRead()
        data = otl_child.dataGet()
        for perimeter in data :
            for vert in perimeter :
                vert[2] = height
        otl_child.dataSet(data)
        otl_child.dataWrite()
        bld_child = otl_child.peer()
        #bld_child.build(True)
        city.builders.build(bld_child)

