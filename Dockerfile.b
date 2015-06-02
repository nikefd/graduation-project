############################################################
# Dockerfile to build TJCodeIDE Containers
# # Based on Ubuntu
# ############################################################

# Set the base image to Ubuntu
FROM nikefd/tjide 

ADD . /opt/gr
