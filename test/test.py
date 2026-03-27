import unittest
from unittest.mock import patch, MagicMock

# Importamos la función desde TU archivo documents.py
from documents import create_document

class TestDocumentsLogic(unittest.TestCase):

    # ATENCIÓN AQUÍ: Ahora los patches apuntan a 'documents', que es donde vive la función
    @patch('documents.pool', create=True)
    @patch('documents.send_email', create=True)
    @patch('documents.create_new_doc_html', create=True)
    @patch('documents.os.environ.get', create=True)
    def test_create_document_flujo_completo(self, mock_env_get, mock_create_html, mock_send_email, mock_pool):
        
        # --- 1. SIMULAMOS LAS VARIABLES DE ENTORNO ---
        def env_side_effect(key):
            env_vars = {
                "MAIL_USERNAME_DOCUMENTS": "test_bot@empresa.com",
                "MAIL_PASSWORD_DOCUMENTS": "12345",
                "MAIL_TEST_DOCUMENTS": "admin@empresa.com"
            }
            return env_vars.get(key)
        mock_env_get.side_effect = env_side_effect

        # --- 2. SIMULAMOS LA BASE DE DATOS (No guardará nada real) ---
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Configuramos fetchone() en el orden que tu código lo llama:
        mock_cursor.fetchone.side_effect = [
            {'Name': 'Factura Comercial'},  # 1. Busca el nombre del Tipo de Documento
            {'DocumentID': 1024},           # 2. Obtiene el ID tras insertar la Cabecera
            {'Name': 'Monto', 'DataType': 'float'},  # 3. Info del 1er campo dinámico
            {'Name': 'Es Urgente', 'DataType': 'bool'} # 4. Info del 2do campo dinámico
        ]
        
        # Configuramos fetchall() para cuando busca los nombres de las empresas
        mock_cursor.fetchall.return_value = [
            {'Name': 'Empresa Alpha'},
            {'Name': 'Empresa Beta'}
        ]

        # Simulamos el HTML que genera tu función de correo
        mock_create_html.return_value = "<html>Cuerpo del correo</html>"

        # --- 3. CREAMOS LOS DATOS FALSOS QUE ENVIARÍA EL FRONTEND ---
        datos_prueba = {
            'companyId': [1, 2],
            'docTypeId': 5,
            'documentName': 'Factura de Prueba 2026',
            'fields': [
                {'fieldId': 10, 'value': '1500.50'},
                {'fieldId': 11, 'value': True} # Booleano para probar tu lógica de conversión
            ]
        }
        url_archivo = "https://onedrive.live.com/prueba.pdf"

        # --- 4. EJECUTAMOS TU FUNCIÓN ---
        resultado = create_document(datos_prueba, url_archivo)

        # --- 5. VERIFICAMOS QUE TODO SALIÓ BIEN ---
        # A. Verificar respuesta de la función
        self.assertEqual(resultado['document_id'], 1024)
        self.assertEqual(resultado['document_name'], 'Factura de Prueba 2026')
        self.assertEqual(resultado['annex_url'], url_archivo)

        # B. Verificar base de datos (que hizo commit y cerró)
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        # C. Verificar envío de correo
        mock_send_email.assert_called_once()
        
        # Extraemos los argumentos con los que se llamó al correo simulado
        _, kwargs = mock_send_email.call_args
        
        # Validamos que construyó el asunto correctamente con los nombres de BD simulados
        self.assertEqual(kwargs['subject'], "Nuevo Documento Creado: Factura Comercial - Empresa Alpha, Empresa Beta")
        self.assertEqual(kwargs['sender_email'], "test_bot@empresa.com")
        self.assertEqual(kwargs['receiver_emails'], ["admin@empresa.com"])


if __name__ == '__main__':
    unittest.main()