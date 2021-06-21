# Reciprocal Rigid Rig Blender Addon
# Copyright (C) 2021 Pierre
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
import math
import mathutils

#addon info read by Blender
bl_info = {
    "name": "Reciprocal Rigid Rig",
    "author": "Pierre",
    "version": (0, 0, 1),
    "blender": (2, 92, 0),
    "description": "Add rigid bodies to a rig to create whole body movement effects",
    "category": "Animation"
    }

#panel class for Reciprocal Rigid Rig setup menu items in object mode
class RECRIG_PT_SetupPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Reciprocal Rigid Rig Setup'
    bl_context = 'objectmode'
    bl_category = 'Reciprocal Rigid Rig'
    bpy.types.Scene.RECRIGFix = bpy.props.BoolProperty(name="Apply Scale & Clear Underscores",description="Apply armature scale and remove underscores from bone names for rigs that have these features",default=False)

    def draw(self, context):
        self.layout.prop(context.scene,"RECRIGFix")
        self.layout.operator('recrig.addtorig', text ='Add Effect To Selected Armatures')
        self.layout.operator('recrig.removefromrig', text ='Remove Effect From Selected')
     
#panel class for rigid body tweaking
class RECRIG_PT_TweakingPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Rigid Body Tweaking'
    bl_context = 'objectmode'
    bl_category = 'Reciprocal Rigid Rig'

    def draw(self, context):
        self.layout.operator('recrig.setstrong', text ='Set Strong Constraints on Selected')
        self.layout.operator('recrig.setflexible', text ='Set Flexible Constraints on Selected')
        self.layout.operator('recrig.setfloppy', text ='Set Floppy Constraints on Selected')
     
   
#panel class for animation utilities
class RECRIG_PT_AnimationPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Rigid Body Animation Utilities'
    bl_context = 'objectmode'
    bl_category = 'Reciprocal Rigid Rig'

    def draw(self, context):
        self.layout.operator('recrig.clearcache', text ='Clear Cached Rigid Body Animation')

#function to remove physics objects and constraints from rig
class RECRIG_OT_RemoveFromRig(bpy.types.Operator):
    bl_idname = "recrig.removefromrig"
    bl_label = "Remove reciprocal rigid rig effect"
    bl_description = "Remove rigid bodies and constraints from the armatures associated with the selected objects"
    
    def execute(self, context):
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        #recrig requires objects and armatures to be visible
        bpy.context.space_data.show_object_viewport_armature = True
        bpy.context.space_data.show_object_viewport_mesh = True
        sceneObjects = bpy.context.scene.objects
        #iterate all selected objects and clear all recrig related data
        for potentialRecrigObjectNumber in range(len(bpy.context.selected_objects)):
            #only attempt to process an object if it still exists
            if(potentialRecrigObjectNumber < len(bpy.context.selected_objects)):
                potentialRecrigObject = bpy.context.selected_objects[potentialRecrigObjectNumber]
                #begin by assuming selected is the original armature
                originalArmature = potentialRecrigObject
                #if selected has recrig underscore naming then second underscored part of name should be the armature name
                if("recrig_" in potentialRecrigObject.name):
                    recrigSplitName = potentialRecrigObject.name.split("_")[1]
                    if(recrigSplitName in sceneObjects):
                        originalArmature = sceneObjects[recrigSplitName]
                #proceed if there is a suitably named collection
                recrigCollectionName = "recrigObjects_" + originalArmature.name
                if(recrigCollectionName in bpy.data.collections):
                    bpy.ops.object.select_all(action='DESELECT')
                    recrigCollectionObjects = bpy.data.collections[recrigCollectionName].objects
                    for collectionObject in recrigCollectionObjects:
                        collectionObject.hide_viewport = False
                        collectionObject.select_set(True)
                    originalArmature.select_set(False)
                    bpy.ops.object.delete(use_global=False,confirm=False)
                    bpy.data.collections.remove(bpy.data.collections[recrigCollectionName])
        return {'FINISHED'}

#function to create physics objects and constraints
class RECRIG_OT_AddToRig(bpy.types.Operator):
    bl_idname = "recrig.addtorig"
    bl_label = "Add reciprocal rigid rig effect"
    bl_description = "Set up rigid bodies and constraints to enable reciprocal rigid rig effect for the selected armatures"
    
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
        sceneObjects = bpy.context.scene.objects
        #recrig requires objects and armatures to be visible
        bpy.context.space_data.show_object_viewport_armature = True
        bpy.context.space_data.show_object_viewport_mesh = True
        #iterate through all selected objects and make sure they are armatures
        for potentialArmature in bpy.context.selected_objects:
            if potentialArmature.type == 'ARMATURE':
                #don't apply effect to this armature if it appears to already have the effect applied
                originalArmatureSplitName = potentialArmature.name
                if("recrig_" in potentialArmature.name and "_controlrig" in potentialArmature.name):
                    originalArmatureSplitName = potentialArmature.name.split("_")[1]
                if("recrigObjects_" + potentialArmature.name in bpy.data.collections or "recrig_" in potentialArmature.name):
                    self.report({'WARNING'}, '\'' + originalArmatureSplitName + '\' may already have reciprocal rigid rig applied. Please use \'Remove Effect From Selected\' on \'' + originalArmatureSplitName + '\' if you wish to reapply reciprocal rigid rig.')
                else:
                    armatureObject = potentialArmature
                    #apply scale and remove underscores in a rig that has these features
                    if(context.scene.RECRIGFix == True):
                        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                        #remove underscores from armature and bone names, recrig uses underscores
                        armatureObject.name = armatureObject.name.replace("_","")
                        for targetBone in armatureObject.data.bones:
                            targetBone.name = targetBone.name.replace("_","")
                    #create a collection
                    recrigCollectionName = "recrigObjects_" + armatureObject.name
                    self.setupCollection(context,recrigCollectionName)
                    #create an initial rigid body to make sure that the rigid body world exists
                    bpy.ops.mesh.primitive_cube_add(size=2)
                    RigidBodyCube = bpy.context.selected_objects[0]
                    bpy.ops.rigidbody.object_add()
                    bpy.ops.object.delete(use_global=False, confirm=False)
                    #configure the rigid body world
                    bpy.context.scene.rigidbody_world.time_scale = 1.3
                    bpy.context.scene.rigidbody_world.substeps_per_frame = 10
                    bpy.context.scene.rigidbody_world.solver_iterations = 20
                    bpy.context.scene.gravity = [0,0,-50]
                    #turn off autokey
                    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
                    #select armature and duplicate to create control rig
                    bpy.ops.object.select_all(action='DESELECT')
                    armatureObject.select_set(True)
                    context.view_layer.objects.active = armatureObject
                    bpy.ops.object.duplicate()
                    controlArmature = bpy.context.selected_objects[0]
                    controlArmature.name = "recrig_" + armatureObject.name + "_controlrig"
                    #clear all constraints
                    bpy.ops.object.posemode_toggle()
                    bpy.ops.pose.select_all(action='SELECT')
                    bpy.ops.pose.constraints_clear()
                    #set up passive rigid bodies for control rig
                    for targetBone in bpy.context.selected_pose_bones:
                        bpy.ops.object.posemode_toggle()
                        bpy.ops.mesh.primitive_plane_add(size = targetBone.length*0.1)
                        boneHandleObject = bpy.context.selected_objects[0]
                        #add rigid bodies to the recrig collection
                        self.assignToCollection(context,recrigCollectionName,boneHandleObject)
                        #naming, scaling and parenting
                        boneHandleObject.name = "recrig_" + armatureObject.name + "_" + targetBone.name + "_handle"
                        bpy.context.object.rotation_mode = 'QUATERNION'
                        boneHandleObject.parent = controlArmature
                        boneHandleObject.parent_type = 'BONE'
                        boneHandleObject.parent_bone = targetBone.name
                        #important that this is at the end of the bone, it will serve as a pivot point
                        boneHandleObject.location = [0,-targetBone.length,0]
                        #edit plane to be handle sized
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X', orient_type='LOCAL', constraint_axis=(True, False, False))
                        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0,0,targetBone.length/4), "orient_type":'NORMAL', "constraint_axis":(False, False, True)})
                        bpy.ops.object.editmode_toggle()
                        #enable passive rigid body on handle
                        bpy.ops.rigidbody.object_add()
                        boneHandleObject.rigid_body.type = 'PASSIVE'
                        boneHandleObject.rigid_body.kinematic = True
                        #make handle not collide with objects in collection 0 by placing it in collection 1
                        boneHandleObject.rigid_body.collision_collections[1] = True
                        boneHandleObject.rigid_body.collision_collections[0] = False
                        boneHandleObject.hide_render = True
                        
                    
                    #return to editing physics affected rig by selecting it
                    bpy.ops.object.select_all(action='DESELECT')
                    armatureObject.select_set(True)
                    context.view_layer.objects.active = armatureObject
                    #enter pose mode
                    #bpy.ops.object.posemode_toggle()
                    #option to force selection of all bones when in pose mode, disabled by comment
                    #bpy.ops.pose.select_all(action='SELECT')
                    bpy.ops.object.editmode_toggle()
                    for targetBone in bpy.context.selected_editable_bones:
                        targetBone.use_connect = False
                    #back into posemode to create the rigid bodies for each bone
                    bpy.ops.object.posemode_toggle()
                    for targetBone in bpy.context.selected_pose_bones:
                        bpy.ops.object.posemode_toggle()
                        bpy.ops.mesh.primitive_plane_add(size = targetBone.length*0.3)
                        bonePhysObject = bpy.context.selected_objects[0]
                        #add rigid bodies to the recrig collection
                        self.assignToCollection(context,"recrigObjects_" + armatureObject.name,bonePhysObject)
                        #naming, scaling and parenting
                        bonePhysObject.name = "recrig_" + armatureObject.name + "_" + targetBone.name + "_phys"
                        bpy.context.object.rotation_mode = 'QUATERNION'
                        bonePhysObject.parent = armatureObject
                        bonePhysObject.parent_type = 'BONE'
                        bonePhysObject.parent_bone = targetBone.name
                        bonePhysObject.location = [0,-targetBone.length,0]
                        
                        #edit plane to become bone length
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X', orient_type='LOCAL', constraint_axis=(True, False, False))
                        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0,0,-targetBone.length), "orient_type":'NORMAL', "constraint_axis":(False, False, True)})
                        bpy.ops.object.editmode_toggle()
                        
                        #create vertex group to bring bone to bottom of mesh and keep origin in place
                        bonePosVertGroup = bonePhysObject.vertex_groups.new(name="bonePos")
                        bonePosVertGroup.add([4,5,6,7],1,'REPLACE')
                        
                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='MEDIAN')
                        bonePhysObject.location = [0,-targetBone.length/2,0]
                        
                        #switch the parenting so that the bone follows the physics object
                        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                        #use existing constraints if they are available
                        boneCopyLocation = None
                        if ("recrig_FollowLocation" in targetBone.constraints):
                            boneCopyLocation = targetBone.constraints["recrig_FollowLocation"]
                        else:
                            boneCopyLocation = targetBone.constraints.new('COPY_LOCATION')
                            boneCopyLocation.name = "recrig_FollowLocation"
                        boneCopyLocation.target = bonePhysObject
                        boneCopyLocation.subtarget = "bonePos"
                        boneCopyRotation = None
                        if ("recrig_FollowRotation" in targetBone.constraints):
                            boneCopyRotation = targetBone.constraints["recrig_FollowRotation"]
                        else:
                            boneCopyRotation = targetBone.constraints.new('COPY_ROTATION')
                            boneCopyRotation.name = "recrig_FollowRotation"
                        boneCopyRotation.target = bonePhysObject
                        #enable physics on the bone physics object
                        bpy.ops.rigidbody.object_add()
                        bonePhysObject.rigid_body.mass = 2
                        bonePhysObject.rigid_body.mesh_source = 'FINAL'
                        bonePhysObject.rigid_body.linear_damping = 0.3
                        bonePhysObject.rigid_body.angular_damping = 0.1
                        bonePhysObject.hide_render = True
          
                    #list unparented bones to report to user
                    unparentedBones = []
                    #fill in all physics constraints from collection
                    for potentialPhysObject in bpy.data.collections[recrigCollectionName].objects:
                        if("recrig_" in potentialPhysObject.name and armatureObject.name in potentialPhysObject.name):
                            #if it is the physics object, attach it to the associated handle
                            if("_phys" in potentialPhysObject.name):
                                associatedHandle = sceneObjects[potentialPhysObject.name.replace('_phys','_handle')]
                                print("physics object " + potentialPhysObject.name + " to attach to " + associatedHandle.name)
                                #select physics object to attach it to handle with constraint
                                bpy.ops.object.select_all(action='DESELECT')
                                potentialPhysObject.select_set(True)
                                context.view_layer.objects.active = potentialPhysObject
                                #set up rigid body constraint on physics object
                                bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
                                physRigidConstraint = potentialPhysObject.rigid_body_constraint
                                #assign objects and configure
                                physRigidConstraint.object1 = potentialPhysObject
                                physRigidConstraint.object2 = associatedHandle
                                physRigidConstraint.disable_collisions = True
                                physRigidConstraint.enabled = True
                                #hard limits
                                physRigidConstraint.use_limit_lin_x = False
                                physRigidConstraint.use_limit_lin_y = False
                                physRigidConstraint.use_limit_lin_z = False
                                
                                physRigidConstraint.use_limit_ang_x = True
                                physRigidConstraint.use_limit_ang_y = True
                                physRigidConstraint.use_limit_ang_z = True
                                physRigidConstraint.limit_ang_x_lower = -0.2
                                physRigidConstraint.limit_ang_y_lower = -0.2
                                physRigidConstraint.limit_ang_z_lower = -0.2
                                physRigidConstraint.limit_ang_x_upper = 0.2
                                physRigidConstraint.limit_ang_y_upper = 0.2
                                physRigidConstraint.limit_ang_z_upper = 0.2
                                
                                physRigidConstraint.use_spring_ang_x = True
                                physRigidConstraint.use_spring_ang_y = True
                                physRigidConstraint.use_spring_ang_z = True
                                physRigidConstraint.use_spring_x = True
                                physRigidConstraint.use_spring_y = True
                                physRigidConstraint.use_spring_z = True
                                physRigidConstraint.spring_stiffness_ang_x = 700
                                physRigidConstraint.spring_stiffness_ang_y = 700
                                physRigidConstraint.spring_stiffness_ang_z = 700
                                physRigidConstraint.spring_stiffness_x = 100
                                physRigidConstraint.spring_stiffness_y = 100
                                physRigidConstraint.spring_stiffness_z = 100
                                physRigidConstraint.spring_damping_x = 10
                                physRigidConstraint.spring_damping_y = 10
                                physRigidConstraint.spring_damping_z = 10
                                physRigidConstraint.spring_damping_ang_x = 10
                                physRigidConstraint.spring_damping_ang_y = 10
                                physRigidConstraint.spring_damping_ang_z = 10
                            #if it is the handle object, use it to add a spring between each physics object for reciprocal movement
                            if("_handle" in potentialPhysObject.name):
                                targetBone = armatureObject.data.bones[potentialPhysObject.name.split("_")[2]]
                                #count unparented bones to report to user incase this causes undesirable results
                                if(targetBone.parent == None):
                                    unparentedBones.append(targetBone.name)
                                else:
                                    if("recrig_" + armatureObject.name + "_" + targetBone.parent.name + "_phys" in sceneObjects and "recrig_" + armatureObject.name + "_" + targetBone.name + "_phys" in sceneObjects):
                                        firstPhysicsObject = sceneObjects["recrig_" + armatureObject.name + "_" + targetBone.name + "_phys"]
                                        secondPhysicsObject = sceneObjects["recrig_" + armatureObject.name + "_" + targetBone.parent.name + "_phys"]
                                        print("physics object " + firstPhysicsObject.name + " to spring to " + secondPhysicsObject.name)
                                        #select handle object
                                        bpy.ops.object.select_all(action='DESELECT')
                                        potentialPhysObject.select_set(True)
                                        context.view_layer.objects.active = potentialPhysObject
                                        #set up rigid body constraint using handle as a pivot point for connecting rigid bodies with springs
                                        bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
                                        handleRigidConstraint = potentialPhysObject.rigid_body_constraint
                                        #connect first and second physics objects
                                        handleRigidConstraint.object1 = firstPhysicsObject
                                        handleRigidConstraint.object2 = secondPhysicsObject
                                        handleRigidConstraint.disable_collisions = True
                                        handleRigidConstraint.enabled = True
                                        #hard limits
                                        handleRigidConstraint.use_limit_lin_x = True
                                        handleRigidConstraint.use_limit_lin_y = True
                                        handleRigidConstraint.use_limit_lin_z = True
                                        handleRigidConstraint.limit_lin_x_lower = -0.1
                                        handleRigidConstraint.limit_lin_y_lower = -0.1
                                        handleRigidConstraint.limit_lin_z_lower = -0.1
                                        handleRigidConstraint.limit_lin_x_upper = 0.1
                                        handleRigidConstraint.limit_lin_y_upper = 0.1
                                        handleRigidConstraint.limit_lin_z_upper = 0.1
                                        #springs
                                        handleRigidConstraint.use_spring_ang_x = True
                                        handleRigidConstraint.use_spring_ang_y = True
                                        handleRigidConstraint.use_spring_ang_z = True
                                        handleRigidConstraint.use_spring_x = True
                                        handleRigidConstraint.use_spring_y = True
                                        handleRigidConstraint.use_spring_z = True
                                        handleRigidConstraint.spring_stiffness_ang_x = 200
                                        handleRigidConstraint.spring_stiffness_ang_y = 200
                                        handleRigidConstraint.spring_stiffness_ang_z = 200
                                        handleRigidConstraint.spring_stiffness_x = 1000
                                        handleRigidConstraint.spring_stiffness_y = 1000
                                        handleRigidConstraint.spring_stiffness_z = 1000
                                        handleRigidConstraint.spring_damping_x = 30
                                        handleRigidConstraint.spring_damping_y = 30
                                        handleRigidConstraint.spring_damping_z = 30
                                        handleRigidConstraint.spring_damping_ang_x = 10
                                        handleRigidConstraint.spring_damping_ang_y = 10
                                        handleRigidConstraint.spring_damping_ang_z = 10
                                potentialPhysObject.hide_viewport = True
                    #processing finished, report outcomes and select control rig for animation
                    if(len(unparentedBones) > 1):
                        self.report({'WARNING'}, 'Recrig did not apply constraints to some unparented bones. Please review parenting of these bones and reapply Recrig if results are undesired: ' + str(unparentedBones).replace("["," ").replace("]",""))    
                    bpy.ops.object.select_all(action='DESELECT')
                    controlArmature.select_set(True)
                    context.view_layer.objects.active = controlArmature
        return {'FINISHED'}
    
#function to nudge the physics timescale to clear the physics cache
class RECRIG_OT_ClearCache(bpy.types.Operator):
    bl_idname = "recrig.clearcache"
    bl_label = "clear physics cache"
    bl_description = "Clear physics cache by nudging the physics timescale"
    
    def execute(self, context):
        if(bpy.context.scene.rigidbody_world != None):
            bpy.context.scene.rigidbody_world.time_scale = bpy.context.scene.rigidbody_world.time_scale + 1
            bpy.context.scene.rigidbody_world.time_scale = bpy.context.scene.rigidbody_world.time_scale - 1
        return {'FINISHED'}
    
#function to make strong constraints between control armature and rigid bodies
class RECRIG_OT_SetStrong(bpy.types.Operator):
    bl_idname = "recrig.setstrong"
    bl_label = "Make rigid rig constraints strong on selected"
    bl_description = "Make the selected rigid bodies follow the control armature closely"
    
    def execute(self, context):
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        #recrig requires objects and armatures to be visible
        bpy.context.space_data.show_object_viewport_armature = True
        bpy.context.space_data.show_object_viewport_mesh = True
        sceneObjects = bpy.context.scene.objects
        #iterate through all selected objects and change constraint properties on recrig rigid bodies
        for potentialRecrigObject in bpy.context.selected_objects:
            if("recrig_" in potentialRecrigObject.name and "_phys" in potentialRecrigObject.name and potentialRecrigObject.rigid_body_constraint != None):
                recrigSplitName = potentialRecrigObject.name.split("_")
                handleRigidName = "recrig_" + recrigSplitName[1] + "_" + recrigSplitName[2] + "_handle"
                if(handleRigidName in sceneObjects):
                    handleRigidObject = sceneObjects[handleRigidName]
                    if(handleRigidObject.rigid_body_constraint != None):
                        handleRigidConstraint = sceneObjects[handleRigidName].rigid_body_constraint
                        physRigidConstraint = potentialRecrigObject.rigid_body_constraint
                        physRigidConstraint.use_limit_ang_x = True
                        physRigidConstraint.use_limit_ang_y = True
                        physRigidConstraint.use_limit_ang_z = True
                        physRigidConstraint.limit_ang_x_lower = 0
                        physRigidConstraint.limit_ang_y_lower = 0
                        physRigidConstraint.limit_ang_z_lower = 0
                        physRigidConstraint.limit_ang_x_upper = 0
                        physRigidConstraint.limit_ang_y_upper = 0
                        physRigidConstraint.limit_ang_z_upper = 0
                        handleRigidConstraint.limit_lin_x_lower = 0
                        handleRigidConstraint.limit_lin_y_lower = 0
                        handleRigidConstraint.limit_lin_z_lower = 0
                        handleRigidConstraint.limit_lin_x_upper = 0
                        handleRigidConstraint.limit_lin_y_upper = 0
                        handleRigidConstraint.limit_lin_z_upper = 0 
                        physRigidConstraint.use_spring_ang_x = True
                        physRigidConstraint.use_spring_ang_y = True
                        physRigidConstraint.use_spring_ang_z = True
                        physRigidConstraint.spring_stiffness_x = 100
                        physRigidConstraint.spring_stiffness_y = 100
                        physRigidConstraint.spring_stiffness_z = 100
                        physRigidConstraint.spring_damping_x = 10
                        physRigidConstraint.spring_damping_y = 10
                        physRigidConstraint.spring_damping_z = 10
                        
        return {'FINISHED'}
    
#function to make flexible constraints between control armature and rigid bodies
class RECRIG_OT_SetFlexible(bpy.types.Operator):
    bl_idname = "recrig.setflexible"
    bl_label = "Make rigid rig constraints flexible on selected"
    bl_description = "Make the selected rigid bodies follow the control armature with flexibility"
    
    def execute(self, context):
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        #recrig requires objects and armatures to be visible
        bpy.context.space_data.show_object_viewport_armature = True
        bpy.context.space_data.show_object_viewport_mesh = True
        sceneObjects = bpy.context.scene.objects
        #iterate through all selected objects and change constraint properties on recrig rigid bodies
        for potentialRecrigObject in bpy.context.selected_objects:
            if("recrig_" in potentialRecrigObject.name and "_phys" in potentialRecrigObject.name and potentialRecrigObject.rigid_body_constraint != None):
                recrigSplitName = potentialRecrigObject.name.split("_")
                handleRigidName = "recrig_" + recrigSplitName[1] + "_" + recrigSplitName[2] + "_handle"
                if(handleRigidName in sceneObjects):
                    handleRigidObject = sceneObjects[handleRigidName]
                    if(handleRigidObject.rigid_body_constraint != None):
                        handleRigidConstraint = sceneObjects[handleRigidName].rigid_body_constraint
                        physRigidConstraint = potentialRecrigObject.rigid_body_constraint
                        physRigidConstraint.use_limit_ang_x = True
                        physRigidConstraint.use_limit_ang_y = True
                        physRigidConstraint.use_limit_ang_z = True
                        physRigidConstraint.limit_ang_x_lower = -0.2
                        physRigidConstraint.limit_ang_y_lower = -0.2
                        physRigidConstraint.limit_ang_z_lower = -0.2
                        physRigidConstraint.limit_ang_x_upper = 0.2
                        physRigidConstraint.limit_ang_y_upper = 0.2
                        physRigidConstraint.limit_ang_z_upper = 0.2
                        handleRigidConstraint.limit_lin_x_lower = -0.1
                        handleRigidConstraint.limit_lin_y_lower = -0.1
                        handleRigidConstraint.limit_lin_z_lower = -0.1
                        handleRigidConstraint.limit_lin_x_upper = 0.1
                        handleRigidConstraint.limit_lin_y_upper = 0.1
                        handleRigidConstraint.limit_lin_z_upper = 0.1 
                        physRigidConstraint.use_spring_ang_x = True
                        physRigidConstraint.use_spring_ang_y = True
                        physRigidConstraint.use_spring_ang_z = True
                        physRigidConstraint.spring_stiffness_x = 100
                        physRigidConstraint.spring_stiffness_y = 100
                        physRigidConstraint.spring_stiffness_z = 100
                        physRigidConstraint.spring_damping_x = 10
                        physRigidConstraint.spring_damping_y = 10
                        physRigidConstraint.spring_damping_z = 10
                        
                        
        return {'FINISHED'}
    
#function to make weak constraints between control armature and rigid bodies
class RECRIG_OT_SetFloppy(bpy.types.Operator):
    bl_idname = "recrig.setfloppy"
    bl_label = "Make rigid rig constraints floppy on selected"
    bl_description = "Make the selected rigid bodies not follow the control armature"
    
    def execute(self, context):
        #speed up processing by setting simplify
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0
        #recrig requires objects and armatures to be visible
        bpy.context.space_data.show_object_viewport_armature = True
        bpy.context.space_data.show_object_viewport_mesh = True
        sceneObjects = bpy.context.scene.objects
        #iterate through all selected objects and change constraint properties on recrig rigid bodies
        for potentialRecrigObject in bpy.context.selected_objects:
            if("recrig_" in potentialRecrigObject.name and "_phys" in potentialRecrigObject.name and potentialRecrigObject.rigid_body_constraint != None):
                recrigSplitName = potentialRecrigObject.name.split("_")
                handleRigidName = "recrig_" + recrigSplitName[1] + "_" + recrigSplitName[2] + "_handle"
                if(handleRigidName in sceneObjects):
                    handleRigidObject = sceneObjects[handleRigidName]
                    if(handleRigidObject.rigid_body_constraint != None):
                        handleRigidConstraint = sceneObjects[handleRigidName].rigid_body_constraint
                        physRigidConstraint = potentialRecrigObject.rigid_body_constraint
                        physRigidConstraint.use_limit_ang_x = False
                        physRigidConstraint.use_limit_ang_y = False
                        physRigidConstraint.use_limit_ang_z = False
                        handleRigidConstraint.limit_lin_x_lower = -0.1
                        handleRigidConstraint.limit_lin_y_lower = -0.1
                        handleRigidConstraint.limit_lin_z_lower = -0.1
                        handleRigidConstraint.limit_lin_x_upper = 0.1
                        handleRigidConstraint.limit_lin_y_upper = 0.1
                        handleRigidConstraint.limit_lin_z_upper = 0.1
                        physRigidConstraint.use_spring_ang_x = False
                        physRigidConstraint.use_spring_ang_y = False
                        physRigidConstraint.use_spring_ang_z = False
                        physRigidConstraint.spring_stiffness_x = 5
                        physRigidConstraint.spring_stiffness_y = 5
                        physRigidConstraint.spring_stiffness_z = 5
                        physRigidConstraint.spring_damping_x = 3
                        physRigidConstraint.spring_damping_y = 3
                        physRigidConstraint.spring_damping_z = 3
        return {'FINISHED'}
             
#register and unregister all Reciprocal Rigid Rig classes
recrigClasses = (  RECRIG_PT_SetupPanel,
                    RECRIG_PT_TweakingPanel,
                    RECRIG_PT_AnimationPanel,
                    RECRIG_OT_AddToRig,
                    RECRIG_OT_RemoveFromRig,
                    RECRIG_OT_ClearCache,
                    RECRIG_OT_SetStrong,
                    RECRIG_OT_SetFlexible,
                    RECRIG_OT_SetFloppy
                    )

register, unregister = bpy.utils.register_classes_factory(recrigClasses)

if __name__ == '__main__':
    register()
