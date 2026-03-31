# 生产镜像，仅包含应用代码
FROM ghcr.io/xinnan-tech/xiaozhi-esp32-server:server-base

COPY main/xiaozhi-server .

# 启动应用 (via entrypoint to inject env vars)
RUN chmod +x entrypoint.sh
CMD ["bash", "entrypoint.sh"]