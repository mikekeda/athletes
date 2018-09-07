# -*- coding: utf-8 -*-
"""
Gunicorn config.
"""
bind = 'unix:/uwsgi/athletes.sock'
workers = 2
timeout = 30
max_requests = 100
daemon = False
umask = '91'
user = 'nobody'
loglevel = 'info'
