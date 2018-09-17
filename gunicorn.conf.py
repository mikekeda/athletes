# -*- coding: utf-8 -*-
"""
Gunicorn config.
"""
bind = '127.0.0.1:8000'
workers = 1
# worker_class = 'eventlet'
worker_class = 'gevent'
timeout = 300
max_requests = 100
daemon = False
reload = True
# check_config = True

loglevel = 'debug'
