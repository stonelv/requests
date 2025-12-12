import logging
import sys
from typing import Optional
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        level_name = log_color + f"{record.levelname:8}" + Style.RESET_ALL
        message = super().format(record)
        return f"{level_name} | {message}"

def setup_logger(config) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger('reqcheck')
    
    # 清除已存在的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 设置日志级别
    if config.verbose:
        logger.setLevel(logging.DEBUG)
    elif config.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    # 设置格式化器
    if config.verbose:
        formatter = ColoredFormatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = ColoredFormatter('%(message)s')
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_error(logger: logging.Logger, url: str, error: str) -> None:
    """记录错误信息"""
    logger.error(f"{Fore.RED}✗ {url} - 错误: {error}{Style.RESET_ALL}")

def log_success(logger: logging.Logger, url: str, status_code: int) -> None:
    """记录成功信息"""
    if 200 <= status_code < 300:
        logger.info(f"{Fore.GREEN}✓ {url} - 状态码: {status_code}{Style.RESET_ALL}")
    elif 300 <= status_code < 400:
        logger.info(f"{Fore.CYAN}⇨ {url} - 重定向: {status_code}{Style.RESET_ALL}")
    else:
        logger.warning(f"{Fore.YELLOW}! {url} - 异常状态码: {status_code}{Style.RESET_ALL}")

def log_debug(logger: logging.Logger, message: str) -> None:
    """记录调试信息"""
    logger.debug(f"{Fore.BLUE}DEBUG: {message}{Style.RESET_ALL}")