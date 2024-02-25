from fastapi import APIRouter, Depends, HTTPException, Request
from . import celery_app
from celery.canvas import Signature
from typeguard import typechecked
from .strategiesDependencies import Run_PivotStrategy
from typing import Annotated


class _STRATEGY_API:

    active_tasks = []
    
    @typechecked
    def __init__(self, strategy_main_loop_task:Signature, 
                 strategy_prefix_name:str = "pivotStrategy") -> None:
        
        self.strategy_name = strategy_prefix_name
        self.loop_task = strategy_main_loop_task
        
        self.router = APIRouter(prefix = f"/{self.strategy_name}", 
                                tags = [f"{self.strategy_name}", "strategies"])
        
        self.router.add_api_route("/start", self.Start, methods = ["GET"])
        self.router.add_api_route("/stop", self.Stop, methods = ["GET"])
        self.router.add_api_route("/", self.Log, methods = ["GET"])
        self.router.add_api_route("/log", self.Log, methods = ["GET"])
            
    
    @property # get active tasks sorted from newest to oldest
    async def _ActiveTasks(self) -> list[dict]:
        inspector = celery_app.control.inspect()
        each_worker_tasks = inspector.active(safe = True).values()
        tasks_list = [task for task_list in each_worker_tasks for task in task_list
                      if self.strategy_name in task["name"] ]
        tasks_list_sorted = sorted(tasks_list, key = lambda x: x['time_start'])
        return tasks_list_sorted
        
        
    @property
    async def _terminate_AllActiveTasks(self):
        tasks = await self._ActiveTasks
        if not tasks: return
        for taskID in tasks:
            celery_app.control.terminate( taskID['id'] )
            
    @property
    async def _Last_ActivatedTaskID(self):
        taskIDs = await self._ActiveTasks
        if taskIDs == []: return None
        return taskIDs[0]['id']

    
    @property
    async def _terminate_LastActivatedTask(self):
        task = await self._Last_ActivatedTaskID
        if task: celery_app.control.terminate(task)
    
    
    async def Start(self, Strategy_dep: Annotated[Run_PivotStrategy, Depends(Run_PivotStrategy)], 
                    UpdateTime_Interval:int = 60, remove_previous: bool = False,
                    removeAll_previous:bool = False, close_openPositions:bool = False,
                    cancel_PendingOrders:bool = False):
        
        print(f"starting {self.strategy_name}...")
        # remove previous task 
        if remove_previous: await self._terminate_LastActivatedTask
        if removeAll_previous: await self._terminate_AllActiveTasks
        
        # remove previous position and orders if needed
        if close_openPositions: await Strategy_dep.strategy.market.close_allPositions(False)
        if cancel_PendingOrders: await Strategy_dep.strategy.market.cancel_allOrders(False)
        
        # running strategy main loop
        Loop_task = self.loop_task.delay(interval = UpdateTime_Interval, 
                                         Strategy_obj = Strategy_dep)
                
        print(f"\n{self.strategy_name} started with id : {Loop_task.id}\n\n")
        
        return {"msg":f"strategy(task) {self.strategy_name} starting ...",
                "tasks":[ {"id": Loop_task.id,
                           "name": Loop_task.name,
                           "status": Loop_task.status} ]}


    async def Stop(self, All:bool = False):
        print(f"\n\nstopping {self.strategy_name} ...")
        if All: 
            tasks = await self._ActiveTasks
            task_data = [{'id':task['id'], "name":task["name"], "status":"STOPPED"}
                         for task in tasks]
            await self._terminate_AllActiveTasks
        else:
            task = celery_app.AsyncResult(await self._Last_ActivatedTaskID) 
            task_data = [{"id": task.id, "name":task.name, "status":task.status}]
            await self._terminate_LastActivatedTask
        
        print(f"{self.strategy_name} stopped")
        return {"msg":f"strategy/strategies(task/tasks) {self.strategy_name} stopping...",
                "tasks":task_data}
    
    
    async def Log(self):
        return await self._ActiveTasks
    