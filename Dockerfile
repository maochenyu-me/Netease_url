# Python 3.12：requirements.txt 里锁了 click==8.2.1，它要求 Python >= 3.10。
# 所有二进制依赖在 3.12 下都有 musllinux wheel（amd64 + arm64）。
# alpine 3.23 跟随上游；3.12 + alpine3.23 这一组合未经本仓库 CI 验证过时请回退到 alpine3.21。
FROM python:3.12-alpine3.23

# OCI 元信息（GHCR 会读取，便于追溯镜像来源）
LABEL org.opencontainers.image.title="netease-url" \
      org.opencontainers.image.description="网易云音乐解析 API，含 /stream 流式播放端点" \
      org.opencontainers.image.source="https://github.com/maochenyu-me/Netease_url" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    PORT=5000

WORKDIR /app

# ffmpeg 用于写元数据；curl 供 HEALTHCHECK 与容器内自测
RUN apk add --no-cache ffmpeg curl

# 依赖单独一层，改代码不会让这层缓存失效
COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip3 config set global.index-url "$PIP_INDEX_URL" && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .
# cookie.txt 被 .dockerignore 排除（不进镜像），运行时用 -e MUSIC_COOKIE 或 -v 挂载
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/downloads

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" > /dev/null || exit 1

CMD ["/app/entrypoint.sh"]
