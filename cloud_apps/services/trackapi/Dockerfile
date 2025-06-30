FROM python:3.12

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY app app
COPY trackapi.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP=trackapi.py
ENV FLASK_DEBUG=1
ENV DATABASE_DOCKER_URL=postgresql://nick:password@postgres/test_scans

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
