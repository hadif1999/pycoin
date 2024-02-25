from abc import ABC, abstractmethod, abstractproperty

class _BASE(ABC):
    
    @abstractmethod
    def make_order(self): pass
    
    
    @abstractproperty
    def available_markets(self): pass
    
    @abstractmethod
    def open_positions(self): pass
    
    @abstractmethod
    def pending_orders(self): pass
    
    @abstractmethod
    def closed_positions(self): pass
    
    
    @abstractmethod
    def cancel_orders(self, IDs:list): pass
    
    @abstractproperty
    def cancel_allOrders(self): pass
    
    @abstractmethod
    def close_position(self): pass
    
    @abstractproperty
    def close_allPositions(self): pass
    
    @abstractproperty
    def get_ticker(self): pass
    
    @abstractproperty
    @property
    def assest_details(self): pass
    
    @abstractproperty
    @property
    def total_balance(self): pass
    
    @abstractproperty
    @property
    def available_margin(self): pass

    @abstractproperty
    @property
    def freezed_margin(self): pass
    
    @abstractmethod
    def add_SL(self, amount:float, at:float, side:str): pass
    
    @abstractmethod
    def add_TP(self, amount, at, side:str): pass
    
    @abstractproperty
    @property
    def current_fee(self): pass
        
    
    
    
    
     
    
    
    
  
    
    
    