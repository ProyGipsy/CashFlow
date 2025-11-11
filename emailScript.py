import os
from email.message import EmailMessage
import ssl
import smtplib
from pathlib import Path
import mimetypes
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()


# --- FUNCIÓN DE ENVÍO DE CORREO ---
def send_email(subject, body_html, sender_email, email_password, receiver_emails, attachments=None):
    
    print(f"Iniciando envío de correo a: {', '.join(receiver_emails)}")
    print(f"Asunto: {subject}")

    mail_server = os.environ.get("MAIL_SERVER")
    mail_port = os.environ.get("EMAIL_PORT", 587) # Puerto estándar para STARTTLS

    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    
    # Contenido HTML
    msg.set_content("Este es un correo con contenido HTML. Por favor, use un cliente de correo compatible para ver el contenido completo.")
    msg.add_alternative(body_html, subtype='html')

    # --- Archivos Adjuntos (PDFs u otros) ---
    if attachments:
        print(f"Adjuntando {len(attachments)} archivo(s)...")
        for file_path in attachments:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                print(f"Advertencia: El archivo adjunto {file_path} no existe. Omitiendo.")
                continue
            
            # Adivinar el tipo MIME
            ctype, encoding = mimetypes.guess_type(file_path_obj)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'  # Default genérico
            
            maintype, subtype = ctype.split('/', 1)
            
            try:
                with open(file_path_obj, "rb") as f:
                    file_data = f.read()
                
                msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_path_obj.name)
                print(f"Archivo {file_path_obj.name} adjuntado exitosamente.")
            except Exception as e:
                print(f"Error al leer o adjuntar el archivo {file_path_obj.name}: {e}")

    context = ssl.create_default_context()

    try:
        # Usar SMTP con STARTTLS (más común que SSL directo)
        # Si tu servidor usa el puerto 465 (SMTPO_SSL), cambia smtplib.SMTP a smtplib.SMTP_SSL y quita smtp.starttls()
        with smtplib.SMTP(mail_server, mail_port) as smtp:
            smtp.starttls(context=context)
            smtp.login(sender_email, email_password)
            smtp.sendmail(sender_email, receiver_emails, msg.as_string())
        print(f"Correo enviado exitosamente a {', '.join(receiver_emails)}!\n")
    except Exception as e:
        print(f"Error al enviar el correo a {', '.join(receiver_emails)}: {e}\n")


# --- ESTILO CSS BASE PARA GIPSY DOCUMENTOS ---

def get_base_email_style():
    """CSS base para los correos de Gipsy Documentos."""
    return """
        body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            color: black !important;
            background: #f4f4f7 !important;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 650px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #dcdcdc;
            border-radius: 10px;
            padding: 20px 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #8b56ed; /* Color lila principal */
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .header h2 {
            margin: 0;
            color: #421d83; /* Color lila oscuro */
            font-size: 24px;
            font-weight: bold;
        }
        .body-content {
            color: #333; /* Texto gris oscuro */
        }
        .body-content p {
            margin: 0 0 15px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
            color: #888;
        }
        .button {
            display: inline-block;
            padding: 12px 25px;
            margin-top: 20px;
            background-color: #8b56ed; /* Color lila principal */
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .data-table th, .data-table td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        .data-table th {
            background-color: #E6E6FA; /* Color lila claro */
            color: #421d83;
            width: 35%;
            font-weight: bold;
        }
        .data-table td {
            word-wrap: break-word;
        }
        .message-body {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-top: 10px;
        }
        """

# --- CORREO DE CREACIÓN DE TIPO DE DOCUMENTO ---

def create_doc_type_html(data):
    
    # Generar filas de la tabla de campos
    fields_rows = ""
    for field in data.get('fields', []):
        fields_rows += f"""
        <tr>
            <td>{field.get('nombre', 'N/A')}</td>
            <td>{field.get('tipo_dato', 'N/A')}</td>
            <td>{field.get('longitud', 'N/A')}</td>
            <td>{field.get('precision', 'N/A')}</td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"/>
        <style>{get_base_email_style()}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Gipsy Documentos - Nuevo Tipo de Documento</h2>
            </div>
            <div class="body-content">
                <p>Se ha creado un nuevo tipo de documento en la plataforma.</p>
                <p><strong>Detalles del Tipo de Documento:</strong></p>
                
                <table class="data-table">
                    <tr>
                        <th>Nombre</th>
                        <td>{data.get('doc_type_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Alias (Siglas)</th>
                        <td>{data.get('alias', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Descripción</th>
                        <td>{data.get('description', 'N/A')}</td>
                    </tr>
                </table>

                <h3 style="color: #421d83;">Campos Definidos</h3>
                <table class="data-table">
                    <thead>
                        <tr style="background-color: #E6E6FA; color: #421d83;">
                            <th style="width: auto; text-align: left; padding: 10px; border: 1px solid #ddd;">Nombre</th>
                            <th style="width: auto; text-align: left; padding: 10px; border: 1px solid #ddd;">Tipo de Dato</th>
                            <th style="width: auto; text-align: left; padding: 10px; border: 1px solid #ddd;">Longitud</th>
                            <th style="width: auto; text-align: left; padding: 10px; border: 1px solid #ddd;">Precisión</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fields_rows}
                    </tbody>
                </table>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no responda a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


# --- CORREO DE CREACIÓN DE DOCUMENTO ---

def create_new_doc_html(data):
    
    # Generar filas de la tabla de campos y valores
    fields_rows = ""
    for field in data.get('fields', []):
        fields_rows += f"""
        <tr>
            <td><strong>{field.get('nombre', 'N/A')}</strong></td>
            <td>{field.get('valor', 'N/A')}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8" />
        <style>{get_base_email_style()}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Gipsy Documentos - Nuevo Documento Creado</h2>
            </div>
            <div class="body-content">
                <p><strong>Hola, {data.get('user_name', 'Usuario')}.</strong></p>
                <p>Se ha creado un nuevo documento en la plataforma. A continuación, se detallan los datos del mismo:</p>
                
                <table class="data-table">
                    <tr>
                        <th>Tipo de Documento</th>
                        <td>{data.get('doc_type', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Empresa Asociada</th>
                        <td>{data.get('company', 'N/A')}</td>
                    </tr>
                </table>

                <h3 style="color: #421d83;">Datos del Documento</h3>
                <table class="data-table">
                    {fields_rows}
                </table>
                
                <p>Para su referencia, se adjunta el archivo .pdf correspondiente a este documento.</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no responda a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


# --- ENVÍO DE CORREO DE DOCUMENTOS ---

def generate_document_content_html(doc_data):
    """Genera un bloque HTML estilizado para mostrar los campos de un documento,
    usando estilos consistentes con la paleta de colores del CSS base."""

    # Colores extraídos del CSS base:
    COLOR_DARK_LILA = "#421d83"
    COLOR_PRIMARY_LILA = "#8b56ed"
    COLOR_TEXT_DARK = "#333"
    COLOR_BG_DETAIL = "#f9f9f9"
    COLOR_BORDER = "#e0e0e0"
    
    doc_title = f"{doc_data.get('docTypeName', 'Documento sin Nombre')} ({doc_data.get('companyName', 'Empresa Desconocida')})"
    
    # Encabezado del bloque del documento
    html = f"""
        <tr>
            <td style="padding: 20px 0 10px 0;">
                <h3 style="margin: 0; font-size: 16px; color: {COLOR_DARK_LILA}; border-bottom: 1px solid {COLOR_BORDER}; padding-bottom: 5px;">
                    Detalles del Documento: {doc_title}
                </h3>
                <p style="margin-top: 10px; margin-bottom: 0; font-size: 13px; color: #555; font-style: italic;">
                    Archivo Adjunto: {doc_data.get('attachment', 'N/A')}
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding: 15px 15px; background-color: {COLOR_BG_DETAIL}; border: 1px solid {COLOR_BORDER}; border-radius: 5px;">
                <table width="100%" cellspacing="0" cellpadding="0" border="0" style="font-size: 13px; border-collapse: collapse;">
    """
    
    fields_data = doc_data.get('fieldsData', {})
    field_keys = list(fields_data.keys())
    
    # Iterar de 2 en 2 para crear filas con 2 campos (diseño de 2 columnas)
    for i in range(0, len(field_keys), 2):
        key1 = field_keys[i]
        val1 = fields_data[key1]
        
        # Estilo para la separación de filas de datos
        border_style = f"1px dotted {COLOR_BORDER}"
        
        html += '<tr>'
        
        # Columna 1 (Campo y Valor)
        html += f"""
            <td width="50%" style="padding: 8px 10px 8px 0; vertical-align: top; border-bottom: {border_style};">
                <strong style="color: {COLOR_TEXT_DARK}; font-weight: 600; display: block;">{key1}:</strong> 
                <span style="color: #666; display: block; margin-top: 2px;">{val1}</span>
            </td>
        """
        
        # Columna 2 (Campo y Valor - si existe)
        if i + 1 < len(field_keys):
            key2 = field_keys[i+1]
            val2 = fields_data[key2]
            html += f"""
                <td width="50%" style="padding: 8px 0 8px 10px; vertical-align: top; border-bottom: {border_style};">
                    <strong style="color: {COLOR_TEXT_DARK}; font-weight: 600; display: block;">{key2}:</strong> 
                    <span style="color: #666; display: block; margin-top: 2px;">{val2}</span>
                </td>
            """
        else:
            # Columna vacía si es un número impar de campos
            html += f'<td width="50%" style="border-bottom: {border_style};"></td>'
            
        html += '</tr>'

    # Cierre del bloque del documento
    html += """
                </table>
            </td>
        </tr>
    """
    
    return html


def create_custom_email_html(custom_email_data, document_data_list=None): 
    """
    Genera el cuerpo HTML completo de un correo personalizado usando clases CSS 
    del estilo base.
    """
    
    css_styles = get_base_email_style() # Obtiene la cadena CSS
    
    greeting_name = custom_email_data.get("greeting_name", "Estimado/a")
    body_message = custom_email_data.get("body_message", "Se adjunta la documentación solicitada.")
    signature_name = custom_email_data.get("signature_name", "El Equipo de Gipsy")

    body_message_html = body_message.replace('\n', '<br>')
    
    # Generar el contenido de los documentos si existe
    documents_html_blocks = ""
    if document_data_list and isinstance(document_data_list, list):
        # Encabezado antes de los documentos
        documents_html_blocks = f"""
        <tr>
            <td class="body-content" style="padding: 0 0 10px 0;">
                <p style="font-weight: bold; margin-bottom: 0;">Documentos Enviados:</p>
            </td>
        </tr>
        """ + "".join(generate_document_content_html(doc_data) for doc_data in document_data_list)

    # HTML Template que respeta la estructura de email-safe tables y usa las clases CSS
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Envío de Documentos</title>
        <style type="text/css">
            {css_styles}
        </style>
    </head>
    <body style="padding: 0; margin: 0; background-color: #f4f4f7;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f7;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table role="presentation" class="container" width="650" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); padding: 0;">
                        
                        <tr>
                            <td style="padding: 20px 30px;">
                                <div class="header" style="text-align: left; border-bottom: 2px solid #8b56ed; padding-bottom: 15px; margin-bottom: 20px;">
                                    <h2 style="color: #421d83; font-size: 24px; margin: 0;">Envío de Documentos</h2>
                                </div>
                                
                                <div class="body-content" style="color: #333;">
                                    <p style="margin-top: 0; margin-bottom: 15px; font-size: 14px;">
                                        Estimado(a) {greeting_name},
                                    </p>

                                    <div class="message-body">
                                        {body_message_html}
                                    </div>
                                    
                                    <table width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 20px;">
                                        {documents_html_blocks} 
                                    </table>
                                    <p style="margin-top: 20px; font-size: 14px;">
                                        Saludos cordiales,
                                        <br>
                                        {signature_name}
                                    </p>
                                </div>
                                
                                <div class="footer">
                                    Este es un correo automatizado de Gipsy Documentos. Por favor, no responda a esta dirección.
                                </div>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html_content


# --- CORREO DE NOTIFICACIÓN DE ENVÍO ---

def create_send_notification_html(data):
    
    recipients_list = ", ".join(data.get('recipients', []))
    body_message_html = data.get('body_message', '').replace('\n', '<br>')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"/>
        <style>{get_base_email_style()}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Gipsy Documentos - Notificación de Envío</h2>
            </div>
            <div class="body-content">
                <p>Este es un mensaje de confirmación para notificarle que se ha enviado un correo con documentos que contienen los siguientes detalles.</p>
                
                <h3 style="color: #421d83;">Resumen del Envío</h3>
                <table class="data-table">
                    <tr>
                        <th>Fecha de Envío</th>
                        <td>{data.get('send_date', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Usuario Emisor</th>
                        <td>{data.get('sender_user', 'N/A')} ({data.get('sender_email', 'N/A')})</td>
                    </tr>
                    <tr>
                        <th>Destinatario(s)</th>
                        <td>{recipients_list}</td>
                    </tr>
                    <tr>
                        <th>Asunto</th>
                        <td>{data.get('subject', 'N/A')}</td>
                    </tr>
                </table>

                <h3 style="color: #421d83;">Cuerpo del Mensaje Enviado</h3>
                <div class="message-body">
                    {body_message_html}
                </div>
                
                <p style="margin-top: 20px;">Los documentos enviados se encuentran adjuntos en este correo para su registro.</p>
            </div>
            <div class="footer">
                <p>Este es un correo automático, por favor no responda a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


# --- MAIN - EJECUCIÓN DE PRUEBA ---

if __name__ == "__main__":
    print("Script de prueba de envío de correos de Gipsy Documentos")
    
    # --- Configuración de Envío ---
    receiver_email_test = os.environ.get("MAIL_RECIPIENT_TEST") # RECEPTOR DE PRUEBA
    receiver_email_test2 = os.environ.get("EMAIL_RECIPIENT_GIPSYCORP") # RECEPTOR DE PRUEBA 2
    sender_email = os.environ.get("MAIL_USERNAME_RECEIPT")
    email_password = os.environ.get("MAIL_PASSWORD_RECEIPT")
    
    if not all([receiver_email_test, sender_email, email_password]):
        print("Error: Faltan variables de entorno (MAIL_RECIPIENT_TEST, MAIL_USERNAME_RECEIPT, MAIL_PASSWORD_RECEIPT).")
        print("No se pueden enviar correos de prueba.")
    else:
        # --- Buscar archivos PDF existentes para adjuntar. Aquí deberá buscarse de OneDrive ---
        print("Buscando archivos PDF existentes para adjuntar...")
        script_dir = Path(__file__).resolve().parent
        filenames = [
            "1.1 Práctica 1(primera parte).pdf",
            "1.2 Práctica 1 (segunda parte).pdf",
            "1.3 Práctica 1 (tercera parte).pdf"
        ]

        attachments_found = []
        for name in filenames:
            p = script_dir / name
            if p.exists():
                attachments_found.append(str(p))
                print(f"Encontrado: {p.name}")
            else:
                print(f"Advertencia: archivo no encontrado: {name}")

        if not attachments_found:
            print("No se encontraron archivos para adjuntar. Los correos se enviarán sin adjuntos.")

        # Preparar referencias individuales (si existen) para mantener la semántica previa
        doc1_path = attachments_found[0] if len(attachments_found) >= 1 else None
        doc2_path = attachments_found[1] if len(attachments_found) >= 2 else None
        doc3_path = attachments_found[2] if len(attachments_found) >= 3 else None


        # --- 1. PRUEBA: Nuevo Tipo de Documento ---

        print("--- Iniciando Prueba 1: Nuevo Tipo de Documento ---")
        doc_type_data = {
            "doc_type_name": "Factura de Proveedor",
            "alias": "FACT-PROV",
            "description": "Documento para registrar facturas emitidas por proveedores externos.",
            "fields": [
                {"nombre": "Nro. Factura", "tipo_dato": "Texto", "longitud": 50, "precision": 0},
                {"nombre": "Nro. Control", "tipo_dato": "Texto", "longitud": 50, "precision": 0},
                {"nombre": "Fecha Emisión", "tipo_dato": "Fecha", "longitud": 0, "precision": 0},
                {"nombre": "Monto Base", "tipo_dato": "Numérico", "longitud": 18, "precision": 2},
                {"nombre": "IVA (16%)", "tipo_dato": "Numérico", "longitud": 18, "precision": 2}
            ]
        }
        subject_1 = f"Se ha creado el Tipo de Documento: {doc_type_data['doc_type_name']}"
        body_html_1 = create_doc_type_html(doc_type_data)
        send_email(subject_1, body_html_1, sender_email, email_password, [receiver_email_test], attachments=None)
        
        
        # --- 2. PRUEBA: Nuevo Documento Creado ---

        print("--- Iniciando Prueba 2: Nuevo Documento Creado ---")
        new_doc_data = {
            "user_name": "Ana López",
            "doc_type": "Factura de Proveedor",
            "company": "ACME C.A.",
            "fields": [
                {"nombre": "Nro. Factura", "valor": "F-2024-00123"},
                {"nombre": "Nro. Control", "valor": "NC-2024-00123"},
                {"nombre": "Fecha Emisión", "valor": "2024-10-28"},
                {"nombre": "Monto Base", "valor": "1500.00"},
                {"nombre": "IVA (16%)", "valor": "240.00"}
            ]
        }
        subject_2 = f"Nuevo Documento Creado: {new_doc_data['doc_type']} {new_doc_data['company']}"
        body_html_2 = create_new_doc_html(new_doc_data)
        send_email(subject_2, body_html_2, sender_email, email_password, [receiver_email_test], attachments=([doc1_path] if doc1_path else None))


        # --- 3. PRUEBA: Envío Personalizado (MODIFICADO) ---

        document_data_list = [
            {
                "docTypeName": "Factura de Venta",
                "companyName": "ACME C.A.",
                "attachment": "FV-00123_ACME.pdf",
                "fieldsData": {
                    "Número de Factura": "FV-00123",
                    "Fecha de Emisión": "2025-11-10",
                    "Monto Neto": "150.00",
                    "IVA (16%)": "24.00",
                    "Método de Pago": "Transferencia"
                }
            },
            {
                "docTypeName": "Contrato Laboral",
                "companyName": "ACME C.A.",
                "attachment": "Contrato_Carlos_R.pdf",
                "fieldsData": {
                    "Cédula de Identidad": "98765432",
                    "Fecha de Ingreso": "2023-03-15",
                    "Puesto": "Gerente de Ventas",
                    "Salario Base": "2000.50",
                    "Cláusula Especial": "N/A"
                }
            }
        ]

        print("--- Iniciando Prueba 3: Envío Personalizado ---")
        custom_email_data = {
            "greeting_name": "Sr. Carlos Rodríguez (ACME C.A.)",
            "body_message": "Le escribo para hacerle llegar los documentos correspondientes a la orden de compra #887-B.\n\nSe incluye la factura y el contrato de servicio firmado.\n\nQuedamos atentos a sus comentarios.",
            "signature_name": "Ana López (Gipsy Documentos)"
        }
        subject_3 = f"Envío de Documentos a {custom_email_data['greeting_name']}"
        body_html_3 = create_custom_email_html(custom_email_data, document_data_list)
        send_email(subject_3, body_html_3, sender_email, email_password, [receiver_email_test], 
                attachments=([p for p in (doc1_path, doc2_path) if p] or None))


        # --- 4. PRUEBA: Notificación de Envío ---

        print("--- Iniciando Prueba 4: Notificación de Envío ---")
        notification_data = {
            "send_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender_user": "Ana López",
            "sender_email": "ana.lopez@gipsy.com",
            "recipients": [receiver_email_test, "carlos.r@acme.com"],
            "subject": subject_3, # Reusamos el asunto de la prueba 3
            "body_message": custom_email_data['body_message'] # Reusamos el cuerpo de la prueba 3
        }
        subject_4 = f"Confirmación de Envío: {notification_data['subject']}"
        body_html_4 = create_send_notification_html(notification_data)
        send_email(subject_4, body_html_4, sender_email, email_password, [receiver_email_test], attachments=([p for p in (doc1_path, doc2_path) if p] or None))
        
        
        print("Prueba de envío de correos completada.")