import pyproj

_OUTPUT_PROJECTION = pyproj.Proj("+init=EPSG:4326")

def _transform(coords, projection):
    _INPUT_PROJECTION = pyproj.Proj("+init=EPSG:" + projection)
    x1,y1= coords.split(" ")
    x2,y2=pyproj.transform(_INPUT_PROJECTION, _OUTPUT_PROJECTION, float(x1), float(y1))
    return str(x2) + " " + str(y2)

def extract_tracks_coords(coords_list, projection):
    geom = "LINESTRING("
    transformed_coords = [_transform(coords, projection) for coords in coords_list]
    for i in transformed_coords:
        geom = geom + i + ","
    geom = geom[:-1] + ")"
    return geom

def extract_elements_coords(coords, projection):
    geom = "POINT("
    transformed_coords = _transform(coords, projection)
    return geom + transformed_coords + ")"
