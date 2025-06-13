from flask import Blueprint, request, jsonify
from app.models.unidades import Unidad
from app.models.usuarios import Usuario, RolUsuario
from app import db
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


@unidades_bp.route('/unidades', methods=['GET'])
@jwt_required()
def obtener_unidades():
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    almacen_filtro = request.args.get('almacen_codigo')
    activo_filtro = request.args.get('activo')

    # Manejo estricto del parámetro `activo` (solo acepta "true" o "false")
    activo = None
    if activo_filtro is not None:
        if activo_filtro.lower() == 'true':
            activo = True
        elif activo_filtro.lower() == 'false':
            activo = False
        else:
            return jsonify({'error': 'El parámetro "activo" debe ser "true" o "false"'}), 400

    if usuario_actual.rol == RolUsuario.ADMIN:
        query = Unidad.query   # Consulta inicial: SELECT * FROM unidades
        if almacen_filtro:
            query = query.filter(Unidad.almacen_codigo == almacen_filtro) # Añade filtro: WHERE almacen_codigo = ?
    elif usuario_actual.rol == RolUsuario.GERENTE:
        query = Unidad.query.filter(Unidad.almacen_codigo == usuario_actual.almacen_codigo)
        if almacen_filtro and almacen_filtro != usuario_actual.almacen_codigo:
            return jsonify({'error': 'Solo puedes ver unidades de tu propia sucursal'}), 403
    else:
        return jsonify({'error': 'No tienes permisos para ver esta información'}), 403

    if activo is not None:
        query = query.filter(Unidad.activo == activo) 

    unidades = query.all()
    return jsonify([unidad.to_dict() for unidad in unidades]), 200


@unidades_bp.route('/unidades/<int:id_unidad>/estado', methods=['PATCH'])
@jwt_required()
def cambiar_estado_unidad(id_unidad):
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401


    unidad = Unidad.query.get(id_unidad)
    if not unidad:
        return jsonify({'error': 'Unidad no encontrada'}), 404

    if usuario_actual.rol == RolUsuario.GERENTE and unidad.almacen_codigo != usuario_actual.almacen_codigo:
        return jsonify({'error': 'No puedes modificar unidades de otra sucursal'}), 403

    # Cambiar el estado (invertirlo)
    unidad.activo = not unidad.activo

    try:
        db.session.commit()
        return jsonify({
            'mensaje': 'Estado actualizado correctamente',
            'nuevo_estado': unidad.activo,
            'unidad': unidad.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al actualizar la unidad', 'detalle': str(e)}), 500


@unidades_bp.route('/unidades/<int:id_unidad>/desasignar-chofer', methods=['PATCH'])
@jwt_required()
def desasignar_chofer(id_unidad):
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    unidad = Unidad.query.get(id_unidad)
    if not unidad:
        return jsonify({'error': 'Unidad no encontrada'}), 404

    if usuario_actual.rol == RolUsuario.GERENTE and unidad.almacen_codigo != usuario_actual.almacen_codigo:
        return jsonify({'error': 'No puedes modificar unidades de otra sucursal'}), 403

    # Verificar si ya está desasignada
    if unidad.chofer_id is None:
        return jsonify({'error': 'La unidad no tiene chofer asignado'}), 400

    # Desasignar chofer
    unidad.chofer_id = None

    try:
        db.session.commit()
        return jsonify({
            'mensaje': 'Chofer desasignado correctamente',
            'unidad': unidad.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al desasignar chofer', 'detalle': str(e)}), 500


@unidades_bp.route('/unidades/<int:id_unidad>/asignar-chofer', methods=['PATCH'])
@jwt_required()
def asignar_chofer(id_unidad):
    usuario_actual = get_usuario_actual()

    # 1. Validar usuario autenticado
    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    # 2. Validar rol (solo admin o gerente)
    if usuario_actual.rol not in [RolUsuario.ADMIN, RolUsuario.GERENTE]:
        return jsonify({
            'error': 'Permisos insuficientes',
            'detalle': 'Solo administradores y gerentes pueden asignar choferes'
        }), 403

    # 3. Validar datos del request
    data = request.get_json()
    if not data or 'chofer_id' not in data:
        return jsonify({'error': 'Se requiere el campo "chofer_id"'}), 400

    # 4. Buscar unidad y chofer en BD
    unidad = Unidad.query.get(id_unidad)
    chofer = Usuario.query.get(data['chofer_id'])

    if not unidad:
        return jsonify({'error': 'Unidad no encontrada'}), 404
    if not chofer or chofer.rol != RolUsuario.CHOFER:
        return jsonify({'error': 'ID no corresponde a un chofer válido'}), 400

    # 5. Validar que el chofer pertenezca al mismo almacén que la unidad
    if chofer.almacen_codigo != unidad.almacen_codigo:
        return jsonify({
            'error': 'Asignación no permitida',
            'detalle': 'El chofer debe pertenecer al mismo almacén que la unidad'
        }), 403

    # 6. Validar que la unidad no tenga chofer asignado
    if unidad.chofer_id is not None:
        return jsonify({
            'error': 'Unidad ya asignada',
            'detalle': f'La unidad ya tiene asignado al chofer ID {unidad.chofer_id}'
        }), 400

    # 7. Asignar chofer
    unidad.chofer_id = chofer.id_usuario

    try:
        db.session.commit()
        return jsonify({
            'mensaje': 'Asignación exitosa',
            'unidad': unidad.to_dict(),
            'chofer': {
                'id': chofer.id_usuario,
                'nombre': chofer.nombre,
                'almacen_codigo': chofer.almacen_codigo
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error en la base de datos', 'detalle': str(e)}), 500
    

@unidades_bp.route('/unidades/<int:id_unidad>', methods=['PUT'])
@jwt_required()
def actualizar_unidad(id_unidad):
    datos = request.get_json()
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    unidad = Unidad.query.get(id_unidad)
    if not unidad:
        return jsonify({'error': 'Unidad no encontrada'}), 404

    if usuario_actual.rol == RolUsuario.GERENTE:
        if unidad.almacen_codigo != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No puedes modificar unidades de otra sucursal'}), 403
    elif usuario_actual.rol != RolUsuario.ADMIN:
        return jsonify({'error': 'No tienes permisos para modificar unidades'}), 403

    if 'nombre' in datos:
        unidad.nombre = datos['nombre']
    if 'placas' in datos:
        unidad.placas = datos['placas']
    if 'descripcion' in datos:
        unidad.descripcion = datos['descripcion']

    try:
        db.session.commit()
        return jsonify(unidad.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

