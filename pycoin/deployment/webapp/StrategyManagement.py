from fastapi import APIRouter
from pycoin.deployment.webapp.strategies.pivotStrategy import pivotStrategyAPI

router = APIRouter(prefix = "/strategies", tags = ["strategies"])

router.include_router(pivotStrategyAPI.strategy_api.router)



