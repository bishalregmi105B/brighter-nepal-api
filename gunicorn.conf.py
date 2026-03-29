"""
Gunicorn production config for brighter-nepal-api.
Optimised for 4 vCPU / 8 GB RAM VPS.
Run: gunicorn -c gunicorn.conf.py run:app
"""
import multiprocessing
import os as _os

# ── Worker strategy ────────────────────────────────────────────────────────
# gevent lets each worker handle thousands of concurrent I/O-bound requests
# instead of blocking one-request-per-worker like the sync class.
worker_class = 'gevent'
workers = int(_os.environ.get('WEB_CONCURRENCY', min(4, multiprocessing.cpu_count())))
worker_connections = 2000         # max greenlets per worker

# ── Connection queue ───────────────────────────────────────────────────────
backlog = 2048

# ── Worker recycling (prevents slow memory leaks) ─────────────────────────
max_requests = 2000
max_requests_jitter = 200

# ── Timeouts ───────────────────────────────────────────────────────────────
timeout = 60
graceful_timeout = 30
keepalive = 5

# ── Binding ────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{_os.environ.get('PORT', '5000')}"

# ── Logging ────────────────────────────────────────────────────────────────
accesslog = '-'
errorlog  = '-'
loglevel  = 'warning'

# Pre-load app so all workers share the same memory footprint
preload_app = True
