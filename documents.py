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

        # C. Campos (Fields)
        sql_document_fields = """
        INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision)
        OUTPUT INSERTED.FieldID
        VALUES (%s, %s, %s, %s, %s)
        """

        sql_specific_values = """
        INSERT INTO Documents.SpecificValue (FieldID, Value)
        VALUES (%s, %s)
        """

        # Diccionario para traducir tipos de datos técnicos a texto legible en el correo
        type_translation = {
            'text': 'Texto Corto', 'textarea': 'Texto Largo', 
            'int': 'Numérico Entero', 'float': 'Decimal', 
            'date': 'Fecha', 'specificValues': 'Lista de Opciones'
        }
        
        # Lista para guardar los campos formateados y usarlos en el correo después
        fields_for_email = []

        for field in data.get('fields', []):
            f_len = field.get('length') if field.get('length') else 0
            f_prec = field.get('precision') if field.get('precision') else 0

            # Guardamos datos para el correo
            fields_for_email.append({
                'nombre': field['name'],
                'tipo_dato': type_translation.get(field['type'], field['type']),
                'longitud': f_len if f_len > 0 else 'N/A',
                'precision': f_prec if f_prec > 0 else 'N/A'
            })

            cursor.execute(sql_document_fields, (
                inserted_id, 
                field['name'], 
                field['type'], 
                f_len, 
                f_prec
            ))
            
            if field['type'] == 'specificValues':
                field_row = cursor.fetchone()
                if field_row:
                    field_id = field_row['FieldID']
                    for value in field.get('specificValues', []):
                        val_text = value['value'] if isinstance(value, dict) else value
                        cursor.execute(sql_specific_values, (field_id, val_text))
        
        connection.commit()

        # ==========================================
        # 3. NOTIFICACIÓN POR CORREO (Usando tu función)
        # ==========================================
        try:
            # A. Obtener credenciales de variables de entorno
            sender_email = os.environ.get("MAIL_USERNAME_DOCUMENTS") # O MAIL_USERNAME_RECEIPT según tu .env
            email_password = os.environ.get("MAIL_PASSWORD_DOCUMENTS")
            recipient_admin = os.environ.get("MAIL_RECIPIENT_TEST") # Correo del administrador que recibe la alerta

            if sender_email and email_password and recipient_admin:
                
                # B. Preparar datos para tu plantilla HTML (create_doc_type_html)
                email_context = {
                    'doc_type_name': data['name'],
                    'alias': data['alias'],
                    'description': data.get('description', 'Sin descripción'),
                    'fields': fields_for_email
                }

                # C. Generar HTML
                subject = f"Nuevo Tipo de Documento Creado: {data['name']}"
                html_body = create_doc_type_html(email_context)

                # D. Enviar usando TU función
                # Nota: pasamos [recipient_admin] como lista, y attachments=None
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
            # Capturamos error de correo para NO romper la creación del documento
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

        sql = """
        SELECT DT.TypeID AS id, DT.Name AS name, DT.ShortName AS shortName, DT.Description AS description,
               TF.FieldID AS fieldId, TF.Name AS fieldName, TF.DataType AS fieldType, TF.Length AS fieldLength, TF.Precision AS fieldPrecision,
               SV.ValueID AS valueId, SV.Value AS value
        FROM Documents.DocumentType DT
        LEFT JOIN Documents.TypeFields TF ON DT.TypeID = TF.DocumentTypeID
        LEFT JOIN Documents.SpecificValue SV ON TF.FieldID = SV.FieldID
        WHERE DT.TypeID = %s
        """

        cursor.execute(sql, (data['id'],))
        rows = cursor.fetchall()

        #print(f'Hola desde documents.py: {rows}')
        
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
            if field_id and field_id not in fields_map:
                fields_map[field_id] = {
                    'id': field_id,
                    'name': row['fieldName'],
                    'type': row['fieldType'],
                    'length': row['fieldLength'],
                    'precision': row['fieldPrecision'],
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
        # Necesitamos saber cómo se llama AHORA para poder encontrar su permiso correspondiente
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

        # 2. ACTUALIZAR EL PERMISO (Usando el nombre viejo que guardamos)
        # Buscamos el permiso que tenga el old_doc_name y le ponemos el nuevo data['name']
        sql_access_control = """
            UPDATE AccessControl.Permissions
            SET name = %s
            WHERE name = %s
        """
        cursor.execute(sql_access_control, (data['name'], old_doc_name))

        # 3. DEFINIR SQLs DE CAMPOS
        sql_update_field = """
            UPDATE Documents.TypeFields
            SET Name = %s, DataType = %s, Length = %s, Precision = %s
            WHERE FieldID = %s AND DocumentTypeID = %s
        """
        
        sql_insert_field = """
            INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision)
            VALUES (%s, %s, %s, %s, %s)
        """ 

        sql_get_new_id = "SELECT SCOPE_IDENTITY() AS new_id"
        
        sql_insert_value = "INSERT INTO Documents.SpecificValue (FieldID, Value) VALUES (%s, %s)"
        sql_delete_values = "DELETE FROM Documents.SpecificValue WHERE FieldID = %s"

        # 4. PROCESAR CAMPOS
        for field in data.get('fields', []):
            field_id = field.get('id')

            if field_id is None:
                # --- INSERTAR ---
                cursor.execute(sql_insert_field, (
                    data['id'], 
                    field['name'], 
                    field['type'], 
                    field.get('length', 0), 
                    field.get('precision', 0)
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

        # 1. OBTENER NOMBRES (Para el Correo y Logs)
        sql_names = """
            SELECT 
                DT.Name AS DocTypeName,
                C.Name AS CompanyName
            FROM Documents.DocumentType DT
            JOIN Documents.Company C ON C.CompanyID = %s
            WHERE DT.TypeID = %s
        """
        cursor.execute(sql_names, (data['companyId'], data['docTypeId']))
        names_row = cursor.fetchone()
        
        doc_type_name = names_row['DocTypeName'] if names_row else 'Desconocido'
        company_name = names_row['CompanyName'] if names_row else 'Desconocida'

        # 2. INSERTAR DOCUMENTO (Cabecera)
        sql_doc = """
            INSERT INTO Documents.Document (TypeID, CompanyID)
            OUTPUT INSERTED.DocumentID
            VALUES (%s, %s)
        """
        cursor.execute(sql_doc, (data['docTypeId'], data['companyId']))
        row = cursor.fetchone()

        if not row:
            raise Exception('No se pudo obtener el ID del documento creado')

        inserted_id = row['DocumentID']

        # 3. INSERTAR VALORES Y PREPARAR DATOS CORREO
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (FieldID, DocumentID, Value)
            VALUES (%s, %s, %s)
        """
        
        # Consulta auxiliar para obtener el nombre del campo dado su ID
        sql_get_field_name = "SELECT Name FROM Documents.TypeFields WHERE FieldID = %s"

        fields_for_email = []

        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            value = field.get('value')
            
            # Insertar Valor
            if field_id is not None:
                cursor.execute(sql_insert_value, (field_id, inserted_id, value))
                
                # Obtener Nombre del Campo para el Correo
                cursor.execute(sql_get_field_name, (field_id,))
                name_row = cursor.fetchone()
                field_name = name_row['Name'] if name_row else f"Campo {field_id}"
                
                fields_for_email.append({
                    'nombre': field_name,
                    'valor': value
                })

        # 4. INSERTAR ANEXO
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
                    'user_name': 'Administrador', # O pasar el usuario real si lo tienes en 'data'
                    'doc_type': doc_type_name,
                    'company': company_name,
                    'fields': fields_for_email,
                    'file_url': file_url
                }

                subject = f"Nuevo Documento Creado: {doc_type_name} - {company_name}"
                html_body = create_new_doc_html(email_context)

                send_email(
                    subject=subject,
                    body_html=html_body,
                    sender_email=sender_email,
                    email_password=email_password,
                    receiver_emails=[recipient_admin],
                    attachments=None 
                )
                print(f"Correo de notificación enviado a {recipient_admin}")

        except Exception as email_error:
            print(f"Documento creado, pero falló el envío de correo: {email_error}")

        return inserted_id

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

        # SQLs preparados
        sql_update_value = """
            UPDATE Documents.FieldValue
            SET Value = %s
            WHERE FieldID = %s AND DocumentID = %s
        """
        
        # Necesitamos el INSERT por si el campo estaba vacío antes
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (Value, FieldID, DocumentID)
            VALUES (%s, %s, %s)
        """

        # 1. ACTUALIZAR O INSERTAR VALORES (Lógica UPSERT)
        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            new_value = field.get('value')
            
            # A. Intentamos actualizar
            cursor.execute(sql_update_value, (new_value, field_id, data['id']))

            # B. Si no se actualizó nada (rowcount es 0), significa que el campo no existía. Lo insertamos.
            if cursor.rowcount == 0:
                cursor.execute(sql_insert_value, (new_value, field_id, data['id']))

        # 2. ACTUALIZAR ARCHIVO ADJUNTO
        if new_file_url:
            sql_update_annex = """
                UPDATE Documents.DocumentAnnex
                SET AnnexURL = %s, Date = GETDATE()
                WHERE DocumentID = %s
            """
            cursor.execute(sql_update_annex, (new_file_url, data['id']))
            
            # Misma lógica: Si no existía anexo, lo creamos
            if cursor.rowcount == 0:
                sql_insert_annex = """
                    INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
                    VALUES (%s, %s, GETDATE())
                """
                cursor.execute(sql_insert_annex, (data['id'], new_file_url))

        connection.commit()
        return True

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error actualizando el Documento: {e}")
        raise e # Re-lanzar para que el endpoint sepa que falló
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_documents_lists(data):
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
            D.CompanyID AS companyId, 
            C.Name AS companyName,  
            -- Fecha del anexo (puede ser null si no se ha subido)
            A.Date AS annexDate
        FROM Documents.Document D
        
        -- JOIN para obtener el nombre del tipo (útil para el frontend)
        JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
        
        -- JOIN para obtener el nombre de la empresa
        JOIN Documents.Company C ON D.CompanyID = C.CompanyID
        
        -- LEFT JOIN CRÍTICO: Trae el documento aunque no tenga anexo en la tabla DocumentAnnex
        LEFT JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID
        
        -- FILTRO POR ID (Numérico)
        WHERE D.TypeID = %s
        """

        cursor.execute(sql, (data['docType_id'],))
        documents = cursor.fetchall()
        
        return documents
    
    except Exception as e:
        print(f"Error SQL en get_documents_lists: {e}")
        # Retornamos lista vacía en caso de error para no romper el frontend, 
        # aunque idealmente se debería propagar la excepción.
        return []
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_all_documents_lists():
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        SELECT 
            D.DocumentID, 
            D.TypeID, 
            DT.Name AS TypeName,
            D.CompanyID, 
            C.Name AS CompanyName, 
            DA.Date AS AnnexDate
        FROM Documents.Document D
        JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
        JOIN Documents.Company C ON D.CompanyID = C.CompanyID
        LEFT JOIN Documents.DocumentAnnex DA ON D.DocumentID = DA.DocumentID
        """

        cursor.execute(sql)
        documents = cursor.fetchall()
        
        return documents
    
    except Exception as e:
        print(f"Error SQL en get_all_documents_lists: {e}")
        # Retornamos lista vacía en caso de error para no romper el frontend, 
        # aunque idealmente se debería propagar la excepción.
        return []
    
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
                D.CompanyID, 
                C.Name AS CompanyName, 
                DA.AnnexURL
            FROM Documents.Document D
            -- Join para nombre del tipo
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
            -- Join para nombre de la empresa
            JOIN Documents.Company C ON D.CompanyID = C.CompanyID
            -- Left Join para el anexo (puede no tener, o no haberse subido aún)
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

        # Construimos el objeto final
        document_full = {
            'DocumentID': doc_header['DocumentID'],
            'TypeID': doc_header['TypeID'],
            'TypeName': doc_header['TypeName'],
            'CompanyID': doc_header['CompanyID'],
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