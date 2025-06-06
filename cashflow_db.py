import os
import pymssql

def get_db_connection():
    server = os.environ.get('DB_SERVER')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    conn = pymssql.connect(server, user, password, database)
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


def get_operations():
    conn = get_db_connection()
    cursor = conn.cursor()
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
        ORDER BY O.OperationDate 
    ''')
    operations = cursor.fetchall()
    conn.close()

    # Calcular el saldo acumulado
    balance = 0
    operations_with_balance = []
    for operation in operations:
        credit = operation[9] if operation[9] is not None else 0
        debit = operation[10] if operation[10] is not None else 0
        balance += credit - debit

        formattedCredit = "{:,.2f}".format(credit).replace(".", "X").replace(",", ".").replace("X", ",")
        formattedDebit = "{:,.2f}".format(debit).replace(".", "X").replace(",", ".").replace("X", ",")
        formattedBalance = "{:,.2f}".format(balance).replace(".", "X").replace(",", ".").replace("X", ",")
        
        operation_list = list(operation)
        operation_list[9] = formattedCredit
        operation_list[10] = formattedDebit
        operation_list.append(formattedBalance)
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