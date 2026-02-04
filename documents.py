import os
import json
import pymssql

from datetime import datetime
from collections import Counter
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
        print(f"Error al obtener las entidades: {e}")
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
        INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision, isMandatory)
        OUTPUT INSERTED.FieldID
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        sql_specific_values = """
        INSERT INTO Documents.SpecificValue (FieldID, Value)
        VALUES (%s, %s)
        """

        type_translation = {
            'text': 'Texto Corto', 'textarea': 'Texto Largo', 
            'int': 'Numérico Entero', 'float': 'Decimal', 'money': 'Moneda',
            'date': 'Fecha', 'specificValues': 'Lista de Opciones'
        }
        
        fields_for_email = []

        for field in data.get('fields', []):
            f_len = field.get('length') if field.get('length') else 0
            f_prec = field.get('precision') if field.get('precision') else 0
            is_mandatory = field.get('isRequired', 0)

            fields_for_email.append({
                'nombre': field['name'],
                'tipo_dato': type_translation.get(field['type'], field['type']),
                'longitud': f_len if f_len > 0 else 'N/A',
                'precision': f_prec if f_prec > 0 else 'N/A',
                'obligatorio': 'Sí' if is_mandatory == 1 else 'No'
            })

            cursor.execute(sql_document_fields, (
                inserted_id, 
                field['name'], 
                field['type'], 
                f_len, 
                f_prec,
                is_mandatory
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

            # --- DEFINIR LA COPIA OCULTA (BCC) ---
            bcc_list = ['bibliotecagipsy@outlook.com']

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
                    attachments=None,
                    bcc=bcc_list # <--- AQUÍ PASAMOS LA COPIA OCULTA
                )
                print(f"Correo de notificación enviado exitosamente a {recipient_admin} (con copia oculta)")
            
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
        AND UR.isActive = 1 -- (Opcional) Recomendado si manejas borrado lógico
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
        AND UR.isActive = 1 -- (Opcional) Recomendado si manejas borrado lógico
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

        """
        # 2. GESTIÓN DE PERMISOS (Estrategia Soft Delete + Upsert)
        
        # A. "Resetear": Marcar todos los permisos actuales como inactivos
        sql_deactivate_perms = 
            UPDATE Documents.RolePermissions 
            SET isActive = 0, lastUpdate = GETDATE() 
            WHERE roleId = %s
        
        cursor.execute(sql_deactivate_perms, (data['id'],))

        # B. "Upsert": Reactivar los seleccionados o insertar nuevos
        sql_update_perm = 
            UPDATE Documents.RolePermissions
            SET isActive = 1, lastUpdate = GETDATE()
            WHERE roleId = %s AND permissionId = %s
        
        
        sql_insert_perm = 
            INSERT INTO Documents.RolePermissions (roleId, permissionId, isActive, lastUpdate)
            VALUES (%s, %s, 1, GETDATE())
        

        for permiso in data.get('permisos', []):
            permission_id = permiso['id']
            
            # Intentamos actualizar (reactivar)
            cursor.execute(sql_update_perm, (data['id'], permission_id))
            
            # Si rowcount es 0, significa que la relación no existía, así que insertamos
            if cursor.rowcount == 0:
                cursor.execute(sql_insert_perm, (data['id'], permission_id))
        """

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

        if company_ids:
            placeholders = ', '.join(['%s'] * len(company_ids))
            sql_comp_names = f"SELECT Name FROM Documents.Company WHERE CompanyID IN ({placeholders})"
            cursor.execute(sql_comp_names, tuple(company_ids))
            comp_rows = cursor.fetchall()
            company_names_list = [row['Name'] for row in comp_rows]
            company_name_str = ", ".join(company_names_list)
        else:
            company_name_str = "Sin Empresa Asignada"

        # 2. INSERTAR DOCUMENTO (Cabecera)
        sql_doc = """
            INSERT INTO Documents.Document (TypeID, DocumentName)
            OUTPUT INSERTED.DocumentID
            VALUES (%s, %s)
        """
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
            if comp_id: 
                cursor.execute(sql_doc_company, (inserted_id, comp_id))

        # 4. INSERTAR VALORES DINÁMICOS
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (FieldID, DocumentID, Value)
            VALUES (%s, %s, %s)
        """
        
        # Modificamos esta consulta para traer también el Tipo de Dato (DataType)
        # Esto nos ayuda a formatear el correo mejor (ej: mostrar 'Sí' en lugar de '1')
        sql_get_field_info = "SELECT Name, DataType FROM Documents.TypeFields WHERE FieldID = %s"

        fields_for_email = []

        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            value = field.get('value')
            
            # --- CORRECCIÓN PARA BOOLEANOS ---
            if isinstance(value, bool):
                value = '1' if value else '0'
            
            # Insertar Valor
            if field_id is not None:
                cursor.execute(sql_insert_value, (field_id, inserted_id, value))
                
                # Obtener Nombre y Tipo para el Correo
                cursor.execute(sql_get_field_info, (field_id,))
                field_info = cursor.fetchone()
                
                if field_info:
                    field_name = field_info['Name']
                    field_type = field_info['DataType']
                    
                    # Formatear valor para el correo (Visualización amigable)
                    display_value = value
                    if field_type == 'bool' or field_type == 'bit': # Ajusta según tu BD
                        display_value = 'Sí' if value == '1' else 'No'
                else:
                    field_name = f"Campo {field_id}"
                    display_value = value
                
                fields_for_email.append({
                    'nombre': field_name,
                    'valor': display_value
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
            bcc_list = ['bibliotecagipsy@outlook.com'] 

            if sender_email and email_password and recipient_admin:
                
                email_context = {
                    'user_name': 'Administrador', 
                    'doc_type': doc_type_name,
                    'company': company_name_str,
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
                    attachments=None,
                    bcc=bcc_list
                )

        except Exception as email_error:
            print(f"Documento creado, pero falló el envío de correo: {email_error}")

        return {
            'document_id': inserted_id,
            'document_name': data['documentName'], 
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

        # Variable para guardar el nombre actual o el nuevo
        current_name = ""

        if current_doc_row:
            current_name = current_doc_row['DocumentName']
            
            if data.get('documentName') and data['documentName'] != current_name:
                sql_doc_name_update = """
                    UPDATE Documents.Document
                    SET DocumentName = %s
                    WHERE DocumentID = %s
                """
                cursor.execute(sql_doc_name_update, (data['documentName'], data['id']))
                current_name = data['documentName'] # Actualizamos la variable local
        else:
            raise ValueError(f"El documento ID {data['id']} no existe.")

        # --- 2. ACTUALIZAR COMPAÑÍAS ---
        if 'companyId' in data:
            raw_company = data['companyId']
            company_ids = raw_company if isinstance(raw_company, list) else [raw_company]

            # A. Borrar relaciones existentes
            sql_delete_rels = "DELETE FROM Documents.DocumentCompanies WHERE DocumentID = %s"
            cursor.execute(sql_delete_rels, (data['id'],))

            # B. Insertar las nuevas
            if company_ids:
                sql_insert_rel = """
                    INSERT INTO Documents.DocumentCompanies (DocumentID, CompanyID) 
                    VALUES (%s, %s)
                """
                for comp_id in company_ids:
                    if comp_id: 
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
            
            # --- CORRECCIÓN PARA BOOLEANOS ---
            # Convertimos True/False a '1'/'0' para la BD
            if isinstance(new_value, bool):
                new_value = '1' if new_value else '0'
            
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
        
        return {
            'document_id': data['id'],
            'document_name': current_name
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

        # PASO 1: Obtener la lista principal de documentos
        sql_docs = """
            SELECT 
                D.DocumentID AS id, 
                D.TypeID AS typeId, 
                DT.Name AS docTypeName,
                D.DocumentName AS DocumentName,
                
                -- Nombres de compañías concatenados
                (
                    SELECT STRING_AGG(C.Name, ', ') 
                    FROM Documents.DocumentCompanies DC
                    JOIN Documents.Company C ON DC.CompanyID = C.CompanyID
                    WHERE DC.DocumentID = D.DocumentID
                ) AS companyName,
                
                -- IDs de compañías
                (
                    SELECT STRING_AGG(CAST(DC.CompanyID AS VARCHAR), ',') 
                    FROM Documents.DocumentCompanies DC
                    WHERE DC.DocumentID = D.DocumentID
                ) AS companyIds,

                A.Date AS annexDate,
                A.AnnexURL AS annexUrl

            FROM Documents.Document D
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
            LEFT JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID
            WHERE D.TypeID = %s
            ORDER BY D.DocumentID DESC -- Orden recomendado
        """
        cursor.execute(sql_docs, (data['docType_id'],))
        documents = cursor.fetchall()
        
        # Si no hay documentos, retornamos lista vacía inmediatamente
        if not documents:
            return []

        # PASO 2: Obtener los Campos Dinámicos (FieldValue)       
        # A. Extraemos todos los IDs de los documentos encontrados
        doc_ids = [d['id'] for d in documents]
        
        # B. Preparamos el query con IN (...) para traer campos solo de estos docs
        placeholders = ','.join(['%s'] * len(doc_ids))
        
        sql_fields = f"""
            SELECT 
                FV.DocumentID,
                TF.Name AS FieldName,
                FV.Value,
                TF.DataType -- Importante para convertir bools
            FROM Documents.FieldValue FV
            JOIN Documents.TypeFields TF ON FV.FieldID = TF.FieldID
            WHERE FV.DocumentID IN ({placeholders})
        """
        
        cursor.execute(sql_fields, tuple(doc_ids))
        all_fields = cursor.fetchall()

        # PASO 3: Unir datos en Python (Mapping)    
        # Creamos un diccionario para acceso rápido: { doc_id: { 'Campo1': 'Valor', ... } }
        fields_map = {}
        
        for row in all_fields:
            doc_id = row['DocumentID']
            field_name = row['FieldName']
            val = row['Value']
            dtype = row['DataType']

            # Conversión de Booleano (Igual que hicimos antes)
            if dtype == 'bool' or dtype == 'bit':
                val = True if val == '1' or val == 'true' else False

            # Inicializamos el dict del doc si no existe
            if doc_id not in fields_map:
                fields_map[doc_id] = {}
            
            fields_map[doc_id][field_name] = val

        # PASO 4: Inyectar fieldsData en cada documento
        for doc in documents:
            # Asignamos los campos correspondientes o un objeto vacío si no tiene
            doc['fieldsData'] = fields_map.get(doc['id'], {})
            
            # (Opcional) Procesar companyIds de string "1,2" a lista [1, 2]
            raw_ids = doc.get('companyIds')
            doc['companyIdsList'] = [int(x) for x in raw_ids.split(',')] if raw_ids else []

        return documents
    
    except Exception as e:
        print(f"Error en get_documents_by_type_id: {e}")
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
                
                -- CAMBIO PRINCIPAL: Subconsulta para obtener nombres de entidades concatenados
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

        # 1. CABECERA (Sin cambios)
        sql_header = """
            SELECT 
                D.DocumentID, D.TypeID, DT.Name AS TypeName, D.DocumentName,
                (SELECT STRING_AGG(C.Name, ', ') FROM Documents.DocumentCompanies DC JOIN Documents.Company C ON DC.CompanyID = C.CompanyID WHERE DC.DocumentID = D.DocumentID) AS CompanyName,
                (SELECT STRING_AGG(CAST(DC.CompanyID AS VARCHAR), ',') FROM Documents.DocumentCompanies DC WHERE DC.DocumentID = D.DocumentID) AS CompanyIDs,
                DA.AnnexURL
            FROM Documents.Document D
            JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
            LEFT JOIN Documents.DocumentAnnex DA ON D.DocumentID = DA.DocumentID
            WHERE D.DocumentID = %s
        """
        cursor.execute(sql_header, (data['id'],))
        doc_header = cursor.fetchone()

        if not doc_header: return None

        # 2. VALORES (MODIFICADO: Traemos el DataType para saber cuándo convertir)
        sql_values = """
            SELECT 
                TF.Name AS FieldName, 
                TF.DataType, -- <--- Necesitamos esto
                FV.Value
            FROM Documents.FieldValue FV
            JOIN Documents.TypeFields TF ON FV.FieldID = TF.FieldID
            WHERE FV.DocumentID = %s
        """
        cursor.execute(sql_values, (data['id'],))
        field_rows = cursor.fetchall()

        # 3. TRANSFORMACIÓN DE DATOS (Conversión inteligente)
        fields_data_dict = {}
        for row in field_rows:
            val = row['Value']
            dtype = row['DataType']

            # Si es bool, convertimos '1'/'0' a True/False real de Python
            if dtype == 'bool' or dtype == 'bit':
                val = True if val == '1' or val == 'true' else False
            
            fields_data_dict[row['FieldName']] = val

        # Procesar CompanyIDs
        raw_company_ids = doc_header.get('CompanyIDs', '')
        company_ids_list = [int(x) for x in raw_company_ids.split(',')] if raw_company_ids else []

        return {
            'DocumentID': doc_header['DocumentID'],
            'TypeID': doc_header['TypeID'],
            'TypeName': doc_header['TypeName'],
            'DocumentName': doc_header['DocumentName'],
            'CompanyIDs': company_ids_list, 
            'CompanyID': company_ids_list[0] if company_ids_list else None, 
            'CompanyName': doc_header['CompanyName'],
            'AnnexURL': doc_header['AnnexURL'],
            'fieldsData': fields_data_dict # Ahora lleva booleanos reales
        }

    except Exception as e:
        print(f"Error: {e}")
        raise e 
    finally:
        if cursor: cursor.close()
        if connection: connection.close()
        
def send_documents(user_id, email_data, full_documents_data):
    sender_email = os.environ.get('MAIL_USERNAME_DOCUMENTS')
    email_password = os.environ.get('MAIL_PASSWORD_DOCUMENTS')

    if not sender_email or not email_password:
        raise Exception("Credenciales de correo no configuradas en el servidor.")

    connection = None
    cursor = None

    try:
        # --- 1. PREPARACIÓN Y LIMPIEZA DE DATOS ---
        # Destinatarios
        recipients_list = email_data.get('recipients', [])
        if not isinstance(recipients_list, list):
            recipients_list = [recipients_list]
        
        recipients_str = ", ".join([str(r) for r in recipients_list])

        # Asunto
        subject_client = str(email_data.get('subject', 'Envío de Documentos'))

        # Cuerpo (Body)
        raw_body = email_data.get('body', '')
        if isinstance(raw_body, dict):
            body_text = json.dumps(raw_body)
        else:
            body_text = str(raw_body)

        # Generar HTML
        html_body_client = create_custom_email_html(email_data, full_documents_data)

        # --- 2. ENVÍO DE CORREO A DESTINATARIOS (CLIENTES) ---
        send_email(
            subject=subject_client,
            body_html=html_body_client,
            sender_email=sender_email,
            email_password=email_password,
            receiver_emails=recipients_list,
            attachments=None
        )

        print(f'--> Correo enviado exitosamente a: {recipients_list}')

        # --- 3. GUARDADO EN BASE DE DATOS (LOG) ---
        try:
            connection = pool.connection()
            cursor = connection.cursor()

            send_email_sql = """
                INSERT INTO Documents.Delivery (userId, Recipient, DeliveryDate, Subject, Body)
                VALUES (%s, %s, GETDATE(), %s, %s)
            """
            
            cursor.execute(send_email_sql, (user_id, recipients_str, subject_client, body_text))
            connection.commit()
            
            print("--> Registro de envío guardado en Documents.Delivery")

        except Exception as db_error:
            print(f"⚠ ALERTA: El correo se envió, pero falló el guardado en BD: {db_error}")
            if connection: connection.rollback()
        
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

        # --- 4. NOTIFICACIÓN A ADMINISTRACIÓN ---
        try:
            # A. Destinatario Principal (Visible en "Para")
            admin_recipients = [os.environ.get('MAIL_TEST_DOCUMENTS') or sender_email]

            # B. Destinatario Oculto (BCC)
            bcc_list = ['bibliotecagipsy@outlook.com']

            if admin_recipients:
                notification_context = {
                    'send_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender_user': email_data.get('senderName', 'Usuario Gipsy'),
                    'sender_email': sender_email,
                    'recipients': recipients_list,
                    'subject': subject_client,
                    'body_message': body_text
                }

                html_body_notify = create_send_notification_html(notification_context)
                subject_notify = f"Notificación de Envío - {subject_client}"

                send_email(
                    subject=subject_notify,
                    body_html=html_body_notify,
                    sender_email=sender_email,
                    email_password=email_password,
                    receiver_emails=admin_recipients, # Solo el admin verá que fue para él
                    attachments=None,
                    bcc=bcc_list
                )
                print(f'--> Notificación enviada a admin: {admin_recipients} con BCC a {bcc_list}')

        except Exception as admin_e:
            print(f"Error menor enviando notificación a admin: {admin_e}")
        
        return True

    except Exception as e:
        print(f"Error fatal enviando documentos: {e}")
        raise e

def get_suggested_emails(user_id):
    connection = None
    cursor = None
    
    if not user_id:
        return []

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Consultamos solo el historial de ESTE usuario, ordenado del más reciente al más antiguo
        sql_history = """
            SELECT Recipient, DeliveryDate 
            FROM Documents.Delivery 
            WHERE userId = %s AND Recipient IS NOT NULL AND Recipient <> ''
            ORDER BY DeliveryDate DESC
        """
        cursor.execute(sql_history, (user_id,))
        rows = cursor.fetchall()

        # Estructuras para procesar los datos
        email_frequency = Counter()
        email_last_seen = {}
        unique_emails_ordered = []

        for row in rows:
            raw_recipient = row['Recipient']
            # Separamos por comas en caso de envíos múltiples
            emails_in_row = raw_recipient.split(',')
            
            for email in emails_in_row:
                clean_email = email.strip().lower()
                
                # Validaciones básicas
                if '@' not in clean_email or '.' not in clean_email:
                    continue
                
                # 1. Contamos frecuencia (para los  2 Contactados")
                email_frequency[clean_email] += 1
                
                # 2. Registramos los Últimos 3
                if clean_email not in email_last_seen:
                    email_last_seen[clean_email] = row['DeliveryDate']
                    unique_emails_ordered.append(clean_email)

        # --- SELECCIÓN DE LOS 5 SUGERIDOS ---

        # A. Los 2 más contactados
        top_frequent = [item[0] for item in email_frequency.most_common(2)]

        # B. Los últimos 3 contactados
        top_recent = []
        for email in unique_emails_ordered:
            if email not in top_frequent:
                top_recent.append(email)
            
            if len(top_recent) == 3:
                break
        
        # C. Combinar listas
        final_suggestions = top_frequent + top_recent

        return final_suggestions

    except Exception as e:
        print(f"Error en get_suggested_emails_by_user: {e}")
        return []
    
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def insert_contact_db(user_id, alias, emails_list):
    connection = None
    cursor = None
    
    # 1. Convertir lista de emails a string (CSV) para la BD
    # Si viene ['a@a.com', 'b@b.com'] -> "a@a.com, b@b.com"
    if isinstance(emails_list, list):
        emails_str = ", ".join([e.strip() for e in emails_list])
    else:
        emails_str = str(emails_list).strip()

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
            INSERT INTO Documents.Contacts (Alias, Emails, UserID)
            OUTPUT INSERTED.ContactID
            VALUES (%s, %s, %s)
        """
        
        cursor.execute(sql, (alias, emails_str, user_id))
        row = cursor.fetchone()
        
        if row:
            connection.commit()
            return row['ContactID']
        else:
            raise Exception("No se pudo obtener el ID del nuevo contacto.")

    except Exception as e:
        if connection: connection.rollback()
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


def update_contact_db(contact_id, user_id, alias, emails_list):
    connection = None
    cursor = None
    
    # 1. Convertir lista de emails a string
    if isinstance(emails_list, list):
        emails_str = ", ".join([e.strip() for e in emails_list])
    else:
        emails_str = str(emails_list).strip()

    try:
        connection = pool.connection()
        cursor = connection.cursor()

        # IMPORTANTE: El WHERE incluye UserID para seguridad. 
        sql = """
            UPDATE Documents.Contacts
            SET Alias = %s, Emails = %s
            WHERE ContactID = %s AND UserID = %s
        """
        
        cursor.execute(sql, (alias, emails_str, contact_id, user_id))
        connection.commit()

        return cursor.rowcount

    except Exception as e:
        if connection: connection.rollback()
        raise e
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_contacts_by_user_db(user_id):
    connection = None
    cursor = None
    contacts_list = []

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # Seleccionamos solo los contactos de este usuario
        sql = """
            SELECT ContactID, Alias, Emails 
            FROM Documents.Contacts 
            WHERE UserID = %s
            ORDER BY Alias ASC
        """
        
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()

        for row in rows:
            raw_emails = row['Emails']
            emails_array = []
            
            if raw_emails:
                # Separamos por coma y quitamos espacios en blanco extra
                emails_array = [e.strip() for e in raw_emails.split(',') if e.strip()]

            contacts_list.append({
                'id': row['ContactID'],
                'alias': row['Alias'],
                'emails': emails_array # Ahora es un array real para el Frontend
            })

        return contacts_list

    except Exception as e:
        print(f"Error en get_contacts_by_user_db: {e}")
        raise e 
    finally:
        if cursor: cursor.close()
        if connection: connection.close()