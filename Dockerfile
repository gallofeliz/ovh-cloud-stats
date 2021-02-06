FROM python:alpine

RUN pip install ovh

WORKDIR /app

ADD app.py .

CMD ./app.py
