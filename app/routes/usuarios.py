from flask import Blueprint, request, jsonify
from app.models.usuarios import Usuario, RolUsuario
from app import db
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash

from app.utils.jwt_helpers import get_usuario_actual

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/crear-usuario', methods=['POST'])
@jwt_required()
def crear_usuario():
    datos = request.get_json()
    
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    # Validar campos requeridos
    required_fields = ['nombre', 'correo', 'contrasena', 'rol']
    for field in required_fields:
        if field not in datos:
            return jsonify({'error': f'El campo {field} es requerido'}), 400

    # Verificar si el correo ya existe
    if Usuario.query.filter_by(correo=datos['correo']).first():
        return jsonify({'error': 'El correo electrónico ya está registrado'}), 400

    try:
        rol_enum = RolUsuario[datos['rol'].upper()]
    except KeyError:
        return jsonify({'error': 'Rol inválido'}), 400


    if usuario_actual.rol == RolUsuario.GERENTE:
        #Si es gerente
        if rol_enum != RolUsuario.CHOFER:
            return jsonify({'error': 'Solo puedes crear choferes'}), 403

        if datos.get('almacen_codigo') != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No puedes asignar choferes de otra sucursal'}), 403
    elif usuario_actual.rol != RolUsuario.ADMIN:
        #Si no es gerente pero tampoco admin
        return jsonify({'error': 'No tienes permisos para crear usuarios'}), 403
    
    contrasena_hash = generate_password_hash(datos['contrasena'])

    try:
        nuevo_usuario = Usuario(
            nombre=datos['nombre'],
            correo=datos['correo'],
            contrasena_hash=contrasena_hash,
            rol=rol_enum,
            almacen_codigo=datos.get('almacen_codigo'), #Se usa get si el campo no es obligatorio o usarás un valor por defecto y si no viene ('almacen_codigo') devuelve none
            activo=datos.get('activo', True)
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return jsonify(nuevo_usuario.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@usuarios_bp.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    datos = request.get_json()
    correo = datos.get('correo')
    nueva_contrasena = datos.get('nueva_contrasena')

    if not correo or not nueva_contrasena:
        return jsonify({'error': 'Correo y nueva contraseña son requeridos'}), 400

    usuario = Usuario.query.filter_by(correo=correo).first()

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if not usuario.cambiar_contrasena:
        return jsonify({'error': 'No está habilitado el cambio de contraseña'}), 403

    # Cambiar y desactivar el flag
    usuario.contrasena_hash = generate_password_hash(nueva_contrasena)
    usuario.cambiar_contrasena = False
    db.session.commit()

    return jsonify({'mensaje': 'Contraseña actualizada correctamente'}), 200


@usuarios_bp.route('/habilitar-cambio-contrasena/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def habilitar_cambio_contrasena(id_usuario):
    claims = get_jwt() #Obtener el JWT
    rol = claims.get("rol") #Sacamos el rol del JWT
    almacen_codigo_token = claims.get("almacen_codigo") #Sacamos el almacén del JWT

    usuario_a_editar = Usuario.query.get(id_usuario)

    if not usuario_a_editar:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if rol == 'ADMIN':
        pass  
    elif rol == 'GERENTE':
        if usuario_a_editar.almacen_codigo != almacen_codigo_token:
            return jsonify({'error': 'No puedes modificar usuarios de otra sucursal'}), 403
    else:
        return jsonify({'error': 'No tienes permisos para esta acción'}), 403

    usuario_a_editar.cambiar_contrasena = True
    db.session.commit()

    return jsonify({'mensaje': 'Cambio de contraseña habilitado correctamente'}), 200


@usuarios_bp.route('/editar-usuario/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def editar_usuario(id_usuario):
    datos = request.get_json()
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    usuario_objetivo = Usuario.query.get(id_usuario)

    if not usuario_objetivo:
        return jsonify({'error': 'Usuario a modificar no encontrado'}), 404

    if usuario_actual.rol == RolUsuario.ADMIN:
        pass  # Admin puede modificar todo
    elif usuario_actual.rol == RolUsuario.GERENTE:
        if usuario_objetivo.rol != RolUsuario.CHOFER:
            return jsonify({'error': 'Solo puedes modificar choferes'}), 403
        if usuario_objetivo.almacen_codigo != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No puedes modificar usuarios de otro almacén'}), 403
    else:
        return jsonify({'error': 'No tienes permisos para modificar usuarios'}), 403

    campos_modificables = ['nombre', 'activo']

    for campo in campos_modificables:
        if campo in datos:
            setattr(usuario_objetivo, campo, datos[campo]) # Setattr(objeto, atributo, valor)
                                                           # sirve para asignar dinámicamente un valor a un atributo de un objeto.

    try:
        db.session.commit()
        return jsonify(usuario_objetivo.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@usuarios_bp.route('/borrar-usuario/<int:id_usuario>', methods=['DELETE'])
@jwt_required()
def borrar_usuario(id_usuario):
    """
    Elimina un usuario del sistema.
    
    Requiere:
    - ADMIN: Puede borrar cualquier usuario
    - GERENTE: Solo puede borrar choferes de su mismo almacén
    - CHOFER: No puede hacer ningún movimiento
    
    Parámetros:
    id_usuario -- ID del usuario a eliminar
    
    Returns:
    Mensaje de éxito o error con el código HTTP apropiado
    """
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401
    
    usuario_borrar = Usuario.query.get(id_usuario)

    if not usuario_borrar:
        return jsonify({'error': 'Usuario a modificar no encontrado'}), 404

    if usuario_actual.rol == RolUsuario.ADMIN:
        pass
    elif usuario_actual.rol == RolUsuario.GERENTE:
        if usuario_borrar.rol != RolUsuario.CHOFER:
            return jsonify({'error': 'Solo puedes eliminar choferes'}), 403
        if usuario_borrar.almacen_codigo != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No puedes modificar usuarios de otro almacén'}), 403
    else: 
        return jsonify({'error': 'No tienes permisos para eliminar usuarios'})
    
    try:
        db.session.delete(usuario_borrar)
        db.session.commit()
        return jsonify({'success': 'Usuario eliminado correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@usuarios_bp.route('/ver-usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    usuario_actual = get_usuario_actual()

    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    if usuario_actual.rol == RolUsuario.ADMIN:
        usuarios = Usuario.query.all()
    elif usuario_actual.rol == RolUsuario.GERENTE:
        #usuarios = Usuario.query.filter_by(almacen_codigo=usuario_actual.almacen_codigo).all()
        usuarios = Usuario.query.filter(Usuario.almacen_codigo == usuario_actual.almacen_codigo,  Usuario.rol == RolUsuario.CHOFER).all()
    else:
        return jsonify({'error': 'No tienes permisos para ver esta información'}), 403

    return jsonify([usuario.to_dict() for usuario in usuarios]), 200


@usuarios_bp.route('/ver-usuario/<int:id_usuario>', methods=['GET'])
@jwt_required()
def obtener_usuario(id_usuario):
    """Obtiene los detalles de un usuario específico según permisos del solicitante.

    Permisos requeridos:
        - ADMIN: Puede ver cualquier usuario
        - GERENTE: Solo puede ver choferes de su mismo almacén
        - CHOFER: No tienen acceso

    Parámetros:
        id_usuario: ID del usuario a consultar

    Returns:
        Response: JSON con los datos del usuario si tiene permisos

    Errores:
        401: Si no hay usuario autenticado
        403: Si no tiene permisos para ver el usuario
        404: Si el usuario solicitado no existe
    """
    usuario_actual = get_usuario_actual()
    if not usuario_actual:
        return jsonify({'error': 'Usuario autenticado no encontrado'}), 401

    usuario_buscado = Usuario.query.get(id_usuario)
    if not usuario_buscado:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if usuario_actual.rol == RolUsuario.ADMIN:
        pass 
    elif usuario_actual.rol == RolUsuario.GERENTE:
        if usuario_buscado.rol != RolUsuario.CHOFER or usuario_buscado.almacen_codigo != usuario_actual.almacen_codigo:
            return jsonify({'error': 'No tienes permisos para ver esta información'}), 403
    else:
        return jsonify({'error': 'No tienes permisos para ver esta información'}), 403

    return jsonify(usuario_buscado.to_dict()), 200

@usuarios_bp.route('/login', methods=['POST'])
def login():
    datos = request.get_json()

    correo = datos.get('correo')
    contrasena = datos.get('contrasena')

    if not correo or not contrasena:
        return jsonify({'error': 'Correo y contraseña requeridos'}), 400

    usuario = Usuario.query.filter_by(correo=correo).first()

    if not usuario or not check_password_hash(usuario.contrasena_hash, contrasena):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    token = create_access_token(identity=str(usuario.id_usuario),additional_claims={"rol": usuario.rol.name,"almacen_codigo": usuario.almacen_codigo})

    return jsonify({
        'access_token': token,
        'usuario': usuario.to_dict()
    }), 200

@usuarios_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'msg': 'Sesión cerrada exitosamente'}), 200