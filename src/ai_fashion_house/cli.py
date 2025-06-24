import logging
import os
from typing import Optional

import typer
from dotenv import load_dotenv, find_dotenv
from typing_extensions import Annotated
from ai_fashion_house.create_rag import main as create_rag

# Load environment variables from a .env file
load_dotenv(find_dotenv())

# Initialize Typer CLI
app = typer.Typer(invoke_without_command=True)

# Configure logging
logging.basicConfig(level=logging.INFO)


def dispatch_fastapi_app(
        app: str,
        host: str,
        port: int,
        workers: Optional[int] = None,
        reload: bool = True
) -> None:
    """
    Launch a FastAPI application using Uvicorn.
    """
    if workers is None:
        workers = (os.cpu_count() or 1) * 2 + 1

    logging.info(f"Starting FastAPI app on {host}:{port} with {workers} workers (reload={reload})")
    import uvicorn
    uvicorn.run(app, host=host, port=port, workers=workers, reload=reload)


@app.command(name="start")
def start(
    # fastapi parameters
    host: Annotated[str, typer.Option("--host", help="Host address")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port number")] = 8080,
    workers: Annotated[Optional[int], typer.Option("--workers", help="Number of workers")] = None,
    reload: Annotated[bool, typer.Option("--reload", help="Enable auto-reload")] = False,
    # API keys
    gemini_api_key: Annotated[Optional[str], typer.Option(envvar="GEMINI_API_KEY", help="Google Gemini API key")] = None
) -> None:
    """
    Start the FastAPI-based Gemini Avatar app with runtime configurations.
    """
    # Set environment variables if keys are passed
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        logging.info("Set GEMINI_API_KEY from input")

    dispatch_fastapi_app("ai_fashion_house.web.app:app", host, port, workers, reload)


@app.command(name="setup-rag")
def setup_rag():
    """
    Deploy the FastAPI app to Google Cloud Run.
    """
    create_rag()


def main():
    app()


if __name__ == "__main__":
    main()
