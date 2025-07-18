#!/bin/bash
# this script is used to boot a Docker container
exec gunicorn -b :5000 --workers=3 --worker-class gevent --access-logfile - --error-logfile - timingcloud:app
