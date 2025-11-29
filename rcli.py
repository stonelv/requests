#!/usr/bin/env python3
"""
HTTP 请求客户端 - 会话持久化增强版
支持 GET/POST/PUT/DELETE 方法，会话持久化，JSON 格式化输出
"""

import argparse
import json
import logging
import os
import re
import time
from typing import Optional, Dict, Any, Union, List

from requests import Session, Response, RequestException
from requests.exceptions import Timeout, ConnectionError, InvalidURL, HTTPError
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

class SessionManager:
    """会话管理类，处理会话的持久化和加载"""
    
    def __init__(self, session_file: str = ".rcli_session"):
        self.session_file = session_file
        self.session = self._load_session()
    
    def _load_session(self) -> Session:
        """从文件加载会话"""
        session = Session()
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # 重建完整的 CookieJar（保留 domain/path 等属性）
                if 'cookies' in session_data:
                    session.cookies = cookiejar_from_dict(session_data['cookies'])
                
                # 恢复完整的请求头
                if 'headers' in session_data:
                    session.headers.update(session_data['headers'])
                
                logging.info("会话已从 %s 加载", self.session_file)
            except Exception as e:
                logging.warning("加载会话失败: %s，将创建新会话", str(e))
        return session
    
    def save_session(self) -> None:
        """保存会话到文件"""
        session_data = {
            'cookies': dict_from_cookiejar(self.session.cookies),  # 保存完整的 cookie 属性
            'headers': dict(self.session.headers),  # 保存完整的请求头
            'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            logging.debug("会话已保存到 %s", self.session_file)
        except Exception as e:
            logging.warning("保存会话失败: %s", str(e))
    
    def clear_session(self) -> None:
        """清除会话文件"""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
            logging.info("会话已清除")
        else:
            logging.info("没有会话文件需要清除")

class ResponseFormatter:
    """响应格式化类，处理响应的美化输出"""
    
    @staticmethod
    def colorize(text: str, color: str, use_color: bool = True) -> str:
        """
        为文本添加颜色
        :param text: 要着色的文本
        :param color: 颜色名称
        :param use_color: 是否启用颜色输出
        :return: 着色后的文本
        """
        if not use_color:
            return text
            
        colors = {
            'red': '31',
            'green': '32',
            'yellow': '33',
            'blue': '34',
            'magenta': '35',
            'cyan': '36',
            'white': '37'
        }
        return f"\033[{colors.get(color, '37')}m{text}\033[0m"
    
    @staticmethod
    def format_json(data: Any, use_color: bool = True) -> str:
        """
        格式化 JSON 数据并添加语法高亮
        :param data: JSON 数据
        :param use_color: 是否启用颜色输出
        :return: 格式化后的 JSON 字符串
        """
        if not data:
            return ""
        
        # 先获取带缩进的JSON字符串
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if not use_color:
            return json_str
        

        
        return json_str
    
    @staticmethod
    def format_response(response: Response, use_color: bool = True, max_body_length: int = 1000) -> str:
        """
        格式化响应输出
        :param response: Response 对象
        :param use_color: 是否启用颜色输出
        :param max_body_length: 响应体最大显示长度
        :return: 格式化后的响应字符串
        """
        colorize = lambda text, color: ResponseFormatter.colorize(text, color, use_color)
        
        # 基本响应信息
        lines = [
            colorize("===== 响应信息 =====", "cyan"),
            f"{colorize('状态码:', 'yellow')} {response.status_code} ({response.reason})",
            f"{colorize('URL:', 'yellow')} {response.url}",
            f"{colorize('时间戳:', 'yellow')} {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{colorize('编码:', 'yellow')} {response.encoding if response.encoding else '未知'}",
            f"{colorize('是否重定向:', 'yellow')} {'是' if response.history else '否'}",
            ""
        ]
        
        # 响应头信息
        lines.append(colorize("===== 响应头 =====", "cyan"))
        for key, value in response.headers.items():
            lines.append(f"{colorize(key + ':', 'yellow')} {value}")
        lines.append("")
        
        # 响应体信息
        lines.append(colorize("===== 响应体 =====", "cyan"))
        
        try:
            # 尝试 JSON 解析
            json_data = response.json()

            formatted_json = ResponseFormatter.format_json(json_data, use_color=use_color)
            
            # 检查是否需要截断
            if len(formatted_json) > max_body_length:
                lines.append(formatted_json[:max_body_length])
                lines.append(colorize(f"... 响应体过长，已截断为 {max_body_length} 字符", "yellow"))
            else:
                lines.append(formatted_json)
        except:
            # 非 JSON 响应，显示原始文本
            text_content = response.text
            if len(text_content) > max_body_length:
                lines.append(text_content[:max_body_length])
                lines.append(colorize(f"... 响应体过长，已截断为 {max_body_length} 字符", "yellow"))
            else:
                lines.append(text_content)
        
        return "\n".join(lines)

class HTTPClient:
    """HTTP 客户端类，处理请求发送"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: int = 10
    ) -> Response:
        """
        发送 HTTP 请求
        :param method: 请求方法
        :param url: 请求 URL
        :param headers: 请求头
        :param data: 请求体
        :param timeout: 超时时间
        :return: Response 对象
        """
        try:
            # 决定使用 json 参数还是 data 参数
            use_json = False
            if headers and isinstance(data, dict):
                content_type = headers.get('Content-Type', '').lower()
                if 'application/json' in content_type:
                    use_json = True
            elif isinstance(data, dict):
                # 默认情况下，字典使用 JSON 格式
                use_json = True
            
            response = self.session_manager.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if use_json and isinstance(data, dict) else None,
                data=data if not use_json or isinstance(data, str) else None,
                timeout=timeout
            )
            
            # 检查 HTTP 错误状态
            response.raise_for_status()
            
            # 保存会话（确保会话持久化）
            self.session_manager.save_session()
            
            return response
        except Timeout:
            raise RequestException(f"请求超时错误: 连接超时，请检查网络或增加超时时间。错误详情: 超过 {timeout} 秒")
        except ConnectionError:
            raise RequestException(f"连接错误: 无法连接到服务器，请检查网络连接和URL是否正确。错误详情: {ConnectionError}")
        except InvalidURL:
            raise RequestException(f"无效的URL: 请检查URL格式是否正确。错误详情: {url}")
        except HTTPError as e:
            raise RequestException(f"HTTP错误: 请求返回非2xx状态码。错误详情: {e}")
        except RequestException as e:
            raise RequestException(f"请求发生异常: {str(e)}")

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description='HTTP 请求客户端 - 会话持久化增强版')
    parser.add_argument('-m', '--method', default='GET', help='请求方法（默认：GET）')
    parser.add_argument('-u', '--url', required=True, help='请求 URL')
    parser.add_argument('-H', '--headers', action='append', help='请求头（格式：Key:Value）')
    parser.add_argument('-d', '--data', help='请求体数据')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='超时时间（默认：10秒）')
    parser.add_argument('--clear-session', action='store_true', help='清除会话')
    parser.add_argument('--verbose', action='store_true', help='启用详细输出模式')
    parser.add_argument('--no-color', action='store_true', help='禁用彩色输出')
    parser.add_argument('--max-body-length', type=int, default=1000, help='响应体最大显示长度（默认：1000）')
    
    args = parser.parse_args()
    
    # 配置日志
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logging_level, format='%(levelname)s: %(message)s')
    
    # 处理清除会话
    if args.clear_session:
        session_manager = SessionManager()
        session_manager.clear_session()
        return
    
    # 初始化会话管理
    session_manager = SessionManager()
    
    # 处理请求头
    headers: Dict[str, str] = {}
    if args.headers:
        for header in args.headers:
            try:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                logging.warning("无效的请求头格式: %s，请使用 Key:Value 格式", header)
    
    # 处理请求体
    data: Optional[Union[str, Dict[str, Any]]] = None
    if args.data:
        # 首先尝试解析为 JSON
        try:
            # 处理命令行常见的 JSON 格式问题
            data_str = args.data.strip()
            
            # 处理 PowerShell 可能导致的引号问题：如果整体被单引号包裹，去除
            if data_str.startswith("'") and data_str.endswith("'"):
                data_str = data_str[1:-1]
            
            # 处理双引号转义问题：将 "" 转换为 "
            data_str = data_str.replace('""', '"')
            
            # 处理键没有双引号的情况
            data_str = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)\s*:', lambda m: f'"{m.group(1)}":', data_str)
            
            # 处理字符串值没有双引号的情况
            # 匹配没有引号的值：在冒号后，逗号或花括号前的内容
            data_str = re.sub(r':\s*([a-zA-Z0-9_\-\s]+?)(?=\s*(,|}))', lambda m: f': "{m.group(1).strip()}"', data_str)
            
            # 如果看起来像 JSON 对象但缺少花括号，尝试添加
            if ':' in data_str and not (data_str.startswith('{') and data_str.endswith('}')):
                data_str = '{' + data_str + '}'
            
            # 如果看起来像 JSON 数组但缺少方括号，尝试添加
            if ',' in data_str and not (data_str.startswith('[') and data_str.endswith(']')):
                # 检查是否已经是对象
                if '{' not in data_str and '}' not in data_str:
                    data_str = '[' + data_str + ']'
            
            logging.debug(f"处理后的 JSON 字符串: {data_str}")
            data = json.loads(data_str)
            logging.info("请求体解析为 JSON 格式")
        except json.JSONDecodeError as e:
            logging.debug(f"JSON 解析错误: {str(e)}")
            # 如果不是 JSON，尝试按键值对格式处理
            try:
                import urllib.parse
                data = {}
                for pair in args.data.split('&'):
                    key, value = pair.split('=', 1)
                    data[urllib.parse.unquote(key.strip())] = urllib.parse.unquote(value.strip())
                logging.info("请求体解析为键值对格式")
            except ValueError:
                # 如果也不是键值对，按原始文本处理
                data = args.data
                logging.warning("非合法 JSON 或键值对格式，按原始文本发送")
    
    # 记录请求体信息
    if data:
        if isinstance(data, dict):
            # 计算 Content-Length 并记录
            try:
                json_str = json.dumps(data)
                content_length = len(json_str)
                logging.info(f"请求体大小: {content_length} 字节")
            except:
                pass
        elif isinstance(data, str):
            content_length = len(data)
            logging.info(f"请求体大小: {content_length} 字节")
    
    # 发送请求
    client = HTTPClient(session_manager)
    
    try:
        # 记录请求开始时间
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        
        response = client.send_request(
            method=args.method,
            url=args.url,
            headers=headers,
            data=data,
            timeout=args.timeout
        )

        # 打印响应信息
        
        # 在 verbose 模式下打印请求头与请求体摘要
        if args.verbose:
            colorize = ResponseFormatter.colorize if not args.no_color else lambda text, _: text
            if headers:
                print("\n" + colorize("===== 请求头 =====", "cyan"))
                for key, value in headers.items():
                    print(f"{colorize(key + ':', 'yellow')} {value}")
            
            if data:
                print("\n" + colorize("===== 请求体 =====", "cyan"))
                if isinstance(data, dict):
                    print(ResponseFormatter.format_json(data, use_color=not args.no_color))
                else:
                    print(data)

        
        # 打印响应信息
        print("\n" + ResponseFormatter.format_response(response, not args.no_color, args.max_body_length))
        
    except RequestException as e:
        logging.error("请求失败: %s", str(e))

if __name__ == '__main__':
    main()