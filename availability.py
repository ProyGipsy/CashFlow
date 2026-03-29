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

def get_accounts_by_bank(bank_id):
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
        WHERE BankID = %s AND IsActive = 1
        ORDER BY AccountName ASC
        """

        cursor.execute(sql, (bank_id,))
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