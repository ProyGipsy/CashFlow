import os
import base64
from msal import ConfidentialClientApplication

from dotenv import load_dotenv
load_dotenv()

client_id = os.environ.get('APP_CLIENT_ID')
client_secret = os.environ.get('APP_CLIENT_SECRET')
tenant_id = os.environ.get('APP_TENANT_ID')

msal_authority = f"https://login.microsoftonline.com/{tenant_id}"
msal_scope = ["https://graph.microsoft.com/.default"]

def get_onedrive_headers():

    msal_app = ConfidentialClientApplication(
        client_id = client_id,
        client_credential = client_secret,
        authority = msal_authority
    )

    result = msal_app.acquire_token_silent(
        scopes = msal_scope,
        account = None
    )

    if not result:
        result = msal_app.acquire_token_for_client(scopes=msal_scope)

    if "access_token" in result:
        access_token = result["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        return headers
    
    else:
        print(f"Token error: {result['error']}")
        print("Error details:", result.get("error_description", "No additional details"))
        raise Exception("No se pudo obtener el token de acceso")
    
def get_onedrive_headers_manual(clientId, clientSecret, tenantId):

    msal_app = ConfidentialClientApplication(
        client_id = clientId,
        client_credential = clientSecret,
        authority = f"https://login.microsoftonline.com/{tenantId}"
    )

    result = msal_app.acquire_token_silent(
        scopes = ["https://graph.microsoft.com/.default"],
        account = None
    )

    if not result:
        result = msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" in result:
        access_token = result["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        return headers
    
    else:
        print(f"Token error: {result['error']}")
        print("Error details:", result.get("error_description", "No additional details"))
        raise Exception("No se pudo obtener el token de acceso")
    
def graph_url_encoding(url):
    """
    Microsoft requiere que las URLs de Share/OneDrive se codifiquen en un Base64 especial
    para poder consultarlas en el endpoint /shares/
    """
    encodedBytes = base64.b64encode(url.encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    # Reglas específicas de codificación de Microsoft
    encodedStr = encodedStr.replace("/", "_").replace("+", "-").rstrip("=")
    return "u!" + encodedStr