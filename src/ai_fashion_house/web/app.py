import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api # gemini live websocket stuff
from .web import web # fastapi static web app generated vite

logger = logging.getLogger("rich")


def mount_apps(app: FastAPI):
    apps = {
        "/api": api,
        "/": web,
    }
    for path, sub_app in apps.items():
        app.mount(path, sub_app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Api life span
    :return:
    """
    logger.info("app is starting")
    mount_apps(app)
    yield
    logger.info("app is shutting down")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)