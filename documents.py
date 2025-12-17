import os
import pymssql

from datetime import datetime
from dbutils.pooled_db import PooledDB
from emailScript import (
    send_email,
    create_doc_type_html,
    create_new_doc_html,
    generate_document_content_html,
    create_custom_email_html,
    create_send_notification_html,
)

# Configuración del pool de conexiones

pool = PooledDB(
    creator=pymssql,
    maxconnections = 15,
    mincached = 3,
    maxcached = 6,
    blocking = True,
    host = os.environ.get('DB_SERVER'),
    user = os.environ.get('DB_USER'),
    password = os.environ.get('DB_PASSWORD'),
    database = os.environ.get('DB_NAME')
)

def get_docs_by_type():
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT TypeID AS id, Name AS name, ShortName AS shortName 
        FROM Documents.DocumentType
        ORDER BY name
        """

        cursor.execute(sql)
        documents = cursor.fetchall()
        
        return documents
    
    except Exception as e:
        print(f"Error al obtener los Tipos de Documento: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_docs_companies():
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT CompanyID AS id, Name AS name, RIFtype AS rifType, RIFnumber AS rifNumber
        FROM Documents.Company
        ORDER BY name
        """

        cursor.execute(sql)
        companies = cursor.fetchall()
        
        return companies
    
    except Exception as e:
        print(f"Error al obtener las empresas: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_doc_type(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # 1. VALIDACIÓN
        validation_sql = """
        SELECT TypeID
        FROM Documents.DocumentType
        WHERE (Name = %s OR ShortName = %s)
        """
        cursor.execute(validation_sql, (data['name'], data['alias']))
        existing = cursor.fetchone()

        if existing:
            raise ValueError("Ya existe un Tipo de Documento con ese Nombre o Alias.")

        # 2. INSERCIÓN EN BASE DE DATOS
        
        # A. Cabecera
        sql = """
        INSERT INTO Documents.DocumentType (Name, ShortName, Description)
        OUTPUT INSERTED.TypeID
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (data['name'], data['alias'], data.get('description', '')))
        row = cursor.fetchone()
        inserted_id = row['TypeID']

        # B. Permisos
        sql_access_control = """
        INSERT INTO AccessControl.Permissions (name, isDocumentsModule)
        VALUES (%s, 1)
        """
        cursor.execute(sql_access_control, (data['name'],))

        # C. Campos (Fields) - MODIFICADO AQUÍ PARA INCLUIR isMandatory
        sql_document_fields = """
        INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision, isMandatory)
        OUTPUT INSERTED.FieldID
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        sql_specific_values = """
        INSERT INTO Documents.SpecificValue (FieldID, Value)
        VALUES (%s, %s)
        """

        # Diccionario para traducir tipos de datos
        type_translation = {
            'text': 'Texto Corto', 'textarea': 'Texto Largo', 
            'int': 'Numérico Entero', 'float': 'Decimal', 'money': 'Moneda',
            'date': 'Fecha', 'specificValues': 'Lista de Opciones'
        }
        
        fields_for_email = []

        for field in data.get('fields', []):
            f_len = field.get('length') if field.get('length') else 0
            f_prec = field.get('precision') if field.get('precision') else 0
            
            # 1. Obtenemos el valor de isRequired (1 o 0), por defecto 0 si no viene
            is_mandatory = field.get('isRequired', 0)

            # Guardamos datos para el correo (Opcional: puedes agregar 'Obligatorio' al correo si quieres)
            fields_for_email.append({
                'nombre': field['name'],
                'tipo_dato': type_translation.get(field['type'], field['type']),
                'longitud': f_len if f_len > 0 else 'N/A',
                'precision': f_prec if f_prec > 0 else 'N/A',
                'obligatorio': 'Sí' if is_mandatory == 1 else 'No' # Info extra para tu template
            })

            # 2. Ejecutamos la inserción con el nuevo parámetro
            cursor.execute(sql_document_fields, (
                inserted_id, 
                field['name'], 
                field['type'], 
                f_len, 
                f_prec,
                is_mandatory # <--- Aquí pasamos el 1 o 0
            ))
            
            if field['type'] == 'specificValues':
                field_row = cursor.fetchone()
                if field_row:
                    field_id = field_row['FieldID']
                    for value in field.get('specificValues', []):
                        val_text = value['value'] if isinstance(value, dict) else value
                        cursor.execute(sql_specific_values, (field_id, val_text))
        
        connection.commit()

        # 3. NOTIFICACIÓN POR CORREO
        try:
            sender_email = os.environ.get("MAIL_USERNAME_DOCUMENTS")
            email_password = os.environ.get("MAIL_PASSWORD_DOCUMENTS")
            recipient_admin = os.environ.get("MAIL_RECIPIENT_TEST")

            if sender_email and email_password and recipient_admin:
                
                email_context = {
                    'doc_type_name': data['name'],
                    'alias': data['alias'],
                    'description': data.get('description', 'Sin descripción'),
                    'fields': fields_for_email
                }

                subject = f"Nuevo Tipo de Documento Creado: {data['name']}"
                html_body = create_doc_type_html(email_context)

                send_email(
                    subject=subject,
                    body_html=html_body,
                    sender_email=sender_email,
                    email_password=email_password,
                    receiver_emails=[recipient_admin],
                    attachments=None 
                )
                print(f"Correo de notificación enviado exitosamente a {recipient_admin}")
            
            else:
                print("Advertencia: No se envió el correo. Faltan credenciales o destinatario en .env")

        except Exception as email_error:
            print(f"El Tipo de Documento se creó, pero falló el envío de correo: {email_error}")

        return inserted_id

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error creando el Tipo de Documento: {e}")
        raise e

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_doc_type_full(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Agregamos TF.isMandatory a la consulta
        sql = """
        SELECT DT.TypeID AS id, DT.Name AS name, DT.ShortName AS shortName, DT.Description AS description,
               TF.FieldID AS fieldId, TF.Name AS fieldName, TF.DataType AS fieldType, 
               TF.Length AS fieldLength, TF.Precision AS fieldPrecision, 
               TF.isMandatory, -- <--- NUEVO CAMPO
               SV.ValueID AS valueId, SV.Value AS value
        FROM Documents.DocumentType DT
        LEFT JOIN Documents.TypeFields TF ON DT.TypeID = TF.DocumentTypeID
        LEFT JOIN Documents.SpecificValue SV ON TF.FieldID = SV.FieldID
        WHERE DT.TypeID = %s
        """

        cursor.execute(sql, (data['id'],))
        rows = cursor.fetchall()
        
        if not rows:
            return None, 404

        doc_type = {
            'id': rows[0]['id'],
            'name': rows[0]['name'],
            'alias': rows[0]['shortName'],
            'description': rows[0]['description'],
            'fields': []
        }

        fields_map = {}

        for row in rows:
            field_id = row['fieldId']
            
            # Verificamos que exista un field_id (porque el LEFT JOIN puede traer nulos si no hay campos)
            if field_id and field_id not in fields_map:
                fields_map[field_id] = {
                    'id': field_id,
                    'name': row['fieldName'],
                    'type': row['fieldType'],
                    'length': row['fieldLength'],
                    'precision': row['fieldPrecision'],
                    'isRequired': row['isMandatory'], # <--- Mapeamos el valor de la BD (1/0 o True/False)
                    'specificValues': []
                }
                doc_type['fields'].append(fields_map[field_id])

            if row['valueId']:
                fields_map[field_id]['specificValues'].append({
                    'id': row['valueId'],
                    'value': row['value']
                })

        return doc_type
    
    except Exception as e:
        print(f"Error al obtener el Tipo de Documento completo: {e}")
        return None, 500
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def edit_doc_type(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # --- VALIDACIÓN DE DUPLICADOS ---
        validation_sql = """
            SELECT TypeID
            FROM Documents.DocumentType
            WHERE (Name = %s OR ShortName = %s) AND TypeID != %s
        """
        cursor.execute(validation_sql, (data['name'], data['alias'], data['id']))
        existing = cursor.fetchone()

        if existing:
            raise ValueError("Ya existe un Tipo de Documento con ese Nombre o Alias.")
        
        # --- PASO CRÍTICO: OBTENER EL NOMBRE VIEJO ANTES DE TOCAR NADA ---
        get_old_name_sql = "SELECT Name FROM Documents.DocumentType WHERE TypeID = %s"
        cursor.execute(get_old_name_sql, (data['id'],))
        row_name = cursor.fetchone()
        
        old_doc_name = row_name['Name'] if row_name else None

        if not old_doc_name:
             raise ValueError("El documento que intentas editar no existe.")

        # 1. ACTUALIZAR CABECERA (DocumentType)
        sql_doc = """
            UPDATE Documents.DocumentType
            SET Name = %s, ShortName = %s, Description = %s
            WHERE TypeID = %s
        """
        cursor.execute(sql_doc, (data['name'], data['alias'], data.get('description', ''), data['id']))

        # 2. ACTUALIZAR EL PERMISO
        sql_access_control = """
            UPDATE AccessControl.Permissions
            SET name = %s
            WHERE name = %s
        """
        cursor.execute(sql_access_control, (data['name'], old_doc_name))

        # 3. DEFINIR SQLs DE CAMPOS (Actualizados con isMandatory)
        sql_update_field = """
            UPDATE Documents.TypeFields
            SET Name = %s, DataType = %s, Length = %s, Precision = %s, isMandatory = %s
            WHERE FieldID = %s AND DocumentTypeID = %s
        """
        
        sql_insert_field = """
            INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision, isMandatory)
            VALUES (%s, %s, %s, %s, %s, %s)
        """ 

        sql_get_new_id = "SELECT SCOPE_IDENTITY() AS new_id"
        
        sql_insert_value = "INSERT INTO Documents.SpecificValue (FieldID, Value) VALUES (%s, %s)"
        sql_delete_values = "DELETE FROM Documents.SpecificValue WHERE FieldID = %s"

        # 4. PROCESAR CAMPOS
        for field in data.get('fields', []):
            field_id = field.get('id')
            
            # Obtener el valor isRequired (1 o 0)
            is_mandatory = field.get('isRequired', 0)

            if field_id is None:
                # --- INSERTAR ---
                cursor.execute(sql_insert_field, (
                    data['id'], 
                    field['name'], 
                    field['type'], 
                    field.get('length', 0), 
                    field.get('precision', 0),
                    is_mandatory # <--- Nuevo parámetro
                ))

                cursor.execute(sql_get_new_id)
                row = cursor.fetchone()
                current_field_db_id = int(row['new_id'])
            
            else:
                # --- ACTUALIZAR ---
                current_field_db_id = field_id
                cursor.execute(sql_update_field, (
                    field['name'], 
                    field['type'], 
                    field.get('length', 0), 
                    field.get('precision', 0), 
                    is_mandatory, # <--- Nuevo parámetro
                    field_id, 
                    data['id']
                ))

            # 5. VALORES ESPECÍFICOS
            if field['type'] == 'specificValues' and 'specificValues' in field:
                cursor.execute(sql_delete_values, (current_field_db_id,))
                
                for val in field['specificValues']:
                    val_text = val['value'] if isinstance(val, dict) else val
                    cursor.execute(sql_insert_value, (current_field_db_id, val_text))
        
        connection.commit()
        return True

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error en edit_doc_type: {e}")
        raise e 

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def create_company(data):
    connection = None
    cursor = None
    
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        INSERT INTO Documents.Company (Name, RIFtype, RIFnumber)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (data['name'], data['rifType'], data['rifNumber']))
        connection.commit()

        return cursor.rowcount

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error creando la Empresa: {e}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_company(data):
    connection = None
    cursor = None
    
    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        UPDATE Documents.Company
        SET Name = %s, RIFtype = %s, RIFnumber = %s
        WHERE CompanyID = %s
        """
        cursor.execute(sql, (data['name'], data['rifType'], data['rifNumber'], data['id']))
        connection.commit()

        return cursor.rowcount

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error actualizando la Empresa: {e}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def format_roles(raw_rows, byUser=False):
    """
    Toma las filas planas (diccionarios) y las convierte en estructura anidada.
    """
    roles_map = {}

    for row in raw_rows:
        # CORRECCIÓN: Usamos row['columna'] en lugar de row.columna
        # Asegúrate de que las claves coincidan EXACTAMENTE con los nombres/alias en tu SELECT
        
        role_id = row['roleId']
        
        # 1. Inicializar el rol si no existe
        if role_id not in roles_map:
            roles_map[role_id] = {
                'id': role_id,
                'name': row['roleName'], # Alias definido en el SQL
                '_temp_permisos': {},
                '_temp_usuarios': {}
            }
        
        # 2. Procesar Permisos
        # Verificamos si permissionId no es None
        if row['permissionId'] is not None:
            perm_id = row['permissionId']
            if perm_id not in roles_map[role_id]['_temp_permisos']:
                roles_map[role_id]['_temp_permisos'][perm_id] = {
                    'id': perm_id,
                    'name': row['permissionName']
                }

        if not byUser:
            # 3. Procesar Usuarios
            # Verificamos si userId no es None
            if row['userId'] is not None:
                user_id = row['userId']
                if user_id not in roles_map[role_id]['_temp_usuarios']:
                    # Manejo seguro de strings vacíos para el nombre
                    f_name = row['firstName'] if row['firstName'] else ''
                    l_name = row['lastName'] if row['lastName'] else ''
                    full_name = f"{f_name} {l_name}".strip()
                    
                    roles_map[role_id]['_temp_usuarios'][user_id] = {
                        'userId': user_id, 
                        'fullName': full_name,
                        'username': row['username']
                    }

    # 4. Limpieza final y conversión a lista
    final_list = []
    for role in roles_map.values():
        role['permisos'] = list(role['_temp_permisos'].values())

        if not byUser:
            role['usuarios'] = list(role['_temp_usuarios'].values())

        del role['_temp_permisos']    
        del role['_temp_usuarios']

        final_list.append(role)

    return final_list

def get_roles():
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql_all_roles = """
        SELECT 
            R.roleId, 
            R.name AS roleName,
            P.permissionId, 
            P.name AS permissionName,
            U.userId, 
            U.firstName, 
            U.lastName, 
            U.username
        FROM AccessControl.Roles R
        LEFT JOIN Documents.RolePermissions RP ON R.roleId = RP.roleId
        LEFT JOIN AccessControl.Permissions P ON RP.permissionId = P.permissionId AND P.isDocumentsModule = 1
        LEFT JOIN Documents.UserRoles UR ON R.roleId = UR.roleId
        LEFT JOIN AccessControl.Users U ON UR.userId = U.userId
        ORDER BY R.roleId;
        """

        sql_only_documents_roles = """
        SELECT 
            R.roleId, 
            R.name AS roleName,
            P.permissionId, 
            P.name AS permissionName,
            U.userId, 
            U.firstName, 
            U.lastName, 
            U.username
        FROM AccessControl.Roles R
        -- Usamos INNER JOIN aquí para obligar a que exista una relación con permisos
        JOIN Documents.RolePermissions RP ON R.roleId = RP.roleId
        -- Usamos INNER JOIN aquí para obligar a que el permiso exista y sea de Documentos
        JOIN AccessControl.Permissions P ON RP.permissionId = P.permissionId
        LEFT JOIN Documents.UserRoles UR ON R.roleId = UR.roleId
        LEFT JOIN AccessControl.Users U ON UR.userId = U.userId
        -- Filtramos explícitamente
        WHERE P.isDocumentsModule = 1 
        AND RP.isActive = 1 -- (Opcional) Recomendado si manejas borrado lógico
        ORDER BY R.roleId;
        """
        cursor.execute(sql_only_documents_roles)

        roles = cursor.fetchall()
        roles = format_roles(roles)

        return roles
    
    except Exception as e:
        print(f"Error al obtener los Roles: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_permissions():
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT permissionId AS id, name 
        FROM AccessControl.Permissions
        WHERE isDocumentsModule = 1
        ORDER BY name
        """

        cursor.execute(sql)
        permissions = cursor.fetchall()
        
        return permissions

    except Exception as e:
        print(f"Error al obtener los Permisos: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_users():
    connection = None
    cursor = None

    try: 
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT userId AS id, firstName + ' ' + lastName AS fullName, username 
        FROM AccessControl.Users
        WHERE isActive = 1
        ORDER BY fullName
        """

        cursor.execute(sql)
        users = cursor.fetchall()

        return users
    
    except Exception as e:
        print(f"Error al obtener los Usuarios: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_user_by_id(id):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        user_sql = """
        SELECT userId AS id, firstName, lastName, username, email
        FROM AccessControl.Users
        WHERE userId = %s AND isActive = 1
        """
        cursor.execute(user_sql, (id))

        user_data = cursor.fetchone()

        roles_sql = """
        SELECT 
            R.roleId, 
            R.name AS roleName,
            P.permissionId, 
            P.name AS permissionName
        FROM AccessControl.Roles R
        -- Usamos INNER JOIN aquí para obligar a que exista una relación con permisos
        JOIN Documents.RolePermissions RP ON R.roleId = RP.roleId
        -- Usamos INNER JOIN aquí para obligar a que el permiso exista y sea de Documentos
        JOIN AccessControl.Permissions P ON RP.permissionId = P.permissionId
        LEFT JOIN Documents.UserRoles UR ON R.roleId = UR.roleId
        LEFT JOIN AccessControl.Users U ON UR.userId = U.userId
        -- Filtramos explícitamente
        WHERE P.isDocumentsModule = 1 
        AND U.userId = %s
        AND RP.isActive = 1 -- (Opcional) Recomendado si manejas borrado lógico
        ORDER BY R.roleId;
        """
        cursor.execute(roles_sql, (id))

        user_roles = cursor.fetchall()
        user_roles = format_roles(user_roles, byUser=True)

        for role in user_roles:
            pass

        user = {
            'id': user_data['id'],
            'firstName': user_data['firstName'],
            'lastName': user_data['lastName'],
            'fullName': f"{user_data['firstName']} {user_data['lastName']}",
            'username': user_data['username'],
            'email': user_data['email'],
            'roles': user_roles,
        }

        return user

    except Exception as e:
        print(f"Error al obtener el usuario: {e}")
        return []
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_role(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        INSERT INTO AccessControl.Roles (name)
        OUTPUT INSERTED.roleID
        VALUES (%s)
        """
        cursor.execute(sql, (data['name'],))
        inserted_id = cursor.fetchone()['roleID']

        sql_role_permissions = """
        INSERT INTO Documents.RolePermissions (roleId, permissionId, isActive, lastUpdate)
        VALUES (%s, %s, 1, GETDATE())
        """

        for permiso in data.get('permisos', []):
            cursor.execute(sql_role_permissions, (inserted_id, permiso['id']))

        sql_user_roles = """
        INSERT INTO Documents.UserRoles (roleId, userId, isActive, lastUpdate)
        VALUES (%s, %s, 1, GETDATE())
        """

        for usuario in data.get('usuarios', []):
            cursor.execute(sql_user_roles, (inserted_id, usuario['id']))
                
        connection.commit()

        return inserted_id

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error creando el Rol: {e}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def edit_role(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # 1. ACTUALIZAR NOMBRE DEL ROL
        sql_update_role = """
            UPDATE AccessControl.Roles
            SET name = %s
            WHERE roleID = %s
        """
        cursor.execute(sql_update_role, (data['name'], data['id']))

        # 2. GESTIÓN DE PERMISOS (Estrategia Soft Delete + Upsert)
        
        # A. "Resetear": Marcar todos los permisos actuales como inactivos
        sql_deactivate_perms = """
            UPDATE Documents.RolePermissions 
            SET isActive = 0, lastUpdate = GETDATE() 
            WHERE roleId = %s
        """
        cursor.execute(sql_deactivate_perms, (data['id'],))

        # B. "Upsert": Reactivar los seleccionados o insertar nuevos
        sql_update_perm = """
            UPDATE Documents.RolePermissions
            SET isActive = 1, lastUpdate = GETDATE()
            WHERE roleId = %s AND permissionId = %s
        """
        
        sql_insert_perm = """
            INSERT INTO Documents.RolePermissions (roleId, permissionId, isActive, lastUpdate)
            VALUES (%s, %s, 1, GETDATE())
        """

        for permiso in data.get('permisos', []):
            permission_id = permiso['id']
            
            # Intentamos actualizar (reactivar)
            cursor.execute(sql_update_perm, (data['id'], permission_id))
            
            # Si rowcount es 0, significa que la relación no existía, así que insertamos
            if cursor.rowcount == 0:
                cursor.execute(sql_insert_perm, (data['id'], permission_id))

        # 3. GESTIÓN DE USUARIOS (Misma estrategia)
        # A. "Resetear": Marcar todos los usuarios actuales como inactivos
        sql_deactivate_users = """
            UPDATE Documents.UserRoles 
            SET isActive = 0, lastUpdate = GETDATE() 
            WHERE roleId = %s
        """
        cursor.execute(sql_deactivate_users, (data['id'],))

        # B. "Upsert": Reactivar o Insertar
        sql_update_user = """
            UPDATE Documents.UserRoles
            SET isActive = 1, lastUpdate = GETDATE()
            WHERE roleId = %s AND userId = %s
        """
        
        sql_insert_user = """
            INSERT INTO Documents.UserRoles (roleId, userId, isActive, lastUpdate)
            VALUES (%s, %s, 1, GETDATE())
        """

        for usuario in data.get('usuarios', []):
            user_id = usuario['id']
            
            # Intentamos actualizar (reactivar)
            cursor.execute(sql_update_user, (data['id'], user_id))
            
            # Si no existía, insertamos
            if cursor.rowcount == 0:
                cursor.execute(sql_insert_user, (data['id'], user_id))

        connection.commit()
        return True

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error editando el Rol: {e}")
        raise e

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def create_document(data, file_url):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # --- 0. PREPARACIÓN DE IDs DE EMPRESA ---
        raw_company = data.get('companyId')
        company_ids = raw_company if isinstance(raw_company, list) else [raw_company]

        # 1. OBTENER NOMBRES (Para el Correo y Logs)
        sql_dtype_name = "SELECT Name FROM Documents.DocumentType WHERE TypeID = %s"
        cursor.execute(sql_dtype_name, (data['docTypeId'],))
        dt_row = cursor.fetchone()
        doc_type_name = dt_row['Name'] if dt_row else 'Desconocido'

        # Obtenemos los nombres de las Compañías (Concatenados)
        if company_ids:
            placeholders = ', '.join(['%s'] * len(company_ids))
            sql_comp_names = f"SELECT Name FROM Documents.Company WHERE CompanyID IN ({placeholders})"
            cursor.execute(sql_comp_names, tuple(company_ids))
            comp_rows = cursor.fetchall()
            company_names_list = [row['Name'] for row in comp_rows]
            company_name_str = ", ".join(company_names_list) # Ej: "Empresa A, Empresa B"
        else:
            company_name_str = "Sin Empresa Asignada"

        # 2. INSERTAR DOCUMENTO (Cabecera)
        sql_doc = """
            INSERT INTO Documents.Document (TypeID, DocumentName)
            OUTPUT INSERTED.DocumentID
            VALUES (%s, %s)
        """
        # Enviamos docTypeId y documentName (que ahora viene separado en el JSON)
        cursor.execute(sql_doc, (data['docTypeId'], data['documentName']))
        row = cursor.fetchone()

        if not row:
            raise Exception('No se pudo obtener el ID del documento creado')

        inserted_id = row['DocumentID']

        # 3. INSERTAR RELACIÓN DOCUMENTO - COMPAÑÍA
        sql_doc_company = """
            INSERT INTO Documents.DocumentCompanies (DocumentID, CompanyID)
            VALUES (%s, %s)
        """
        for comp_id in company_ids:
            if comp_id: # Validación simple para no insertar nulos
                cursor.execute(sql_doc_company, (inserted_id, comp_id))

        # 4. INSERTAR VALORES DINÁMICOS
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (FieldID, DocumentID, Value)
            VALUES (%s, %s, %s)
        """
        
        sql_get_field_name = "SELECT Name FROM Documents.TypeFields WHERE FieldID = %s"

        fields_for_email = []

        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            value = field.get('value')
            
            # Insertar Valor
            if field_id is not None:
                cursor.execute(sql_insert_value, (field_id, inserted_id, value))
                
                # Obtener Nombre del Campo para el Correo (Opcional: podrías optimizarlo con un JOIN previo)
                cursor.execute(sql_get_field_name, (field_id,))
                name_row = cursor.fetchone()
                field_name = name_row['Name'] if name_row else f"Campo {field_id}"
                
                fields_for_email.append({
                    'nombre': field_name,
                    'valor': value
                })

        # 5. INSERTAR ANEXO
        if file_url:
            sql_insert_annex = """
                INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
                VALUES (%s, %s, GETDATE())
            """
            cursor.execute(sql_insert_annex, (inserted_id, file_url))

        connection.commit()

        # 📧 NOTIFICACIÓN POR CORREO
        try:
            sender_email = os.environ.get("MAIL_USERNAME_DOCUMENTS")
            email_password = os.environ.get("MAIL_PASSWORD_DOCUMENTS")
            recipient_admin = os.environ.get("MAIL_TEST_DOCUMENTS") 

            if sender_email and email_password and recipient_admin:
                
                email_context = {
                    'user_name': 'Administrador', 
                    'doc_type': doc_type_name,
                    'company': company_name_str, # Ahora pasamos la cadena concatenada
                    'fields': fields_for_email,
                    'file_url': file_url
                }

                subject = f"Nuevo Documento Creado: {doc_type_name} - {company_name_str}"
                html_body = create_new_doc_html(email_context)

                send_email(
                    subject=subject,
                    body_html=html_body,
                    sender_email=sender_email,
                    email_password=email_password,
                    receiver_emails=[recipient_admin],
                    attachments=None 
                )
                # print(f"Correo de notificación enviado a {recipient_admin}")

        except Exception as email_error:
            print(f"Documento creado, pero falló el envío de correo: {email_error}")

        # Retornamos datos útiles para el frontend (incluyendo el nombre del documento)
        return {
            'document_id': inserted_id,
            'document_name': data['documentName'], # Confirmamos el nombre guardado
            'annex_url': file_url
        }

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error creando el Documento: {e}")
        raise e
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def edit_document(data, new_file_url=None):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # 1. ACTUALIZAR NOMBRE DEL DOCUMENTO (Si cambió)
        get_current_doc_name_sql = """
            SELECT DocumentName
            FROM Documents.Document
            WHERE DocumentID = %s
        """
        cursor.execute(get_current_doc_name_sql, (data['id'],))
        current_doc_row = cursor.fetchone()

        if current_doc_row:
            current_name = current_doc_row['DocumentName']
            
            if data.get('documentName') and data['documentName'] != current_name:
                sql_doc_name_update = """
                    UPDATE Documents.Document
                    SET DocumentName = %s
                    WHERE DocumentID = %s
                """
                cursor.execute(sql_doc_name_update, (data['documentName'], data['id']))
        else:
            raise ValueError(f"El documento ID {data['id']} no existe.")

        # --- 2. ACTUALIZAR COMPAÑÍAS ---
        # Verificamos si la clave 'companyId' existe en el diccionario 'data'.
        # Esto permite editar otros campos sin tocar las compañías si el frontend no envía el campo.
        if 'companyId' in data:
            raw_company = data['companyId']
            # Normalizamos a lista (puede venir un int o una lista de ints)
            company_ids = raw_company if isinstance(raw_company, list) else [raw_company]

            # A. Borrar relaciones existentes (Estrategia: Borrón y cuenta nueva)
            sql_delete_rels = "DELETE FROM Documents.DocumentCompanies WHERE DocumentID = %s"
            cursor.execute(sql_delete_rels, (data['id'],))

            # B. Insertar las nuevas (si la lista no está vacía)
            if company_ids:
                sql_insert_rel = """
                    INSERT INTO Documents.DocumentCompanies (DocumentID, CompanyID) 
                    VALUES (%s, %s)
                """
                for comp_id in company_ids:
                    if comp_id: # Validación para no insertar nulos/vacíos
                        cursor.execute(sql_insert_rel, (data['id'], comp_id))

        # 3. SQLs preparados para Campos
        sql_update_value = """
            UPDATE Documents.FieldValue
            SET Value = %s
            WHERE FieldID = %s AND DocumentID = %s
        """
        
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (Value, FieldID, DocumentID)
            VALUES (%s, %s, %s)
        """

        # 4. ACTUALIZAR O INSERTAR VALORES (Lógica UPSERT)
        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            new_value = field.get('value')
            
            # A. Intentamos actualizar
            cursor.execute(sql_update_value, (new_value, field_id, data['id']))

            # B. Si no se actualizó nada (rowcount 0), insertamos
            if cursor.rowcount == 0:
                cursor.execute(sql_insert_value, (new_value, field_id, data['id']))

        # 5. ACTUALIZAR ARCHIVO ADJUNTO (Si se subió uno nuevo)
        if new_file_url:
            sql_update_annex = """
                UPDATE Documents.DocumentAnnex
                SET AnnexURL = %s, Date = GETDATE()
                WHERE DocumentID = %s
            """
            cursor.execute(sql_update_annex, (new_file_url, data['id']))
            
            if cursor.rowcount == 0:
                sql_insert_annex = """
                    INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
                    VALUES (%s, %s, GETDATE())
                """
                cursor.execute(sql_insert_annex, (data['id'], new_file_url))

        connection.commit()
        
        # Devolvemos el nombre para actualizar el estado en el frontend inmediatamente
        return {
            'document_id': data['id'],
            'document_name': data.get('documentName', current_name)
        }

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error actualizando el Documento: {e}")
        raise e 
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_documents_by_type_id(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
            SELECT 
                D.DocumentID AS id, 
                D.TypeID AS typeId, 
                DT.Name AS docTypeName,
                D.DocumentName AS DocumentName,
                
                -- SUBQUERY para obtener los nombres de las compañías concatenados
                (
                    SELECT STRING_AGG(C.Name, ', ') 
                    FROM Documents.DocumentCompanies DC
                    JOIN Documents.Company C ON DC.CompanyID = C.CompanyID
                    WHERE DC.DocumentID = D.DocumentID
                ) AS companyName,
                
                -- También es útil traer los IDs de las compañías por si necesitas filtrar en el front
                (
                    SELECT STRING_AGG(CAST(DC.CompanyID AS VARCHAR), ',') 
                    FROM Documents.DocumentCompanies DC
                    WHERE DC.DocumentID = D.DocumentID
                ) AS companyIds,

                -- Fecha del anexo
                A.Date AS annexDate

            FROM Documents.Document D

            -- JOIN para obtener el nombre del tipo
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID

            -- YA NO HACEMOS JOIN DIRECTO A COMPANY AQUÍ para evitar duplicados
            -- La relación se maneja en las subqueries de arriba

            -- LEFT JOIN para el anexo
            LEFT JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID

            -- FILTRO POR TIPO DE DOCUMENTO
            WHERE D.TypeID = %s
        """

        cursor.execute(sql, (data['docType_id'],))
        documents = cursor.fetchall()
        
        return documents
    
    except Exception as e:
        print(f"Error SQL en get_documents_by_type_id: {e}")
        # Retornamos lista vacía en caso de error para no romper el frontend, 
        # aunque idealmente se debería propagar la excepción.
        return []
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_all_documents_lists(page=1, page_size=20):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Calculamos el desplazamiento para la paginación
        offset = (page - 1) * page_size

        sql = """
            SELECT 
                D.DocumentID, 
                D.TypeID, 
                DT.Name AS TypeName,
                D.DocumentName AS DocumentName,
                
                -- CAMBIO PRINCIPAL: Subconsulta para obtener nombres de empresas concatenados
                (
                    SELECT STRING_AGG(C.Name, ', ') 
                    FROM Documents.DocumentCompanies DC
                    JOIN Documents.Company C ON DC.CompanyID = C.CompanyID
                    WHERE DC.DocumentID = D.DocumentID
                ) AS CompanyName, 

                DA.Date AS AnnexDate,
                FV.Value AS ExpirationDate, -- Campo dinámico de vencimiento
                
                -- El conteo total se mantiene correcto porque no hay duplicidad de filas
                COUNT(*) OVER() as TotalCount 

            FROM Documents.Document D

            -- Join para el Tipo de Documento
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID

            -- Join para el Anexo
            LEFT JOIN Documents.DocumentAnnex DA ON D.DocumentID = DA.DocumentID

            -- Join para Fecha de Vencimiento (Mantenemos tu lógica)
            -- NOTA: Si un documento tuviera 2 campos que coinciden con el LIKE, esto duplicaría filas.
            -- Si eso pasa, avísame para cambiarlo a un OUTER APPLY.
            LEFT JOIN Documents.FieldValue FV ON D.DocumentID = FV.DocumentID 
                AND FV.FieldID IN (
                    SELECT FieldID FROM Documents.TypeFields 
                    WHERE Name LIKE '%Vencimiento%' OR Name LIKE '%Fecha%Venc%'
                )
        """

        params = []

        # Ordenamiento y Paginación (Crucial para velocidad)
        sql += """
        ORDER BY D.DocumentID DESC
        OFFSET %s ROWS
        FETCH NEXT %s ROWS ONLY
        """
        params.extend([offset, page_size])

        cursor.execute(sql, tuple(params))
        documents = cursor.fetchall()

        # Si no hay documentos, devolvemos estructura vacía
        if not documents:
            return {'data': [], 'total': 0, 'page': page}

        # El TotalCount viene repetido en cada fila (truco de SQL), lo sacamos del primero
        total_records = documents[0]['TotalCount'] if documents else 0

        # Limpiamos el TotalCount de cada objeto para no ensuciar el JSON
        for doc in documents:
            doc.pop('TotalCount', None)
        
        result = {
            'data': documents, 
            'total': total_records,
            'page': page,
            'pageSize': page_size
        }

        return result
    
    except Exception as e:
        print(f"Error SQL en get_all_documents_lists: {e}")
        return {'data': [], 'total': 0, 'error': str(e)}
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_document_by_id(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # 1. OBTENER CABECERA (Datos fijos + Anexo)
        sql_header = """
            SELECT 
                D.DocumentID, 
                D.TypeID, 
                DT.Name AS TypeName,
                D.DocumentName AS DocumentName,
                
                -- SUBCONSULTA: Concatena los nombres de las empresas (Ej: "Empresa A, Empresa B")
                (
                    SELECT STRING_AGG(C.Name, ', ') 
                    FROM Documents.DocumentCompanies DC
                    JOIN Documents.Company C ON DC.CompanyID = C.CompanyID
                    WHERE DC.DocumentID = D.DocumentID
                ) AS CompanyName,

                -- OPCIONAL PERO RECOMENDADO: Traer también los IDs para poder pre-cargar el formulario de edición
                (
                    SELECT STRING_AGG(CAST(DC.CompanyID AS VARCHAR), ',') 
                    FROM Documents.DocumentCompanies DC
                    WHERE DC.DocumentID = D.DocumentID
                ) AS CompanyIDs,

                DA.AnnexURL

            FROM Documents.Document D

            -- Join para nombre del tipo
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
            -- Left Join para el anexo
            LEFT JOIN Documents.DocumentAnnex DA ON D.DocumentID = DA.DocumentID

            WHERE D.DocumentID = %s 
        """
        
        cursor.execute(sql_header, (data['id'],))
        doc_header = cursor.fetchone()

        if not doc_header:
            return None

        # 2. OBTENER VALORES DE LOS CAMPOS (Datos dinámicos)
        sql_values = """
            SELECT 
                TF.Name AS FieldName, 
                FV.Value
            FROM Documents.FieldValue FV
            JOIN Documents.TypeFields TF ON FV.FieldID = TF.FieldID
            WHERE FV.DocumentID = %s
        """
        
        cursor.execute(sql_values, (data['id'],))
        field_rows = cursor.fetchall()

        # 3. TRANSFORMACIÓN DE DATOS (Para el Frontend)
        
        fields_data_dict = {row['FieldName']: row['Value'] for row in field_rows}
        raw_company_ids = doc_header.get('CompanyIDs', '')
        company_ids_list = [int(x) for x in raw_company_ids.split(',')] if raw_company_ids else []

        # Construimos el objeto final
        document_full = {
            'DocumentID': doc_header['DocumentID'],
            'DocumentName': doc_header['DocumentName'],
            'TypeID': doc_header['TypeID'],
            'TypeName': doc_header['TypeName'],
            'CompanyIDs': company_ids_list,
            'CompanyID': company_ids_list[0] if company_ids_list else None,
            'CompanyName': doc_header['CompanyName'],
            'AnnexURL': doc_header['AnnexURL'],
            'fieldsData': fields_data_dict # <--- Esto es lo que usa el Modal para rellenar inputs
        }

        return document_full

    except Exception as e:
        print(f"Error obteniendo detalle del documento ID {data.get('id')}: {e}")
        raise e # Relanzamos para que la ruta capture el 500
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def send_documents(email_data, full_documents_data):
    sender_email = os.environ.get('MAIL_USERNAME_DOCUMENTS')
    email_password = os.environ.get('MAIL_PASSWORD_DOCUMENTS')

    if not sender_email or not email_password:
        raise Exception("Credenciales de correo no configuradas en el servidor.")

    try:
        # ENVÍO DE CORREO A LOS DESTINATARIOS
        html_body_client = create_custom_email_html(email_data, full_documents_data)
        recipients_list = email_data.get('recipients', [])
        subject_client = email_data.get('subject', 'Envío de Documentos')

        send_email(
            subject=subject_client,
            body_html=html_body_client,
            sender_email=sender_email,
            email_password=email_password,
            receiver_emails=recipients_list,
            attachments=None
        )

        print(f'--> Correo enviado a los destinatarios: {recipients_list}')

        # ENVÍO DE CORREO A LA ADMINISTRACIÓN
        try:
            notification_recipient = os.environ.get('MAIL_TEST_DOCUMENTS') or sender_email

            if notification_recipient:
                notification_context = {
                    'send_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender_user': email_data.get('senderName', 'Usuario Gipsy'),
                    'sender_email': sender_email,
                    'recipients': recipients_list,
                    'subject': subject_client,
                    'body_message': email_data.get('body', '')
                }

                html_body_notify = create_send_notification_html(notification_context)
                subject_notify = f"Notificación de Envío de Documentos - {subject_client}"

                send_email(
                    subject=subject_notify,
                    body_html=html_body_notify,
                    sender_email=sender_email,
                    email_password=email_password,
                    receiver_emails=[notification_recipient],
                    attachments=None
                )

                print(f'--> Correo enviado a la administración: {notification_recipient}')

                return True

        except Exception as admin_e:
            print(f"Error enviando notificación a la administración: {admin_e}")
            return True

    except Exception as e:
        print(f"Error enviando documentos por correo: {e}")
        raise e