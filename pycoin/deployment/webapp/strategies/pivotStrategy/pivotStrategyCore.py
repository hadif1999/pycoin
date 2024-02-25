from .. import Run_PivotStrategy
from .. import celery_app as app
from ..strategiesDependencies import celeryTaskRetryPolicy_conf
import time
from celery.utils.log import get_task_logger

logger = get_task_logger("strategies.pivotStrategy.log")

@app.task(bind = True, name = "strategies.pivotStrategy.run", 
          retry_policy = celeryTaskRetryPolicy_conf, queue = "strategies",
          track_started = True, default_retry_delay = 20, ignore_result=True)
def runPivotStrategy(self, Strategy_obj:Run_PivotStrategy, interval:int = 60):    
    
    Strategy_obj.strategy.update_pivots
    while True:
        try:
            Strategy_obj.log
            Strategy_obj.posLog
            Strategy_obj.RUN()
            logger.info(f"*** sleeping for {interval} seconds\n\n")
            time.sleep(interval)
            logger.info("updating data ...\n\n")
            Strategy_obj.update_data()
        except Exception as e: 
            logger.error(f"ERROR {e} occurred in pivotStrategy task with id: {self.request.id}\n\n")
            raise self.retry(exc = e)
        