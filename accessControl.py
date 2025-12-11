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

    # --- QUERY 1: Obtener la data estándar y permisos generales ---
    cursor.execute('''
                    SELECT U.userId, U.salesRepId, U.firstName, U.lastName, R.roleId, P.moduleId, P.permissionId
                    FROM AccessControl.Users U
                    JOIN AccessControl.UserRoles R ON U.userId = R.userId
                    JOIN AccessControl.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                   ''', (username, password))
    
    results_general = cursor.fetchall()
    
    # --- QUERY 2: Verificar roles/permisos para el MÓDULO 3 (Tablas Documents) ---
    # Usamos una consulta simple que solo verifica la existencia de roles.
    # No necesitamos traer todos los campos si solo verificamos el acceso.
    cursor.execute('''
                    SELECT 1
                    FROM AccessControl.Users U
                    JOIN Documents.UserRoles R ON U.userId = R.userId
                    JOIN Documents.RolePermissions P ON R.roleId = P.roleId
                    WHERE U.username=%s AND U.passwordHash=%s
                    -- LIMIT 1 (o TOP 1 en SQL Server) para optimizar la verificación
                   ''', (username, password))

    results_module3 = cursor.fetchone() # Solo necesitamos un registro para saber si tiene acceso
    
    conn.close()

    if not results_general:
        # El usuario no existe o la contraseña es incorrecta (no hay roles estándar)
        return None

    # --- Procesamiento de los resultados ---
    
    # Inicializa las listas de módulos y permisos con los datos generales
    roles_id_list = []
    modules_id_list = []
    permissions_id_list = []

    for row in results_general:
        # Los primeros 4 campos son de usuario, por eso los tomamos del primer registro
        # Esto solo se hace una vez (si results_general no está vacío)
        user_data = {
            'user_id': row[0],
            'salesRep_id': row[1],
            'firstName': row[2],
            'lastName': row[3],
        }

        roles_id_list.append(row[4])
        modules_id_list.append(row[5])
        permissions_id_list.append(row[6])

    # Paso CLAVE: Añadir el Módulo 3 si se encontró algún registro en el Query 2
    if results_module3:
        MODULE_ID_3 = 3
        # Solo lo agregamos si no está ya en la lista (por si el Query 1 lo incluyera por error)
        if MODULE_ID_3 not in modules_id_list:
            modules_id_list.append(MODULE_ID_3)

    # El procesamiento en Python garantiza que solo se añada el ID 3 UNA vez
    user_data['roles_id'] = list(set(roles_id_list)) # Usar set() para IDs únicos
    user_data['modules_id'] = list(set(modules_id_list)) # Usar set() para IDs únicos
    user_data['permissions_id'] = list(set(permissions_id_list)) # Usar set() para IDs únicos

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