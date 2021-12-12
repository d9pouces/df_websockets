from enum import Enum


class Worker(Enum):
    WORKER_CELERY = "celery"
    WORKER_CHANNEL = "channels"
    WORKER_PROCESS = "process"
    WORKER_THREAD = "thread"
