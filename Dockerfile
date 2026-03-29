# 生产镜像，仅包含应用代码
FROM ghcr.io/xinnan-tech/xiaozhi-esp32-server:server-base

# Install Caddy reverse proxy for single-port Railway deploy
RUN apt-get update && apt-get install -y --no-install-recommends \
    debian-keyring debian-archive-keyring apt-transport-https curl && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && apt-get install -y caddy && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY main/xiaozhi-server .

# 启动应用 (via entrypoint to inject env vars + start Caddy)
RUN chmod +x entrypoint.sh
CMD ["bash", "entrypoint.sh"]