"""
from flask import Blueprint, jsonify
from app.models.almacenes import Almacen
from app.models.clientes import Cliente

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes', methods=['GET'])
def obtener_clientes():
    try:
        clientes = Cliente.query.all()
        return jsonify({
            'success': True,
            'data': [cliente.to_dict() for cliente in clientes],
            'count': len(clientes)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@clientes_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def obtener_cliente(cliente_id):
    try:
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            return jsonify({
                'success': True,
                'data': cliente.to_dict()
            })
        return jsonify({
            'success': False,
            'error': 'Cliente no encontrado'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    """