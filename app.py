import os
import urllib.parse
import json
from io import BytesIO
import mimetypes
import requests
import base64
from datetime import datetime, timedelta

#from weasyprint import HTML
from werkzeug.utils import secure_filename

from datetime import datetime
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response, current_app)
from flask_mail import Mail, Message

from cashflow_db import (get_beneficiaries, get_cashflowStores, get_concepts, get_creditConcepts, get_debitConcepts,
    get_operations, get_last_beneficiary_id, get_last_concept_id, get_motion_id, get_last_store_id,
    set_beneficiaries, set_concepts, set_stores, set_operations)

# OJO: Variables balance corresponden a PaidAmount
from receipt_db import (get_db_connection, get_receiptStores_DebtAccount, get_receiptStores_Receipts, get_receiptStores_Sellers,
    get_receiptStore_by_id, get_sellers, get_count_sellers, get_seller_details, get_customers, get_tender, get_commissionsRules,
    get_invoices_by_customer, get_receiptsInfo, get_receiptsStoreCustomer, get_bankAccounts, get_commissions, get_customer_by_id,
    get_customers_with_unvalidated_receipts, get_count_customers_with_unvalidated_receipts, get_unvalidated_receipts_by_customer,
    get_invoices_by_receipt, get_paymentEntries_by_receipt, get_salesRep_isRetail, set_SalesRepCommission, get_SalesRepCommission,
    set_commissionsRules, set_paymentReceipt, set_paymentEntry, save_proofOfPayment, set_invoicePaidAmount, set_DebtPaymentRelation,
    set_isReviewedReceipt, set_isApprovedReceipt, get_onedriveProofsOfPayments, get_onedriveStoreLogo,
    get_count_customers_with_accountsReceivable, get_currency)

from onedrive import get_onedrive_headers

app = Flask(__name__)

# Configuración del servidor SMTP
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL')

@app.route('/')
def index():
    return render_template('index.html')


# INICIOS DE SESIÓN

@app.route('/loginCashflow', methods=['GET', 'POST'])
def loginCashflow():
    if request.method == 'POST':
        user = request.form.get('User')
        password = request.form.get('Password')

        if ((user == os.environ.get('CASHFLOW_USERTDV') and password == os.environ.get('CASHFLOW_PASSTDV')) or
            (user == os.environ.get('CASHFLOW_USERGIPSY') and password == os.environ.get('CASHFLOW_PASSGIPSY'))):
            return redirect(url_for('homeCashier'))
        else:
            return render_template('cashflow.login.html', error="Credenciales incorrectas, por favor intente de nuevo.")
            
    return render_template('cashflow.login.html')


@app.route('/loginReceipt', methods=['GET', 'POST'])
def loginReceipt():
    if request.method == 'POST':
        user = request.form.get('User')
        password = request.form.get('Password')

        if ((user == os.environ.get('CASHFLOW_USERTDV') and password == os.environ.get('CASHFLOW_PASSTDV')) or
            (user == os.environ.get('CASHFLOW_USERGIPSY') and password == os.environ.get('CASHFLOW_PASSGIPSY'))):
            return redirect(url_for('homeAdmin'))
        elif (user == os.environ.get('RECEIPT_USERSELLER') and password == os.environ.get('RECEIPT_PASSSELLER')):
            return redirect(url_for('homeSeller'))
        else:
            return render_template('receipt.login.html', error="Credenciales incorrectas, por favor intente de nuevo.")

    return render_template('receipt.login.html')


# CASHFLOW - RUTAS

# Configuración de correo SMTP para Flujo de Caja
#app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_CASHFLOW') #Correo por defecto
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_CASHFLOW')
MAIL_RECIPIENT_CASHFLOW = os.environ.get('MAIL_RECIPIENT_CASHFLOW')
mail = Mail(app)

@app.route('/cashier')
def homeCashier():
    return render_template('cashflow.homeCashier.html', page='homeCashier', active_page='homeCashier')

@app.route('/operations', methods=['GET', 'POST'])
def operations():
    operations = get_operations()
    stores = get_cashflowStores()
    concepts = get_concepts()
    creditConcepts = get_creditConcepts()
    debitConcepts = get_debitConcepts()
    beneficiaries = get_beneficiaries()

    current_date = datetime.now()
    current_year = current_date.strftime("%Y")
    # Variables para permitir editar el mes actual y el anterior
    #current_yearMonth = current_date.strftime("%Y-%m")
    #previous_month_date = current_date - timedelta(days=current_date.day)
    #previous_yearMonth = previous_month_date.strftime("%Y-%m")
    processedOperations = []
    for operation in operations:
        operation_date = operation[1]
        operation_yearMonth = operation_date.strftime("%Y")
        #operation_yearMonth = operation_date.strftime("%Y-%m")
        processedOperations.append(operation + (operation_yearMonth,))

    if request.method == 'POST':

        # Inserción
        date_operation = request.form['date_operation']
        concept_id = request.form['concept']
        store_id = request.form['store']
        beneficiary_id = request.form['beneficiary']
        observation = request.form['observation']
        amount = float(request.form['amount'])
        operation_id = set_operations(store_id, beneficiary_id, concept_id, observation, date_operation, amount, request.form.get('operation_id'))

        # Email
        store_name = request.form.get('store_name')
        concept_name = request.form.get('concept_name')
        beneficiary_name = request.form.get('beneficiary_name')
        motion_type = request.form['motionType']

        # Crear el contenido HTML
        html_content = f"""
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
                        }}

                        .header {{
                            display: flex;
                            align-items: center;
                            margin-bottom: 20px;
                            position: relative;
                        }}
                        
                        .logo-left {{
                            margin-right: 20px;
                            height: 60px;
                            display: flex;
                            align-items: center;
                        }}
                        
                        .logo-left img {{
                            height: 100%;
                            width: auto;
                            max-height: 60px;
                        }}
                        
                        .header h2 {{
                            position: absolute;
                            left: 50%; /* Centrado horizontal */
                            transform: translateX(-50%);
                            margin: 0;
                            width: 100%;
                            text-align: center;
                            line-height: 60px;
                            pointer-events: none;
                        }}

                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 0;
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
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="logo-left">
                            <img src="cid:Gipsy_isotipo_color.png" alt="Logo Cobranza">
                        </div>
                        <h2>Reporte de Operación Gipsy Corp</h2>
                    </div>
                    <table border="1" cellpadding="5" cellspacing="0">
                        <tr>
                            <th>ID</th>
                            <th>Movimiento</th>
                            <th>Fecha</th>
                            <th>Compañía</th>
                            <th>Concepto</th>
                            <th>Beneficiario</th>
                            <th>Observación</th>
                            <th>Monto</th>
                        </tr>
                        <tr>
                            <td>{operation_id}</td>
                            <td>{"Ingreso" if motion_type == "1" else "Egreso"}</td>
                            <td>{date_operation}</td>
                            <td>{store_name}</td>
                            <td>{concept_name}</td>
                            <td>{beneficiary_name}</td>
                            <td>{observation}</td>
                            <td>{amount:.2f}</td>
                        </tr>
                    </table>
                    <p style="color: #666; font-style: italic;">
                        Flujo de Caja GIPSY<br>
                        Avenida Francisco de Miranda, Centro Lido, Torre A, Piso 9, Oficina 93<br>
                        Zona industrial Guayaba, Av. Pual. Guayabal, galpón 45, Guarenas<br>
                        One Turnberry Place, 19495 Biscayne Blvd. #609 Aventura FL 33180 United States of America
                    </p>
                </body>
                </html>
                """

        subject = f'Operación {operation_id}: {"Ingreso" if motion_type == "1" else "Egreso"} Agregado'

        if store_id == '4':
            app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_CASHFLOW_REMBD')
        else: 
            app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_CASHFLOW')

        msg = Message(subject=subject,
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[app.config['MAIL_USERNAME']])
        
        msg.html = html_content

        with app.open_resource('static/IMG/Gipsy_isotipo_color.png') as logo:
            msg.attach(
                filename='Gipsy_isotipo_color.png',
                content_type='image/png',
                data=logo.read(),
                disposition='inline',
                headers={'Content-ID': '<Gipsy_isotipo_color.png>'}
            )

        try:
            mail.send(msg)
            print("Correo enviado exitosamente.")
        except Exception as e:
            print(f"Error al enviar correo: {e}")
        
        return redirect(url_for('operations'))


    return render_template(
        'cashflow.operations.html',
        page='operations',
        active_page='operations',
        operations=processedOperations,
        concepts=concepts,
        creditConcepts=creditConcepts,
        debitConcepts=debitConcepts,
        stores=stores,
        beneficiaries=beneficiaries,
        current_year=current_year
        #current_yearMonth=current_yearMonth,
        #previous_yearMonth=previous_yearMonth
    )

@app.route('/beneficiaries', methods=['GET', 'POST'])
def beneficiaries():
    beneficiaries = get_beneficiaries()
    last_id = get_last_beneficiary_id()
    if request.method == 'POST':
        data = request.get_json()  # Obtener datos JSON
        set_beneficiaries(data)
        return jsonify(success=True)
    return render_template('cashflow.beneficiaries.html', page='beneficiaries', active_page='beneficiaries', beneficiaries=beneficiaries, last_id=last_id)
    
@app.route('/stores', methods=['GET', 'POST'])
def stores():
    stores = get_cashflowStores()
    last_id = get_last_store_id()
    if request.method == 'POST':
        data = request.get_json()
        set_stores(data)
        return jsonify(success=True)
    return render_template('cashflow.stores.html', page='stores', active_page='stores', stores=stores, last_id=last_id)

@app.route('/concepts', methods=['GET', 'POST'])
def concepts():
    concepts = get_concepts()
    last_id = get_last_concept_id()
    if request.method == 'POST':
        data = request.get_json()
        for concept in data:
            type_motion = concept.get('motion')
            motion_id = get_motion_id(type_motion)
            concept['motion'] = motion_id
        set_concepts(data)
        return jsonify(success=True)
    return render_template('cashflow.concepts.html', page='concepts', active_page='concepts', concepts=concepts, last_id=last_id)
   

# RECIBO DE VENDEDORES - RUTAS

# Configuración de correo SMTP para Recibo
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
MAIL_RECIPIENT_RECEIPT = os.environ.get('MAIL_RECIPIENT_CASHFLOW')
mail = Mail(app)

@app.route('/receiptAdmin')
def homeAdmin():
    return render_template('receipt.homeAdmin.html', page='homeAdmin', active_page='homeAdmin')

@app.route('/sellers')
def sellers():
    stores = get_receiptStores_Sellers()
    sellers_by_store = {store[0]: get_sellers(store[0]) for store in stores}
    count_sellers_by_store = {store[0]: get_count_sellers(store[0]) for store in stores}
    return render_template('receipt.sellers.html',
                           page='sellers',
                           active_page='sellers',
                           stores=stores,
                           sellers_by_store=sellers_by_store,
                           count_sellers_by_store=count_sellers_by_store)

@app.route('/sellerDetails/<int:seller_id>')
def sellerDetails(seller_id):
    seller = get_seller_details(seller_id)
    if seller:
        store = get_receiptStore_by_id(seller[5])
        return render_template('receipt.sellerDetails.html', page='sellerDetails', active_page='sellers', seller=seller, store=store)
    else:
        return "Vendedor no encontrado", 404

@app.route('/receipts')
def receipts():
    stores = get_receiptStores_Receipts()
    customers_with_unvalidated_receipts = {store[0]: get_customers_with_unvalidated_receipts(store[0]) for store in stores}
    customer_counts = {store[0]: get_count_customers_with_unvalidated_receipts(store[0]) for store in stores}
    return render_template(
        'receipt.receipts.html', 
        page='receipts', active_page='receipts', 
        stores=stores, 
        customers_with_unvalidated_receipts=customers_with_unvalidated_receipts, 
        customer_counts=customer_counts)

@app.route('/receiptDetails/<int:customer_id>/<int:store_id>/<int:pagination>')
def receiptDetails(customer_id, store_id, pagination=1):
    receipts_per_page = 1
    receipts = get_unvalidated_receipts_by_customer(customer_id)
    store = get_receiptStore_by_id(store_id)
    customer = get_customer_by_id(customer_id)

    # Paginación
    total_receipts = len(receipts)
    start = (pagination - 1) * receipts_per_page
    end = start + receipts_per_page
    paginated_receipts = receipts[start:end]

    # Obtención de receipt_id, facturas y formas de pago por página
    receipt_id = paginated_receipts[0][0]
    invoices = get_invoices_by_receipt(receipt_id)
    paymentEntries = get_paymentEntries_by_receipt(receipt_id)
    salesRepComm = get_SalesRepCommission(receipt_id)

    # Obtención de comprobantes de pago desde OneDrive, actualización de paymentEntries
    paymentEntries = get_onedriveProofsOfPayments(paymentEntries)

    return render_template('receipt.receiptDetails.html', 
                           page='receiptDetails', 
                           active_page='receipts', 
                           customer_id=customer_id,
                           store_id=store_id,
                           receipts=receipts,
                           store=store,
                           customer=customer,
                           invoices=invoices,
                           paymentEntries=paymentEntries,
                           salesRepComm = salesRepComm,
                           pagination=pagination,
                           total_receipts=total_receipts,
                           receipts_per_page=receipts_per_page)


@app.route('/businessRules', methods=['GET', 'POST'])
def businessRules():
    rules = get_commissionsRules()
    if request.method == 'POST':
        data = request.get_json()
        set_commissionsRules(data)
        return jsonify(success=True)
    return render_template('receipt.businessRules.html', page='businessRules', active_page='businessRules', rules=rules)

@app.route('/receiptSeller')
def homeSeller():
    return render_template('receipt.homeSeller.html', page='homeSeller', active_page='homeSeller')

@app.route('/accountsReceivable')
def accountsReceivable():
    stores = get_receiptStores_DebtAccount()
    customers_by_store = {store[0]: get_customers(store[0]) for store in stores}
    count_customers_by_store = {store[0]: get_count_customers_with_accountsReceivable(store[0]) for store in stores}
    return render_template('receipt.accountsReceivable.html',
                           page='accountsReceivable',
                           active_page='accountsReceivable',
                           stores=stores,
                           customers_by_store=customers_by_store,
                           count_customers_by_store=count_customers_by_store)

@app.route('/get_invoices/<customer_id>/<store_id>')
def get_invoices(customer_id, store_id):
    invoices = get_invoices_by_customer(customer_id, store_id)
    # Formatear datos para JSON
    formatted_invoices = [
        {
            'AccountID': invoice[0],
            'N_CTA': invoice[1],
            'Amount': float(invoice[2]),
            'Balance': float(invoice[3]),
            'IVA': 0,
            'Remaining': float(invoice[2] - invoice[3]),
            'Currency': invoice[4]
        } for invoice in invoices
    ]
    return jsonify({'invoices': formatted_invoices})

@app.route('/accountsForm/<string:account_ids>')
def accountsForm(account_ids):
    account_ids_list = account_ids.split('-')
    receiptStoreCustomer = get_receiptsStoreCustomer(account_ids_list)
    currencies = get_currency()
    receiptsInfo = get_receiptsInfo(account_ids_list)
    bankAccounts = []
    commissions = get_commissions()
    return render_template(
        'receipt.accountsForm.html',
        page='accountsForm',
        active_page='accountsReceivable',
        receiptStoreCustomer=receiptStoreCustomer,
        receiptDetails=receiptsInfo,
        bankAccounts=bankAccounts,
        commissions=commissions,
        currencies=currencies
    )

# Obtención de formas de pago según moneda
@app.route('/get_tenders/<int:currency_id>')
def get_tenders(currency_id):
    tenders = get_tender(currency_id)
    return jsonify([{'id': t[0], 'description': t[1]} for t in tenders])

# Obtención de cuentas bancarias
@app.route('/get_bankAccounts', methods=['POST'])
def get_bank_accounts():
    store_id = request.json['store_id']
    currency_id = request.json['currency_id']
    tender_id = request.json['tender_id']
    bank_accounts = get_bankAccounts(store_id, currency_id, tender_id)
    return jsonify(bank_accounts)


@app.route('/submit_receipt', methods=['POST'])
def submit_receipt():
    #Conexión a la BD. Ejecución como una única transacción
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # Obtención de datos del formulario
        balance_note = float(request.form['balance_note'])
        commission_note = float(request.form['commission_note'])

        # Inserción de Recibo en BD
        receipt_id = set_paymentReceipt(cursor, balance_note, commission_note)

        payment_entries = request.form.getlist('payment_entries[]')
        payment_entries = [json.loads(entry) for entry in payment_entries] 
        proof_of_payments = request.files.getlist('proof_of_payment[]')

        # Importes adeudados de cada factura
        balance_calculations = []
        index = 0
        while f'balance_calculation_{index}' in request.form:
                balance_calculations.append(float(request.form[f'balance_calculation_{index}']))
                index += 1

        account_ids = [entry['account_id'] for entry in payment_entries if entry.get('account_id')]

        for index, entry in enumerate(payment_entries):
            payment_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
            amount = float(entry['amount'])
            discount = float(entry['discount'])
            reference = entry['reference']
            payment_destination_id = entry['payment_destination_id']

            # Obtención de balance, comisión y días
            account_id = account_ids[index]
            balance_amount = entry['balance_amount']
            commission_amount = entry['commission_amount']
            days_passed = entry['days_passed']
            tender_id = entry['tender_id']

            if proof_of_payments and index < len(proof_of_payments):
                file_path = save_proofOfPayment([proof_of_payments[index]], receipt_id, payment_date, index)
                file_path = file_path[0] if file_path else ""  # Toma el primer elemento o cadena vacía
            else:
                file_path = "" 

            set_paymentEntry(cursor, receipt_id, payment_date, amount, discount, reference, payment_destination_id, tender_id, file_path)

            # Obtención de SalesRepID e isRetail
            debt_account = get_salesRep_isRetail(account_id)
            sales_rep_id = debt_account[0]
            is_retail = debt_account[1]
            # Inserción en SalesRepCommission
            set_SalesRepCommission(cursor, sales_rep_id, account_id, is_retail, balance_amount, days_passed, commission_amount, receipt_id)

        # Actualización de Monto Abonado
        amount_paid_list = request.form.getlist('amount_paid[]')
        original_amounts = request.form.getlist('original_amount[]')
        for index in range(len(original_amounts)):
            account_id = account_ids[index]
            amount_paid = float(amount_paid_list[index])
            set_invoicePaidAmount(cursor, account_id, amount_paid)
            # Inserción de la Relación Receipt-DebtAccount
            set_DebtPaymentRelation(cursor, account_id, receipt_id)
            
        # Confirmación la transacción
        conn.commit()
        return redirect(url_for('accountsReceivable'))
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return "Error al procesar la solicitud", 500
    
    finally:
        cursor.close()
        conn.close()


# Rechazo de Recibo de Pago
@app.route('/send_rejectionReceipt_email', methods=['POST'])
def send_rejectionEmail():

    receipt_id = int(request.form.get('receipt_id', ''))
    set_isReviewedReceipt(receipt_id)

    rejection_reason = request.form.get('rejection_reason', '')
    rejection_reason_html = "<br>".join(line.strip() for line in rejection_reason.split('\n') if line.strip())
    store_id = request.form.get('store_id', '')
    store_name = request.form.get('store_name', '')
    customer = request.form.get('customer', '')
    currency = request.form.get('currency', '')
    totalPaid = request.form.get('total_paid', '')
    totalCommission = request.form.get('total_commission', '')

    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')

    msg = Message(subject='Rechazo de Recibo de Cobranza',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[MAIL_RECIPIENT_RECEIPT])

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>El recibo de cobranza con los siguientes datos:</p>

            <ul style="list-style-type: disc; margin-left: 5px; padding-left: 5px;">
                <li><strong>Empresa:</strong> {store_name}</li>
                <li><strong>Cliente:</strong> {customer}</li>
                <li><strong>Moneda:</strong> {currency}</li>
                <li><strong>Monto total:</strong> {totalPaid} {currency}</li>
                <li><strong>Comisión a recibir:</strong> {totalCommission} {currency}</li>
            </ul>          
            
            <p>ha sido rechazado por el siguiente motivo:</p>
            
            <blockquote style="border-left: 5px solid #ccc; margin: 1.5em 0; padding: 0.5em 1em;">
                {rejection_reason_html}
            </blockquote>
            
            <p>Se solicita verificar y volver a realizar el registro de la cobranza.</p>
            
            <p>Atentamente,</p>
            
            <p style="color: #666; font-style: italic;">
                GIPSY<br>
                Avenida Francisco de Miranda, Centro Lido, Torre A, Piso 9, Oficina 93<br>
                Zona industrial Guayaba, Av. Pual. Guayabal, galpón 45, Guarenas<br>
                One Turnberry Place, 19495 Biscayne Blvd. #609 Aventura FL 33180 United States of America
            </p>
            
            <img src="cid:Gipsy_imagotipo_color.png" alt="Gipsy Logo" style="max-width: 200px;">
        </body>
    </html>
    """
    msg.html = html_body
    
    with app.open_resource('static/IMG/Gipsy_imagotipo_color.png') as logo:
        msg.attach(
            filename='Gipsy_imagotipo_color.png',
            content_type='image/png',
            data=logo.read(),
            disposition='inline',
            headers={'Content-ID': '<Gipsy_imagotipo_color.png>'}
        )

    mail.send(msg)

    return jsonify({'success': True})


@app.route('/send_validateReceipt_email', methods=['POST'])
def send_validationEmail():

    # Datos iniciales para la interfaz
    store_id = request.form.get('store_id', '')
    customer_id = request.form.get('customer_id', '')
    pagination = int(request.form.get('pagination', ''))
    receipt_id = int(request.form.get('receipt_id', ''))

    receipts_per_page = 1
    receipts = get_unvalidated_receipts_by_customer(customer_id)
    store = get_receiptStore_by_id(store_id)
    customer = get_customer_by_id(customer_id)
    store_name = store[1] if store else ''
    customer_name = f"{customer[1]} {customer[2]}" if customer else ''
    total_receipts = len(receipts)
    invoices = get_invoices_by_receipt(receipt_id)
    paymentEntries = get_paymentEntries_by_receipt(receipt_id)
    paymentEntries = get_onedriveProofsOfPayments(paymentEntries)
    salesRepComm = get_SalesRepCommission(receipt_id)

    # Validación de Recibo de Pago
    """
    OJO: El JS primero llama a la función de enviar el correo y luego la del PDF.
    Si se valida el recibo aquí, al renderizar la interfaz para el PDF, no tendrá acceso a los campos.
    Al implementar el pdf en producción, realizar la validación luego de este último renderizado.
    """
    set_isReviewedReceipt(receipt_id)
    set_isApprovedReceipt(receipt_id)
    
    # Logo Store (dinámico desde store[2])
    logo_store_path = store[2] if store and len(store) > 2 else None
    logo_store_cid = 'logo_store' if logo_store_path else None 

    # Renderizar el HTML
    html_content = render_template('receipt.receiptDetails.html',
                                 is_pdf=True,   # Tomar sólo la info destinada al pdf
                                 page='receiptDetails',
                                 active_page='receipts',
                                 customer_id=customer_id,
                                 store_id=store_id,
                                 receipts=receipts,
                                 store=store,
                                 customer=customer,
                                 invoices=invoices,
                                 paymentEntries=paymentEntries,
                                 salesRepComm=salesRepComm,
                                 pagination=pagination,
                                 total_receipts=total_receipts,
                                 receipts_per_page=receipts_per_page)
    
    html_body = f"""
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
                    }}

                    .header {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid black;
                        padding-bottom: 10px;
                        position: relative;
                    }}

                    .header img {{
                        max-height: 80px;
                        filter: grayscale(100%);
                    }}

                    .logo-left {{
                        position: absolute;
                        left: 0;
                    }}

                    .logo-right {{
                        position: absolute;
                        right: 0;
                    }}

                    .logo-right img {{
                        max-height: 100px;
                        filter: grayscale(100%);
                    }}

                    .header-text {{
                        text-align: center;
                        margin: 0 auto;
                        max-width: 60%;
                    }}

                    .header-text h1, h3 {{
                        font-size: 14px !important;
                        margin: 0;
                        color: black !important;
                    }}

                    .header-text p {{
                        margin: 5px 0;
                        color: black !important;
                    }}

                    .title-container, .button-container, .back {{
                        display: none;
                    }}

                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 0;
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

                    img {{
                        max-width: 100%;
                        height: auto;
                        filter: grayscale(100%);
                    }}

                    .client-info, .styled-table, .inline-label, .file-upload-container {{
                        color: black !important;
                    }}

                    .styled-table th {{
                        background-color: #f0f0f0 !important;
                        color: black !important;
                    }}

                    .styled-table td {{
                        color: black !important;
                    }}

                    .file-upload-container {{
                        margin: 20px 0;
                    }}

                    .file-upload-container img {{
                        max-width: 500px;
                        height: auto;
                        display: block;
                    }}

                    .paymentImage {{
                        width: 500px !important;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="logo-left">
                        <img src="cid:Gipsy_isotipo_color.png" alt="Logo Cobranza">
                    </div>
                    <div class="header-text">
                        <h1>Reporte de Cobranza Gipsy Corp</h1>
                        <p><strong>{store_name}</strong></p>
                        <p><strong>{customer_name}</strong></p>
                    </div>
                    <div class="logo-right">
                        {f'<img src="cid:logo_store" alt="Logo Store">' if logo_store_path else ''}
                    </div>
                </div>
                {html_content}
                <br>
                <p>Se anexan los comprobantes de pago del recibo.</p>
                <p>Atentamente,</p>
                <p style="color: #666; font-style: italic;">
                    GIPSY<br>
                    Avenida Francisco de Miranda, Centro Lido, Torre A, Piso 9, Oficina 93<br>
                    Zona industrial Guayaba, Av. Pual. Guayabal, galpón 45, Guarenas<br>
                    One Turnberry Place, 19495 Biscayne Blvd. #609 Aventura FL 33180 United States of America
                </p>
            </body>
            </html>
            """
    
    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')

    # Lógica para enviar el correo
    msg = Message(subject='Validación de Recibo de Cobranza',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[MAIL_RECIPIENT_RECEIPT])
    
    msg.html = html_body

    # Adjuntar logo Gipsy (fijo)
    with app.open_resource('static/IMG/Gipsy_isotipo_color.png') as logo:
        msg.attach(
            filename='Gipsy_isotipo_color.png',
            content_type='image/png',
            data=logo.read(),
            disposition='inline',
            headers={'Content-ID': '<Gipsy_isotipo_color.png>'}
        )

    # Adjuntar logo Store (dinámico desde OneDrive)
    if logo_store_path:
        logo_content = get_onedriveStoreLogo(logo_store_path)
        
        if logo_content:
            # Determinar el tipo MIME basado en la extensión del archivo
            if logo_store_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif logo_store_path.lower().endswith('.jpg') or logo_store_path.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'application/octet-stream'  # Tipo genérico si no se reconoce
                
            msg.attach(
                filename=logo_store_path,
                content_type=mime_type,
                data=logo_content,
                disposition='inline',
                headers={'Content-ID': '<logo_store>'}
            )
        else:
            print(f"No se pudo obtener el logo {logo_store_path} desde OneDrive")

    # Adjuntar comprobantes de pago (dinámico desde OneDrive)
    headers = get_onedrive_headers()
    for paymentEntry in paymentEntries:
        file_info = paymentEntry[7]
        if file_info:
            file_url = file_info.get('url', '')
            filename = file_info.get('name', '')
            mime_type = "application/pdf" if filename.lower().endswith('.pdf') else "image/jpeg"

            try:
                response = requests.get(file_url, headers=headers)
                if response.status_code == 200:
                    file_content = response.content
                    
                    msg.attach(filename, mime_type, file_content)
                else:
                    print(f"Error al descargar el archivo desde OneDrive: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Excepción al intentar descargar el archivo: {e}")

    # Envío del correo
    try:
        mail.send(msg)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return jsonify({'success': False, 'error': str(e)})
    

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Datos iniciales para la interfaz
    store_id = request.form.get('store_id', '')
    customer_id = request.form.get('customer_id', '')
    pagination = int(request.form.get('pagination', ''))
    receipt_id = int(request.form.get('receipt_id', ''))

    receipts_per_page = 1
    receipts = get_unvalidated_receipts_by_customer(customer_id)
    store = get_receiptStore_by_id(store_id)
    customer = get_customer_by_id(customer_id)
    store_name = store[1] if store else ''
    customer_name = f"{customer[1]} {customer[2]}" if customer else ''
    total_receipts = len(receipts)
    invoices = get_invoices_by_receipt(receipt_id)
    paymentEntries = get_paymentEntries_by_receipt(receipt_id)
    paymentEntries = get_onedriveProofsOfPayments(paymentEntries)
    salesRepComm = get_SalesRepCommission(receipt_id)
    
    # Logo Store (dinámico desde store[2])
    logo_store_path = store[2] if store and len(store) > 2 else None
    logo_content = get_onedriveStoreLogo(logo_store_path)
    logo_store_64 = base64.b64encode(logo_content).decode('utf-8')
    logo_right_img = f'<img src="data:image/png;base64,{logo_store_64}" alt="Logo Store" />' if logo_store_64 else ''

    # Logo Gipsy (fijo)
    logo_gipsy_path = current_app.static_folder + f'/IMG/Gipsy_isotipo_color.png'
    with open(logo_gipsy_path, "rb") as image_file:
        logo_gipsy_64 = base64.b64encode(image_file.read()).decode('utf-8')
    logo_left_img = f'<img src="data:image/png;base64,{logo_gipsy_64}" alt="Logo Gipsy">' if logo_gipsy_64 else ''

    # Validación de Recibo de Pago
    set_isReviewedReceipt(receipt_id)
    set_isApprovedReceipt(receipt_id)

    # Renderización del HTML
    html_content = render_template('receipt.receiptDetails.html',
                                 is_pdf=True,
                                 page='receiptDetails',
                                 active_page='receipts',
                                 customer_id=customer_id,
                                 store_id=store_id,
                                 receipts=receipts,
                                 store=store,
                                 customer=customer,
                                 invoices=invoices,
                                 paymentEntries=paymentEntries,
                                 salesRepComm=salesRepComm,
                                 pagination=pagination,
                                 total_receipts=total_receipts,
                                 receipts_per_page=receipts_per_page)
    
    html_body = f"""
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
                    }}

                    .header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid black;
                        padding-bottom: 10px;
                    }}

                    .logo-left, .logo-right {{
                        flex: 1;
                        display: flex;
                        justify-content: center;
                    }}

                    .header img {{
                        max-height: 60px;
                        filter: grayscale(100%);
                    }}

                    .header-text {{
                        flex: 2;
                        text-align: center;
                        margin: 0;
                    }}

                    .header-text h1, h3 {{
                        font-size: 14px !important;
                        margin: 0;
                        color: black !important;
                    }}

                    .header-text p {{
                        color: black !important;
                        font-size: 14px !important;
                    }}

                    .title-container, .button-container, .back {{
                        display: none;
                    }}

                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 0;
                        font-size: 10px !important;
                    }}

                    table, th, td {{
                        border: 1px solid black !important;
                    }}

                    th, td {{
                        padding: 4px !important;
                        text-align: left;
                        color: black !important;
                    }}

                    th {{
                        background-color: #f0f0f0 !important;
                    }}

                    img {{
                        max-width: 100%;
                        height: auto;
                        filter: grayscale(100%);
                    }}

                    .client-info, .styled-table, .inline-label, .file-upload-container {{
                        color: black !important;
                    }}

                    .styled-table {{
                        font-size: 12px !important;
                    }}

                    .styled-table th {{
                        background-color: #f0f0f0 !important;
                        color: black !important;
                    }}

                    .styled-table td {{
                        color: black !important;
                    }}

                    .file-upload-container {{
                        margin: 20px 0;
                    }}

                    .file-upload-container img {{
                        max-width: 500px;
                        height: auto;
                        display: block;
                    }}

                    .paymentImage {{
                        width: 500px !important;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="logo-left">
                        {logo_left_img}
                    </div>
                    <div class="header-text">
                        <h1>Reporte de Cobranza Gipsy Corp</h1>
                        <p><strong>{store_name}</strong></p>
                        <p><strong>{customer_name}</strong></p>
                    </div>
                    <div class="logo-right">
                        {logo_right_img}
                    </div>
                </div>
                {html_content}
            </body>
            </html>
            """

    # Generar el PDF
    pdf_bytes = HTML(string=html_body).write_pdf()

    # Crear respuesta
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f'Cobranza_{receipt_id}_{store_id}_{customer_id}.pdf'
    safe_filename = secure_filename(filename)
    response.headers['Content-Disposition'] = f'inline; filename="{safe_filename}"'
    return response



if __name__ == '__main__':
   app.run()
