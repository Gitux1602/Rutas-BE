from app import db

class Unidad(db.Model):
    __tablename__ = 'unidades'

    id_unidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    placas = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.Text)
    almacen_codigo = db.Column(db.String(10), db.ForeignKey('almacenes.codigo'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    chofer_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)

    def to_dict(self):
        return {
            'id_unidad': self.id_unidad,
            'nombre': self.nombre,
            'placas': self.placas,
            'descripcion': self.descripcion,
            'almacen_codigo': self.almacen_codigo,
            'activo': self.activo,
            'chofer_id': self.chofer_id
        }
