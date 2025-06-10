from flask import Blueprint, jsonify
from app.models.almacenes import Almacen

almacenes_bp = Blueprint('almacenes', __name__)

@almacenes_bp.route('/almacenes', methods=['GET'])
def obtener_almacenes():
    try:
        almacenes = Almacen.query.all()
        return jsonify({
            'success': True,
            'data': [almacen.to_dict() for almacen in almacenes],
            'count': len(almacenes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500