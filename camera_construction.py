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
class DotDict(dict):
    # dot.notation access to dictionary attributes
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    
class Utils:    
    @staticmethod
    def lenghtOfMesh(obj):
        length = 0
        if obj and obj.type == "CURVE":
            mesh = obj.to_mesh(bpy.context.scene, False, "PREVIEW")
            obj = bpy.data.objects.new("HIYARI", mesh)
            bpy.context.scene.objects.link(obj) 
            ve = mesh.vertices
            for i in mesh.edges:
                distance = ve[i.vertices[0]].co - ve[i.vertices[1]].co
                length += distance.length
            length = round(length,4)       
            # bpy.data.meshes.remove(mesh)
        return length
    
    @staticmethod
    def lenghtOfPath(obj):
        length = 0
        if obj and obj.type == "CURVE":
            mesh = obj.to_mesh(bpy.context.scene, False, "PREVIEW")
            ve = mesh.vertices
            for i in mesh.edges:
                distance = ve[i.vertices[0]].co - ve[i.vertices[1]].co
                length += distance.length
            length = round(length,4)       
            bpy.data.meshes.remove(mesh)
        return length

    @staticmethod
    def rotationInDegToRad(x=0, y=0, z=0):
        return (math.radians(x), math.radians(y), math.radians(z))

    @staticmethod
    def objectExists(obj):
        return obj and (obj.name in bpy.data.objects) 

    @staticmethod
    def generatateGroundTruthString(fileName, location, quaternion):
        x, y ,z = location
        w, p, q, r = quaternion
        return "{}.png {} {} {} {} {} {} {}".format(fileName, x,y,z,w,p,q,r)
    
    
class CameraConstruct:
    def __init__(self, cameras = [], pathObj = None, cubeObj = None):
        self.cameras = cameras
        self.pathObj = pathObj # holds the path
        self.cubeObj = cubeObj # holds the cameracuberoot element
        self.pathLength = 0;

    @staticmethod
    def generate(currentPosition = (0, 0, 0)):
        instance = CameraConstruct()
        # create path
        bpy.ops.curve.primitive_nurbs_path_add(location=currentPosition)
        instance.pathObj = bpy.context.object
        instance.pathObj.name = "CameraConstruct"

        # create cube
        bpy.ops.object.empty_add(type="CUBE", radius=0.2)
        instance.cubeObj = bpy.context.object
        instance.cubeObj.name = "CameraRootCube"

        instance.select()

        # the active object will be the parent of all selected object
        bpy.context.scene.objects.active = instance.pathObj
        bpy.ops.object.parent_set(type="FOLLOW")

        # correct the rotation and location of cubeObj inclusive cameras
        instance.cubeObj.location.x -= 2
        instance.createCameras()
        instance.configure()
        return instance;

    def selectSplinePoint(self, index):
        bpy.ops.curve.select_all(action="DESELECT")
        self.pathObj.data.splines[0].points[index].select = True
        
    def changeSpline(self, points):
        self.pathObj.data.splines.clear()
        polyline = self.pathObj.data.splines.new("NURBS")
        polyline.use_endpoint_u = True
        polyline.points.add(len(points)-1)
        
        # cant make a function: items at [i] are readonly, but props not
        for i, source in enumerate(points):
            polyline.points[i].co = source.co
            polyline.points[i].radius = source.radius
            polyline.points[i].tilt = source.tilt
            polyline.points[i].weight = source.weight
            polyline.points[i].weight_softbody = source.weight_softbody
        # workaround
        polyline.use_bezier_u = True
        polyline.use_bezier_u = False
        self.calcPathLength()
             
    def copyPathPoints(self, path):
        
        
        # if path is same path, so copy all points, changeSpline removes points (points are refs)
        points = list(path.data.splines[0].points)
        if path == self.pathObj:
            pointsHolder = []
            for source in points:
                copyPoint = {
                    "co" : source.co.copy(),
                    "radius" : source.radius,
                    "tilt" : source.tilt,
                    "weight" : source.weight,
                    "weight_softbody" : source.weight_softbody
                }
                
                pointsHolder.append(DotDict(copyPoint))
            points = pointsHolder
                
        self.changeSpline(points)
        
    def uiToPointList(self):
        scene = bpy.context.scene
        points = list(scene.listOfPoints)
        self.changeSpline(points)
    
    def pointListToUI(self):
        scene = bpy.context.scene
        scene.listIndex = 0
        points = list(self.pathObj.data.splines[0].points)
        scene.listOfPoints.clear()
        
        # doesnt support add(amount)
        for i in range(len(points)):
            scene.listOfPoints.add()
            
        # cant make a function: items at [i] are readonly, but props not
        for i, source in enumerate(points):
            scene.listOfPoints[i].co = source.co
            scene.listOfPoints[i].radius = source.radius
            scene.listOfPoints[i].tilt = source.tilt
            scene.listOfPoints[i].weight = source.weight
            scene.listOfPoints[i].weight_softbody = source.weight_softbody
        
    
    def getPathLength(self):
        return self.pathLength;

    def getName(self):
        if self.pathObj and self.pathObj.name:
            return self.pathObj.name
        else:
            return ""

    def isValid(self):
        return Utils.objectExists(self.pathObj) and Utils.objectExists(self.cubeObj) and len(self.cameras) > 0


    def select(self):
        bpy.ops.object.select_all(action="DESELECT") 
        self.pathObj.select = True
        self.cubeObj.select = True
    
    def addCamera(self, x=0, y=0, z=0):
        scene = bpy.context.scene
        settings = scene.ccSettings
        cameraName = "Camera_x{}_y{}_z{}".format(x, y, z)
        print("Created: " + cameraName)

        camera = bpy.data.cameras.new(cameraName)
        obj = bpy.data.objects.new(cameraName, camera)
        
        # if sample of configured camera is setted, so copy configuration
        if settings.sampleOfCamera and scene.objects[settings.sampleOfCamera] and scene.objects[settings.sampleOfCamera].type == "CAMERA":
            obj.data = scene.objects[settings.sampleOfCamera].data

        obj.location = (0, 0, 0) # relative to cube
        obj.rotation_mode = "ZYX"
        obj.rotation_euler = Utils.rotationInDegToRad(x,y,z)
        obj.rotation_mode = "QUATERNION"
        obj.parent = self.cubeObj

        scene.objects.link(obj)     # add camera to scene
        self.cameras.append(obj)
        
    def createCameras(self):
        scene = bpy.context.scene
        settings = scene.ccSettings
        allowsAxes = list(settings.variationOfAxes)
        steps = settings.steps
        stepSize = settings.stepSize
        stepRange = steps*stepSize
        allowX = allowsAxes[0]
        allowY = allowsAxes[1]
        allowZ = allowsAxes[2]
        for x in range(-stepRange, stepRange+1, stepSize):
            if x == 0 or allowX:
                for y in range(-stepRange, stepRange+1, stepSize):
                    if y == 0 or allowY:
                        for z in range(-stepRange, stepRange+1, stepSize):
                            if z == 0 or allowZ:
                                self.addCamera(x, y, z)
    
               
    def calcPathLength(self):
        self.pathLength = Utils.lenghtOfPath(self.pathObj)
        
    def configureCubeRotation(self):
        if not self.cubeObj or not self.pathObj:
            return 0

        usePathFollow = self.pathObj.data.use_path_follow 
        
        self.cubeObj.rotation_mode = "ZYX"
        if(usePathFollow):
            self.cubeObj.rotation_euler = Utils.rotationInDegToRad(y = -90, z = -90)
        else:
            self.cubeObj.rotation_euler = Utils.rotationInDegToRad(x = 90, y = 180)
            
    def configure(self):
        scene = bpy.context.scene
        settings = scene.ccSettings
        usePathFollow = settings.usePathFollow
        
        self.pathObj.data.path_duration = ConstructManager.keypoints
        self.pathObj.data.use_path_follow = usePathFollow
        self.configureCubeRotation()
        self.calcPathLength()
        
class ConstructManager:
    sceneKey = None

    records = False
    iteratesOverCams = False
    canChangePointList = False
    
    keypoints = 0
    currentFrame = 0
    file = None # holds the file handler
    pathToStore = ""

    lastPointIndex = -1
    
    cc = CameraConstruct()


    @classmethod
    def setCenterCamera(cls):
        index = int(len(cls.cc.cameras)/2);
        bpy.data.scenes[cls.sceneKey].camera = cls.cc.cameras[index]   

    @classmethod
    def stopRecord(cls):
        if cls.file:
            cls.file.close()
            cls.file = None
        cls.records = False
        bpy.ops.screen.animation_cancel()
        
    @classmethod
    def startRecord(cls):
        cls.file = open( os.path.join(bpy.path.abspath(cls.pathToStore), "data.txt"), "w+")
        cls.currentFrame = 0
        cls.records = True 
        cls.resetFrameSettings()
        bpy.ops.screen.animation_cancel()
        bpy.ops.screen.animation_play() 
    
    @classmethod
    def takePictures(cls, location):
        print("Taking pictures...")
        print("Using Scene[{}]".format(cls.sceneKey))

        amount = len(cls.cc.cameras) * cls.keypoints

        cls.iteratesOverCams = True
        for obj in cls.cc.cameras:
            cls.currentFrame += 1

            print("{}% \t\t {:06} / {:06}".format(round(cls.currentFrame/amount*100,2), cls.currentFrame, amount))
            fileName = "{:06}".format(cls.currentFrame)
            fileName = os.path.join("img", fileName)
            groundtruth = Utils.generatateGroundTruthString(fileName, location, obj.rotation_quaternion)
            cls.file.write(groundtruth+"\n")

            # set scenes camera and output filename
            bpy.data.scenes[cls.sceneKey].camera = obj
            bpy.data.scenes[cls.sceneKey].render.image_settings.file_format = "PNG"
            bpy.data.scenes[cls.sceneKey].render.filepath = os.path.join(cls.pathToStore, fileName)

            # render scene and store the scene
            bpy.ops.render.render( write_still = True )
        cls.iteratesOverCams = False
        print("Done for location: {}".format(location))

    @classmethod
    def reinitalize(cls):
        scene = bpy.context.scene
        settings = scene.ccSettings
        obj = settings.currentConstruct

        if obj and scene.objects[obj]:
            _pathObj = scene.objects[obj]
            # first obj is a curve and has childrens
            if _pathObj.type == "CURVE" and _pathObj.data.use_path and len(_pathObj.children) > 0:
                _cubeObj = _pathObj.children[0]
                # second obj is an empty and has childrens
                if _cubeObj.type == "EMPTY" and len(_cubeObj.children) > 0:
                    _cameras = _cubeObj.children
                    # third obj is a camera and has childrens
                    if _cameras[0].type == "CAMERA":
                        cls.reset()
                        cls.cc = CameraConstruct(list(_cameras), _pathObj, _cubeObj)
                        # for better vizualisation
                        cls.cc.select()
                        cls.cc.pointListToUI()

                        return ("Information", "Construct initilized")
                    else:
                        return ("Error", "No cameras aviable")
                else:
                    return ("Error", "CameraRootCube is missing")
            else:
                return ("Error", "Construct object doesnt seems similar an acceptable construct!")
        else:
            return ("Error", "Object doesnt exists!")

        
    @classmethod
    def generate(cls):
        currentPosition = bpy.context.scene.cursor_location
        return CameraConstruct.generate(currentPosition) 

    @classmethod
    def applySettings(cls):
        scene = bpy.context.scene
        settings = scene.ccSettings
        usePathFollow = settings.usePathFollow
        picturePerUnit = settings.picturePerUnit
        cls.cc.configure()
        pathLength = cls.cc.getPathLength()
        cls.keypoints = math.ceil(pathLength / picturePerUnit)
        cls.pathToStore = settings.pathToStore
        
    @classmethod
    def resetFrameSettings(cls):
        cls.cc.pathObj.data.eval_time = 0
        bpy.data.scenes[cls.sceneKey].frame_start = 0
        bpy.data.scenes[cls.sceneKey].frame_end = cls.keypoints

        

    @classmethod
    def reset(cls):
        if cls.file:
            cls.file.close()
        cls.file = None
        cls.pathToStore = ""
        cls.cc = CameraConstruct()
        cls.records = False
        cls.iteratesOverCams = False
        cls.canChangePointList = False
        cls.keypoints = 0
        cls.currentFrame = 0
        cls.sceneKey = bpy.data.scenes.keys()[0]
        cls.lastPointIndex = -1

    @classmethod
    def canTakePictures(cls):
        if cls.records:
            return False
        elif not cls.cc.isValid():
            cls.reset()
            return False
        else:
            return True

def ShowMessageBox(message = "", title = "Message Box", icon = "INFO"):
    
    def draw(self, context):
        self.layout.label(message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


@persistent
def onFrameChanged(scene):
    # on iterating over all cams frame changed get triggered :s
    if ConstructManager.iteratesOverCams and scene.camera:
        return 0

    if scene.frame_current <= ConstructManager.keypoints:
        if len(ConstructManager.cc.cameras) > 0:
            if ConstructManager.records:
                ConstructManager.setCenterCamera()
                if scene.camera:
                    print("Frame in progress {}".format(scene.frame_current))
                    # get current position, workaround via scene camera
                    location, *_ = scene.camera.matrix_world.decompose()
                    ConstructManager.takePictures(location)
    
    # cancel / stop animation after finishing
    if scene.frame_current >= ConstructManager.keypoints:
        ConstructManager.stopRecord()
        
    return None

def onPointListChange(self, context):
    if ConstructManager.canChangePointList:
        ConstructManager.cc.uiToPointList()
        ConstructManager.applySettings()
    return None

def onUpdateSettings(self, context):
    ConstructManager.applySettings()
    return None


def onChangeConstruct(self, context):
    scene = context.scene
    settings = scene.ccSettings
    title, message = ConstructManager.reinitalize()

    ShowMessageBox(message, title)
    if title == "Error":
        ConstructManager.reset()
    else:
        ConstructManager.applySettings()
    return None


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class PanelSettings(PropertyGroup):


    hasSampleOfCamera = BoolProperty(
        name="Custom configured camera",
        description="Custom configured camera",
        default = False
        )

    sampleOfCamera = StringProperty(
        name="Sample of camera object",
        description="Sample or configured camera object",
        default="",
        )

    currentConstruct = StringProperty(
        name="Current construct",
        description="Current construct",
        default="",
        update = onChangeConstruct
        )

    steps = IntProperty(
        name = "Rotation variation",
        description="Steps of the rotation variation in each x, y, z axes, centered on zero and mirrored",
        default = 1,
        min = 0,
        max = 180
        )

    stepSize = IntProperty(
        name = "Step size in angles",
        description="Stepsize in angles for variation of the cameras rotation",
        default = 10,
        min = 1,
        max = 180
        )

    variationOfAxes = BoolVectorProperty(
        name = "Varying axes",
        description="Shows axes wich will get varying rotations",
        default = (False, True, True),
        subtype = "XYZ"
        )

    picturePerUnit = FloatProperty(
        name = "Distance in units of length",
        description = "Distance of each pictures in units of length",
        default = 0.05,
        min = 0.01,
        update = onUpdateSettings
        )

    usePathFollow = BoolProperty(
        name="Path rotation follow",
        description="Camera construct follows the rotation on the path",
        default = False,
        update = onUpdateSettings
        )

    pathToStore = StringProperty(
        name="Path to store",
        description="Absolute path to store the pictures and ground truth",
        default = "",
        subtype= "DIR_PATH",
        update = onUpdateSettings
        )

     
    tabBar = EnumProperty(
        name="Options",
        description="Select between construct generation or selecting an existing construct",
        items=[ ("OP1", "Generate", ""),
                ("OP2", "Select", ""),
               ],
        default = "OP1"
        )

# ------------------------------------------------------------------------

class ListItem(PropertyGroup):
    
    co = FloatVectorProperty(
        name="Co",
        description="Point coordinates",        
        default = (0.0, 0.0, 0.0, 1.0),
        subtype = "XYZ",
        size = 4,
        update = onPointListChange
        )

    
    radius = FloatProperty(
        name = "Radius",
        description = "Radius for beveling",
        default = 1.0,
        min = 0.0,
        update = onPointListChange
        )
    
    tilt = FloatProperty(
        name = "Tilt",
        description = "Tilt in 3D View",
        default = 0.0,
        min = -376.991,
        max = 376.991,
        update = onPointListChange
        )
    
    weight = FloatProperty(
        name = "Weight",
        description = "NURBS weight",
        default = 1.0,
        update = onPointListChange
        )
    
    weight_softbody = FloatProperty(
        name = "Weight softbody",
        description = "Softbody goal weight",
        default = 1.0,
        min = 0.01,
        max = 100,
        update = onPointListChange
        )
    
# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class GenerateConstructOperator(Operator):
    bl_idname = "sahin.generate_construct_operator"
    bl_label = "Generate camera construct"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        scene = context.scene
        settings = scene.ccSettings

        _cc = ConstructManager.generate()
        settings.tabBar = "OP2"

        settings.currentConstruct = _cc.getName()

        
        return {"FINISHED"}

class RenderImagesAndSaveOperator(Operator):
    bl_idname = "sahin.render_images_and_save_operator"
    bl_label = "Render images and save"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        settings = scene.ccSettings
        return ConstructManager.canTakePictures() and ConstructManager.pathToStore

    def execute(self, context):
        ConstructManager.startRecord()
        return {"FINISHED"}

# Point list

class ListNewItem(Operator):
    bl_idname = "sahin.list_new_item"
    bl_label = "Add"

    def execute(self, context):
        context.scene.listOfPoints.add()
        onPointListChange(self, context)
        return{"FINISHED"}


class ListDeleteItem(Operator):
    bl_idname = "sahin.list_delete_item"
    bl_label = "Delete"

    @classmethod
    def poll(cls, context):
        return len(context.scene.listOfPoints)>1

    def execute(self, context):
        my_list = context.scene.listOfPoints
        index = context.scene.listIndex
        
        my_list.remove(index)
        context.scene.listIndex = min(max(0, index - 1), len(my_list) - 1)
        onPointListChange(self, context)
        return{"FINISHED"}

class ListMoveItem(Operator):
    bl_idname = "sahin.list_move_item"
    bl_label = "Move"

    direction = EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", "")))

    @classmethod
    def poll(cls, context):
        return len(context.scene.listOfPoints)>1

    def move_index(self):
        index = bpy.context.scene.listIndex
        list_length = len(bpy.context.scene.listOfPoints) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == "UP" else 1)

        bpy.context.scene.listIndex = max(0, min(new_index, list_length))

    def execute(self, context):
        my_list = context.scene.listOfPoints
        index = context.scene.listIndex

        neighbor = index + (-1 if self.direction == "UP" else 1)
        my_list.move(neighbor, index)
        self.move_index()
        onPointListChange(self, context)
        return{"FINISHED"}
    
class ListLoadCurve(Operator):
    bl_idname = "sahin.list_load_curve"
    bl_label = "Load"

    @classmethod
    def poll(cls, context):
        return context.object \
                and context.object.type == "CURVE" \
                and context.object.data.splines[0] \
                and context.object.data.splines[0].type == "NURBS" \
                and context.object.data.splines[0].use_endpoint_u == True

    def execute(self, context):
        ConstructManager.canChangePointList = False
        ConstructManager.cc.copyPathPoints(context.object)
        ConstructManager.cc.pointListToUI()
        return{"FINISHED"}
    
# ------------------------------------------------------------------------
#    List
# ------------------------------------------------------------------------    
class PointList(UIList): 
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        cicon = "DOT"
        if self.layout_type in {"DEFAULT", "COMPACT"}: 
            row = layout.row()
            row.prop(item, "co")
        elif self.layout_type in {"GRID"}: 
            layout.alignment = "CENTER" 
            layout.label("", icon = cicon) 

# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------    

class CameraConstructPanel(Panel):
    bl_idname = "sahin.camera_construct_panel"
    bl_label = "Camera Construct Panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Camera Construct"

    @classmethod
    def poll(self,context):
        return context.scene is not None

    
    def drawGeneration(self,context,box):
        layout = self.layout
        scene = context.scene
        settings = scene.ccSettings
        
        row = box.row()
        row.prop(settings, "hasSampleOfCamera")
        if settings.hasSampleOfCamera:
            row.prop_search(settings, "sampleOfCamera", scene, "objects")
        layout.separator()
        row = box.row()
        row.prop(settings, "variationOfAxes")
        if settings.variationOfAxes[0] or settings.variationOfAxes[1] or settings.variationOfAxes[2]:
            box.prop(settings, "steps")
            if settings.steps > 0:
                box.prop(settings, "stepSize")
        box.operator(GenerateConstructOperator.bl_idname, icon="ZOOMIN")
       
    def drawSelection(self ,context, box):
        layout = self.layout
        scene = context.scene
        settings = scene.ccSettings

        box.prop_search(settings, "currentConstruct", scene, "objects")

        if ConstructManager.cc and ConstructManager.cc.isValid():
            self.drawInformation(context, box)
            self.drawCurvePoints(context)

    def drawInformation(self, context, box):
        amountOfPictures = (ConstructManager.keypoints)*len(ConstructManager.cc.cameras)
    
        row = box.row()
        row.label(text="{} cameras".format(len(ConstructManager.cc.cameras)), icon="CAMERA_DATA")
        row.label(text="{} path length (length unit)".format(ConstructManager.cc.getPathLength()), icon="CURVE_PATH")
        row = box.row()
        row.label(text="{} keypoints".format(ConstructManager.keypoints), icon="SPACE2")
        row.label(text="{} total images".format(amountOfPictures), icon="IMAGE_DATA")


    def drawCurvePoints(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        box.label(text="Path controll point edit", icon="IPO_ELASTIC")
        row = box.row()
        row.operator(ListNewItem.bl_idname, icon="ZOOMIN")
        row.operator(ListDeleteItem.bl_idname, icon="X")
        row.operator(ListMoveItem.bl_idname, icon="TRIA_UP").direction = "UP"
        row.operator(ListMoveItem.bl_idname, icon="TRIA_DOWN").direction = "DOWN"
        row.operator(ListLoadCurve.bl_idname, icon="LOAD_FACTORY")
        box.template_list("PointList", "point_list", scene,
                          "listOfPoints", scene, "listIndex")


        
        if scene.listIndex >= 0 and scene.listOfPoints:
            
            # on selecting a point on the list, it will select it on the edit 3d view
            changed = ConstructManager.lastPointIndex - scene.listIndex 
            if changed != 0:
                ConstructManager.canChangePointList = True
                ConstructManager.lastPointIndex = scene.listIndex
                if context.mode == "EDIT_CURVE":
                    ConstructManager.cc.selectSplinePoint(scene.listIndex)
                
            item = scene.listOfPoints[scene.listIndex]
            layout.separator()
            box.label(text="Expanded controll point edit", icon="RECOVER_AUTO")
            row = box.row()
            row.prop(item, "co")
            box.prop(item, "radius")
            box.prop(item, "tilt")
            box.prop(item, "weight")
            box.prop(item, "weight_softbody")
            
    def drawRenderOptions(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ccSettings
        
        amountOfPictures = (ConstructManager.keypoints)*len(ConstructManager.cc.cameras)
        
        box = layout.box()

        box.label(text="Render options")
        if not ConstructManager.records:
            box.prop(settings, "picturePerUnit")
            box.prop(settings, "usePathFollow")
            box.prop(settings, "pathToStore")
        else:
            box.label(text="{}%  {} / {}".format(round(ConstructManager.currentFrame/amountOfPictures*100,2), ConstructManager.currentFrame, amountOfPictures), icon="SCRIPT")
        box.operator(RenderImagesAndSaveOperator.bl_idname, icon="RENDER_STILL")
        
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.ccSettings



        box = layout.box()
        
        row = box.row()
        row.prop(settings, "tabBar", expand=True)
        if settings.tabBar == "OP1":
            self.drawGeneration(context, box)
        else:
            self.drawSelection(context, box)
            
        if ConstructManager.cc.isValid():
            self.drawRenderOptions(context)




# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.ccSettings = PointerProperty(type=PanelSettings)
    bpy.types.Scene.listOfPoints = CollectionProperty(type = ListItem)
    bpy.types.Scene.listIndex = IntProperty(name = "Index for listOfPoints", default = 0)
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(onFrameChanged)

    
def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.ccSettings
    del bpy.types.Scene.listOfPoints
    del bpy.types.Scene.listIndex
    
if __name__ == "__main__":
    register()