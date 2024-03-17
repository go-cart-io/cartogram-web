FROM python:3-slim-bookworm

COPY ./internal /root/internal
COPY ./data /root/data

RUN apt-get update && apt-get -y install cron
RUN (crontab -l ; echo "0 0 * * * /usr/local/bin/python3 /root/internal/cleanup.py > /root/cron.txt") | crontab

RUN apt-get -y install gcc libgeos-dev libjpeg-dev zlib1g-dev
RUN pip install --upgrade pip
RUN pip install -r /root/internal/requirements.txt

EXPOSE 5000
WORKDIR /root/internal