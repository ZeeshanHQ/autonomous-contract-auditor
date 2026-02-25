import os

# Gunicorn configuration for Render.com Free Tier
# Memory limit is 512MB, so we use a single worker

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True
