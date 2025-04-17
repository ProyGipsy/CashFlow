import os
import pymssql
from datetime import datetime
from werkzeug.utils import secure_filename
from onedrive import get_onedrive_headers
import requests

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
    cursor.execute('SELECT ID, Name, LogoPath FROM Main.Store WHERE ID = %s', (store_id,))
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

def get_customer_by_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT C.ID, C.FirstName, C.LastName
                    FROM Main.Customer C
                    WHERE C.ID = %s''', (customer_id,))
    sellers = cursor.fetchone()
    conn.close()
    return sellers

def get_customers(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT (C.ID), C.FirstName, C.LastName
                    FROM Main.Customer C
                    JOIN CommissionReceipt.DebtAccount D ON C.ID = D.CustomerID
                    WHERE D.StoreID = %s''', (store_id,))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_customers_with_unvalidated_receipts(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
            SELECT DISTINCT (C.ID), C.FirstName, C.LastName
            FROM Main.Customer C
            JOIN CommissionReceipt.DebtAccount D ON C.ID = D.CustomerID
            JOIN CommissionReceipt.DebtPaymentRelation P ON D.AccountID = P.DebtAccountID
            JOIN CommissionReceipt.PaymentReceipt R ON P.PaymentReceiptID = R.ReceiptID
            WHERE R.IsValidated = 0 AND D.StoreID = %s
            ''', (store_id,))
    customers = cursor.fetchall()
    conn.close()
    return customers

def get_count_customers_with_unvalidated_receipts(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT C.ID) AS CustomerCount
        FROM Main.Customer C
        JOIN CommissionReceipt.DebtAccount D ON C.ID = D.CustomerID
        JOIN CommissionReceipt.DebtPaymentRelation P ON D.AccountID = P.DebtAccountID
        JOIN CommissionReceipt.PaymentReceipt R ON P.PaymentReceiptID = R.ReceiptID
        WHERE R.IsValidated = 0 AND D.StoreID = %s
    ''', (store_id,))
    customer_count = cursor.fetchone()[0]
    conn.close()
    return customer_count

def get_tender(currency_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Description FROM Main.Tender WHERE CurrencyID=%s', (currency_id))
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

def get_invoices_by_customer(customer_id, store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(D.AccountID), D.N_CTA, D.Amount, D.PaidAmount, C.Description
                   FROM CommissionReceipt.DebtAccount D
                   JOIN Main.Currency C ON D.CurrencyID = C.ID
                   WHERE CustomerID = %s AND StoreID = %s AND D.Amount-D.PaidAmount > 0
                   ORDER BY D.N_CTA''',
                   (customer_id, store_id))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_receiptsStoreCustomer(account_ids):
    account_ids_tuple = tuple(account_ids)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT TOP (1) S.ID, S.Name, C.ID, C.FirstName, C.LastName, Y.Description, Y.ID
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
    cursor.execute('''SELECT D.N_CTA, D.Amount, D.DueDate, D.DueDate, D.PaidAmount, D.AccountID
                   FROM CommissionReceipt.DebtAccount D
                   WHERE AccountID IN %s
                   ORDER BY D.DueDate''',
                   (account_ids_tuple,))
    receipts = cursor.fetchall()
    conn.close()
    return receipts

def get_bankAccounts(store_id, currency_id, tender_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT AccountID, BankName, Destiny
                   FROM CommissionReceipt.PaymentOption
                   WHERE StoreID = %s AND CurrencyID = %s AND TenderID = %s
                   ''', (store_id, currency_id, tender_id))
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

def get_unvalidated_receipts_by_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(R.ReceiptID), R.Amount, R.CommissionAmount, R.IsValidated, R.FilePath
        FROM CommissionReceipt.PaymentReceipt R
        JOIN CommissionReceipt.DebtPaymentRelation P ON R.ReceiptID = P.PaymentReceiptID
        JOIN CommissionReceipt.DebtAccount D ON P.DebtAccountID = D.AccountID
        WHERE R.IsValidated = 0 AND D.CustomerID = %s
        ''', (customer_id,))
    receipts = cursor.fetchall()
    conn.close()
    return receipts

def get_invoices_by_receipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(D.N_CTA), D.Amount, D.DueDate, D.DueDate, D.PaidAmount, D.AccountID, C.Description
                    FROM CommissionReceipt.DebtAccount D
                    JOIN CommissionReceipt.DebtPaymentRelation R ON D.AccountID = R.DebtAccountID
                    JOIN Main.Currency C ON D.CurrencyID = C.ID
                    WHERE R.PaymentReceiptID = %s
                    ''', (receipt_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_paymentEntries_by_receipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT T.Description, E.PaymentDate, E.Amount, E.Discount, E.Reference, O.BankName, O.Destiny, E.ProofOfPaymentPath
                    FROM CommissionReceipt.PaymentReceiptEntry E
                    JOIN CommissionReceipt.PaymentOption O ON E.PaymentDestinationID = O.AccountID
                    JOIN Main.Tender T ON E.TenderID = T.ID
                    WHERE E.ReceiptID = %s
                    ''', (receipt_id,))
    paymentEntries = cursor.fetchall()
    conn.close()
    return paymentEntries

def get_salesRep_isRetail(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT SalesRepID, IsRetail 
                    FROM CommissionReceipt.DebtAccount
                    WHERE AccountID = %s
                    ''', (account_id,))
    salesRep_isRetail = cursor.fetchone()
    conn.close()
    return salesRep_isRetail

def get_SalesRepCommission(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT D.N_CTA, C.AmountOwed, C.DaysElapsed, C.CommissionAmount
                    FROM CommissionReceipt.SalesRepCommission C
                    JOIN CommissionReceipt.DebtAccount D ON C.AccountID = D.AccountID
                    WHERE ReceiptID = %s
                    ''', (receipt_id,))
    salesRepComm = cursor.fetchall()
    conn.close()
    return salesRepComm


def get_onedriveFiles(paymentEntries):
    headers = get_onedrive_headers()
    folder_path = "/Recibos de Cobranza/Comprobantes de Pago"
    updated_entries = []
    
    for entry in paymentEntries:
        if entry[7]:
            filename = entry[7].split('/')[-1]
            file_url = f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/root:{folder_path}/{filename}"

            try:
                response = requests.get(file_url, headers=headers)
                if response.status_code == 200:
                    file_data = response.json()
                    updated_entry = list(entry)
                    
                    file_id = file_data['id']
                    updated_entry[7] = {
                        'url': f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/items/{file_id}/content",
                        'embed_url': f"https://onedrive.live.com/embed?resid={file_id}",
                        'web_url': file_data.get('webUrl'),
                        'file_url': file_url,
                        'name': filename
                    }
                    
                    updated_entries.append(tuple(updated_entry))
                else:
                    updated_entries.append(entry)
            except Exception as e:
                updated_entries.append(entry)
    
    return updated_entries



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


def set_paymentReceipt(cursor, total_receipt_amount, commission_note):
    cursor.execute('''
                   INSERT INTO CommissionReceipt.PaymentReceipt
                   (Amount, CommissionAmount, IsValidated, FilePath, isRetail)
                   VALUES (%s, %s, %s, %s, %s)
                   ''', (total_receipt_amount, commission_note, 0, '', 0))

    #Obtención del ReceiptID generado
    cursor.execute("SELECT SCOPE_IDENTITY()")
    receipt_id = cursor.fetchone()[0]
    
    return receipt_id


def set_paymentEntry(cursor, receipt_id, payment_date, amount, discount, reference, destination_id, tender_id, proof_path):
    cursor.execute('''
        INSERT INTO CommissionReceipt.PaymentReceiptEntry
        (ReceiptID, PaymentDate, Amount, Discount, Reference, PaymentDestinationID, TenderID, isRetail, ProofOfPaymentPath)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (receipt_id, payment_date, amount, discount, reference, destination_id, tender_id, 0, proof_path))

"""
# Guardado de Comprobantes de Pago en el Servidor
def save_proofOfPayment(proof_of_payments, receipt_id, payment_date, index):
    saved_file_paths = []
    for file in proof_of_payments:
        if file:
            formatted_date = payment_date.strftime('%Y-%m-%d')
            new_filename = f"{receipt_id}_{formatted_date}_{index}{os.path.splitext(file.filename)[1]}"
            file_path = os.path.join('static/ProofsOfPayment', new_filename)
            file.save(file_path)
            saved_file_paths.append(file_path)
    return saved_file_paths
"""

# Guardado de Comprobantes de Pago en OneDrive
def save_proofOfPayment(proof_of_payments, receipt_id, payment_date, index):
    saved_file_paths = []
    formatted_date = payment_date.strftime('%Y-%m-%d')
    headers = get_onedrive_headers()

    folder_path = "/Recibos de Cobranza/Comprobantes de Pago"
    for file in proof_of_payments:
        if file:
            new_filename = f"{receipt_id}_{formatted_date}_{index}{os.path.splitext(file.filename)[1]}"
            upload_url = f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/root:/{folder_path}/{new_filename}:/content"

            file_content = file.read()

            response = requests.put(
                url = upload_url,
                headers=headers,
                data=file_content)
            
            if response.status_code == 201:
                print(f"Archivo {new_filename} subido correctamente.")
                saved_file_paths.append(new_filename)
            else:
                print(f"Error al subir el archivo {new_filename}: {response.status_code}")
                print(response.json())

    return saved_file_paths


def set_invoicePaidAmount(cursor, account_id, new_paidAmount):
    cursor.execute('''
                   UPDATE CommissionReceipt.DebtAccount
                   SET PaidAmount = %s
                   WHERE AccountID = %s
                   ''', (new_paidAmount, account_id))
    

def set_DebtPaymentRelation(cursor, account_id, receipt_id):
    cursor.execute('''
                    INSERT INTO CommissionReceipt.DebtPaymentRelation
                    (DebtAccountID, PaymentReceiptID, isRetail)
                    VALUES (%s, %s, %s)
                    ''', (account_id, int(receipt_id), 0))


def set_SalesRepCommission(cursor, sales_rep_id, account_id, is_retail, balance_amount, days_passed, commission_amount, receipt_id):
    cursor.execute('''
                    INSERT INTO [CommissionReceipt].[SalesRepCommission] 
                    (SalesRepID, AccountID, IsRetail, AmountOwed, DaysElapsed, CommissionAmount, CreatedAt, ReceiptID)
                    VALUES (%s, %s, %s, %s, %s, %s, GETDATE(), %s)
                    ''', (sales_rep_id, account_id, is_retail, balance_amount, days_passed, commission_amount, receipt_id))
    
def set_isValidatedReceipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   UPDATE CommissionReceipt.PaymentReceipt
                   SET IsValidated = 1
                   WHERE ReceiptID = %s
                   ''', (receipt_id))
    conn.commit()
    conn.close()