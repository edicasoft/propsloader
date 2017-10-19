############################################################
# Dockerfile to build Python 3 Application Containers
# Based on Ubuntu
############################################################

FROM ubuntu:16.04
MAINTAINER Igor Kurochka <ikurochka@gmail.com>

# Setup environment
ENV DEBIAN_FRONTEND noninteractive

# replace default command interpreter to `bash` to be able to use `source`
RUN ln -snf /bin/bash /bin/sh

# Update sources
RUN apt-get update -y

# Install basic applications
RUN apt-get install -y tar git curl mc wget dialog net-tools build-essential \
        apt-transport-https \
        ca-certificates \
        libssl-dev

# Install python3
RUN apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -sf /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && ln -sf /usr/bin/pip3 pip

# Instal project dependencies
RUN apt-get install -y libmemcached-dev \
  libmysqlclient-dev

# install supervisord
RUN apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor
ADD ./supervisord.conf /etc/

# rm apt lists
RUN rm -rf /var/lib/apt/lists/*


# Install project pip requirements
ADD ./requirements.txt /project/
RUN cd /project \
  && pip install -U -r requirements.txt



WORKDIR /project/app

CMD ["supervisord", "-n"]
