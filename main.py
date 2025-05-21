import os
from datetime import datetime as dt
from pathlib import Path as FPath
from typing import Any, Dict, Optional

import fastapi
from fastapi.responses import PlainTextResponse as TextResp
from loguru import logger as log
from pydantic import BaseModel as BModel
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

REQUESTS_COUNTER = Counter(
    'journal_log_requests_total', 'Total requests to /log endpoint')
SUCCESS_COUNTER = Counter('journal_log_success', 'Successful log operations')
FAILURE_COUNTER = Counter('journal_log_failure', 'Failed logging attempts')
TIME_TRACKER = Histogram('journal_request_duration_seconds', 'Request processing time')

application = fastapi.FastAPI(
    title="JournalService",
    description="API для управления журналами записей",
    version="1.0.1"
)

ENV_GREETING = os.environ.get("APP_GREETING", "Добро пожаловать в приложение")
LOG_LEVEL_SETTING = os.getenv("LOG_LEVEL", "INFO")
STORAGE_PATH = FPath("/srv/journals/app.log")

log.remove()
log.add(STORAGE_PATH, level=LOG_LEVEL_SETTING)
log.add(lambda message: print(message, end=""), level=LOG_LEVEL_SETTING)


class LogEntry(BModel):
    text: str


@application.middleware("http")
async def request_monitor(request: fastapi.Request, next_handler):
    start = dt.now()
    result = await next_handler(request)
    duration = (dt.now() - start).total_seconds() * 1000
    log.debug(f"{request.method} {request.url.path} completed in {duration:.1f}ms")
    return result


@application.get("/", response_class=TextResp)
async def root_handler():
    log.info("Обращение к корневому эндпоинту")
    return ENV_GREETING


@application.get("/healthcheck")
async def health_status() -> Dict[str, str]:
    log.info("Проверка работоспособности сервиса")
    return {"state": "active"}


@application.post("/log")
@TIME_TRACKER.time()
async def create_log_entry(data: LogEntry) -> Dict[str, Any]:
    REQUESTS_COUNTER.inc()
    current_time = dt.now().isoformat(sep=' ', timespec='seconds')

    try:
        with STORAGE_PATH.open('a') as f:
            f.write(f"{current_time} | {data.text}\n")
        
        log.info(f"Записано сообщение: {data.text}")
        SUCCESS_COUNTER.inc()
        
        return {
            "result": "ok",
            "datetime": current_time,
            "details": "Информация сохранена"
        }
    except Exception as err:
        log.error(f"Сбой записи: {err}")
        FAILURE_COUNTER.inc()
        raise fastapi.HTTPException(
            status_code=500, detail=f"Ошибка сохранения: {err}")


@application.get("/entries", response_class=TextResp)
async def read_log_entries() -> str:
    log.info("Запрос на получение логов")

    if not STORAGE_PATH.exists():
        log.warning("Отсутствует файл журнала")
        return "Нет данных"

    try:
        return STORAGE_PATH.read_text(encoding='utf-8')
    except Exception as err:
        log.error(f"Ошибка чтения: {err}")
        raise fastapi.HTTPException(
            status_code=500, detail=f"Ошибка доступа: {err}")


@application.get("/prometheus", response_class=TextResp)
async def metrics_endpoint():
    return TextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@application.on_event("startup")
async def initialization():
    log.success("Сервис инициализирован")
    log.debug(f"Текущий уровень логирования: {LOG_LEVEL_SETTING}")
    log.info(f"Хранилище логов: {STORAGE_PATH}")