## geometry
import collections
from math import *

import bpy
import mathutils
from mathutils import *
from blended_cities.core.common import *


## returns the area of a polyline
def area(poly,ptype='coord') :
    if ptype=='vector' : poly=vecToCoord(poly)
    A=0
    poly.append(poly[0])
    for i,c in enumerate(poly) :
        j = (i+1)%(len(poly))
        A += poly[i][0] * poly[j][1]
        A -= poly[i][1] * poly[j][0]
    A /= 2
    return abs(A)


## returns the perimeter of a polyline
def perimeter(poly,ptype="vector") :
    if ptype=="coord" : poly=coordToVec(poly,True)
    L=0
    for i in range(1,len(poly)) :
        l,d=readVec(poly[i])
        L +=l
    return L


## check if there's nested lists in a list. used by functions that need
# list(s) of vertices/faces/edges etc as input
# @param lst a list of vector or a list of list of vectors
# @returns always nested list(s)
# a boolean True if was nested, False if was not
def nested(lst) :
    try :
        t = lst[0][0][0]
        return lst, True
    except :
        return [lst], False

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

## returns faces for a loop of vertices
# the index of theses vertices are supposed to be ordered (anticlock)
# @param offset int index of the first vertex of the lie/poly
# @param length int number of verts defining a line or a poly, they are supposed to be ordered
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


## returns edges for a loop of vertices
# the index of theses vertices are supposed to be ordered (anticlock)
# @param offset int index of the first vertex of the lie/poly
# @param length int number of verts defining a line or a poly, they are supposed to be ordered
# @param line bool True if is a line, False (default) if is a poly
# @param loop TODO number of layers of faces
# @return quad faces
def edgesLoop(offset,length,line=False,loop=1) :
    edges = []
    for v1 in range(length) :
        if v1 == length - 1 :
            if line : return edges
            v2 = 0
        else : v2 = v1 + 1
        edges.append([ offset + v1, offset + v2 ])
    return edges

##############
## CONVERTERS
##############

##  ordered coords ---> ordered vectors
# @param polys list of coordinates or list ot lists of coordinates
# @param ispoly default True : a (list of) polygon is given. False : a (list of) line  is given
# @param nocheck something related to polygon first end coords.. WIP
# @return a list or a list of lists of vectors
def coordToVec(polys,ispoly=True,nocheck=False) :
    polys, nest = nested(polys)
    for ip,poly in enumerate(polys) :
        if len(poly)>1 :
            #print poly
            c=Vector(poly[0])
            vecs=[c]
            if ispoly : l=len(poly)
            else : l=len(poly)-1
            for i in range(l) :
                if ispoly and i==len(poly)-1 : n=0
                else : n=i+1
                c=Vector(poly[n])-Vector(poly[i])
                #if readVec(c)[0] != 0 or nocheck : vecs.append(c) # BC 2.49b
                if c.length != 0 or nocheck : vecs.append(c)
            polys[ip]=vecs

    if nest : return polys
    else : return polys[0]


## ordered vectors ---> ordered coords
# ignore the last vector if it closes the poly
# @param polys list of vectors or list ot lists of vectors
# @param ispoly default True : a (list of) polygon is given. False : a (list of) line  is given
# @param nocheck something related to polygon first end coords.. WIP
# @return a list or a list of lists of coordinates (vector format)
def vecToCoord(polys,ispoly=True,nocheck=False) :
    polys, nest = nested(polys)
    for ip,poly in enumerate(polys) :
        if len(poly)>1 :
            c=Vector([0,0,0])
            coords=[]
            for i,v in enumerate(poly) :
                c = c+Vector(v)
                #if ispoly and i==len(poly)-1 and (nocheck or cfloat(c,'eq',Vector(poly[0]),0.00001)) : pass
                if ispoly and i==len(poly)-1 and (nocheck or c == Vector(poly[0])) : pass
                else :coords.append(c)
            polys[ip]=coords

    if nest : return polys
    else : return polys[0]


## blender units ---> meters
# @param vertslists list of coordinates or list ot lists of coordinates
# @return list of coordinates or list ot lists of coordinates
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


## meters ---> blender units 
# @param vertslists list of coordinates or list ot lists of coordinates
# @return list of coordinates or list ot lists of coordinates
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


## like tesselate but with an optional index offset giving the first vert index
# @param list of vertices. vertices are in Vector format.
# @offset index of the first vertex
# @return list of faces
def fill(vertlist,offset=0) :
    faces = geometry.tesselate_polygon([vertlist])
    for i,f in enumerate(faces) : faces[i] = ( f[0] + offset, f[1] + offset, f[2] + offset )
    return faces


##  determine if a point is inside a given polygon or not
# z coords are considered planar
# @param x x location of the point
# @param y y location of the point
# @poly perimeter
# @ptype as ordered coord or as ordered vector
# @return True if the point is inside the poly, else False
def pointInPoly(x,y,poly,ptype="coord"):
    inside =False
    if ptype=="vector":poly=vecToCoord(poly)
    p1x,p1y,z = poly[0]
    n = len(poly)
    for i in range(n+1):
        p2x,p2y,z = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside


## returns extruded polygons from polygons
# @param polys
# @param width
# @param ptype
# @param lst
def polyIn(polys,width,ptype="vector",lst=[],pdeb=False) :
    global debug
    pdeb = True
    if pdeb : print('polyin :')

    polys, nest = nested(polys)

    if nest :
        # check if the given width is an int applied to each poly or if each poly has its own width
        try:
            a=width[0][0]
            wlist=True
        except :
            wlist=False
            if type(width)==type(int()) or type(width)==type(float()):
                width=[width for p in range(len(polys))]
    else :
        try :
            a=width[0]
            wlist=True
            width=[width]
        except : # fixed width/poly
            wlist=False
            width=[width]

    newpolys = []

    for i,poly in enumerate(polys) :

        newpoly = []
        for ci1,p1 in enumerate(poly) :
            ci0=ci1-1
            ci2=(ci1+1)%(len(poly))
            if ci1 == 0 :
                t = angleEnlarge(poly[ci0],p1,poly[ci2],0.001)
                dir = -1 if pointInPoly(t[0],t[1],poly) else 1
            #w=[pwidth[ci1][0]*s[0],pwidth[ci1][1]*s[0]]
            w=[width[i] * dir, width[i] * dir]
            nc=angleEnlarge(poly[ci0],p1,poly[ci2],w)
            newpoly.append(nc)
        newpolys.append(newpoly)

    if nest : return newpolys
    else : return newpolys[0]

## from a vector, returns its length and its direction in degrees
# direction is planar, from x y components
def readVec(side) :
    a=side[0]
    c=side[1]
    try :
        lenght=sqrt((a*a)+(c*c))
    except :
        dprint('error lenght (except readvec): %s'%(side),4)
        if str(a)=='-1.#IND00' : a=0
        if str(c)=='-1.#IND00' : c=0
        lenght=0
    if str(lenght)=='nan' :
        dprint('error lenght (readvec): %s'%(side),4)
        a=c=0
    rot=atan2( c, a )*(180/pi)
    if str(rot)=='nan' :
        dprint('error rot (readvec) : %s %s'%(side,lenght),4)
    #return lenght,fixfloat(rot)
    return lenght,rot

## from a length and a direction in degrees, returns a vector
# direction is planar, from x y components
def writeVec(lenght,alpha,z=0) :
    beta=radians((90-alpha))
    alpha=radians(alpha)
    x=(lenght * sin(beta)) / sin(alpha+beta)
    y=(lenght * sin(alpha)) / sin(alpha+beta)
    if cfloat(x,'eq',round(x),0.0001) :x=round(x)
    if cfloat(y,'eq',round(y),0.0001) :y=round(y)
    return Vector([x,y,z])


## float/list comparison
# x and y are either floats or 2 lists of same lenght (2 verts for example)
def cfloat(x,comp,y,floattest=0.1) :
    try :t=y[0]
    except :
        x=[float(x)]
        y=[float(y)]
    if comp=="in" :
        for f in y :
            try :
                t=f[0]
                for v in y :
                    for ci,c in enumerate(x) :
                        #if str(abs(c-v[ci])) > str(floattest) : break
                        if abs(c-v[ci]) > floattest : break
                    else : return True        
                return False
            except :
                #if str(abs(x-f)) <= str(floattest) : return True
                if abs(x-f) <= floattest : return True
        return False
    else :
        for i in range(len(x)) :
            if comp=="eq" and abs(x[i]-y[i]) > floattest : return False
            elif comp=="not" and abs(x[i]-y[i]) <= floattest : return False
        return True


def angleEnlarge(c0,c1,c2,w) :
    try :t=w[0]        # variable width
    except :w=[w,w] # uniform offset
    c0=Vector(c0)
    c1=Vector(c1)
    c2=Vector(c2)
    
    v0=c1-c0
    v1=c2-c1
    
    sz, rot = readVec(v0)
    b = writeVec(w[0],rot-90)
    b = b + c0
    c = b + v0
    
    sz, rot = readVec(v1)
    d = writeVec(w[1],rot-90)
    d = d + c1
    e = d + v1    
    
    interlist = geometry.intersect_line_line(b,c,d,e)
    print(interlist)
    if type(interlist) != type(None) :
        return interlist[0]
    else :
        return c
