bl_info = {
    "name": "Camera Construct (dataset vizualizer)",
    "description": "Camera Construct (dataset vizualizer)",
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
def onUpdateVizualizerSettings(self, context):
    if  bpy.context and bpy.context.scene and bpy.context.scene.cursor_location:
        scene = bpy.context.scene
        settings = scene.dsSettings
        bpy.context.scene.cursor_location = settings.position
    DatasetVizualizerManager.preview()
    return None

class DatasetVizualizerManager:

    previewObj = None
    loaded = False
    pointArray = []

    @classmethod
    def makeGrid(cls, name="Root_CameraDataset"):
        scene = bpy.context.scene
        settings = scene.dsSettings
        currentPosition = settings.position
        sphereObj = bpy.data.objects.new(name, None)
        sphereObj.location = currentPosition
        sphereObj.empty_draw_size = 0.1
        sphereObj.empty_draw_type = "SPHERE"
        scene.objects.link(sphereObj)

        for i, r in enumerate(cls.pointArray):
            cameraName = r[0]
            camera = bpy.data.cameras.new(cameraName)
            
            camObj = bpy.data.objects.new(cameraName, camera)
            camObj.location.x += float(r[1])
            camObj.location.y += float(r[2])
            camObj.location.z += float(r[3])
            camObj.rotation_mode = 'QUATERNION'
            camObj.rotation_quaternion.w = float(r[4])
            camObj.rotation_quaternion.x = float(r[5])
            camObj.rotation_quaternion.y = float(r[6])
            camObj.rotation_quaternion.z = float(r[7])
            camObj.parent = sphereObj
            scene.objects.link(camObj)
        return sphereObj


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
            cls.previewObj = cls.makeGrid()

    @classmethod
    def loadFile(cls):
        scene = bpy.context.scene
        settings = scene.dsSettings
        fp = bpy.path.abspath(settings.loadPath)
        with open(fp) as csvfile:
            rdr = csv.reader(csvfile, delimiter=" ")
            for i, item in enumerate(rdr):
                if i < 3 or len(item) != 8:
                    continue
                
                cls.pointArray.append(item)
            csvfile.close()
            cls.loaded = True
        

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------
class DatasetSettings(PropertyGroup):
    position = FloatVectorProperty(
        name="Position",
        description="Spawn position",        
        default = (0.0, 0.0, 0.0),
        subtype = "XYZ",
        size = 3,
        update = onUpdateVizualizerSettings
    )
    loadPath = StringProperty(
        name="CSV File path",
        description="Absolute path to CSV file",
        default = "",
        subtype= "FILE_PATH"
    )

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class TransferPositionDatasetOperator(Operator):
    bl_idname = "sahin.transfer_position_dataset_operator"
    bl_label = "Cursor position"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and bpy.context.scene.cursor_location
    
    def execute(self, context):
        scene = context.scene
        settings = scene.dsSettings
        settings.position = bpy.context.scene.cursor_location
        DatasetVizualizerManager.preview()
        return {"FINISHED"}


class ShowDatasetOperator(Operator):
    bl_idname = "sahin.show_dataset_operator"
    bl_label = "Show dataset"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.dsSettings
        return context and bpy.context.scene and bpy.context.scene.cursor_location and os.path.exists(bpy.path.abspath(settings.loadPath))
    
    def execute(self, context):
        scene = context.scene
        settings = scene.dsSettings
        DatasetVizualizerManager.loadFile()
        DatasetVizualizerManager.preview()
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------    
    

class DatasetVizualizerPanel(Panel):
    bl_idname = "sahin.dataset_vizualizer_panel"
    bl_label = "Dataset Vizualizer"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Camera Construct"

    @classmethod
    def poll(self,context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.dsSettings
        box = layout.box()

        row = box.row()
        box.prop(settings, "loadPath")
        row.prop(settings, "position")
        row.operator(TransferPositionDatasetOperator.bl_idname, icon="LOAD_FACTORY")
        
        row = box.row()  
        row.operator(ShowDatasetOperator.bl_idname, icon="RESTRICT_VIEW_OFF")




# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.dsSettings = PointerProperty(type=DatasetSettings)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.dsSettings
    
if __name__ == "__main__":
    register()
