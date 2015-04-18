FROM ubuntu:14.04

MAINTAINER nikefd <nikefd@gmail.com>

RUN apt-get update
RUN apt-get install -y build-essential python python-tornado strace python-pip
RUN pip install tailer

WORKDIR /opt/gr

ADD . /opt/gr

EXPOSE 8889

CMD ["python /opt/gr/server.py"]
