# 网易云音乐无损解析

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/Suxiaoqinx/Netease_url?style=flat-square)
![GitHub forks](https://img.shields.io/github/forks/Suxiaoqinx/Netease_url?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/Suxiaoqinx/Netease_url?style=flat-square)
![GitHub license](https://img.shields.io/github/license/Suxiaoqinx/Netease_url?style=flat-square)

**功能强大的网易云音乐解析工具**

支持歌曲搜索 | 单曲解析 | 歌单解析 | 专辑解析 | 音乐下载

[在线体验](https://wyapi.toubiec.cn) • [使用文档](./使用文档.md) • [问题反馈](https://github.com/Suxiaoqinx/Netease_url/issues)

</div>

---

## 授权说明 / License

本仓库中的源代码基于 **MIT License** 开源，任何人可按 MIT 条款使用、修改和分发本仓库代码。

⚠️ 注意：
线上体验版本（Online Demo / 官网体验页）是作者另行独立开发的闭源产品，
不属于本仓库 MIT 代码的一部分。
线上版本的权利声明以对应产品页面为准（可能标注 All rights reserved）。

简单说：
- 本仓库代码 → MIT
- 线上体验站 → 闭源，独立作品

## ✨ 功能特性

### 🎵 核心功能
- **🔍 歌曲搜索**：支持关键词搜索网易云音乐库中的歌曲
- **🎧 单曲解析**：解析单首歌曲的详细信息和下载链接
- **📋 歌单解析**：批量解析歌单中的所有歌曲信息
- **💿 专辑解析**：批量解析专辑中的所有歌曲信息
- **⬇️ 音乐下载**：支持多种音质的音乐文件下载

### 🎼 音质支持
- `standard`：标准音质 (128kbps)
- `exhigh`：极高音质 (320kbps)
- `lossless`：无损音质 (FLAC)
- `hires`：Hi-Res音质 (24bit/96kHz)
- `jyeffect`：高清环绕声
- `sky`：沉浸环绕声
- `jymaster`：超清母带

### 🌐 使用方式
- **Web界面**：直观友好的网页操作界面
- **RESTful API**：完整的API接口支持
- **批量处理**：支持歌单和专辑的批量解析
- **多格式支持**：支持ID和链接多种输入格式

---

## 🚀 快速开始

### 环境要求
- Python 3.10+（推荐 Python 3.12，与 Docker 镜像一致）
- 网易云音乐黑胶会员账号

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/Suxiaoqinx/Netease_url.git
cd Netease_url
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置Cookie
在 `cookie.txt` 文件中填入黑胶会员账号的Cookie：

> 💡 **获取Cookie方法**：登录网易云音乐网页版 → F12开发者工具 → Network标签页 → 复制任意请求的Cookie值


> 杜比全景声音质需要设备支持，不同的设备可能会返回不同码率的 url cookie 需要传入os=pc保证返回正常码率的 url

#### 4. 启动服务
```bash
python main.py
```

#### 5. 访问界面
打开浏览器访问：`http://localhost:5000`

### 🐳 Docker部署

镜像由 GitHub Actions 自动构建（amd64 / arm64），推到 GHCR：

```bash
# 直接跑（把 MUSIC_U 换成自己的）
docker run -d --name netease-url -p 5000:5000 \
  -e MUSIC_COOKIE='MUSIC_U=xxxx' \
  --restart unless-stopped \
  ghcr.io/maochenyu-me/netease-url:latest

# 或者用 compose（cookie 写在 .env 里）
cp .env.example .env && vi .env
docker compose up -d
```

自己构建：`docker build -t netease-url .`
（国内网络加 `--build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/`）

---

## 📖 使用指南

### Web界面使用

#### 🔍 歌曲搜索
1. 选择功能：**歌曲搜索**
2. 输入关键词（歌曲名、歌手名等）
3. 点击**搜索**按钮
4. 在搜索结果中点击**解析**或**下载**按钮

#### 🎧 单曲解析
1. 选择功能：**单曲解析**
2. 输入歌曲ID或网易云音乐链接
   - 支持格式：`1234567890` 或 `https://music.163.com/song?id=1234567890`
3. 点击**解析**按钮查看歌曲信息

#### 📋 歌单解析
1. 选择功能：**歌单解析**
2. 输入歌单ID或网易云音乐歌单链接
   - 支持格式：`1234567890` 或 `https://music.163.com/playlist?id=1234567890`
3. 点击**解析**按钮查看歌单中所有歌曲
4. 点击单首歌曲的**解析**或**下载**按钮

#### 💿 专辑解析
1. 选择功能：**专辑解析**
2. 输入专辑ID或网易云音乐专辑链接
   - 支持格式：`1234567890` 或 `https://music.163.com/album?id=1234567890`
3. 点击**解析**按钮查看专辑中所有歌曲
4. 点击单首歌曲的**解析**或**下载**按钮

#### ⬇️ 音乐下载
1. 选择功能：**音乐下载**
2. 输入歌曲ID或链接
3. 选择音质（标准/极高/无损/Hi-Res等）
4. 点击**下载**按钮

### 支持的链接格式

```
# 歌曲链接
https://music.163.com/song?id=1234567890
https://music.163.com/#/song?id=1234567890

# 歌单链接
https://music.163.com/playlist?id=1234567890
https://music.163.com/#/playlist?id=1234567890

# 专辑链接
https://music.163.com/album?id=1234567890
https://music.163.com/#/album?id=1234567890

# 直接使用ID
1234567890
```

## 🔌 API接口文档

### 基础信息
- **Base URL**: `http://localhost:5000`
- **请求方式**: GET / POST（GET 时参数走 query string；POST 支持 JSON 或表单，JSON 优先）
- **响应格式**: JSON，统一结构为 `{"status": 200, "success": true, "message": "...", "data": {...}}`，
  出错时 `success` 为 `false` 且不带 `data`

### 接口列表

> 兼容性别名：`/Search`、`/Song_V1`、`/Playlist`、`/Album`、`/Download` 与对应小写接口完全等价，老客户端不用改。

#### 1. 健康检查
```http
GET /health
```
**响应示例**:
```json
{
  "status": 200,
  "success": true,
  "message": "API服务运行正常",
  "data": {
    "service": "running",
    "timestamp": 1762712345,
    "cookie_status": "valid",
    "cookie_count": 12,
    "downloads_dir": "/app/downloads",
    "version": "2.1.0"
  }
}
```

`cookie_status` 为 `valid` / `invalid`——容器里用 `MUSIC_COOKIE` 环境变量注入也算 `valid`，
可以直接拿来当 K8s / compose 的存活探针（镜像里的 `HEALTHCHECK` 就是打这个接口）。

#### 2. 歌曲搜索
```http
POST /search
Content-Type: application/json

{
  "keywords": "周杰伦 稻香",
  "limit": 10
}
```
也可以走 GET：`GET /search?keywords=周杰伦 稻香&limit=10`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `keywords` | 是 | 关键词，别名 `keyword` / `q` |
| `limit` | 否 | 返回条数，默认 30，上限 100 |

**响应示例**:
```json
{
  "status": 200,
  "success": true,
  "message": "搜索完成",
  "data": [
    {
      "id": 185668,
      "name": "稻香",
      "artists": "周杰伦",
      "album": "魔杰座",
      "picUrl": "http://p1.music.126.net/xxx.jpg",
      "artist_string": "周杰伦"
    }
  ]
}
```

`data` 直接是歌曲数组；`artists` 是**用 `/` 拼好的字符串**（多歌手如 `周杰伦/费玉清`），不是数组。

#### 3. 单曲解析
```http
POST /song
Content-Type: application/json

{
  "id": "185668"
}
```

#### 4. 歌单解析
```http
POST /playlist
Content-Type: application/json

{
  "id": "123456789"
}
```

#### 5. 专辑解析
```http
POST /album
Content-Type: application/json

{
  "id": "123456789"
}
```

#### 6. 音乐下载
```http
POST /download
Content-Type: application/json

{
  "id": "185668",
  "quality": "lossless"
}
```
**响应**: 直接返回音频文件流

#### 7. 流式播放（本项目新增）
```http
GET /stream?id=185668&level=exhigh
```
**响应**: `audio/mpeg` 流，支持 `Range`（可拖进度条）

和 `/download` 的区别：`/download` 会**先把整首歌下载到服务器磁盘再发**，13MB 的歌首字节要 12 秒；
`/stream` 拿到直链后**边下边发**，首字节 0.3 秒左右，适合给网页播放器当 `<audio src>`。

```bash
# 探测可用性（HEAD 只回响应头）
curl -I "http://127.0.0.1:5000/stream?id=185668&level=exhigh"
# 期望: 200 / 206、Content-Type: audio/mpeg、Accept-Ranges: bytes

# 测首字节
curl -o /dev/null -w "TTFB=%{time_starttransfer}s\n" -r 0-65535 \
  "http://127.0.0.1:5000/stream?id=185668&level=exhigh"
```

> 直链会在进程内存里缓存 5 分钟（`URL_CACHE_TTL` 可调，`0` 关闭）。
> 因为一次播放会被浏览器拆成多个 Range 请求，不缓存的话每个分片都要重新换一次直链（1~2 秒）；
> 命中缓存后只剩 CDN 往返，实测 TTFB 从 ~2s 降到 ~0.1s。
> 直链过期或被防盗链（403/410）时会自动丢弃缓存、重新解析并重试一次。

> ⚠️ 反代到 nginx 时**必须关掉缓冲**，否则等于又变回 `/download` 的行为：
> ```nginx
> location / {
>     proxy_pass http://127.0.0.1:5000;
>     proxy_buffering off;
>     proxy_request_buffering off;
>     proxy_http_version 1.1;
>     proxy_read_timeout 300s;
> }
> ```

#### 8. API 信息
```http
GET /api/info
```
**响应示例**:
```json
{
  "status": 200,
  "success": true,
  "message": "API信息获取成功",
  "data": {
    "name": "网易云音乐API服务",
    "version": "2.1.0",
    "description": "提供网易云音乐相关API服务",
    "endpoints": {
      "/health": "GET - 健康检查",
      "/song": "GET/POST - 获取歌曲信息",
      "/search": "GET/POST - 搜索音乐",
      "/playlist": "GET/POST - 获取歌单详情",
      "/album": "GET/POST - 获取专辑详情",
      "/download": "GET/POST - 下载音乐",
      "/stream": "GET - 流式播放（边下边发，支持 Range）",
      "/api/info": "GET - API信息"
    },
    "supported_qualities": ["standard", "exhigh", "lossless", "hires", "sky", "jyeffect", "jymaster"],
    "config": {
      "downloads_dir": "/app/downloads",
      "max_file_size": "500MB",
      "request_timeout": "30s"
    }
  }
}
```

**用途**：能力自发现。前端或客户端启动时打一次，就能拿到服务版本、全部端点、支持的音质和关键配置，
不用把接口清单硬编码在前端——后续加接口，前端跟着自动适配。

> `supported_qualities` 是**接口自报的**音质列表，实际解析时 `/song`、`/download`、`/stream`
> 还额外接受 `dolby` 参数（这里没列进去，是当前实现的已知小偏差）；以实际调用是否 404 为准。
>
> `downloads_dir` 是运行时的绝对路径：容器内为 `/app/downloads`，本地直接 `python main.py`
> 则是项目下 `downloads/` 的绝对路径。

---

## 音质参数说明（仅限单曲解析）

- `standard`：标准音质
- `exhigh`：极高音质
- `lossless`：无损音质
- `hires`：Hi-Res音质
- `jyeffect`：高清环绕声
- `sky`：沉浸环绕声
- `jymaster`：超清母带
- `dolby`：杜比全景声

> 黑胶VIP音质：standard, exhigh, lossless, hires, jyeffect  
> 黑胶SVIP音质：sky, jymaster  
> `dolby` 需要账号有对应权益，拿不到直链时接口返回 404

---

## Docker 一键部署

### 1. 拉镜像（推荐）

```bash
docker pull ghcr.io/maochenyu-me/netease-url:latest
```

> 私有镜像要先登录：`echo $GITHUB_TOKEN | docker login ghcr.io -u <你的用户名> --password-stdin`

### 2. 配 cookie（二选一）

**a) 环境变量**（最简单，改完 restart 生效）

```bash
docker run -d --name netease-url -p 5000:5000 \
  -e MUSIC_COOKIE='整条 cookie 粘这里' \
  --restart unless-stopped \
  ghcr.io/maochenyu-me/netease-url:latest
```

**b) 挂载文件**（不想把 cookie 写进 `docker run` 历史）

```bash
cp cookie.txt.example cookie.txt && vi cookie.txt     # 粘整条 cookie
docker run -d --name netease-url -p 5000:5000 \
  -v "$(pwd)/cookie.txt:/app/cookie.txt:ro" \
  --restart unless-stopped \
  ghcr.io/maochenyu-me/netease-url:latest
```

> 镜像里**不含** cookie（`.dockerignore` 已排除）。没给 cookie 也能跑，只是 VIP/无损拿不到。

### 3. 用 compose（推荐长期用）

```bash
cp .env.example .env
vi .env            # 填 MUSIC_COOKIE
docker compose up -d
docker compose logs -f
```

`.env` / `cookie.txt` 都在 `.gitignore` 里，不会误提交。

### 4. 环境变量

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `MUSIC_COOKIE` | 空 | 整条网易云 cookie，优先级高于 `cookie.txt` |
| `PORT` | `5000` | 容器内监听端口，改了要同步改 `ports` 映射 |
| `LOG_LEVEL` | `INFO` | DEBUG / INFO / WARNING / ERROR |
| `CORS_ORIGINS` | `*` | 允许的前端来源，纯前端直连保持 `*` |
| `DOWNLOADS_DIR` | `downloads` | `/download` 的临时目录 |
| `URL_CACHE_TTL` | `300` | 播放直链的内存缓存秒数，`0` 关闭 |

### 5. 反代（nginx / Caddy）

**必须关掉响应缓冲**，否则 `/stream` 会退化成 `/download` 的体验（首字节十几秒）：

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_buffering off;
    proxy_request_buffering off;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 300s;
}
```

### 6. 部署后自测

```bash
curl -s http://127.0.0.1:5000/health
# {"data":{"cookie_status":"valid","service":"running",...}}

curl -o /dev/null -w "TTFB=%{time_starttransfer}s code=%{http_code}\n" \
  -r 0-65535 "http://127.0.0.1:5000/stream?id=287398&level=exhigh"
# 期望 code=206、TTFB < 1.5s
```

---

## 在线演示

[在线解析](https://wyapi.toubiec.cn/)

---

## 注意事项

- 必须使用黑胶会员账号的 Cookie 才能解析高音质资源。
- Cookie 格式请严格按照 `cookie.txt` 示例填写。

---

## 致谢

- [Ravizhan](https://github.com/ravizhan)

---

## 反馈与交流

- 在 Github [Issues](https://github.com/Suxiaoqinx/Netease_url/issues) 提交反馈
- 或访问 [我的博客](https://www.toubiec.cn)

---

欢迎 Star、Fork 和 PR！



