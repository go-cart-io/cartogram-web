FROM python:3.12-slim-bookworm

COPY ./internal /root/internal

RUN apt-get update && apt-get -y install cron wget
RUN (crontab -l ; echo "0 0 * * * wget -O /root/cron.txt http://localhost:5000/cleanup") | crontab

RUN apt-get -y install gcc libgeos-dev libjpeg-dev zlib1g-dev libfftw3-dev nlohmann-json3-dev libcairo2-dev libomp-dev libcgal-dev
RUN pip install --upgrade pip
RUN pip install -r /root/internal/requirements.txt

EXPOSE 5000
WORKDIR /root/internal