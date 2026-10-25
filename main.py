"""网易云音乐API服务主程序

提供网易云音乐相关API服务，包括：
- 歌曲信息获取
- 音乐搜索
- 歌单和专辑详情
- 音乐下载
- 健康检查
"""

import logging
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote
import requests
from flask import Flask, request, send_file, render_template, Response, stream_with_context

try:
    from music_api import (
        NeteaseAPI, APIException, QualityLevel, APIConstants,
        url_v1, name_v1, lyric_v1, search_music,
        playlist_detail, album_detail,
        load_cookies,
    )
    from music_downloader import MusicDownloader, DownloadException, AudioFormat
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块存在且可用")
    sys.exit(1)


@dataclass
class APIConfig:
    """API配置类"""
    host: str = '0.0.0.0'
    port: int = 5000
    debug: bool = False
    downloads_dir: str = 'downloads'
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    request_timeout: int = 30
    log_level: str = 'INFO'
    cors_origins: str = '*'


class APIResponse:
    """API响应工具类"""
    
    @staticmethod
    def success(data: Any = None, message: str = 'success', status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """成功响应"""
        response = {
            'status': status_code,
            'success': True,
            'message': message
        }
        if data is not None:
            response['data'] = data
        return response, status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str = None) -> Tuple[Dict[str, Any], int]:
        """错误响应"""
        response = {
            'status': status_code,
            'success': False,
            'message': message
        }
        if error_code:
            response['error_code'] = error_code
        return response, status_code


class MusicAPIService:
    """音乐API服务类"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.netease_api = NeteaseAPI()
        self.downloader = MusicDownloader()

        # 创建下载目录
        self.downloads_path = Path(config.downloads_dir)
        self.downloads_path.mkdir(exist_ok=True)

        self.logger.info(f"音乐API服务初始化完成，下载目录: {self.downloads_path.absolute()}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('music_api')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            try:
                file_handler = logging.FileHandler('music_api.log', encoding='utf-8')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"无法创建日志文件: {e}")
        
        return logger
    
    def _get_cookies(self) -> Dict[str, str]:
        """直接从 cookie.txt 读取并解析为 dict"""
        try:
            cookies = load_cookies()
            if not cookies:
                self.logger.warning("cookie.txt 为空或不存在，部分接口（VIP 音质）将不可用")
            return cookies
        except Exception as e:
            self.logger.error(f"读取 cookie.txt 异常: {e}")
            return {}
    
    def _extract_music_id(self, id_or_url: str) -> str:
        """提取音乐ID"""
        try:
            # 处理短链接
            if '163cn.tv' in id_or_url:
                import requests
                response = requests.get(id_or_url, allow_redirects=False, timeout=10)
                id_or_url = response.headers.get('Location', id_or_url)
            
            # 处理网易云链接
            if 'music.163.com' in id_or_url:
                index = id_or_url.find('id=') + 3
                if index > 2:
                    return id_or_url[index:].split('&')[0]
            
            # 直接返回ID
            return str(id_or_url).strip()
            
        except Exception as e:
            self.logger.error(f"提取音乐ID失败: {e}")
            return str(id_or_url).strip()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f}{units[unit_index]}"
    
    def _get_quality_display_name(self, quality: str) -> str:
        """获取音质显示名称"""
        quality_names = {
            'standard': "标准音质",
            'exhigh': "极高音质", 
            'lossless': "无损音质",
            'hires': "Hi-Res音质",
            'sky': "沉浸环绕声",
            'jyeffect': "高清环绕声",
            'jymaster': "超清母带",
            'dolby': "杜比全景声"
        }
        return quality_names.get(quality, f"未知音质({quality})")
    
    def _validate_request_params(self, required_params: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], int]]:
        """验证请求参数"""
        for param_name, param_value in required_params.items():
            if not param_value:
                return APIResponse.error(f"参数 '{param_name}' 不能为空", 400)
        return None
    
    def _safe_get_request_data(self) -> Dict[str, Any]:
        """安全获取请求数据"""
        try:
            if request.method == 'GET':
                return dict(request.args)
            else:
                # 优先使用JSON数据，然后是表单数据
                json_data = request.get_json(silent=True) or {}
                form_data = dict(request.form)
                # 合并数据，JSON优先
                return {**form_data, **json_data}
        except Exception as e:
            self.logger.error(f"获取请求数据失败: {e}")
            return {}


# 创建Flask应用和服务实例
config = APIConfig()
app = Flask(__name__)
api_service = MusicAPIService(config)


@app.before_request
def before_request():
    """请求前处理"""
    # 记录请求信息
    api_service.logger.info(
        f"{request.method} {request.path} - IP: {request.remote_addr} - "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )


@app.after_request
def after_request(response: Response) -> Response:
    """请求后处理 - 设置CORS头"""
    response.headers.add('Access-Control-Allow-Origin', config.cors_origins)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    
    # 记录响应信息
    api_service.logger.info(f"响应状态: {response.status_code}")
    return response


@app.errorhandler(400)
def handle_bad_request(e):
    """处理400错误"""
    return APIResponse.error("请求参数错误", 400)


@app.errorhandler(404)
def handle_not_found(e):
    """处理404错误"""
    return APIResponse.error("请求的资源不存在", 404)


@app.errorhandler(500)
def handle_internal_error(e):
    """处理500错误"""
    api_service.logger.error(f"服务器内部错误: {e}")
    return APIResponse.error("服务器内部错误", 500)


@app.route('/')
def index() -> str:
    """首页路由"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查API"""
    try:
        # 检查 Cookie 状态：直接读 cookie.txt
        cookies = load_cookies()
        cookie_status = 'valid' if cookies else 'invalid'

        health_info = {
            'service': 'running',
            'timestamp': int(time.time()) if 'time' in sys.modules else None,
            'cookie_status': cookie_status,
            'cookie_count': len(cookies),
            'downloads_dir': str(api_service.downloads_path.absolute()),
            'version': '2.0.0'
        }

        return APIResponse.success(health_info, "API服务运行正常")
        
    except Exception as e:
        api_service.logger.error(f"健康检查失败: {e}")
        return APIResponse.error(f"健康检查失败: {str(e)}", 500)


@app.route('/song', methods=['GET', 'POST'])
@app.route('/Song_V1', methods=['GET', 'POST'])  # 向后兼容
def get_song_info():
    """获取歌曲信息API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        song_ids = data.get('ids') or data.get('id')
        url = data.get('url')
        level = data.get('level', 'lossless')
        info_type = data.get('type', 'url')
        
        # 参数验证
        if not song_ids and not url:
            return APIResponse.error("必须提供 'ids'、'id' 或 'url' 参数")
        
        # 提取音乐ID
        music_id = api_service._extract_music_id(song_ids or url)
        
        # 验证音质参数
        valid_levels = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster', 'dolby']
        if level not in valid_levels:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_levels)}")
        
        # 验证类型参数
        valid_types = ['url', 'name', 'lyric', 'json']
        if info_type not in valid_types:
            return APIResponse.error(f"无效的类型参数，支持: {', '.join(valid_types)}")
        
        cookies = api_service._get_cookies()
        
        # 根据类型获取不同信息
        if info_type == 'url':
            result = url_v1(music_id, level, cookies)
            if result and result.get('data') and len(result['data']) > 0:
                song_data = result['data'][0]
                response_data = {
                    'id': song_data.get('id'),
                    'url': song_data.get('url'),
                    'level': song_data.get('level'),
                    'quality_name': api_service._get_quality_display_name(song_data.get('level', level)),
                    'size': song_data.get('size'),
                    'size_formatted': api_service._format_file_size(song_data.get('size', 0)),
                    'type': song_data.get('type'),
                    'bitrate': song_data.get('br')
                }
                return APIResponse.success(response_data, "获取歌曲URL成功")
            else:
                return APIResponse.error("获取音乐URL失败，可能是版权限制或音质不支持", 404)
        
        elif info_type == 'name':
            result = name_v1(music_id)
            return APIResponse.success(result, "获取歌曲信息成功")
        
        elif info_type == 'lyric':
            result = lyric_v1(music_id, cookies)
            return APIResponse.success(result, "获取歌词成功")
        
        elif info_type == 'json':
            # 获取完整的歌曲信息（用于前端解析）
            song_info = name_v1(music_id)
            url_info = url_v1(music_id, level, cookies)
            lyric_info = lyric_v1(music_id, cookies)
            
            if not song_info or 'songs' not in song_info or not song_info['songs']:
                return APIResponse.error("未找到歌曲信息", 404)
            
            song_data = song_info['songs'][0]
            
            # 构建前端期望的响应格式
            response_data = {
                'id': music_id,
                'name': song_data.get('name', ''),
                'ar_name': ', '.join(artist['name'] for artist in song_data.get('ar', [])),
                'al_name': song_data.get('al', {}).get('name', ''),
                'pic': song_data.get('al', {}).get('picUrl', ''),
                'level': level,
                'lyric': lyric_info.get('lrc', {}).get('lyric', '') if lyric_info else '',
                'tlyric': lyric_info.get('tlyric', {}).get('lyric', '') if lyric_info else ''
            }
            
            # 添加URL和大小信息
            if url_info and url_info.get('data') and len(url_info['data']) > 0:
                url_data = url_info['data'][0]
                response_data.update({
                    'url': url_data.get('url', ''),
                    'size': api_service._format_file_size(url_data.get('size', 0)),
                    'level': url_data.get('level', level)
                })
            else:
                response_data.update({
                    'url': '',
                    'size': '获取失败'
                })
            
            return APIResponse.success(response_data, "获取歌曲信息成功")
            
    except APIException as e:
        api_service.logger.error(f"API调用失败: {e}")
        return APIResponse.error(f"API调用失败: {str(e)}", 500)
    except Exception as e:
        api_service.logger.error(f"获取歌曲信息异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"服务器错误: {str(e)}", 500)


@app.route('/search', methods=['GET', 'POST'])
@app.route('/Search', methods=['GET', 'POST'])  # 向后兼容
def search_music_api():
    """搜索音乐API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        keyword = data.get('keyword') or data.get('keywords') or data.get('q')
        limit = int(data.get('limit', 30))
        offset = int(data.get('offset', 0))
        search_type = data.get('type', '1')  # 1-歌曲, 10-专辑, 100-歌手, 1000-歌单
        
        # 参数验证
        validation_error = api_service._validate_request_params({'keyword': keyword})
        if validation_error:
            return validation_error
        
        # 限制搜索数量
        if limit > 100:
            limit = 100
        
        cookies = api_service._get_cookies()
        result = search_music(keyword, cookies, limit)
        
        # search_music返回的是歌曲列表，需要包装成前端期望的格式
        if result:
            for song in result:
                # 添加艺术家字符串（如果需要）
                if 'artists' in song:
                    song['artist_string'] = song['artists']
        
        return APIResponse.success(result, "搜索完成")
        
    except ValueError as e:
        return APIResponse.error(f"参数格式错误: {str(e)}")
    except Exception as e:
        api_service.logger.error(f"搜索音乐异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"搜索失败: {str(e)}", 500)


@app.route('/playlist', methods=['GET', 'POST'])
@app.route('/Playlist', methods=['GET', 'POST'])  # 向后兼容
def get_playlist():
    """获取歌单详情API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        playlist_id = data.get('id')
        
        # 参数验证
        validation_error = api_service._validate_request_params({'playlist_id': playlist_id})
        if validation_error:
            return validation_error
        
        cookies = api_service._get_cookies()
        result = playlist_detail(playlist_id, cookies)
        
        # 适配前端期望的响应格式
        response_data = {
            'status': 'success',
            'playlist': result
        }
        
        return APIResponse.success(response_data, "获取歌单详情成功")
        
    except Exception as e:
        api_service.logger.error(f"获取歌单异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"获取歌单失败: {str(e)}", 500)


@app.route('/album', methods=['GET', 'POST'])
@app.route('/Album', methods=['GET', 'POST'])  # 向后兼容
def get_album():
    """获取专辑详情API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        album_id = data.get('id')
        
        # 参数验证
        validation_error = api_service._validate_request_params({'album_id': album_id})
        if validation_error:
            return validation_error
        
        cookies = api_service._get_cookies()
        result = album_detail(album_id, cookies)
        
        # 适配前端期望的响应格式
        response_data = {
            'status': 200,
            'album': result
        }
        
        return APIResponse.success(response_data, "获取专辑详情成功")
        
    except Exception as e:
        api_service.logger.error(f"获取专辑异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"获取专辑失败: {str(e)}", 500)


@app.route('/download', methods=['GET', 'POST'])
@app.route('/Download', methods=['GET', 'POST'])  # 向后兼容
def download_music_api():
    """下载音乐API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        music_id = data.get('id')
        quality = data.get('quality', 'lossless')
        return_format = data.get('format', 'file')  # file 或 json
        
        # 参数验证
        validation_error = api_service._validate_request_params({'music_id': music_id})
        if validation_error:
            return validation_error
        
        # 验证音质参数
        valid_qualities = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster', 'dolby']
        if quality not in valid_qualities:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_qualities)}")
        
        # 验证返回格式
        if return_format not in ['file', 'json']:
            return APIResponse.error("返回格式只支持 'file' 或 'json'")
        
        music_id = api_service._extract_music_id(music_id)
        cookies = api_service._get_cookies()
        
        # 获取音乐基本信息
        song_info = name_v1(music_id)
        if not song_info or 'songs' not in song_info or not song_info['songs']:
            return APIResponse.error("未找到音乐信息", 404)
        
        # 获取音乐下载链接
        url_info = url_v1(music_id, quality, cookies)
        if not url_info or 'data' not in url_info or not url_info['data'] or not url_info['data'][0].get('url'):
            return APIResponse.error("无法获取音乐下载链接，可能是版权限制或音质不支持", 404)
        
        # 构建音乐信息
        song_data = song_info['songs'][0]
        url_data = url_info['data'][0]
        
        music_info = {
            'id': music_id,
            'name': song_data['name'],
            'artist_string': ', '.join(artist['name'] for artist in song_data['ar']),
            'album': song_data['al']['name'],
            'pic_url': song_data['al']['picUrl'],
            'file_type': url_data['type'],
            'file_size': url_data['size'],
            'duration': song_data.get('dt', 0),
            'download_url': url_data['url']
        }
        
        # 生成安全文件名
        safe_name = f"{music_info['name']} [{quality}]"
        safe_name = ''.join(c for c in safe_name if c not in r'<>:"/\|?*')
        filename = f"{safe_name}.{music_info['file_type']}"
        
        file_path = api_service.downloads_path / filename
        
        # 检查文件是否已存在
        if file_path.exists():
            api_service.logger.info(f"文件已存在: {filename}")
        else:
            # 使用优化后的下载器下载
            try:
                download_result = api_service.downloader.download_music_file(
                    music_id, quality
                )
                
                if not download_result.success:
                    return APIResponse.error(f"下载失败: {download_result.error_message}", 500)
                
                file_path = Path(download_result.file_path)
                api_service.logger.info(f"下载完成: {filename}")
                
            except DownloadException as e:
                api_service.logger.error(f"下载异常: {e}")
                return APIResponse.error(f"下载失败: {str(e)}", 500)
        
        # 根据返回格式返回结果
        if return_format == 'json':
            response_data = {
                'music_id': music_id,
                'name': music_info['name'],
                'artist': music_info['artist_string'],
                'album': music_info['album'],
                'quality': quality,
                'quality_name': api_service._get_quality_display_name(quality),
                'file_type': music_info['file_type'],
                'file_size': music_info['file_size'],
                'file_size_formatted': api_service._format_file_size(music_info['file_size']),
                'file_path': str(file_path.absolute()),
                'filename': filename,
                'duration': music_info['duration']
            }
            return APIResponse.success(response_data, "下载完成")
        else:
            # 返回文件下载
            if not file_path.exists():
                return APIResponse.error("文件不存在", 404)
            
            try:
                response = send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=filename,
                    mimetype=f"audio/{music_info['file_type']}"
                )
                response.headers['X-Download-Message'] = 'Download completed successfully'
                response.headers['X-Download-Filename'] = quote(filename, safe='')
                return response
            except Exception as e:
                api_service.logger.error(f"发送文件失败: {e}")
                return APIResponse.error(f"文件发送失败: {str(e)}", 500)
            
    except Exception as e:
        api_service.logger.error(f"下载音乐异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"下载异常: {str(e)}", 500)


@app.route('/api/info', methods=['GET'])
def api_info():
    """API信息接口"""
    try:
        info = {
            'name': '网易云音乐API服务',
            'version': '2.0.0',
            'description': '提供网易云音乐相关API服务',
            'endpoints': {
                '/health': 'GET - 健康检查',
                '/song': 'GET/POST - 获取歌曲信息',
                '/search': 'GET/POST - 搜索音乐',
                '/playlist': 'GET/POST - 获取歌单详情',
                '/album': 'GET/POST - 获取专辑详情',
                '/download': 'GET/POST - 下载音乐',
                '/stream': 'GET - 流式播放（边下边发，支持 Range）',
                '/api/info': 'GET - API信息'
            },
            'supported_qualities': [
                'standard', 'exhigh', 'lossless', 
                'hires', 'sky', 'jyeffect', 'jymaster'
            ],
            'config': {
                'downloads_dir': str(api_service.downloads_path.absolute()),
                'max_file_size': f"{config.max_file_size // (1024*1024)}MB",
                'request_timeout': f"{config.request_timeout}s"
            }
        }
        
        return APIResponse.success(info, "API信息获取成功")
        
    except Exception as e:
        api_service.logger.error(f"获取API信息异常: {e}")
        return APIResponse.error(f"获取API信息失败: {str(e)}", 500)


@app.route('/stream', methods=['GET', 'HEAD'])
def stream_music():
    """流式转发音频：边下边发，透传 Range（支持拖动进度）。

    与 /download 的区别：
      /download   先把整首歌下载到服务器磁盘，再 send_file —— 13MB 的歌首字节要 12 秒；
      /stream     拿到 CDN 直链后直接用 requests 的 stream 转发，首字节约 0.3~1 秒，
                  并且把 Range / Content-Range / Content-Length 原样透传，
                  <audio> 才能算总时长、拖进度条。
    """
    try:
        song_id = request.args.get('id') or request.args.get('ids') or request.args.get('url')
        level = request.args.get('level', 'exhigh')

        if not song_id:
            return APIResponse.error("缺少 'id' 参数")

        valid_levels = ['standard', 'exhigh', 'lossless', 'hires',
                        'sky', 'jyeffect', 'jymaster', 'dolby']
        if level not in valid_levels:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_levels)}")

        music_id = api_service._extract_music_id(song_id)
        cookies = api_service._get_cookies()
        # 直链带时效签名，每次现取，不缓存
        try:
            url_info = _resolve_song_url(music_id, level, cookies)
        except Exception as e:
            api_service.logger.warning(f"/stream 取直链失败 id={music_id}: {e}")
            return APIResponse.error("获取播放链接失败（上游网络异常），请重试", 502)

        data = (url_info or {}).get('data') or []
        upstream_url = data[0].get('url') if data else None
        if not upstream_url:
            return APIResponse.error("获取音乐URL失败，可能是版权限制或音质不支持", 404)

        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER,
        }
        # 浏览器拖动进度时会带 Range，原样转给 CDN
        range_header = request.headers.get('Range')
        if range_header:
            headers['Range'] = range_header

        upstream = requests.get(upstream_url, headers=headers, stream=True, timeout=config.request_timeout)
        if upstream.status_code not in (200, 206):
            code = upstream.status_code
            upstream.close()
            api_service.logger.warning(f"/stream 上游返回 {code}: {song_id}")
            return APIResponse.error(f"上游返回 {code}", 502)

        response = Response(
            stream_with_context(_iter_upstream(upstream)),
            status=upstream.status_code,
            content_type=upstream.headers.get('Content-Type', 'audio/mpeg'),
        )
        # 分片信息必须原样透传，否则浏览器算不出总时长、拖不动进度条
        for header in ('Content-Length', 'Content-Range', 'Accept-Ranges'):
            if header in upstream.headers:
                response.headers[header] = upstream.headers[header]
        # Werkzeug 会给 str 型 content-type 自动补 `; charset=UTF-8`，音频不需要
        response.headers['Content-Type'] = upstream.headers.get('Content-Type', 'audio/mpeg').split(';')[0].strip()
        # 少数 CDN 节点不回 Accept-Ranges，但实际支持 Range；补上让浏览器敢拖进度
        response.headers.setdefault('Accept-Ranges', 'bytes')
        response.headers['Cache-Control'] = 'no-store'

        # HEAD 只回响应头（客户端探测可用性用），不占着上游连接
        if request.method == 'HEAD':
            upstream.close()
            response.response = []

        return response

    except Exception as e:
        api_service.logger.error(f"/stream 异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"流式转发失败: {str(e)}", 500)


def _resolve_song_url(music_id, level: str, cookies, attempts: int = 3):
    """取播放直链，失败重试几次（网易云接口偶发断连，一次失败就报错太脆）。"""
    last_error = None
    for i in range(attempts):
        try:
            return url_v1(music_id, level, cookies)
        except Exception as e:
            last_error = e
            if i < attempts - 1:
                time.sleep(0.4 * (i + 1))
    raise last_error


def _iter_upstream(upstream, chunk_size: int = 64 * 1024):
    """按块转发上游响应体，异常或客户端断开时保证关闭连接。"""
    try:
        for chunk in upstream.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
    finally:
        upstream.close()


def start_api_server():
    """启动API服务器"""
    try:
        print("\n" + "="*60)
        print("🚀 网易云音乐API服务启动中...")
        print("="*60)
        print(f"📡 服务地址: http://{config.host}:{config.port}")
        print(f"📁 下载目录: {api_service.downloads_path.absolute()}")
        print(f"📋 日志级别: {config.log_level}")
        print("\n📚 API端点:")
        print(f"  ├─ GET  /health        - 健康检查")
        print(f"  ├─ POST /song          - 获取歌曲信息")
        print(f"  ├─ POST /search        - 搜索音乐")
        print(f"  ├─ POST /playlist      - 获取歌单详情")
        print(f"  ├─ POST /album         - 获取专辑详情")
        print(f"  ├─ POST /download      - 下载音乐")
        print(f"  ├─ GET  /stream        - 流式播放（支持 Range）")
        print(f"  └─ GET  /api/info      - API信息")
        print("\n🎵 支持的音质:")
        print(f"  standard, exhigh, lossless, hires, sky, jyeffect, jymaster")
        print("="*60)
        print(f"⏰ 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("🌟 服务已就绪，等待请求...\n")
        
        # 启动Flask应用
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        api_service.logger.error(f"启动服务失败: {e}")
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    start_api_server()

