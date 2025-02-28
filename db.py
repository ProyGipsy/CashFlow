import os
import pymssql

def get_db_connection():
    server = os.environ['AZURE_SQL_SERVER']
    database = os.environ['AZURE_SQL_DATABASE']
    user = os.environ['AZURE_SQL_USER']
    password = os.environ['AZURE_SQL_PASSWORD']
    conn = pymssql.connect(server, database, user, password)
    return conn


# Obtención de Data en la Interfaz

def get_beneficiaries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT BeneficiaryID, BeneficiaryName FROM cashflow.Beneficiary')
    beneficiaries = cursor.fetchall()
    conn.close()
    return beneficiaries

def get_last_beneficiary_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(BeneficiaryID) FROM cashflow.Beneficiary")
    last_id = cursor.fetchone()[0] 
    conn.close()
    return last_id if last_id is not None else 0  # Retorna 0 si no hay registros
