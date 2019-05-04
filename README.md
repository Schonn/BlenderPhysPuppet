# BlenderPhysPuppet
Addon to create a physics 'puppet' from an armature, with a duplicate armature to control the movement. Designed for Blender 2.8.
To use, run the script in blender and open the rightmost toolbar to see the puppet physics tab. Select the bones which you want to be turned into a puppet in pose mode, then go back into object mode with the armature selected which you want to apply the effect to. Once you have clicked 'create armature puppet' and it has generated a duplicate armature, drag the newly generated armature to a convenient location and begin animating using the duplicate armature. 
To force the physics cache to clear so that you can easily perform a calculate to frame or play the simulation forwards, there is now a Force Clear Cache option.

WIP: The Create Driver Armature option will duplicate the selected armature and create local to local copy rotation constraints on the bones from the original armature that were selected at the time of duplication (and none of the unselected bones). These constraints will be driven by the Z position of a single empty which is also created when this option is pressed. This is intended to enable realtime switching of animations similar to NLA. Currently the driver empties all use world position and therefore move to 0 on Z when created.

