FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive TZ=UTC \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget git jq ripgrep fd-find tree less vim-tiny nano \
    python3 python3-pip python3-venv python3-dev build-essential nodejs npm \
    openssh-client zip unzip tar gzip bzip2 xz-utils procps iproute2 iputils-ping \
    dnsutils net-tools && rm -rf /var/lib/apt/lists/*

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash agent && \
    mkdir -p /workspace /aifile /userfile /app /run/agent-ssh && \
    chown -R agent:agent /workspace /aifile /userfile /app

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt
COPY app /app/app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh && chown -R agent:agent /app

EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
