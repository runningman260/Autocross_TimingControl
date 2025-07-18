FROM python:3.12

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app
COPY timingctrl.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP=timingctrl.py


EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
