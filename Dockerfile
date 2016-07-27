FROM mbodenhamer/python-dev:latest
COPY dev/ /usr/local/bin/

# Install docker client
RUN curl -sSL -O https://get.docker.com/builds/Linux/x86_64/docker-1.9.1.tgz \
    && tar zxf docker-1.9.1.tgz -C / \
    && rm docker-1.9.1.tgz
