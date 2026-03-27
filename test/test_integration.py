import unittest
import os
import io

# Importamos tu app y funciones reales
from app import create_document, upload_file_to_onedrive # Ajusta el import
from documents import pool # Importamos el pool para poder limpiar la BD después

class TestIntegrationCreateDocument(unittest.TestCase):

    def setUp(self):
        # 1. Asegurarnos de que las credenciales existen en el entorno
        self.assertTrue(os.environ.get("MAIL_USERNAME_DOCUMENTS"), "Falta credencial de correo")
        self.assertTrue(os.environ.get("MAIL_PASSWORD_DOCUMENTS"), "Falta password de correo")
        self.assertTrue(os.environ.get("MAIL_TEST_DOCUMENTS"), "Falta correo de destino de prueba")
        
        # Guardaremos el ID insertado para poder borrarlo al final
        self.inserted_doc_id = None

    def test_1_onedrive_upload(self):
        """Prueba real de subida a OneDrive"""
        print("\n--- Probando conexión a OneDrive ---")
        
        # Simulamos un archivo en memoria (como si viniera de un formulario web)
        dummy_file = io.BytesIO(b"Este es un archivo de prueba generado automaticamente.")
        dummy_file.filename = "archivo_prueba_integracion.txt"
        
        # Ejecutamos la subida real
        resultado = upload_file_to_onedrive(dummy_file)
        
        # Verificamos que OneDrive respondió con un link
        self.assertIn('link', resultado)
        self.assertTrue(resultado['link'].startswith('http'))
        print(f"Éxito: Archivo subido. URL: {resultado['link']}")
        
        # Guardamos la URL para usarla en la siguiente prueba
        self.__class__.test_file_url = resultado['link']

    def test_2_database_and_email(self):
        """Prueba real de inserción en BD y envío de correo"""
        print("\n--- Probando Base de Datos y Envío de Correo ---")
        
        # Asumimos que existen IDs válidos en tu BD para la prueba (Ej: Empresa 1, TipoDoc 1)
        # Ajusta estos IDs a unos que sepas que existen en tu base de datos
        datos_prueba = {
            'companyId': [1], 
            'docTypeId': 1,   
            'documentName': 'INTEGRATION TEST - ELIMINAR',
            'fields': []
        }
        
        # Usamos la URL de la prueba anterior (o una de fallback)
        url = getattr(self.__class__, 'test_file_url', "https://onedrive.live.com/test")

        # Ejecutamos la función REAL
        resultado = create_document(datos_prueba, url)
        
        self.assertIsNotNone(resultado['document_id'])
        self.inserted_doc_id = resultado['document_id']
        print(f"Éxito: Documento insertado en BD con ID {self.inserted_doc_id}")
        print("Revisa tu bandeja de entrada de correo. Deberías tener un nuevo mensaje.")

    def tearDown(self):
        """Este método se ejecuta SIEMPRE al final de cada prueba, pase lo que pase.
        Lo usaremos para limpiar la basura que dejamos en la base de datos."""
        
        if self.inserted_doc_id:
            print(f"\n[Limpieza] Eliminando el documento {self.inserted_doc_id} de la BD...")
            connection = None
            cursor = None
            try:
                connection = pool.connection()
                cursor = connection.cursor()
                
                # Borramos en orden para respetar las llaves foráneas (Foreign Keys)
                cursor.execute("DELETE FROM Documents.FieldValue WHERE DocumentID = %s", (self.inserted_doc_id,))
                cursor.execute("DELETE FROM Documents.DocumentCompanies WHERE DocumentID = %s", (self.inserted_doc_id,))
                cursor.execute("DELETE FROM Documents.DocumentAnnex WHERE DocumentID = %s", (self.inserted_doc_id,))
                cursor.execute("DELETE FROM Documents.Document WHERE DocumentID = %s", (self.inserted_doc_id,))
                
                connection.commit()
                print("[Limpieza] Documento de prueba eliminado exitosamente.")
            except Exception as e:
                print(f"[Limpieza] Error al borrar datos de prueba: {e}")
                if connection:
                    connection.rollback()
            finally:
                if cursor: cursor.close()
                if connection: connection.close()

if __name__ == '__main__':
    unittest.main()