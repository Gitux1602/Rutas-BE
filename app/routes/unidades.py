from flask import Blueprint, request, jsonify
from app.models.unidades import Unidad
from app.models.usuarios import Usuario, RolUsuario
from app import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required

from app.utils.jwt_helpers import get_usuario_actual

unidades_bp = Blueprint('unidades', __name__)

@unidades_bp.route('/unidades', methods=['POST'])
@jwt_required()
def crear_unidad():
    datos = request.get_json()
    
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    if usuario_actual.rol not in [RolUsuario.ADMIN, RolUsuario.GERENTE]:
        return jsonify({'error': 'No tienes permisos para crear unidades'}), 403

    required_fields = ['nombre', 'placas', 'descripcion', 'almacen_codigo', 'chofer_id']
    for field in required_fields:
        if field not in datos:
            return jsonify({'error': f'El campo {field} es requerido'}), 400

    chofer = Usuario.query.filter_by(id_usuario=datos['chofer_id']).first()
    if not chofer:
        return jsonify({'error': 'El chofer asignado no existe'}), 400
    if chofer.rol != RolUsuario.CHOFER:
        return jsonify({'error': 'El usuario asignado no es un chofer'}), 400

    if datos['almacen_codigo'] != chofer.almacen_codigo:
        return jsonify({'error': 'El chofer debe pertenecer al mismo almacén que la unidad'}), 400

    if usuario_actual.rol == RolUsuario.GERENTE:
        if datos['almacen_codigo'] != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No puedes asignar unidades a otro almacén que no sea el tuyo'}), 403

    try:
        nueva_unidad = Unidad(
            nombre=datos['nombre'],
            placas=datos['placas'],
            descripcion=datos['descripcion'],
            almacen_codigo=datos['almacen_codigo'],
            activo=datos.get('activo', True),
            chofer_id=datos['chofer_id']
        )

        db.session.add(nueva_unidad)
        db.session.commit()

        return jsonify(nueva_unidad.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
