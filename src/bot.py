import sys, os, time
import traceback
from botbuilder.core import  TurnContext, MessageFactory, MemoryStorage
from botbuilder.schema import  CardAction, ActionTypes, SuggestedActions
from teams.ai.prompts import PromptFunctions, PromptManager, PromptManagerOptions,prompt
from teams import Application, ApplicationOptions, TeamsAdapter
from state import AppTurnState
from teams.ai.planners import ActionPlanner, ActionPlannerOptions,ActionPlannerPromptFactory
from teams.ai.models import AzureOpenAIModelOptions, OpenAIModel 
from teams.ai.actions import ActionTurnContext
from teams.ai import AIOptions
from teams.ai.tokenizers import Tokenizer, GPTTokenizer
from teams.state import MemoryBase
from teams.adaptive_cards import adaptive_cards
from config import DefaultConfig
from typing import Any, Dict, List
from SendChat import send_chat

config = DefaultConfig()

# Create AI components
model: OpenAIModel
planner: ActionPlanner
model = OpenAIModel(
    AzureOpenAIModelOptions(
        api_key=config.AZURE_OPENAI_API_KEY,
        default_model=config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME,    
        endpoint=config.AZURE_OPENAI_ENDPOINT,
    )
)


prompts = PromptManager(PromptManagerOptions(prompts_folder=f"{os.path.dirname(os.path.abspath(__file__))}/prompts",role='system'))

planner = ActionPlanner[AppTurnState](ActionPlannerOptions(model=model, prompts=prompts,default_prompt='chat'))

storage = MemoryStorage()
app = Application[AppTurnState](
    ApplicationOptions(
        bot_app_id="",
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner)        
    )
)


@app.turn_state_factory
async def turn_state_factory(context: TurnContext):
    
    return await AppTurnState.load(context, storage)



@app.ai.action("LightsOn")
async def on_lights_on(
    context: ActionTurnContext[Dict[str, Any]],
    state: AppTurnState,
):
    await send_chat(context,state)
    state.conversation.lights_on = True
    await context.send_activity("[lights on]")
    return "the lights are now on"


@app.ai.action("LightsOff")
async def on_lights_off(
    context: ActionTurnContext[Dict[str, Any]],
    state: AppTurnState,
):
    
    state.conversation.lights_on = False    
    await context.send_activity("[lights off]")
    return "the lights are now off"

@prompts.function("get_light_status")
async def on_get_light_status(
    _context: TurnContext,
    state: MemoryBase,
    _functions: PromptFunctions,
    _tokenizer: Tokenizer,
    _args: List[str],
):
    return "on" if state.get("conversation.lightsOn") else "off"


@app.ai.action("Pause")
async def on_pause(
    context: ActionTurnContext[Dict[str, Any]],
    _state: AppTurnState,
):
    print(context.data["time"])
    time_ms = int(context.data["time"]) #if context.data["time"] else 1000
    await context.send_activity(f"[pausing for {time_ms / 1000} seconds]")
    time.sleep(time_ms / 1000)
    return "done pausing"

@app.ai.action("LightStatus")
async def on_lights_status(
    _context: ActionTurnContext[Dict[str, Any]],
    state: AppTurnState,
):     
    return "the lights are on" if state.conversation.lights_on else "the lights are off"

@app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}")
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
