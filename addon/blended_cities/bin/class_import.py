import bpy
from blended_cities.bin.class_main import *

# ########################################################
# set of generic update functions used in builder classes
# ########################################################

# this link to the build() method of the current class
def updateBuild(self,context='') :
    self.build(True)


# ###################################################################
# from now we can search and register the standalone builders modules
# ###################################################################

def register_Builders(builders_list) :

    builders_class = 'class BC_builders(bpy.types.PropertyGroup) :\n'

    for b in builders_list :
        
        exec('bpy.utils.register_class(%s)'%b.__name__)
        builders_class += '    %s = bpy.props.CollectionProperty(type=%s)\n'%(b.__name__[3:],b.__name__)
    print(builders_class)
    exec(builders_class,globals())

# load the builders
# for file in dir x...
from blended_cities.builders.buildings_class import *
from blended_cities.builders.buildings_ui import *
bpy.utils.register_class(BC_buildings_panel)

builders_list  = [BC_buildings]

register_Builders(builders_list)


bpy.utils.register_class(BC_builders)

'''
def register() :
    bpy.utils.register_class(BC_outlines)
    bpy.utils.register_class(BC_elements)

def unregister() :
    # for classname in builders_list, exec..
    bpy.utils.unregister_class(BC_buildings)

    bpy.utils.unregister_class(BC_builders)
    bpy.utils.unregister_class(BC_outlines)
    bpy.utils.unregister_class(BC_elements)

    
if __name__ == '__main__' :
    register()
'''