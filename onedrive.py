import os
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