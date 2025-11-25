# WebCache Explorer 项目文档

## 项目概述

WebCache Explorer 是一个功能强大的 Python 工具，用于抓取、缓存和搜索网页内容。它提供了完整的网页内容管理解决方案，包括并发抓取、智能缓存、文本处理和全文搜索功能。

## 核心功能

### 1. 网页抓取
- **并发抓取**: 支持多线程并发抓取，提高抓取效率
- **智能重试**: 自动重试失败的请求，支持指数退避策略
- **内容验证**: 验证HTTP状态码和内容完整性
- **超时控制**: 可配置的超时时间，适应不同网络环境

### 2. 缓存管理
- **本地存储**: 将抓取的内容存储在本地文件系统
- **索引管理**: 维护URL索引和元数据信息
- **内容去重**: 基于内容哈希值检测重复内容
- **缓存清理**: 支持按时间、大小等条件清理缓存

### 3. 文本处理
- **HTML解析**: 提取纯文本内容，移除HTML标签
- **关键词提取**: 基于TF-IDF算法提取关键词
- **相关性评分**: 计算内容与搜索词的相关性
- **智能摘要**: 生成内容摘要，突出重要信息

### 4. 搜索功能
- **全文搜索**: 支持在缓存内容中进行全文搜索
- **相关性排序**: 按相关性评分对搜索结果排序
- **结果过滤**: 支持限制搜索结果数量
- **多语言支持**: 支持中文、英文等多种语言内容

## 安装指南

### 系统要求
- Python 3.7+
- 支持的操作系统: Windows, macOS, Linux

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/webcache-explorer.git
cd webcache-explorer
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **安装项目**
```bash
pip install -e .
```

## 快速开始

### 基本使用

1. **抓取网页**
```bash
# 抓取单个URL
webcache_explorer fetch --urls https://python.org

# 抓取多个URL
webcache_explorer fetch --urls urls.txt
```

2. **搜索内容**
```bash
# 搜索编程相关内容
webcache_explorer search "programming tutorial"

# 限制搜索结果数量
webcache_explorer search "python" --top-k 5
```

3. **查看统计信息**
```bash
webcache_explorer stats
```

### 配置文件

创建 `config.toml` 文件来自定义配置：

```toml
[fetching]
max_workers = 5
timeout = 30
try_delay = 1.0
max_retries = 3

[storage]
data_dir = "cache_data"
index_file = "cache_index.json"

[processing]
max_content_size = 10485760

[logging]
level = "INFO"
file = "app.log"
```

## API文档

### WebCrawler类

```python
from webcache_explorer import WebCrawler, Config

config = Config()
crawler = WebCrawler(config)

# 抓取单个URL
result = crawler.fetch_url("https://example.com")

# 批量抓取URLs
results = crawler.fetch_urls(["url1", "url2", "url3"])
```

### CacheManager类

```python
from webcache_explorer import CacheManager

cache = CacheManager(config)

# 存储抓取结果
cache.store(result)

# 检索缓存内容
entry = cache.retrieve("https://example.com")

# 搜索URL
cache_entries = cache.search_urls("python")

# 获取统计信息
stats = cache.get_stats()
```

### TextProcessor类

```python
from webcache_explorer import TextProcessor

processor = TextProcessor()

# 提取文本
text = processor.extract_text(html_content)

# 提取关键词
keywords = processor.extract_keywords(text, top_k=10)

# 搜索内容
search_results = processor.search_content(cache_entries, "search term")

# 生成摘要
summary = processor.generate_summary(text, max_sentences=3)
```

## 性能优化

### 并发调优

```toml
[fetching]
max_workers = 10  # 高速网络\max_workers = 3   # 慢速网络
timeout = 60      # 不稳定网络
```

### 内存管理

```toml
[processing]
max_content_size = 20971520  # 20MB限制
```

### 缓存策略

```python
# 定期清理过期缓存
stats = cache.get_stats()
if stats['total_entries'] > 1000:
    cache.clear_old_entries(days=30)
```

## 故障排除

### 常见问题

1. **抓取失败**
   - 检查网络连接
   - 增加超时时间
   - 验证URL有效性

2. **内存不足**
   - 减少并发数
   - 限制内容大小
   - 分批处理URL

3. **搜索无结果**
   - 检查缓存是否为空
   - 验证搜索关键词
   - 检查文本提取是否正常

### 调试模式

启用调试日志：

```toml
[logging]
level = "DEBUG"
file = "debug.log"
```

## 高级功能

### 内容监控

```python
def monitor_websites(urls, interval_hours=6):
    """定期监控网站内容变化"""
    # 实现内容变化检测
    # 发送通知等
```

### 内容聚合

```python
def build_content_aggregator(search_terms):
    """构建内容聚合器"""
    # 从多个源聚合相关内容
    # 生成摘要和报告
```

### 网站地图生成

```python
def generate_sitemap_from_cache():
    """从缓存生成网站地图"""
    # 分析缓存结构
    # 生成可视化地图
```

## 贡献指南

### 开发环境设置

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范

- 遵循PEP 8编码规范
- 编写单元测试
- 更新文档
- 添加类型注解

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_crawler.py

# 性能测试
python bench.py
```

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础抓取功能
- 缓存管理
- 文本处理
- 搜索功能

### v1.1.0 (2024-02-01)
- 性能优化
- 并发抓取改进
- 错误处理增强
- 文档完善

## 许可证

本项目采用MIT许可证。详情请参见LICENSE文件。

## 联系方式

- 项目主页: https://github.com/yourusername/webcache-explorer
- 问题反馈: https://github.com/yourusername/webcache-explorer/issues
- 邮件: your.email@example.com

## 致谢

感谢所有贡献者和开源社区的支持。

---

*本文档最后更新: 2024年1月*