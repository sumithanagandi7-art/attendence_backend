from geopy.distance import geodesic


def distance_meters(lat1, lng1, lat2, lng2):
    """Return the distance in meters between two GPS coordinates."""
    return geodesic((lat1, lng1), (lat2, lng2)).meters


def find_matching_location(lat, lng, locations):
    """
    Given a GPS point and a list of WorkLocation objects (only the ones
    the employee is authorized for), return the first location whose
    geofence radius contains the point, else None.
    """
    for loc in locations:
        d = distance_meters(lat, lng, loc.latitude, loc.longitude)
        if d <= loc.radius_meters:
            return loc, d
    return None, None
