import base64
import logging
import os
import traceback
import uuid

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import BaseAgent
from google.adk.runners import InMemoryRunner
from google.adk.events.event import Event as ADKEvent
from google.genai import types
from ai_fashion_house.agents.marketing_agent.agent import root_agent

# Load environment variables
load_dotenv(find_dotenv())
APP_NAME = os.getenv("APP_NAME", str(uuid.uuid4()))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI-Fashion-API")

# Initialize FastAPI app
api = FastAPI(root_path="/api", lifespan=lambda app: lifespan(app))
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    logger.info("🚀 Starting Gemini Live Avatar API")
    yield
    logger.info("🛑 Shutting down Gemini Live Avatar API")


async def create_adk_session(root_agent: BaseAgent, user_id: str, session_id: str) -> InMemoryRunner:
    """Initialize an ADK session with a runner."""
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    await runner.session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    return runner


@api.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "AI Fashion House API is running!"}


@api.websocket("/ws")
async def websocket_receiver(websocket: WebSocket):
    """WebSocket endpoint for real-time interaction."""
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"🌐 WebSocket connection from {client_info}")
    await websocket.accept()

    await websocket.send_json({
        "event": "log",
        "data": "WebSocket connection established. You can now send data."
    })

    try:
        while True:
            message = await websocket.receive_json()
            event_type = message.get("event")
            data = message.get("data", {})

            logger.info(f"📥 Event '{event_type}' from {client_info}: {data}")

            if event_type != "start_design":
                await websocket.send_json({"event": "error", "data": "Unknown event type."})
                continue

            prompt = data.get("prompt")
            if not prompt:
                await websocket.send_json({
                    "event": "error",
                    "data": "No prompt provided to start the session."
                })
                continue

            user_id = data.get("user_id", str(uuid.uuid4()))
            session_id = data.get("session_id", str(uuid.uuid4()))
            logger.info(f"🧵 Starting session {session_id} for user {user_id}")

            runner = await create_adk_session(root_agent, user_id, session_id)
            user_content = types.Content(role="user", parts=[types.Part(text=prompt)])

            try:
                async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
                    await handle_event(event, websocket)

                    if event.is_final_response():
                        logger.info(f"✅ Final response for session {session_id}")
                        await send_artifacts(runner, user_id, session_id, websocket)
                        await send_state(runner, user_id, session_id, websocket)
                        break
            except Exception as e:
                logger.error(f"❌ Error during session run: {e}")
                logger.debug(traceback.format_exc())
                await websocket.send_json({
                    "event": "error",
                    "data": f"An error occurred during session: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {client_info}")
    except Exception as e:
        logger.error(f"❗ Unexpected WebSocket error from {client_info}: {e}")
        logger.debug(traceback.format_exc())
        await websocket.close(code=1011, reason="Internal server error")


async def handle_event(event: ADKEvent, websocket: WebSocket) -> None:
    """Send structured event data to WebSocket based on ADK event."""
    if not event.content or not event.content.parts:
        return

    part = event.content.parts[0]
    is_final = event.is_final_response()
    payload = {"author": event.author, "is_final": is_final}

    if part.function_call:
        logger.info(f"🔧 Function call: {part.function_call.name}")
        await websocket.send_json({
            "event": "function_call",
            "data": {**payload, "function_name": part.function_call.name, "arguments": part.function_call.args}
        })
    elif part.function_response:
        await websocket.send_json({
            "event": "function_response",
            "data": {**payload, "function_name": part.function_response.name, "response": part.function_response.response}
        })
    elif part.text:
        await websocket.send_json({
            "event": "text_response",
            "data": {**payload, "text": part.text}
        })


# async def send_artifacts(
#     runner: InMemoryRunner,
#     user_id: str,
#     session_id: str,
#     websocket: WebSocket
# ) -> None:
#     """Send all artifacts generated in a session to the WebSocket."""
#     artifact_keys = await runner.artifact_service.list_artifact_keys(
#         app_name=APP_NAME, user_id=user_id, session_id=session_id
#     )
#     desired_sorted_keys =["met_rag_results.csv", "moodboard.png", "generated_image.png", "generated_video.mp4"]
#     for key in artifact_keys:
#         artifact = await runner.artifact_service.load_artifact(
#             app_name=APP_NAME, user_id=user_id, session_id=session_id, filename=key
#         )
#         logger.info(f"📦 Sending artifact: {key} ({artifact.inline_data.mime_type})")
#         encoded = base64.b64encode(artifact.inline_data.data).decode("utf-8")
#         await websocket.send_json({
#             "event": "artifact",
#             "data": {
#                 "filename": key,
#                 "mime_type": artifact.inline_data.mime_type,
#                 "content": encoded
#             }
#         })
async def send_artifacts(
    runner: InMemoryRunner,
    user_id: str,
    session_id: str,
    websocket: WebSocket
) -> None:
    """Send all artifacts generated in a session to the WebSocket in a defined order, including section names."""
    artifact_keys = await runner.artifact_service.list_artifact_keys(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    # Mapping from filename to section name
    artifact_sections = {
        "met_rag_results.csv": "Design Inspirations",
        "moodboard.png": "Design Inspirations",
        "generated_image.png": "Fashion image generated with Imagen 4",
        "generated_video.mp4": "Runway video with music generated with Veo 3"
    }

    desired_sorted_keys = list(artifact_sections.keys())
    ordered_keys = [k for k in desired_sorted_keys if k in artifact_keys]
    extras = [k for k in artifact_keys if k not in desired_sorted_keys]
    final_keys = ordered_keys + extras

    for key in final_keys:
        artifact = await runner.artifact_service.load_artifact(
            app_name=APP_NAME, user_id=user_id, session_id=session_id, filename=key
        )
        logger.info(f"📦 Sending artifact: {key} ({artifact.inline_data.mime_type})")
        encoded = base64.b64encode(artifact.inline_data.data).decode("utf-8")
        await websocket.send_json({
            "event": "artifact",
            "data": {
                "filename": key,
                "mime_type": artifact.inline_data.mime_type,
                "section_name": artifact_sections.get(key, key),  # fallback to filename if not mapped
                "content": encoded
            }
        })



async def send_state(
    runner: InMemoryRunner,
    user_id: str,
    session_id: str,
    websocket: WebSocket
) -> None:
    """Send the current state of the session to the WebSocket."""
    session = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    state = session.state if session else {}
    logger.info(f"📊 Sending session state for {session_id}: {state}")
    await websocket.send_json({
        "event": "state",
        "data": state
    })


