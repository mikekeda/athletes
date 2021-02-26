"""Gunicorn config."""
bind = "unix:/uwsgi/athletes.sock"
workers = 2
timeout = 300
max_requests = 100
daemon = False
umask = "91"
user = "nginx"
loglevel = "info"
