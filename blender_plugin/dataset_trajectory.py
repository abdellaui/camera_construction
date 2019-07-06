bl_info = {
    "name": "Camera Construct (dataset trajectory)",
    "description": "Camera Construct (dataset trajectory)",
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
def onUpdateTrajectorySettings(self, context):
    if  bpy.context and bpy.context.scene and bpy.context.scene.cursor_location:
        scene = bpy.context.scene
        settings = scene.dtSettings
        bpy.context.scene.cursor_location = settings.position
    DatasetTrajectoryManager.preview()
    return None

class DatasetTrajectoryManager:

    previewObj = None
    loaded = False
    pointArray = []

    @classmethod
    def makeGrid(cls, name="TrajectoryDataset"):
        scene = bpy.context.scene
        settings = scene.dtSettings
        currentPosition = settings.position
        
        bpy.ops.curve.primitive_nurbs_path_add(location=currentPosition)
        pathObj = bpy.context.object
        pathObj.name = name
        
        
        pathObj.data.splines.clear()
        polyline = pathObj.data.splines.new("NURBS")
        polyline.use_endpoint_u = True
        polyline.points.add(len(cls.pointArray)-1)
        print(cls.pointArray)
        # cant make a function: items at [i] are readonly, but props not
        for i, r in enumerate(cls.pointArray):
            polyline.points[i].co[0] = float(r[1]) * settings.scaleFactor.x
            polyline.points[i].co[1] = float(r[2]) * settings.scaleFactor.y
            polyline.points[i].co[2] = float(r[3]) * settings.scaleFactor.z
            polyline.points[i].co[3] = 1.0
            polyline.points[i].radius = 1.0
            polyline.points[i].tilt = 0.0
            polyline.points[i].weight = 1.0
            polyline.points[i].weight_softbody = 1.0
            
        # workaround
        polyline.use_bezier_u = True
        polyline.use_bezier_u = False
        return pathObj


    @classmethod
    def clearPreview(cls):
        if cls.previewObj:
            bpy.data.objects.remove(cls.previewObj)
            cls.previewObj = None

    @classmethod
    def preview(cls):
        # cls.clearPreview()
        if cls.loaded:
            cls.previewObj = cls.makeGrid()

    @classmethod
    def loadFile(cls):
        scene = bpy.context.scene
        settings = scene.dtSettings
        fp = bpy.path.abspath(settings.loadPath)
        stride = int(settings.stride)
        with open(fp) as csvfile:
            rdr = csv.reader(csvfile, delimiter=" ")
            count = -1
            for i, item in enumerate(rdr):
                count += 1
                if i < 3 or len(item) != 8 or count%stride != 0:
                    continue
                
                cls.pointArray.append(item)
            csvfile.close()
            cls.loaded = True
        

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------
class DatasetTrajectory(PropertyGroup):
    position = FloatVectorProperty(
        name="Position",
        description="Spawn position",        
        default = (0.0, 0.0, 0.0),
        subtype = "XYZ",
        size = 3,
        update = onUpdateTrajectorySettings
    )
    stride = IntProperty(
        name = "Stride",
        description="X-th data will be affect the NURB",
        default = 1,
        min = 1,
        update = onUpdateTrajectorySettings
    )
    scaleFactor = FloatVectorProperty(
        name="Scale factor",
        description="Scale factor",        
        default = (1.0, 1.0, 1.0),
        subtype = "XYZ",
        size = 3,
        update = onUpdateTrajectorySettings
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
    bl_idname = "sahin.transfer_position_trajectory_operator"
    bl_label = "Cursor position"

    @classmethod
    def poll(cls, context):
        return context and context.mode == "OBJECT" and bpy.context.scene and bpy.context.scene.cursor_location
    
    def execute(self, context):
        scene = context.scene
        settings = scene.dtSettings
        settings.position = bpy.context.scene.cursor_location
        DatasetTrajectoryManager.preview()
        return {"FINISHED"}


class GenerateTrajectoryOperator(Operator):
    bl_idname = "sahin.generate_trajectory_operator"
    bl_label = "Generate trajectory of dataset"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.dtSettings
        return context and bpy.context.scene and bpy.context.scene.cursor_location and os.path.exists(bpy.path.abspath(settings.loadPath))
    
    def execute(self, context):
        scene = context.scene
        settings = scene.dtSettings
        DatasetTrajectoryManager.loadFile()
        DatasetTrajectoryManager.preview()
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------    
    

class DatasetTrajectoryPanel(Panel):
    bl_idname = "sahin.dataset_trajector<_panel"
    bl_label = "Dataset Trajectory"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Camera Construct"

    @classmethod
    def poll(self,context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.dtSettings
        box = layout.box()

        box.prop(settings, "loadPath")
        row = box.row()
        row.prop(settings, "position")
        row.operator(TransferPositionDatasetOperator.bl_idname, icon="LOAD_FACTORY")
        
        box.prop(settings, "stride")
        row = box.row()
        row.prop(settings, "scaleFactor")
        
        row = box.row()  
        row.operator(GenerateTrajectoryOperator.bl_idname, icon="NORMALIZE_FCURVES")




# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.dtSettings = PointerProperty(type=DatasetTrajectory)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.dtSettings
    
if __name__ == "__main__":
    register()
