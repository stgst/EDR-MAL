FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip openssh-client openssh-server && \
    apt-get clean

# RUN pip3 install psutil

RUN useradd -ms /bin/bash ctf
RUN mkdir -p /home/ctf/.ssh && \
    chown -R ctf:ctf /home/ctf/.ssh

RUN echo '#!/bin/bash\n\
ssh-keygen -t ed25519 -N "" -f /home/ctf/.ssh/id_ed25519 -q\n\
chown -R ctf:ctf /home/ctf/.ssh\n\
exec python3 runner.py' > /start.sh && \
    chmod +x /start.sh

WORKDIR /app
COPY . /app
RUN chown -R ctf:ctf /app

USER ctf
ENTRYPOINT ["/start.sh"]