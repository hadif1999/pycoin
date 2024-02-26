import os
from fastapi import File, UploadFile, Depends
from pycoin.order_making import Bingx
from typing import Annotated, Any


# always API keys will be read from env and can change via file or url 
async def _Read_APIkeys_fromEnv():
    API_KEY = os.environ.get("API_KEY")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    return {"API_KEY":API_KEY, "SECRET_KEY":SECRET_KEY}


def _getModule_Vars(module) -> dict:
    vars = [item for item in dir(module) if not item.startswith("__") 
                                            and not item.endswith("__") ]
    vars_dict = {item:module.__dict__.get(item) for item in vars}
    return vars_dict


def _Dict2EnvVars(_dict_: dict[str,str]):
    import os
    for key, val in _dict_.items():
        os.environ[key] = str(val)


def _check_EnvVar_exists(EnvVar:str):
    import os
    assert EnvVar in os.environ.keys(), f"\n\n'{EnvVar}' not found in env variables"
    
        
def _isEnvVar_True(EnvVar:str):
    import os
    env_val = os.getenv(EnvVar).lower()
    if env_val in ["1", "true"]: return True
    elif env_val in ['0', '-1', 'false']: return False
    else: raise NotImplementedError(f"'{EnvVar}' env variable does not have a valid value")  




async def _Read_APIkeys_fromFile(file:UploadFile):
    import json
    if not file:
        raise FileNotFoundError("file not uploaded")
    if file: 
        try: res = await file.read()
        except: await file.close()
        keys_dict:dict = json.loads(res)
        API_KEY = keys_dict.get("API_KEY")
        SECRET_KEY = keys_dict.get("SECRET_KEY")
    if None in [API_KEY, SECRET_KEY]: raise ValueError("API keys not found")
    return {"API_KEY":API_KEY, "SECRET_KEY":SECRET_KEY}
    
    

async def Market_builder(API_keys: Annotated[dict, Depends(_Read_APIkeys_fromEnv)], 
                              symbol:str = "BTC-USDT", isdemo:bool = True,
                              market:str = "bingx" ):
    match market.lower():
        case "bingx":
            return Bingx(symbol = symbol , API_key=API_keys.get("API_KEY"),
                        Secret_key=API_keys.get("SECRET_KEY"), isdemo = isdemo)

        case _: raise ValueError("market not found")



market_dependency = Annotated[Bingx, Depends(Market_builder)]


        
        
    
    
    