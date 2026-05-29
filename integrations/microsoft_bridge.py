import os
from azure.identity import DefaultAzureCredential
from msal import ClientApp, ConfidentialClientApplication
from requests import Session

# Set up Azure AD

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
TENANT_ID = "your_tenant_id"

# Authenticate with Microsoft Teams API

credential = DefaultAzureCredential()
app = ConfidentialClientApplication(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, authority=f"https://login.microsoftonline.com/{TENANT_ID}")
token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
access_token = token_response.get("access_token")

# Make API calls to the Microsoft Teams API

session = Session()
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
}
url = "https://graph.microsoft.com/v1.0/me/chats"
response = session.get(url, headers=headers)

if response.status_code == 200:
    chats = response.json().get("value", [])
    for chat in chats:
        print(chat)
else:
    print(f"Failed to get chats: {response.status_code}")