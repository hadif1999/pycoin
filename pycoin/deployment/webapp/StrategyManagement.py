from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from pydantic import BaseModel
from typing import Annotated
import pandas as pd
# from ...celery import app
from starlette.datastructures import URL
from .strategies.pivotStrategy import pivotStrategyAPI

router = APIRouter(prefix = "/strategies", tags = ["strategies"])

router.include_router(pivotStrategyAPI.strategy_api.router)



