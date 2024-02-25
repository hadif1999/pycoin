

import os, json
from typing import Any
from ..utils.utils import current_time
from typeguard import typechecked


class API_MANAGER:
    
    def __init__(self):
        self.__SECRET_KEY = None
        self.__API_KEY = None
        pass
    
    # def __setattr__(self, name, val):
    #     if any([True for Str in ["API", "SECRET"] if Str in name]): 
    #         raise PermissionError("access denied")
    #     else: self.__dict__[name] = val
        
        
    def __delattr__(self, name: str):
        if any([True for Str in ["API", "SECRET"] if Str in name]): 
            raise PermissionError("access denied")
        else: del self.__dict__[name]
        
    # def __getattribute__(self, name: str) -> Any: 
    #     if any([True for Str in ["API_KEY", "SECRET_KEY"] if Str in name]): return None
    #     else: return super().__getattribute__(name)  
    
    @typechecked
    def readAPIs(self,* , filename:str , dir:str = None): 
        pwd = os.getcwd()
        if dir and dir not in os.getcwd(): os.chdir(dir)
        with open(filename, "r") as key_file:
            res = key_file.read()
            key_dict = json.loads(res)
            key_file.close()
        _key_dict = {key.upper():value for key, value in key_dict.items() 
                    if key.upper() in ["API_KEY", "SECRET_KEY"]}
        self._change_APIkeys(_key_dict["API_KEY"], _key_dict["SECRET_KEY"])
        # except: raise ValueError("keys of API_keys json file can be 'API_key', 'secret_key'.")
        os.chdir(pwd)
    
    
    @typechecked
    def _change_APIkeys(self, API_key:str, secret_key:str):
        self.__API_KEY = API_key
        self.__SECRET_KEY = secret_key
        
        
    @property
    def _check_API_keys(self):
        if self.__API_KEY and self.__SECRET_KEY:   return True
        else: raise NotImplementedError("\napi keys did not given yet.\n")
    
    @typechecked
    def writeAPIs(self, filename:str, dir:str):
        self._check_API_keys
        pwd = os.getcwd()
        if dir != None: os.chdir(dir)
        if filename == None: filename = f"{self.__class__.__name__.lower()}_API_keys_{current_time(as_str = True)}.json" 
        with open(filename, "w") as api_file:
            api_file.write(json.dumps({"API_key":self.__API_KEY, "secret_key":self.__SECRET_KEY}))
            api_file.close()
        os.chdir(pwd)
    
    @property
    def _API_key(self): return self.__API_KEY
    
    @property
    def _SECRET_key(self): return self.__SECRET_KEY
        
    @property
    def clearAPIkeys(self):
        self.__API_KEY = self.__SECRET_KEY = None
    
            