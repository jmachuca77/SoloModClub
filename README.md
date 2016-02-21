# SoloModClub

This repository is to keep any modifications done for the 3DR Solo. 

## Shots Installer

The files contained here were originally written by Jason Short and published on the [Facebook Solo Mod Club](https://www.facebook.com/groups/3DRSOLOModClub/?fref=nf) group. Following is the post from Jason (Slightly modified):

Merry Christmas!
Hey, over the Christmas break I wrote a new Smart Shot called Pano. It's not an officially supported shot so I wrote it in a way that does not require the mobile app to be updated. To try this out you'll need to do a few things:

1 Upgrade to the latest Solo software. This shot will only work with the current version of ShotManager. When new updates come along you'll need to factory reset or run the installer script to do a "Sololink settings reset".

2 Run the installer script from a command line like this:
./solo_tools.command
And choose whatever you want to do.

3 I have mapped the Pano shot to override the Sport flight mode. Assign the Sport fight mode to A or B on the controller and you should be good. Now restart Solo to enable the shot.
When you want to take a Pano, enter Sport mode while in the air. The controller will say Pano If it enters the shot (the app won't really know what's happening)
(If you actually enter Sport mode in the air, hit FLY asap and try to reinstall the files.)
So what does it do?
to.


### Pano:

This is a SmartShot that will take a sequence of pictures to create a panorma

How does it work:
Once you enter the mode, A and B become a menu. Photo for a photo panorama, and Video for a video panorama. Photo has two options - Linear and Sphere. A linear Pano will grab a 180 FOV in 3 shots. Center your subject and it will look left to right

A spherical Pano will grab 13 shots at multiple angles. You can stitch with your favorite app such as PT GUI or Kolor to make a little planet or VR sphere.

The video pano lets you control a constant Yaw rate. Use the left stick to slow, speed up or reverse the direction. Use it for Hyperlapses or easy video pans.

Known bugs: The photo pano takes an extra photo when starting. no big deal, just toss the extra pho