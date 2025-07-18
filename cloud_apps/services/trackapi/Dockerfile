FROM python:3.12

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app
COPY trackapi.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP=trackapi.py


EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
