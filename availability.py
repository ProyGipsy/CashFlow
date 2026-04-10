import os
import json
import pymssql

from datetime import datetime
from collections import Counter
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

def get_transaction_statuses():
    """
    Obtiene los estados disponibles para las transacciones.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT TransitStatusID, StatusCode, StatusName, IsFinal, SortOrder
        FROM AccountBalance.TransitStatus
        """

        cursor.execute(sql)
        statuses = cursor.fetchall()

        return statuses

    except Exception as e:
        print(f"Error al obtener los estados de transacción: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_banks():
    """
    Obtiene la lista de bancos disponibles.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT BankID, BankName
        FROM AccountBalance.Bank
        """

        cursor.execute(sql)
        banks = cursor.fetchall()

        return banks

    except Exception as e:
        print(f"Error al obtener la lista de bancos: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_accounts_by_bank_and_entity(bank_id, entity_id):
    """
    Obtiene las cuentas asociadas a un banco específico.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT AccountID, AccountNumber, AccountName, CurrencyID
        FROM AccountBalance.Account
        WHERE BankID = %s AND EntityID = %s AND IsActive = 1
        ORDER BY AccountName ASC
        """

        cursor.execute(sql, (bank_id, entity_id))
        accounts = cursor.fetchall()

        #print(f"Cuentas obtenidas para el banco {bank_id}: {accounts}")
        return accounts

    except Exception as e:
        print(f"Error al obtener las cuentas por banco: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_entities():
    """
    Obtiene la lista de entidades disponibles.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT EntityID, EntityName
        FROM AccountBalance.Entity
        """

        cursor.execute(sql)
        entities = cursor.fetchall()

        return entities

    except Exception as e:
        print(f"Error al obtener la lista de entidades: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_currencies():
    """
    Obtiene la lista de monedas disponibles.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT CurrencyID, CurrencyCode, CurrencyName
        FROM AccountBalance.Currency
        """

        cursor.execute(sql)
        currencies = cursor.fetchall()

        return currencies

    except Exception as e:
        print(f"Error al obtener la lista de monedas: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_transit_transactions():
    """
    Obtiene las transacciones en tránsito.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT 
            T.TransitTransactionID AS id, 
            CAST(T.TransactionTime AS DATE) AS date, -- CAST opcional para que envíe solo YYYY-MM-DD
            C.CurrencyName AS currency, 
            E.EntityName AS entity, 
            B.BankName AS bank, 
            A.AccountNumber AS account, 
            T.Reference AS reference, 
            T.Concept AS concept, 
            T.Amount AS amount, 
            S.StatusName AS status
        FROM AccountBalance.TransitTransaction T
            -- 1. Primero unimos la cuenta a la transacción
            INNER JOIN AccountBalance.Account A ON T.AccountID = A.AccountID
            
            -- 2. Ahora, a través de la cuenta, llegamos al Banco y a la Moneda
            INNER JOIN AccountBalance.Bank B ON A.BankID = B.BankID
            INNER JOIN AccountBalance.Currency C ON A.CurrencyID = C.CurrencyID
            
            -- 3. La Entidad y el Estado sí están directo en la transacción
            INNER JOIN AccountBalance.Entity E ON T.EntityID = E.EntityID
            INNER JOIN AccountBalance.TransitStatus S ON T.TransitStatusID = S.TransitStatusID
        ORDER BY 
            T.TransactionTime DESC
        """
        cursor.execute(sql)
        
        transactions = cursor.fetchall()

        return transactions
    
    except Exception as e:
        print(f"Error al obtener las transacciones en tránsito: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_transaction(data):
    """
    Crea una nueva transacción en tránsito.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor()

        status_id = data.get('TransitStatusID', 1)
        
        from datetime import datetime
        executed_at = datetime.now() if status_id == 2 else None
        cancelled_at = datetime.now() if status_id == 3 else None

        sql = """
            SET NOCOUNT ON;
            
            INSERT INTO AccountBalance.TransitTransaction 
            (TransactionTime, EntityID, AccountID, Reference, Concept, Amount, TransitStatusID, ExecutedAt, CancelledAt, CreatedAt, UpdatedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), GETDATE());
            
            SELECT SCOPE_IDENTITY();
        """

        cursor.execute(sql, (
            data['DateTrx'],
            data['EntityID'],
            data['AccountID'],
            data.get('ReferenceDoc', ''),
            data['Concept'],
            data['Amount'],
            status_id,
            executed_at,
            cancelled_at
        ))

        # 1. PRIMERO leemos el resultado del SELECT SCOPE_IDENTITY()
        row = cursor.fetchone()
        
        if not row or row[0] is None:
            raise Exception("El INSERT fue exitoso pero SCOPE_IDENTITY devolvió nulo.")
            
        new_id = int(row[0])
        
        # 2. DESPUÉS hacemos el commit para guardar los cambios en BD
        connection.commit()
        
        return new_id

    except Exception as e:
        print(f"Error al crear la transacción: {e}")
        # Hacemos rollback en caso de que algo falle
        if connection:
            connection.rollback()
        return False

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def update_transaction(transaction_id, data):
    """
    Actualiza una transacción en tránsito existente.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor()
        
        status_id = data['TransitStatusID']

        # Usamos CASE WHEN en SQL para proteger las fechas de ejecución/anulación previas
        sql = """
            UPDATE [AccountBalance].[TransitTransaction]
            SET TransactionTime = %s, 
                EntityID = %s, 
                AccountID = %s, 
                Reference = %s, 
                Concept = %s, 
                Amount = %s, 
                TransitStatusID = %s,
                ExecutedAt = CASE 
                                WHEN %s = 2 THEN COALESCE(ExecutedAt, GETDATE()) 
                                WHEN %s = 1 THEN NULL 
                                ELSE ExecutedAt 
                             END,
                CancelledAt = CASE 
                                WHEN %s = 3 THEN COALESCE(CancelledAt, GETDATE()) 
                                WHEN %s = 1 THEN NULL 
                                ELSE CancelledAt 
                              END,
                UpdatedAt = GETDATE()
            WHERE TransitTransactionID = %s
        """
        
        cursor.execute(sql, (
            data['DateTrx'],
            data['EntityID'],
            data['AccountID'],
            data.get('ReferenceDoc', ''),
            data['Concept'],
            data['Amount'],
            status_id,
            # Parámetros repetidos para evaluar el CASE de ExecutedAt
            status_id, status_id, 
            # Parámetros repetidos para evaluar el CASE de CancelledAt
            status_id, status_id, 
            transaction_id
        ))

        connection.commit()
        return cursor.rowcount > 0  

    except pymssql.Error as db_err:
        print(f"Error de BD/Driver al actualizar la transacción {transaction_id}: {db_err}")
        if connection:
            connection.rollback()
        return False
    
    except Exception as e:
        print(f"Error al actualizar la transacción: {e}")
        return False

    finally:
        if cursor: cursor.close()
        if connection: connection.close()


def get_banks_by_entity(entity_id):
    """
    Obtiene los bancos únicos que tienen cuentas activas asociadas a una entidad específica.
    """
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT DISTINCT B.BankID, B.BankName
        FROM AccountBalance.Bank B
        INNER JOIN AccountBalance.Account A ON B.BankID = A.BankID
        WHERE A.EntityID = %s AND A.IsActive = 1
        ORDER BY B.BankName ASC
        """

        cursor.execute(sql, (entity_id,))
        banks = cursor.fetchall()

        return banks

    except Exception as e:
        print(f"Error al obtener los bancos por entidad: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()