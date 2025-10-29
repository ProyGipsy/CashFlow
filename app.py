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
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response, current_app, session)
from flask_session import Session
from flask_mail import Mail, Message
from reports import reports_bp


from cashflow_db import (get_beneficiaries, get_cashflowStores, get_concepts, get_creditConcepts, get_debitConcepts,
    get_operations, get_last_beneficiary_id, get_last_concept_id, get_motion_id, get_last_store_id,
    set_beneficiaries, set_concepts, set_stores, set_operations, get_operations_count)

# OJO: Variables balance corresponden a PaidAmount
from receipt_db import (get_db_connection, get_receiptStores_DebtAccount, get_receiptStores_Receipts, get_receiptStores_Sellers,
    get_receiptStore_by_id, get_sellers, get_count_sellers, get_seller_details, get_customers, get_tender, get_commissionsRules,
    get_invoices_by_customer, get_receiptsInfo, get_receiptsStoreCustomer, get_bankAccounts, get_commissions, get_customer_by_id,
    get_customers_with_unvalidated_receipts, get_count_customers_with_unvalidated_receipts, get_unvalidated_receipts_by_customer,
    get_invoices_by_receipt, get_paymentEntries_by_receipt, get_salesRep_isRetail, set_SalesRepCommission, get_SalesRepCommission,
    set_commissionsRules, set_paymentReceipt, set_paymentEntry, save_proofOfPayment, set_invoicePaidAmount, set_DebtPaymentRelation,
    set_isReviewedReceipt, set_isApprovedReceipt, get_onedriveProofsOfPayments, get_onedriveStoreLogo, get_count_customers_with_accountsReceivable,
    get_currency, get_paymentRelations_by_receipt, get_invoiceCurrentPaidAmount, revert_invoicePaidAmount, get_customers_admin,
    get_count_customers_with_accountsReceivable_admin, get_receiptStores_DebtAccount_admin, get_invoices_by_customer_admin, 
    set_paymentEntryCommission, get_SalesRepCommission_OLD, check_already_paid_invoices, check_duplicate_receipt)
    


from accessControl import (get_user_data, get_roleInfo, get_userEmail, get_salesRepNameAndEmail)

from onedrive import get_onedrive_headers

app = Flask(__name__)
app.register_blueprint(reports_bp)

# Configuración de sesión para usuarios
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración del servidor SMTP
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('newIndex.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('User')
        password = request.form.get('Password')

        user_data = get_user_data(username, password)

        if user_data:

            # Creación de la sesión
            session.update({
                'user_id': user_data['user_id'],
                'logged_in': True,
                'salesRep_id': user_data['salesRep_id'],
                'user_firstName': user_data['firstName'],
                'user_lastName': user_data['lastName'],
                'roles': user_data['roles_id'],
                'modules': user_data['modules_id'],
                'permissions': user_data['permissions_id']
            })

            return redirect(url_for('welcome'))
        else: 
            return render_template('indexLogin.html', error="Credenciales incorrectas, por favor intente de nuevo.")
   
    return render_template('indexLogin.html')

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    roles_info = []
    seen_roles = set() 

    for role in session.get('roles', []):
        if role not in seen_roles:
            seen_roles.add(role)
            role_name = get_roleInfo(role)
            if role_name:
                roles_info.append({
                    'id': role,
                    'name': role_name
                })

    return render_template('welcome.html', roles_info=roles_info)


# INICIOS DE SESIÓN INDIVIDUALES (Descartados con el nuevo flujo)

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

@app.route('/cashier')
def homeCashier():
    return render_template('cashflow.homeCashier.html', page='homeCashier', active_page='homeCashier')

@app.route('/operations', methods=['GET', 'POST'])
def operations():

    # Obtención del número de página
    try:
        pagination = int(request.args.get('pagination', 1))
    except Exception:
        pagination = 1

    results_per_page = 500

    #operations = get_operations()
    operations = get_operations(page=pagination, page_size=results_per_page)
    total_operations = get_operations_count()
    total_pages = (total_operations // results_per_page) + (1 if total_operations % results_per_page > 0 else 0)

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

                        .signature-section {{
                            margin-top: 60px;
                            width: 100%;
                            font-size: 14px;
                            line-height: 2;
                        }}

                        .signature-item {{
                            display: block;
                            margin-bottom: 25px;
                            width: 100%;
                        }}

                        .signature-line {{
                            display: inline-block;
                            border-bottom: 1px solid #000000;
                            width: 30%;
                            margin-left: 10px;
                            padding-bottom: 3px;
                            vertical-align: middle;
                        }}
                    </style>
                </head>
                <body>
                    <br>
                    <div class="header">
                        <h2>{"Comprobante de Entrada" if motion_type == "1" else "Comprobante de Salida"}</h2>
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
                    <div class="signature-section">
                        <div class="signature-item">
                            Recibido por: <span class="signature-line">&nbsp;</span>
                        </div>
                        <div class="signature-item">
                            C.I. del receptor: <span class="signature-line">&nbsp;</span>
                        </div>
                        <div class="signature-item">
                            Fecha: <span class="signature-line">&nbsp;</span>
                        </div>
                        <div class="signature-item">
                            Firma: <span class="signature-line">&nbsp;</span>
                        </div>
                    </div>
                </body>
                </html>
                """

        subject = f'Operación {operation_id}: {"Ingreso" if motion_type == "1" else "Egreso"} Agregado'

        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')   
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_CASHFLOW')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_CASHFLOW')
        if store_id == '4':
            recipient_cashflow = os.environ.get('MAIL_RECIPIENT_CASHFLOW_REMBD')
        else:
            recipient_cashflow = os.environ.get('MAIL_RECIPIENT_CASHFLOW_GIPSYCORP')
        mail = Mail(app)

        msg = Message(subject=subject,
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[recipient_cashflow])
        
        msg.html = html_content

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
        current_year=current_year,
        pagination=pagination,
        results_per_page=results_per_page,
        total_operations=total_operations,
        total_pages=total_pages
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
   

# RECIBO DE COBRANZA AL MAYOR - RUTAS

# Configuración de correo SMTP para Recibo
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
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

@app.route('/receiptDetails/<int:customer_id>/<int:customer_isRembd>/<int:store_id>/<int:pagination>')
def receiptDetails(customer_id, customer_isRembd, store_id, pagination=1):
    receipts_per_page = 1
    receipts = get_unvalidated_receipts_by_customer(customer_id, customer_isRembd)
    store = get_receiptStore_by_id(store_id)
    customer = get_customer_by_id(customer_id, customer_isRembd)

    # Paginación
    total_receipts = len(receipts)
    start = (pagination - 1) * receipts_per_page
    end = start + receipts_per_page
    paginated_receipts = receipts[start:end]

    # Obtención de receipt_id, facturas y formas de pago por página
    receipt_id = paginated_receipts[0][0]
    invoices = get_invoices_by_receipt(receipt_id)
    salesRep_id = invoices[0][7]
    salesRep_NameEmail = get_salesRepNameAndEmail(salesRep_id)
    paymentEntries = get_paymentEntries_by_receipt(receipt_id)

    # Cambio en la app, agregando tabla PaymentEntryCommission
    if receipt_id <= 250:
        salesRepComm = get_SalesRepCommission_OLD(receipt_id)
    else:
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
                           salesRep_NameEmail=salesRep_NameEmail,
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
    if (session['salesRep_id'] == '99' or session['user_id'] == 20):
        stores = get_receiptStores_DebtAccount_admin()
        customers_by_store = {store[0]: get_customers_admin(store[0]) for store in stores}
        count_customers_by_store = {store[0]: get_count_customers_with_accountsReceivable_admin(store[0]) for store in stores}
    else:
        stores = get_receiptStores_DebtAccount(session['salesRep_id'])
        customers_by_store = {store[0]: get_customers(store[0], session['salesRep_id']) for store in stores}
        count_customers_by_store = {store[0]: get_count_customers_with_accountsReceivable(store[0], session['salesRep_id']) for store in stores}
    return render_template('receipt.accountsReceivable.html',
                           page='accountsReceivable',
                           active_page='accountsReceivable',
                           stores=stores,
                           customers_by_store=customers_by_store,
                           count_customers_by_store=count_customers_by_store)

@app.route('/get_invoices/<customer_id>/<customer_isRembd>/<store_id>')
def get_invoices(customer_id, customer_isRembd, store_id):
    if (session['salesRep_id'] == '99' or session['user_id'] == 20):
        invoices = get_invoices_by_customer_admin(customer_id, customer_isRembd, store_id)
    else: 
        invoices = get_invoices_by_customer(customer_id, customer_isRembd, store_id, session['salesRep_id'])
    # Formatear datos para JSON
    formatted_invoices = [
        {
            'AccountID': invoice[0],
            'N_CTA': invoice[1],
            'Amount': float(invoice[2]),
            'Balance': float(invoice[3]),
            'IVA': 0,
            'Remaining': float(invoice[2] - invoice[3]),
            'Currency': invoice[4],
            'DocumentType': invoice[5]
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
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obtener TODOS los account_ids de las facturas (no solo los de payment_entries)
        all_account_ids = json.loads(request.form.get('all_account_ids', '[]'))

        # Verificación de facturas
        already_paid_invoices = check_already_paid_invoices(cursor, all_account_ids)
        if already_paid_invoices:
            print("Algunas facturas ya han sido pagadas:", already_paid_invoices)
            return jsonify({
                'error': 'Algunas facturas ya han sido pagadas. No se pueden registrar cobranzas duplicadas.',
                'paid_invoices': already_paid_invoices
            }), 400

        # Obtención de datos del formulario
        balance_note = float(request.form['balance_note'])
        commission_total_per_currency_json = request.form.get('commission_total_per_currency', '{}')
        commission_total_per_currency = json.loads(commission_total_per_currency_json)
        comision_bs = commission_total_per_currency.get('Bs', 0)
        comision_usd = commission_total_per_currency.get('USD', 0)

        # Leer datos necesarios para validación de duplicados (antes de insertar)
        commission_data = json.loads(request.form.get('commission_data', '[]'))
        payment_entries_raw = request.form.getlist('payment_entries[]')
        payment_entries = [json.loads(entry) for entry in payment_entries_raw]
        proof_of_payments = request.files.getlist('proof_of_payment[]')

        # Obtención de los detalles de las formas de pago (relacionando facturas)
        payment_invoice_details = json.loads(request.form.get('payment_invoice_details', '[]'))
        original_amounts = request.form.getlist('original_amount[]')
        invoice_paid_amounts = request.form.getlist('invoice_paid_amounts[]')

        # Verificación de duplicados: mismas facturas + mismos montos + mismas entradas de pago (monto, fecha, referencia)
        duplicate_receipt_id = check_duplicate_receipt(cursor, all_account_ids, invoice_paid_amounts, payment_entries)
        if duplicate_receipt_id:
            print(f"Recibo duplicado detectado: {duplicate_receipt_id}")
            return jsonify({
                'error': 'Recibo duplicado: ya existe un recibo con las mismas facturas, montos y entradas de pago.',
                'duplicate_receipt_id': duplicate_receipt_id
            }), 409

        # Inserción de Recibo en BD
        receipt_id = set_paymentReceipt(cursor, balance_note, comision_bs, comision_usd) # NUEVO, CAMBIO EN COMISIÓN

        # Procesar cada forma de pago
        payment_entry_ids = []

        for entry in payment_entries:
            payment_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
            amount = float(entry['amount'])
            discount = float(entry['discount'])
            reference = entry['reference']
            payment_destination_id = entry['payment_destination_id']
            tender_id = entry['tender_id']
            
            account_id = entry.get('account_id')

            if proof_of_payments:
                file_path = save_proofOfPayment([proof_of_payments[payment_entries.index(entry)]], receipt_id, payment_date, payment_entries.index(entry))
                file_path = file_path[0] if file_path else ""
            else:
                file_path = ""

            payment_entry_id = set_paymentEntry(cursor, receipt_id, payment_date, amount, discount, reference, payment_destination_id, tender_id, file_path)
            payment_entry_ids.append(payment_entry_id)
        
        for detail in payment_invoice_details:
            paymentReceiptEntry_id = payment_entry_ids[detail['paymentReceiptEntryIdx']]
            debtaccount_id = detail['debtAccountId']
            payment_date = detail['paymentDate']
            amount = detail['amount']
            days_elapsed = detail['daysElapsed']
            commission_id = detail['commissionId']
            commission_amount = detail['commissionAmount']
            commission_per_currency = detail['commission_per_currency']
            bs_commission = commission_per_currency.get('Bs', 0) if commission_per_currency else 0
            usd_commission = commission_per_currency.get('USD', 0) if commission_per_currency else 0
            set_paymentEntryCommission(cursor, receipt_id, paymentReceiptEntry_id, debtaccount_id, payment_date, amount, days_elapsed, commission_id, bs_commission, usd_commission) # CAMBIO EN COMISIÓN

        # Actualización de Monto Abonado
        original_amounts = request.form.getlist('original_amount[]')
        invoice_paid_amounts = request.form.getlist('invoice_paid_amounts[]')

        # Validación de consistencia
        if not (len(original_amounts) == len(invoice_paid_amounts) == len(all_account_ids)):
            raise ValueError("Inconsistencia en los datos recibidos")

        for index in range(len(all_account_ids)):
            account_id = all_account_ids[index]

            # Datos e inserción en SalesRepCommission
            debt_account = get_salesRep_isRetail(account_id)
            sales_rep_id = debt_account[0]
            is_retail = debt_account[1]
            commission_info = next((item for item in commission_data if item['account_id'] == account_id), None)
            balance_amount = float(commission_info['balance_amount'])
            days_passed = int(commission_info['days_passed'])
            commission_per_currency = commission_info['commission_per_currency']
            bs_commission = commission_per_currency.get('Bs', 0) if commission_per_currency else 0
            usd_commission = commission_per_currency.get('USD', 0) if commission_per_currency else 0
            set_SalesRepCommission(cursor, sales_rep_id, account_id, is_retail, balance_amount, days_passed, receipt_id, bs_commission, usd_commission)

            # Actualización de factura
            invoice_paidAmount = float(invoice_paid_amounts[index])
            # Anteriormente se realizaba el cálculo en Python
            #new_amount_paid = float(original_amounts[index]) - balance_amount
            # Ahora se realiza en el mismo query para evitar inconsistencias
            set_invoicePaidAmount(cursor, account_id, invoice_paidAmount)
            # Relación factura-recibo
            set_DebtPaymentRelation(cursor, account_id, receipt_id, invoice_paidAmount)

        # Confirmación la transacción
        conn.commit()

        # Obtención de N_CTAs (para especificar en el correo)
        invoices = get_invoices_by_receipt(receipt_id)
        ncta_list = [str(invoice[0]) for invoice in invoices]
        ncta_str = ", ".join(ncta_list)

        # Envío de correo electrónico de notificación
        store_id = request.form.get('store_id', '')
        store_name = request.form.get('store_name', '')
        customer_name = request.form.get('customer_name', '')
        currency = request.form.get('currency', '')
        send_receipt_adminNotification(receipt_id, store_id, store_name, customer_name, balance_note, comision_bs, comision_usd, currency, ncta_str)
        send_receipt_salesRepNotification(receipt_id, store_id, store_name, customer_name, balance_note, comision_bs, comision_usd, currency, ncta_str)
        

        return redirect(url_for('accountsReceivable'))
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return "Error al procesar la solicitud", 500
    
    finally:
        cursor.close()
        conn.close()

def send_receipt_adminNotification(receipt_id, store_id, store_name, customer_name, total_receipt_amount, commission_bs, commission_usd, currency, ncta_str):

    # Formateo del monto de comisión según la moneda
    if commission_bs > 0 and commission_usd > 0:
        # Caso 1: Ambos montos son mayores a 0
        commission_text = f"Bs {commission_bs:.2f} y USD {commission_usd:.2f}"
    elif commission_bs > 0:
        # Caso 2: Solo hay monto en Bs
        commission_text = f"Bs {commission_bs:.2f}"
    elif commission_usd > 0:
        # Caso 3: Solo hay monto en USD
        commission_text = f"USD {commission_usd:.2f}"
    else:
        # Caso 4: Ninguno de los dos tiene monto (>0)
        commission_text = "0.00"

    subject = f"Recibo {receipt_id}: Se ha registrado una cobranza para el cliente {customer_name} de la tienda {store_name}"
    app_url = os.environ.get('APP_URL')

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER_RECEIPT')
    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT_REMBD')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT_REMBD')
    else:
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT')
    mail = Mail(app)

    msg = Message(subject=subject,
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_USERNAME'], recipient_receipt])

    body = f"""
    <html>
        <body>
            <p>Se ha registrado una nueva cobranza con los siguientes detalles:</p>
            <ul>
                <li><strong>Vendedor:</strong> {session['salesRep_id']} | {session['user_firstName']} {session['user_lastName']}</li>
                <li><strong>Número de Recibo:</strong> {receipt_id}</li>
                <li><strong>Tienda:</strong> {store_name}</li>
                <li><strong>Cliente:</strong> {customer_name}</li>
                <li><strong>N_CTA Factura(s):</strong> {ncta_str}</li>
                <li><strong>Monto Total:</strong> {currency} {total_receipt_amount}</li>
                <li><strong>Comisión a Recibir:</strong> {commission_text}</li>
            </ul>
                
            <p>Por favor ingrese a la <a href="{app_url}">aplicación web de GIPSY</a> de <strong>"Registro de Cobranza al Mayor"</strong> y diríjase a la sección de <strong>"Recibos de Cobranza"</strong> para revisar y validar la cobranza registrada.</p>
        </body>
    </html>
    """

    msg.html = body

    mail.send(msg)

    return jsonify({'success': True})

def send_receipt_salesRepNotification(receipt_id, store_id, store_name, customer_name, total_receipt_amount, commission_bs, commission_usd, currency, ncta_str):

    # Formateo del monto de comisión según la moneda
    if commission_bs > 0 and commission_usd > 0:
        # Caso 1: Ambos montos son mayores a 0
        commission_text = f"Bs {commission_bs:.2f} y USD {commission_usd:.2f}"
    elif commission_bs > 0:
        # Caso 2: Solo hay monto en Bs
        commission_text = f"Bs {commission_bs:.2f}"
    elif commission_usd > 0:
        # Caso 3: Solo hay monto en USD
        commission_text = f"USD {commission_usd:.2f}"
    else:
        # Caso 4: Ninguno de los dos tiene monto (>0)
        commission_text = "0.00"

    subject = f"Recibo {receipt_id}: Usted ha registrado una cobranza para el cliente {customer_name} de la tienda {store_name}"
    app_url = os.environ.get('APP_URL')

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER_RECEIPT')
    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT_REMBD')
    else:
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
    mail = Mail(app)

    salesRep_Recipient = get_userEmail(session['user_id'])

    msg = Message(subject=subject,
                sender=app.config['MAIL_USERNAME'],
                recipients=[salesRep_Recipient])

    body = f"""
    <html>
        <body>
            <p>Hola, vendedor(a) {session['user_firstName']} {session['user_lastName']}.</p>
            <p>Usted ha registrado una nueva cobranza con los siguientes detalles:</p>
            <ul>
                <li><strong>Vendedor:</strong> {session['salesRep_id']} | {session['user_firstName']} {session['user_lastName']}</li>
                <li><strong>Número de Recibo:</strong> {receipt_id}</li>
                <li><strong>Tienda:</strong> {store_name}</li>
                <li><strong>Cliente:</strong> {customer_name}</li>
                <li><strong>N_CTA Factura(s):</strong> {ncta_str}</li>
                <li><strong>Monto Total:</strong> {currency} {total_receipt_amount}</li>
                <li><strong>Comisión a Recibir:</strong> {commission_text}</li>
            </ul>
            <p>El equipo administrativo la revisará y validará en breve. Una vez confirmada, recibirá una notificación adicional.</p>
        </body>
    </html>
    """

    msg.html = body

    mail.send(msg)

    return jsonify({'success': True})


# Rechazo de Recibo de Pago
@app.route('/send_rejectionReceipt_email', methods=['POST'])
def send_rejectionEmail():

    receipt_id = int(request.form.get('receipt_id', ''))

    invoices = get_invoices_by_receipt(receipt_id)
    ncta_list = [str(invoice[0]) for invoice in invoices]
    ncta_str = ", ".join(ncta_list)

    set_isReviewedReceipt(receipt_id)

    # Revirtiendo monto abonado
    try:
        payment_relations = get_paymentRelations_by_receipt(receipt_id)
        discount_value = float(request.form.get('discount_value', 0))
        for relation in payment_relations:
            debtAccount_id = relation[0]
            paid_amount = float(relation[1])

            debtAccount_amounts = get_invoiceCurrentPaidAmount(debtAccount_id)
            current_paid = float(debtAccount_amounts[0])
            total_amount = float(debtAccount_amounts[1])

            if discount_value > 0:
                discount_amount = round(total_amount * (discount_value/100), 2)
                paid_amount += discount_amount

            new_paid_amount = round(current_paid - paid_amount, 2)
            revert_invoicePaidAmount(debtAccount_id, new_paid_amount)
   
    except Exception as e:
        app.logger.error(f"Error al revertir pagos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

    rejection_reason = request.form.get('rejection_reason', '')
    rejection_reason_html = "<br>".join(line.strip() for line in rejection_reason.split('\n') if line.strip())
    store_id = request.form.get('store_id', '')
    store_name = request.form.get('store_name', '')
    customer = request.form.get('customer', '')
    currency = request.form.get('currency', '')
    totalPaid = request.form.get('total_paid', '')
    totalCommission = request.form.get('total_commission', '')
    salesRep_fullname = request.form.get('salesRep_fullname', '')
    salesRep_email = request.form.get('salesRep_email', '')

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER_RECEIPT')
    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT_REMBD')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT_REMBD')
    else:
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT')
    mail = Mail(app)

    subject = f"Recibo de Cobranza #{ receipt_id }: Rechazado"
    msg = Message(subject=subject,
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[app.config['MAIL_USERNAME'], salesRep_email, recipient_receipt])

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>El recibo de cobranza con los siguientes datos:</p>

            <ul style="list-style-type: disc; margin-left: 5px; padding-left: 5px;">
                <li><strong>Vendedor:</strong> {salesRep_fullname}</li>
                <li><strong>Empresa:</strong> {store_name}</li>
                <li><strong>Cliente:</strong> {customer}</li>
                <li><strong>N_CTA Factura(s):</strong> {ncta_str}</li>
                <li><strong>Moneda:</strong> {currency}</li>
                <li><strong>Monto total:</strong> {currency} {totalPaid}</li>
                <li><strong>Comisión a recibir:</strong> {currency} {totalCommission}</li>
            </ul>          
            
            <p>ha sido rechazado por el siguiente motivo:</p>
            
            <blockquote style="border-left: 5px solid #ccc; margin: 1.5em 0; padding: 0.5em 1em;">
                {rejection_reason_html}
            </blockquote>
            
            <p>Se solicita verificar y volver a realizar el registro de la cobranza.</p>
        </body>
    </html>
    """
    msg.html = html_body

    mail.send(msg)

    return jsonify({'success': True})


@app.route('/send_validateReceipt_email', methods=['POST'])
def send_validationEmail():

    # Datos iniciales para la interfaz
    store_id = request.form.get('store_id', '')
    customer_id = request.form.get('customer_id', '')
    customer_isRembd = request.form.get('customer_isRembd', '')
    pagination = int(request.form.get('pagination', ''))
    receipt_id = int(request.form.get('receipt_id', ''))
    salesRep_NameEmail = request.form.get('salesRep_NameEmail', '')
    salesRep_fullname = request.form.get('salesRep_fullname', '')
    salesRep_email = request.form.get('salesRep_email', '')

    receipts_per_page = 1
    receipts = get_unvalidated_receipts_by_customer(customer_id, customer_isRembd)
    store = get_receiptStore_by_id(store_id)
    customer = get_customer_by_id(customer_id, customer_isRembd)
    store_name = store[1] if store else ''
    customer_name = f"{customer[1]} {customer[2]}" if customer else ''
    total_receipts = len(receipts)
    invoices = get_invoices_by_receipt(receipt_id)
    ncta_list = [str(invoice[0]) for invoice in invoices]
    ncta_str = ", ".join(ncta_list)
    paymentEntries = get_paymentEntries_by_receipt(receipt_id)
    paymentEntries = get_onedriveProofsOfPayments(paymentEntries)

    if receipt_id <= 250:
        salesRepComm = get_SalesRepCommission_OLD(receipt_id)
    else:
        salesRepComm = get_SalesRepCommission(receipt_id)

    # Validación de Recibo de Pago
    """
    OJO: El JS primero llama a la función de enviar el correo y luego la del PDF.
    Si se valida el recibo aquí, al renderizar la interfaz para el PDF, no tendrá acceso a los campos.
    Al implementar el pdf en producción, realizar la validación luego de este último renderizado.
    NOTA: Actualmente, el PDF se descarga directamente del correo, así que no ha sido solicitado
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
                                 salesRep_NameEmail=salesRep_NameEmail,
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
                        align-items: center;
                        margin-bottom: 20px;
                        position: relative;
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
                    <h2>Reporte de Cobranza al Mayor</h2>
                    <p><strong>{store_name}</strong></p>
                    <p><strong>Vendedor:</strong> {salesRep_fullname}</p>
                    <p><strong>Cliente:</strong> {customer_name}</p>
                    <p><strong>N_CTA Factura(s):</strong> {ncta_str}</p>
                </div>
                {html_content}
                <br>
                <p>Se anexan los comprobantes de pago del recibo.</p>
            </body>
            </html>
            """

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER_RECEIPT')
    if store_id == '904' or store_id == '905':
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT_REMBD')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT_REMBD')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT_REMBD')
    else:
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_RECEIPT')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD_RECEIPT')
        recipient_receipt = os.environ.get('MAIL_RECIPIENT_RECEIPT')
    mail = Mail(app)

    # Lógica para enviar el correo
    subject = f"Recibo de Cobranza #{ receipt_id }: Validado"
    msg = Message(subject=subject,
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[app.config['MAIL_USERNAME'], salesRep_email, recipient_receipt])
    
    msg.html = html_body

    # Adjuntar comprobantes de pago (dinámico desde OneDrive)
    headers = get_onedrive_headers()
    for paymentEntry in paymentEntries:
        file_info = paymentEntry[7]
        if file_info:
            file_url = file_info.get('email_url', '')
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
    
    if receipt_id <= 250:
        salesRepComm = get_SalesRepCommission_OLD(receipt_id)
    else:
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