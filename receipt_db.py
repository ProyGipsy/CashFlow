import os
import pymssql
from dbutils.pooled_db import PooledDB
from onedrive import get_onedrive_headers
import requests

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

def get_receiptStores_Sellers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT T.ID, T.Name
                    FROM Main.Store T
                    JOIN Commission_Receipt.DebtAccount D ON T.ID = D.StoreID
                    JOIN Commission_Receipt.SalesRep S ON D.SalesRepID = S.ID
                    WHERE T.ID != 0 AND S.isRetail = 0
                    ORDER BY T.ID;''')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_receiptStores_DebtAccount(salesRep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(S.ID), S.Name
                    FROM Main.Store S
                    JOIN Commission_Receipt.DebtAccount D ON S.ID = D.StoreID
                    WHERE S.ID != 0 AND (D.Amount-D.PaidAmount) > 0 AND D.SalesRepID=%s
                   ''', (salesRep_id))
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_receiptStores_DebtAccount_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(S.ID), S.Name
                    FROM Main.Store S
                    JOIN Commission_Receipt.DebtAccount D ON S.ID = D.StoreID
                    WHERE S.ID != 0 AND (D.Amount-D.PaidAmount) > 0 ''',)
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_receiptStores_Receipts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(S.ID), S.Name
                    FROM Main.Store S
                    JOIN Commission_Receipt.DebtAccount D ON S.ID = D.StoreID
                    JOIN Commission_Receipt.DebtPaymentRelation R ON D.AccountID = R.DebtAccountID
                    JOIN Commission_Receipt.PaymentReceipt P ON R.PaymentReceiptID = P.ReceiptID
                    WHERE P.IsReviewed = 0''')
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
    cursor.execute('''SELECT DISTINCT S.ID, S.Name
                    FROM Commission_Receipt.SalesRep S
                    JOIN Commission_Receipt.DebtAccount D ON S.ID = D.SalesRepID
                    WHERE S.isRetail = 0 AND D.StoreID = %s
                    ORDER BY S.ID''', (store_id,))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_count_sellers(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(DISTINCT(S.ID))
                    FROM Commission_Receipt.SalesRep S
                    JOIN Commission_Receipt.DebtAccount D ON S.ID = D.SalesRepID
                    WHERE S.isRetail = 0 AND D.StoreID = %s''', (store_id,))
    sellers = cursor.fetchone()[0]
    conn.close()
    return sellers

def get_seller_details(seller_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Name, EmailAddress, Telephone, CONCAT(FLOOR(PercentOfSale*100), '%'), StoreID FROM Commission_Receipt.SalesRep WHERE ID = %s", (seller_id,))
    seller = cursor.fetchone()
    conn.close()
    return seller

def get_customer_by_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT C.ID, C.FirstName, C.LastName
                    FROM Commission_Receipt.Customer C
                    WHERE C.ID = %s''', (customer_id,))
    sellers = cursor.fetchone()
    conn.close()
    return sellers

def get_customers(store_id, salesRep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT (C.ID), C.FirstName, C.LastName
                    FROM Commission_Receipt.Customer C
                    JOIN Commission_Receipt.DebtAccount D ON C.ID = D.CustomerID
                    WHERE C.isRetail = 0 AND (Amount-PaidAmount) > 0 AND D.StoreID = %s AND D.SalesRepID = %s
                   ''', (store_id, salesRep_id))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_customers_admin(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT (C.ID), C.FirstName, C.LastName
                    FROM Commission_Receipt.Customer C
                    JOIN Commission_Receipt.DebtAccount D ON C.ID = D.CustomerID
                    WHERE C.isRetail = 0 AND (Amount-PaidAmount) > 0 AND D.StoreID = %s
                   ''', (store_id))
    sellers = cursor.fetchall()
    conn.close()
    return sellers

def get_count_customers_with_accountsReceivable(store_id, salesRep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''  SELECT DISTINCT T.CountCustomers, T.Balance, M.Code AS Currency
                    FROM (
                        SELECT D.CurrencyID, 
                            COUNT(DISTINCT D.CustomerID) AS CountCustomers,
                            SUM(D.Amount - D.PaidAmount) AS Balance
                        FROM Commission_Receipt.DebtAccount D
                        WHERE (D.Amount - D.PaidAmount) > 0 AND D.StoreID = %s AND D.SalesRepID = %s
                        GROUP BY D.CurrencyID
                    ) AS T
                    JOIN Main.Currency M ON T.CurrencyID = M.ID;''', (store_id, salesRep_id))
    sellers = list(cursor.fetchone())
    formattedSum = "{:,.2f}".format(sellers[1]).replace(".", "X").replace(",", ".").replace("X", ",")
    sellers[1] = formattedSum
    conn.close()
    return sellers

def get_count_customers_with_accountsReceivable_admin(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT T.CountCustomers, T.Balance, M.Code AS Currency
                    FROM (
                        SELECT D.CurrencyID, 
                            COUNT(DISTINCT D.CustomerID) AS CountCustomers,
                            SUM(D.Amount - D.PaidAmount) AS Balance
                        FROM Commission_Receipt.DebtAccount D
                        WHERE (D.Amount - D.PaidAmount) > 0 AND D.StoreID = %s
                        GROUP BY D.CurrencyID
                    ) AS T
                    JOIN Main.Currency M ON T.CurrencyID = M.ID;''', (store_id))
    sellers = list(cursor.fetchone())
    formattedSum = "{:,.2f}".format(sellers[1]).replace(".", "X").replace(",", ".").replace("X", ",")
    sellers[1] = formattedSum
    conn.close()
    return sellers

def get_customers_with_unvalidated_receipts(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
            SELECT DISTINCT (C.ID), C.FirstName, C.LastName
            FROM Commission_Receipt.Customer C
            JOIN Commission_Receipt.DebtAccount D ON C.ID = D.CustomerID
            JOIN Commission_Receipt.DebtPaymentRelation P ON D.AccountID = P.DebtAccountID
            JOIN Commission_Receipt.PaymentReceipt R ON P.PaymentReceiptID = R.ReceiptID
            WHERE  C.isRetail = 0 AND R.IsReviewed = 0 AND D.StoreID = %s
            ''', (store_id,))
    customers = cursor.fetchall()
    conn.close()
    return customers

def get_count_customers_with_unvalidated_receipts(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT C.ID) AS CustomerCount
        FROM Commission_Receipt.Customer C
        JOIN Commission_Receipt.DebtAccount D ON C.ID = D.CustomerID
        JOIN Commission_Receipt.DebtPaymentRelation P ON D.AccountID = P.DebtAccountID
        JOIN Commission_Receipt.PaymentReceipt R ON P.PaymentReceiptID = R.ReceiptID
        WHERE C.isRetail = 0 AND R.IsReviewed = 0 AND D.StoreID = %s
    ''', (store_id,))
    customer_count = cursor.fetchone()[0]
    conn.close()
    return customer_count

def get_currency():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT(ID), Code, OficialExchangeRate FROM Main.Currency WHERE ID != 0 AND isRetail = 0')
    currencies = cursor.fetchall()
    conn.close()
    return currencies

def get_tender(currency_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Description FROM Main.Tender WHERE IsRetail=0 AND CurrencyID=%s', (currency_id))
    tenders = cursor.fetchall()
    conn.close()
    return tenders

def get_bankAccounts(store_id, currency_id, tender_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT AccountID, BankName, Destiny
                   FROM Commission_Receipt.PaymentOption
                   WHERE StoreID = %s AND CurrencyID = %s AND TenderID = %s
                   ''', (store_id, currency_id, tender_id))
    bankAccounts = cursor.fetchall()
    conn.close()
    return bankAccounts

def get_commissionsRules():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT CommissionID, CommissionName, DaysSinceDue, CommissionRate, Active FROM Commission_Receipt.Commission')
    rules = cursor.fetchall()
    conn.close()
    return rules

def get_invoices_by_customer(customer_id, store_id, salesRep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(D.AccountID), D.N_CTA, D.Amount, D.PaidAmount, C.Description, D.DocumentType
                   FROM Commission_Receipt.DebtAccount D
                   JOIN Main.Currency C ON D.CurrencyID = C.ID
                   WHERE CustomerID = %s AND StoreID = %s AND D.Amount-D.PaidAmount > 0 AND D.SalesRepID = %s
                   ORDER BY D.N_CTA''',
                   (customer_id, store_id, salesRep_id))
    invoices = cursor.fetchall()    
    conn.close()
    return invoices

def get_invoices_by_customer_admin(customer_id, store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(D.AccountID), D.N_CTA, D.Amount, D.PaidAmount, C.Description, D.DocumentType
                   FROM Commission_Receipt.DebtAccount D
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
                   FROM Commission_Receipt.DebtAccount D
                   JOIN Main.Store S ON D.StoreID = S.ID
                   JOIN Commission_Receipt.Customer C ON D.CustomerID = C.ID
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
    cursor.execute('''SELECT D.N_CTA, D.Amount, D.InvoiceIssueDate, D.DueDate, D.PaidAmount, D.AccountID, D.DocumentType
                   FROM Commission_Receipt.DebtAccount D
                   WHERE AccountID IN %s
                   ORDER BY D.DueDate''',
                   (account_ids_tuple,))
    receipts = cursor.fetchall()
    conn.close()
    return receipts

def get_commissions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT CommissionID, CommissionRate, DaysSinceDue, Active FROM Commission_Receipt.Commission')
    commissions = cursor.fetchall()
    conn.close()
    return commissions

def get_unvalidated_receipts_by_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(R.ReceiptID), R.Amount, R.CommissionAmount, R.IsReviewed, R.FilePath
        FROM Commission_Receipt.PaymentReceipt R
        JOIN Commission_Receipt.DebtPaymentRelation P ON R.ReceiptID = P.PaymentReceiptID
        JOIN Commission_Receipt.DebtAccount D ON P.DebtAccountID = D.AccountID
        WHERE R.IsReviewed = 0 AND D.CustomerID = %s
        ''', (customer_id,))
    receipts = cursor.fetchall()
    conn.close()
    return receipts

def get_invoices_by_receipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT(D.N_CTA), D.Amount, D.DueDate, D.DueDate, D.PaidAmount, D.AccountID, C.Description, D.SalesRepID
                    FROM Commission_Receipt.DebtAccount D
                    JOIN Commission_Receipt.DebtPaymentRelation R ON D.AccountID = R.DebtAccountID
                    JOIN Main.Currency C ON D.CurrencyID = C.ID
                    WHERE R.PaymentReceiptID = %s
                    ''', (receipt_id,))
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def get_paymentEntries_by_receipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT T.Description, E.PaymentDate, E.Amount, E.Discount, E.Reference, O.BankName, O.Destiny, E.ProofOfPaymentPath, C.Code, E.PaymentEntryID
                    FROM Commission_Receipt.PaymentReceiptEntry E
                    JOIN Commission_Receipt.PaymentOption O ON E.PaymentDestinationID = O.AccountID
                    JOIN Main.Tender T ON E.TenderID = T.ID
                    JOIN Main.Currency C ON T.CurrencyID = C.ID
                    WHERE T.IsRetail = 0 AND E.ReceiptID = %s
                    ORDER BY E.PaymentEntryID
                    ''', (receipt_id,))
    paymentEntries = cursor.fetchall()
    conn.close()
    return paymentEntries

def get_salesRep_isRetail(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT SalesRepID, IsRetail 
                    FROM Commission_Receipt.DebtAccount
                    WHERE AccountID = %s
                    ''', (account_id,))
    salesRep_isRetail = cursor.fetchone()
    conn.close()
    return salesRep_isRetail

def get_SalesRepCommission(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT D.N_CTA, C.AmountOwed, STRING_AGG(CAST(P.DaysElapsed AS NVARCHAR(MAX)), ' / ') AS DaysElapsed, C.CommissionAmount, P.DebtAccountID
                    FROM Commission_Receipt.SalesRepCommission C
                    JOIN Commission_Receipt.DebtAccount D ON C.AccountID = D.AccountID
					JOIN Commission_Receipt.PaymentEntryCommission P ON C.AccountID = P.DebtAccountID AND C.ReceiptID = P.ReceiptID
                    WHERE C.ReceiptID = %s
					GROUP BY D.N_CTA, C.AmountOwed, C.CommissionAmount, P.DebtAccountID
                    ''', (receipt_id,))
    salesRepComm = cursor.fetchall()
    conn.close()
    return salesRepComm

def get_SalesRepCommission_OLD(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT D.N_CTA, C.AmountOwed, C.DaysElapsed, C.CommissionAmount
                    FROM Commission_Receipt.SalesRepCommission C
                    JOIN Commission_Receipt.DebtAccount D ON C.AccountID = D.AccountID
                    WHERE ReceiptID = %s
                    ''', (receipt_id,))
    salesRepComm = cursor.fetchall()
    conn.close()
    return salesRepComm

def get_onedriveProofsOfPayments(paymentEntries):
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
                    
                    file_id = file_data['id']

                    # Generación de enlace de compartición
                    share_url = f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/items/{file_id}/createLink"
                    share_data = {
                        "type": "view",
                        "scope": "anonymous"
                    }
                    share_response = requests.post(share_url, headers=headers, json=share_data)

                    updated_entry = list(entry)
                    if share_response.status_code == 200:
                        shared_link = share_response.json()["link"]["webUrl"]
                        updated_entry[7] = {
                            'url': shared_link,
                            'name': filename,
                            'error': False,
                            'email_url': f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/items/{file_id}/content"
                        }
                    else:
                        shared_link = file_data.get('webUrl')
                        updated_entry[7] = {
                            'url': shared_link,
                            'name': filename,
                            'error': True,
                            'email_url': f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/items/{file_id}/content"
                        }

                    updated_entries.append(tuple(updated_entry))
                
                else:
                    updated_entries.append(entry)
            
            except Exception as e:
                updated_entries.append(entry)
    
    return updated_entries


def get_onedriveStoreLogo(logo_name):
    headers = get_onedrive_headers()
    folder_path = "/Recibos de Cobranza/Logos Stores"
    file_url = f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/root:{folder_path}/{logo_name}"

    try:
        # Verificar si el archivo existe y obtener metadata
        response = requests.get(file_url, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            file_id = file_data['id']
            
            download_url = f"https://graph.microsoft.com/v1.0/users/desarrollo@grupogipsy.com/drive/items/{file_id}/content"
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            return response.content
        
        else:
            print(f"Logo no encontrado en OneDrive: {logo_name}")
            return None
    
    except Exception as e:
        print(f"Error al obtener logo {logo_name}: {str(e)}")
        return None
    
def get_paymentRelations_by_receipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DebtAccountID, PaidAmount 
        FROM Commission_Receipt.DebtPaymentRelation
        WHERE PaymentReceiptID = %s
    ''', (receipt_id,))
    relations = cursor.fetchall()
    conn.close()
    return relations

def get_invoiceCurrentPaidAmount(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT PaidAmount, Amount 
        FROM Commission_Receipt.DebtAccount
        WHERE AccountID = %s
    ''', (account_id,))
    paid_amount = cursor.fetchone()
    conn.close()
    return paid_amount


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
            MERGE INTO Commission_Receipt.Commission AS target
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
                   INSERT INTO Commission_Receipt.PaymentReceipt
                   (Amount, CommissionAmount, IsReviewed, FilePath, isRetail, IsApproved)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ''', (total_receipt_amount, commission_note, 0, '', 0, 0))

    #Obtención del ReceiptID generado
    cursor.execute("SELECT SCOPE_IDENTITY()")
    receipt_id = cursor.fetchone()[0]
    
    return receipt_id


def set_paymentEntry(cursor, receipt_id, payment_date, amount, discount, reference, destination_id, tender_id, proof_path): 
    cursor.execute('''
        INSERT INTO Commission_Receipt.PaymentReceiptEntry
        (ReceiptID, PaymentDate, Amount, Discount, Reference, PaymentDestinationID, TenderID, isRetail, ProofOfPaymentPath)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (receipt_id, payment_date, amount, discount, reference, destination_id, tender_id, 0, proof_path))
    
    #Obtención del PaymentReceiptID generado
    cursor.execute("SELECT SCOPE_IDENTITY()")
    paymentEntry_id = cursor.fetchone()[0]
    print(f"Payment Entry ID: {paymentEntry_id}")

    return paymentEntry_id
    

def set_paymentEntryCommission(cursor, receipt_id, paymentEntry_id, debtaccount_id, payment_date, amount, days_elapsed, commission_id, commission_amount):
    cursor.execute('''
        INSERT INTO Commission_Receipt.PaymentEntryCommission
        (ReceiptID, PaymentReceiptEntryID, DebtAccountID, PaymentDate, Amount, DaysElapsed, CommissionID, CommissionAmount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (receipt_id, paymentEntry_id, debtaccount_id, payment_date, amount, days_elapsed, commission_id, commission_amount))


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
                   UPDATE Commission_Receipt.DebtAccount
                   SET PaidAmount = %s
                   WHERE AccountID = %s
                   ''', (new_paidAmount, account_id))
    
def revert_invoicePaidAmount(account_id, new_paidAmount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Commission_Receipt.DebtAccount
        SET PaidAmount = %s
        WHERE AccountID = %s
    ''', (new_paidAmount, account_id))
    conn.commit()
    conn.close()
    

def set_DebtPaymentRelation(cursor, account_id, receipt_id, invoice_paidAmount):
    cursor.execute('''
                    INSERT INTO Commission_Receipt.DebtPaymentRelation
                    (DebtAccountID, PaymentReceiptID, isRetail, PaidAmount)
                    VALUES (%s, %s, %s, %s)
                    ''', (account_id, int(receipt_id), 0, invoice_paidAmount))


def set_SalesRepCommission(cursor, sales_rep_id, account_id, is_retail, balance_amount, days_passed, commission_amount, receipt_id):
    cursor.execute('''
                    INSERT INTO Commission_Receipt.SalesRepCommission
                    (SalesRepID, AccountID, IsRetail, AmountOwed, DaysElapsed, CommissionAmount, CreatedAt, ReceiptID)
                    VALUES (%s, %s, %s, %s, %s, %s, GETDATE(), %s)
                    ''', (sales_rep_id, account_id, is_retail, balance_amount, days_passed, commission_amount, receipt_id))
    

def set_isReviewedReceipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   UPDATE Commission_Receipt.PaymentReceipt
                   SET IsReviewed = 1, ReviewedDate = GETDATE()
                   WHERE ReceiptID = %s
                   ''', (receipt_id))
    conn.commit()
    conn.close()

def set_isApprovedReceipt(receipt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   UPDATE Commission_Receipt.PaymentReceipt
                   SET IsApproved = 1
                   WHERE ReceiptID = %s
                   ''', (receipt_id))
    conn.commit()
    conn.close()
