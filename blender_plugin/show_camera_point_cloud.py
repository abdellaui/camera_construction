bl_info = {
    "name": "Camera Construct",
    "description": "Camera Construct",
    "author": "Abdullah Sahin",
    "version": (0, 0, 2),
    "blender": (2, 79, 0),
    "location": "3D View > Tools > Camera Construct",
    "category": "Render"
}


import bpy
import math
import os
import csv
from datetime import datetime

from bpy.app.handlers import persistent

from bpy.props import (StringProperty,
                       BoolProperty,
                       BoolVectorProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty,
                       FloatVectorProperty
                       )
from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       UIList,
                       SplinePoint
                       )


# ------------------------------------------------------------------------
#    Classes & Functions
# ------------------------------------------------------------------------
def onUpdateLampSettings(self, context):
    PointManager.preview()
    return None

class PointManager:

    previewObj = None
    loaded = False
    pointArray = []

    @classmethod
    def makeGrid(cls, name="PointPath"):
        scene = bpy.context.scene
        settings = scene.ppSettings
        currentPosition = settings.position
        cubeObj = bpy.data.objects.new(name, None)
        cubeObj.location = currentPosition
        cubeObj.empty_draw_size = 0.1
        cubeObj.empty_draw_type = "SPHERE"
        scene.objects.link(cubeObj)

        for i, r in enumerate(cls.pointArray):
            rowCubeName = "LampRow[{:03}]".format(i)
            rowCubeObj = bpy.data.objects.new(rowCubeName, None)
            rowCubeObj.empty_draw_size = 0.1
            rowCubeObj.empty_draw_type = "CUBE"
            rowCubeObj.location.x += float(r[0])
            rowCubeObj.location.y += float(r[1])
            rowCubeObj.location.z += float(r[2])
            rowCubeObj.parent = cubeObj
            scene.objects.link(rowCubeObj)
        return cubeObj


    @classmethod
    def clearPreview(cls):
        if cls.previewObj:
            for child in cls.previewObj.children:
                for childchild in child.children:
                    bpy.data.objects.remove(childchild)
                bpy.data.objects.remove(child)
            bpy.data.objects.remove(cls.previewObj)
            cls.previewObj = None

    @classmethod
    def preview(cls):
        cls.clearPreview()
        if cls.loaded:
            cls.previewObj = cls.makeGrid("PointPath")

    @classmethod
    def loadFile(cls):
        scene = bpy.context.scene
        settings = scene.ppSettings
        fp = bpy.path.abspath(settings.loadPath)
        with open(fp) as csvfile:
            rdr = csv.reader(csvfile, delimiter=" ")
            for item in rdr:
                cls.pointArray.append(item)
            csvfile.close()
            cls.loaded = True
        

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------
class LampSettings(PropertyGroup):
    position = FloatVectorProperty(
        name="Position",
        description="Spawn position",        
        default = (0.0, 0.0, 0.0),
        subtype = "XYZ",
        size = 3,
        update = onUpdateLampSettings
    )
    loadPath = StringProperty(
        name="Load csv from",
        description="Absolute path from loading csv",
        default = "",
        subtype= "FILE_PATH"
    )

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class PreviewPointOperator(Operator):
    bl_idname = "sahin.preview_point_operator"
    bl_label = "Preview point path"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.ppSettings
        return context.mode == "OBJECT"
    
    def execute(self, context):
        PointManager.preview()
        return {"FINISHED"}


class LoadFilePointOperator(Operator):
    bl_idname = "sahin.transfer_position_position_operator"
    bl_label = "Cursor position"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.ppSettings
        return context and bpy.context.scene and bpy.context.scene.cursor_location and os.path.exists(bpy.path.abspath(settings.loadPath))
    
    def execute(self, context):
        scene = context.scene
        settings = scene.ppSettings
        PointManager.loadFile()
        PointManager.preview()
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------    
    

class PointPathPanel(Panel):
    bl_idname = "sahin.point_path_panel"
    bl_label = "Point Path Panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Camera Construct"

    @classmethod
    def poll(self,context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ppSettings
        box = layout.box()

        row = box.row()
        box.prop(settings, "loadPath")
        row.prop(settings, "position")
        row.operator(PreviewPointOperator.bl_idname, icon="LOAD_FACTORY")
        
        row = box.row()  
        row.operator(LoadFilePointOperator.bl_idname, icon="ZOOMIN")




# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.ppSettings = PointerProperty(type=LampSettings)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.ppSettings
    
if __name__ == "__main__":
    register()
