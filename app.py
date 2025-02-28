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
   

@mainapp.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == '__main__':
   app.run()
