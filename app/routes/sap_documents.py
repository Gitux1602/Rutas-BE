from flask import Blueprint, jsonify, request
from app.db.hana import get_db_connection
from datetime import datetime

sap_documents_bp = Blueprint("sap_documents", __name__)

@sap_documents_bp.route('/sap-documents', methods=['GET'])
def obtener_documentos_sap():
    # 1. Obtener y validar parámetros
    card_code = request.args.get('cardCode')
    database_name = request.args.get('database')
    
    if not card_code or not database_name:
        return jsonify({"error": "Se requieren cardCode y database"}), 400
    
    # 2. Establecer conexión
    conn = get_db_connection(database_name)
    if not conn:
        return jsonify({"error": "Error de conexión a HANA"}), 500
    
    try:
        cursor = conn.cursor()
        
        # 3. Consulta SQL
        query = f"""
        SELECT 
            'Factura' AS "TipoDocumento",
            "DocEntry", "DocNum", "DocDate", "DocDueDate", 
            "CardCode", "CardName", "DocTotal", "PaidToDate",
            ("DocTotal" - "PaidToDate") AS "SaldoPendiente"
        FROM 
            {database_name}.OINV
        WHERE 
            "CardCode" = '{card_code}' 
        """
        cursor.execute(query)
        
        # 4. Obtener nombres de columnas
        column_names = [col[0] for col in cursor.description] # Obtener nombres de columnas (fila 0, que son las cabeceras)
                                                              # cursor.description te devuelve una lista de tuplas, donde cada tupla representa una columna con su información.
        
        # 5. Procesar resultados 
        facturas = []
        for row in cursor.fetchall():
            documento = {
                column_names[i]: (row[i].strftime('%Y-%m-%d') if isinstance(row[i], datetime) else row[i])    #Ternary expression
                for i in range(len(column_names))                                                             #<valor_si_true> if <condición> else <valor_si_false>
                #(clave: valor) (for variable in iterable)
            }
            facturas.append(documento)
        
        # 6. Calcular total pendiente
        total_pendiente = sum(factura["SaldoPendiente"] for factura in facturas)
        
        # 7. Retornar respuesta
        return jsonify({
            "success": True,
            "facturas": facturas,
            "total_pendiente": total_pendiente
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()