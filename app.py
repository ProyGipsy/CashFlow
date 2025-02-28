import os

from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, redirect, jsonify)

app = Flask(__name__)


@app.route('/')
def index():
   print('Request for login page received')
   return render_template('index.html')

@app.route('/cashier')
def homeCashier():
    return render_template('homeCashier.html', page='homeCashier', active_page='homeCashier')

@mainapp.route('/operations', methods=['GET', 'POST'])
def operations():
    operations = get_operations()
    stores = get_stores()
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
        return redirect(url_for('mainapp.operations'))

    return render_template(
        'operations.html',
        page='operations',
        active_page='operations',
        operations=operations,
        concepts=concepts,
        creditConcepts=creditConcepts,
        debitConcepts=debitConcepts,
        stores=stores,
        beneficiaries=beneficiaries
    )

@mainapp.route('/beneficiaries', methods=['GET', 'POST'])
def beneficiaries():
    beneficiaries = get_beneficiaries()
    last_id = get_last_beneficiary_id()
    if request.method == 'POST':
        data = request.get_json()  # Obtener datos JSON
        set_beneficiaries(data)
        return jsonify(success=True)
    return render_template('beneficiaries.html', page='beneficiaries', active_page='beneficiaries', beneficiaries=beneficiaries, last_id=last_id)
    
@mainapp.route('/stores', methods=['GET', 'POST'])
def stores():
    stores = get_stores()
    last_id = get_last_store_id()
    if request.method == 'POST':
        data = request.get_json()
        set_stores(data)
        return jsonify(success=True)
    return render_template('stores.html', page='stores', active_page='stores', stores=stores, last_id=last_id)

@mainapp.route('/concepts', methods=['GET', 'POST'])
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
    return render_template('concepts.html', page='concepts', active_page='concepts', concepts=concepts, last_id=last_id)

@mainapp.route('/logout')
def logout():
    return render_template('login.html', page='login', active_page='login')

if __name__ == '__main__':
   app.run()
