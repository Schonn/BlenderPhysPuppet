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
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "description": "Create proxies for rigid bodies for physics based character animation",
    "category": "Animation"
    }

#panel class for physics puppet menu items in object mode
class PHYPUPPuppetPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Physics Puppet'
    #bl_context = 'posemode'
    bl_context = 'objectmode'
    bl_category = 'Puppet Physics'

    def draw(self, context):
        self.layout.operator('phypup.makeproxy', text ='Create Animation Proxy')
        self.layout.operator('phypup.makepuppet', text ='Create Armature Puppet')

        
class PHYPUPCreateProxy(bpy.types.Operator):
    bl_idname = "phypup.makeproxy"
    bl_label = "create physics animation proxy"
    bl_description = "create a clone of the currently selected physics object to control rotation"
    
    def execute(self, context):
        sceneObjects = bpy.context.scene.objects
        physSourceObject = bpy.context.selected_objects[0]
        if bpy.context.object.rigid_body is None:
            bpy.ops.rigidbody.object_add()
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'},TRANSFORM_OT_translate={"value":(3,0,0)})
        physHandleObject = bpy.context.selected_objects[0]
        physHandleObject.rigid_body.type = 'PASSIVE'
        physHandleObject.rigid_body.kinematic = True
        bpy.ops.rigidbody.constraint_add()
        physHandleObject.rigid_body_constraint.type = 'GENERIC_SPRING'
        physHandleObject.rigid_body_constraint.use_spring_ang_x = True
        physHandleObject.rigid_body_constraint.use_spring_ang_y = True
        physHandleObject.rigid_body_constraint.use_spring_ang_z = True
        physHandleObject.rigid_body_constraint.spring_stiffness_ang_x = 100
        physHandleObject.rigid_body_constraint.spring_stiffness_ang_y = 100
        physHandleObject.rigid_body_constraint.spring_stiffness_ang_z = 100
        physHandleObject.rigid_body_constraint.spring_damping_ang_x = 10
        physHandleObject.rigid_body_constraint.spring_damping_ang_y = 10
        physHandleObject.rigid_body_constraint.spring_damping_ang_z = 10
        physHandleObject.rigid_body_constraint.object1 = physSourceObject
        physHandleObject.rigid_body_constraint.object2 = physHandleObject
        return {'FINISHED'}
    
#function to create physics puppet controls for the currently selected armature
class PHYPUPCreateArmaturePuppet(bpy.types.Operator):
    bl_idname = "phypup.makepuppet"
    bl_label = "create physics puppet"
    bl_description = "set up physics and puppet handles for the selected armature"
    
    def execute(self, context):
        handleOffsetDistance = 5
        sceneObjects = bpy.context.scene.objects
        #pick up armature from first in selection, make sure it is armature
        armatureObject = bpy.context.selected_objects[0]
        if armatureObject.type == 'ARMATURE':
            bpy.context.scene.rigidbody_world.time_scale = 1.4
            bpy.context.scene.rigidbody_world.steps_per_second = 100
            bpy.context.scene.rigidbody_world.solver_iterations = 100
            bpy.context.scene.gravity = [0,0,-100]
            bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
            #posemode and select all bones, then edit to uncheck connected on all bones
            bpy.ops.object.posemode_toggle()
            #bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.object.editmode_toggle()
            for targetBone in bpy.context.selected_editable_bones:
                targetBone.use_connect = False
            #back into posemode to create the colliders for each bone
            bpy.ops.object.posemode_toggle()
            for targetBone in bpy.context.selected_pose_bones:
                bpy.ops.object.posemode_toggle()
                bpy.ops.mesh.primitive_plane_add(radius = targetBone.length*0.3)
                bonePhysObject = bpy.context.selected_objects[0]
                bonePhysObject.name = "PHYPUP_" + armatureObject.name + "_" + targetBone.name + "_phys"
                bpy.context.object.rotation_mode = 'QUATERNION'
                bonePhysObject.parent = armatureObject
                bonePhysObject.parent_type = 'BONE'
                bonePhysObject.parent_bone = targetBone.name
                bonePhysObject.location = [0,-targetBone.length,0]
                bpy.ops.object.editmode_toggle()
                bpy.ops.transform.rotate(value=1.5708,axis=(0.59,-0.80,2.98),constraint_axis=(True,False,False),constraint_orientation='LOCAL')
                bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0,0,-targetBone.length),"constraint_axis":(False,False,True),"constraint_orientation":'NORMAL'})
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
                bonePhysObject.rigid_body.linear_damping = 0.04
                bonePhysObject.rigid_body.angular_damping = 0.1
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
                    bonePhysObject.rigid_body_constraint.limit_lin_x_lower = -0.05
                    bonePhysObject.rigid_body_constraint.limit_lin_y_lower = -0.05
                    bonePhysObject.rigid_body_constraint.limit_lin_z_lower = -0.05
                    bonePhysObject.rigid_body_constraint.limit_lin_x_upper = 0.05
                    bonePhysObject.rigid_body_constraint.limit_lin_y_upper = 0.05
                    bonePhysObject.rigid_body_constraint.limit_lin_z_upper = 0.05
                    bonePhysObject.rigid_body_constraint.object1 = bonePhysObject
                    bonePhysObject.hide_render = True
                    #bonePhysObject.rigid_body_constraint.object2 = sceneObjects["PHYPUP_" + armatureObject.name + "_" + targetBone.parent.name + "_phys"]
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
                physHandleObject.rigid_body_constraint.limit_ang_x_lower = -0.1
                physHandleObject.rigid_body_constraint.limit_ang_y_lower = -0.1
                physHandleObject.rigid_body_constraint.limit_ang_z_lower = -0.1
                physHandleObject.rigid_body_constraint.limit_ang_x_upper = 0.1
                physHandleObject.rigid_body_constraint.limit_ang_y_upper = 0.1
                physHandleObject.rigid_body_constraint.limit_ang_z_upper = 0.1
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
            bpy.context.collection.objects.link(handleArmature)
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = handleArmature
            handleArmature.location[0] = handleArmature.location[0] + handleOffsetDistance
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
            
        return {'FINISHED'}
            
    
#register all classes when addon is loaded
def register():
    bpy.utils.register_class(PHYPUPPuppetPanel)
    bpy.utils.register_class(PHYPUPCreateProxy)
    bpy.utils.register_class(PHYPUPCreateArmaturePuppet)
#unregister all classes when addon is removed
def unregister():
    bpy.utils.unregister_class(PHYPUPPuppetPanel)
    bpy.utils.unregister_class(PHYPUPCreateProxy)
    bpy.utils.unregister_class(PHYPUPCreateArmaturePuppet)
#allow debugging for this addon in the Blender text editor
if __name__ == '__main__':
    register()
