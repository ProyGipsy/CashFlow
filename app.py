import os
import urllib.parse
import json

#from weasyprint import HTML
from datetime import datetime
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response)

from cashflow_db import (get_beneficiaries, get_cashflowStores, get_concepts, get_creditConcepts, get_debitConcepts,
    get_operations, get_last_beneficiary_id, get_last_concept_id, get_motion_id, get_last_store_id,
    set_beneficiaries, set_concepts, set_stores, set_operations)

from receipt_db import (get_db_connection, 
    get_receiptStores, get_receiptStore_by_id, get_sellers, get_seller_details, get_customers, get_tender, get_commissionsRules,
    get_invoices_by_customer, get_receiptsInfo, get_receiptsStoreCustomer, get_bankAccounts, get_commissions, get_customer_by_id,
    get_customers_with_unvalidated_receipts, get_count_customers_with_unvalidated_receipts, get_unvalidated_receipts_by_customer,
    get_invoices_by_receipt, get_paymentEntries_by_receipt, get_salesRep_isRetail, set_SalesRepCommission, get_SalesRepCommission,
    set_commissionsRules, set_paymentReceipt, set_paymentEntry, save_proofOfPayment, set_invoiceBalance, set_DebtPaymentRelation)

app = Flask(__name__)

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

    if request.method == 'POST':
        date_operation = request.form['date_operation']
        concept_id = request.form['concept']
        store_id = request.form['store']
        beneficiary_id = request.form['beneficiary']
        observation = request.form['observation']
        amount = float(request.form['amount'])

        set_operations(store_id, beneficiary_id, concept_id, observation, date_operation, amount)
        return redirect(url_for('operations'))

    return render_template(
        'cashflow.operations.html',
        page='operations',
        active_page='operations',
        operations=operations,
        concepts=concepts,
        creditConcepts=creditConcepts,
        debitConcepts=debitConcepts,
        stores=stores,
        beneficiaries=beneficiaries
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

@app.route('/receiptAdmin')
def homeAdmin():
    return render_template('receipt.homeAdmin.html', page='homeAdmin', active_page='homeAdmin')

@app.route('/sellers')
def sellers():
    stores = get_receiptStores()
    sellers_by_store = {store[0]: get_sellers(store[0]) for store in stores}
    return render_template('receipt.sellers.html', page='sellers', active_page='sellers', stores=stores, sellers_by_store=sellers_by_store)

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
    stores = get_receiptStores()
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
    stores = get_receiptStores()
    customers_by_store = {store[0]: get_customers(store[0]) for store in stores}
    return render_template('receipt.accountsReceivable.html', page='accountsReceivable', active_page='accountsReceivable', stores=stores, customers_by_store=customers_by_store)

@app.route('/get_invoices/<customer_id>')
def get_invoices(customer_id):
    invoices = get_invoices_by_customer(customer_id)
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
    currencyID = receiptStoreCustomer[6]
    tender = get_tender(currencyID)
    receiptsInfo = get_receiptsInfo(account_ids_list)
    bankAccounts = []
    commissions = get_commissions()
    return render_template(
        'receipt.accountsForm.html',
        page='accountsForm',
        active_page='accountsReceivable',
        tender=tender,
        receiptStoreCustomer=receiptStoreCustomer,
        receiptDetails=receiptsInfo,
        bankAccounts=bankAccounts,
        commissions=commissions
    )

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
            set_invoiceBalance(cursor, account_id, amount_paid)
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


# Generación del PDF
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Renderiza el template HTML con los datos de la solicitud
    rendered = render_template('receipt.receiptDetails.html', 
                               storeName=request.form.get('storeName'),
                               customerName=request.form.get('customerName'),
                               is_pdf=True)  # Pasar is_pdf=True para el PDF

    # Convierte el HTML renderizado a PDF con WeasyPrint
    pdf = HTML(string=rendered, base_url="https://gipsy-app-new-exdecybsd2cab7gk.westus-01.azurewebsites.net").write_pdf()

    # Prepara la respuesta con el PDF generado
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'

    # Nombre del archivo PDF que se descarga
    store_name = request.form.get('storeName', 'Empresa')
    customer_name = request.form.get('customerName', 'Cliente')
    filename = f'Cobranza_{store_name}_{customer_name}.pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    return response


if __name__ == '__main__':
   app.run()
