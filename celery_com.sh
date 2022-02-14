#!/bin/bash

python3 manage.py runserver
celery -A hedge worker -l info
celery -A hedge beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler