import click
import json
from .config import Config
from .logging_utils import setup_logger
from .runner import Runner
from .exporters import get_exporter

@click.command()
@click.argument('input_file', required=False)
@click.option('-o', '--output-file', help='输出文件路径')
@click.option('-f', '--output-format', default='json', type=click.Choice(['csv', 'json']), help='输出格式')
@click.option('-m', '--method', default='GET', help='HTTP请求方法')
@click.option('-H', '--header', multiple=True, help='自定义请求头，格式为 "Key: Value"')
@click.option('-c', '--cookie', multiple=True, help='自定义Cookie，格式为 "Key=Value"')
@click.option('-t', '--timeout', default=10, help='超时时间（秒）')
@click.option('-p', '--proxy', multiple=True, help='代理服务器，格式为 "http://proxy:port"')
@click.option('-C', '--concurrency', default=5, help='并发数')
@click.option('-r', '--max-retries', default=3, help='最大重试次数')
@click.option('-b', '--backoff-factor', default=0.5, help='退避因子')
@click.option('-d', '--download', is_flag=True, help='下载模式')
@click.option('-D', '--download-dir', default='./downloads', help='下载目录')
@click.option('-v', '--verbose', is_flag=True, help='详细输出')
@click.option('-q', '--quiet', is_flag=True, help='静默模式')
@click.option('--config', help='配置文件路径')
def main(
    input_file, output_file, output_format,
    method, header, cookie, timeout, proxy,
    concurrency, max_retries, backoff_factor,
    download, download_dir, verbose, quiet,
    config
):
    """批量URL检查工具 - reqcheck"""
    
    # 加载配置
    config_obj = Config()
    
    # 从配置文件加载
    if config:
        file_config = Config.from_file(config)
        config_obj.merge(file_config)
    
    # 从命令行参数更新配置
    if input_file:
        config_obj.input_file = input_file
    
    if output_file:
        config_obj.output_file = output_file
    
    config_obj.output_format = output_format
    config_obj.method = method
    config_obj.timeout = timeout
    config_obj.concurrency = concurrency
    config_obj.max_retries = max_retries
    config_obj.backoff_factor = backoff_factor
    config_obj.download = download
    config_obj.download_dir = download_dir
    config_obj.verbose = verbose
    config_obj.quiet = quiet
    
    # 解析请求头
    headers = {}
    for h in header:
        if ':' in h:
            key, value = h.split(':', 1)
            headers[key.strip()] = value.strip()
    config_obj.headers = headers
    
    # 解析Cookie
    cookies = {}
    for c in cookie:
        if '=' in c:
            key, value = c.split('=', 1)
            cookies[key.strip()] = value.strip()
    config_obj.cookies = cookies
    
    # 解析代理
    proxies = {}
    for p in proxy:
        if p.startswith('http://'):
            proxies['http'] = p
        elif p.startswith('https://'):
            proxies['https'] = p
        else:
            proxies['http'] = p
            proxies['https'] = p
    config_obj.proxies = proxies
    
    # 验证配置
    try:
        config_obj.validate()
    except Exception as e:
        click.echo(f"配置错误: {e}", err=True)
        return
    
    # 设置日志
    logger = setup_logger(config_obj)
    
    # 运行任务
    try:
        with Runner(config_obj, logger) as runner:
            results = runner.run()
            
            # 导出结果
            if results:
                exporter = get_exporter(config_obj)
                exporter.export(results)
                
                if not output_file and not quiet:
                    logger.info("\n结果已输出到控制台")
    except Exception as e:
        logger.error(f"程序运行错误: {e}")

if __name__ == '__main__':
    main()