# Physics Puppet Blender Addon
# Copyright (C) 2018 Pierre
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

#import blender python libraries
import bpy
import random
import math
import mathutils

#addon info read by Blender
bl_info = {
    "name": "Puppet Physics",
    "author": "Pierre",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "description": "Create proxies for rigid bodies for physics based character animation",
    "category": "Animation"
    }

#panel class for physics puppet menu items in object mode
class PHYPUP_PT_PuppetPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Physics Puppet'
    bl_context = 'objectmode'
    bl_category = 'Puppet Physics'

    def draw(self, context):
        self.layout.operator('phypup.makepuppet', text ='Create Puppet From Armature')
        self.layout.operator('phypup.makedriverarmature', text ='Create Driver Armature')
        
#panel class for rigid body related items in object mode
class PHYPUP_PT_RigidBodyPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Puppet Rigid Body'
    bl_context = 'objectmode'
    bl_category = 'Puppet Physics'
    bpy.types.Scene.PHYPUPStretchAmount = bpy.props.FloatProperty(name="Stretch Distance",description="Amount of stretch to allow when making links stretchy",default=1,min=0,max=1000)

    def draw(self, context):
        self.layout.operator('phypup.clearcache', text ='Force Clear Cache')
        self.layout.operator('phypup.makenarrower', text ='Make Narrower')
        self.layout.operator('phypup.makewider', text ='Make Wider')
        self.layout.operator('phypup.makelinksrigid', text ='Make Links Rigid')
        self.layout.operator('phypup.makelinksslack', text ='Make Links Slack')
        self.layout.operator('phypup.makelinksspringy', text ='Make Links Springy')
        self.layout.operator('phypup.makelinksfloppy', text ='Make Links Floppy')
        self.layout.prop(context.scene,"PHYPUPStretchAmount",slider=True)
        self.layout.operator('phypup.makelinksstretchy', text ='Make Links Stretchy')
        self.layout.operator('phypup.setfrictionhigh', text ='Set Friction High')
        self.layout.operator('phypup.setfrictionlow', text ='Set Friction Low')

#function to make a physics object thinner 
class PHYPUP_OT_MakeNarrower(bpy.types.Operator):
    bl_idname = "phypup.makenarrower"
    bl_label = "make a physics object narrower"
    bl_description = "edit a physics object to become narrower"
    
    def execute(self, context):
        if("PHYPUP_" in context.view_layer.objects.active.name):
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
            bpy.ops.transform.resize(value=(0.8,0.8,0.8),constraint_axis=(True,False,True),orient_type='LOCAL')
            bpy.ops.object.editmode_toggle()    
        return {'FINISHED'}

#function to make a physics object thinner 
class PHYPUP_OT_MakeWider(bpy.types.Operator):
    bl_idname = "phypup.makewider"
    bl_label = "make a physics object wider"
    bl_description = "edit a physics object to become wider"
    
    def execute(self, context):
        if("PHYPUP_" in context.view_layer.objects.active.name):
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
            bpy.ops.transform.resize(value=(1.25,1.25,1.25),constraint_axis=(True,False,True),orient_type='LOCAL')
            bpy.ops.object.editmode_toggle()    
        return {'FINISHED'}
    
#function to make a physics link rigid
class PHYPUP_OT_MakeLinksRigid(bpy.types.Operator):
    bl_idname = "phypup.makelinksrigid"
    bl_label = "make physics object links rigid"
    bl_description = "make the links rigid between the selected puppet handles and physics joints (good for head, torso and legs)"
    
    def setPhysConstraintValues(self,context,physObject):
        if(physObject.rigid_body_constraint != None):
            physObject.rigid_body_constraint.use_spring_ang_x = False
            physObject.rigid_body_constraint.use_spring_ang_y = False
            physObject.rigid_body_constraint.use_spring_ang_z = False
            physObject.rigid_body_constraint.use_limit_ang_x = False
            physObject.rigid_body_constraint.use_limit_ang_y = False
            physObject.rigid_body_constraint.use_limit_ang_z = False
            physObject.rigid_body_constraint.limit_lin_x_lower = 0
            physObject.rigid_body_constraint.limit_lin_y_lower = 0
            physObject.rigid_body_constraint.limit_lin_z_lower = 0
            physObject.rigid_body_constraint.limit_lin_x_upper = 0
            physObject.rigid_body_constraint.limit_lin_y_upper = 0
            physObject.rigid_body_constraint.limit_lin_z_upper = 0
        
    def setHandleConstraintValues(self,context,handleObject):
        if(handleObject.rigid_body_constraint != None):
            handleObject.rigid_body_constraint.use_limit_ang_x = True
            handleObject.rigid_body_constraint.use_limit_ang_y = True
            handleObject.rigid_body_constraint.use_limit_ang_z = True
            handleObject.rigid_body_constraint.use_spring_ang_x = True
            handleObject.rigid_body_constraint.use_spring_ang_y = True
            handleObject.rigid_body_constraint.use_spring_ang_z = True
            handleObject.rigid_body_constraint.limit_ang_x_lower = 0
            handleObject.rigid_body_constraint.limit_ang_y_lower = 0
            handleObject.rigid_body_constraint.limit_ang_z_lower = 0
            handleObject.rigid_body_constraint.limit_ang_x_upper = 0
            handleObject.rigid_body_constraint.limit_ang_y_upper = 0
            handleObject.rigid_body_constraint.limit_ang_z_upper = 0
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        #check through selected objects for physics puppet related physics objects
        for physCandidate in bpy.context.selected_objects:
            if("PHYPUP_" in physCandidate.name):
                #split name by underscores to access as tags
                physObjectTags = physCandidate.name.split("_")
                #get each handle for each physics object and each physics object for each handle so that all properties are changed appropriately
                if("phys" in physObjectTags):
                    self.setPhysConstraintValues(context,physCandidate)
                    linkedHandleObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_handle"
                    if(linkedHandleObjectName in sceneObjects):
                        self.setHandleConstraintValues(context,sceneObjects[linkedHandleObjectName])                 
                elif("handle" in physObjectTags):
                    self.setHandleConstraintValues(context,physCandidate)
                    linkedPhysObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_phys"
                    if(linkedPhysObjectName in sceneObjects):
                        self.setPhysConstraintValues(context,sceneObjects[linkedPhysObjectName])
        return {'FINISHED'}

#function to make a physics link slack
class PHYPUP_OT_MakeLinksSlack(bpy.types.Operator):
    bl_idname = "phypup.makelinksslack"
    bl_label = "make physics object links slack"
    bl_description = "make the link slack between the selected puppet handle and physics joint (good for arms)"
    
    def setPhysConstraintValues(self,context,physObject):
        if(physObject.rigid_body_constraint != None):
            physObject.rigid_body_constraint.use_spring_ang_x = False
            physObject.rigid_body_constraint.use_spring_ang_y = False
            physObject.rigid_body_constraint.use_spring_ang_z = False
            physObject.rigid_body_constraint.use_limit_ang_x = False
            physObject.rigid_body_constraint.use_limit_ang_y = False
            physObject.rigid_body_constraint.use_limit_ang_z = False
            physObject.rigid_body_constraint.limit_lin_x_lower = 0
            physObject.rigid_body_constraint.limit_lin_y_lower = 0
            physObject.rigid_body_constraint.limit_lin_z_lower = 0
            physObject.rigid_body_constraint.limit_lin_x_upper = 0
            physObject.rigid_body_constraint.limit_lin_y_upper = 0
            physObject.rigid_body_constraint.limit_lin_z_upper = 0
        
    def setHandleConstraintValues(self,context,handleObject):
        if(handleObject.rigid_body_constraint != None):
            handleObject.rigid_body_constraint.use_limit_ang_x = True
            handleObject.rigid_body_constraint.use_limit_ang_y = True
            handleObject.rigid_body_constraint.use_limit_ang_z = True
            handleObject.rigid_body_constraint.use_spring_ang_x = True
            handleObject.rigid_body_constraint.use_spring_ang_y = True
            handleObject.rigid_body_constraint.use_spring_ang_z = True
            handleObject.rigid_body_constraint.limit_ang_x_lower = -0.2
            handleObject.rigid_body_constraint.limit_ang_y_lower = -0.2
            handleObject.rigid_body_constraint.limit_ang_z_lower = -0.2
            handleObject.rigid_body_constraint.limit_ang_x_upper = 0.2
            handleObject.rigid_body_constraint.limit_ang_y_upper = 0.2
            handleObject.rigid_body_constraint.limit_ang_z_upper = 0.2
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        #check through selected objects for physics puppet related physics objects
        for physCandidate in bpy.context.selected_objects:
            if("PHYPUP_" in physCandidate.name):
                #split name by underscores to access as tags
                physObjectTags = physCandidate.name.split("_")
                #get each handle for each physics object and each physics object for each handle so that all properties are changed appropriately
                if("phys" in physObjectTags):
                    self.setPhysConstraintValues(context,physCandidate)
                    linkedHandleObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_handle"
                    if(linkedHandleObjectName in sceneObjects):
                        self.setHandleConstraintValues(context,sceneObjects[linkedHandleObjectName])                 
                elif("handle" in physObjectTags):
                    self.setHandleConstraintValues(context,physCandidate)
                    linkedPhysObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_phys"
                    if(linkedPhysObjectName in sceneObjects):
                        self.setPhysConstraintValues(context,sceneObjects[linkedPhysObjectName])
        return {'FINISHED'}
    
#function to make a physics link stretchy
class PHYPUP_OT_MakeLinksStretchy(bpy.types.Operator):
    bl_idname = "phypup.makelinksstretchy"
    bl_label = "make physics object links stretchy"
    bl_description = "add stretch to the selected physics objects"
    
    def setPhysConstraintValues(self,context,physObject):
        if(physObject.rigid_body_constraint != None):
            physObject.rigid_body_constraint.use_spring_y = False
            physObject.rigid_body_constraint.limit_lin_y_lower = -context.scene.PHYPUPStretchAmount
        
    def setHandleConstraintValues(self,context,handleObject):
        if(handleObject.rigid_body_constraint != None):
            handleObject.rigid_body_constraint.use_limit_ang_x = True
            handleObject.rigid_body_constraint.use_limit_ang_y = True
            handleObject.rigid_body_constraint.use_limit_ang_z = True
            handleObject.rigid_body_constraint.use_spring_ang_x = True
            handleObject.rigid_body_constraint.use_spring_ang_y = True
            handleObject.rigid_body_constraint.use_spring_ang_z = True
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        #check through selected objects for physics puppet related physics objects
        for physCandidate in bpy.context.selected_objects:
            if("PHYPUP_" in physCandidate.name):
                #split name by underscores to access as tags
                physObjectTags = physCandidate.name.split("_")
                #get each handle for each physics object and each physics object for each handle so that all properties are changed appropriately
                if("phys" in physObjectTags):
                    self.setPhysConstraintValues(context,physCandidate)
                    linkedHandleObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_handle"
                    if(linkedHandleObjectName in sceneObjects):
                        self.setHandleConstraintValues(context,sceneObjects[linkedHandleObjectName])                 
                elif("handle" in physObjectTags):
                    self.setHandleConstraintValues(context,physCandidate)
                    linkedPhysObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_phys"
                    if(linkedPhysObjectName in sceneObjects):
                        self.setPhysConstraintValues(context,sceneObjects[linkedPhysObjectName])
        return {'FINISHED'}

#function to make a physics link springy
class PHYPUP_OT_MakeLinksSpringy(bpy.types.Operator):
    bl_idname = "phypup.makelinksspringy"
    bl_label = "make physics object links springy"
    bl_description = "make the links springy between physics objects and handles to move like a spring (good for antennae)"
    
    def setPhysConstraintValues(self,context,physObject):
        if(physObject.rigid_body_constraint != None):
            physObject.rigid_body_constraint.use_spring_ang_x = False
            physObject.rigid_body_constraint.use_spring_ang_y = False
            physObject.rigid_body_constraint.use_spring_ang_z = False
            physObject.rigid_body_constraint.limit_lin_x_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_y_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_z_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_x_upper = 0.05
            physObject.rigid_body_constraint.limit_lin_y_upper = 0.05
            physObject.rigid_body_constraint.limit_lin_z_upper = 0.05
            physObject.rigid_body_constraint.use_limit_ang_x = False
            physObject.rigid_body_constraint.use_limit_ang_y = False
            physObject.rigid_body_constraint.use_limit_ang_z = False
            physObject.rigid_body_constraint.limit_ang_x_lower = -0.08
            physObject.rigid_body_constraint.limit_ang_y_lower = -0.08
            physObject.rigid_body_constraint.limit_ang_z_lower = -0.08
            physObject.rigid_body_constraint.limit_ang_x_upper = 0.08
            physObject.rigid_body_constraint.limit_ang_y_upper = 0.08
            physObject.rigid_body_constraint.limit_ang_z_upper = 0.08
            
        
    def setHandleConstraintValues(self,context,handleObject):
        if(handleObject.rigid_body_constraint != None):
            handleObject.rigid_body_constraint.use_limit_ang_x = True
            handleObject.rigid_body_constraint.use_limit_ang_y = True
            handleObject.rigid_body_constraint.use_limit_ang_z = True
            handleObject.rigid_body_constraint.limit_ang_x_lower = -1
            handleObject.rigid_body_constraint.limit_ang_y_lower = -1
            handleObject.rigid_body_constraint.limit_ang_z_lower = -1
            handleObject.rigid_body_constraint.limit_ang_x_upper = 1
            handleObject.rigid_body_constraint.limit_ang_y_upper = 1
            handleObject.rigid_body_constraint.limit_ang_z_upper = 1
            handleObject.rigid_body_constraint.use_spring_ang_x = True
            handleObject.rigid_body_constraint.use_spring_ang_y = True
            handleObject.rigid_body_constraint.use_spring_ang_z = True
            handleObject.rigid_body_constraint.spring_stiffness_ang_x = 1000
            handleObject.rigid_body_constraint.spring_stiffness_ang_y = 1000
            handleObject.rigid_body_constraint.spring_stiffness_ang_z = 1000
            handleObject.rigid_body_constraint.spring_damping_ang_x = 3
            handleObject.rigid_body_constraint.spring_damping_ang_y = 3
            handleObject.rigid_body_constraint.spring_damping_ang_z = 3
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        #check through selected objects for physics puppet related physics objects
        for physCandidate in bpy.context.selected_objects:
            if("PHYPUP_" in physCandidate.name):
                #split name by underscores to access as tags
                physObjectTags = physCandidate.name.split("_")
                #get each handle for each physics object and each physics object for each handle so that all properties are changed appropriately
                if("phys" in physObjectTags):
                    self.setPhysConstraintValues(context,physCandidate)
                    linkedHandleObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_handle"
                    if(linkedHandleObjectName in sceneObjects):
                        self.setHandleConstraintValues(context,sceneObjects[linkedHandleObjectName])                 
                elif("handle" in physObjectTags):
                    self.setHandleConstraintValues(context,physCandidate)
                    linkedPhysObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_phys"
                    if(linkedPhysObjectName in sceneObjects):
                        self.setPhysConstraintValues(context,sceneObjects[linkedPhysObjectName])
        return {'FINISHED'}

#function to nudge the physics timescale to clear the physics cache
class PHYPUP_OT_ClearCache(bpy.types.Operator):
    bl_idname = "phypup.clearcache"
    bl_label = "clear physics cache"
    bl_description = "clear physics cache by nudging the physics timescale"
    
    def execute(self, context):
        if(bpy.context.scene.rigidbody_world != None):
            bpy.context.scene.rigidbody_world.time_scale = bpy.context.scene.rigidbody_world.time_scale + 1
            bpy.context.scene.rigidbody_world.time_scale = bpy.context.scene.rigidbody_world.time_scale - 1
        return {'FINISHED'}

#function to make a physics link floppy
class PHYPUP_OT_MakeLinksFloppy(bpy.types.Operator):
    bl_idname = "phypup.makelinksfloppy"
    bl_label = "make physics object links floppy"
    bl_description = "make the links have no constraint between the selected puppet handles and physics joints, so that they move loosely (good for hair and accessories)"
    
    def setPhysConstraintValues(self,context,physObject):
        if(physObject.rigid_body_constraint != None):
            physObject.rigid_body_constraint.use_spring_ang_x = True
            physObject.rigid_body_constraint.use_spring_ang_y = True
            physObject.rigid_body_constraint.use_spring_ang_z = True
            physObject.rigid_body_constraint.use_limit_ang_x = False
            physObject.rigid_body_constraint.use_limit_ang_y = False
            physObject.rigid_body_constraint.use_limit_ang_z = False
            physObject.rigid_body_constraint.spring_stiffness_ang_x = 500
            physObject.rigid_body_constraint.spring_stiffness_ang_y = 500
            physObject.rigid_body_constraint.spring_stiffness_ang_z = 500
            physObject.rigid_body_constraint.spring_damping_ang_x = 1
            physObject.rigid_body_constraint.spring_damping_ang_y = 1
            physObject.rigid_body_constraint.spring_damping_ang_z = 1
            physObject.rigid_body_constraint.limit_lin_x_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_y_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_z_lower = -0.05
            physObject.rigid_body_constraint.limit_lin_x_upper = 0.05
            physObject.rigid_body_constraint.limit_lin_y_upper = 0.05
            physObject.rigid_body_constraint.limit_lin_z_upper = 0.05
        
    def setHandleConstraintValues(self,context,handleObject):
        if(handleObject.rigid_body_constraint != None):
            handleObject.rigid_body_constraint.use_limit_ang_x = False
            handleObject.rigid_body_constraint.use_limit_ang_y = False
            handleObject.rigid_body_constraint.use_limit_ang_z = False
            handleObject.rigid_body_constraint.use_spring_ang_x = False
            handleObject.rigid_body_constraint.use_spring_ang_y = False
            handleObject.rigid_body_constraint.use_spring_ang_z = False
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        #check through selected objects for physics puppet related physics objects
        for physCandidate in bpy.context.selected_objects:
            if("PHYPUP_" in physCandidate.name):
                #split name by underscores to access as tags
                physObjectTags = physCandidate.name.split("_")
                #get each handle for each physics object and each physics object for each handle so that all properties are changed appropriately
                if("phys" in physObjectTags):
                    self.setPhysConstraintValues(context,physCandidate)
                    linkedHandleObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_handle"
                    if(linkedHandleObjectName in sceneObjects):
                        self.setHandleConstraintValues(context,sceneObjects[linkedHandleObjectName])                 
                elif("handle" in physObjectTags):
                    self.setHandleConstraintValues(context,physCandidate)
                    linkedPhysObjectName = physObjectTags[0]+"_"+physObjectTags[1]+"_"+physObjectTags[2]+"_phys"
                    if(linkedPhysObjectName in sceneObjects):
                        self.setPhysConstraintValues(context,sceneObjects[linkedPhysObjectName])
        return {'FINISHED'}
    
#function to set high friction on selected physics objects
class PHYPUP_OT_SetFrictionHigh(bpy.types.Operator):
    bl_idname = "phypup.setfrictionhigh"
    bl_label = "set high friction on the selected physics objects"
    bl_description = "make the selected physics objects have high friction (good for hands and feet)"
    
    def execute(self, context):
        for physCandidate in bpy.context.selected_objects:
            if(physCandidate.rigid_body != None):
                physCandidate.rigid_body.friction = 999999
        return {'FINISHED'}
    
#function to set low friction on selected physics objects
class PHYPUP_OT_SetFrictionLow(bpy.types.Operator):
    bl_idname = "phypup.setfrictionlow"
    bl_label = "set low friction on the selected physics objects"
    bl_description = "make the selected physics objects have low friction (good for parts which need to move and slide easily)"
    
    def execute(self, context):
        for physCandidate in bpy.context.selected_objects:
            if(physCandidate.rigid_body != None):
                physCandidate.rigid_body.friction = 0.5
        return {'FINISHED'}

#function to create physics puppet controls for the currently selected armature
class PHYPUP_OT_CreateArmaturePuppet(bpy.types.Operator):
    bl_idname = "phypup.makepuppet"
    bl_label = "create physics puppet"
    bl_description = "set up physics and puppet handles for the selected armature"
    
    def setupCollection(self,context,newCollectionName):
        if(newCollectionName not in bpy.data.collections.keys()):
            bpy.ops.collection.create(name=newCollectionName)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.children.link(bpy.data.collections[newCollectionName])
            else:
                bpy.data.collections[context.collection.name].children.link(bpy.data.collections[newCollectionName])

    def assignToCollection(self,context,assignCollectionName,assignObject):
        if(assignObject.name not in bpy.data.collections[assignCollectionName].objects):
            bpy.data.collections[assignCollectionName].objects.link(assignObject)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.objects.unlink(assignObject)
            else:
                bpy.data.collections[context.collection.name].objects.unlink(assignObject)
    
    def execute(self, context):
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        handleOffsetDistance = 5
        sceneObjects = bpy.context.scene.objects
        #pick up armature from first in selection, make sure it is armature
        armatureObject = bpy.context.selected_objects[0]
        if armatureObject.type == 'ARMATURE':
            #create a collection
            self.setupCollection(context,"PHYPUPObjects_" + armatureObject.name)
            #create an initial rigid body to make sure that the rigid body world exists
            bpy.ops.mesh.primitive_cube_add(size=2)
            RigidBodyCube = bpy.context.selected_objects[0]
            bpy.ops.rigidbody.object_add()
            bpy.ops.object.delete(use_global=False, confirm=False)
            bpy.ops.object.select_all(action='DESELECT')
            armatureObject.select_set(True)
            context.view_layer.objects.active = armatureObject
            #configure the rigid body world
            bpy.context.scene.rigidbody_world.time_scale = 1.4
            bpy.context.scene.rigidbody_world.steps_per_second = 100
            bpy.context.scene.rigidbody_world.solver_iterations = 100
            bpy.context.scene.gravity = [0,0,-100]
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            bpy.ops.object.posemode_toggle()
            #option to force selection of all bones, disabled by comment
            #bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.object.editmode_toggle()
            for targetBone in bpy.context.selected_editable_bones:
                targetBone.use_connect = False
            #back into posemode to create the colliders for each bone
            bpy.ops.object.posemode_toggle()
            for targetBone in bpy.context.selected_pose_bones:
                bpy.ops.object.posemode_toggle()
                bpy.ops.mesh.primitive_plane_add(size = targetBone.length*0.3)
                bonePhysObject = bpy.context.selected_objects[0]
                #add rigid bodies to the PHYPUP collection
                self.assignToCollection(context,"PHYPUPObjects_" + armatureObject.name,bonePhysObject)
                #naming, scaling and parenting
                bonePhysObject.name = "PHYPUP_" + armatureObject.name + "_" + targetBone.name + "_phys"
                bpy.context.object.rotation_mode = 'QUATERNION'
                bonePhysObject.parent = armatureObject
                bonePhysObject.parent_type = 'BONE'
                bonePhysObject.parent_bone = targetBone.name
                bonePhysObject.location = [0,-targetBone.length,0]
                bpy.ops.object.editmode_toggle()
                bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='LOCAL', constraint_axis=(True, False, False))
                bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0,0,targetBone.length), "orient_type":'NORMAL', "constraint_axis":(False, False, True)})
                bpy.ops.object.editmode_toggle()
                #switch the parenting so that the bone follows the physics object
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                boneCopyTransforms = targetBone.constraints.new('COPY_TRANSFORMS')
                boneCopyTransforms.name = "PHYPUP_FollowPhysics"
                boneCopyTransforms.target = bonePhysObject
                #enable physics on the bone physics object
                bpy.ops.rigidbody.object_add()
                bonePhysObject.rigid_body.mass = 2
                bonePhysObject.rigid_body.mesh_source = 'FINAL'
                bonePhysObject.rigid_body.linear_damping = 0.7
                bonePhysObject.rigid_body.angular_damping = 1
                if(targetBone.parent != None):
                    bpy.ops.rigidbody.constraint_add()
                    bonePhysObject.rigid_body_constraint.type = 'GENERIC_SPRING'
                    bonePhysObject.rigid_body_constraint.use_spring_x = True
                    bonePhysObject.rigid_body_constraint.use_spring_y = True
                    bonePhysObject.rigid_body_constraint.use_spring_z = True
                    bonePhysObject.rigid_body_constraint.spring_stiffness_x = 3000
                    bonePhysObject.rigid_body_constraint.spring_stiffness_y = 3000
                    bonePhysObject.rigid_body_constraint.spring_stiffness_z = 3000
                    bonePhysObject.rigid_body_constraint.spring_damping_x = 3
                    bonePhysObject.rigid_body_constraint.spring_damping_y = 3
                    bonePhysObject.rigid_body_constraint.spring_damping_z = 3
                    bonePhysObject.rigid_body_constraint.use_limit_lin_x = True
                    bonePhysObject.rigid_body_constraint.use_limit_lin_y = True
                    bonePhysObject.rigid_body_constraint.use_limit_lin_z = True
                    bonePhysObject.rigid_body_constraint.limit_lin_x_lower = 0
                    bonePhysObject.rigid_body_constraint.limit_lin_y_lower = 0
                    bonePhysObject.rigid_body_constraint.limit_lin_z_lower = 0
                    bonePhysObject.rigid_body_constraint.limit_lin_x_upper = 0
                    bonePhysObject.rigid_body_constraint.limit_lin_y_upper = 0
                    bonePhysObject.rigid_body_constraint.limit_lin_z_upper = 0
                    bonePhysObject.rigid_body_constraint.object1 = bonePhysObject
                    bonePhysObject.hide_render = True
                #set up physics control handle proxy
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'},TRANSFORM_OT_translate={"value":(handleOffsetDistance,0,0)})
                physHandleObject = bpy.context.selected_objects[0]
                physHandleObject.name = "PHYPUP_" + armatureObject.name + "_" + targetBone.name + "_handle"
                physHandleObject.rigid_body.type = 'PASSIVE'
                physHandleObject.rigid_body.kinematic = True
                bpy.ops.rigidbody.constraint_add()
                physHandleObject.rigid_body_constraint.type = 'GENERIC_SPRING'
                physHandleObject.rigid_body_constraint.use_spring_x = False
                physHandleObject.rigid_body_constraint.use_spring_y = False
                physHandleObject.rigid_body_constraint.use_spring_z = False
                physHandleObject.rigid_body_constraint.use_spring_ang_x = True
                physHandleObject.rigid_body_constraint.use_spring_ang_y = True
                physHandleObject.rigid_body_constraint.use_spring_ang_z = True
                physHandleObject.rigid_body_constraint.spring_stiffness_ang_x = 3000
                physHandleObject.rigid_body_constraint.spring_stiffness_ang_y = 3000
                physHandleObject.rigid_body_constraint.spring_stiffness_ang_z = 3000
                physHandleObject.rigid_body_constraint.spring_damping_ang_x = 3
                physHandleObject.rigid_body_constraint.spring_damping_ang_y = 3
                physHandleObject.rigid_body_constraint.spring_damping_ang_z = 3
                physHandleObject.rigid_body_constraint.use_limit_ang_x = True
                physHandleObject.rigid_body_constraint.use_limit_ang_y = True
                physHandleObject.rigid_body_constraint.use_limit_ang_z = True
                physHandleObject.rigid_body_constraint.use_limit_lin_x = False
                physHandleObject.rigid_body_constraint.use_limit_lin_y = False
                physHandleObject.rigid_body_constraint.use_limit_lin_z = False
                physHandleObject.rigid_body_constraint.limit_ang_x_lower = -0.2
                physHandleObject.rigid_body_constraint.limit_ang_y_lower = -0.2
                physHandleObject.rigid_body_constraint.limit_ang_z_lower = -0.2
                physHandleObject.rigid_body_constraint.limit_ang_x_upper = 0.2
                physHandleObject.rigid_body_constraint.limit_ang_y_upper = 0.2
                physHandleObject.rigid_body_constraint.limit_ang_z_upper = 0.2
                physHandleObject.rigid_body_constraint.object1 = bonePhysObject
                physHandleObject.rigid_body_constraint.object2 = physHandleObject
                physHandleObject.hide_render = True
            #fix missing constraints for branching parent physics objects
            for potentialPhysObject in sceneObjects:
                if("PHYPUP_" in potentialPhysObject.name and "_phys" in potentialPhysObject.name and armatureObject.name in potentialPhysObject.name):
                    targetBone = armatureObject.data.bones[potentialPhysObject.name.split("_")[2]]
                    if(targetBone.parent != None):
                        potentialPhysObject.rigid_body_constraint.object2 = sceneObjects["PHYPUP_" + armatureObject.name + "_" + targetBone.parent.name + "_phys"]
            #create an armature to control the physics handles
            handleArmature = armatureObject.copy()
            handleArmature.data = armatureObject.data.copy()
            handleArmature.name = "PHYPUP_" + armatureObject.name + "_HandleArmature"
            bpy.context.collection.objects.link(handleArmature)
            self.assignToCollection(context,"PHYPUPObjects_" + armatureObject.name,handleArmature)
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = handleArmature
            handleArmature.location[0] = handleArmature.location[0] + handleOffsetDistance
            handleArmature.show_in_front = True
            bpy.ops.object.posemode_toggle()
            for targetBone in bpy.context.selected_pose_bones:
                targetBone.constraints.remove(targetBone.constraints["PHYPUP_FollowPhysics"])
                boneHandleObject = sceneObjects["PHYPUP_" + armatureObject.name + "_" + targetBone.name + "_handle"]
                boneHandleObject.parent = handleArmature
                boneHandleObject.parent_type = 'BONE'
                boneHandleObject.parent_bone = targetBone.name
                boneHandleObject.location = [0,-targetBone.length,0]
                boneHandleObject.rotation_quaternion = [1,0,0,0]
            bpy.ops.object.posemode_toggle()
            #optionally, simplify can be turned off after processing
            #context.scene.render.use_simplify = False
        return {'FINISHED'}
    
#function to create a duplicate of the puppet armature with a driver object for realtime action blending
class PHYPUP_OT_CreateDriverArmature(bpy.types.Operator):
    bl_idname = "phypup.makedriverarmature"
    bl_label = "create driver armature"
    bl_description = "create a copy of the armature with drivers to affect the influence on the original armature"
    
    def setupCollection(self,context,newCollectionName):
        if(newCollectionName not in bpy.data.collections.keys()):
            bpy.ops.collection.create(name=newCollectionName)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.children.link(bpy.data.collections[newCollectionName])
            else:
                bpy.data.collections[context.collection.name].children.link(bpy.data.collections[newCollectionName])

    def assignToCollection(self,context,assignCollectionName,assignObject):
        if(assignObject.name not in bpy.data.collections[assignCollectionName].objects):
            bpy.data.collections[assignCollectionName].objects.link(assignObject)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.objects.unlink(assignObject)
            else:
                bpy.data.collections[context.collection.name].objects.unlink(assignObject)
    
    def execute(self, context):   
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        #pick up armature from first in selection, make sure it is armature
        armatureObject = bpy.context.selected_objects[0]
        #create a collection
        self.setupCollection(context,"PHYPUPDriverArmatures_" + armatureObject.name)
        if armatureObject.type == 'ARMATURE':
            #create a duplicate armature which can control the original using a driver
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False,"mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(5,0,0)})
            driverArmature = bpy.context.selected_objects[0]
            driverArmature.name = "PHYPUP_" + armatureObject.name + "_DriverArmature"
            self.assignToCollection(context,"PHYPUPDriverArmatures_" + armatureObject.name,driverArmature)
            driverArmature.location[0] = driverArmature.location[0] + 5
            driverArmature.show_in_front = True
            bpy.ops.object.posemode_toggle()
            #clear constraints in bones so that duplicate driven armatures don't control each other
            bpy.ops.pose.select_all(action='SELECT')
            for targetBone in bpy.context.selected_pose_bones:
                for constraintToRemove in targetBone.constraints:
                    targetBone.constraints.remove(constraintToRemove)
            bpy.ops.object.posemode_toggle()   
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=False, location=driverArmature.location)
            driverEmptyObject = bpy.context.selected_objects[0]
            #add driver empty to the PHYPUP collection
            self.assignToCollection(context,"PHYPUPDriverArmatures_" + armatureObject.name,driverEmptyObject)
            driverEmptyObject.name = "PHYPUP_" + armatureObject.name + "_DriverArmatureEmpty"
            driverEmptyObject.location = [driverEmptyObject.location[0] + 5,driverEmptyObject.location[1],0]
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = armatureObject
            bpy.ops.object.posemode_toggle()
            #create rotation constraints driven by the driver empty object
            for targetBone in bpy.context.selected_pose_bones:
                boneCopyRotation = targetBone.constraints.new('COPY_ROTATION')
                boneCopyRotation.name = "PHYPUP_CopyRotationDriven"
                boneCopyRotation.target = driverArmature
                boneCopyRotation.subtarget = targetBone.name
                boneCopyRotation.target_space = 'LOCAL'
                boneCopyRotation.owner_space = 'LOCAL'
                copyRotationDriver = boneCopyRotation.driver_add("influence")
                copyRotationDriver.driver.expression = "PHYPUPDriverVar * 0.05"
                rotationDriverVar = copyRotationDriver.driver.variables.new()
                rotationDriverVar.name = "PHYPUPDriverVar"
                rotationDriverVar.type = 'TRANSFORMS'
                rotationDriverVar.targets[0].transform_type = 'LOC_Z'
                rotationDriverVar.targets[0].id = driverEmptyObject
            bpy.ops.object.posemode_toggle()
        #optionally, simplify can be turned off after processing
        #context.scee.render.use_simplify = False
        return {'FINISHED'}
             
#register and unregister all Physics Puppet classes
phypupClasses = (  PHYPUP_PT_PuppetPanel,
                    PHYPUP_PT_RigidBodyPanel,
                    PHYPUP_OT_CreateArmaturePuppet,
                    PHYPUP_OT_MakeNarrower,
                    PHYPUP_OT_MakeWider,
                    PHYPUP_OT_MakeLinksRigid,
                    PHYPUP_OT_MakeLinksSlack,
                    PHYPUP_OT_MakeLinksSpringy,
                    PHYPUP_OT_MakeLinksFloppy,
                    PHYPUP_OT_SetFrictionLow,
                    PHYPUP_OT_SetFrictionHigh,
                    PHYPUP_OT_CreateDriverArmature,
                    PHYPUP_OT_ClearCache,
                    PHYPUP_OT_MakeLinksStretchy)

register, unregister = bpy.utils.register_classes_factory(phypupClasses)

#allow debugging for this addon in the Blender text editor
if __name__ == '__main__':
    register()
