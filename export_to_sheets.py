"""
Módulo para exportar resultados de BigQuery a Google Sheets
"""

import logging
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def export_to_sheets(
    spreadsheet_id: str,
    sheet_name: str,
    data: List[Dict[str, Any]],
    credentials_path: str = None
):
    """
    Exporta datos a Google Sheets
    
    Args:
        spreadsheet_id: ID de la hoja de cálculo de Google Sheets
        sheet_name: Nombre de la hoja dentro del spreadsheet
        data: Lista de diccionarios con los datos a exportar
        credentials_path: Ruta al archivo de credenciales (opcional)
    """
    if not data:
        logger.warning("No hay datos para exportar")
        return
    
    try:
        # Obtener credenciales
        if credentials_path:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
        else:
            # Usar credenciales por defecto (Application Default Credentials)
            from google.auth import default
            creds, _ = default(scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        
        # Preparar datos: encabezados + filas
        if not data:
            return
        
        headers = list(data[0].keys())
        
        # Función para formatear valores numéricos
        def format_value(value, header):
            if value is None or value == '':
                return ''
            # Si es id_partner, formatear como entero
            if header == 'id_partner' or header.lower() == 'id_partner':
                try:
                    num_value = float(value)
                    return str(int(num_value))
                except (ValueError, TypeError):
                    return str(value)
            # Si es un número, formatear con 2 decimales
            try:
                num_value = float(value)
                # Formatear con 2 decimales, sin notación científica
                return f"{num_value:.2f}"
            except (ValueError, TypeError):
                # Si no es número, devolver como string
                return str(value)
        
        # Preparar valores con formato numérico
        values = [headers] + [[format_value(row.get(h, ''), h) for h in headers] for row in data]
        
        # Limpiar hoja existente o crear nueva
        try:
            # Intentar obtener la hoja
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_exists = any(s['properties']['title'] == sheet_name 
                             for s in spreadsheet.get('sheets', []))
            
            if not sheet_exists:
                # Crear nueva hoja
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=request_body
                ).execute()
        except HttpError as e:
            logger.error(f"Error al verificar/crear hoja: {e}")
            return
        
        # Limpiar contenido existente (sobrescribir todo)
        # Usar un rango grande para asegurar que se limpie todo
        range_name = f"{sheet_name}!A1:ZZ10000"
        try:
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            logger.info(f"Contenido anterior de la hoja '{sheet_name}' limpiado")
        except HttpError as e:
            logger.warning(f"No se pudo limpiar la hoja (puede que no exista): {e}")
        
        # Escribir datos
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Datos exportados exitosamente: {result.get('updatedCells')} celdas actualizadas")
        
    except HttpError as e:
        logger.error(f"Error exportando a Google Sheets: {e}")
        raise

