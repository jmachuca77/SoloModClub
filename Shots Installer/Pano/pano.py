#
#  pano.py
#  shotmanager
#
#  The pano smart shot controller.
#  Runs as a DroneKit-Python script under MAVProxy.
#
#  Created by Jason Short and Will Silva on 11/30/2015.
#  Copyright (c) 2015 3D Robotics. All rights reserved.

from droneapi.lib import VehicleMode
from droneapi.lib import Location
from pymavlink import mavutil
import os
from os import sys, path
import math
import struct
import time

sys.path.append(os.path.realpath(''))
import app_packet
import camera
import location_helpers
import shotLogger
import shots
from shotManagerConstants import *
import GoProManager
from GoProConstants import *

# on host systems these files are located here
sys.path.append(os.path.realpath('../../flightcode/stm32'))
from sololink import btn_msg

# in degrees per second
YAW_SPEED = 10.0

# cm / second
PITCH_1 = 0
PITCH_2 = -45
PITCH_3 = -90

STEPS = 360 / 45
STEPS_TOTAL = STEPS * 2 + 1

YAW_DELTA = 360 / STEPS

INCREMENT_INTERVAL = UPDATE_RATE * 3
GOPRO_INTERVAL = UPDATE_RATE * 1.8
LINEAR_INCREMENT_ANGLE = 45.0
MIN_YAW_RATE = -60  # deg/s
MAX_YAW_RATE = 60  # deg/s
MAX_YAW_ACCEL_PER_TICK = (MAX_YAW_RATE) / (4 * UPDATE_RATE)  # deg/s^2/tick

logger = shotLogger.logger

PANO_NONE = 0
PANO_PHOTO = 1
PANO_VIDEO = 2
PANO_LINEAR = 3
PANO_SPHERE = 4

YAW = 3


class PanoShot():

    def __init__(self, vehicle, shotmgr):
        # assign the vehicle object
        self.vehicle = vehicle

        # assign the shotManager object
        self.shotmgr = shotmgr

        # ticks to track timing in shot
        self.ticks = 0

        # steps to track incrementing in shot
        self.step = 0

        # Default panoMode to None
        self.panoMode = PANO_NONE

        # Yaw rate for Video Pano shot
        self.degSecondYaw = 10

        # default FOV for Linear Pano shot
        self.fov = 180

        # index that tracks angles in Linear Pano shot
        self.linearIndex = 0

        # list of angles in Linear Pano shot
        self.linearAngles = []

        # default camYaw to current pointing
        self.camYaw = camera.getYaw(self.vehicle)

        # default camPitch to PITCH_1
        self.camPitch = camera.getPitch(self.vehicle)

        # default origYaw to current pointing
        self.origYaw = self.camYaw

        # default to not paused
        self.paused = False

        # set button mappings on Artoo
        self.setButtonMappings()

        # switch vehicle into GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")

        # switch gimbal into MAVLINK TARGETING mode
        self.setupTargeting()

    # channels are expected to be floating point values in the (-1.0, 1.0)
    # range
    def handleRCs(self, channels):

        if not self.paused:
            if self.panoMode == PANO_NONE:
                self.manualPitch(channels)
                self.handlePitchYaw()
                
            elif self.panoMode == PANO_VIDEO:
                self.runVideo(channels)
                self.manualPitch(channels)
                self.handlePitchYaw()

            elif self.panoMode == PANO_SPHERE:
                self.runSphere()
                self.handlePitchYaw()

            elif self.panoMode == PANO_LINEAR:
                self.runLinear()
                self.handlePitchYaw()

        # Always call flush to guarantee that previous writes to the vehicle
        # have taken place
        self.vehicle.flush()

    def manualPitch(self, channels):
        self.camPitch = (1-channels[5]) * -45

    def runSphere(self):
        '''Run the Hemi pano program'''
        self.ticks += 1

        # time delay between moves
        if self.ticks > INCREMENT_INTERVAL:
            self.incrementHemi()
            self.ticks = 0

        # time delay between snapshots
        if self.ticks == GOPRO_INTERVAL:
            self.shotmgr.goproManager.handleRecordCommand(self.shotmgr.goproManager.captureMode, RECORD_COMMAND_TOGGLE)

    def incrementHemi(self):
        '''Increment the Hemi pano shot'''
        if(self.camPitch == PITCH_3):
            logger.log("Complete")
            self.step = 0
            self.shotmgr.enterShot(shots.APP_SHOT_NONE)
            return

        # increment yaw
        self.camYaw = (self.origYaw + (self.step * YAW_DELTA)) % 360

        if self.step >= STEPS_TOTAL:
            self.camPitch = PITCH_3
            logger.log("set PITCH_3")

        elif self.step >= STEPS:
            self.camPitch = PITCH_2
            logger.log("set PITCH_2")

        else:
            self.camPitch = PITCH_1
            logger.log("set PITCH_1")

        # incement steps
        self.step += 1

    def runLinear(self):
        '''Run the Linear pano program'''
        self.ticks += 1

        # time delay between moves
        if self.ticks > INCREMENT_INTERVAL:
            self.incrementLinear()
            self.ticks = 0

        # time delay between snapshots
        if self.ticks == GOPRO_INTERVAL:
            self.shotmgr.goproManager.handleRecordCommand(self.shotmgr.goproManager.captureMode, RECORD_COMMAND_TOGGLE)

    def incrementLinear(self):
        '''Increment the Linear pano shot'''
        self.linearIndex += 1
        if self.linearIndex >= len(self.linearAngles):
            logger.log("linear pano complete")
            self.shotmgr.enterShot(shots.APP_SHOT_NONE)
            return

        # turn copter to next angle
        self.camYaw = self.linearAngles[self.linearIndex]

    def initLinear(self):
        '''Initialize the linear pano shot'''
        self.fov = max(self.fov, 91.0)
        self.fov = min(self.fov, 360.0)
        steps = math.ceil(self.fov / LINEAR_INCREMENT_ANGLE)

        # we could do center+- or left>right
        self.origYaw = camera.getYaw(self.vehicle)

        self.linearAngles = []
        self.linearAngles.append(self.origYaw)
        for x in xrange(1, int(steps)):
            tmp = (self.origYaw - (self.fov / 2)) + (self.fov / steps) * x
            if tmp < 0:
                tmp += 360
            elif tmp > 360:
                tmp -= 360
            self.linearAngles.append(tmp)

    def runVideo(self, channels):
        '''Run the Video pano program'''
        # modulate yaw rate based on yaw stick input
        if channels[YAW] != 0:
            self.degSecondYaw = self.degSecondYaw + \
                (channels[YAW] * MAX_YAW_ACCEL_PER_TICK)

        # limit yaw rate
        self.degSecondYaw = min(self.degSecondYaw, MAX_YAW_RATE)
        self.degSecondYaw = max(self.degSecondYaw, MIN_YAW_RATE)

        # increment desired yaw angle
        self.camYaw += (self.degSecondYaw * UPDATE_TIME)
        self.camYaw %= 360.0

    # if we can handle the button we do
    def handleButton(self, button, event):
        # we are not in a mode yet
        if self.panoMode == PANO_NONE:
            if button == btn_msg.ButtonA and event == btn_msg.Press:
                self.panoMode = PANO_PHOTO
                self.enterPhotoMode()
            if button == btn_msg.ButtonB and event == btn_msg.Press:
                self.panoMode = PANO_VIDEO
                self.shotmgr.goproManager.handleRecordCommand(CAPTURE_MODE_VIDEO, RECORD_COMMAND_START)

        # We are in a photo mode - must make choice of pano type
        elif self.panoMode == PANO_PHOTO:
            if button == btn_msg.ButtonA and event == btn_msg.Press:
                self.panoMode = PANO_LINEAR
                self.initLinear()
            if button == btn_msg.ButtonB and event == btn_msg.Press:
                self.panoMode = PANO_SPHERE
        
        if button == btn_msg.ButtonLoiter and event == btn_msg.Press:
            if self.paused:
                self.paused = False
            else:
                self.paused = True

        self.setButtonMappings()

    # not handling any options from the app for now
    def handleOptions(self, options):
        return

    def setButtonMappings(self):
        buttonMgr = self.shotmgr.buttonManager
        if self.panoMode == PANO_NONE:
            buttonMgr.setArtooButton(
                btn_msg.ButtonA, shots.APP_SHOT_PANO, btn_msg.ARTOO_BITMASK_ENABLED, "Photo\0")
            buttonMgr.setArtooButton(
                btn_msg.ButtonB, shots.APP_SHOT_PANO, btn_msg.ARTOO_BITMASK_ENABLED, "Video\0")
        elif self.panoMode == PANO_PHOTO:
            buttonMgr.setArtooButton(
                btn_msg.ButtonA, shots.APP_SHOT_PANO, btn_msg.ARTOO_BITMASK_ENABLED, "Linear\0")
            buttonMgr.setArtooButton(
                btn_msg.ButtonB, shots.APP_SHOT_PANO, btn_msg.ARTOO_BITMASK_ENABLED, "Sphere\0")
        else:
            buttonMgr.setArtooButton(
                btn_msg.ButtonA, shots.APP_SHOT_PANO, 0, "\0")
            buttonMgr.setArtooButton(
                btn_msg.ButtonB, shots.APP_SHOT_PANO, 0, "\0")

    # send our current set of options to the app
    def updateAppOptions(self):
        return

    def setupTargeting(self):
        # set gimbal targeting mode
        msg = self.vehicle.message_factory.mount_configure_encode(
                    0, 1,    # target system, target component
                    mavutil.mavlink.MAV_MOUNT_MODE_MAVLINK_TARGETING,  #mount_mode
                    1,  # stabilize roll
                    1,  # stabilize pitch
                    1,  # stabilize yaw
                    )

        self.shotmgr.remapper.enableRemapping( True )
        logger.log("setting gimbal to mavlink mode")

        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()

    def handlePitchYaw(self):
        '''Send pitch and yaw commands to gimbal or fixed mount'''
        # if we do have a gimbal, use mount_control to set pitch and yaw
        if self.vehicle.mount_status[0] is not None:
            msg = self.vehicle.message_factory.mount_control_encode(
                0, 1,    # target system, target component
                self.camPitch * 100,  # pitch is in centidegrees
                0.0,  # roll
                self.camYaw * 100,  # yaw is in centidegrees
                0  # save position
            )
        else:
            # if we don't have a gimbal, just set CONDITION_YAW
            msg = self.vehicle.message_factory.command_long_encode(
                0, 0,    # target system, target component
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
                0,  # confirmation
                self.camYaw,  # param 1 - target angle
                YAW_SPEED,  # param 2 - yaw speed
                1,  # param 3 - direction
                0.0,  # relative offset
                0, 0, 0  # params 5-7 (unused)
            )

        self.vehicle.send_mavlink(msg)

    def enterPhotoMode(self):
        # default camPitch to PITCH_1
        #self.camPitch = PITCH_1
    
        # switch into photo mode if we aren't already in it
        if self.shotmgr.goproManager.captureMode != CAPTURE_MODE_PHOTO:
            self.shotmgr.goproManager.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE, (CAPTURE_MODE_PHOTO, 0 ,0 , 0))

