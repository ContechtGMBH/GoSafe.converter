from flask import Blueprint, request, jsonify
from utils.helpers import read_geojson, read_shapefile
from src.models import db as graph

vector = Blueprint('ifc', __name__, url_prefix='/api/v1/vector')

@vector.route("/import/geojson", methods=["POST"])
def import_geojson():
    res = read_geojson(request.files["file"], graph, "Testing", "test")

    return jsonify(res)


@vector.route("/import/shapefile", methods=["POST"])
def import_shapefile():
    res = read_shapefile(request.files["file"], graph, "Building", "buildings")

    return jsonify(res)
