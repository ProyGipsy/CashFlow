import os
import pymssql
from dbutils.pooled_db import PooledDB

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

        validation_sql = """
        SELECT TypeID
        FROM Documents.DocumentType
        WHERE (Name = %s OR ShortName = %s)
        AND TypeID = %s
        """
        cursor.execute(validation_sql, (data['name'], data['alias'], data['id']))
        existing = cursor.fetchone()

        if existing:
            raise ValueError("Ya existe un Tipo de Documento con ese Nombre o Alias.")

        sql = """
        INSERT INTO Documents.DocumentType (Name, ShortName, Description)
        OUTPUT INSERTED.TypeID
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (data['name'], data['alias'], data.get('description', '')))
        inserted_id = cursor.fetchone()['TypeID']

        sql_access_control = """
        INSERT INTO AccessControl.Permissions (name, isDocumentsModule)
        VALUES (%s, 1)
        """
        cursor.execute(sql_access_control, (data['name'],))

        sql_document_fields = """
        INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision)
        OUTPUT INSERTED.FieldID
        VALUES (%d, %s, %s, %d, %d)
        """

        sql_specific_values = """
        INSERT INTO Documents.SpecificValue (FieldID, Value)
        VALUES (%d, %s)
        """

        for field in data.get('fields', []):
            cursor.execute(sql_document_fields, (inserted_id, field['name'], field['type'], field.get('length', None), field.get('precision', None)))
            
            if field['type'] == 'specificValues':
                field_id = cursor.fetchone()['FieldID']
                for value in field.get('specificValues', []):
                    cursor.execute(sql_specific_values, (field_id, value))
                
        connection.commit()

        return inserted_id

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error creando el Tipo de Documento: {e}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close

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

def format_roles(raw_rows):
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

        sql = """
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
        LEFT JOIN AccessControl.RolePermissions RP ON R.roleId = RP.roleId
        LEFT JOIN AccessControl.Permissions P ON RP.permissionId = P.permissionId AND P.isDocumentsModule = 1
        LEFT JOIN AccessControl.UserRoles UR ON R.roleId = UR.roleId
        LEFT JOIN AccessControl.Users U ON UR.userId = U.userId
        ORDER BY R.roleId;
        """

        cursor.execute(sql)
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
        INSERT INTO AccessControl.RolePermissions (roleId, moduleId, permissionId)
        VALUES (%s, 3, %s)
        """

        for permiso in data.get('permisos', []):
            cursor.execute(sql_role_permissions, (inserted_id, permiso['id']))

        sql_user_roles = """
        INSERT INTO AccessControl.UserRoles (userId, roleId)
        VALUES (%s, %s)
        """

        for usuario in data.get('usuarios', []):
            cursor.execute(sql_user_roles, (usuario['id'], inserted_id))
                
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

def update_role(data):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        UPDATE AccessControl.Roles
        SET name = ?
        WHERE roleID = ?
        """
        cursor.execute(sql, (data['name'], data['id']))
        

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error actualizando el Rol: {e}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_document(data, file_url):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        sql = """
        INSERT INTO Documents.Document (TypeID, CompanyID)
        OUTPUT INSERTED.DocumentID
        VALUES (%s, %s)
        """
        cursor.execute(sql, (data['docTypeId'], data['companyId']))
        row = cursor.fetchone()

        if not row:
            raise Exception('No se pudo obtener el ID del documento creado')

        inserted_id = row['DocumentID']

        # Aquí se deberían agregar las inserciones de FieldValue y DocumentAnnex
        sql_insert_value = """
            INSERT INTO Documents.FieldValue (FieldID, DocumentID, Value)
            VALUES (%s, %s, %s)
        """

        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            value = field.get('value')
            
            cursor.execute(sql_insert_value, (field_id, inserted_id, value))

        if file_url:
            sql_insert_annex = """
                INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
                VALUES (%s, %s, GETDATE())
            """
            cursor.execute(sql_insert_annex, (inserted_id, file_url))

        connection.commit()
        return inserted_id

    except Exception as e:
        if connection:
            connection.rollback()

        print(f"Error creando el Documento: {e}")
        raise e
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def edit_document(data, new_file_url=None):
    connection = None
    cursor = None

    try:
        connection = pool.connection()
        cursor = connection.cursor(as_dict=True)

        # 1. ACTUALIZAR VALORES DE LOS CAMPOS
        sql_update_value = """
            UPDATE Documents.FieldValue
            SET Value = %s
            WHERE FieldID = %s AND DocumentID = %s
        """

        # Iteramos sobre los campos recibidos.
        # data['fields'] viene como [{'fieldId': 1, 'value': 'Nuevo Valor'}, ...]
        for field in data.get('fields', []):
            field_id = field.get('fieldId')
            new_value = field.get('value')
            
            # Ejecutamos update para cada campo
            cursor.execute(sql_update_value, (new_value, field_id, data['id']))

        # 2. ACTUALIZAR ARCHIVO ADJUNTO (Solo si se subió uno nuevo)
        if new_file_url:
            # Opción A: Actualizar el registro existente (si la relación es 1 a 1)
            sql_update_annex = """
                UPDATE Documents.DocumentAnnex
                SET AnnexURL = %s, Date = GETDATE()
                WHERE DocumentID = %s
            """
            cursor.execute(sql_update_annex, (new_file_url, data['id']))
            
            # Nota: Si checkeas rowcount y da 0, significa que el documento no tenía anexo previo.
            # En ese caso podrías necesitar hacer un INSERT de contingencia.
            if cursor.rowcount == 0:
                sql_insert_annex = """
                    INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
                    VALUES (%s, %s, GETDATE())
                """
                cursor.execute(sql_insert_annex, (data['id'], new_file_url))

        connection.commit()
        return True

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error actualizando el Documento: {e}")
        raise e
    
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

"""
---- QUERIES APP DE DOCUMENTOS ---

-- FLUJO GENERAL --


-- Home con cards de Tipos de Documentos

SELECT TypeID, Name, ShortName 
FROM Documents.DocumentType



-- Visualización de Documentos por Tipo

-- Nota: La fecha indica la última actualización, que es lo que guarda la tabla del anexo
SELECT D.DocumentID, D.TypeID, D.CompanyID, C.Name, A.Date
FROM Documents.Document D
JOIN Documents.Company C ON D.CompanyID = C.CompanyID
JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID
WHERE D.TypeID = ?



-- Visualización de Documentos por Tipo (REVISAR CON DATA)

-- Nota: La fecha indica la última actualización, que es lo que guarda la tabla del anexo
-- Los campos del tipo de documento y sus valores se podrían estructurar y enviarlos al modal de visualización
-- Un solo query porque es más rápido en tiempos de respuesta, pero se puede evaluar
SELECT D.DocumentID, D.TypeID, DT.Name, D.CompanyID, C.Name, A.Date, F.Name, V.Value, SV.Value, A.AnnexURL
FROM Documents.Document D
JOIN Documents.DocumentType DT ON D.TypeID = DT.TypeID
JOIN Documents.Company C ON D.CompanyID = C.CompanyID
JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID
JOIN Documents.TypeFields F ON D.TypeID = F.DocumentTypeID
JOIN Documents.FieldValue V ON F.FieldID = V.FieldID AND D.DocumentID = V.DocumentID
LEFT JOIN Documents.SpecificValue SV ON F.FieldID = SV.FieldID



-- CREACIÓN DE TIPO DE DOCUMENTO

-- 1. Inserción del Tipo de Documento
INSERT INTO Documents.DocumentType (Name, ShortName, Description)
OUTPUT INSERTED.TypeID
VALUES (?, ?, ?)

-- 1.1 Inserción del Tipo como Permiso (usar el nombre largo del tipo)
INSERT INTO AccessControl.Permissions (name, isDocumentsModule)
VALUES (?, 1)

-- 2. Inserción de Campos para ese tipo de documento (usar el TypeID insertado en el query anterior)
INSERT INTO Documents.TypeFields (DocumentTypeID, Name, DataType, Length, Precision)
OUTPUT INSERTED.FieldID
VALUES (?, ?, ?, ?, ?)

-- 2.1 Para Campos de Valores Específicos (usar el FieldID insertado en en el query anterior)
INSERT INTO Documents.SpecificValue (FieldID, Value)
VALUES (?, ?)

-- EDICIÓN DE TIPO DE DOCUMENTO

-- OJO: Verificar si ya hay documentos creados con ese tipo. En ese caso, no permitir eliminar campos
-- Utilizar el mismo query de "Visualización de Documentos por Tipo" y si arroja resultados, quitar la opción de eliminar campos
-- También quitar la opción de eliminar valores específicos

-- 1. Actualización del Tipo de Documento
UPDATE Documents.DocumentType
SET Name = ?, ShortName = ?, Description = ?
WHERE TypeID = ?

-- 2. Actualización de Campos para ese tipo de documento
UPDATE Documents.TypeFields
SET Name = ?, DataType = ?, Length = ?, Precision = ?
WHERE FieldID = ? AND DocumentTypeID = ?

-- 2.1 Actualización de Valores Específicos (OJO: Revisar funcionamiento y cómo manejar eliminaciones de campos)
UPDATE Documents.SpecificValue
SET Value = ?
WHERE FieldID = ? AND ValueID = ?



-- CREACIÓN DE DOCUMENTO

-- 1. Llamar al mismo query de tipos de documentos, para mostrar los resultados en el select html

-- 2. Empresas Asociadas, mostrar en el select html

SELECT CompanyID, Name
FROM Documents.Company

-- 3. Según el tipo de documento, mostrar los campos y tipos que permite
SELECT DocumentTypeID, FieldID, Name, DataType, Length, Precision
FROM Documents.TypeFields
WHERE DocumentTypeID = ?

-- 4. Inserciones a realizar
-- 4.1 Inserción del documento
INSERT INTO Documents.Document (TypeID, CompanyID)
OUTPUT INSERTED.DocumentID
VALUES (?, ?)
-- 4.2 Inserción de valores de los campos (imagino que esto será iterando para cada campo existente)
-- (usar el DocumentID recién creado, mantener FieldID de cada uno y tomar los valores de los inputs)
INSERT INTO Documents.FieldValue (FieldID, DocumentID, Value)
VALUES (?, ?, ?)
-- 4.3 Inserción del archivo adjunto (guardar pdf en OneDrive, ruta APP DOCUMENTOS / Anexos)
INSERT INTO Documents.DocumentAnnex (DocumentID, AnnexURL, Date)
VALUES (?, ?, GETDATE)

-- ACTUALIZACIÓN DE DOCUMENTO

-- 1. Actualización de valores de los campos
UPDATE Documents.FieldValue
SET Value = ?
WHERE FieldID = ? AND DocumentID = ?

-- 2. Actualización del archivo adjunto (guardar pdf en OneDrive, ruta APP DOCUMENTOS / Anexos)
UPDATE Documents.DocumentAnnex
SET AnnexURL = ?, Date = GETDATE()
WHERE DocumentID = ?



-- Interfaz de Envío de Documentos por Correo
-- (Mismo query de docs, pero sin filtro por tipo. Esta interfaz posee paginado)
SELECT D.DocumentID, D.TypeID, D.CompanyID, C.Name, A.Date
FROM Documents.Document D
JOIN Documents.Company C ON D.CompanyID = C.CompanyID
JOIN Documents.DocumentAnnex A ON A.DocumentID = D.DocumentID



-- FLUJO DE ADMINISTRACIÓN --


-- MANEJO DE ROLES

-- Interfaz Principal
SELECT R.roleId, R.name AS RoleName, P.name AS PermissionName, U.userId, U.firstName + ' ' + U.lastName AS UserFullName
FROM AccessControl.Roles R
JOIN AccessControl.RolePermissions RP ON R.roleId = RP.roleId
JOIN AccessControl.Permissions P ON RP.permissionId = P.permissionId
JOIN AccessControl.UserRoles UR ON R.roleId = UR.roleId
JOIN AccessControl.Users U ON UR.userId = U.userId

-- Agregar Rol

-- 1. Permisos para mostrar en el select html
SELECT permissionId, name
FROM AccessControl.Permissions
WHERE isDocumentsModule = 1

-- 2. Usuarios a mostrar en el select html
SELECT userId, firstName + ' ' + lastName AS FullName, username
FROM AccessControl.Users
WHERE isActive = 1

-- 3. Inserción del Rol y sus Relaciones

-- 3.1 Inserción del Rol (esta tabla sólo guarda el nombre y genera el ID)
INSERT INTO AccessControl.Roles (name)
OUTPUT INSERTED.roleID
VALUES (?)

-- 3.2 Relación del rol con el módulo y los permisos. Tomar el roleId recién creado
-- OJO: Habría que hacer esto por cada permiso iterando, o llevando una lista de permissionId y adaptando el query
INSERT INTO AccessControl.RolePermissions (roleId, moduleId, permissionId)
VALUES (?, 4, ?)

-- 3.3 Asignación del rol a los usuarios. Tomar el roleId recién creado
-- También habría que iterar o llevar un listado adaptando el query
INSERT INTO AccessControl.UserRoles (userId, roleId)
VALUES (?, ?)

-- 4. Edición del Rol y sus Relaciones

-- 4.1 Actualización del Nombre del Rol
UPDATE AccessControl.Roles
SET name = ?
WHERE roleID = ?

-- 4.2 Sincronización de Permisos del Rol (insertar nuevos y eliminar los que ya no estén)
-- OJO: REVISAR. Gemini propone un procedimiento almacenado en SQL Server y llamarlo desde Python
CREATE PROCEDURE AccessControl.SyncRolePermissions (
    @RoleID INT,
    @ModuleID INT,
    @NewPermissions AccessControl.PermissionListType READONLY
)
AS
BEGIN
    -- ELIMINACIÓN:
    DELETE RP FROM AccessControl.RolePermissions RP
    WHERE
        RP.roleId = @RoleID
        AND RP.moduleId = @ModuleID
        AND NOT EXISTS (
            SELECT 1 FROM @NewPermissions NP
            WHERE NP.permissionId = RP.permissionId
        );

    -- INSERCIÓN:
    INSERT INTO AccessControl.RolePermissions (roleId, moduleId, permissionId)
    SELECT
        @RoleID,
        @ModuleID,
        NP.permissionId
    FROM
        @NewPermissions NP
    WHERE
        NOT EXISTS (
            SELECT 1 FROM AccessControl.RolePermissions RP
            WHERE RP.roleId = @RoleID
              AND RP.moduleId = @ModuleID
              AND RP.permissionId = NP.permissionId
        );
END

-- 4.3 Sincronización de Usuarios del Rol (insertar nuevos y eliminar los que ya no estén)
-- OJO: REVISAR. Gemini propone un procedimiento almacenado en SQL Server y llamarlo desde Python
-- 2. Crear el procedimiento almacenado para sincronizar usuarios
CREATE PROCEDURE AccessControl.SyncUserRoles (
    @RoleID INT,
    @NewUsers AccessControl.UserListType READONLY
)
AS
BEGIN
    -- 1. ELIMINACIÓN: Eliminar usuarios que actualmente tienen el rol,
    -- pero que NO están en la lista de @NewUsers entrante (usuarios desmarcados).
    DELETE UR FROM AccessControl.UserRoles UR
    WHERE
        UR.roleId = @RoleID
        AND NOT EXISTS (
            SELECT 1 FROM @NewUsers NU
            WHERE NU.userId = UR.userId -- Compara el ID de usuario de la tabla con el de la lista entrante
        );

    -- 2. INSERCIÓN: Insertar usuarios que están en la lista de @NewUsers,
    -- pero que NO tienen el rol asignado actualmente (usuarios nuevos marcados).
    INSERT INTO AccessControl.UserRoles (userId, roleId)
    SELECT
        NU.userId,
        @RoleID
    FROM
        @NewUsers NU
    WHERE
        NOT EXISTS (
            SELECT 1 FROM AccessControl.UserRoles UR
            WHERE UR.roleId = @RoleID
              AND UR.userId = NU.userId
        );
END
GO


-- GESTIONAR EMPRESAS

-- Interfaz base
SELECT CompanyID, Name, RIFtype, RIFnumber
FROM Documents.Company

-- Agregar Empresa
INSERT INTO Documents.Company (Name, RIFtype, RIFnumber)
VALUES (?, ?, ?)

-- Editar Empresa
UPDATE Documents.Company
SET Name = ?, RIFtype = ?, RIFnumber = ?
WHERE CompanyID = ?


"""