FROM python:3-slim

COPY ./internal /root/internal
COPY ./data /root/data

RUN apt-get update && apt-get -y install cron curl
RUN (crontab -l ; echo "0 0 * * * curl http://localhost:5000/cleanup") | crontab

RUN apt-get -y install gcc libgeos-dev libjpeg-dev zlib1g-dev
RUN pip install --upgrade pip
RUN pip install -r /root/internal/requirements.txt

EXPOSE 5000
WORKDIR /root/internal