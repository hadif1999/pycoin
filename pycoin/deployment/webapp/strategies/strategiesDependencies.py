from . import Run_PivotStrategy
from fastapi import Depends
from typing import Annotated
from ..dependencies import _Read_APIkeys_fromEnv



celeryTaskRetryPolicy_conf = {'max_retries': 3,
                              'interval_start': 0,
                              'interval_step': 0.2,
                              'interval_max': 0.2,
                              'retry_errors': None }


