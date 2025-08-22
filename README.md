# BlenderPhysPuppet
---

Retrograded for Blender 2.7.9 for use on older hardware and due to the fast opengl internal renderer in this legacy Blender version !

---

### Addon to create a physics 'puppet' from an armature, with a duplicate armature to control movement.

---

### To install:

-Download as zip from GitHub with 'Code > Download Zip'

-Install zip from Add-Ons section of Blender preferences window

-Make sure add-on is switched on and user preferences are saved

----

### To access the Physics Puppet menu:

-See 'Physics Puppet' tab in right-hand menu of 3D viewport when in object mode.

----

### To prepare an armature for one-click physics puppet:

  -Name bones with 'loose','floppy','weak' or 'lazy' in the bone name for them to have a fair bit of 'give' and appear floppy. May be useful for antennae or hair
  
----

### To apply phys puppet to an armature or multiple armatures at once:

-Enter pose mode for each of the armatures you wish to add physics puppet to

-Select the bones you wish to have physics enabled on

  -You do not need to apply physics to all bones. This is especially useful if you don't want physically simulated fingers or face bones. You may keep these kinds of bones unselected so they do not become part of the physics puppet.
  
-Return to object mode

-Select the armature or armatures you wish to add physics puppet to. 

-In object mode, press 'Make Puppet From Armature' in the 'Physics Puppet' menu.

----

### To add constraint armatures to control armatures for nonlinear-style animation:

-Generate the physics puppet for your chosen armature

-Select the bones you wish to create a constraint armature for from within the physics puppet armature

-Return to object mode and click 'Constraint Armature From Selected Bones'

-You may then use the generated armature and influence control empty as an 'animation layer' for the physics puppet control armature

-You may wish to generate multiple constraint armatures for one control armature, or chain constraint armatures together to form branching or pseudo-state-machine like influences

----

### How to animate with physics puppet:

-The original armature will be controlled by the duplicate armature using rigid body constraints.

-Before starting your animation, you may need to allow enough simulation frames to get your characters into position

-Leave at least 2 still reference-pose frames at the start of the physics simulation before moving into any poses, or the constraints may become misaligned

-Animate your control armature without paying too much attention to what the simulated armature is doing

-Try to imagine how the movements of the control armature will interact with the physical scene while animating

-Once you have a motion you want to test, move the playhead to the end of your current animation progress

-Click on 'Scene Properties > Rigid Body Cache > Calculate to Frame'

-Click on 'Scene Properties > Rigid Body Cache > Current Cache to Bake' to make sure the preview is preserved. You may have strange results if you do not click this!

-Scrub through the timeline to preview the result

-Adjust the animation of your control rig based on what you have seen in the resulting physics sim 

-Click on 'Scene Properties > Rigid Body Cache > Delete All Bakes' so that you may recalculate to frame and bake cache again to preview your new animation changes

-Repeat this process until you are satisfied with your animation

-Once your characters are animated, change the render range start frame so that the render begins right as the action starts. This way, you don't have to render out all of the physics setup frames!
