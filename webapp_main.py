from fastapi import FastAPI, APIRouter
from pycoin.deployment.webapp import StrategyManagement
from pycoin.utils import Add_Tasks
import uvicorn
import os
import asyncio

from pycoin.deployment.webapp import positions, APIKEYS, utils

app = FastAPI()

app.include_router(positions.router)            
app.include_router(APIKEYS.router)
app.include_router(utils.router)
app.include_router(StrategyManagement.router)


@app.get("/")
async def home():
    return {"msg":"Welcome!"}



if __name__ == "__main__":
    uvicorn.run(app = app, host = "127.0.0.1", port = 8080)

