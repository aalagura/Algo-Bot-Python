import msal.authority
from msgraph import GraphServiceClient
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.item_body import ItemBody
from azure.identity import ClientSecretCredential, DeviceCodeCredential
from teams.ai.actions import ActionTurnContext
from state import AppTurnState
from typing import Any, Dict
import msal
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_type import ChatType
from kiota_abstractions.api_error import APIError
from kiota_abstractions.base_request_configuration import RequestConfiguration, HeadersCollection
from config import DefaultConfig


CONFIG = DefaultConfig()

async def send_chat(  context: ActionTurnContext[Dict[str, Any]],
    state: AppTurnState,):
    # Create a credential object. Used to authenticate requests
    credential = ClientSecretCredential(
        tenant_id=CONFIG.TENANT_ID,
        client_id=CONFIG.APP_ID,
        client_secret=CONFIG.APP_PASSWORD
    )
    
    #graph_scopes = 'Chat.Create ChatMessage.Send Chat.ReadWrite.All'
    graph_scopes = 'https://graph.microsoft.com/.default'

    graph_client = GraphServiceClient(credential,scopes=graph_scopes.split(' '))
    access_token = credential.get_token(graph_scopes)                                           
    request_body = Chat(
        chat_type = ChatType.OneOnOne,
        members = [
            AadUserConversationMember(
                odata_type = "#microsoft.graph.aadUserConversationMember",
                roles = [
                    "guest",
                ],
                #user_id = '0df762cb-22a5-4c02-a326-7cab9cb0e7db',
                additional_data = {
                        #"user@odata_bind" : "https://graph.microsoft.com/v1.0/users('0df762cb-22a5-4c02-a326-7cab9cb0e7db')"
                        "user@odata.bind" : "https://graph.microsoft.com/v1.0/users/admin@rzww.onmicrosoft.com"
                }
            ),
            AadUserConversationMember(
                odata_type = "#microsoft.graph.aadUserConversationMember",
                roles = [
                    "guest",
                ],
                #user_id = 'b0caafbd-2320-4fb6-9811-069fc83ce0c6',
                additional_data = {
                        #"user@odata_bind" : "https://graph.microsoft.com/v1.0/users('b0caafbd-2320-4fb6-9811-069fc83ce0c6')"
                        "user@odata.bind" : "https://graph.microsoft.com/v1.0/users/AdeleV@rzww.onmicrosoft.com"

                }
            )
        ],
    )

    headers = HeadersCollection()
    headers.add( header_name="Authorization",            header_values= f"Bearer {access_token.token}") 
    headers.add( header_name="Content-Type",            header_values= "application/json")
    reqconf = RequestConfiguration(headers= headers)

    try:
        result = await graph_client.chats.post(request_body,reqconf)
        chat_id = result.id
        print(chat_id)
    except APIError as e:
        print(f'Error: {e.error.message}')
        return
   
   
    req_body = ChatMessage(        
        body = ItemBody(
            content = "Hello world111",
            
        ),        
        chat_id=result.id,
        
        
    )    
                
    try:
        #print(result.id)
        #print(access_token)
        
        res = await graph_client.chats.by_chat_id(result.id).messages.post(req_body,reqconf)
    except APIError as e:
        print(f'Error: {e.error.message}')
        return
    return 
