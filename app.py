import os
import urllib.parse
#from weasyprint import HTML

from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify)

from cashflow_db import get_beneficiaries, get_cashflowStores, get_concepts, get_creditConcepts, get_debitConcepts, get_operations
from cashflow_db import get_last_beneficiary_id, get_last_concept_id, get_motion_id, get_last_store_id
from cashflow_db import set_beneficiaries, set_concepts, set_stores, set_operations

from receipt_db import get_receiptStores, get_receiptStore_by_id, get_sellers, get_seller_details, get_customers, get_tender, get_commissionsRules
from receipt_db import get_invoices_by_customer, get_receiptsInfo, get_receiptsStoreCustomer
from receipt_db import set_commissionsRules

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
    customers_by_store = {store[0]: get_customers(store[0]) for store in stores}
    return render_template('receipt.receipts.html', page='receipts', active_page='receipts', stores=stores, customers_by_store=customers_by_store)

@app.route('/receiptDetails')
def receiptDetails():
    return render_template('receipt.receiptDetails.html', page='receiptDetails', active_page='receipts')

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
            'Remaining': float(invoice[2] - invoice[3])
        } for invoice in invoices
    ]
    return jsonify({'invoices': formatted_invoices})

@app.route('/accountsForm/<string:account_ids>')
def accountsForm(account_ids):
    account_ids_list = account_ids.split('-')
    tender = get_tender()
    receiptStoreCustomer = get_receiptsStoreCustomer(account_ids_list)
    receiptsInfo = get_receiptsInfo(account_ids_list)
    return render_template(
        'receipt.accountsForm.html',
        page='accountsForm',
        active_page='accountsReceivable',
        tender=tender,
        receiptStoreCustomer=receiptStoreCustomer,
        receiptDetails=receiptsInfo
    )


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
