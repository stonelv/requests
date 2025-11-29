#!/usr/bin/env python3
"""
rcli - 基于 requests 的命令行 HTTP 客户端工具

一个功能完整的命令行 HTTP 客户端，支持多种 HTTP 方法、会话持久化、
彩色输出和详细的错误处理。

功能特性:
- 支持 GET, POST, PUT, DELETE 等 HTTP 方法
- 自动会话持久化（Cookie 管理）
- 彩色输出和 JSON 格式化显示
- 详细的错误处理和日志记录
- 完整的类型注解和文档字符串

作者: Python 工程师
版本: 1.0.0
"""

import argparse
import json
import logging
import os
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
from requests.exceptions import InvalidURL


class ANSIColors:
    """ANSI 颜色代码类，用于终端彩色输出"""
    
    # 文本颜色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 背景颜色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    
    # 样式
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    REVERSE = '\033[7m'
    
    # 重置
    RESET = '\033[0m'
    
    # 颜色开关
    _no_color = False
    
    @classmethod
    def disable_color(cls):
        """禁用颜色输出"""
        cls._no_color = True
    
    @classmethod
    def enable_color(cls):
        """启用颜色输出"""
        cls._no_color = False
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """
        给文本添加颜色
        
        Args:
            text: 要着色的文本
            color: 颜色代码
            
        Returns:
            着色后的文本（如果颜色被禁用则返回原文本）
        """
        if cls._no_color:
            return text
        return f"{color}{text}{cls.RESET}"


class SessionManager:
    """会话管理器，负责 Cookie 的持久化存储和加载"""
    
    def __init__(self, session_file: str = ".rcli_session"):
        """
        初始化会话管理器
        
        Args:
            session_file: 会话文件路径
        """
        self.session_file = Path(session_file)
        self.session: Optional[requests.Session] = None
        
    def create_session(self) -> requests.Session:
        """
        创建新的会话，如果存在持久化会话则加载

        Returns:
            requests.Session 对象
        """
        session = requests.Session()
        
        # 尝试加载已保存的 cookies
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    cookies_dict = json.load(f)
                    session.cookies.update(cookies_dict)
                logging.info(f"已加载会话文件: {self.session_file}")
            except Exception as e:
                logging.warning(f"加载会话文件失败: {e}")
                
        self.session = session
        return session
    
    def save_session(self) -> None:
        """
        保存当前会话的 cookies 到文件
        """
        if self.session is None:
            return
            
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                cookies_dict = self.session.cookies.get_dict()
                json.dump(cookies_dict, f, ensure_ascii=False, indent=2)
            logging.info(f"会话已保存到: {self.session_file}")
        except Exception as e:
            logging.error(f"保存会话失败: {e}")
    
    def clear_session(self) -> None:
        """
        清除会话文件和当前会话
        """
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                logging.info(f"会话文件已删除: {self.session_file}")
            except Exception as e:
                logging.error(f"删除会话文件失败: {e}")
        
        if self.session:
            self.session.cookies.clear()


class JSONFormatter:
    """JSON 格式化器，提供带高亮的 JSON 输出"""
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """
        格式化 JSON 数据并添加语法高亮
        
        Args:
            data: 要格式化的数据
            indent: 缩进级别
            
        Returns:
            格式化并高亮后的 JSON 字符串
        """
        try:
            json_str = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
            return JSONFormatter._highlight_json(json_str)
        except Exception as e:
            logging.error(f"JSON 格式化失败: {e}")
            return str(data)
    
    @staticmethod
    def _highlight_json(json_str: str) -> str:
        """
        为 JSON 字符串添加语法高亮
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            高亮后的 JSON 字符串
        """
        lines = json_str.split('\n')
        highlighted_lines = []
        import re
        
        for line in lines:
            highlighted_line = line
            
            # 高亮 JSON 键（双引号后跟冒号）
            highlighted_line = re.sub(
                r'("[^"]*"):\s*',
                lambda m: ANSIColors.colorize(m.group(1), ANSIColors.CYAN) + ": ",
                highlighted_line
            )
            
            # 高亮 JSON 字符串值
            highlighted_line = re.sub(
                r':\s*("[^"]*")',
                lambda m: ": " + ANSIColors.colorize(m.group(1), ANSIColors.GREEN),
                highlighted_line
            )
            
            # 高亮数字
            highlighted_line = re.sub(
                r'\b(\d+(?:\.\d+)?)\b',
                lambda m: ANSIColors.colorize(m.group(1), ANSIColors.YELLOW),
                highlighted_line
            )
            
            # 高亮布尔值和 null
            highlighted_line = re.sub(
                r'\b(true|false|null)\b',
                lambda m: ANSIColors.colorize(m.group(1), ANSIColors.MAGENTA),
                highlighted_line
            )
            
            highlighted_lines.append(highlighted_line)
        
        return '\n'.join(highlighted_lines)


class HTTPClient:
    """HTTP 客户端类，封装 HTTP 请求逻辑"""
    
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
    
    def __init__(self, session_manager: SessionManager, timeout: int = 30):
        """
        初始化 HTTP 客户端
        
        Args:
            session_manager: 会话管理器
            timeout: 请求超时时间（秒）
        """
        self.session_manager = session_manager
        self.timeout = timeout
        self.session = session_manager.create_session()
        
    def make_request(self, method: str, url: str, data: Optional[str] = None, 
                    headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            data: 请求数据（JSON 字符串）
            headers: 自定义请求头
            
        Returns:
            响应对象
            
        Raises:
            ValueError: 不支持的 HTTP 方法
            RequestException: 请求异常
        """
        method = method.upper()
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(f"不支持的 HTTP 方法: {method}. "
                           f"支持的方法: {', '.join(self.SUPPORTED_METHODS)}")
        
        # 解析请求数据
        request_data = None
        if data:
            try:
                # 先尝试解析为 JSON
                request_data = json.loads(data)
            except json.JSONDecodeError:
                # 解析失败则作为纯文本处理
                request_data = data
        
        # 设置默认请求头
        default_headers = {
            'User-Agent': 'rcli/1.0.0 (Python HTTP Client)'
        }
        if headers:
            default_headers.update(headers)
        
        # 添加 Content-Type（如果需要）
        if method in ['POST', 'PUT'] and request_data:
            if isinstance(request_data, (dict, list)):
                default_headers['Content-Type'] = 'application/json'
        
        try:
            logging.info(f"发送 {method} 请求到: {url}")
            
            if method == 'GET':
                response = self.session.get(url, headers=default_headers, timeout=self.timeout)
            elif method == 'POST':
                response = self.session.post(url, json=request_data if isinstance(request_data, (dict, list)) else request_data, 
                                           headers=default_headers, timeout=self.timeout)
            elif method == 'PUT':
                response = self.session.put(url, json=request_data if isinstance(request_data, (dict, list)) else request_data, 
                                          headers=default_headers, timeout=self.timeout)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=default_headers, timeout=self.timeout)
            
            # 保存会话（更新 cookies）
            self.session_manager.save_session()
            
            return response
            
        except Timeout as e:
            raise RequestException(f"请求超时: {e}")
        except ConnectionError as e:
            raise RequestException(f"连接错误: {e}")
        except HTTPError as e:
            raise RequestException(f"HTTP 错误: {e}")
        except InvalidURL as e:
            raise RequestException(f"无效的 URL: {e}")
        except RequestException as e:
            raise RequestException(f"请求异常: {e}")
        except Exception as e:
            raise RequestException(f"未知错误: {e}")


class ResponseFormatter:
    """响应格式化器，负责美化和显示 HTTP 响应"""
    
    def __init__(self, max_body_length: int = 1000):
        """初始化响应格式化器
        
        Args:
            max_body_length: 响应体最大显示长度（字符数）
        """
        self.json_formatter = JSONFormatter()
        self.max_body_length = max_body_length
    
    def format_request_info(self, method: str, url: str, headers: Dict[str, str], 
                           data: Optional[Any] = None) -> str:
        """
        格式化请求信息
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            headers: 请求头
            data: 请求数据
            
        Returns:
            格式化的请求信息字符串
        """
        lines = []
        lines.append(ANSIColors.colorize("=" * 60, ANSIColors.BLUE))
        lines.append(ANSIColors.colorize("📤 REQUEST INFO", ANSIColors.BOLD + ANSIColors.CYAN))
        lines.append(ANSIColors.colorize("=" * 60, ANSIColors.BLUE))
        
        # 基本信息
        lines.append(f"{ANSIColors.colorize('Method:', ANSIColors.YELLOW)} {method}")
        lines.append(f"{ANSIColors.colorize('URL:', ANSIColors.YELLOW)} {url}")
        lines.append(f"{ANSIColors.colorize('Timestamp:', ANSIColors.YELLOW)} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 请求头
        if headers:
            lines.append(f"\n{ANSIColors.colorize('Headers:', ANSIColors.YELLOW)}")
            for key, value in headers.items():
                lines.append(f"  {ANSIColors.colorize(key, ANSIColors.GREEN)}: {value}")
        
        # 请求数据
        if data:
            lines.append(f"\n{ANSIColors.colorize('Request Data:', ANSIColors.YELLOW)}")
            if isinstance(data, (dict, list)):
                formatted_data = self.json_formatter.format_json(data)
                lines.extend([f"  {line}" for line in formatted_data.split('\n')])
            else:
                lines.append(f"  {data}")
        
        return '\n'.join(lines)
    
    def format_response_info(self, response: requests.Response, elapsed_time: float) -> str:
        """
        格式化响应信息
        
        Args:
            response: HTTP 响应对象
            elapsed_time: 请求耗时（秒）
            
        Returns:
            格式化的响应信息字符串
        """
        lines = []
        lines.append(ANSIColors.colorize("\n" + "=" * 60, ANSIColors.BLUE))
        lines.append(ANSIColors.colorize("📥 RESPONSE INFO", ANSIColors.BOLD + ANSIColors.CYAN))
        lines.append(ANSIColors.colorize("=" * 60, ANSIColors.BLUE))
        
        # 状态信息
        status_color = ANSIColors.GREEN if response.status_code < 400 else ANSIColors.RED
        lines.append(f"{ANSIColors.colorize('Status Code:', ANSIColors.YELLOW)} "
                    f"{ANSIColors.colorize(str(response.status_code), status_color)}")
        lines.append(f"{ANSIColors.colorize('Status Text:', ANSIColors.YELLOW)} {response.reason}")
        lines.append(f"{ANSIColors.colorize('Time Elapsed:', ANSIColors.YELLOW)} {elapsed_time:.3f}s")
        lines.append(f"{ANSIColors.colorize('Encoding:', ANSIColors.YELLOW)} {response.encoding or 'None'}")
        
        # 错误摘要（非 2xx/3xx 响应）
        if response.status_code >= 400:
            lines.append(f"\n{ANSIColors.colorize('⚠️  错误摘要:', ANSIColors.RED)}")
            lines.append(f"  {ANSIColors.colorize('状态码:', ANSIColors.YELLOW)} {response.status_code}")
            lines.append(f"  {ANSIColors.colorize('原因:', ANSIColors.YELLOW)} {response.reason}")
            
            # 根据状态码提供建议
            if response.status_code == 404:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 检查 URL 是否正确")
            elif response.status_code == 401:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 检查认证信息")
            elif response.status_code == 403:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 检查访问权限")
            elif response.status_code == 500:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 服务器内部错误，稍后重试")
            elif response.status_code >= 500:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 服务器错误，请稍后重试")
            elif response.status_code >= 400:
                lines.append(f"  {ANSIColors.colorize('建议:', ANSIColors.CYAN)} 检查请求参数和数据格式")
        
        # 响应头
        lines.append(f"\n{ANSIColors.colorize('Headers:', ANSIColors.YELLOW)}")
        for key, value in response.headers.items():
            lines.append(f"  {ANSIColors.colorize(key, ANSIColors.GREEN)}: {value}")
        
        # 响应内容
        if response.content:
            lines.append(f"\n{ANSIColors.colorize('Response Body:', ANSIColors.YELLOW)}")
            
            # 尝试解析 JSON
            try:
                json_data = response.json()
                formatted_json = self.json_formatter.format_json(json_data)
                lines.append(formatted_json)
            except ValueError:
                # 非 JSON 内容
                content = response.text
                if len(content) > self.max_body_length:
                    content = content[:self.max_body_length] + f"...\n[内容已截断，显示前 {self.max_body_length} 个字符]"
                lines.append(content)
        
        return '\n'.join(lines)


class RCLI:
    """主应用程序类"""
    
    def __init__(self):
        """初始化 RCLI 应用程序"""
        self.setup_logging()
        self.session_manager = SessionManager()
        self.http_client = HTTPClient(self.session_manager)
        self.response_formatter = None  # 将在 run 方法中初始化
    
    def setup_logging(self) -> None:
        """
        设置日志配置
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def parse_arguments(self) -> argparse.Namespace:
        """
        解析命令行参数
        
        Returns:
            解析后的参数命名空间
        """
        parser = argparse.ArgumentParser(
            description='rcli - 基于 requests 的命令行 HTTP 客户端工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  rcli -m GET -u https://api.github.com/users/octocat
  rcli -m POST -u https://httpbin.org/post -d '{"name": "test"}'
  rcli -m PUT -u https://httpbin.org/put -d '{"updated": true}'
  rcli -m DELETE -u https://httpbin.org/delete
  rcli --clear-session
            """
        )
        
        # HTTP 方法
        parser.add_argument(
            '-m', '--method',
            choices=['GET', 'POST', 'PUT', 'DELETE'],
            default='GET',
            help='HTTP 方法 (默认: GET)'
        )
        
        # URL
        parser.add_argument(
            '-u', '--url',
            help='目标 URL'
        )
        
        # 请求数据
        parser.add_argument(
            '-d', '--data',
            help='请求数据 (JSON 字符串或纯文本)'
        )
        
        # 自定义请求头
        parser.add_argument(
            '-H', '--header',
            action='append',
            help='自定义请求头 (格式: "Key: Value")'
        )
        
        # 超时时间
        parser.add_argument(
            '-t', '--timeout',
            type=int,
            default=30,
            help='请求超时时间（秒）(默认: 30)'
        )
        
        # 清除会话
        parser.add_argument(
            '--clear-session',
            action='store_true',
            help='清除会话文件和 Cookies'
        )
        
        # 详细输出
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='显示详细输出'
        )
        
        # 禁用颜色输出
        parser.add_argument(
            '--no-color',
            action='store_true',
            help='禁用彩色输出'
        )
        
        # 响应体最大长度
        parser.add_argument(
            '--max-body-length',
            type=int,
            default=1000,
            help='响应体最大显示长度（字符数）(默认: 1000)'
        )
        
        return parser.parse_args()
    
    def parse_headers(self, header_list: Optional[List[str]]) -> Dict[str, str]:
        """
        解析请求头列表
        
        Args:
            header_list: 请求头字符串列表
            
        Returns:
            请求头字典
        """
        headers = {}
        if not header_list:
            return headers
        
        for header in header_list:
            if ':' not in header:
                logging.warning(f"无效的请求头格式: {header}")
                continue
            
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
        
        return headers
    
    def run(self) -> int:
        """
        运行应用程序
        
        Returns:
            退出码 (0: 成功, 1: 失败)
        """
        try:
            args = self.parse_arguments()
            
            # 处理颜色开关
            if args.no_color:
                ANSIColors.disable_color()
            
            # 初始化响应格式化器
            self.response_formatter = ResponseFormatter(max_body_length=args.max_body_length)

            # 设置控制台编码为 UTF-8（Windows 兼容性）
            if sys.platform == 'win32':
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            
            # 处理清除会话请求
            if args.clear_session:
                self.session_manager.clear_session()
                print(ANSIColors.colorize("✅ 会话已清除", ANSIColors.GREEN))
                return 0
            
            # 验证必需参数
            if not args.url:
                print(ANSIColors.colorize("❌ 错误: 必须提供 URL (-u 参数)", ANSIColors.RED))
                return 1
            
            # 解析请求头
            headers = self.parse_headers(args.header)
            
            # 设置超时时间
            self.http_client.timeout = args.timeout
            
            # 显示请求信息（详细模式）
            if args.verbose:
                request_info = self.response_formatter.format_request_info(
                    args.method, args.url, headers, args.data
                )
                print(request_info)
            
            # 发送请求
            start_time = time.time()
            response = self.http_client.make_request(
                method=args.method,
                url=args.url,
                data=args.data,
                headers=headers
            )
            elapsed_time = time.time() - start_time
            
            # 显示响应信息
            response_info = self.response_formatter.format_response_info(response, elapsed_time)
            print(response_info)
            
            # 显示总结信息
            status_color = ANSIColors.GREEN if response.status_code < 400 else ANSIColors.RED
            summary = f"\n{ANSIColors.colorize('✅ 请求完成', ANSIColors.GREEN)} - "
            summary += f"状态码: {ANSIColors.colorize(str(response.status_code), status_color)} - "
            summary += f"耗时: {elapsed_time:.3f}s"
            print(summary)
            
            return 0 if response.status_code < 400 else 1
            
        except KeyboardInterrupt:
            print(f"\n{ANSIColors.colorize('⚠️  用户中断操作', ANSIColors.YELLOW)}")
            return 1
        except ValueError as e:
            print(f"{ANSIColors.colorize('❌ 参数错误:', ANSIColors.RED)} {e}")
            return 1
        except RequestException as e:
            print(f"{ANSIColors.colorize('❌ 请求失败:', ANSIColors.RED)} {e}")
            return 1
        except Exception as e:
            print(f"{ANSIColors.colorize('❌ 未知错误:', ANSIColors.RED)} {e}")
            logging.exception("发生未预期的错误")
            return 1


def main():
    """主函数"""
    rcli = RCLI()
    sys.exit(rcli.run())


if __name__ == '__main__':
    main()