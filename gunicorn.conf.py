"""
Gunicorn production config for brighter-nepal-api.
Run: gunicorn -c gunicorn.conf.py run:app
"""
import multiprocessing

# Workers: (2 × CPU cores) + 1 is the standard formula
workers = multiprocessing.cpu_count() * 2 + 1

# Use sync worker — best for I/O-bound Flask with SQLAlchemy
worker_class = 'sync'

# Each worker handles up to 1000 simultaneous connections in queue
backlog = 1000

# Max number of requests a worker serves before being recycled
# Prevents memory leaks in long-running workers
max_requests = 1000
max_requests_jitter = 100   # stagger recycling so not all die at once

# Timeouts
timeout = 60            # kill worker if request takes > 60s
graceful_timeout = 30   # give 30s for in-flight requests to finish on reload
keepalive = 5           # keep connection alive for 5s for subsequent requests

# Binding
bind = '0.0.0.0:5000'

# Logging
accesslog = '-'         # stdout
errorlog  = '-'         # stderr
loglevel  = 'warning'   # only warnings/errors in production (not info spam)

# Pre-load app to share memory and detect startup errors early
preload_app = True
