"""Correlate readings from two sensors (CSV and JSON) into likely common detections.

Output format (see Samples/SampleOutput.json): {"<sensor1 id>": <sensor2 id>, ...}
"""
import csv
import json
import math
import sys

MAX_DISTANCE_M = 200 # sensors are accurate to 100 m each, so the same object can show up 200 m apart

def load_sensor1(path):
    """Read the CSV sensor file. Return a list of readings."""
    with open(path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        readings = [
                {
                    "id": int(row["id"]),
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
                for row in reader
        ]

        return readings

def load_sensor2(path):
    """Read the JSON sensor file. Return a list of readings."""
    with open(path, mode="r", encoding="utf-8") as file:
        data = json.load(file)

    return data

def is_valid(reading):
    """True if the coordinates are legal WGS 84 values."""
    latitude = reading.get("latitude")
    longitude = reading.get("longitude")

    if latitude < -90 or latitude > 90:
        return False
    if longitude < -180 or longitude > 180:
        return False

    return True


def distance_m(a, b):
    """Geodesic distance in metres between two readings."""

    # Haversine Formula (Great-Circle Distance in Meters)
    # Variables:
    #   R   = Earth's mean radius (6,371,000 meters)
    #   φ1  = Latitude of point 1 in radians
    #   φ2  = Latitude of point 2 in radians
    #   Δφ  = Difference in latitude (φ2 - φ1) in radians
    #   Δλ  = Difference in longitude (λ2 - λ1) in radians

    # Equations:
    #   a = sin²(Δφ / 2) + cos(φ1) * cos(φ2) * sin²(Δλ / 2)
    #   c = 2 * atan2(√a, √(1 - a))
    #   d = R * c

    # Earths mean radius in meters
    R = 6371000.0 

    lat1 = a.get("latitude")
    lat2 = b.get("latitude")

    lon1 = a.get("longitude")
    lon2 = b.get("longitude")
    
    phil, phil2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi /2) ** 2 + math.cos(phil) * math.cos(phil2) * math.sin(dlambda / 2) ** 2)
    a = min(1.0, max(0.0, a)) # guard against float error pushing it slightly outside 0..1

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

def correlate(sensor1, sensor2, max_distance_m):
    """Return {sensor1_id: sensor2_id} for readings that match."""

    # drop readings with impossible coordinates
    sensor1 = [r for r in sensor1 if is_valid(r)]
    sensor2 = [r for r in sensor2 if is_valid(r)]
    
    # every pair that's close enough to be the same object
    candidates = []
    for reading1 in sensor1:
        for reading2 in sensor2:
            d = distance_m(reading1, reading2)
            if d <= max_distance_m:
                candidates.append((d, reading1["id"], reading2["id"]))

    # closest pairs first, so a reading goes to its nearest match
    candidates.sort()

    # each id can only be used once
    correlated_data = {}
    used1 = set()
    used2 = set()
    for d, id1, id2 in candidates:
        if id1 in used1 or id2 in used2:
            continue
        correlated_data[id1] = id2
        used1.add(id1)
        used2.add(id2)

    return correlated_data    

def main(argv):
    sensor1 = load_sensor1(argv[0])
    sensor2 = load_sensor2(argv[1])
    out_path = argv[2] if len(argv) > 2 else "out.json"

    result = correlate(sensor1, sensor2, MAX_DISTANCE_M)

    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

if __name__ == "__main__":
    main(sys.argv[1:])
