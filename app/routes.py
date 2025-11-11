from flask import Blueprint, jsonify

bp = Blueprint("routes", __name__)

@bp.get("/")
def index():
    return jsonify({"message": "API Flask OK"})
