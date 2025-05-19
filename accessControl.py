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
    print('''
                    SELECT U.userId, U.salesRepId, U.firstName, U.lastName, P.moduleId
                    FROM AccessControl.Users U
                    JOIN AccessControl.UserRoles R ON U.userId = R.userId
                    JOIN AccessControl.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                   ''', (username, password))
    cursor.execute('''
                    SELECT U.userId, U.salesRepId, U.firstName, U.lastName, P.moduleId
                    FROM AccessControl.Users U
                    JOIN AccessControl.UserRoles R ON U.userId = R.userId
                    JOIN AccessControl.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                   ''', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user