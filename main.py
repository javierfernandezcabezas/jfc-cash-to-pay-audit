"""
Google Cloud Function: jfc-cash-to-pay-audit
Función HTTP que procesa auditorías de cash-to-pay
"""

import json
import logging
from typing import Any, Dict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def jfc_cash_to_pay_audit(request) -> Dict[str, Any]:
    """
    Función HTTP que procesa solicitudes de auditoría cash-to-pay.
    
    Args:
        request: Flask Request object con los datos de la solicitud
        
    Returns:
        Dict con la respuesta de la función
    """
    # Manejar CORS para peticiones desde navegadores
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Configurar headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Obtener datos de la solicitud
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = request.get_json(silent=True) or {}
        
        logger.info(f"Recibida solicitud: {request.method}")
        logger.info(f"Datos recibidos: {data}")
        
        # Aquí puedes agregar tu lógica de auditoría
        # Ejemplo de procesamiento
        result = {
            "status": "success",
            "message": "Auditoría procesada correctamente",
            "data_received": data,
            "function_name": "jfc-cash-to-pay-audit",
            "project_id": "check-in-sf"
        }
        
        logger.info(f"Respuesta generada: {result}")
        
        return (json.dumps(result), 200, headers)
        
    except Exception as e:
        logger.error(f"Error procesando la solicitud: {str(e)}", exc_info=True)
        error_response = {
            "status": "error",
            "message": f"Error procesando la solicitud: {str(e)}"
        }
        return (json.dumps(error_response), 500, headers)

