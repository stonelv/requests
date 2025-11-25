# WebCache Explorer - 快速入门指南

## 安装

### 方法一：从PyPI安装（推荐）
```bash
pip install webcache-explorer
```

### 方法二：从源码安装
```bash
git clone https://github.com/yourusername/webcache-explorer.git
cd webcache-explorer
pip install -e .
```

## 基本用法

### 1. 抓取网页

```bash
# 抓取单个网页
webcache_explorer fetch --urls https://python.org

# 从文件批量抓取
echo "https://python.org
https://javascript.info
https://example.com" > urls.txt
webcache_explorer fetch --urls urls.txt
```

### 2. 搜索内容

```bash
# 搜索编程相关内容
webcache_explorer search "programming tutorial"

# 限制搜索结果数量
webcache_explorer search "python" --top-k 3
```

### 3. 查看统计

```bash
webcache_explorer stats
```

### 4. 查看缓存内容

```bash
webcache_explorer show https://python.org
```

### 5. 导出数据

```bash
# 导出所有缓存数据
webcache_explorer export backup.json
```

## 配置文件

创建 `config.toml`：

```toml
[fetching]
max_workers = 5
timeout = 30

[storage]
data_dir = "my_cache"
```

使用配置：
```bash
webcache_explorer fetch --urls urls.txt --config config.toml
```

## Python API

```python
from webcache_explorer import WebCrawler, CacheManager, TextProcessor, Config

# 初始化
config = Config()
crawler = WebCrawler(config)
cache = CacheManager(config)
processor = TextProcessor()

# 抓取网页
result = crawler.fetch_url("https://python.org")
if result['success']:
    cache.store(result)

# 搜索内容
entries = [cache.retrieve(url) for url in cache.get_successful_urls()]
results = processor.search_content(entries, "python tutorial")

# 显示结果
for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"摘要: {result.summary}")
```

## 故障排除

### 抓取失败
- 检查网络连接
- 增加超时时间
- 验证URL是否正确

### 搜索无结果
- 确认已抓取内容
- 检查搜索关键词
- 查看缓存统计信息

### 性能问题
- 减少并发数（慢速网络）
- 分批处理大量URL
- 定期清理过期缓存

## 获取帮助

```bash
webcache_explorer --help
webcache_explorer fetch --help
webcache_explorer search --help
```

更多信息请查看完整文档。