import os
import pymssql
from datetime import datetime

def get_db_connection():
    server = os.environ.get('DB_SERVER')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    conn = pymssql.connect(server, user, password, database)
    return conn


# Obtención de Data en la Interfaz

def get_receiptStores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Name FROM Main.Store')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_receiptStore_by_id(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Name FROM Main.Store WHERE ID = %s', (store_id,))
    store = cursor.fetchone()
    conn.close()
    return store

def get_sellers(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Name FROM Main.SalesRep WHERE StoreID = %s', (store_id,))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_seller_details(seller_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Name, EmailAddress, Telephone, CONCAT(FLOOR(PercentOfSale*100), '%'), StoreID FROM Main.SalesRep WHERE ID = %s", (seller_id,))
    seller = cursor.fetchone()
    conn.close()
    return seller

def get_customers(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, FirstName, LastName FROM Main.Customer WHERE StoreID = %s', (store_id,))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_tender():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Description FROM Main.Tender')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_commissionsRules():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT CommissionID, CommissionName, DaysSinceDue, CommissionRate, Active FROM CommissionReceipt.Commission')
    rules = cursor.fetchall()
    conn.close()
    return rules

def get_invoices_by_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT D.AccountID, D.N_CTA, D.Amount, D.Balance, C.Description
                   FROM CommissionReceipt.DebtAccount D
                   JOIN Main.Currency C ON D.CurrencyID = C.ID
                   WHERE CustomerID = %s
                   ORDER BY D.N_CTA''',
                   (customer_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_receiptsStoreCustomer(account_ids):
    account_ids_tuple = tuple(account_ids)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT TOP (1) S.Name, C.FirstName, C.LastName, Y.Description
                   FROM CommissionReceipt.DebtAccount D
                   JOIN Main.Store S ON D.StoreID = S.ID
                   JOIN Main.Customer C ON D.CustomerID = C.ID
                   JOIN Main.Currency Y ON D.CurrencyID = Y.ID
                   WHERE AccountID IN %s''',
                   (account_ids_tuple,))
    receiptStoreCustomer = cursor.fetchone()
    conn.close()
    return receiptStoreCustomer

def get_receiptsInfo(account_ids):
    account_ids_tuple = tuple(account_ids)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT D.N_CTA, D.Amount, D.DueDate, D.DueDate, D.Balance
                   FROM CommissionReceipt.DebtAccount D
                   WHERE AccountID IN %s
                   ORDER BY D.DueDate''',
                   (account_ids_tuple,))
    receipts = cursor.fetchall()
    conn.close()
    return receipts

def get_bankAccounts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT AccountID, BankName, Destiny FROM CommissionReceipt.PaymentOption')
    bankAccounts = cursor.fetchall()
    conn.close()
    return bankAccounts

def get_commissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT CommissionID, CommissionRate, DaysSinceDue, Active FROM CommissionReceipt.Commission')
    commissions = cursor.fetchall()
    conn.close()
    return commissions


# Escritura de datos en la BD a través de la Interfaz

def set_commissionsRules(rules):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for rule in rules:
        id = rule.get('id')
        name = rule['name']
        days = rule['days']
        percentage = rule['percentage']
        is_active = rule['is_active']
        
        cursor.execute(f"""
            MERGE INTO CommissionReceipt.Commission AS target
            USING (VALUES (%s, %s, %s, %s, %s, %s)) AS source (CommissionID, CommissionName, CommissionRate, DaysSinceDue, Active, DateCreated)
            ON target.CommissionID = source.CommissionID
            WHEN MATCHED THEN
                UPDATE SET 
                    target.CommissionName = source.CommissionName,
                    target.CommissionRate = source.CommissionRate,
                    target.DaysSinceDue = source.DaysSinceDue,
                    target.Active = source.Active
            WHEN NOT MATCHED THEN
                INSERT (CommissionName, CommissionRate, DaysSinceDue, Active, DateCreated)
                VALUES (source.CommissionName, source.CommissionRate, source.DaysSinceDue, source.Active, GETDATE());
        """, (id, name, percentage, days, is_active, None))
    
    conn.commit()
    conn.close()