FROM python:3-stretch

COPY ./internal /root/internal
COPY ./data /root/data

RUN echo "deb http://archive.debian.org/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://archive.debian.org/debian/ stretch-proposed-updates main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://archive.debian.org/debian-security stretch/updates main contrib non-free" > /etc/apt/sources.list.d/sources.list
RUN apt-get update && apt-get -y install cron
RUN (crontab -l ; echo "0 0 * * * curl http://localhost:5000/cleanup") | crontab

RUN pip install --upgrade pip
RUN pip install -r /root/internal/requirements.txt

EXPOSE 5000
WORKDIR /root/internal