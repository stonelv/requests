#!/usr/bin/env python3
"""命令行 HTTP 客户端工具，基于 requests 库实现。

功能特点：
- 支持 GET、POST、PUT、DELETE 等 HTTP 方法
- 会话持久化，自动保存和读取 Cookies
- 精美的格式化输出，包括 JSON 高亮显示
- 详细的异常处理和错误提示
"""

import argparse
import json
import os
import logging
from typing import Dict, Optional, Any, Union
import requests
from requests.exceptions import (
    RequestException, ConnectionError, Timeout,
    HTTPError, InvalidURL, JSONDecodeError
)


class SessionManager:
    """管理会话持久化的类，负责保存和读取 Cookies。"""

    def __init__(self, session_file: str = ".rcli_session"):
        """初始化 SessionManager。

        Args:
            session_file: 保存会话 Cookies 的文件路径。
        """
        self.session_file = session_file
        self.session = requests.Session()
        self._load_session()

    def _load_session(self) -> None:
        """从文件加载会话 Cookies。"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    cookies = json.load(f)
                    self.session.cookies.update(cookies)
                logging.info("会话已从 %s 加载", self.session_file)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning("加载会话失败: %s", e)

    def save_session(self) -> None:
        """将会话 Cookies 保存到文件。"""
        try:
            with open(self.session_file, "w") as f:
                json.dump(self.session.cookies.get_dict(), f)
            logging.info("会话已保存到 %s", self.session_file)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning("保存会话失败: %s", e)

    def clear_session(self) -> None:
        """清除会话 Cookies 和会话文件。"""
        self.session.cookies.clear()
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
                logging.info("会话已清除")
            except OSError as e:
                logging.warning("清除会话文件失败: %s", e)


class ResponseFormatter:
    """格式化 HTTP 响应的类，支持彩色输出和 JSON 格式化。"""

    # ANSI 颜色码
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
    }

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """给文本添加颜色。

        Args:
            text: 要添加颜色的文本。
            color: 颜色名称，必须是 COLORS 中的键。

        Returns:
            添加了颜色的文本字符串。
        """
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

    @classmethod
    def format_json(cls, data: Any, indent: int = 2) -> str:
        """格式化 JSON 数据，支持彩色输出。

        Args:
            data: 要格式化的 JSON 数据。
            indent: 缩进级别。

        Returns:
            格式化后的彩色 JSON 字符串。
        """
        def _colorize_json(obj: Any) -> str:
            """递归给 JSON 元素添加颜色。"""
            if isinstance(obj, bool):
                return cls.colorize(str(obj), 'yellow')
            elif isinstance(obj, (int, float)):
                return cls.colorize(str(obj), 'blue')
            elif isinstance(obj, str):
                return cls.colorize(f'"{obj}"', 'green')
            elif isinstance(obj, list):
                items = [_colorize_json(item) for item in obj]
                return f'[ {" , ".join(items)} ]'
            elif isinstance(obj, dict):
                items = []
                for key, value in obj.items():
                    key_str = cls.colorize(f'"{key}"', 'magenta')
                    value_str = _colorize_json(value)
                    items.append(f'{key_str}: {value_str}')
                return f'{{ {" , ".join(items)} }}'
            else:
                return str(obj)

        try:
            return _colorize_json(data)
        except Exception:
            return json.dumps(data, indent=indent)

    @classmethod
    def format_response(cls, response: requests.Response) -> str:
        """格式化 HTTP 响应为可读字符串。

        Args:
            response: requests.Response 对象。

        Returns:
            格式化后的响应字符串。
        """
        # 构建响应信息
        response_info = [
            f"{cls.colorize('状态码:', 'cyan')} {response.status_code}",
            f"{cls.colorize('响应时间:', 'cyan')} {response.elapsed.total_seconds():.3f}s",
            f"{cls.colorize('响应头:', 'cyan')}"
        ]

        # 添加响应头
        for key, value in response.headers.items():
            response_info.append(f"  {cls.colorize(key, 'yellow')}: {value}")

        # 添加响应体
        response_info.append(f"{cls.colorize('响应体:', 'cyan')}")

        try:
            # 尝试解析为 JSON
            json_data = response.json()
            response_info.append(cls.format_json(json_data))
        except JSONDecodeError:
            # 如果不是 JSON，直接显示文本
            response_info.append(response.text[:1000])  # 限制显示长度

        return '\n'.join(response_info)


class HTTPClient:
    """HTTP 客户端类，负责处理 HTTP 请求和响应。"""

    def __init__(self, session_manager: SessionManager):
        """初始化 HTTPClient。

        Args:
            session_manager: SessionManager 对象，用于管理会话。
        """
        self.session_manager = session_manager
        self.session = session_manager.session

    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, Dict[str, Any]]] = None,
        timeout: int = 10
    ) -> requests.Response:
        """发送 HTTP 请求。

        Args:
            method: HTTP 方法，如 'GET'、'POST' 等。
            url: 请求的 URL。
            headers: 请求头字典。
            data: 请求体数据。
            timeout: 请求超时时间，单位秒。

        Returns:
            requests.Response 对象。

        Raises:
            RequestException: 如果请求失败。
        """
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data,
                timeout=timeout
            )
            response.raise_for_status()  # 抛出 HTTP 错误
            return response
        except (ConnectionError, Timeout, InvalidURL, HTTPError) as e:
            raise RequestException(f"请求失败: {e}")

    def close(self) -> None:
        """关闭会话。"""
        self.session.close()


def main() -> None:
    """主函数，处理命令行参数并执行请求。"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="命令行 HTTP 客户端工具，基于 requests 库实现。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 基本参数
    parser.add_argument(
        "-m", "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP 请求方法"
    )
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="请求的 URL"
    )
    parser.add_argument(
        "-d", "--data",
        help="请求体数据，可以是 JSON 字符串或键值对格式"
    )
    parser.add_argument(
        "-H", "--header",
        action="append",
        help="请求头，格式为 Key:Value，可以多次使用"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="请求超时时间（秒）"
    )
    parser.add_argument(
        "--clear-session",
        action="store_true",
        help="清除会话 Cookies"
    )

    # 解析参数，处理 Windows 命令提示符中的引号问题
    import sys
    if sys.platform == 'win32':
        # 处理 Windows 命令提示符中的引号问题
        sys.argv = [arg.replace('\\"', '"') for arg in sys.argv]
    
    # 检查是否需要清除会话
    if '--clear-session' in sys.argv:
        session_manager = SessionManager()
        session_manager.clear_session()
        return
    
    args = parser.parse_args()

    # 处理会话
    session_manager = SessionManager()

    if args.clear_session:
        session_manager.clear_session()
        return

    # 处理请求头
    headers: Dict[str, str] = {}
    if args.header:
        for header in args.header:
            try:
                key, value = header.split(":", 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                logging.warning("无效的请求头格式: %s，请使用 Key:Value 格式", header)

    # 处理请求体
    data: Optional[Union[str, Dict[str, Any]]] = None
    if args.data:
        try:
            # 尝试解析为 JSON，处理 Windows 命令提示符中的引号问题
            data_str = args.data.replace("'", '"')
            # 处理 Windows 命令提示符自动删除双引号的问题
            if not data_str.startswith('{'):
                data_str = "{" + data_str + "}"
            data = json.loads(data_str)
        except json.JSONDecodeError:
            # 如果不是 JSON，按键值对处理
            data = {}
            for pair in args.data.split("&"):
                try:
                    key, value = pair.split("=", 1)
                    data[key.strip()] = value.strip()
                except ValueError:
                    pass

    # 发送请求
    client = HTTPClient(session_manager)

    try:
        response = client.send_request(
            method=args.method,
            url=args.url,
            headers=headers,
            data=data,
            timeout=args.timeout
        )

        # 打印请求信息
        print(ResponseFormatter.colorize("\n===== 请求信息 =====", "cyan"))
        print(f"{ResponseFormatter.colorize('方法:', 'yellow')} {args.method.upper()}")
        print(f"{ResponseFormatter.colorize('URL:', 'yellow')} {args.url}")
        print(f"{ResponseFormatter.colorize('请求头:', 'yellow')}")
        for key, value in headers.items():
            print(f"  {key}: {value}")

        # 打印响应信息
        print(ResponseFormatter.colorize("\n===== 响应信息 =====", "cyan"))
        print(ResponseFormatter.format_response(response))

        # 保存会话
        session_manager.save_session()

    except RequestException as e:
        logging.error("请求失败: %s", e)
    finally:
        client.close()


if __name__ == "__main__":
    main()