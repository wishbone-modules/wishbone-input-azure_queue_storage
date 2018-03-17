FROM            smetj/wishbone:latest
MAINTAINER      Jelle Smet
ARG             branch
RUN             apk add --update alpine-sdk python3 python3-dev build-base libffi libffi-dev openssl-dev
RUN             LC_ALL=en_US.UTF-8 /usr/bin/pip3 install --process-dependency-link https://github.com/wishbone-modules/wishbone-input-azure_queue_storage/archive/$branch.zip
RUN             rm -rf /var/cache/apk/*
