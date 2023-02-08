# functionary development image
# This Dockerfile assumes that the docker-compose.yml in this project is used
# to start things, and thus neede volume mounts etc. will be in place. It is
# not intended as a general purpose Dockerfile.
FROM python:3.10-slim

ARG uid=1000
ARG user=functionary
ARG install_dir=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# initial setup
RUN apt-get update && \
    apt-get install -y \
    # python build deps
    make gcc python3-dev libpq-dev

RUN useradd -l -m -u $uid $user && \
    mkdir -p $install_dir && \
    chown $user:$user -R $install_dir

WORKDIR $install_dir
USER $user
RUN echo "source $HOME/venv/bin/activate" >> $HOME/.bashrc

# pip installs
COPY requirements.txt requirements-dev.txt $install_dir/
RUN python -m venv $HOME/venv && \
    bash -c "source $HOME/venv/bin/activate && pip install --upgrade pip" && \
    bash -c "source $HOME/venv/bin/activate && pip install -r $install_dir/requirements.txt -r $install_dir/requirements-dev.txt"

ENTRYPOINT ["./run.sh"]
CMD ["start"]
