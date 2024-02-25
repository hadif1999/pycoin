from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Annotated
import pandas as pd
from . import dependencies 
from starlette.datastructures import URL


market_dep = dependencies.market_dependency

router = APIRouter(prefix = "/orders", tags = ["orders"])

@router.get("/")
async def logOrders(market:market_dep,  AllSymbols:bool = True, side:str|None = None):
    if not side:
        return await market.AllSymbols_OrdersAmt if AllSymbols \
        else await market.CurrentSymbol_TOTAL_OrdersAmt
        
    elif side.upper() == "LONG":
        return await (market.AllSymbols_LONG_OrdersAmt if AllSymbols  
        else market.CurrentSymbol_LONG_OrdersAmt)
        
    elif side.upper() == "SHORT":
        return await (market.AllSymbols_SHORT_OrdersAmt if AllSymbols 
                else market.AllSymbols_SHORT_OrdersAmt)
        
        
@router.get("/log" )
async def Logorders(request: Request):
    url = request.url_for("logOrders")
    return RedirectResponse(url)


@router.get("/cancelAll")
async def cancellOrders(market:market_dep, AllSymbols:bool = False):
    return await market.cancel_allOrders(AllSymbols = AllSymbols)



@router.get("/SLTPs/")
async def getSLTPs(market:market_dep, AllSymbols:bool = True, side:str|None = None):
    if not side: 
        return await (market.AllSymbols_PendingSLTPs if AllSymbols 
                else market.CurrentSymbol_PendingSLTPs)
        
    elif side.upper() == "LONG":
        return await (market.AllSymbols_LONG_PendingSLTPs if AllSymbols 
                else market.CurrentSymbol_LONG_PendingSLTPs)
        
    elif side.upper() == "SHORT":
        return await (market.AllSymbols_SHORT_PendingSLTPs if AllSymbols
                else market.CurrentSymbol_SHORT_PendingSLTPs)
        
    else: raise HTTPException(3000, "side arg can be 'LONG', 'SHORT' or None ")
    
    
@router.get("/SLs/")
async def getSLs(market:market_dep, AllSymbols:bool = True, side:str|None = None):
    if not side: 
        return await (market.AllSymbols_PendingSLs if AllSymbols 
                else market.CurrentSymbol_PendingSLs)
        
    elif side.upper() == "LONG":
        return await (market.AllSymbols_LONG_PendingSLs if AllSymbols 
                else market.CurrentSymbol_LONG_PendingSLs)
        
    elif side.upper() == "SHORT":
        return await (market.AllSymbols_SHORT_PendingSLs if AllSymbols
                else market.CurrentSymbol_SHORT_PendingSLs)
        
    else: raise HTTPException(3000, "side arg can be 'LONG', 'SHORT' or None ")
    
    
@router.get("/TPs/")
async def getTPs(market:market_dep, AllSymbols:bool = True, side:str|None = None):
    if not side: 
        return await (market.AllSymbols_PendingTPs if AllSymbols 
                else market.CurrentSymbol_PendingTPs)
        
    elif side.upper() == "LONG":
        return await (market.AllSymbols_LONG_PendingTPs if AllSymbols 
                else market.CurrentSymbol_LONG_PendingTPs)
        
    elif side.upper() == "SHORT":
        return await (market.AllSymbols_SHORT_PendingTPs if AllSymbols
                else market.CurrentSymbol_SHORT_PendingTPs)
        
    else: raise HTTPException(3000, "side arg can be 'LONG', 'SHORT' or None ")
    
    
