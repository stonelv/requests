import logging
import sys
from typing import Optional

class Logger:
    def __init__(self, name: str = 'reqcheck', verbose: bool = False, debug: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # 清除已存在的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        
        # 设置格式
        if debug:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif verbose:
            formatter = logging.Formatter('%(levelname)s: %(message)s')
        else:
            formatter = logging.Formatter('%(message)s')
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 设置处理器级别
        if debug:
            console_handler.setLevel(logging.DEBUG)
        elif verbose:
            console_handler.setLevel(logging.INFO)
        else:
            console_handler.setLevel(logging.WARNING)
        
        self.debug_mode = debug
        self.verbose_mode = verbose

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    def progress(self, message: str):
        if self.verbose_mode or self.debug_mode:
            self.logger.info(message)

    def stats(self, message: str):
        self.logger.info(message)

    def debug_enabled(self) -> bool:
        return self.debug_mode

    def verbose_enabled(self) -> bool:
        return self.verbose_mode

    def __repr__(self) -> str:
        return f'Logger(name={self.logger.name}, debug={self.debug_mode}, verbose={self.verbose_mode})'

# 全局日志实例
logger = Logger()

def init_logger(config) -> Logger:
    global logger
    logger = Logger(verbose=config.verbose, debug=config.debug)
    return logger

def get_logger() -> Logger:
    return logger
