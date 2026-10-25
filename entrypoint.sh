#!/bin/sh
set -e

# 四个参数原来传 --level/--mode/--url，但 main.py 从来没解析过命令行参数（无 argparse / 无 sys.argv），
# 等于死配置。改成环境变量驱动，见 main.py 里 config = APIConfig() 之后那段：
#   HOST / PORT / LOG_LEVEL / CORS_ORIGINS / DOWNLOADS_DIR / MUSIC_COOKIE
echo "[entrypoint] 启动网易云解析服务，端口 ${PORT:-5000}，cookie 来源：$([ -n "$MUSIC_COOKIE" ] && echo '环境变量 MUSIC_COOKIE' || echo 'cookie.txt')"
exec python3 main.py
