bl_info = {
    "name": "Blended Cities",
    "description": "A city builder",
    "author": "Jerome Mahieux (Littleneo)",
    "version": (0, 1),
    "blender": (2, 5, 8),
    "api": 37702,
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
    "dependencies" : [ ['Script Events',(0,1)] ]
}
 
print('\n. %s addon init\n'% __name__)


if __name__ != "__main__" :

    if "bpy" in locals():
        print('\n. reload modules\n')
        import imp
        imp.reload(core.class_main)
        imp.reload(core.class_import)
        imp.reload(core.main)
        print()
    else:
        print('\n. load modules\n')
        import bpy
        from blended_cities.core.class_main import *
        from blended_cities.core.class_import import *
        from blended_cities.utils.meshes_io import *
        from blended_cities.core.ui import *
        from blended_cities.core.main import *
        print()

else :
    print('\n%s init as text\n'% __name__)
    print('\nNOT IMPLEMENTED :\n')
    poo()
 
    
def register() :
        # For now they need to be registered first due to: http://wiki.blender.org/index.php/Dev:2.5/Py/API/Overview#Manipulating-Classes
        # Maybe later we find another solution to be able to register builders later too?
        # builders :
        register_default_builders()

        #operators :
        bpy.utils.register_class(OP_BC_cityMethods)
        # ui
        bpy.utils.register_class(WM_OT_Panel_expand)
        bpy.utils.register_class(BC_City_ui)
        bpy.utils.register_class(OP_BC_Selector)
        bpy.utils.register_class(BC_main_panel)
        bpy.utils.register_class(BC_outlines_panel)
        #bpy.utils.register_class(BC_selector_panel)
        # class_main
        bpy.utils.register_class(BC_groups)
        bpy.utils.register_class(BC_builders)
        bpy.utils.register_class(BC_outlines)
        bpy.utils.register_class(BC_elements)
        bpy.utils.register_class(BlendedCities)

        bpy.types.Scene.city = bpy.props.PointerProperty(type=BlendedCities)
        #bpy.types.Scene.city.ui = bpy.props.PointerProperty(type=BC_City_ui)
        BlendedCities.builders = bpy.props.PointerProperty(type=BC_builders)
        items=[('niet','niet','')]
        for m in bpy.data.materials :
                items.append( (m.name,m.name,'') )
        BC_City_ui.matmenu = bpy.props.EnumProperty(items=items)

def unregister() :
    print('\n. %s addon unregister\n'% __name__)
    scene = bpy.data.scenes[0]
    module_name = 'blended_cities.builders'
    for m in dict(sys.modules) :
        if module_name + '.' == m[0:len(module_name) +1 ] :
            builder = m[len(module_name) +1:]+'.BC_'+m[len(module_name) +5:]
            exec('bpy.utils.unregister_class(builders.%s)'%builder)
            exec('bpy.utils.unregister_class(builders.%s_panel)'%builder)
            del sys.modules[m]
            print('\t%s unregistered'%builder)
    del bpy.types.Scene.city
    bpy.utils.unregister_class(BlendedCities)
    bpy.utils.unregister_class(BC_elements)
    bpy.utils.unregister_class(BC_outlines)
    bpy.utils.unregister_class(BC_builders)

    # ui
    bpy.utils.unregister_class(OP_BC_Selector)
    bpy.utils.unregister_class(BC_main_panel)
    bpy.utils.unregister_class(BC_outlines_panel)
    #bpy.utils.unregister_class(BC_selector_panel)
    bpy.utils.unregister_class(WM_OT_Panel_expand)
    bpy.utils.unregister_class(BC_City_ui)

    # operators
    bpy.utils.unregister_class(OP_BC_cityMethods)

    # permits to work on multifiles addons without having to restarts blender every 3 min.
    module_name = 'blended_cities'
    for m in dict(sys.modules) :
        if module_name + '.' == m[0:len(module_name) +1 ] :
            print('\tcleaning sys.module : %s'%(m[len(module_name) +1:]))
            del sys.modules[m]
    try : del sys.modules[module_name]
    except : print('\tcleaning sys module : %s missing ?'%module_name)






