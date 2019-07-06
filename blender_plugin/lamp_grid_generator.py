bl_info = {
    "name": "Camera Construct (lamp grid generator)",
    "description": "Camera Construct (lamp grid generator)",
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
    if  bpy.context and bpy.context.scene and bpy.context.scene.cursor_location:
        scene = bpy.context.scene
        settings = scene.lgSettings
        bpy.context.scene.cursor_location = settings.position
    LampManager.preview()
    return None


class LampManager:

    previewObj = None

    @staticmethod
    def makeGrid(callback_fn, name="LampGrid"):
        scene = bpy.context.scene
        settings = scene.lgSettings
        currentPosition = settings.position
        factorL = -1 if settings.directionLayers else 1
        factorR = -1 if settings.directionRows else 1
        cubeObj = bpy.data.objects.new(name, None)
        cubeObj.location = currentPosition
        cubeObj.empty_draw_size = 0.4
        cubeObj.empty_draw_type = "CUBE"
        scene.objects.link(cubeObj)
        for l in range(settings.layers):
            layerCubeName = "LampLayer[{:03}]".format(l)
            layerCubeObj = bpy.data.objects.new(layerCubeName, None)
            layerCubeObj.empty_draw_size = 0.4
            layerCubeObj.empty_draw_type = "CUBE"
            layerCubeObj.location.z += l * settings.distanceLayers * factorL
            layerCubeObj.parent = cubeObj
            scene.objects.link(layerCubeObj)
            for r in range(settings.rows):
                rowCubeName = "LampRow[{:03}][{:03}]".format(l, r)
                rowCubeObj = bpy.data.objects.new(rowCubeName, None)
                rowCubeObj.empty_draw_size = 0.4
                rowCubeObj.empty_draw_type = "CUBE"
                rowCubeObj.location.x += r * settings.distanceRows * factorR
                rowCubeObj.parent = layerCubeObj
                scene.objects.link(rowCubeObj)

                for c in range(settings.cols):
                    callback_fn(cubeObj, layerCubeObj, rowCubeObj, l, r, c)
                    
        return cubeObj

    @staticmethod
    def createLamps(cubeObj, layerCubeObj, rowCubeObj, l, r, c):
        scene = bpy.context.scene
        settings = scene.lgSettings
        factor = -1 if settings.directionColumns else 1


        lampName = "Lamp[{:03}][{:03}][{:03}]".format(l ,r ,c)
        lamp = bpy.data.lamps.new(lampName, type = "POINT")
        lampObj = bpy.data.objects.new(lampName, lamp)
        lampObj.data.distance = 5.0
        # lampObj.data.use_sphere = True

        if settings.sampleOfLamp \
            and scene.objects[settings.sampleOfLamp] \
            and scene.objects[settings.sampleOfLamp].type == "LAMP":
            lampObj.data = scene.objects[settings.sampleOfLamp].data

        lampObj.parent = rowCubeObj
        lampObj.location.y += c * settings.distanceColumns * factor   
        scene.objects.link(lampObj)

    @staticmethod
    def previewLamps(cubeObj, layerCubeObj, rowCubeObj, l, r, c):
        scene = bpy.context.scene
        settings = scene.lgSettings
        factor = -1 if settings.directionColumns else 1
        
        colCubeName = "Lamp[{:03}][{:03}][{:03}]".format(l, r, c)
        colCubeObj = bpy.data.objects.new(colCubeName, None)
        colCubeObj.empty_draw_size = 0.4
        colCubeObj.empty_draw_type = "CUBE"
        colCubeObj.location.y += c * settings.distanceColumns * factor   
        colCubeObj.parent = rowCubeObj
        scene.objects.link(colCubeObj)

    @staticmethod
    def removeRecrusion(obj):
        if obj:
            for child in obj.children:
                LampManager.removeRecrusion(child)
            bpy.data.objects.remove(obj)
            
    @classmethod
    def clearPreview(cls):
        if cls.previewObj: 
            LampManager.removeRecrusion(cls.previewObj)
            cls.previewObj = None

    @classmethod
    def preview(cls):
        cls.clearPreview()
        cls.previewObj = LampManager.makeGrid(LampManager.previewLamps, "LampGridPreview")

    @classmethod
    def generate(cls):
        LampManager.makeGrid(LampManager.createLamps)

  

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------
class LampSettings(PropertyGroup):
    hasSampleOfLamp = BoolProperty(
        name="Custom configured lamp",
        description="Custom configured lamp",
        default = False
        )

    sampleOfLamp = StringProperty(
        name="Sample of lamp object",
        description="Sample or configured lamp object",
        default="",
        )
    position = FloatVectorProperty(
        name="Position",
        description="Spawn position",        
        default = (0.0, 0.0, 0.0),
        subtype = "XYZ",
        size = 3,
        update = onUpdateLampSettings
    )    
    layers = IntProperty(
        name = "Layers",
        description="Layers of grid",
        default = 1,
        min = 1,
        max = 100,
        update = onUpdateLampSettings
        )
    rows = IntProperty(
        name = "Rows",
        description="Rows per grid",
        default = 1,
        min = 1,
        max = 100,
        update = onUpdateLampSettings
        )
    cols = IntProperty(
        name = "Columns",
        description="Columns per grid",
        default = 1,
        min = 1,
        max = 100,
        update = onUpdateLampSettings
        )
    
    distanceLayers = FloatProperty(
        name = "Distance per layer",
        description = "Distance per layer",
        default = 5,
        min = 0.01,
        update = onUpdateLampSettings
        )
    
    distanceRows = FloatProperty(
        name = "Distance per row",
        description = "Distance per row",
        default = 5,
        min = 0.01,
        update = onUpdateLampSettings
        )

    distanceColumns = FloatProperty(
        name = "Distance per column",
        description = "Distance per column",
        default = 5,
        min = 0.01,
        update = onUpdateLampSettings
        )
    
    directionLayers = BoolProperty(
        name = "Flip direction",
        description = "Grow on the opposite direction",
        default = False,
        update = onUpdateLampSettings
    )
    
    directionRows = BoolProperty(
        name = "Flip direction",
        description = "Grow on the opposite direction",
        default = False,
        update = onUpdateLampSettings
        )

    directionColumns = BoolProperty(
        name = "Flip direction",
        description = "Grow on the opposite direction",
        default = False,
        update = onUpdateLampSettings
    )
    


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class GenerateLampOperator(Operator):
    bl_idname = "sahin.generate_lamp_operator"
    bl_label = "Generate lamp grid"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.lgSettings
        return context.mode == "OBJECT" and (not settings.hasSampleOfLamp or (settings.sampleOfLamp \
            and scene.objects[settings.sampleOfLamp] \
            and scene.objects[settings.sampleOfLamp].type == "LAMP"))
    
    def execute(self, context):
        LampManager.generate()
        return {"FINISHED"}


class TransferPositionLampOperator(Operator):
    bl_idname = "sahin.transfer_position_lamp_operator"
    bl_label = "Cursor position"

    @classmethod
    def poll(cls, context):
        return context and context.mode == "OBJECT" and bpy.context.scene and bpy.context.scene.cursor_location
    
    def execute(self, context):
        scene = context.scene
        settings = scene.lgSettings
        settings.position = bpy.context.scene.cursor_location
        return {"FINISHED"}

# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------    

class LampGridPanel(Panel):
    bl_idname = "sahin.lamp_grid_panel"
    bl_label = "Lamp Grid"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Camera Construct"
    # bl_context = "object"

    @classmethod
    def poll(self,context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.lgSettings
        box = layout.box()
        row = box.row()
        row.prop(settings, "hasSampleOfLamp")
        if settings.hasSampleOfLamp:
            row.prop_search(settings, "sampleOfLamp", scene, "objects")
        layout.separator()
        row = box.row()
        row.prop(settings, "position")
        row.operator(TransferPositionLampOperator.bl_idname, icon="LOAD_FACTORY")
        box.prop(settings, "layers")
        box.prop(settings, "rows")
        box.prop(settings, "cols")
        
        if settings.layers > 1:
            row = box.row()
            row.prop(settings, "distanceLayers")
            row.prop(settings, "directionLayers")
            
        if settings.rows > 1:
            row = box.row()
            row.prop(settings, "distanceRows")
            row.prop(settings, "directionRows")

        if settings.cols > 1:
            row = box.row()
            row.prop(settings, "distanceColumns")
            row.prop(settings, "directionColumns")
            
            
        row = box.row()  
        row.operator(GenerateLampOperator.bl_idname, icon="ZOOMIN")


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.lgSettings = PointerProperty(type=LampSettings)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.lgSettings
    
if __name__ == "__main__":
    register()
