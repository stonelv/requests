# WebCache Explorer - 使用示例

本文档提供了 WebCache Explorer 工具的详细使用示例和最佳实践。

## 基础使用示例

### 1. 批量抓取网页

```bash
# 创建URL列表文件
echo "https://python.org
https://javascript.info
https://httpbin.org/html
https://example.com" > urls.txt

# 执行批量抓取
webcache_explorer fetch --urls urls.txt

# 查看抓取结果
webcache_explorer stats
```

### 2. 搜索缓存内容

```bash
# 搜索编程相关内容
webcache_explorer search "programming language"

# 搜索Python相关内容，限制结果数量
webcache_explorer search "python tutorial" --top-k 3

# 搜索并导出结果到文件
webcache_explorer search "web development" > search_results.txt
```

### 3. 管理缓存数据

```bash
# 查看特定URL的缓存内容
webcache_explorer show https://python.org

# 导出所有缓存数据
webcache_explorer export cache_backup.json

# 强制重新抓取已缓存的URL
webcache_explorer refetch --urls urls.txt
```

## 高级配置示例

### 自定义配置文件

创建 `custom_config.toml`：

```toml
[fetching]
max_workers = 8          # 增加并发数以提高速度
timeout = 45             # 增加超时时间
try_delay = 2.0          # 增加重试延迟
max_retries = 5          # 增加重试次数

[storage]
data_dir = "my_data"     # 自定义数据目录
index_file = "my_index.json"

[processing]
max_content_size = 20971520  # 增加到20MB

[logging]
level = "DEBUG"          # 启用调试日志
file = "debug.log"
```

使用自定义配置：

```bash
webcache_explorer fetch --urls urls.txt --config custom_config.toml
```

### 处理大量URL

对于包含数千个URL的大型列表：

```bash
# 分批处理，每次处理100个URL
split -l 100 large_urls.txt urls_batch_

# 逐批处理
for batch in urls_batch_*; do
    echo "Processing batch: $batch"
    webcache_explorer fetch --urls "$batch"
    sleep 5  # 批次间延迟
done
```

## 编程接口示例

### 基本API使用

```python
from webcache_explorer import Config, WebCrawler, CacheManager, TextProcessor

# 初始化组件
config = Config()
crawler = WebCrawler(config)
cache = CacheManager(config)
processor = TextProcessor()

# 抓取单个URL
result = crawler.fetch_url("https://python.org")
if result['success']:
    print(f"成功抓取: {result['url']}")
    print(f"状态码: {result['status_code']}")
    print(f"内容大小: {len(result.get('content', ''))} 字节")
    
    # 存储到缓存
cache.store(result)
```

### 批量处理和搜索

```python
# 批量抓取URLs
urls = [
    "https://python.org",
    "https://javascript.info", 
    "https://httpbin.org/html",
    "https://example.com"
]

results = crawler.fetch_urls(urls)

# 存储所有结果到缓存
for result in results:
    if result['success']:
        cache.store(result)

# 获取所有成功的URL
successful_urls = cache.get_successful_urls()

# 准备搜索数据
cache_entries = []
for url in successful_urls:
    entry = cache.retrieve(url)
    if entry:
        cache_entries.append(entry)

# 执行搜索
search_results = processor.search_content(
    cache_entries, 
    "programming tutorial",
    top_k=5
)

# 显示搜索结果
for result in search_results:
    print(f"\nURL: {result.url}")
    print(f"标题: {result.title}")
    print(f"相关度: {result.relevance_score:.2f}")
    print(f"摘要: {result.summary}")
```

### 文本处理功能

```python
# HTML文本提取
html_content = "<html><body><h1>标题</h1><p>这是内容</p></body></html>"
text = processor.extract_text(html_content)
print(f"提取的文本: {text}")

# 标题提取
title = processor.extract_title(html_content)
print(f"提取的标题: {title}")

# 关键词提取
keywords = processor.extract_keywords(text, top_k=5)
print(f"关键词: {keywords}")

# 生成摘要
summary = processor.generate_summary(text, max_sentences=2)
print(f"摘要: {summary}")

# 计算相关性评分
score = processor.calculate_relevance_score(
    "Python programming tutorial guide",
    "python tutorial"
)
print(f"相关性评分: {score}")
```

## 性能优化技巧

### 1. 并发调优

```python
# 根据网络条件调整并发数
config.max_workers = 10  # 高速网络\config.max_workers = 3   # 慢速网络
config.timeout = 60      # 不稳定网络
```

### 2. 缓存策略

```python
# 定期清理过期缓存
stats = cache.get_stats()
if stats['total_entries'] > 1000:
    # 清理最旧的条目
    cache.clear_old_entries(days=30)
```

### 3. 错误处理

```python
# 处理抓取失败的情况
results = crawler.fetch_urls(urls)

failed_urls = []
for result in results:
    if not result['success']:
        failed_urls.append({
            'url': result['url'],
            'error': result.get('error_message', 'Unknown error')
        })

# 重试失败的URL
if failed_urls:
    print(f"失败数量: {len(failed_urls)}")
    retry_urls = [item['url'] for item in failed_urls]
    
    # 等待一段时间后重试
    time.sleep(10)
    retry_results = crawler.fetch_urls(retry_urls)
```

## 实际应用场景

### 1. 网站内容监控

```python
import time
from datetime import datetime

def monitor_websites(urls, interval_hours=6):
    """定期监控网站内容变化"""
    
    config = Config()
    crawler = WebCrawler(config)
    cache = CacheManager(config)
    
    while True:
        print(f"\n[{datetime.now()}] 开始监控检查...")
        
        # 抓取所有URL
        results = crawler.fetch_urls(urls)
        
        changes_detected = []
        
        for result in results:
            if result['success']:
                # 检查内容是否变化（通过哈希值）
                old_entry = cache.retrieve(result['url'])
                
                if old_entry:
                    if old_entry['content_hash'] != result['content_hash']:
                        changes_detected.append({
                            'url': result['url'],
                            'old_hash': old_entry['content_hash'],
                            'new_hash': result['content_hash']
                        })
                
                # 更新缓存
                cache.store(result)
        
        if changes_detected:
            print(f"检测到 {len(changes_detected)} 个网站内容变化")
            for change in changes_detected:
                print(f"  - {change['url']}")
        else:
            print("未发现内容变化")
        
        # 等待下次检查
        print(f"下次检查时间: {interval_hours}小时后")
        time.sleep(interval_hours * 3600)

# 使用示例
monitor_urls = [
    "https://news.ycombinator.com",
    "https://reddit.com/r/programming",
    "https://github.com/trending"
]

monitor_websites(monitor_urls, interval_hours=2)
```

### 2. 内容聚合器

```python
def build_content_aggregator(search_terms):
    """构建内容聚合器"""
    
    # 定义源网站
    sources = {
        'tech_news': [
            'https://techcrunch.com',
            'https://arstechnica.com',
            'https://theverge.com'
        ],
        'programming': [
            'https://stackoverflow.com/questions/tagged/python',
            'https://dev.to/t/python',
            'https://realpython.com'
        ]
    }
    
    config = Config()
    crawler = WebCrawler(config)
    cache = CacheManager(config)
    processor = TextProcessor()
    
    # 抓取所有源
    all_urls = []
    for category, urls in sources.items():
        all_urls.extend(urls)
    
    print(f"开始抓取 {len(all_urls)} 个源...")
    results = crawler.fetch_urls(all_urls)
    
    # 存储到缓存
    for result in results:
        if result['success']:
            cache.store(result)
    
    # 搜索相关内容
    successful_urls = cache.get_successful_urls()
    cache_entries = [cache.retrieve(url) for url in successful_urls]
    
    aggregated_content = {}
    
    for term in search_terms:
        print(f"\n搜索相关内容: '{term}'")
        search_results = processor.search_content(cache_entries, term, top_k=10)
        
        aggregated_content[term] = []
        for result in search_results:
            aggregated_content[term].append({
                'url': result.url,
                'title': result.title,
                'summary': result.summary,
                'relevance': result.relevance_score
            })
    
    return aggregated_content

# 使用示例
search_terms = ['machine learning', 'web development', 'data science']
content = build_content_aggregator(search_terms)

# 显示聚合结果
for term, results in content.items():
    print(f"\n=== {term.upper()} ===")
    for result in results[:3]:  # 显示前3个结果
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"相关度: {result['relevance']:.2f}")
        print(f"摘要: {result['summary'][:100]}...")
        print("-" * 50)
```

### 3. 网站地图生成器

```python
def generate_sitemap_from_cache():
    """从缓存生成网站地图"""
    
    config = Config()
    cache = CacheManager(config)
    
    # 获取所有缓存的URL
    stats = cache.get_stats()
    all_urls = cache.get_successful_urls() + cache.get_failed_urls()
    
    sitemap = {
        'total_urls': len(all_urls),
        'successful_urls': stats['successful_entries'],
        'failed_urls': stats['failed_entries'],
        'categories': {}
    }
    
    # 按域名分类
    for url in all_urls:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if domain not in sitemap['categories']:
            sitemap['categories'][domain] = []
        
        entry = cache.retrieve(url)
        if entry:
            sitemap['categories'][domain].append({
                'url': url,
                'title': entry.get('title', 'Unknown'),
                'status_code': entry.get('status_code'),
                'fetch_time': entry.get('fetch_time'),
                'content_size': len(entry.get('content', '')) if entry.get('content') else 0
            })
    
    return sitemap

# 生成并保存网站地图
sitemap = generate_sitemap_from_cache()

import json
with open('sitemap.json', 'w', encoding='utf-8') as f:
    json.dump(sitemap, f, ensure_ascii=False, indent=2)

print(f"网站地图已生成，包含 {sitemap['total_urls']} 个URL")
print(f"成功: {sitemap['successful_urls']}, 失败: {sitemap['failed_urls']}")
```

## 最佳实践

### 1. 错误处理

```python
def safe_fetch_with_fallback(urls, max_attempts=3):
    """带重试和回退的安全抓取"""
    
    config = Config()
    crawler = WebCrawler(config)
    
    for attempt in range(max_attempts):
        try:
            results = crawler.fetch_urls(urls)
            
            # 检查成功率
            success_rate = sum(1 for r in results if r['success']) / len(results)
            
            if success_rate < 0.5:  # 成功率低于50%
                print(f"尝试 {attempt + 1}: 成功率过低 ({success_rate:.1%})，重试...")
                time.sleep(10 * (attempt + 1))  # 递增延迟
                continue
            
            return results
            
        except Exception as e:
            print(f"尝试 {attempt + 1} 失败: {e}")
            if attempt < max_attempts - 1:
                time.sleep(10 * (attempt + 1))
    
    # 所有尝试都失败，返回空结果
    return []
```

### 2. 性能优化

```python
def optimized_batch_processing(urls, batch_size=50):
    """优化的批量处理"""
    
    config = Config()
    # 根据网络条件调整参数
    config.max_workers = min(10, len(urls) // 10)  # 动态调整并发数
    config.timeout = 60  # 充足的超时时间
    
    crawler = WebCrawler(config)
    
    # 分批处理
    results = []
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        print(f"处理批次 {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1}")
        
        batch_results = crawler.fetch_urls(batch)
        results.extend(batch_results)
        
        # 批次间短暂休息
        if i + batch_size < len(urls):
            time.sleep(2)
    
    return results
```

### 3. 数据验证

```python
def validate_and_clean_results(results):
    """验证和清理抓取结果"""
    
    valid_results = []
    
    for result in results:
        if not result['success']:
            continue
            
        # 验证内容
        content = result.get('content', '')
        if not content or len(content) < 100:  # 内容太短
            print(f"跳过 {result['url']}: 内容太短")
            continue
            
        # 验证内容类型
        content_type = result.get('content_type', '')
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            print(f"跳过 {result['url']}: 不支持的内容类型 {content_type}")
            continue
            
        # 验证状态码
        if result['status_code'] != 200:
            print(f"跳过 {result['url']}: 状态码 {result['status_code']}")
            continue
            
        valid_results.append(result)
    
    print(f"有效结果: {len(valid_results)}/{len(results)}")
    return valid_results
```

## 故障排除

### 常见问题解决方案

```python
def troubleshoot_fetch_issues():
    """抓取问题故障排除"""
    
    config = Config()
    
    # 问题1: 连接超时
    config.timeout = 120  # 增加超时时间
    
    # 问题2: 频繁失败
    config.max_retries = 5  # 增加重试次数
    config.retry_delay = 3.0  # 增加重试延迟
    
    # 问题3: 内存不足
    config.max_workers = 2  # 减少并发数
    config.max_content_size = 5 * 1024 * 1024  # 限制内容大小为5MB
    
    crawler = WebCrawler(config)
    
    # 测试单个URL
    test_url = "https://httpbin.org/html"
    result = crawler.fetch_url(test_url)
    
    if result['success']:
        print(f"测试成功: {result['url']}")
        print(f"状态码: {result['status_code']}")
        print(f"抓取时间: {result['fetch_time']:.2f}s")
        print(f"内容大小: {len(result.get('content', ''))} bytes")
    else:
        print(f"测试失败: {result.get('error_message', 'Unknown error')}")
    
    return result
```

这个示例文档展示了 WebCache Explorer 的各种使用场景，从基础操作到高级应用，帮助用户充分利用工具的功能。