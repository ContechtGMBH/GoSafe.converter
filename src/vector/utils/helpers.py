from osgeo import ogr
import json
from py2neo import Node
import zipfile
import tempfile
import os

def read_geojson(geojson_file, graph, label, layer_name):
    try:
        data_source = ogr.Open(geojson_file.read())
        layer = data_source.GetLayer()
        geojsonOK = True
    except:
        traceback.print_exc()
        geojsonOK = False

    if not geojsonOK:
        return {"status": "error", "message": "invalid geojson"}

    for feature in layer:
        properties = json.loads(feature.ExportToJson())["properties"]
        properties["geometry"] = feature.GetGeometryRef().ExportToWkt()
        node = Node(label, **properties)
        graph.create(node)

    graph.run(
        """MATCH (n:%s)
        WHERE EXISTS(n.geometry) AND NOT (n)--()
        WITH collect(n) AS nodes
        CALL spatial.addNodes('%s', nodes)
        YIELD count RETURN count""" % (label, layer_name)
        )

    return {"status": "ok", "message": "ok"}

def read_shapefile(shp_file, graph, label, layer_name):
    if not zipfile.is_zipfile(shp_file):
        return {"status": "error", "message": "not a zipfile"}

    archive = zipfile.ZipFile(shp_file)

    required_suffixes = [".shp", ".shx", ".dbf", ".prj"]
    has_suffix = {}
    for suffix in required_suffixes:
        has_suffix[suffix] = False
    for info in archive.infolist():
        extension = os.path.splitext(info.filename)[1].lower()
        if extension in required_suffixes:
            has_suffix[extension] = True
    for suffix in required_suffixes:
        if not has_suffix[suffix]:
            archive.close()
            return {"status": "error", "message": "Archive missing required " + suffix + " file."}

    shapefile_name = None
    dst_dir = tempfile.mkdtemp()
    for info in archive.infolist():
        if info.filename.endswith(".shp"):
            shapefile_name = info.filename
        dst_file = os.path.join(dst_dir, info.filename)
        f = open(dst_file, "wb")
        f.write(archive.read(info.filename))
        f.close()
    archive.close()

    try:
        datasource = ogr.Open(os.path.join(dst_dir, shapefile_name))
        layer = datasource.GetLayer(0)
        shapefileOK = True
    except:
        traceback.print_exc()
        shapefileOK = False

    if not shapefileOK:
        #os.remove(fname)
        shutil.rmtree(dst_dir)
        return {"status": "error", "message": "invalid shapefile"}

    for feature in layer:
        properties = json.loads(feature.ExportToJson())["properties"]
        for k,v in properties.iteritems():
            if v is None:
                properties[k] = "None"
        properties["geometry"] = feature.GetGeometryRef().ExportToWkt()
        node = Node(label, **properties)
        graph.create(node)

    graph.run(
        """MATCH (n:%s)
        WHERE EXISTS(n.geometry) AND NOT (n)--()
        WITH collect(n) AS nodes
        CALL spatial.addNodes('%s', nodes)
        YIELD count RETURN count""" % (label, layer_name)
        )

    return {"status": "ok", "message": "ok"}
