from pycoin import celery_app
from pycoin.deployment.webapp.strategies.pivotStrategy.pivotStrategyCore import runPivotStrategy
from pycoin.deployment.webapp.strategies import _STRATEGY_API
from typing import Annotated
from pycoin.deployment.webapp.strategies import Run_PivotStrategy
from fastapi import Depends


class PIVOTSTRATEGY_API(_STRATEGY_API):
    
    async def Start(self, Strategy_dep: Annotated[Run_PivotStrategy, Depends(Run_PivotStrategy)], 
                    UpdateTime_Interval: int = 60, remove_previous: bool = False,
                    close_openPositions: bool = False, cancel_PendingOrders: bool = False):
        
        return await super().Start(Strategy_dep, UpdateTime_Interval,
                                   remove_previous, close_openPositions,
                                   cancel_PendingOrders)
    

            
strategy_api = PIVOTSTRATEGY_API(strategy_main_loop_task = runPivotStrategy.s(),
                                 strategy_prefix_name = "pivotStrategy")

