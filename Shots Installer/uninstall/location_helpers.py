#helper functions for location
from droneapi.lib import Location
import math
from vector3 import Vector3

EARTH_RADIUS = 6371010.0
LATLON_TO_M = 111319.5

#based on https://github.com/100grams/CoreLocationUtils
#returns distance between the given points in meters
def getDistanceFromPoints(a, b):
    # Get the difference between our two points then convert the difference into radians
    nDLat = math.radians(a.lat - b.lat)
    nDLon = math.radians(a.lon - b.lon)
    
    fromLat =  math.radians(b.lat)
    toLat =  math.radians(a.lat)
    
    lat2 = math.sin(nDLat/2) * math.sin(nDLat/2)
    long2 = math.sin(nDLon/2) * math.sin(nDLon/2)
    nA = lat2 + math.cos(fromLat) * math.cos(toLat) * long2
    
    nC = 2 * math.atan2( math.sqrt(nA), math.sqrt( 1 - nA ))
    nD = EARTH_RADIUS * nC

    return nD

# Same as above, except includes altitude in the calculation
# this isn't the most efficient calculation - it's just bolted on the 2d version
def getDistanceFromPoints3d(a, b):
    TwoDDist = getDistanceFromPoints(a, b)
    alt2 = (a.alt - b.alt) * (a.alt - b.alt)
    dist2 = TwoDDist * TwoDDist
    
    return math.sqrt( alt2 + dist2 )


#Calculate a Location from a start location, azimuth (in degrees), and distance
#this only handles the 2D component (no altitude)
def newLocationFromAzimuthAndDistance(loc, azimuth, distance):
    result = Location(loc.lat, loc.lon, loc.alt)
    
    rLat = math.radians(loc.lat)
    rLong = math.radians(loc.lon)
    dist = distance / EARTH_RADIUS
    az = math.radians(azimuth)
    
    lat = math.asin( math.sin(rLat) * math.cos(dist) + math.cos(rLat) * math.sin(dist) * math.cos(az) )
    
    result.lat = math.degrees(lat)
    result.lon = math.degrees(rLong + math.atan2( math.sin(az) * math.sin(dist) * math.cos(rLat), math.cos(dist) - math.sin(rLat) * math.sin(lat) ))
    
    return result

#calculate azimuth between a start and end point (in degrees)
#see http://www.movable-type.co.uk/scripts/latlong.html
def calcAzimuthFromPoints(start, end):
    rLat1 = math.radians(start.lat)
    rLong1 = math.radians(start.lon)
    rLat2 = math.radians(end.lat)
    rLong2 = math.radians(end.lon)
    
    y = math.sin(rLong2 - rLong1) * math.cos(rLat2)
    x = math.cos(rLat1) * math.sin(rLat2) - math.sin(rLat1) * math.cos(rLat2) * math.cos( rLong2 - rLong1 )
    
    rad = math.atan2(y, x)
    
    #convert to degrees, then normalize to (0, 360) range
    degrees = math.degrees(rad)
    
    degrees = (degrees + 360.0) % 360.0
    return degrees

# given a start and an end point, return a tuple containing deltas in meters between start/end 
# along each axis
# returns a Vector3 
def getVectorFromPoints(start, end):
    x = (end.lat - start.lat) * LATLON_TO_M

    # calculate longitude scaling factor.  We could cache this if necessary
    # but we aren't doing so now
    scale = abs(math.cos(math.radians(end.lat))) 
    y = (end.lon - start.lon) * LATLON_TO_M * scale
    z = end.alt - start.alt

    return Vector3(x, y, z)

# add the given Vector3 (storing meter deltas) to the given Location
# and return the resulting Location
def addVectorToLocation(loc, vec):
    xToDeg = vec.x / LATLON_TO_M
    # calculate longitude scaling factor.  We could cache this if necessary
    # but we aren't doing so now
    scale = abs(math.cos(math.radians(loc.lat))) 
    yToDeg = vec.y / LATLON_TO_M / scale

    return Location(loc.lat + xToDeg, loc.lon + yToDeg, loc.alt + vec.z)

def wrapTo180(val):
    if (val < -180) or (180 < val):
        return wrapTo360(val + 180) - 180
    else:
        return val

def wrapTo360(val):
    wrapped = val % 360
    if wrapped == 0 and val > 0:
        return 360
    else:
        return wrapped