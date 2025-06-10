from flask_jwt_extended import get_jwt_identity
from app.models.usuarios import Usuario  

def get_usuario_actual():
    id_usuario = get_jwt_identity()
    if not id_usuario:
        return None
    return Usuario.query.get(id_usuario)
