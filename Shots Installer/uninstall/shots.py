#!/usr/bin/env python

# definitions of shots
# NOTE: Make sure this stays in sync with the app's definitions!  Those are in iSolo/UI/ShotLibrary.swift

APP_SHOT_NONE = -1
APP_SHOT_SELFIE = 0
APP_SHOT_ORBIT = 1
APP_SHOT_CABLECAM = 2
APP_SHOT_RECORD = 4
APP_SHOT_FOLLOW = 5
APP_SHOT_MULTIPOINT = 6

# NULL terminated for sending to Artoo
SHOT_NAMES = {
	APP_SHOT_NONE : "FLY\0",
	APP_SHOT_SELFIE : "Selfie\0",
	APP_SHOT_ORBIT : "Orbit\0",
	APP_SHOT_CABLECAM : "Cable Cam\0",
	APP_SHOT_FOLLOW : "Follow\0",
	APP_SHOT_MULTIPOINT: "Cable Cam\0",
}