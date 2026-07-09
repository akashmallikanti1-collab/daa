"""
Areas Module – RideShareVCE
Defines the area graph around Vasavi College, Ibrahimbagh, Hyderabad.
Used by Dijkstra's algorithm and BFS route matching.
"""
import math

AREAS = {
    "Vasavi College (Ibrahimbagh)": {"lat": 17.3850, "lng": 78.4011, "zone": 0},
    "Golconda Fort":                 {"lat": 17.3833, "lng": 78.4011, "zone": 1},
    "Nanalnagar":                    {"lat": 17.3885, "lng": 78.4180, "zone": 1},
    "Langar Houz":                   {"lat": 17.3760, "lng": 78.4260, "zone": 2},
    "Aramghar":                      {"lat": 17.3700, "lng": 78.4350, "zone": 2},
    "Attapur":                       {"lat": 17.3631, "lng": 78.4219, "zone": 2},
    "Tolichowki":                    {"lat": 17.4048, "lng": 78.4196, "zone": 2},
    "Mehdipatnam":                   {"lat": 17.3927, "lng": 78.4357, "zone": 2},
    "Karwan":                        {"lat": 17.3978, "lng": 78.4497, "zone": 3},
    "Rajendranagar":                 {"lat": 17.3322, "lng": 78.4126, "zone": 3},
}

GRAPH = {
    "Vasavi College (Ibrahimbagh)": {"Golconda Fort": 0.6, "Nanalnagar": 1.8, "Tolichowki": 2.5, "Attapur": 3.2},
    "Golconda Fort":                 {"Vasavi College (Ibrahimbagh)": 0.6, "Nanalnagar": 1.5, "Langar Houz": 3.0, "Attapur": 3.8},
    "Nanalnagar":                    {"Vasavi College (Ibrahimbagh)": 1.8, "Golconda Fort": 1.5, "Langar Houz": 1.2, "Mehdipatnam": 1.9, "Tolichowki": 2.1},
    "Langar Houz":                   {"Nanalnagar": 1.2, "Golconda Fort": 3.0, "Aramghar": 1.1, "Attapur": 1.4, "Mehdipatnam": 1.5},
    "Aramghar":                      {"Langar Houz": 1.1, "Attapur": 1.3, "Rajendranagar": 4.2},
    "Attapur":                       {"Vasavi College (Ibrahimbagh)": 3.2, "Golconda Fort": 3.8, "Langar Houz": 1.4, "Aramghar": 1.3, "Rajendranagar": 3.5},
    "Tolichowki":                    {"Vasavi College (Ibrahimbagh)": 2.5, "Nanalnagar": 2.1, "Mehdipatnam": 1.4, "Karwan": 2.3},
    "Mehdipatnam":                   {"Nanalnagar": 1.9, "Langar Houz": 1.5, "Tolichowki": 1.4, "Karwan": 1.8},
    "Karwan":                        {"Tolichowki": 2.3, "Mehdipatnam": 1.8, "Rajendranagar": 5.5},
    "Rajendranagar":                 {"Attapur": 3.5, "Aramghar": 4.2, "Karwan": 5.5},
}

FARE_RATES = {
    "bike": {"base": 15, "per_km": 8},
    "car":  {"base": 30, "per_km": 14},
}


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def calculate_fare(pickup, dropoff, vehicle="car"):
    p = AREAS.get(pickup)
    d = AREAS.get(dropoff)
    if not p or not d:
        return 0
    dist = haversine(p["lat"], p["lng"], d["lat"], d["lng"])
    rate = FARE_RATES.get(vehicle, FARE_RATES["car"])
    return round(rate["base"] + dist * rate["per_km"], 1)


def get_route_areas(pickup, dropoff):
    p = AREAS.get(pickup)
    d = AREAS.get(dropoff)
    if not p or not d:
        return [pickup, dropoff]
    pzone, dzone = p["zone"], d["zone"]
    min_z, max_z = min(pzone, dzone), max(pzone, dzone)
    route = [pickup]
    for name, info in AREAS.items():
        if name not in (pickup, dropoff) and min_z <= info["zone"] <= max_z:
            route.append(name)
    route.append(dropoff)
    return route
