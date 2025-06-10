# 🚚 Sistema de Gestión de Rutas de Entrega (Backend)

## 🔍 Descripción
Sistema integral para administrar rutas de entrega entre almacenes con autenticación por roles e integración de múltiples bases de datos.

## ✨ Características Principales
## 🔧 Módulos Principales

| 🔐 **Autenticación Avanzada**                | 🗃️ **Integración de Bases de Datos**                       | 📍 **Gestión de Rutas en Tiempo Real**      
|-------------------------------------         |------------------------------------------                   |--------------------------------------------
| • 3 roles jerárquicos (Admin/Gerente/Chofer) | • **MySQL**: Control completo de rutas, unidades y usuarios | • Estados automáticos (Pendiente/En Ruta/Entregado)
| • JWT con encriptación HS256                 | • **SAP HANA**: Conexión directa a facturas                 | • Registro de hora exacta en cada evento  
| • Permisos por almacén (T001, T002...)       | • Múltiples facturas por parada                             |  • Manejo de excepciones (clientes no disponibles) 
| • Session management con Flask-Login                                   


## 🛠️ Stack Tecnológico
Flask | MySQL | SAP HANA Connector | JWT Auth

# 🚀 Instalación
git clone https://github.com/Gitux1602/Rutas-BE.git         cd Rutas-BE         pip install -r requirements.txt
