web: flask db upgrade; flask translate compile; gunicorn timingctrl:app
worker: rq worker timingctrl-tasks
