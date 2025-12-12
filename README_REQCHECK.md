# reqcheck - 批量URL检查工具

一个功能强大的批量URL检查工具，支持并发请求、指数退避重试、代理配置、超时管理、结果导出和文件下载功能。

## 功能特性

- ✅ **批量URL检查**：从文件读取URL列表并发访问
- 🔄 **指数退避重试**：自动重试失败的请求，支持自定义重试策略
- 🕒 **超时配置**：可自定义请求超时时间
- 📡 **代理支持**：HTTP/HTTPS代理配置
- 📊 **结果导出**：支持CSV和JSON格式输出
- 📥 **文件下载**：支持批量下载文件，带进度条显示
- 📈 **统计信息**：详细的错误统计和成功率分析
- 🎨 **彩色输出**：支持彩色日志和进度条

## 安装方法

### 直接安装

```bash
pip install -e .
```

### 从源码安装

```bash
git clone https://github.com/your/repo.git
cd repo
pip install -r requirements_reqcheck.txt
python setup_reqcheck.py install
```

## 快速开始

### 基础使用

```bash
# 检查URL列表并输出JSON结果
reqcheck examples/urls.txt -o results.json

# 检查URL列表并输出CSV结果
reqcheck examples/urls.txt -o results.csv -f csv

# 详细模式输出
reqcheck examples/urls.txt -v
```

### 高级使用

```bash
# 自定义请求头
reqcheck examples/urls.txt -H "User-Agent: CustomAgent/1.0" -H "Accept: application/json"

# 高并发检查
reqcheck examples/urls.txt -C 10

# 自定义重试策略
reqcheck examples/urls.txt -r 5 -b 1.0

# 使用代理
reqcheck examples/urls.txt -p "http://proxy:8080"

# 下载模式
reqcheck -d -D ./downloads examples/urls.txt

# 使用配置文件
reqcheck --config examples/config.json
```

## 命令行参数

```
Usage: reqcheck [OPTIONS] [INPUT_FILE]

批量URL检查工具 - reqcheck

Options:
  -o, --output-file TEXT      输出文件路径
  -f, --output-format [csv|json]
                              输出格式
  -m, --method TEXT           HTTP请求方法
  -H, --header TEXT           自定义请求头，格式为 "Key: Value"
  -c, --cookie TEXT           自定义Cookie，格式为 "Key=Value"
  -t, --timeout INTEGER       超时时间（秒）
  -p, --proxy TEXT            代理服务器，格式为 "http://proxy:port"
  -C, --concurrency INTEGER   并发数
  -r, --max-retries INTEGER   最大重试次数
  -b, --backoff-factor FLOAT  退避因子
  -d, --download              下载模式
  -D, --download-dir TEXT     下载目录
  -v, --verbose               详细输出
  -q, --quiet                 静默模式
  --config TEXT               配置文件路径
  --help                      显示帮助信息
```

## 配置文件

可以使用JSON配置文件来保存常用配置：

```json
{
  "input_file": "examples/urls.txt",
  "output_file": "results.json",
  "output_format": "json",
  "method": "GET",
  "timeout": 10,
  "concurrency": 5,
  "max_retries": 3,
  "backoff_factor": 0.5,
  "download": false,
  "download_dir": "./downloads",
  "verbose": false,
  "quiet": false
}
```

## 结果格式

### JSON格式

```json
[
  {
    "url": "https://example.com",
    "final_url": "https://example.com",
    "status_code": 200,
    "error": null,
    "response_time": 0.5,
    "redirected": false,
    "timeout": false,
    "content_length": 1024,
    "headers": {
      "server": "nginx",
      "content_type": "text/html",
      "last_modified": "Wed, 21 Oct 2015 07:28:00 GMT",
      "etag": "\"3147526947\""
    }
  }
]
```

### CSV格式

CSV格式包含以下字段：
- url: 原始URL
- final_url: 最终重定向后的URL
- status_code: HTTP状态码
- error: 错误信息（如果有）
- response_time: 响应时间（秒）
- redirected: 是否重定向
- timeout: 是否超时
- content_length: 内容长度
- server: 服务器信息
- content_type: 内容类型
- last_modified: 最后修改时间
- etag: ETag

## 示例

查看`examples/`目录下的示例文件：

- `urls.txt`: 示例URL列表
- `headers.json`: 示例请求头配置
- `cookies.json`: 示例Cookie配置
- `config.json`: 示例配置文件
- `run_example.sh`: 示例运行脚本

运行所有示例：

```bash
chmod +x examples/run_example.sh
examples/run_example.sh
```

## 单元测试

运行单元测试：

```bash
python -m pytest tests/test_reqcheck.py -v
```

## 项目结构

```
reqcheck/
├── __init__.py              # 包初始化
├── __main__.py              # 模块入口
├── __version__.py           # 版本信息
├── cli.py                   # 命令行界面
├── config.py                # 配置管理
├── logging_utils.py         # 日志工具
├── requestor.py             # HTTP请求处理
├── downloader.py            # 文件下载
├── exporters.py             # 结果导出
├── runner.py                # 任务运行器
```

## 依赖

- requests>=2.31.0
- click>=8.0.0
- tqdm>=4.64.0
- colorama>=0.4.6
- python-dotenv>=1.0.0
- urllib3>=2.0.0

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！