import os
import logging

broker_url = os.getenv("BROKER")
result_backend = os.getenv("BACKEND")

task_serializer = 'pickle'
result_serializer = 'pickle'
accept_content = ["pickle", "json"]
timezone = 'Europe/Oslo'
enable_utc = True

worker_redirect_stdouts_level = "INFO" # changing default log level

task_routes = {"pycoin.deployment.webapp.strategies.*":"strategies"}



