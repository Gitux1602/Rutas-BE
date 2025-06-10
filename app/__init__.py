from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.db.connector import db, init_db
from dotenv import load_dotenv
import os

jwt = JWTManager() 

def create_app():
    load_dotenv()  # ← Carga variables del .env

    app = Flask(__name__)
    CORS(app)

    # Configuración JWT segura
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

    jwt.init_app(app)

    init_db(app)

    with app.app_context():
        db.create_all()

    # Registrar rutas
    from app.routes.sap_documents import sap_documents_bp
    from app.routes.almacenes import almacenes_bp
    from app.routes.usuarios import usuarios_bp

    app.register_blueprint(sap_documents_bp, url_prefix="/api")
    app.register_blueprint(almacenes_bp, url_prefix="/api")
    app.register_blueprint(usuarios_bp, url_prefix="/api")

    return app
