############################################################
# Dockerfile to build TJCodeIDE Containers
# # Based on Ubuntu
# ############################################################

# Set the base image to Ubuntu
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER nikefd <nikefd@gmail.com>

# Updata the sources list
RUN apt-get update

# Install some tools
RUN apt-get install -y build-essential python python-tornado strace python-pip
RUN pip install tailer

#expose ports
EXPOSE 8889

# Set the default directory where CMD will execute
WORKDIR /opt/gr


#RUN groupadd -r postgres && useradd -r -g postgres foo && echo "foo:foo" | chpasswd && adduser foo sudo
RUN groupadd -r postgres && useradd -r -g postgres foo && echo "foo:123456" | chpasswd && adduser foo sudo

RUN mkdir -p /home/foo && chown -R foo:postgres /home/foo

USER foo

ADD . /opt/gr
#ENTRYPOINT ["python", "server.py"]
ENTRYPOINT ["/bin/bash"]
