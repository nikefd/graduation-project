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
RUN apt-get install -y python2.7 python-tornado python-pip libffi-dev libssl-dev python-dev

RUN pip install bcrypt futures Markdown torndb

#expose ports
EXPOSE 8888

# Set the default directory where CMD will execute
WORKDIR /opt/gr


#RUN groupadd -r postgres && useradd -r -g postgres tjide && echo "tjide:tjide" | chpasswd && adduser tjide sudo
RUN groupadd -r postgres && useradd -r -g postgres tjide && echo "tjide:123456" | chpasswd && adduser tjide sudo

RUN mkdir -p /home/tjide && chown -R tjide:postgres /home/tjide

ADD . /opt/gr
#ENTRYPOINT ["python", "server.py"]
ENTRYPOINT ["/bin/bash"]
