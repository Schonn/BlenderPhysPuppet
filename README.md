# BlenderPhysPuppet
---

Updated for Blender 3.4.1

---

### Addon to create a physics 'puppet' from an armature, with a duplicate armature to control movement.

---

### To install:

-Download as zip from GitHub with 'Code > Download Zip'

-Install zip from Add-Ons section of Blender preferences window

-Make sure add-on is switched on

----

### To access the Physics Puppet menu:

-See 'Physics Puppet' tab in right-hand menu of 3D viewport when in object mode.

----

### To prepare an armature for one-click physics puppet:

-Name your bones according to how floppy or rigid they should be in the physics sim

  -bones with 'strong','rigid','tight','tough' or 'welded' in the bone name will follow the control armature rotation tightly and won't translate much. May be useful for arms, legs, hands or other things that require precise, strong movement.
  
  -bones with 'loose','floppy','weak' or 'lazy' will have a fair bit of give and appear floppy. May be useful for antennae or hair
  
  -bones without any of the above keywords will twist and shift very slightly, but mostly follow the control armature
  
----

### To apply phys puppet to an armature or multiple armatures at once:

-Enter pose mode for each of the armatures you wish to add physics puppet to

-Select the bones you wish to have physics enabled on

  -You do not need to apply physics to all bones. This is especially useful if you don't want physically simulated fingers or face bones. You may keep these kinds of bones unselected so they do not become part of the physics puppet.
  
-Return to object mode

-Select the armature or armatures you wish to add physics puppet to. 

-In object mode, press 'Make Puppet From Armature' in the 'Physics Puppet' menu.

----

### How to animate with physics puppet:

-The original armature will be controlled by the duplicate armature using rigid body constraints.

-Before starting your animation, you may need to allow enough simulation frames to get your characters into position

-Leave at least 2 still reference-pose frames at the start of the physics simulation before moving into any poses, or the constraints may become misaligned

-Animate your control armature without paying too much attention to what the simulated armature is doing

-Try to imagine how the movements of the control armature will interact with the physical scene while animating

-Once you have a motion you want to test, move the playhead to the end of your current animation progress

-Click on 'Scene Properties > Rigid Body World > Cache > Calculate to Frame'

-Click on 'Scene Properties > Rigid Body World > Cache > Current Cache to Bake' to make sure the preview is preserved. You may have strange results if you do not click this!

-Scrub through the timeline to preview the result

-Adjust the animation of your control rig based on what you have seen in the resulting physics sim 

-Click on 'Scene Properties > Rigid Body World > Cache > Delete All Bakes' so that you may recalculate to frame and bake cache again to preview your new animation changes

-Repeat this process until you are satisfied with your animation

-Once your characters are animated, change the render range start frame so that the render begins right as the action starts. This way, you don't have to render out all of the physics setup frames!
