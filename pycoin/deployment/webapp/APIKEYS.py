from fastapi import APIRouter, UploadFile
from pycoin.deployment.webapp import dependencies
from fastapi.responses import PlainTextResponse
import os, json

market_dep = dependencies.market_dependency


router = APIRouter(prefix = "/APIKEYS", tags = ["APIKEYS"])

@router.get("/change", response_class= PlainTextResponse)
async def change_APIKEYS_FromURL(API_KEY:str, SECRET_KEY:str):
    os.environ["API_KEY"] = API_KEY
    os.environ["SECRET_KEY"] = SECRET_KEY
    return "API keys changed"


@router.post("/change/file", response_class = PlainTextResponse)
async def change_APIKEYS_FromFile(fileUpload:UploadFile):
    try: 
        contents = await fileUpload.read()
    except: return {"msg":"error accured while reading"}
    finally: await fileUpload.close()
    
    keys_dict:dict = json.loads(contents)
    API_KEY = keys_dict.get("API_KEY")
    SECRET_KEY = keys_dict.get("SECRET_KEY")
    if None in [API_KEY, SECRET_KEY]: raise ValueError("API keys not found")
    os.environ["API_KEY"] = API_KEY
    os.environ["SECRET_KEY"] = SECRET_KEY
    return "API keys changed"