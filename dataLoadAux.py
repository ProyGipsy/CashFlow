import os
import pymssql
import numpy as np
import pandas as pd

from datetime import datetime
from dbutils.pooled_db import PooledDB
from emailScript import (
    send_email,
    create_doc_type_html,
    create_new_doc_html,
    generate_document_content_html,
    create_custom_email_html,
    create_send_notification_html,
)

from documents import (
    create_company,
    create_document,
    get_doc_type_full,
)

from dataDocsFromExcel import (
    companies,
    rif_list,
    vehicules_list,
    pw_list,
    p_sanit_loc_list,
    p_seguros_vh,
    p_seguros_emp,
    patent_list,
    reg_merc_map,
    reg_sanit_map,
    generate_payloads_from_df,
    generate_payloads_typed,
    MAPA_EMPRESAS,
)

# Configuración del pool de conexiones

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

def cleaning(docId):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor() # No hace falta as_dict=True para borrar

        # 1. (Opcional) Borrar Anexos si existen (según tu código anterior)
        delete_annex_sql = "DELETE FROM Documents.DocumentAnnex WHERE DocumentID = %s"
        cursor.execute(delete_annex_sql, (docId,))

        # 2. Borrar Valores (Hijos)
        delete_fields_sql = "DELETE FROM Documents.FieldValue WHERE DocumentID = %s"
        cursor.execute(delete_fields_sql, (docId,)) # <--- OJO A LA COMA

        # 3. Borrar Documento (Padre)
        delete_doc_sql = "DELETE FROM Documents.Document WHERE DocumentID = %s"
        cursor.execute(delete_doc_sql, (docId,))   # <--- OJO A LA COMA

        # 4. CRÍTICO: Guardar los cambios
        connection.commit()
        
        print(f"Documento {docId} eliminado correctamente.")

    except Exception as e:
        # 5. Buena práctica: Deshacer si hay error
        if connection: connection.rollback()
        print(f"Error al borrar: {e}")

    finally:
        if cursor: cursor.close()
        if connection: connection.close()


file_path = r'./static/data/BASE DE DATOS DOCUMENTOS.xlsx'
def get_reg_sanit():
    df = pd.read_excel(file_path, sheet_name='Registro Sanitario')
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.dropna(how='all')

    return df

def get_reg_merc():
    df = pd.read_excel(file_path, sheet_name='Registros Mercantiles')
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df = df.dropna(how='all')

    if 'Columna1' in df.columns:
        df = df.drop(columns=['Columna1'])

    return df

if __name__ == "__main__":
    
    #for company in companies:
    #    create_company(company)

    #for rif in rif_list:
    #    create_document(rif, file_url = None)

    #for vehicule in vehicules_list:
    #    create_document(vehicule, file_url = None)

    #for pw in pw_list:
    #    create_document(pw, file_url = None)

    #for p in p_sanit_loc_list:
    #    create_document(p, file_url = None)

    #for vh in p_seguros_vh:
    #    create_document(vh, file_url = None)

    #for emp in p_seguros_emp:
    #    create_document(emp, file_url = None)

    #for patent in patent_list:
    #    create_document(patent, file_url = None)

    #df_reg_sanit = get_reg_sanit()
    #reg_sanit_list = generate_payloads_from_df(df_reg_sanit, doc_type_id=24, company_id=1, mapping=reg_sanit_map)
    
    #for rs in reg_sanit_list:
    #    create_document(rs, file_url = None)

    df_reg_merc = get_reg_merc()
    reg_merc_list = generate_payloads_typed(df_reg_merc, doc_type_id=21, companies_dict=MAPA_EMPRESAS, mapping=reg_merc_map)
    
    for rm in reg_merc_list:
        create_document(rm, file_url = None)