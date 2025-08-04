FROM python:3.12-slim-bookworm

RUN apt-get update
RUN apt-get -y install gcc libgeos-dev
RUN pip install --upgrade pip setuptools wheel

COPY ./internal /root/internal
COPY ./data /root/data

RUN echo "deb http://archive.debian.org/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://archive.debian.org/debian/ stretch-proposed-updates main contrib non-free" > /etc/apt/sources.list
RUN echo "deb http://archive.debian.org/debian-security stretch/updates main contrib non-free" > /etc/apt/sources.list.d/sources.list

RUN pip install --upgrade pip
RUN pip install -r /root/internal/requirements.txt

EXPOSE 5000
WORKDIR /root/internal