import os
from hdbcli import dbapi
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()

# Configuración de conexión a SAP HANA
hana_config = {
    "host": os.getenv("HANA_HOST"),
    "port": int(os.getenv("HANA_PORT")),
    "user": os.getenv("HANA_USER"),
    "password": os.getenv("HANA_PASSWORD")
}

def get_db_connection(database_name):
    """
    Establece y devuelve una conexión a SAP HANA usando la base de datos indicada.
    """
    try:
        connection = dbapi.connect(
            address=hana_config["host"],
            port=hana_config["port"],
            user=hana_config["user"],
            password=hana_config["password"],
            database=database_name
        )
        return connection
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos HANA: {e}")
        return None
