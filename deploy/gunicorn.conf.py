"""Gunicorn config for the Flask backend.

Run from the backend directory:
gunicorn -c ../deploy/gunicorn.conf.py run:app
"""
import multiprocessing
import os


bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:5001")
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
