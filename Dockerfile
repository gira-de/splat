FROM ubuntu:24.04
# remove ubuntu user to fix permission issue in DevContainers
RUN userdel -r ubuntu || true

# === general ===
# Always use UTF-8 with default language:
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Don't ask questions, because splat will run non-interactively:
ENV DEBIAN_FRONTEND=noninteractive

# === asdf ===
ENV ASDF_DATA_DIR="/splat/.asdf"
ENV PATH="$ASDF_DATA_DIR/shims:$PATH"

# === python ===
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

# === pipenv ===
# Don't create virtual envs in home folder, but directly in the app's project folder:
ENV PIPENV_VENV_IN_PROJECT=1
# When calling "pipenv" while running in a virtual environment,
# use the virtual environment from the project folder instead of the active one:
ENV PIPENV_IGNORE_VIRTUALENVS=1

# === poetry ===
ENV POETRY_VERSION=2.0.1
# When calling "poetry" while running in a virtual environment,
# use the virtual environment from the project folder instead of the active one:
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
# Install splat deps into the system environment:
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && \
    apt-get install -y libnss-wrapper \
    # prepare dependencies for asdf
    curl git wget software-properties-common gnupg2 apt-transport-https \
    # asdf-nodejs
    dirmngr gawk \
    # yarn
    gpg \
    # github-actions
    jq

# Add the deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update

# Install all actively supported python versions.
# Please UPDATE when new python versions are released or support ends for older python versions:
RUN apt-get install -y \
    python3.8 python3.8-distutils python3.8-venv \
    python3.9 python3.9-distutils python3.9-venv \
    python3.10 python3.10-distutils python3.10-venv \
    python3.11 python3.11-distutils python3.11-venv \
    python3.12 python3.12-venv \
    python3.13 python3.13-venv \
    python3-pip

RUN pip3 install --break-system-packages \
    poetry==$POETRY_VERSION \
    pipenv \
    uv


# === node.js (v20.x) ===
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# === yarn ===
RUN npm install -g corepack \
    && corepack enable \
    && corepack prepare yarn@stable --activate

# === Splat deps install globally ===
WORKDIR /splat/
COPY pyproject.toml poetry.lock ./
RUN pip install poetry-plugin-export==1.9.0 --break-system-packages && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install -r requirements.txt --break-system-packages

COPY splat/ splat/
COPY bin/splat bin/splat
COPY splat/utils/aggregate_summaries.py aggregate_summaries.py
RUN chmod +x bin/splat \
    && ln -s /splat/bin/splat /usr/local/bin/splat

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN groupadd --gid 1000 splatuser \
    && useradd --uid 1000 --gid splatuser \
    --home-dir /home/splatuser --create-home --shell /bin/sh splatuser

RUN chown -R splatuser:splatuser /splat && \
    chmod -R a+rwX /splat

RUN mkdir -p /home/hostuser \
    && chmod a+rwX /home/hostuser

USER splatuser
ENV HOME=/home/splatuser

# === runtime envs ===
ENV PATH="/usr/local/bin:$ASDF_DATA_DIR/shims:/splat/bin/:$PATH" \
    # Allow virtual env creation for cloned projects
    POETRY_VIRTUALENVS_CREATE=true \
    # Don't try to symlink dependencies:
    UV_LINK_MODE=copy \
    # Allow "splat" to be used as a python module (there is a folder /splat/splat/):
    PYTHONPATH="/splat/"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
