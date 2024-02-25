from celery import Celery
import os
from pycoin.deployment import celeryConfig

modules = ["pycoin.deployment.webapp.strategies.pivotStrategy.pivotStrategyCore"]

cloudamqp_brok = 'amqp://wdwlkcxg:DJkfokvz7rdFcnsT-ZJzyqcHkrFP4kVw@sparrow-01.rmq.cloudamqp.com:5672/wdwlkcxg'
liara_mysql = 'db+mysql+pymysql://root:QegPczR0cw1sfRpMjUTpbp8y@billy.iran.liara.ir:33157/upbeat_shtern'
redis_db = "redis://:CD6empYY2EPyWvbVaM7071UN@damavand.liara.cloud:34305/0"

app = Celery("pycoin", 
             broker = cloudamqp_brok,
             backend = redis_db,
             include = modules)


app.config_from_object(celeryConfig)
app.control.add_consumer('strategies', reply = True)


if __name__ == '__main__':
    app.start()