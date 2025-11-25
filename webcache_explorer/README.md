# WebCache Explorer

一个功能强大的Python网络缓存探索和搜索工具，支持批量并发抓取、智能缓存管理和全文搜索。

## 功能特性

- 🚀 **批量并发抓取**: 使用 `requests` + `ThreadPoolExecutor` 实现高效并发抓取
- 💾 **智能缓存管理**: 自动缓存抓取内容，维护索引文件，支持重复抓取
- 🔍 **全文搜索**: 基于关键词的智能搜索，返回匹配度最高的结果
- 📊 **性能统计**: 详细的抓取性能统计和缓存使用情况
- ⚙️ **灵活配置**: 支持配置文件，可自定义并发数、超时、重试等参数
- 🖥️ **命令行界面**: 提供完整的CLI子命令，操作简单直观
- 🧪 **全面测试**: 包含完整的pytest测试套件
- 📈 **性能基准**: 内置性能测试脚本，评估系统性能

## 安装

### 系统要求

- Python 3.7+
- Windows/Linux/macOS

### 快速安装

```bash
# 克隆项目
git clone https://github.com/your-username/webcache_explorer.git
cd webcache_explorer

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 开发安装

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装预提交钩子（可选）
pre-commit install
```

## 快速开始

### 1. 准备URL列表

创建 `urls.txt` 文件，每行一个URL：

```
https://httpbin.org/html
https://httpbin.org/json
https://example.com
https://python.org
```

### 2. 批量抓取

```bash
# 基本抓取
webcache_explorer fetch --urls urls.txt

# 使用自定义配置
webcache_explorer fetch --urls urls.txt --config config.toml

# 强制重新抓取（忽略缓存）
webcache_explorer refetch --urls urls.txt
```

### 3. 添加单个URL

```bash
# 添加单个URL到缓存
webcache_explorer add-url https://example.com
```

### 4. 搜索内容

```bash
# 搜索关键词
webcache_explorer search "python programming"

# 搜索并限制结果数量
webcache_explorer search "web development" --top-k 5
```

### 5. 查看统计信息

```bash
# 查看缓存统计
webcache_explorer stats

# 查看特定URL的详细信息
webcache_explorer show https://example.com
```

### 6. 导出数据

```bash
# 导出缓存索引
webcache_explorer export cache_export.json
```

## 配置说明

### 配置文件 (config.toml)

```toml
[fetching]
max_workers = 4          # 最大并发数
timeout = 30             # 超时时间（秒）
max_retries = 3          # 最大重试次数
retry_delay = 1.0        # 重试延迟（秒）

[storage]
data_dir = "data"        # 数据目录
index_file = "index.json" # 索引文件名

[processing]
max_content_size = 10485760  # 最大内容大小（字节）

[logging]
level = "INFO"           # 日志级别
file = "webcache_explorer.log"  # 日志文件
```

### 环境变量

- `WEBCACHE_CONFIG`: 配置文件路径
- `WEBCACHE_DATA_DIR`: 数据目录路径

## 性能测试

### 运行性能基准测试

```bash
# 运行完整的性能测试
python bench.py

# 运行pytest测试套件
pytest tests/

# 运行特定测试
pytest tests/test_crawler.py

# 生成测试覆盖率报告
pytest --cov=webcache_explorer --cov-report=html
```

### 性能指标

基准测试会测量以下指标：

- 单URL抓取性能
- 并发抓取性能
- 缓存存储和检索性能
- 成功率统计
- 内容大小分析
- 请求吞吐量

## 项目结构

```
webcache_explorer/
├── src/webcache_explorer/    # 主要源代码
│   ├── __init__.py           # 包初始化
│   ├── config.py             # 配置管理
│   ├── crawler.py            # 网络爬虫
│   ├── cache.py              # 缓存管理
│   ├── text_processor.py     # 文本处理和搜索
│   └── cli.py                # 命令行接口
├── tests/                    # 测试套件
│   ├── test_config.py        # 配置测试
│   ├── test_crawler.py       # 爬虫测试
│   ├── test_cache.py         # 缓存测试
│   ├── test_text_processor.py  # 文本处理测试
│   └── test_cli.py           # CLI测试
├── config/                   # 配置文件
│   └── config.toml           # 默认配置
├── data/                     # 数据目录（自动生成）
│   ├── index.json            # 缓存索引
│   └── content/              # 缓存内容
├── requirements.txt          # 生产依赖
├── requirements-dev.txt      # 开发依赖
├── pyproject.toml            # 项目元数据
├── bench.py                  # 性能测试脚本
├── urls.txt                  # 示例URL列表
└── README.md                 # 项目文档
```

## API 使用

### 作为库使用

```python
from webcache_explorer import Config, WebCrawler, CacheManager, TextProcessor

# 创建配置
config = Config()

# 初始化组件
crawler = WebCrawler(config)
cache_manager = CacheManager(config)
text_processor = TextProcessor()

# 抓取URL
result = crawler.fetch_url("https://example.com")

# 存储到缓存
cache_manager.store(result)

# 搜索内容
entries = cache_manager.get_successful_urls()
cache_entries = [cache_manager.retrieve(url) for url in entries]
results = text_processor.search_content(cache_entries, "search term")

# 打印结果
for result in results:
    print(f"URL: {result.url}")
    print(f"Title: {result.title}")
    print(f"Score: {result.relevance_score}")
    print(f"Summary: {result.summary}")
    print("-" * 50)
```

## 高级功能

### 自定义搜索算法

```python
from webcache_explorer.text_processor import TextProcessor

processor = TextProcessor()

# 自定义相关性评分
score = processor.calculate_relevance_score(
    text="Python programming tutorial",
    query="python tutorial"
)

# 提取关键词
keywords = processor.extract_keywords(
    text="Python is a programming language for web development",
    top_k=5
)

# 生成摘要
summary = processor.generate_summary(
    text="Long article content...",
    max_sentences=3
)
```

### 批量处理

```python
from webcache_explorer import WebCrawler

crawler = WebCrawler()

# 批量抓取URLs
urls = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

results = crawler.fetch_urls(urls)

# 处理结果
for result in results:
    if result['success']:
        print(f"✓ {result['url']}: {result['status_code']}")
    else:
        print(f"✗ {result['url']}: {result.get('error_message')}")
```

## 故障排除

### 常见问题

1. **连接超时**
   - 检查网络连接
   - 增加配置文件中的 `timeout` 值
   - 检查目标网站是否可访问

2. **内存不足**
   - 减少 `max_workers` 并发数
   - 减小 `max_content_size` 限制
   - 分批处理大量URL

3. **权限错误**
   - 确保有写入数据目录的权限
   - 检查配置文件权限

4. **SSL证书错误**
   - 某些网站可能需要特殊SSL配置
   - 考虑使用代理或VPN

### 调试模式

```bash
# 启用调试日志
export WEBCACHE_LOG_LEVEL=DEBUG
webcache_explorer fetch --urls urls.txt

# 或使用配置文件
# 在 config.toml 中设置 logging.level = "DEBUG"
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写单元测试
- 更新文档
- 确保所有测试通过

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0 (2024-01)
- ✨ 初始版本发布
- 🚀 批量并发抓取功能
- 💾 智能缓存管理
- 🔍 全文搜索功能
- 📊 性能统计和基准测试
- 🖥️ 完整的CLI界面
- 🧪 全面的测试套件

## 联系方式

- 项目主页: https://github.com/your-username/webcache_explorer
- 问题反馈: https://github.com/your-username/webcache_explorer/issues
- 邮箱: your.email@example.com

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！