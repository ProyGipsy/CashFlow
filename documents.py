import os
from flask import Blueprint
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify, make_response, current_app, session, abort)
from flask_session import Session

documents_bp = Blueprint('documents', __name__)


"""
REDIRECCIONAMIENTO A REPOSITORIO DE REACT
"""

def _find_frontend_static_dir():
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DocumentosApp', 'frontend'))
    dist_dir = os.path.join(frontend_root, 'dist')
    build_dir = os.path.join(frontend_root, 'build')
    if os.path.isdir(dist_dir):
        return dist_dir
    if os.path.isdir(build_dir):
        return build_dir
    return None


@documents_bp.route('/documents', defaults={'path': ''})
@documents_bp.route('/documents/<path:path>')
def serve_react_app(path: str):
    """Serve React build files.

    This will serve files from the React build folder located at
    ../DocumentosApp/frontend/build relative to this file. If the
    requested path exists in the build folder it will be returned
    (useful for /documents/static/js/...), otherwise index.html is
    returned so React Router can handle client-side routes.
    """
    # Frontend output directories: Vite uses `dist`, CRA uses `build`.
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DocumentosApp', 'frontend'))
    static_dir = _find_frontend_static_dir()

    if static_dir is None:
        message = (
            "Frontend build not found. Build the frontend and place the output folder (`dist` or `build`) at:\n"
            f"{frontend_root}\n\n"
            "Commands (from DocumentosApp/frontend):\n"
            "npm install ; npm run build\n"
            "For Vite the output will be `dist`, for CRA it's `build`.\n"
        )
        return (message, 500)

    # If the requested file exists in the static directory, serve it
    requested_file = os.path.join(static_dir, path)
    if path and os.path.exists(requested_file) and os.path.isfile(requested_file):
        # Compute relative path inside static_dir
        rel_path = os.path.relpath(requested_file, static_dir)
        return send_from_directory(static_dir, rel_path)

    # Otherwise serve index.html so client-side routing works
    index_path = os.path.join(static_dir, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_dir, 'index.html')

    # Fallback (should not normally happen)
    abort(404)


@documents_bp.route('/assets/<path:filename>')
def serve_frontend_assets(filename: str):
    """Serve frontend assets when index.html references root-relative /assets/... URLs."""
    static_dir = _find_frontend_static_dir()
    if static_dir is None:
        abort(404)

    assets_dir = os.path.join(static_dir, 'assets')
    requested = os.path.join(assets_dir, filename)
    if os.path.exists(requested) and os.path.isfile(requested):
        return send_from_directory(assets_dir, filename)

    abort(404)

"""
Fin de redireccionamiento a repositorio de React
"""




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