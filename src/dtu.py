import json
import math

INPUT = "bairros.geojson"
OUTPUT = "bairros_ll.geojson"

UTM_ZONE = 23
SOUTH = True  # Belo Horizonte = Hemisfério Sul

def utm_to_latlon(easting, northing, zone=23, south=True):
    a = 6378137.0
    e = 0.081819191
    k0 = 0.9996

    x = easting - 500000.0
    y = northing
    if south:
        y -= 10000000.0

    m = y / k0
    mu = m / (a * (1 - e**2/4 - 3*e**4/64 - 5*e**6/256))

    e1 = (1 - math.sqrt(1-e**2)) / (1 + math.sqrt(1-e**2))

    j1 = 3*e1/2 - 27*e1**3/32
    j2 = 21*e1**2/16 - 55*e1**4/32
    j3 = 151*e1**3/96
    j4 = 1097*e1**4/512

    fp = mu + j1*math.sin(2*mu) + j2*math.sin(4*mu) + j3*math.sin(6*mu) + j4*math.sin(8*mu)

    e2 = e**2 / (1-e**2)
    c1 = e2 * math.cos(fp)**2
    t1 = math.tan(fp)**2
    r1 = a*(1-e**2) / ((1-e**2*(math.sin(fp))**2)**1.5)
    n1 = a / math.sqrt(1-e**2*(math.sin(fp))**2)

    d = x / (n1*k0)

    q1 = n1*math.tan(fp)/r1
    q2 = (d**2)/2
    q3 = (5 + 3*t1 + 10*c1 - 4*c1**2 - 9*e2)*(d**4)/24
    q4 = (61 + 90*t1 + 298*c1 + 45*t1**2 - 252*e2 - 3*c1**2)*(d**6)/720

    lat = fp - q1*(q2 - q3 + q4)

    q5 = d
    q6 = (1 + 2*t1 + c1)*(d**3)/6
    q7 = (5 - 2*c1 + 28*t1 - 3*c1**2 + 8*e2 + 24*t1**2)*(d**5)/120

    lon = (q5 - q6 + q7) / math.cos(fp)

    lon0 = (zone * 6 - 183) * math.pi/180  # meridiano central

    lat = lat * 180/math.pi
    lon = lon0 + lon
    lon = lon * 180/math.pi

    return lat, lon


with open(INPUT, "r", encoding="utf-8") as f:
    g = json.load(f)

for feat in g["features"]:
    geom = feat["geometry"]

    if geom["type"] == "Polygon":
        new_coords = []
        for ring in geom["coordinates"]:
            new_ring = []
            for x, y in ring:
                lat, lon = utm_to_latlon(x, y, UTM_ZONE, SOUTH)
                new_ring.append([lon, lat])
            new_coords.append(new_ring)
        geom["coordinates"] = new_coords

    elif geom["type"] == "MultiPolygon":
        new_mp = []
        for poly in geom["coordinates"]:
            new_poly = []
            for ring in poly:
                new_ring = []
                for x, y in ring:
                    lat, lon = utm_to_latlon(x, y, UTM_ZONE, SOUTH)
                    new_ring.append([lon, lat])
                new_poly.append(new_ring)
            new_mp.append(new_poly)
        geom["coordinates"] = new_mp

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False)
