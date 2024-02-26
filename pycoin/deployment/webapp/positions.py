from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pycoin.deployment.webapp import dependencies 

market_dep = dependencies.market_dependency
router = APIRouter(prefix = "/positions", tags = ["positions"])

@router.get("/")
async def logPositions(market:market_dep, AllSymbols:bool = True, side:str|None = None):
    if not side:
        return await market.AllSymbols_PositionsAmt if AllSymbols \
        else await market.CurrentSymbol_TOTAL_PositionsAmt
        
    elif side.upper() == "LONG":
        return await (market.AllSymbols_LONG_PositionsAmt if AllSymbols  
        else market.CurrentSymbol_LONG_PositionsAmt)
        
    elif side.upper() == "SHORT":
        return await (market.AllSymbols_SHORT_PositionsAmt if AllSymbols 
                else market.AllSymbols_SHORT_PositionsAmt)

    
@router.get("/log" )
async def LogPositions(request: Request):
    url = request.url_for("logPositions")
    return RedirectResponse(url)
    
    
@router.get("/closeAll")
async def closePositions(market:market_dep, AllSymbols:bool = False):
    return await market.close_allPositions(AllSymbols = AllSymbols)
    
    



    