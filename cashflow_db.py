import os
import pymssql
from dbutils.pooled_db import PooledDB

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

def get_db_connection():
    return pool.connection()


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


def get_cashflowStores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT StoreID, StoreName FROM cashflow.Store')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_last_store_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(StoreID) FROM cashflow.Store")
    last_id = cursor.fetchone()[0] 
    conn.close()
    return last_id if last_id is not None else 0  # Retorna 0 si no hay registros


def get_concepts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT C.ConceptID, C.ConceptName, C.ConceptDescription, M.MotionType FROM cashflow.Concept C JOIN cashflow.Motion M ON C.MotionID = M.MotionID')
    concepts = cursor.fetchall()
    conn.close()
    return concepts

def get_creditConcepts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT C.ConceptID, C.ConceptName, C.ConceptDescription, M.MotionType FROM cashflow.Concept C JOIN cashflow.Motion M ON C.MotionID = M.MotionID WHERE C.MotionID = 1')
    creditConcepts = cursor.fetchall()
    conn.close()
    return creditConcepts

def get_debitConcepts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT C.ConceptID, C.ConceptName, C.ConceptDescription, M.MotionType FROM cashflow.Concept C JOIN cashflow.Motion M ON C.MotionID = M.MotionID WHERE C.MotionID = 2')
    debitConcepts = cursor.fetchall()
    conn.close()
    return debitConcepts

def get_last_concept_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ConceptID) FROM cashflow.Concept")
    last_id = cursor.fetchone()[0] 
    conn.close()
    return last_id if last_id is not None else 0  # Retorna 0 si no hay registros

def get_motion_id(MotionType):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT MotionID FROM cashflow.Motion WHERE MotionType = %s"
    cursor.execute(query, (MotionType,))
    motion_id = cursor.fetchone()[0]
    conn.close()
    return motion_id

#anterior casi
def get_operations(page=1, page_size=500):
    """
    Devuelve las operaciones paginadas con un saldo acumulado correcto.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Se obtienen todas las operaciones en el orden correcto para calcular el saldo acumulado
    cursor.execute('''
        SELECT 
            O.OperationID, 
            O.OperationDate, 
            S.StoreID, 
            S.StoreName, 
            C.ConceptID,
            C.ConceptName, 
            B.BeneficiaryID,
            B.BeneficiaryName, 
            Observation, 
            CASE 
                WHEN C.MotionID = 1 THEN OperationAmount 
                ELSE 0 
            END AS Crédito,
            CASE 
                WHEN C.MotionID = 2 THEN OperationAmount 
                ELSE 0 
            END AS Débito
        FROM 
            cashflow.Operation O 
            JOIN cashflow.Store S ON O.StoreID = S.StoreID 
            JOIN cashflow.Concept C ON O.ConceptID = C.ConceptID 
            JOIN cashflow.Beneficiary B ON O.BeneficiaryID = B.BeneficiaryID
        ORDER BY O.OperationDate ASC, O.OperationID ASC
    ''')
    all_operations = cursor.fetchall()
    conn.close()

    # Calcular el saldo acumulado para todas las operaciones de forma secuencial
    balance = 0
    operations_with_balance_chronological = []
    
    for operation in all_operations:
        credit = operation[9] if operation[9] is not None else 0
        debit = operation[10] if operation[10] is not None else 0
        
        if operation[4] != 79: # Las operaciones con concepto 79 (Shajor) no afectan el saldo
            balance += credit - debit
        
        operation_list = list(operation)
        operation_list.append(balance)
        operations_with_balance_chronological.append(tuple(operation_list))

    # Invertir el orden para que la operación más reciente esté primero para la interfaz
    operations_with_balance = operations_with_balance_chronological[::-1]
    
    # Aplicar la paginación a la lista ya invertida
    final_operations = []
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    for operation in operations_with_balance[start_index:end_index]:
        operation_list = list(operation)
        
        # Formatear el crédito y el débito
        credit = operation_list[9] if operation_list[9] is not None else 0
        debit = operation_list[10] if operation_list[10] is not None else 0
        balance_val = operation_list[11] if operation_list[11] is not None else 0

        formattedCredit = "{:,.2f}".format(credit).replace(".", "X").replace(",", ".").replace("X", ",")
        formattedDebit = "{:,.2f}".format(debit).replace(".", "X").replace(",", ".").replace("X", ",")
        formattedBalance = "{:,.2f}".format(balance_val).replace(".", "X").replace(",", ".").replace("X", ",")
        
        operation_list[9] = formattedCredit
        operation_list[10] = formattedDebit
        operation_list[11] = formattedBalance
        
        final_operations.append(tuple(operation_list))

    return final_operations


# Para obtener el total de operaciones (para la paginación en el frontend)
def get_operations_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM cashflow.Operation')
    total = cursor.fetchone()[0]
    conn.close()
    return total



# Escritura de Data en la BD a través de la Interfaz:

def set_beneficiaries(beneficiaries):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for beneficiary in beneficiaries:
        id = beneficiary['id']
        name = beneficiary['name']
        cursor.execute(f"""
            MERGE INTO cashflow.Beneficiary AS target
            USING (VALUES (%s, %s)) AS source (BeneficiaryID, BeneficiaryName)
            ON target.BeneficiaryID = source.BeneficiaryID
            WHEN MATCHED THEN
                UPDATE SET target.BeneficiaryName = source.BeneficiaryName
            WHEN NOT MATCHED THEN
                INSERT (BeneficiaryName) VALUES (source.BeneficiaryName);
        """, (id, name))
    
    conn.commit()
    conn.close()

def set_stores(stores):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for store in stores:
        id = store['id']
        name = store['name']
        cursor.execute(f"""
            MERGE INTO cashflow.Store AS target
            USING (VALUES (%s, %s)) AS source (StoreID, StoreName)
            ON target.StoreID = source.StoreID
            WHEN MATCHED THEN
                UPDATE SET target.StoreName = source.StoreName
            WHEN NOT MATCHED THEN
                INSERT (StoreName) VALUES (source.StoreName);
        """, (id, name))
    
    conn.commit()
    conn.close()

def set_concepts(concepts):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for concept in concepts:
        id = concept['id']
        name = concept['name']
        desc = concept['desc']
        motion_id = concept['motion']
        
        cursor.execute(f"""
            MERGE INTO cashflow.Concept AS target
            USING (VALUES (%s, %s, %s, %s)) AS source (ConceptID, ConceptName, ConceptDescription, MotionID)
            ON target.ConceptID = source.ConceptID
            WHEN MATCHED THEN
                UPDATE SET 
                    target.ConceptName = source.ConceptName, 
                    target.ConceptDescription = source.ConceptDescription, 
                    target.MotionID = source.MotionID
            WHEN NOT MATCHED THEN
                INSERT (ConceptName, ConceptDescription, MotionID) 
                VALUES (source.ConceptName, source.ConceptDescription, source.MotionID);
        """, (id, name, desc, motion_id))
    
    conn.commit()
    conn.close()


def set_operations(store_id, beneficiary_id, concept_id, observation, date_operation, amount, operation_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if operation_id:
        cursor.execute('''
            UPDATE cashflow.Operation
            SET StoreID = %s, BeneficiaryID = %s, ConceptID = %s, Observation = %s, OperationDate = %s, OperationAmount = %s
            WHERE OperationID = %s
        ''', (store_id, beneficiary_id, concept_id, observation, date_operation, amount, operation_id))
        conn.commit()
        conn.close()
        return operation_id
    else:
        cursor.execute('''
            INSERT INTO cashflow.Operation (StoreID, BeneficiaryID, ConceptID, Observation, OperationDate, OperationAmount)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (store_id, beneficiary_id, concept_id, observation, date_operation, amount))
        cursor.execute("SELECT SCOPE_IDENTITY() AS new_id")
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return new_id