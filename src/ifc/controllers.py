from flask import Blueprint, request, jsonify

ifc = Blueprint('ifc', __name__, url_prefix='/api/v1/ifc')

@ifc.route("/import", methods=["POST"])
def import_ifc():
    return jsonify({"status": "ok"})
