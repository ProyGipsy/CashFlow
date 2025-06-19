import os
import pymssql

# Conexión a la BDI
def get_db_connection():
    server = os.environ.get('DB_SERVER')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')
    conn = pymssql.connect(server, user, password, database)
    return conn

# Obtención de datos de usuario
def get_user_data(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    SELECT U.userId, U.salesRepId, U.firstName, U.lastName, R.roleId, P.moduleId
                    FROM AccessControl.Users U
                    JOIN AccessControl.UserRoles R ON U.userId = R.userId
                    JOIN AccessControl.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                   ''', (username, password))
    results = cursor.fetchall()
    conn.close()

    if results:
        user_data = {
            'user_id': results[0][0],
            'salesRep_id': results[0][1],
            'firstName': results[0][2],
            'lastName': results[0][3],
            'roles_id': [row[4] for row in results],
            'modules_id': [row[5] for row in results]
        }
        return user_data
        
    return None

def get_roleInfo(role_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    SELECT name 
                    FROM AccessControl.Roles
                    WHERE roleId = %s
                   ''', (role_id,))
    roleInfo = cursor.fetchone()[0]
    conn.close()
    return roleInfo

def get_userEmail(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    SELECT email
                    FROM AccessControl.Users
                    WHERE userId = %s
                   ''', (user_id,))
    userEmail = cursor.fetchone()[0]
    conn.close()
    return userEmail

def get_salesRepNameAndEmail(salesRep_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    SELECT firstName, lastName, email
                    FROM AccessControl.Users
                    WHERE salesRepId = %s
                   ''', (salesRep_id,))
    salesRepEmail = cursor.fetchone()
    conn.close()
    return salesRepEmail