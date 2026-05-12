import os
import json
import shutil
import pymssql
import requests
import tempfile

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

def add_purchase(data):
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor()

        # Completamos a 20 dígitos si es necesario por reglas de la BD
        account_padded = str(data['account']).zfill(20)

        # ELIMINADO: BolivarsAmount de la lista de columnas y un %s de los valores
        sql = """
            INSERT INTO Exchange.CurrencyPurchase 
            (PurchaseDate, EntityID, BankID, AccountNumber, DollarsPurchased, ExchangeRate, Observations, CreatedAt, UpdatedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, GETDATE(), GETDATE());

            SELECT SCOPE_IDENTITY();
        """
        
        # ELIMINADO: data['bolivares'] de la tupla de ejecución
        cursor.execute(sql, (
            data['date'], 
            data['entityId'], 
            data['bankId'], 
            account_padded, 
            data['dollarsBought'], 
            data['exchangeRate'], 
            data['observations']
        ))
        
        result = cursor.fetchone()
        new_id = result[0] if result else None
        connection.commit()
        return new_id

    except Exception as e:
        if connection: connection.rollback()
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


def update_purchase(purchase_id, data):
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor()
        
        account_padded = str(data['account']).zfill(20)

        # ELIMINADO: BolivarsAmount = %s del bloque SET
        sql = """
            UPDATE Exchange.CurrencyPurchase
            SET PurchaseDate = %s,
                EntityID = %s,
                BankID = %s,
                AccountNumber = %s,
                DollarsPurchased = %s,
                ExchangeRate = %s,
                Observations = %s,
                UpdatedAt = GETDATE()
            WHERE CurrencyPurchaseID = %s
        """
        
        # ELIMINADO: data['bolivares'] de la tupla de ejecución
        cursor.execute(sql, (
            data['date'], 
            data['entityId'], 
            data['bankId'], 
            account_padded, 
            data['dollarsBought'], 
            data['exchangeRate'], 
            data['observations'], 
            purchase_id
        ))
        
        connection.commit()
        return cursor.rowcount > 0

    except Exception as e:
        if connection: connection.rollback()
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_purchases_list():
    connection = None
    cursor = None
    purchases = []

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Ajustado para usar Exchange.Beneficiary y AccountBalance.Bank
        sql = """
            SELECT 
                P.CurrencyPurchaseID AS id,
                CONVERT(varchar, P.PurchaseDate, 23) AS date,
                B.BeneficiaryName AS company,  -- Ahora sacamos el nombre de la tabla Beneficiary
                BK.BankName AS bank,           -- Ahora sacamos el banco de AccountBalance.Bank
                P.AccountNumber AS account,
                P.DollarsPurchased AS dollarsBought,
                P.ExchangeRate AS exchangeRate,
                P.BolivarsAmount AS bolivares,
                P.Observations AS observations
            FROM Exchange.CurrencyPurchase P
            LEFT JOIN Exchange.Beneficiary B ON P.EntityID = B.BeneficiaryID 
            LEFT JOIN AccountBalance.Bank BK ON P.BankID = BK.BankID
            ORDER BY P.PurchaseDate DESC, P.CurrencyPurchaseID DESC
        """
        cursor.execute(sql)
        purchases = cursor.fetchall()

        # PREVENCIÓN DE ERRORES JSON:
        for trx in purchases:
            trx['dollarsBought'] = float(trx['dollarsBought']) if trx['dollarsBought'] is not None else 0.0
            trx['exchangeRate'] = float(trx['exchangeRate']) if trx['exchangeRate'] is not None else 0.0
            trx['bolivares'] = float(trx['bolivares']) if trx['bolivares'] is not None else 0.0

        return purchases

    except pymssql.Error as e:
        print(f"Database error: {e}")
        raise e

    except Exception as e:
        print(f"General error: {e}")
        raise e

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_purchase_settlements_list(): pass

def add_purchase_settlement(data): pass

def update_purchase_settlement(settlement_id, data): pass

def get_beneficiaries_list():
    connection = None
    cursor = None
    beneficiaries = []

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
            SELECT 
                B.BeneficiaryID AS id,
                B.BeneficiaryName AS name,
                BK.BankName AS bank,          -- Este es el nombre para la tabla
                B.BankID AS bankId,           -- Este es el ID para la lógica
                B.AccountNumber AS account,
                B.Observations AS observations
            FROM Exchange.Beneficiary B
            LEFT JOIN AccountBalance.Bank BK ON B.BankID = BK.BankID
            ORDER BY B.BeneficiaryID DESC
        """
        cursor.execute(sql)
        beneficiaries = cursor.fetchall()

        return beneficiaries

    except pymssql.Error as e:
        print(f"Database error: {e}")
        raise e
    
    except Exception as e:
        print(f"General error: {e}")
        raise e
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def add_beneficiary(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO Exchange.Beneficiary (BeneficiaryName, BankID, AccountNumber, Observations, isActive, CreatedAt, UpdatedAt)
            VALUES (%s, %s, %s, %s, 1, GETDATE(), GETDATE());

            SELECT SCOPE_IDENTITY();
        """
        cursor.execute(sql, (data['name'], data['bankId'], data['account'], data['observations']))
        new_id = cursor.fetchone()[0]
        
        connection.commit()

        print(f"New beneficiary added with ID: {new_id}")
        return new_id

    except pymssql.Error as e:
        print(f"Database error: {e}")
        raise e
    
    except Exception as e:
        print(f"General error: {e}")
        raise e
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def update_beneficiary(beneficiary_id, data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor()

        sql = """
            UPDATE Exchange.Beneficiary
            SET BeneficiaryName = %s,
                BankID = %s,
                AccountNumber = %s,
                Observations = %s,
                UpdatedAt = GETDATE()
            WHERE BeneficiaryID = %s
        """
        cursor.execute(sql, (data['name'], data['bankId'], data['account'], data['observations'], beneficiary_id))
        connection.commit()

        if cursor.rowcount > 0:
            print(f"Beneficiary with ID {beneficiary_id} updated successfully.")
            return True
        else:
            print(f"No beneficiary found with ID {beneficiary_id}. Update failed.")
            return False

    except pymssql.Error as e:
        print(f"Database error: {e}")
        raise e
    
    except Exception as e:
        print(f"General error: {e}")
        raise e
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()