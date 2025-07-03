import logging
import typing

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from ai_fashion_house.agents.fashion_design_agent.prompts import get_instructions
from ai_fashion_house.agents.fashion_design_agent.tools import get_fashion_model_details
from ai_fashion_house.agents.met_rag_agent.agent import root_agent as met_rag_agent
from ai_fashion_house.agents.search_agent.agent import root_agent as search_agent
from google.adk.models.llm_request import LlmRequest
from google.genai import types

logger = logging.getLogger(__name__)

async def before_agent_callback(
    callback_context: CallbackContext,
) -> typing.Optional[types.Content]:

    """Callback to run before the agent executes."""
    # You can add any pre-processing logic here if needed
    logging.info("Before Agent Callback")
    if 'model_details' not in callback_context.state:
        return types.ModelContent("Sorry, I don't have the model details to generate the enhanced prompt.")
    return None


async def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
):
  logger.info("Before Model Callback")


research_agent = ParallelAgent(
    name="research_agent",
    description="Coordinates the execution of the met_rag_agent and search agent agents to gather fashion inspiration and insights.",
    sub_agents=[
        met_rag_agent,
        search_agent,
    ]
)
prompt_writer_agent = Agent(
    name="prompt_writer_agent",
    description="Transforms visual references and historical context into a vivid, fashion-forward prompt for AI media generation.",
    model="gemini-2.0-flash",
    instruction=get_instructions(),
    tools=[get_fashion_model_details],
    output_key="enhanced_prompt",
    generate_content_config=types.GenerateContentConfig(temperature=0.5),
)

root_agent = SequentialAgent(
    name="fashion_design_agent",
    sub_agents=[research_agent, prompt_writer_agent],
    description="Coordinates the fashion inspiration gathering process and prompt writing for AI media generation.",
)