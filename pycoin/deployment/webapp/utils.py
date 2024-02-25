
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from . import dependencies
from typing import Annotated
from fastapi.responses import PlainTextResponse


market_dep = dependencies.market_dependency

router = APIRouter()

@router.get("/leverage", tags = ["leverage"])
async def get_leverages(market:market_dep, side:str|None = None):
    if not side: return market._get_leverages
    elif side.upper() == "LONG": return await market.LONG_leverage
    elif side.upper() == "SHORT": return await market.SHORT_leverage
    else: raise HTTPException(3000, "side can be 'LONG' or 'SHORT' ")
    

@router.get("/leverage/change/{n}", response_class = PlainTextResponse, tags = ["leverage"])
async def change_leverage(market:market_dep, n: Annotated[int, Path(gt = 0)], 
                          side:str|None = None):
    if not side:
        await market.Change_Leverage("LONG", n = n)
        await market.Change_Leverage("SHORT", n = n )
        return f"'LONG' and 'SHORT' leverages changed to {n} for {market.symbol} symbol"
    
    elif side.upper() in ["LONG", "SHORT"]:
        await market.Change_Leverage(side = side, n = n)
        return f" {side.upper()} leverage changed to {n} for {market.symbol} symbol"
    else: 
        raise HTTPException(3000, "side can be 'LONG' or 'SHORT'")