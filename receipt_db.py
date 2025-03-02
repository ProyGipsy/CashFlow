import os
import pymssql

def get_db_connection():
    server = os.environ.get('DB_SERVER')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    conn = pymssql.connect(server, user, password, database)
    return conn


# Obtención de Data en la Interfaz

def get_stores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Name FROM Main.Store')
    stores = cursor.fetchall()
    conn.close()
    return stores

def get_store_by_id(store_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT Name FROM Main.Store WHERE ID = %s', (store_id,))
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
    cursor.execute('SELECT ID, Name, EmailAddress, Telephone, PercentOfSale, StoreID FROM Main.SalesRep WHERE ID = %s', (seller_id,))
    seller = cursor.fetchone()
    conn.close()
    return seller
