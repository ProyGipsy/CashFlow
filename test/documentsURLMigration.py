import os
import sys
import time
import pymssql
import tempfile
import requests

from google import genai
from datetime import datetime
from urllib.parse import quote
from dbutils.pooled_db import PooledDB
from msal import ConfidentialClientApplication

from dotenv import load_dotenv
load_dotenv()

pool = PooledDB(
    creator=pymssql,
    maxconnections = 15,
    mincached = 3,
    maxcached = 6,
    blocking = True,
    host = os.environ.get('DB_SERVER'),
    user = os.environ.get('DB_USER'),
    password = os.environ.get('DB_PASSWORD'),
    database = os.environ.get('DB_NAME')
)

# ==========================================
# CONFIGURACIÓN
# ==========================================
APP_CLIENT_ID_NEW = os.environ.get('APP_CLIENT_ID')
APP_CLIENT_SECRET_NEW = os.environ.get('APP_CLIENT_SECRET')
APP_TENANT_ID_NEW = os.environ.get('APP_TENANT_ID')

# SETUP GEMINI (Usando 2.5 Flash)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# DATOS ONEDRIVE
user_email = "desarrollo@grupogipsy.com"
folder_path = quote("GARANTIAS/Facturas")

# ARCHIVO DE RESPALDO (Log)
LOG_FILE = "mapeo_facturas.txt"

# MODO DE PRUEBA (False para que actualice la BD de verdad)
TEST_MODE = True

def get_onedrive_headers_manual(clientId, clientSecret, tenantId):
    msal_app = ConfidentialClientApplication(
        client_id = clientId,
        client_credential = clientSecret,
        authority = f"https://login.microsoftonline.com/{tenantId}"
    )
    result = msal_app.acquire_token_silent(scopes = ["https://graph.microsoft.com/.default"], account = None)
    if not result:
        result = msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" in result:
        return {
            "Authorization": f"Bearer {result['access_token']}",
            "Content-Type": "application/json",
        }
    else:
        raise Exception("No se pudo obtener el token de acceso")
    
def extraer_factura_gemini(download_url, file_name):
    response = requests.get(download_url)
    if response.status_code != 200:
        return "ERROR_DESCARGA"
        
    ext = os.path.splitext(file_name)[1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(response.content)
        temp_path = temp_file.name

    try:
        archivo_gemini = client.files.upload(file=temp_path)
        prompt = (
            "Eres un sistema experto en extracción de datos contables. "
            "Analiza este documento y extrae ÚNICAMENTE el número de factura o recibo. "
            "No incluyas ninguna otra palabra, texto o explicación. "
            "Si no logras encontrar un número de factura, responde exactamente con la palabra 'NOT_FOUND'."
        )
        respuesta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[archivo_gemini, prompt]
        )
        resultado = respuesta.text.strip()
        client.files.delete(name=archivo_gemini.name)
        return resultado
        
    except Exception as e:
        print(f"Error procesando con Gemini: {e}")
        return "ERROR_GEMINI"
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def guardar_log(texto):
    """Guarda una línea en el archivo de texto al instante."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(texto + "\n")

def data_migration():
    print("1. Obteniendo headers para tenant nuevo...")
    try:
        headers_new = get_onedrive_headers_manual(clientId=APP_CLIENT_ID_NEW, clientSecret=APP_CLIENT_SECRET_NEW, tenantId=APP_TENANT_ID_NEW)
    except Exception as e:
        print("Error obteniendo headers:", str(e))
        return
    
    print("\n2. Descarga de índice de archivos...")
    new_annexes_index = [] 
    try:
        graph_url_new = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{folder_path}:/children"
        while graph_url_new:
            response_new = requests.get(graph_url_new, headers=headers_new)
            if response_new.status_code == 200:
                data_new = response_new.json()
                for item in data_new.get('value', []):
                    try:
                        time_str = item['name'][:15]
                        file_datetime = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
                        new_annexes_index.append({
                            'name': item['name'],
                            'id': item['id'],
                            'datetime': file_datetime,
                            'download_url': item.get('@microsoft.graph.downloadUrl')
                        })
                    except ValueError:
                        pass 
                graph_url_new = data_new.get('@odata.nextLink')
            else:
                return
    except Exception as e:
        print("Error durante la descarga:", str(e))
        return
    
    print("\n3. Conexión a la BD...")
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)
    except Exception as e:
        print("Error BD:", str(e))
        return

    print("\n4. Emparejamiento Semántico...")
    
    # Escribimos el encabezado en el archivo de texto si es la primera vez
    if not os.path.exists(LOG_FILE):
        guardar_log("Archivo | Numero_Extraido_Gemini | WarrantyNumber_BD | Estado")

    for file_info in new_annexes_index:
        file_name = file_info['name']
        file_id = file_info['id']
        file_date = file_info['datetime'].strftime('%Y-%m-%d')
        download_url = file_info['download_url']
        
        print(f"\nProcesando: {file_name}")
        
        # 1. Extracción (¡Esto ya se cobra!)
        numero_factura = extraer_factura_gemini(download_url, file_name)
        
        if numero_factura in ["NOT_FOUND", "ERROR_DESCARGA", "ERROR_GEMINI"]:
            print(f"   [OMITIDO] Razón: {numero_factura}")
            guardar_log(f"{file_name} | {numero_factura} | N/A | FALLO_EXTRACCION")
            continue
            
        # 2. Búsqueda en SQL
        search_query = """
            SELECT WarrantyNumber 
            FROM Warranty.warranty
            WHERE CAST(registrationDate AS DATE) = %s AND invoiceNumber = %s 
        """
        cursor.execute(search_query, (file_date, numero_factura))
        match = cursor.fetchone()

        if not match:
            print(f"   [SIN COINCIDENCIA BD] Factura {numero_factura}")
            guardar_log(f"{file_name} | {numero_factura} | N/A | NO_ENCONTRADO_BD")
            continue

        warranty_number = match['WarrantyNumber']

        # 3. Generar enlace y actualizar BD
        new_public_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/items/{file_id}/createLink"
        link_response = requests.post(new_public_url, headers=headers_new, json={'type': 'view', 'scope': 'anonymous'})

        if link_response.status_code in (200, 201):
            new_annex_url = link_response.json()['link']['webUrl']
            new_annex_url += "&action=embedview" if "?" in new_annex_url else "?action=embedview"

            if TEST_MODE:
                print(f"   [SIMULACRO] WarrantyNumber {warranty_number} listo.")
                guardar_log(f"{file_name} | {numero_factura} | {warranty_number} | SIMULACRO_OK")
            else:
                try:
                    update_query = """
                        UPDATE Warranty.warranty 
                        SET invoiceCopyPath = %s, invoiceFileName = %s 
                        WHERE WarrantyNumber = %s
                    """
                    cursor.execute(update_query, (new_annex_url, file_name, warranty_number))
                    connection.commit()
                    print(f"   [OK] Garantía {warranty_number} actualizada.")
                    # ¡AQUÍ ESTÁ EL SALVAVIDAS! Guardamos el registro exitoso en el TXT
                    guardar_log(f"{file_name} | {numero_factura} | {warranty_number} | ACTUALIZADO_OK")
                except Exception as e:
                    connection.rollback()
                    guardar_log(f"{file_name} | {numero_factura} | {warranty_number} | ERROR_SQL")
        else:
            guardar_log(f"{file_name} | {numero_factura} | {warranty_number} | ERROR_ENLACE_MICROSOFT")

        # Sin los límites gratuitos, la pausa puede ser mínima o nula
        time.sleep(4.5) 

    if 'cursor' in locals() and cursor: cursor.close()
    if 'connection' in locals() and connection: connection.close()

if __name__ == "__main__":
    data_migration()