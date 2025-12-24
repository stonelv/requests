#!/usr/bin/env python3
import sys
import os
from typing import Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from logging_utils import init_logger
from runner import Runner
from exporters import Exporter

def main():
    try:
        # 解析命令行参数
        config = Config.from_args()
        
        # 验证配置
        if not config.validate():
            sys.exit(1)
        
        # 初始化日志
        logger = init_logger(config)
        
        # 运行检查
        with Runner(config, logger) as runner:
            results = runner.run()
        
        # 导出结果
        if results:
            exporter = Exporter(config)
            output_file = exporter.export(results)
            if output_file:
                logger.info(f'结果已保存到: {output_file}')
            
            # 打印统计信息
            exporter.print_summary(results)
        
        logger.info('任务完成')
        
    except KeyboardInterrupt:
        print('\n用户中断')
        sys.exit(1)
    except Exception as e:
        print(f'发生错误: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
