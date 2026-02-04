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

    # --- Verificar la existencia del usuario y obtener datos base ---
    # Esto se ejecuta primero para confirmar que el usuario y la contraseña son correctos
    cursor.execute('''
                    SELECT userId, salesRepId, firstName, lastName
                    FROM AccessControl.Users
                    WHERE username=%s AND passwordHash=%s
                   ''', (username, password))
    
    user_base_data = cursor.fetchone()

    # Si el usuario no existe, terminamos aquí.
    if not user_base_data:
        conn.close()
        return None 
    
    # Inicializar el diccionario user_data con los datos base obtenidos
    user_data = {
        'user_id': user_base_data[0],
        'salesRep_id': user_base_data[1],
        'firstName': user_base_data[2],
        'lastName': user_base_data[3],
        'roles_id': [],
        'modules_id': [],
        'permissions_id': []
    }

    # --- QUERY 1: Obtener roles y permisos generales ---
    cursor.execute('''
                    SELECT R.roleId, P.moduleId, P.permissionId
                    FROM AccessControl.Users U
                    JOIN AccessControl.UserRoles R ON U.userId = R.userId
                    JOIN AccessControl.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                   ''', (username, password))
    
    results_general = cursor.fetchall()
    
    # --- QUERY 2: Verificar roles/permisos para el MÓDULO 3 (Documentos) ---
    cursor.execute('''
                    SELECT 1
                    FROM AccessControl.Users U
                    JOIN Documents.UserRoles R ON U.userId = R.userId
                    JOIN Documents.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s AND R.isActive = 1
                   ''', (username, password))

    results_module3 = cursor.fetchone()
    
    conn.close()

    # --- Procesamiento de los resultados ---
    
    roles_id_list = []
    modules_id_list = []
    permissions_id_list = []

    # Procesar resultados del Query 1 (General)
    # Este bucle ahora se enfoca solo en agregar roles y permisos.
    for row in results_general:
        roles_id_list.append(row[0]) # roleId
        modules_id_list.append(row[1]) # moduleId
        permissions_id_list.append(row[2]) # permissionId
        
    # Paso CLAVE: Añadir el Módulo 3 si se encontró algún registro en el Query 2
    if results_module3:
        MODULE_ID_3 = 3
        modules_id_list.append(MODULE_ID_3)

    # Asignar listas únicas al diccionario de usuario
    user_data['roles_id'] = list(set(roles_id_list))
    user_data['modules_id'] = list(set(modules_id_list))
    user_data['permissions_id'] = list(set(permissions_id_list))

    # El usuario existe (validado por el Query 0) y retornamos su data, 
    # incluso si sus listas de roles/módulos están vacías.
    return user_data

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