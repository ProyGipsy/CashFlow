import pyodbc
from email.message import EmailMessage
import ssl
import smtplib
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Redondeo “comercial”
getcontext().rounding = ROUND_HALF_UP

# Conexión a la BD usando pyodbc
connection_string = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=gipsy-sql-srv.database.windows.net;'
    'DATABASE=gipsyIDB;'
    'UID=gipsyApp;'
    'PWD=Ap!tsgps2025#07'
)

def get_db_connection():
    return pyodbc.connect(connection_string)


# Consultas resumen

def get_REMBD_Report():
    conn = get_db_connection()
    cursor = conn.cursor()
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
						PR.CommissionAmount_Bs AS ReceiptCommissionAmount_Bs,
						PR.CommissionAmount_USD AS ReceiptCommissionAmount_USD,
                        PEC.PaymentReceiptEntryID,
                        PEC.PaymentDate,
                        PEC.Amount AS PaymentEntryAmount,
                        PEC.CommissionAmount AS PaymentEntryCommissionAmount,
						PEC.CommissionAmount_Bs AS PaymentEntryCommissionAmount_Bs,
						PEC.CommissionAmount_USD AS PaymentEntryCommissionAmount_USD,
                        PEC.DaysElapsed AS PaymentEntryDaysElapsed,
                        SRC.CommissionAmount AS SalesRepCommissionForInvoice,
						SRC.CommissionAmount_Bs AS SalesRepCommissionForInvoice_Bs,
						SRC.CommissionAmount_USD AS SalesRepCommissionForInvoice_USD,
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
                        AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0) -- OFICIAL, DESCOMENTAR AL AUTOMATIZAR
                        AND PR.ReviewedDate < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0) -- OFICIAL, DESCOMENTAR AL AUTOMATIZAR
						--AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0) -- PRUEBA, para ver resultados del mes actual
						--AND PR.ReviewedDate < GETDATE() -- PRUEBA, para ver resultados del mes actual
                    ORDER BY PR.ReviewedDate
                    ''')
    columns = [column[0] for column in cursor.description]
    info = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return info

def get_GipsyCorp_Report():
    conn = get_db_connection()
    cursor = conn.cursor()
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
						PR.CommissionAmount_Bs AS ReceiptCommissionAmount_Bs,
						PR.CommissionAmount_USD AS ReceiptCommissionAmount_USD,
                        PEC.PaymentReceiptEntryID,
                        PEC.PaymentDate,
                        PEC.Amount AS PaymentEntryAmount,
                        PEC.CommissionAmount AS PaymentEntryCommissionAmount,
						PEC.CommissionAmount_Bs AS PaymentEntryCommissionAmount_Bs,
						PEC.CommissionAmount_USD AS PaymentEntryCommissionAmount_USD,
                        PEC.DaysElapsed AS PaymentEntryDaysElapsed,
                        SRC.CommissionAmount AS SalesRepCommissionForInvoice,
						SRC.CommissionAmount_Bs AS SalesRepCommissionForInvoice_Bs,
						SRC.CommissionAmount_USD AS SalesRepCommissionForInvoice_USD,
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
                        AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()) - 1, 0) -- OFICIAL, DESCOMENTAR AL AUTOMATIZAR
                        AND PR.ReviewedDate < DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0) -- OFICIAL, DESCOMENTAR AL AUTOMATIZAR
						--AND PR.ReviewedDate >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0) -- PRUEBA, para ver resultados del mes actual
						--AND PR.ReviewedDate < GETDATE() -- PRUEBA, para ver resultados del mes actual
                    ORDER BY PR.ReviewedDate
                    ''')
    columns = [column[0] for column in cursor.description]
    info = [dict(zip(columns, row)) for row in cursor.fetchall()]
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
            'ReceiptCommissionAmountBs': to_decimal(row['ReceiptCommissionAmount_Bs']),
            'ReceiptCommissionAmountUSD': to_decimal(row['ReceiptCommissionAmount_USD']),
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
            'SalesRepCommissionForInvoiceBs': to_decimal(row['SalesRepCommissionForInvoice_Bs']),
            'SalesRepCommissionForInvoiceUSD': to_decimal(row['SalesRepCommissionForInvoice_USD']),
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
                'PaymentEntryCommissionAmountBs': to_decimal(row['PaymentEntryCommissionAmount_Bs']),
                'PaymentEntryCommissionAmountUSD': to_decimal(row['PaymentEntryCommissionAmount_USD']),
                'PaymentEntryDaysElapsed':    row['PaymentEntryDaysElapsed'],
            }
            inv['payment_entries'].append(entry)

            # Suma con Decimal ya cuantizado - Usado en Parche
            inv['total_commission_per_invoice_entry'] += commission
            rec['total_commission_per_receipt']        += commission
            rep['total_monthly_commissions'][currency] = (
                rep['total_monthly_commissions'].get(currency, Decimal('0.00'))
                + commission
            )

    # 5) Parche para recibos sin detalle de pago: usar ReceiptCommissionAmount
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
            /* Compact print-friendly styles: smaller fonts, reduced paddings/margins */
            @media print {{
                html, body {{
                    font-size: 10px;
                }}
            }}

            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                color: black !important;
                background: white !important;
                font-family: Arial, sans-serif;
                font-size: 11px;
                line-height: 1.2;
                margin: 8px;
            }}

            h2 {{
                font-size: 14px;
                margin: 6px 0 8px 0;
            }}

            h4 {{
                font-size: 11px;
                margin: 6px 0 4px 0;
                font-weight: bold;
            }}

            p {{
                margin: 2px 0;
            }}

            .header {{
                margin-bottom: 8px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 8px;
                page-break-inside: avoid;
                font-size: 10px;
            }}

            table, th, td {{
                border: 1px solid black !important;
            }}

            th, td {{
                padding: 4px !important;
                text-align: left;
                color: black !important;
                vertical-align: top;
            }}

            th {{
                background-color: #f0f0f0 !important;
                font-weight: bold;
            }}

            .styled-table th {{
                background-color: #f0f0f0 !important;
                color: black !important;
                font-size: 10px;
            }}

            .styled-table td {{
                color: black !important;
                font-size: 10px;
            }}

            .section-separator {{
                margin-top: 12px;
                margin-bottom: 8px;
                border-top: 1px solid #6c757d;
            }}
            .receipt-section {{
                margin-left: 6px;
                margin-top: 8px;
                border-left: 3px solid #6c757d;
                padding-left: 8px;
            }}
            .invoice-section {{
                margin-left: 10px;
                margin-top: 6px;
                border-left: 2px solid #6c757d;
                padding-left: 8px;
            }}
            .payment-entry-section {{
                margin-left: 12px;
                margin-top: 6px;
                border-left: 1px dashed #6c757d;
                padding-left: 6px;
                font-size: 0.9em;
            }}
            .payment-entry-row td {{
                padding-top: 3px !important;
                padding-bottom: 3px !important;
            }}
            .total-row td {{
                font-weight: bold;
                background-color: #e0e0e0 !important;
            }}
            .subtotal-line {{
                text-align: right;
                font-weight: bold;
                padding: 4px 6px;
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
                margin-top: 6px;
                margin-bottom: 6px;
                font-size: 10px;
            }}
            .grand-total-line {{
                text-align: right;
                font-weight: bold;
                padding: 6px 0;
                border-top: 1px solid #000;
                margin-top: 10px;
                font-size: 11px;
            }}

            /* Reduce unnecessary white-space in table cells when printing */
            td, th {{
                white-space: normal;
                word-break: break-word;
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

        commission_text = ""
        if rec_data['ReceiptCommissionAmountBs'] > 0 and rec_data['ReceiptCommissionAmountUSD'] > 0:
            commission_text = f"Bs {format_currency(rec_data['ReceiptCommissionAmountBs'])} y USD {format_currency(rec_data['ReceiptCommissionAmountUSD'])}"
        elif rec_data['ReceiptCommissionAmountBs'] > 0:
            commission_text = f"Bs {format_currency(rec_data['ReceiptCommissionAmountBs'])}"
        elif rec_data['ReceiptCommissionAmountUSD'] > 0:
            commission_text = f"USD {format_currency(rec_data['ReceiptCommissionAmountUSD'])}"
        else:
            commission_text = "0.00"

        html_report += f"""
        <div class="receipt-section">
            <h4>Recibo: {receipt_id}</h4>
            <p>Tienda del Recibo: {rec_data['ReceiptStore']}</p>
            <p>Cliente del Recibo: {rec_data['ReceiptCustomer']}</p>
            <p>Moneda del Recibo: {rec_data['ReceiptCurrencyCode']}</p>
            <p>Monto Total Recibo: {rec_data['ReceiptCurrencyCode']} {format_currency(rec_data['ReceiptTotalAmount'])}</p>
            <p>Monto Comisión Recibo (total): {commission_text}</p>

            <p style="font-weight: bold;">Facturas Asociadas a este recibo:</p>
        """
        # Itera sobre las facturas dentro de este recibo
        for account_id, inv_data in rec_data['invoices'].items():
            invoice_commission_text = ""
            if inv_data['SalesRepCommissionForInvoiceBs'] > 0 and inv_data['SalesRepCommissionForInvoiceUSD'] > 0:
                invoice_commission_text = f"Bs {format_currency(inv_data['SalesRepCommissionForInvoiceBs'])} y USD {format_currency(inv_data['SalesRepCommissionForInvoiceUSD'])}"
            elif inv_data['SalesRepCommissionForInvoiceBs'] > 0:
                invoice_commission_text = f"Bs {format_currency(inv_data['SalesRepCommissionForInvoiceBs'])}"
            elif inv_data['SalesRepCommissionForInvoiceUSD'] > 0:
                invoice_commission_text = f"USD {format_currency(inv_data['SalesRepCommissionForInvoiceUSD'])}"
            else:
                invoice_commission_text = "0.00"

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
                            <td>{invoice_commission_text}</td>
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
                    payment_commission_text = ""
                    if pe_data['PaymentEntryCommissionAmountBs'] > 0 and pe_data['PaymentEntryCommissionAmountUSD'] > 0:
                        payment_commission_text = f"Bs {format_currency(pe_data['PaymentEntryCommissionAmountBs'])} y USD {format_currency(pe_data['PaymentEntryCommissionAmountUSD'])}"
                    elif pe_data['PaymentEntryCommissionAmountBs'] > 0:
                        payment_commission_text = f"Bs {format_currency(pe_data['PaymentEntryCommissionAmountBs'])}"
                    elif pe_data['PaymentEntryCommissionAmountUSD'] > 0:
                        payment_commission_text = f"USD {format_currency(pe_data['PaymentEntryCommissionAmountUSD'])}"
                    else:
                        payment_commission_text = "0.00"

                    html_report += f"""
                        <tr class="payment-entry-row">
                            <td>{pe_data['PaymentDate']}</td>
                            <td>{inv_data['InvoiceCurrencyCode']} {format_currency(pe_data['PaymentEntryAmount'])}</td>
                            <td>{payment_commission_text}</td>
                            <td>{pe_data['PaymentEntryDaysElapsed']}</td>
                        </tr>
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

    # Totales de Comisiones separados por Bs y USD (si existen), usar 0.00 por defecto
    bs_total = total_monthly_commissions.get('Bs') if isinstance(total_monthly_commissions, dict) else None
    usd_total = total_monthly_commissions.get('USD') if isinstance(total_monthly_commissions, dict) else None

    if bs_total is None:
        for k in ("Bs"):
            if isinstance(total_monthly_commissions, dict) and k in total_monthly_commissions:
                bs_total = total_monthly_commissions[k]
                break
    if usd_total is None:
        for k in ("USD"):
            if isinstance(total_monthly_commissions, dict) and k in total_monthly_commissions:
                usd_total = total_monthly_commissions[k]
                break

    # Normalizar a Decimal/str y formatear
    try:
        bs_total_val = bs_total if bs_total is not None else Decimal('0.00')
    except Exception:
        bs_total_val = Decimal('0.00')
    try:
        usd_total_val = usd_total if usd_total is not None else Decimal('0.00')
    except Exception:
        usd_total_val = Decimal('0.00')

    html_report += f"""
                Total de Comisiones del Mes: Bs <strong>Bs {format_currency(bs_total_val)} y USD {format_currency(usd_total_val)}</strong><br>
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

    mail_server = "smtp.gmail.com"
    mail_port = 465

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
            /* Compact print-friendly styles for summary */
            @media print {{
                html, body {{
                    font-size: 10px;
                }}
            }}

            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                color: black !important;
                background: white !important;
                font-family: Arial, sans-serif;
                font-size: 11px;
                line-height: 1.2;
                margin: 8px;
            }}

            h2 {{
                font-size: 14px;
                margin: 6px 0 8px 0;
            }}

            p {{
                margin: 2px 0;
                font-size: 10px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 8px;
                page-break-inside: avoid;
                font-size: 10px;
            }}

            table, th, td {{
                border: 1px solid black !important;
            }}

            th, td {{
                padding: 4px !important;
                text-align: left;
                color: black !important;
                vertical-align: top;
            }}

            th {{
                background-color: #f0f0f0 !important;
                font-weight: bold;
            }}

            .styled-table th {{
                background-color: #f0f0f0 !important;
                color: black !important;
                font-size: 10px;
            }}

            .styled-table td {{
                color: black !important;
                font-size: 10px;
            }}

            .grand-total-line {{
                text-align: right;
                font-weight: bold;
                padding: 6px 0;
                border-top: 1px solid #000;
                margin-top: 10px;
                font-size: 11px;
            }}

            td, th {{
                white-space: normal;
                word-break: break-word;
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
    # Ordenando Vendedor por ID
    def _sort_key(item):
        key = item[0]
        try:
            return int(key)
        except Exception:
            try:
                return int(str(key))
            except Exception:
                return str(key)

    for salesrep_id, salesrep_data in sorted(grouped_data.items(), key=_sort_key):
        receipts = ", ".join(str(r_id) for r_id in salesrep_data['receipts'].keys())
        # Mostrar totales separados por Bs y USD (usar 0.00 si no existen)
        total_commissions = ""
        tm = salesrep_data.get('total_monthly_commissions', {}) if isinstance(salesrep_data, dict) else {}
        bs_total = None
        usd_total = None
        if isinstance(tm, dict):
            bs_total = tm.get('Bs')
            usd_total = tm.get('USD')

        try:
            bs_total_val = bs_total if bs_total is not None else Decimal('0.00')
        except Exception:
            bs_total_val = Decimal('0.00')
        try:
            usd_total_val = usd_total if usd_total is not None else Decimal('0.00')
        except Exception:
            usd_total_val = Decimal('0.00')

        total_commissions = f"Bs {format_currency(bs_total_val)} y USD {format_currency(usd_total_val)}<br>"
        
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
    receiver_email_test = 'proyectogipsy@gmail.com' #RECEPTOR DE PRUEBA, ACTIVAR ENVÍO A VENDEDOR AL CULMINAR

    # -- Reportes REMBD (Tiendas 904, 905) --
    print("\n--- Procesando datos para tiendas REMBD (904, 905) ---")
    raw_data_rembd = get_REMBD_Report()

    if raw_data_rembd:
        sender_email = 'reciborembd@gmail.com'
        email_password = "stui xigp vsrn cmlq"
        receiver_email_rembd = 'recibo@rembd.com'

        grouped_data_by_salesrep_rembd = group_raw_data_by_salesrep(raw_data_rembd)
        print(f"Total de vendedores con datos REMBD: {len(grouped_data_by_salesrep_rembd)}")
        for salesrep_id, salesrep_data in grouped_data_by_salesrep_rembd.items():
            
            # Correo individual por vendedor
            print(f"\n  Generando y enviando reporte REMBD para: {salesrep_data['name']} ({salesrep_data['email']})")
            html_content = format_html_for_single_salesrep(salesrep_data, "REMBD")
            subject = f"Reporte Mensual de Comisiones - REMBD - {salesrep_data['name']}"
            #recipient_list = [salesrep_data['email'], receiver_email_rembd]  #ACTIVAR PARA ENVÍO A VENDEDOR Y OFICINA
            recipient_list = [receiver_email_test] #TESTING
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
        sender_email = 'recibogipsycorp@gmail.com'
        email_password = "wdni ciiw akdu gtvl" 
        receiver_email_gipsycorp = 'recibo@gipsycorp.com'

        grouped_data_by_salesrep_gipsycorp = group_raw_data_by_salesrep(raw_data_gipsycorp)
        print(f"Total de vendedores con datos GipsyCorp: {len(grouped_data_by_salesrep_gipsycorp)}")
        for salesrep_id, salesrep_data in grouped_data_by_salesrep_gipsycorp.items():
            
            # Correo individual por vendedor
            print(f"\n  Generando y enviando reporte GipsyCorp para: {salesrep_data['name']} ({salesrep_data['email']})")
            html_content = format_html_for_single_salesrep(salesrep_data, "GipsyCorp")
            subject = f"Reporte Mensual de Comisiones - GipsyCorp - {salesrep_data['name']}"
            #recipient_list = [salesrep_data['email'], receiver_email_gipsycorp]  #ACTIVAR PARA ENVÍO A VENDEDOR Y OFICINA
            recipient_list = [receiver_email_test] #TESTING
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