#!/bin/bash
# this script is used to boot a Docker container
exec gunicorn -b :5000 --access-logfile - --error-logfile - results:app
