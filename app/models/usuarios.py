from app import db
from enum import Enum
from sqlalchemy import Enum as SqlEnum 

class RolUsuario(Enum):
    ADMIN = 'ADMIN'
    GERENTE = 'GERENTE'
    CHOFER = 'CHOFER'

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        SqlEnum(RolUsuario, values_callable=lambda x: [e.name for e in x]),  
        nullable=False
    )
    almacen_codigo = db.Column(db.String(10), db.ForeignKey('almacenes.codigo'))
    activo = db.Column(db.Boolean, default=True)
    cambiar_contrasena = db.Column(db.Boolean, default=False) 
    almacen = db.relationship('Almacen', backref='usuarios')

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nombre': self.nombre,
            'correo': self.correo,
            'rol': self.rol.name if self.rol else None,  
            'almacen_codigo': self.almacen_codigo,
            'activo': self.activo,
            'cambiar_contrasena': self.cambiar_contrasena  
        }

