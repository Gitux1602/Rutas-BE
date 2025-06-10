from app import db  

class Almacen(db.Model):
    __tablename__ = 'almacenes'

    codigo = db.Column(db.String(10), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'activo': self.activo
        }
