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
 
print('\n%s init addon\n'% __name__)


if __name__ != "__main__" :
    #print('\nlocal :\n')
    #for i in dict(locals()) :
    #    if 'BC_' in i : print(i)
    # never used finally
    if "bpy" in locals():
        print('\nreload modules\n')
        import imp
        imp.reload(core.class_main)
        #imp.reload(core.class_import)
        imp.reload(core.main)
          
    else:
        print('\nload modules\n')
        import bpy
        from blended_cities.core.class_main import *
        #from blended_cities.core.class_import import *
        from blended_cities.utils.meshes_io import *
        from blended_cities.core.ui import *
        from blended_cities.core.main import *
    #print('\nnew local :\n')
    #for i in dict(locals()) :
    #    if 'BC_' in i : print(i)
else :
    print('\n%s init as text\n'% __name__)
    print('\nNOT IMPLEMENTED :\n')
    poo()
 

def register() :
        #operators :
        register_default_builders()
        bpy.utils.register_class(OP_BC_cityMethods)
        bpy.utils.register_class(OP_BC_buildinglist)
        bpy.utils.register_class(OP_BC_buildingBuild)
        bpy.utils.register_class(OP_BC_buildingWipe)
        bpy.utils.register_class(OP_BC_buildersMethods)
        # ui
        bpy.utils.register_class(OP_BC_Selector)
        bpy.utils.register_class(BC_main_panel)
        bpy.utils.register_class(BC_outlines_panel)
        # class_main
        bpy.utils.register_class(BC_builders)
        bpy.utils.register_class(BC_outlines)
        bpy.utils.register_class(BC_elements)
        bpy.utils.register_class(BlendedCities)
        #bpy.utils.register_module(__name__,True)
        
        bpy.types.Scene.city = bpy.props.PointerProperty(type=BlendedCities)



def unregister() :
    print('\n%s init unregister\n'% __name__)
    scene = bpy.data.scenes[0]
#    module_name = 'blended_cities.builders'
#    for m in dict(sys.modules) :
#        if module_name + '.' == m[0:len(module_name) +1 ] and '_class' in m :
#            builder = 'BC_'+m[len(module_name) +1:].split('_')[0] #
#            exec('bpy.utils.unregister_class(%s)'%builder)
#            exec('bpy.utils.unregister_class(%s_panel)'%builder)
#            print('  %s unregistered'%builder)
    del bpy.types.Scene.city
    bpy.utils.unregister_class(BlendedCities)
    bpy.utils.unregister_class(BC_elements)
    bpy.utils.unregister_class(BC_outlines)
    bpy.utils.unregister_class(BC_builders)

    # ui
    bpy.utils.unregister_class(OP_BC_Selector)
    bpy.utils.unregister_class(BC_main_panel)
    bpy.utils.unregister_class(BC_outlines_panel)

    # operators
    bpy.utils.unregister_class(OP_BC_cityMethods)
    bpy.utils.unregister_class(OP_BC_buildinglist)
    bpy.utils.unregister_class(OP_BC_buildingBuild)
    bpy.utils.unregister_class(OP_BC_buildingWipe)
    bpy.utils.unregister_class(OP_BC_buildersMethods)

    # triggers imp.reload() when usepref is on focus
    #    bpy.types.USERPREF_PT_addons._addons_fake_modules['blended_cities'].__time__ = 0


    # the module way
    '''
    for builder in scene.city.builders.builders_list.split(' ') :
        print(builder)
        cls = 'blended_cities.builders.%s_class'%builder[3:]
        ui    = 'blended_cities.builders.%s_ui'%builder[3:]
        clsmod = sys.modules[cls]
        uimod  = sys.modules[ui]
        bpy.utils.unregister_module(clsmod,True)
        bpy.utils.unregister_module(uimod,True)
    bpy.utils.unregister_module(blended_cities.core.class_import,True)
    bpy.utils.unregister_module(blended_cities.core.class_main,True)
    bpy.utils.unregister_module(blended_cities.core.ui,True)
    bpy.utils.unregister_module(blended_cities.core.main,True)
    bpy.utils.unregister_module(blended_cities.core,True)
    bpy.utils.unregister_module(blended_cities,True)
    bpy.utils.unregister_module(__name__,True)
    '''





