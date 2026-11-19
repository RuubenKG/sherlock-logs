import sys
import json
import time
import socket
import logging
import platform
from datetime import datetime, timezone

import psutil
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,  # üles-alla (app_requests_in_progress) — see on minu custom metric
    generate_latest,
    CONTENT_TYPE_LATEST,
)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, "extra_fields"):
            entry.update(record.extra_fields)
        return json.dumps(entry)
    
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)

_handler.setFormatter(JsonFormatter())
logger.addHandler(_handler)
logger.propagate = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total number of HTTP requests handled by the backend.",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "app_request_duration_seconds",
    "Duration of HTTP requests in seconds.",
    ["method", "endpoint"],
)

IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "Number of HTTP requests currently being processed.",
)


@app.middleware("http")
async def observer(request: Request, call_next):

    if request.url.path == "/metrics":
        return await call_next(request)
    
    IN_PROGRESS.inc()
    start = time.perf_counter()
    status = 500  
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:

        elapsed = time.perf_counter() - start

        REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)
        REQUEST_COUNT.labels(request.method, request.url.path, status).inc()
        IN_PROGRESS.dec()

        level = logging.ERROR if status >= 500 else logging.INFO
        logger.log(level, "http_request", extra={"extra_fields": {
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "duration_ms": round(elapsed * 1000, 2),
            "client": request.client.host if request.client else None,
        }})

@app.get("/metrics")
def metrics():

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/info")
def system_info():
    
    memory = psutil.virtual_memory()
    cpu_freq = psutil.cpu_freq()

    return {
        "hostname": socket.gethostname(),
        "os_type": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "cpu_freq_mhz": round(cpu_freq.current) if cpu_freq else "N/A",
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "memory_total_mb": round(memory.total / 1024 / 1024),
        "memory_used_mb": round(memory.used / 1024 / 1024),
        "memory_free_mb": round(memory.available / 1024 / 1024),
        "memory_used_percent": memory.percent,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/boom")
def boom():
    raise Exception("deliberate test error")