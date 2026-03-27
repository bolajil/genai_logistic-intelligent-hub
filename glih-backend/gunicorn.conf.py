"""
Gunicorn production configuration for GLIH Backend.
Run with: gunicorn -c gunicorn.conf.py glih_backend.api.main:app
"""
import os
import multiprocessing

# ── Binding ───────────────────────────────────────────────────────────────────
bind    = f"0.0.0.0:{os.getenv('GLIH_BACKEND_PORT', '9001')}"
backlog = 2048          # max queued connections

# ── Workers ───────────────────────────────────────────────────────────────────
# Formula: (2 × CPU cores) + 1  — good for I/O-bound workloads (API calls, DB)
workers     = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"   # async FastAPI workers
threads      = int(os.getenv("GUNICORN_THREADS", "2"))
worker_connections = 1000

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout       = 120    # agent LLM calls can take 30-60s — give headroom
keepalive     = 5
graceful_timeout = 30  # time to finish in-flight requests on shutdown

# ── Logging ───────────────────────────────────────────────────────────────────
loglevel     = os.getenv("LOG_LEVEL", "info")
accesslog    = "-"     # stdout
errorlog     = "-"     # stderr
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Lifecycle hooks ───────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("GLIH Backend starting — workers: %d", workers)

def worker_exit(server, worker):
    server.log.info("Worker %d exited", worker.pid)
