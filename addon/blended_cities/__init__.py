bl_info = {
    "name": "Blended Cities",
    "description": "reads a .pgn chess file and replays the game in the 3D view.",
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


'''
textFolder = os.path.dirname(bpy.data.texts['__init__.py'].filepath)
if textFolder not in sys.path :
    sys.path.insert(0, textFolder)
'''

def register() :
    main.register()

def unregister():
    main.unregister()


if __name__ != "__main__" :

    if "bpy" in locals():
        print('reload modules')
        import imp
        imp.reload(bin.main)
        #imp.reload(bin.main)
        
    else:
        print('load modules')
        import bpy
        from blended_cities.bin import  main

