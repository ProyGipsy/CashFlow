import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = pymssql.connect(
        server = os.getenv('DB_SERVER'),
        database = os.getenv('DB_NAME'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD')
    )
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
