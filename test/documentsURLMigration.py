import os
import sys
import time
import requests
from datetime import datetime, date
from urllib.parse import quote
from collections import defaultdict

# 1. Ajuste de PATH para importaciones absolutas (Debe ir al principio)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from documents import pool
from onedrive import get_onedrive_headers_manual
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CONFIGURACIÓN
# ==========================================
# SETUP DE CREDENCIALES TENANT NUEVO
APP_CLIENT_ID_NEW = os.environ.get('APP_CLIENT_ID')
APP_CLIENT_SECRET_NEW = os.environ.get('APP_CLIENT_SECRET')
APP_TENANT_ID_NEW = os.environ.get('APP_TENANT_ID')

# DATOS ONEDRIVE
user_email = "desarrollo@grupogipsy.com"
folder_path = quote("APP DOCUMENTOS/Anexos")

# MODO DE PRUEBA (True = Solo imprime, False = Actualiza la BD)
TEST_MODE = True

def data_migration():
    print("1. Obteniendo headers para tenant nuevo...")
    try:
        headers_new = get_onedrive_headers_manual(
            clientId = APP_CLIENT_ID_NEW,
            clientSecret = APP_CLIENT_SECRET_NEW,
            tenantId = APP_TENANT_ID_NEW
        )
        print("Headers obtenidos para tenant nuevo.")
    
    except Exception as e:
        print("Error obteniendo headers para tenant nuevo:", str(e))
        return
    
    print("\n2. Descarga de índice de archivos del Tenant nuevo...")
    new_annexes_index = [] 
    
    try:
        graph_url_new = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{folder_path}:/children"

        while graph_url_new:
            response_new = requests.get(graph_url_new, headers=headers_new)

            if response_new.status_code == 200:
                data_new = response_new.json()
                for item in data_new.get('value', []):
                    nombre_archivo = item['name']
                    file_id = item['id']
                    
                    # Extraer la fecha del nombre: "20260324_153022_factura.pdf" -> "20260324_153022"
                    try:
                        time_str = nombre_archivo[:15]
                        file_datetime = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
                        
                        new_annexes_index.append({
                            'name': nombre_archivo,
                            'id': file_id,
                            'datetime': file_datetime
                        })
                    except ValueError:
                        pass # Ignoramos los archivos que no cumplan el formato de fecha esperado
                        
                graph_url_new = data_new.get('@odata.nextLink')
            else:
                print(f"Error obteniendo archivos: {response_new.status_code} - {response_new.text}")
                return
        
        print(f"Total de archivos procesables en tenant nuevo: {len(new_annexes_index)}")

    except Exception as e:
        print("Error durante la descarga del índice:", str(e))
        return
    
    print("\n3. Conexión a la BD y obtención del listado de anexos...")
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        get_annex_query = """
        SELECT DocumentID, Date, AnnexURL
        FROM Documents.DocumentAnnex
        WHERE AnnexURL IS NOT NULL
        """

        cursor.execute(get_annex_query)
        annexes = cursor.fetchall()

        print(f"Total de anexos a procesar en BD: {len(annexes)}")

    except Exception as e:
        print("Error conectando a la BD o ejecutando la consulta:", str(e))
        return
    
    print("\n4. Emparejamiento Secuencial por Día (Orden de Llegada)...")
    try:
        # Diccionarios para agrupar por fecha 'YYYY-MM-DD'
        db_por_dia = defaultdict(list)
        archivos_por_dia = defaultdict(list)

        # 4.1 Agrupar registros de BD por día
        for annex in annexes:
            doc_id = annex['DocumentID']
            db_date = annex['Date']
            
            if not db_date:
                continue
                
            # Extraer solo la fecha (YYYY-MM-DD) independientemente de si es string o date
            if isinstance(db_date, str):
                fecha_str = db_date.split(' ')[0]
            else:
                fecha_str = db_date.strftime('%Y-%m-%d')
                
            db_por_dia[fecha_str].append(annex)

        # 4.2 Agrupar archivos de OneDrive por día
        for archivo in new_annexes_index:
            fecha_str = archivo['datetime'].strftime('%Y-%m-%d')
            archivos_por_dia[fecha_str].append(archivo)

        annexes_updated = 0
        errores = 0
        discrepancias = 0

        # 4.3 PROCESAR DÍA POR DÍA
        for dia, registros_bd in db_por_dia.items():
            archivos_onedrive = archivos_por_dia.get(dia, [])

            # CRÍTICO: La cantidad de documentos en la BD ese día debe ser igual a los archivos subidos ese día
            if len(registros_bd) == len(archivos_onedrive):
                
                # ORDENAMOS BD por DocumentID (Menor a Mayor = Más viejo a Más nuevo)
                registros_bd.sort(key=lambda x: x['DocumentID'])
                
                # ORDENAMOS Archivos por Fecha Exacta (Más temprano a Más tarde)
                archivos_onedrive.sort(key=lambda x: x['datetime'])

                # EMPAREJAMOS 1 a 1
                for i in range(len(registros_bd)):
                    doc_id = registros_bd[i]['DocumentID']
                    file_info = archivos_onedrive[i]
                    file_name = file_info['name']
                    new_file_id = file_info['id']

                    # Generar enlace público
                    new_public_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/items/{new_file_id}/createLink"
                    body = { 'type': 'view', 'scope': 'anonymous' }
                    link_response = requests.post(new_public_url, headers=headers_new, json=body)

                    if link_response.status_code in (200, 201):
                        new_annex_url = link_response.json()['link']['webUrl']
                        new_annex_url += "&action=embedview" if "?" in new_annex_url else "?action=embedview"

                        if TEST_MODE:
                            print(f"[SIMULACRO PERFECTO] Día {dia} | Doc_ID {doc_id} -> Asignado a: {file_name}")
                        
                        else:
                            try:
                                update_query = "UPDATE Documents.DocumentAnnex SET AnnexURL = ? WHERE DocumentID = ?"
                                cursor.execute(update_query, (new_annex_url, doc_id))
                                connection.commit()
                                print(f"[OK] Doc {doc_id} actualizado exitosamente.")
                                annexes_updated += 1
                            
                            except Exception as e:
                                print(f"[ERROR BD] Falló guardado del Doc {doc_id}: {str(e)}")
                                connection.rollback()
                                errores += 1
                    else:
                        print(f"[ERROR API] Falló enlace público para {file_name}: {link_response.text}")
                        errores += 1
                        
                    # Pausa antibloqueo para la API de Microsoft
                    time.sleep(0.2) 
            else:
                if len(registros_bd) > 0:
                    print(f"\n[ALERTA DISCREPANCIA] Día {dia}: Hay {len(registros_bd)} docs en BD, pero {len(archivos_onedrive)} archivos en OneDrive.")
                    discrepancias += len(registros_bd)

        print("\n" + "="*40)
        print("RESUMEN FINAL SECUENCIAL")
        print("="*40)

        # Calculamos cuántos pasarán exitosamente basándonos en si las listas coinciden
        exitosos_simulados = sum(len(v) for k, v in db_por_dia.items() if len(v) == len(archivos_por_dia.get(k, [])))
        
        print(f"Total emparejados exitosamente: {annexes_updated if not TEST_MODE else exitosos_simulados}")
        print(f"Documentos en días con discrepancias: {discrepancias}")
        print(f"Total errores de API/BD: {errores}")
        print("="*40)

    except Exception as e:
        print("Error durante el emparejamiento secuencial:", str(e))
        import traceback
        traceback.print_exc()
        return
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
            print("Cursor de la BD cerrado.")

        if 'connection' in locals() and connection:
            connection.close()
            print("Conexión a la BD cerrada.")

if __name__ == "__main__":
    data_migration()