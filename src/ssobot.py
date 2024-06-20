from botbuilder.core import (
    TurnContext,
    ConversationState,
    
)
from botbuilder.schema import ActivityTypes
from msal import ConfidentialClientApplication
from config import DefaultConfig
import requests

from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_type import ChatType
from kiota_abstractions.api_error import APIError
from kiota_abstractions.base_request_configuration import RequestConfiguration, HeadersCollection
from msgraph import GraphServiceClient
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
CONFIG = DefaultConfig()
# Microsoft Graph API endpoint
GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'

class SsoBot:
    def __init__(self, conversation_state: ConversationState):
        self.conversation_state = conversation_state

    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.type == ActivityTypes.message:
            await self.process_message(turn_context)

    async def process_message(self, turn_context: TurnContext):
        if 'login' in turn_context.activity.text.lower():
            await self.handle_login(turn_context)
        else:
            await turn_context.send_activity(f"You said: {turn_context.activity.text}")

    async def handle_login(self, turn_context: TurnContext):
        #token_response = await self.get_token(turn_context.activity.from_property.id)

        token1 = await self.get_access_token()
        
        # Example usage
        user_ids = ['0df762cb-22a5-4c02-a326-7cab9cb0e7db', 'b0caafbd-2320-4fb6-9811-069fc83ce0c6']  # Replace with actual user IDs
        new_chat = await self.create_chat(token1, user_ids)
        chat_id = new_chat['id']

        message = 'Hello, this is a proactive message from the bot.'
        respon = await self.send_message_to_chat(token1, chat_id, message)
        print(f"Message sent successfully! {respon}")
        
        if token1:
            await turn_context.send_activity(f"Access Token: {token1}")            
            #await turn_context.send_activity(f"Access Token: {token_response['access_token']}")
        else:
            await turn_context.send_activity("Login failed. Please try again.")

    async def get_token(self, user_id):
        app = ConfidentialClientApplication(
            CONFIG.APP_ID,
            authority=f"https://login.microsoftonline.com/{CONFIG.TENANT_ID}",
            client_credential=CONFIG.APP_PASSWORD
        )
        
    # Acquire token on behalf of user
        accounts = app.get_accounts()        
        result = None
        if accounts:            
            result = app.acquire_token_silent(scopes=["https://graph.microsoft.com/.default"], account=accounts[0])

        if not result:
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result if "access_token" in result else None
    
    
    async def get_access_token(self):
        token_url = f"https://login.microsoftonline.com/{CONFIG.TENANT_ID}/oauth2/v2.0/token"
        scope = "https://graph.microsoft.com/.default"

        payload = {
            'grant_type': 'client_credentials',
            'client_id': CONFIG.APP_ID,
            'client_secret': CONFIG.APP_PASSWORD,
            'scope': scope
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        return response.json()['access_token']
        
        # Function to create a chat
    async def create_chat(self,access_token, user_ids):
        url = f"{GRAPH_ENDPOINT}/chats"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "chatType": "oneOnOne",  # Use "group" for group chat
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{user_id}"
                } for user_id in user_ids
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    # Function to send a message to a chat
    async def send_message_to_chat(self,access_token, chat_id, message):
        url = f"{GRAPH_ENDPOINT}/chats/{chat_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "body": {
                "content": message
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    
