import bpy

## returns an object or a list of objects
# @param ob 'all', 'active', 'selected', <object>, 'objectname'
# @return <object> , list of objects, or None
def returnObject(ob) :
    if type(ob) == str :
        if ob == 'all' : return bpy.context.scene.objects
        elif ob == 'active' : return bpy.context.active_object
        elif ob == 'selected' : return bpy.context.selected_objects
        else :
            try : return bpy.data.objects[object]
            except : return None
    return ob


def dprint(str,level=1) :
    city = bpy.context.scene.city
    if level <= city.debuglevel :
        print(str)


## remove an object from blender internal
def wipeOutObject(ob,and_data=True) :
    objs = returnObject(ob)
    if objs :
        if type(objs) == bpy.types.Object : objs = [objs]
        for ob in objs :
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

            try :
                print('  removing object %s...'%(ob.name)),
                bpy.data.objects.remove(ob)
                print('  done.')
            except : print('  failed. now named %s and unlinked'%ob.name)

            # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
            if and_data :
                wipeOutData(data)


## remove an object data from blender internal
def wipeOutData(data) :
    #print('%s has %s user(s) !'%(data.name,data.users))
    if data.users <= 0 :
        try :
            data.user_clear()
            print('  removing data %s...'%(data.name))
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
                print('  data still here : forgot %s type'%type(data))
            print('  done.')
        except :
            # empty, field
            print('%s has no user_clear attribute.'%data.name)
    else :
        print('  not done, %s has %s user'%(data.name,data.users))
