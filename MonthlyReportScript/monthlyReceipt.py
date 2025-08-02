import os
import pymssql
from dbutils.pooled_db import PooledDB
from email.message import EmailMessage
import ssl
import smtplib
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_UP

from dotenv import load_dotenv
load_dotenv()

# Redondeo “comercial”
getcontext().rounding = ROUND_HALF_UP

# Conexión a la BD
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


# Consultas resumen
def get_REMBD_Report():
    conn = get_db_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute('''
                    SELECT DISTINCT
                        U.firstName,
                        U.lastName,
                        U.salesRepId,
                        U.email,
                        PR.ReceiptID,
                        S.Name AS StoreName,
                        C.FirstName + ' ' + C.LastName AS CustomerName,
                        CY.ID AS CurrencyID,
                        CY.Code AS CurrencyCode,
                        PR.ReviewedDate,
                        SRC.CreatedAt AS RegistrationDate,
                        DA.StoreID,
                        DA.AccountID,
                        DA.CurrencyID,
                        DA.DueDate,
                        DA.N_CTA AS InvoiceNumber,
                        DA.Amount AS InvoiceTotalAmount,
                        DA.PaidAmount AS InvoicePaidAmount,
                        PR.Amount AS ReceiptTotalAmount,
                        PR.CommissionAmount AS ReceiptCommissionAmount,
                        PEC.PaymentReceiptEntryID,
                        PEC.PaymentDate,
                        PEC.Amount AS PaymentEntryAmount,
                        PEC.CommissionAmount AS PaymentEntryCommissionAmount,
                        PEC.DaysElapsed AS PaymentEntryDaysElapsed,
                        SRC.CommissionAmount AS SalesRepCommissionForInvoice,
                        SRC.AmountOwed AS SalesRepAmountOwedForInvoice
                    FROM [AccessControl].[Users] AS U
                    INNER JOIN [Commission_Receipt].[DebtAccount] AS DA ON U.salesRepId = DA.SalesRepID
                    INNER JOIN [Commission_Receipt].[DebtPaymentRelation] AS DPR ON DA.AccountID = DPR.DebtAccountID
                    JOIN [Main].[Store] AS S ON DA.StoreID = S.ID
                    JOIN [Commission_Receipt].[Customer] C ON DA.CustomerID = C.ID
                    JOIN [Main].[Currency] CY ON DA.CurrencyID = CY.ID
                    INNER JOIN [Commission_Receipt].[PaymentReceipt] AS PR ON DPR.PaymentReceiptID = PR.ReceiptID
                    LEFT JOIN [Commission_Receipt].[PaymentEntryCommission] AS PEC ON PR.ReceiptID = PEC.ReceiptID AND DA.AccountID = PEC.DebtAccountID
                    LEFT JOIN [Commission_Receipt].[SalesRepCommission] AS SRC ON U.salesRepId = SRC.SalesRepID AND DA.AccountID = SRC.AccountID AND PR.ReceiptID = SRC.ReceiptID
                    WHERE
                        PR.IsApproved = 1
                        AND DA.StoreID IN (904, 905)
                        --AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0)
                        --AND PR.ReviewedDate < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
                        AND SRC.CreatedAt >= DATEADD(month, DATEDIFF(month, 0, GETDATE())-1, 0)
                        AND SRC.CreatedAt < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
                    ORDER BY SRC.CreatedAt
                    ''')
    info = cursor.fetchall()
    conn.close()
    return info

def get_GipsyCorp_Report():
    conn = get_db_connection()
    cursor = conn.cursor(as_dict=True)
    cursor.execute('''
                    SELECT DISTINCT
                        U.firstName,
                        U.lastName,
                        U.salesRepId,
                        U.email,
                        PR.ReceiptID,
                        S.Name AS StoreName,
                        C.FirstName + ' ' + C.LastName AS CustomerName,
                        CY.ID AS CurrencyID,
                        CY.Code AS CurrencyCode,
                        PR.ReviewedDate,
                        SRC.CreatedAt AS RegistrationDate,
                        DA.StoreID,
                        DA.AccountID,
                        DA.CurrencyID,
                        DA.DueDate,
                        DA.N_CTA AS InvoiceNumber,
                        DA.Amount AS InvoiceTotalAmount,
                        DA.PaidAmount AS InvoicePaidAmount,
                        PR.Amount AS ReceiptTotalAmount,
                        PR.CommissionAmount AS ReceiptCommissionAmount,
                        PEC.PaymentReceiptEntryID,
                        PEC.PaymentDate,
                        PEC.Amount AS PaymentEntryAmount,
                        PEC.CommissionAmount AS PaymentEntryCommissionAmount,
                        PEC.DaysElapsed AS PaymentEntryDaysElapsed,
                        SRC.CommissionAmount AS SalesRepCommissionForInvoice,
                        SRC.AmountOwed AS SalesRepAmountOwedForInvoice
                    FROM [AccessControl].[Users] AS U
                    INNER JOIN [Commission_Receipt].[DebtAccount] AS DA ON U.salesRepId = DA.SalesRepID
                    INNER JOIN [Commission_Receipt].[DebtPaymentRelation] AS DPR ON DA.AccountID = DPR.DebtAccountID
                    JOIN [Main].[Store] AS S ON DA.StoreID = S.ID
                    JOIN [Commission_Receipt].[Customer] C ON DA.CustomerID = C.ID
                    JOIN [Main].[Currency] CY ON DA.CurrencyID = CY.ID
                    INNER JOIN [Commission_Receipt].[PaymentReceipt] AS PR ON DPR.PaymentReceiptID = PR.ReceiptID
                    LEFT JOIN [Commission_Receipt].[PaymentEntryCommission] AS PEC ON PR.ReceiptID = PEC.ReceiptID AND DA.AccountID = PEC.DebtAccountID
                    LEFT JOIN [Commission_Receipt].[SalesRepCommission] AS SRC ON U.salesRepId = SRC.SalesRepID AND DA.AccountID = SRC.AccountID AND PR.ReceiptID = SRC.ReceiptID
                    WHERE
                        PR.IsApproved = 1
                        AND DA.StoreID NOT IN (904, 905)
                        --AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0)
                        --AND PR.ReviewedDate < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
                        AND SRC.CreatedAt >= DATEADD(month, DATEDIFF(month, 0, GETDATE())-1, 0)
                        AND SRC.CreatedAt < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
                    ORDER BY SRC.CreatedAt
                    ''')
    info = cursor.fetchall()
    conn.close()
    return info

def to_decimal(value):
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(Decimal('0.01'))

#Formato de Moneda
def format_currency(amount):
    if amount is None:
        return "0.00"
    if isinstance(amount, (float, Decimal)):
        return "{:,.2f}".format(amount).replace(",", "X").replace(".", ",").replace("X", ".")
    return amount

def group_raw_data_by_salesrep(data):
    """
    Agrupa filas por vendedor, recibo, factura y forma de pago,
    calculando totales de comisiones con dos decimales exactos.
    """
    report = {}

    for row in data:
        rep_id = row['salesRepId']
        receipt_id = row['ReceiptID']
        acc_id = row['AccountID']
        currency = row['CurrencyCode']

        # 1) Inicializar estructura de vendedor
        rep = report.setdefault(rep_id, {
            'name':         f"{row['firstName']} {row['lastName']}",
            'email':        row['email'],
            'receipts':     {},
            'total_monthly_commissions': {}
        })

        # 2) Inicializar recibo
        rec = rep['receipts'].setdefault(receipt_id, {
            'ReceiptStore':         row['StoreName'],
            'ReceiptCustomer':      row['CustomerName'],
            'ReceiptCurrencyCode':  currency,
            'ReceiptTotalAmount':   to_decimal(row['ReceiptTotalAmount']),
            'ReceiptCommissionAmount': to_decimal(row['ReceiptCommissionAmount']),
            'invoices':             {},
            'has_payment_entries':  False,
            'total_commission_per_receipt': Decimal('0.00')
        })

        # 3) Inicializar factura
        inv = rec['invoices'].setdefault(acc_id, {
            'InvoiceNumber':         row['InvoiceNumber'],
            'DueDate':      row['DueDate'].strftime('%d-%m-%Y') if row['DueDate'] else 'N/A',
            'InvoiceTotalAmount':    to_decimal(row['InvoiceTotalAmount']),
            'InvoicePaidAmount':     to_decimal(row['InvoicePaidAmount']),
            'InvoiceCurrencyCode':   currency,
            'SalesRepCommissionForInvoice': to_decimal(row['SalesRepCommissionForInvoice']),
            'SalesRepAmountOwedForInvoice': to_decimal(row['SalesRepAmountOwedForInvoice']),
            'payment_entries':       [],
            'total_commission_per_invoice_entry': Decimal('0.00')
        })

        # 4) Agregar forma de pago y comisiones
        if row['PaymentEntryAmount'] is not None:
            rec['has_payment_entries'] = True

            commission = to_decimal(row['PaymentEntryCommissionAmount'])
            entry = {
                'PaymentReceiptEntryID':      row['PaymentReceiptEntryID'],
                'PaymentDate':                row['PaymentDate'].strftime('%d-%m-%Y') if row['PaymentDate'] else 'N/A',
                'PaymentEntryAmount':         to_decimal(row['PaymentEntryAmount']),
                'PaymentEntryCommissionAmount': commission,
                'PaymentEntryDaysElapsed':    row['PaymentEntryDaysElapsed'],
            }
            inv['payment_entries'].append(entry)

            # Suma con Decimal ya cuantizado
            inv['total_commission_per_invoice_entry'] += commission
            rec['total_commission_per_receipt']        += commission
            rep['total_monthly_commissions'][currency] = (
                rep['total_monthly_commissions'].get(currency, Decimal('0.00'))
                + commission
            )

    # 5) Parche para recibos sin pagos: usar ReceiptCommissionAmount
    for rep in report.values():
        for rec in rep['receipts'].values():
            if not rec['has_payment_entries']:
                commission = rec['ReceiptCommissionAmount']
                curr = rec['ReceiptCurrencyCode']
                rec['total_commission_per_receipt'] = commission
                rep['total_monthly_commissions'][curr] = (
                    rep['total_monthly_commissions'].get(curr, Decimal('0.00'))
                    + commission
                )

    return report


# HTML para resumen individual de vendedores
def format_html_for_single_salesrep(salesrep_data, store_type):

    salesrep_name = salesrep_data['name']
    total_monthly_commissions = salesrep_data.get('total_monthly_commissions', {})

    html_report = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"/>
        <style>
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                color: black !important;
                background: white !important;
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }}

            .header {{
                margin-bottom: 20px;
            }}

            .header-text p {{
                margin: 5px 0;
                color: black !important;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}

            table, th, td {{
                border: 1px solid black !important;
            }}

            th, td {{
                padding: 6px !important;
                text-align: left;
                color: black !important;
            }}

            th {{
                background-color: #f0f0f0 !important;
            }}

            .styled-table th {{
                background-color: #f0f0f0 !important;
                color: black !important;
            }}

            .styled-table td {{
                color: black !important;
            }}
            .section-separator {{
                margin-top: 30px;
                margin-bottom: 20px;
                border-top: 2px solid #6c757d;
            }}
            .receipt-section {{
                margin-left: 10px;
                margin-top: 20px;
                border-left: 3px solid #6c757d;
                padding-left: 10px;
            }}
            .invoice-section {{
                margin-left: 20px;
                margin-top: 15px;
                border-left: 2px solid #6c757d;
                padding-left: 10px;
            }}
            .payment-entry-section {{
                margin-left: 30px;
                margin-top: 10px;
                border-left: 1px dashed #6c757d;
                padding-left: 10px;
                font-size: 0.95em;
            }}
            .total-row td {{
                font-weight: bold;
                background-color: #e0e0e0 !important;
            }}
            .subtotal-line {{
                text-align: right;
                font-weight: bold;
                padding: 5px 8px;
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
                margin-top: 5px;
                margin-bottom: 10px;
            }}
            .grand-total-line {{
                text-align: right;
                font-weight: bold;
                padding: 8px 0;
                border-top: 2px solid #000;
                margin-top: 20px;
                font-size: 1.1em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Reporte Mensual de Comisiones de Cobranza {store_type}</h2>
            <p><strong>Vendedor:</strong> {salesrep_name} </p>
            <p>Fecha de emisión: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    """

    # Itera sobre los recibos del vendedor
    for receipt_id, rec_data in salesrep_data['receipts'].items():
        html_report += f"""
        <div class="receipt-section">
            <h4>Recibo: {receipt_id}</h4>
            <p>Tienda del Recibo: {rec_data['ReceiptStore']}</p>
            <p>Cliente del Recibo: {rec_data['ReceiptCustomer']}</p>
            <p>Moneda del Recibo: {rec_data['ReceiptCurrencyCode']}</p>
            <p>Monto Total Recibo: {rec_data['ReceiptCurrencyCode']} {format_currency(rec_data['ReceiptTotalAmount'])}</p>
            <p>Monto Comisión Recibo (total): {format_currency(rec_data['ReceiptCommissionAmount'])}</p>

            <p style="font-weight: bold;">Facturas Asociadas a este recibo:</p>
        """
        # Itera sobre las facturas dentro de este recibo
        for account_id, inv_data in rec_data['invoices'].items():
            html_report += f"""
            <div class="invoice-section">
                <h4>Factura: {inv_data['InvoiceNumber']} (Vencimiento: {inv_data['DueDate']})</h4>
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>N_CTA</th>
                            <th>Monto Total Factura</th>
                            <th>Monto Pagado Factura</th>
                            <th>Comisión Vendedor (Factura)</th>
                            <th>Monto Adeudado (Factura)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{inv_data['InvoiceNumber']}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(inv_data['InvoiceTotalAmount'])}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(inv_data['InvoicePaidAmount'])}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(inv_data['SalesRepCommissionForInvoice'])}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(inv_data['SalesRepAmountOwedForInvoice'])}</td>
                        </tr>
                    </tbody>
                </table>
            """
            # Condicional para mostrar la tabla de formas de pago
            if inv_data['payment_entries']:
                html_report += f"""
                <h4>Detalle de Formas de Pago para esta Factura:</h4>
                <table class="styled-table" id="pago-table">
                    <thead>
                        <tr>
                            <th>Fecha de Pago</th>
                            <th>Monto Entrada</th>
                            <th>Comisión Entrada</th>
                            <th>Días Transcurridos</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for pe_data in inv_data['payment_entries']:
                    html_report += f"""
                        <tr class="payment-entry-row">
                            <td>{pe_data['PaymentDate']}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(pe_data['PaymentEntryAmount'])}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(pe_data['PaymentEntryCommissionAmount'])}</td>
                            <td>{pe_data['PaymentEntryDaysElapsed']}</td>
                        </tr>
                    """
                html_report += f"""
                    <tr class="total-row">
                        <td colspan="3" style="text-align: right;">Total Comisión (Formas de Pago de Factura):</td>
                        <td>{inv_data['InvoiceCurrencyCode']} {format_currency(inv_data['total_commission_per_invoice_entry'])}</td>
                        <td></td>
                    </tr>
                    </tbody>
                </table>
                """
            html_report += """
            </div> """
        html_report += f"""
        <div class="subtotal-line">
            Total Comisión Acumulada para Recibo ({receipt_id}): <strong>{inv_data['InvoiceCurrencyCode']} {format_currency(rec_data['total_commission_per_receipt'])}</strong>
        </div>
        """
        html_report += """
        </div> """

    html_report += f"""
            <div class="grand-total-line">
            """
    if total_monthly_commissions:
        for currency, total in total_monthly_commissions.items():
            html_report += f"""
                Total de Comisiones de de Facturas en {currency} del Mes: <strong>{currency} {format_currency(total)}</strong><br>
            """
    html_report += f"""
            </div>
            """

    html_report += """
    </body>
    </html>
    """
    return html_report


# Envío de correo individual por vendedor
def send_email(subject, body_html, sender_email, email_password, receiver_emails):

    print("Datos para envío del correo:")
    print("subject: ", subject)
    print("sender_email: ", sender_email)
    print("receiver_email: ", receiver_emails)

    mail_server = os.environ.get("MAIL_SERVER_RECEIPT")
    mail_port = os.environ.get("MAIL_PORT")

    em = EmailMessage()
    em["From"] = sender_email
    em["To"] = ", ".join(receiver_emails)
    em["Subject"] = subject
    em.set_content("Este es un correo HTML. Por favor, usa un cliente de correo compatible para ver el contenido completo.")
    em.add_alternative(body_html, subtype="html")

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as smtp:
            smtp.login(sender_email, email_password)
            smtp.sendmail(sender_email, receiver_emails, em.as_string())
        print(f"Correo enviado exitosamente a {', '.join(receiver_emails)}!")
    except Exception as e:
        print(f"Error al enviar el correo a {', '.join(receiver_emails)}: {e}")


# Resumen general de comisiones por vendedor, reporte para la oficina
def create_summary_html(grouped_data, store_type):
    current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    html_summary = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"/>
        <style>
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                color: black !important;
                background: white !important;
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }}

            .header {{
                margin-bottom: 20px;
            }}

            .header-text p {{
                margin: 5px 0;
                color: black !important;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}

            table, th, td {{
                border: 1px solid black !important;
            }}

            th, td {{
                padding: 6px !important;
                text-align: left;
                color: black !important;
            }}

            th {{
                background-color: #f0f0f0 !important;
            }}

            .styled-table th {{
                background-color: #f0f0f0 !important;
                color: black !important;
            }}

            .styled-table td {{
                color: black !important;
            }}
            .section-separator {{
                margin-top: 30px;
                margin-bottom: 20px;
                border-top: 2px solid #6c757d;
            }}
            .receipt-section {{
                margin-left: 10px;
                margin-top: 20px;
                border-left: 3px solid #6c757d;
                padding-left: 10px;
            }}
            .invoice-section {{
                margin-left: 20px;
                margin-top: 15px;
                border-left: 2px solid #6c757d;
                padding-left: 10px;
            }}
            .payment-entry-section {{
                margin-left: 30px;
                margin-top: 10px;
                border-left: 1px dashed #6c757d;
                padding-left: 10px;
                font-size: 0.95em;
            }}
            .total-row td {{
                font-weight: bold;
                background-color: #e0e0e0 !important;
            }}
            .subtotal-line {{
                text-align: right;
                font-weight: bold;
                padding: 5px 8px;
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
                margin-top: 5px;
                margin-bottom: 10px;
            }}
            .grand-total-line {{
                text-align: right;
                font-weight: bold;
                padding: 8px 0;
                border-top: 2px solid #000;
                margin-top: 20px;
                font-size: 1.1em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Reporte Mensual de Comisiones de Cobranza {store_type} por Vendedor</h2>
            <p><strong>Fecha de emisión:</strong> {current_date}</p>
        </div>

        <table class="styled-table">
            <thead>
                <tr>
                    <th>ID de Vendedor</th>
                    <th>Nombre Vendedor</th>
                    <th>Recibos Registrados</th>
                    <th>Total Mensual del Vendedor</th>
                </tr>
            </thead>
            <tbody>
    """
    for salesrep_id, salesrep_data in grouped_data.items():
        receipts = ", ".join(str(r_id) for r_id in salesrep_data['receipts'].keys())
        total_commissions = ""
        for currency, total in salesrep_data['total_monthly_commissions'].items():
            total_commissions += f"{currency} {format_currency(total)}<br>"
        
        html_summary += f"""
                <tr>
                    <td>{salesrep_id}</td>
                    <td>{salesrep_data['name']}</td>
                    <td>{receipts}</td>
                    <td>{total_commissions}</td>
                </tr>
        """
    
    html_summary += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_summary



if __name__ == "__main__":
    print("Iniciando la generación del reporte mensual de comisiones...")
    receiver_email_test = os.environ.get("MAIL_RECIPIENT_TEST") #RECEPTOR DE PRUEBA, ACTIVAR ENVÍO A VENDEDOR AL CULMINAR
    receiver_email_test2 = os.environ.get("MAIL_RECIPIENT_TEST2") #RECEPTOR DE PRUEBA, ACTIVAR ENVÍO A OFICINA AL CULMINAR

    # -- Reportes REMBD (Tiendas 904, 905) --
    print("\n--- Procesando datos para tiendas REMBD (904, 905) ---")
    raw_data_rembd = get_REMBD_Report()

    if raw_data_rembd:
        sender_email = os.environ.get("MAIL_USERNAME_RECEIPT_REMBD")
        email_password = os.environ.get("MAIL_PASSWORD_RECEIPT_REMBD")
        receiver_email_rembd = os.environ.get("MAIL_RECIPIENT_RECEIPT_REMBD")

        grouped_data_by_salesrep_rembd = group_raw_data_by_salesrep(raw_data_rembd)
        print(f"Total de vendedores con datos REMBD: {len(grouped_data_by_salesrep_rembd)}")
        for salesrep_id, salesrep_data in grouped_data_by_salesrep_rembd.items():
            
            # Correo individual por vendedor
            print(f"\n  Generando y enviando reporte REMBD para: {salesrep_data['name']} ({salesrep_data['email']})")
            html_content = format_html_for_single_salesrep(salesrep_data, "REMBD")
            subject = f"Reporte Mensual de Comisiones - REMBD - {salesrep_data['name']}"
            #recipient_list = [salesrep_data['email'], receiver_email_rembd]  #ACTIVAR PARA ENVÍO A VENDEDOR Y OFICINA
            recipient_list = [receiver_email_test, receiver_email_test2] #TESTING
            send_email(subject, html_content, sender_email, email_password, recipient_list)

        # Correo resumen para la oficina
        print(f"\n  Generando y enviando resumen REMBD para la oficina")
        html_summary = create_summary_html(grouped_data_by_salesrep_rembd, "REMBD")
        summary_subject = "Resumen Mensual de Comisiones - REMBD"
        #summary_recipient_list = [receiver_email_rembd]  #ACTIVAR PARA ENVÍO A OFICINA
        summary_recipient_list = [receiver_email_test] #TESTING
        send_email(summary_subject, html_summary, sender_email, email_password, summary_recipient_list)
    else:
        print("No se encontraron datos de comisiones para tiendas REMBD.")


    # -- Reportes GipsyCorp (Otras Tiendas) --
    print("\n--- Procesando datos para tiendas GipsyCorp (Otras Tiendas) ---")
    raw_data_gipsycorp = get_GipsyCorp_Report()

    if raw_data_gipsycorp:
        sender_email = os.environ.get("MAIL_USERNAME_RECEIPT")
        email_password = os.environ.get("MAIL_PASSWORD_RECEIPT")
        receiver_email_gipsycorp = os.environ.get("MAIL_RECIPIENT_RECEIPT")

        grouped_data_by_salesrep_gipsycorp = group_raw_data_by_salesrep(raw_data_gipsycorp)
        print(f"Total de vendedores con datos GipsyCorp: {len(grouped_data_by_salesrep_gipsycorp)}")
        for salesrep_id, salesrep_data in grouped_data_by_salesrep_gipsycorp.items():
            
            # Correo individual por vendedor
            print(f"\n  Generando y enviando reporte GipsyCorp para: {salesrep_data['name']} ({salesrep_data['email']})")
            html_content = format_html_for_single_salesrep(salesrep_data, "GipsyCorp")
            subject = f"Reporte Mensual de Comisiones - GipsyCorp - {salesrep_data['name']}"
            #recipient_list = [salesrep_data['email'], receiver_email_gipsycorp]  #ACTIVAR PARA ENVÍO A VENDEDOR Y OFICINA
            recipient_list = [receiver_email_test, receiver_email_test2] #TESTING
            send_email(subject, html_content, sender_email, email_password, recipient_list)

        # Correo resumen para la oficina
        print(f"\n  Generando y enviando resumen GipsyCorp para la oficina")
        html_summary = create_summary_html(grouped_data_by_salesrep_gipsycorp, "GipsyCorp")
        summary_subject = "Resumen Mensual de Comisiones - GipsyCorp"
        #summary_recipient_list = [receiver_email_gipsycorp]  #ACTIVAR PARA ENVÍO A OFICINA
        summary_recipient_list = [receiver_email_test] #TESTING
        send_email(summary_subject, html_summary, sender_email, email_password, summary_recipient_list)
    else:
        print("No se encontraron datos de comisiones para tiendas GipsyCorp.")