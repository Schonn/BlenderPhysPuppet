# Physics Puppet Blender Addon
# Copyright (C) 2025 Pierre
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
import mathutils
import math

#addon info read by Blender
bl_info = {
    "name": "Physics Puppet",
    "author": "Pierre",
    "version": (0, 0, 7),
    "blender": (2, 7, 9),
    "description": "Turn armatures into active ragdoll puppets",
    "category": "Animation"
    }


#setup panel class
class PHYSPUP_PT_SetupPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Physics Puppet Setup'
    bl_context = 'objectmode'
    bl_category = 'Physics Puppet'

    def draw(self, context):
        self.layout.operator("physpup.makepuppet", text ="Make Puppet From Armature")
        self.layout.operator("physpup.makeconstraintrig", text ="Constraint Armature From Selected Bones")

#setup operator
class PHYSPUP_OT_MakePuppet(bpy.types.Operator):
    bl_idname = "physpup.makepuppet"
    bl_label = "Make Puppet From Armature"
    bl_description = "Use selected bones in selected armatures to create a physics puppet"
    
    def execute(self, context):
        #make sure rigid body world exists
        if(bpy.context.scene.rigidbody_world == None):
            bpy.ops.rigidbody.world_add()
        #adjust gravity and simulation accuracy
        bpy.context.scene.rigidbody_world.effector_weights.gravity = 1
        bpy.context.scene.rigidbody_world.steps_per_second = 100
        #make sure collision mesh data exists
        collisionMesh = None
        #use existing collision mesh data if available, otherwise generate new
        if("physpup_collisionmesh" in bpy.data.meshes):
            collisionMesh = bpy.data.meshes["physpup_collisionmesh"]
        else:
            colliderVertexData = [
            (-1.0,-1.0,-1.0),(1.0,-1.0,-1.0),(-1.0,-1.0,1.0),(1.0,-1.0,1.0),(-1.0,1.0,-1.0),(1.0,1.0,-1.0),(-1.0,1.0,1.0),(1.0,1.0,1.0),(-0.5,-1.5,0.5),(-0.5,-1.5,-0.5),(0.5,-1.5,-0.5),(0.5,-1.5,0.5),(0.5,1.5,0.5),(-0.5,1.5,0.5),(-0.5,1.5,-0.5),(0.5,1.5,-0.5)
            ]
            colliderEdgeData = [
            (2,0),(0,1),(1,3),(3,2),(6,2),(3,7),(7,6),(4,6),(7,5),(5,4),(0,4),(5,1),(8,9),(9,10),(10,11),(11,8),(12,13),(14,13),(12,15),(15,14),(2,8),(11,3),(1,10),(9,0),(5,15),(12,7),(13,6),(4,14),(9,1),(6,3),(11,2),(0,5),(0,6),(5,3),(8,10),(14,12),(12,5),(13,7),(10,3),(8,0),(15,4),(14,6)
            ]
            colliderFaceData = [
            (1,9,0),(3,6,2),(2,11,3),(5,0,4),(6,0,2),(3,5,7),(10,8,9),(12,14,13),(5,12,7),(7,13,6),(3,10,1),(0,8,2),(4,15,5),(6,14,4),(1,10,9),(3,7,6),(2,8,11),(5,1,0),(6,4,0),(3,1,5),(10,11,8),(12,15,14),(5,15,12),(7,12,13),(3,11,10),(0,9,8),(4,14,15),(6,13,14)
            ]
            collisionMesh = bpy.data.meshes.new("physpup_collisionmesh")
            collisionMesh.from_pydata(colliderVertexData,colliderEdgeData,colliderFaceData)
            collisionMesh.update()
        
        #iterate all selected objects and find armatures
        originalSelectedObjects = bpy.context.selected_objects
        for puppetArmature in originalSelectedObjects:
            if(puppetArmature.type == 'ARMATURE'):
                #create duplicate control armature
                controlArmature = bpy.data.objects.new("physpup_" + puppetArmature.name + "_control",puppetArmature.data)
                bpy.context.scene.objects.link(controlArmature)
                controlArmature.location = puppetArmature.location + mathutils.Vector([0,5,0])
                controlArmature.show_x_ray = True
                #iterate selected bones in puppet armature to create colliders
                for selectedBone in puppetArmature.data.bones:
                    if(selectedBone.select == True):
                        #get collider scales
                        colliderScale = [selectedBone.length*0.2,selectedBone.length*0.3,selectedBone.length*0.2]
                        #create puppet bone collider
                        puppetCollider = bpy.data.objects.new("physpup_" + puppetArmature.name + "_" + selectedBone.name + "_phys",collisionMesh)
                        bpy.context.scene.objects.link(puppetCollider)
                        puppetCollider.matrix_world = puppetArmature.matrix_world * puppetArmature.pose.bones[selectedBone.name].matrix
                        puppetCollider.location = puppetCollider.matrix_world * mathutils.Vector([0,selectedBone.length*0.5,0])
                        puppetCollider.draw_type = 'WIRE'
                        puppetCollider.hide_render = True
                        #set weights for bone transform copy if not existing
                        if(("PHYPUP_bonetransform" in puppetCollider.vertex_groups) == False):
                            transformVertGroup = puppetCollider.vertex_groups.new(name="PHYPUP_bonetransform")
                            transformVertGroup.add([8,9,10,11],1,'REPLACE')
                        
                        #create control bone collider
                        controlCollider = bpy.data.objects.new("physpup_" + puppetArmature.name + "_" + selectedBone.name + "_control",collisionMesh)
                        bpy.context.scene.objects.link(controlCollider)
                        controlCollider.parent = controlArmature
                        controlCollider.parent_type = 'BONE'
                        controlCollider.parent_bone = selectedBone.name
                        controlCollider.location = [0,-selectedBone.length*0.5,0]
                        controlCollider.rotation_euler = [0,0,0]
                        controlCollider.scale = colliderScale
                        controlCollider.draw_type = 'WIRE'
                        controlCollider.hide_render = True
                        
                        #set up rigid bodies
                        bpy.context.scene.objects.active = controlCollider
                        bpy.ops.rigidbody.object_add(type='PASSIVE')
                        controlCollider.rigid_body.kinematic = True
                        bpy.context.scene.objects.active = puppetCollider
                        bpy.ops.rigidbody.object_add(type='ACTIVE')
                        puppetCollider.rigid_body.friction = 0.5
                        puppetCollider.rigid_body.mass = selectedBone.length * 10
                        puppetCollider.rigid_body.linear_damping = 0
                        puppetCollider.rigid_body.angular_damping = 0
                        
                        #create puppet constraint empty if bone has a selected parent
                        puppetConstraintPoint = None
                        if(selectedBone.parent != None):
                            if(selectedBone.parent.select == True):
                                puppetConstraintPoint = bpy.data.objects.new("physpup_" + puppetArmature.name + "_" + selectedBone.name + "_constraint",None)
                                bpy.context.scene.objects.link(puppetConstraintPoint)
                                puppetConstraintPoint.parent = puppetCollider
                                puppetConstraintPoint.location = [0,-1.6,0]
                                puppetConstraintPoint.rotation_euler = [0,0,0]
                                #store associated bone in constraint point for position constraints later
                                puppetConstraintPoint["PHYSPUPAssociatedBone"] = selectedBone.name
                                bpy.context.scene.objects.active = puppetConstraintPoint
                                #add rigid body constraints
                                bpy.ops.rigidbody.constraint_add()
                                #determine minimums and maximums from bone name
                                moveLowerLimit = 0
                                moveUpperLimit = 0
                                puppetConstraintPoint.rigid_body_constraint.type = 'GENERIC'
                                puppetConstraintPoint.rigid_body_constraint.use_limit_lin_x = True
                                puppetConstraintPoint.rigid_body_constraint.use_limit_lin_y = True
                                puppetConstraintPoint.rigid_body_constraint.use_limit_lin_z = True
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_x_lower = moveLowerLimit
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_y_lower = moveLowerLimit
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_z_lower = moveLowerLimit
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_x_upper = moveUpperLimit
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_y_upper = moveUpperLimit
                                puppetConstraintPoint.rigid_body_constraint.limit_lin_z_upper = moveUpperLimit
                        #scale collider with constraint empty attached
                        puppetCollider.scale = colliderScale
                        #add rigid body constraints
                        bpy.context.scene.objects.active = controlCollider
                        bpy.ops.rigidbody.constraint_add()
                        controlCollider.rigid_body_constraint.type = 'GENERIC'
                        controlCollider.rigid_body_constraint.use_limit_ang_x = True
                        controlCollider.rigid_body_constraint.use_limit_ang_y = True
                        controlCollider.rigid_body_constraint.use_limit_ang_z = True
                        #determine minimums and maximums from bone name
                        rotateLowerLimit = math.radians(0)
                        rotateUpperLimit = math.radians(0)
                        #make sure things that are meant to be loose, stay loose
                        if(("loose" in selectedBone.name) 
                        or ("floppy" in selectedBone.name)
                        or ("weak" in selectedBone.name)
                        or ("lazy" in selectedBone.name)):
                            rotateLowerLimit = math.radians(-90)
                            rotateUpperLimit = math.radians(90)
                        controlCollider.rigid_body_constraint.limit_ang_x_lower = rotateLowerLimit
                        controlCollider.rigid_body_constraint.limit_ang_y_lower = rotateLowerLimit
                        controlCollider.rigid_body_constraint.limit_ang_z_lower = rotateLowerLimit
                        controlCollider.rigid_body_constraint.limit_ang_x_upper = rotateUpperLimit
                        controlCollider.rigid_body_constraint.limit_ang_y_upper = rotateUpperLimit
                        controlCollider.rigid_body_constraint.limit_ang_z_upper = rotateUpperLimit
                        controlCollider.rigid_body_constraint.object1 = puppetCollider
                        controlCollider.rigid_body_constraint.object2 = controlCollider
                        
                #iterate selected bones in puppet armature to finish constraint connections
                for selectedConstraintBone in puppetArmature.data.bones:
                    puppetColliderName = "physpup_" + puppetArmature.name + "_" + selectedConstraintBone.name + "_phys"
                    puppetConstraintPointName = "physpup_" + puppetArmature.name + "_" + selectedConstraintBone.name + "_constraint"
                    #if a constraint object has been created, the bone can be position constrained
                    if((puppetConstraintPointName) in bpy.data.objects):
                        puppetConstraintPoint = bpy.data.objects[puppetConstraintPointName]
                        puppetCollider = bpy.data.objects[puppetColliderName]
                        puppetParentCollider = bpy.data.objects["physpup_" + puppetArmature.name + "_" + selectedConstraintBone.parent.name + "_phys"]
                        puppetConstraintPoint.rigid_body_constraint.object1 = puppetCollider
                        puppetConstraintPoint.rigid_body_constraint.object2 = puppetParentCollider
                    #if a puppet collider exists regardless of constraint point, the bone can be constrainted to it
                    if((puppetColliderName) in bpy.data.objects):
                        puppetCollider = bpy.data.objects[puppetColliderName]
                        rotateConstraint = puppetArmature.pose.bones[selectedConstraintBone.name].constraints.new(type='COPY_ROTATION')
                        rotateConstraint.target = puppetCollider
                        positionConstraint = puppetArmature.pose.bones[selectedConstraintBone.name].constraints.new(type='COPY_LOCATION')
                        positionConstraint.target = puppetCollider
                        positionConstraint.subtarget = "PHYPUP_bonetransform"
                #final iteration to split bones
                #ops appears to be the only way to do this
                bpy.ops.object.select_all(action='DESELECT')
                puppetArmature.select = True
                bpy.context.scene.objects.active = puppetArmature
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                for selectedDisconnectBone in puppetArmature.data.bones:
                    puppetArmature.data.edit_bones[selectedDisconnectBone.name].use_connect = False
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        return {'FINISHED'}
    
class PHYSPUP_OT_MakeConstraintRig(bpy.types.Operator):
    bl_idname = "physpup.makeconstraintrig"
    bl_label = "Make constraint rig for selected bones"
    bl_description = "Use selected bones in selected armatures to create constraint rigs with controllable influence"
    
    def execute(self, context):
        #iterate all selected objects and find armatures
        originalSelectedObjects = bpy.context.selected_objects
        for controlArmature in originalSelectedObjects:
            if(controlArmature.type == 'ARMATURE'):
                #create duplicate control armature
                constraintArmature = bpy.data.objects.new(controlArmature.name + "_constraint",controlArmature.data)
                bpy.context.scene.objects.link(constraintArmature)
                constraintArmature.location = controlArmature.location + mathutils.Vector([0,5,0])
                constraintArmature.show_x_ray = True
                #make distance control empty 
                distanceControlEmpty = bpy.data.objects.new("driverinfluence_" + constraintArmature.name,None)
                bpy.context.scene.objects.link(distanceControlEmpty)
                distanceControlEmpty.location = constraintArmature.location
                #iterate selected bones in constraint armature to create constraints
                for selectedBone in controlArmature.data.bones:
                    if(selectedBone.select == True):
                        print(selectedBone.name + " is selected in " + controlArmature.name)
                        boneTransformConstraint = controlArmature.pose.bones[selectedBone.name].constraints.new(type='COPY_TRANSFORMS')
                        boneTransformConstraint.name = "transformconstrain_physpup"
                        boneTransformConstraint.target = constraintArmature
                        boneTransformConstraint.subtarget = selectedBone.name
                        boneTransformConstraint.owner_space = 'LOCAL'
                        boneTransformConstraint.target_space = 'LOCAL'
                        constraintDriver = boneTransformConstraint.driver_add('influence')
                        constraintDriver.driver.type = 'AVERAGE'
                        constraintDriverVariable = constraintDriver.driver.variables.new()
                        constraintDriverVariable.name = "physpup_driveremptydistance"
                        constraintDriverVariable.type = 'LOC_DIFF'
                        constraintDriverVariable.targets[0].id = distanceControlEmpty
                        constraintDriverVariable.targets[1].id = constraintArmature
        return {'FINISHED'}
   
#register and unregister panels and operators
def register():
    bpy.utils.register_class(PHYSPUP_PT_SetupPanel)
    bpy.utils.register_class(PHYSPUP_OT_MakePuppet)
    bpy.utils.register_class(PHYSPUP_OT_MakeConstraintRig)
    
def unregister():
    bpy.utils.unregister_class(PHYSPUP_PT_SetupPanel)
    bpy.utils.unregister_class(PHYSPUP_OT_MakePuppet)
    bpy.utils.unregister_class(PHYSPUP_OT_MakeConstraintRig)

if __name__ == '__main__':
    register()
