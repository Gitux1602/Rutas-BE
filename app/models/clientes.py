from app.db.connector import db

class Cliente(db.Model):
    """Modelo de cliente usando SQLAlchemy"""
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    fecha_nacimiento = db.Column(db.Date)
    saldo = db.Column(db.Numeric(10, 2))

    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'saldo': float(self.saldo) if self.saldo else 0.0
        }