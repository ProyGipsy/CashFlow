import os
import pymssql

def get_db_connection():
    server = os.environ.get('DB_SERVER')
    database = os.environ.get('DB_NAME')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
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


def get_stores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT StoreID, StoreName FROM cashflow.store')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_last_store_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(StoreID) FROM cashflow.store")
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


def get_operations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            O.OperationID, 
            O.OperationDate, 
            S.StoreName, 
            C.ConceptName, 
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
            JOIN cashflow.store S ON O.StoreID = S.StoreID 
            JOIN cashflow.Concept C ON O.ConceptID = C.ConceptID 
            JOIN cashflow.Beneficiary B ON O.BeneficiaryID = B.BeneficiaryID 
    ''')
    operations = cursor.fetchall()
    conn.close()

    # Calcular el saldo acumulado
    saldo = 0
    operations_with_balance = []
    for operation in operations:
        credito = operation[6]
        debito = operation[7]
        saldo += credito - debito
        operation_list = list(operation)
        operation_list.append(saldo)
        operations_with_balance.append(tuple(operation_list))

    return operations_with_balance



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
            MERGE INTO cashflow.store AS target
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
        motion = concept['motion']
        cursor.execute(f"""
            MERGE INTO cashflow.Concept AS target
            USING (VALUES (%s, %s, %s, %s)) AS source (ConceptID, ConceptName, ConceptDescription, motion)
            ON target.ConceptID = source.ConceptID
            WHEN MATCHED THEN
                UPDATE SET target.ConceptName = source.ConceptName, target.ConceptDescription = source.ConceptDescription, target.motion = source.motion
            WHEN NOT MATCHED THEN
                INSERT (ConceptName, ConceptDescription, motion) VALUES (source.ConceptName, source.ConceptDescription, source.motion);
        """, (id, name, desc, motion))
    
    conn.commit()
    conn.close()

def set_operations(store_id, beneficiary_id, concept_id, observation, date_operation, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                INSERT INTO cashflow.Operation (StoreID, BeneficiaryID, ConceptID, Observation, OperationDate, OperationAmount)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (store_id, beneficiary_id, concept_id, observation, date_operation, amount))
    conn.commit()
    conn.close()
