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

        sql = """
            INSERT INTO Exchange.CurrencyPurchase 
            (
                PurchaseDate,
                -- Datos de Origen
                OriginEntityID, OriginBankID, OriginAccountID,

                -- Datos de Destino
                DestinationEntityID, DestinationBankID, DestinationAccountID,

                -- Datos del Proveedor
                BeneficiaryID, 

                -- Datos de la Compra
                DollarsPurchased, ExchangeRate, Observations, 

                CreatedAt, UpdatedAt
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), GETDATE());

            SELECT SCOPE_IDENTITY();
        """
        
        cursor.execute(sql, (
            data['date'], 
            data['originEntityId'], 
            data['originBankId'], 
            data['originAccountId'], 
            data['destEntityId'], 
            data['destBankId'], 
            data['destAccountId'],
            data['beneficiaryId'],
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

        sql = """
            UPDATE Exchange.CurrencyPurchase
            SET PurchaseDate = %s,
                -- Datos de Origen
                OriginEntityID = %s, OriginBankID = %s, OriginAccountID = %s,

                -- Datos de Destino
                DestinationEntityID = %s, DestinationBankID = %s, DestinationAccountID = %s,

                -- Datos del Proveedor
                BeneficiaryID = %s,

                -- Datos de la Compra
                DollarsPurchased = %s, ExchangeRate = %s, Observations = %s,

                UpdatedAt = GETDATE()
            WHERE CurrencyPurchaseID = %s
        """
        
        cursor.execute(sql, (
            data['date'], 
            data['originEntityId'], 
            data['originBankId'], 
            data['originAccountId'], 
            data['destEntityId'], 
            data['destBankId'], 
            data['destAccountId'],
            data['beneficiaryId'],
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

                -- 1. Origen
                P.OriginEntityID AS originEntityId,
                OE.EntityName AS originEntity,
                P.OriginBankID AS originBankId,
                OB.BankName AS originBank,
                P.OriginAccountID AS originAccountId,
                OA.AccountNumber AS originAccount,

                -- 2. Destino
                P.DestinationEntityID AS destEntityId,
                DE.EntityName AS destEntity,
                P.DestinationBankID AS destBankId,
                DB.BankName AS destBank,
                P.DestinationAccountID AS destAccountId,
                DA.AccountNumber AS destAccount,

                -- 3. Proveedor
                P.BeneficiaryID AS providerId,
                BEN.BeneficiaryName AS provider,

                -- 4. Datos de la Compra
                P.DollarsPurchased AS dollarsBought,
                P.ExchangeRate AS exchangeRate,
                P.BolivarsAmount AS bolivares,
                P.Observations AS observations,

                -- Campo de validacion
                CASE WHEN CPS.CurrencyPurchaseID IS NOT NULL THEN 1 ELSE 0 END AS isValidated

            FROM Exchange.CurrencyPurchase P
            -- Origen
            LEFT JOIN AccountBalance.Entity OE ON P.OriginEntityID = OE.EntityID
            LEFT JOIN AccountBalance.Bank OB ON P.OriginBankID = OB.BankID
            LEFT JOIN AccountBalance.Account OA ON P.OriginAccountID = OA.AccountID
            
            -- Destino
            LEFT JOIN AccountBalance.Entity DE ON P.DestinationEntityID = DE.EntityID
            LEFT JOIN AccountBalance.Bank DB ON P.DestinationBankID = DB.BankID
            LEFT JOIN AccountBalance.Account DA ON P.DestinationAccountID = DA.AccountID
            
            -- Beneficiario
            LEFT JOIN Exchange.Beneficiary BEN ON P.BeneficiaryID = BEN.BeneficiaryID

            -- Validación
            LEFT JOIN Exchange.CurrencyPurchaseSettlement CPS ON P.CurrencyPurchaseID = CPS.CurrencyPurchaseID

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

def get_reception_history():
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
            SELECT 
                S.CurrencyPurchaseSettlementID AS id,
                CONVERT(varchar, S.ReceptionDate, 23) AS date,
                E.EntityName AS receivingCompany,
                S.ReceivingBank AS receivingBank,
                S.ReceivingAccountNumber AS account,
                S.ReceivedAmountUSD AS amountReceived,
                S.SettlementStatus AS status,
                S.ReferenceNumber AS referenceNumber,
                S.Observations AS observations
            FROM [Exchange].[CurrencyPurchaseSettlement] S
            JOIN [Exchange].[CurrencyPurchase] P ON S.CurrencyPurchaseID = P.CurrencyPurchaseID
            JOIN [AccountBalance].[Entity] E ON P.DestinationEntityID = E.EntityID
            ORDER BY S.ReceptionDate DESC, S.CurrencyPurchaseSettlementID DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()

    except Exception as e:
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

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
                B.Observations AS observations,
                B.FiscalIdentifier as documentPrefix,
                B.IdentificationNumber as documentNumber,
                B.Email as email
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
            INSERT INTO Exchange.Beneficiary (BeneficiaryName, BankID, AccountNumber, Observations, isActive, CreatedAt, UpdatedAt, FiscalIdentifier, IdentificationNumber, Email)
            VALUES (%s, %s, %s, %s, 1, GETDATE(), GETDATE(), %s, %s, %s);

            SELECT SCOPE_IDENTITY();
        """
        cursor.execute(sql, (data['name'], data['bankId'], data['account'], data['observations'], data['documentPrefix'], data['documentNumber'], data['email']))
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
                UpdatedAt = GETDATE(),
                FiscalIdentifier = %s,
                IdentificationNumber = %s,
                Email = %s
            WHERE BeneficiaryID = %s
        """
        cursor.execute(sql, (data['name'], data['bankId'], data['account'], data['observations'], data['documentPrefix'], data['documentNumber'], data['email'], beneficiary_id))
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

def get_entities_list(currency_mode):
    connection = None
    cursor = None
    entities = []

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)
        
        sql = """
            SELECT DISTINCT 
                E.[EntityID] AS id,
                E.[EntityName] AS name
            FROM [AccountBalance].[Entity] E
            JOIN [AccountBalance].[Account] A ON E.EntityID = A.EntityID
            WHERE A.CurrencyID = %s
            ORDER BY E.EntityID
        """
        cursor.execute(sql, (currency_mode,))
        entities = cursor.fetchall()

        return entities

    except pymssql.Error as e:
        print(f"Database error: {e}")
        raise e
    
    except Exception as e:
        print(f"General error: {e}")
        raise e
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_banks_by_entity_and_currency(entity_id, currency_id):
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Reemplazamos el '1' quemado por el parámetro %s
        sql = """
            SELECT DISTINCT
                   B.[BankID] AS id,
                   B.[BankName] AS name
              FROM [AccountBalance].[Bank] B
              JOIN AccountBalance.Account A ON A.BankID = B.BankID
             WHERE A.CurrencyID = %s AND A.EntityID = %s
             ORDER BY B.[BankName]
        """
        
        # Pasamos ambos parámetros a la consulta
        cursor.execute(sql, (currency_id, entity_id))
        return cursor.fetchall()

    except Exception as e:
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def validate_purchase(purchase_id, data, user_id):
    connection = None
    cursor = None
    try:
        connection = pool.connection()
        cursor = connection.cursor()

        # 1. CONTROL DE SEGURIDAD: Evita doble validación en simultáneo
        check_sql = "SELECT COUNT(1) FROM [Exchange].[CurrencyPurchaseSettlement] WHERE [CurrencyPurchaseID] = %s"
        cursor.execute(check_sql, (purchase_id,))

        if cursor.fetchone()[0] > 0:
            raise Exception("Esta compra ya ha sido validada previamente.")

        sql = """
            INSERT INTO [Exchange].[CurrencyPurchaseSettlement]
            (
                [CurrencyPurchaseID], [ReceptionDate], [ReceivedAmountUSD],
                [ReceivedExchangeRate], [ReferenceNumber], [ReceivingBank],
                [ReceivingAccountNumber], [ValidatedBy], [ValidationDate],
                [SettlementStatus], [Observations], [CreatedAt], [UpdatedAt]
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s, %s, GETDATE(), GETDATE())
        """
        
        cursor.execute(sql, (
            purchase_id,
            data['receptionDate'],
            data['receivedAmountUSD'],
            data['receivedExchangeRate'],
            data['referenceNumber'],
            data['receivingBank'],       
            data['receivingAccount'],    
            user_id,                     
            data['settlementStatus'],    
            data['observations']
        ))
        
        connection.commit()
        return True

    except Exception as e:
        if connection: connection.rollback()
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()