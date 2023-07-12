import datetime as dt
import json
import os

# this class is a wrapper to deploy perpetual future of coinex
class Coinex():
    __API_KEY = None
    __SECRET_KEY = None
    
    orders = {"opened":[], "closed":[] }
    
    def __init__(self, symbol:str, as_demo:bool = False) :
        self.symbol = symbol
        self.isdemo = as_demo
        self.market = None
        
    def __call__(self, symbol):
        self.symbol = symbol
        
    def __str__(self):
        return f"Coinex object for {self.symbol}"
            
    @property
    def __check_API_keys(self):
        if self.__API_KEY == None or self.__SECRET_KEY == None:
            raise ValueError("API tokens not defined !")
        
        
    def change_API_keys(self, API_key:str, secret_key:str):
        pass
    
    @property
    def get_leverage_val(self):
        pass
    
    def change_leverage(self, n:int , side:str, **kwargs):
        pass
        
    def change_margin_mode(self, new_mode:str, **kwargs ):
        pass
    
    @property
    def get_margin_mode(self):
        pass

    def change_isolated_margin(self, amount:float, side:str):
        pass
    
    
    @staticmethod
    def current_time(as_str = False, as_timestamp = False):
        if as_str and as_timestamp: raise ValueError("return format can be str or timestamp, not both!")
        dt_now = dt.datetime.now()
        dt_now_ts = dt_now.timestamp().__int__() 
        if as_str: return dt.datetime.fromtimestamp(dt_now_ts).__str__() 
        elif as_timestamp: return dt_now_ts 
        else: return dt_now
    
        
    def write_API_keys_as_json_to_file(self, file_name:str = None, dir:str = None):
        self.__check_API_keys
        pwd = os.getcwd()
        if dir != None: os.chdir(dir)
        if file_name == None: file_name = f"coinex_API_keys_{self.current_time(as_str = True)}.json" 
        with open(file_name, "w") as api_file:
            api_file.write(json.dumps({"API_key":self.__API_KEY, "secret_key":self.__SECRET_KEY}))
            api_file.close()
        os.chdir(pwd)
    
            
    def read_API_keys_as_json_from_file(self, file_name:str, dir:str = None):
        pwd = os.getcwd()
        if dir != None: os.chdir(dir)
        with open(file_name, "r") as key_file:
            key_dict = json.load(key_file)
            key_file.close()
        try: self.change_API_keys(key_dict["API_key"], key_dict["secret_key"])
        except: raise ValueError("keys of API_keys json file can be 'API_key', 'secret_key'.")
        os.chdir(pwd)
        
    @property
    def list_available_markets(self) -> list:
        pass
    
    @property
    def get_ticker(self):
        pass
    
    @property
    def assest_details(self) -> dict:
        pass
    
    @property
    def total_balance(self):
        pass
    
    @property
    def available_margin(self):
        pass
    
    @property
    def freezed_margin(self):
        pass
    
    def trade(self, 
            position_side: str,
            quantity:float, 
            order_type : str = None,
            order_price :float = None, 
            stop_price:float = None,
            profit_level:float = None,
            leverage:int = None,
            verify_by_user:bool = True,
            **kwargs
            ):
        
        self.__check_API_keys
        pass
    
    
    def __update_open_close_orders(self, just_current_symbol:bool = True):
       pass
        
    
    @property
    def close_all_orders(self):
        self.__check_API_keys
        ans = input(f"are you sure to close all open orders for {self.symbol}?(y to confirm)")
        if ans != 'y' : return None

        pass
        
        
    def close_order(self, order_id, verify_by_user:bool = True, **kwargs):
        self.__check_API_keys
        if verify_by_user: 
            ans = input(f"are you sure you want to close the {order_id} orderd for {self.symbol}?(y to continue)")
            if ans != 'y': return None
            
        pass
        
    @property
    def get_opened_orders(self):
        pass
    
    @property
    def get_closed_orders(self):
        pass
    
    # def save_orders_to_excel(self, file_name:str = None)
                
    def log_all_orders(self, verbose:bool = True, save_to_file:bool = True):
        log = f'''\n\n
                order log of {self.symbol} at {self.current_time(True)}: 
                
                open orders for {self.symbol}:
                
                {self.orders["opened"]}
                
                
                closed orders for {self.symbol}:
                
                {self.orders["closed"]}\n  

              '''
        if verbose: print(log)
        
        if save_to_file:
            file_name = f"coinex_api_{self.symbol}_{self.current_time(True)}.txt"
            with open(file_name, "a") as file:
                file.write(log)
                file.close()
            print(f"\n log saved at {file_name}")
            
        return log
            
            
    def get_order(self, order_id:int) -> dict:
        for type_ in self.orders.keys():
            for order in self.orders[type_]:
                if order_id in order.keys():
                    return type_, {order_id: order[order_id]}

    
    def log_order(self, order_id:int):
        type_ , order = self.get_order(order_id)
        log = f'''\n\n
                order {order_id} is {type_} order
                parameters:
                {order[order_id]} 
              '''
        print(log)
        return log
        
        
        
        

    
    
    
        
        
        