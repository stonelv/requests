# Requests 库架构分析

## 1. 项目模块分层

Requests 库采用了清晰的分层架构，从高到低依次为：

### 1.1 高层 API 接口层
- **文件**: `src/requests/api.py`
- **作用**: 提供简洁的 HTTP 请求方法，如 `get()`, `post()`, `put()` 等，是用户直接调用的入口

### 1.2 会话管理层
- **文件**: `src/requests/sessions.py`
- **作用**: 管理 HTTP 会话，处理 cookies、连接池、重定向等

### 1.3 核心模型层
- **文件**: `src/requests/models.py`
- **作用**: 定义请求和响应的数据模型，如 `Request`, `PreparedRequest`, `Response` 类

### 1.4 传输适配器层
- **文件**: `src/requests/adapters.py`
- **作用**: 负责与底层 HTTP 库（urllib3）的交互，处理连接、证书验证等

### 1.5 工具层
- **文件**: `src/requests/utils.py`, `src/requests/cookies.py`, `src/requests/auth.py` 等
- **作用**: 提供各种工具函数，如 URL 处理、cookie 管理、认证等

## 2. 主要类/函数及其作用

### 2.1 高层 API 接口

#### `get(url, params=None, **kwargs)`
- **文件**: `src/requests/api.py:62`
- **作用**: 发送 GET 请求
- **参数**:
  - `url`: 请求 URL
  - `params`: 查询字符串参数
  - `**kwargs`: 其他可选参数
- **返回值**: `Response` 对象

```python
def get(url, params=None, **kwargs):
    r"""Sends a GET request.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary, list of tuples or bytes to send
        in the query string for the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("get", url, params=params, **kwargs)
```

#### `request(method, url, **kwargs)`
- **文件**: `src/requests/api.py:14`
- **作用**: 构造并发送请求的核心函数
- **参数**:
  - `method`: HTTP 方法
  - `url`: 请求 URL
  - `**kwargs`: 其他可选参数
- **返回值**: `Response` 对象

```python
def request(method, url, **kwargs):
    """Constructs and sends a :class:`Request <Request>`."""

    with sessions.Session() as session:
        return session.request(method=method, url=url, **kwargs)
```

### 2.2 会话管理

#### `Session` 类
- **文件**: `src/requests/sessions.py:356`
- **作用**: 管理 HTTP 会话，处理 cookies、连接池、重定向等
- **主要方法**:
  - `request()`: 发送请求
  - `send()`: 发送准备好的请求
  - `prepare_request()`: 准备请求

#### `session.request(method, url, **kwargs)`
- **文件**: `src/requests/sessions.py:500`
- **作用**: 创建并发送请求
- **参数**:
  - `method`: HTTP 方法
  - `url`: 请求 URL
  - `**kwargs`: 其他可选参数
- **返回值**: `Response` 对象

#### `session.send(request, **kwargs)`
- **文件**: `src/requests/sessions.py:673`
- **作用**: 发送准备好的请求
- **参数**:
  - `request`: `PreparedRequest` 对象
  - `**kwargs`: 其他可选参数
- **返回值**: `Response` 对象

### 2.3 核心模型

#### `Request` 类
- **文件**: `src/requests/models.py:230`
- **作用**: 表示一个 HTTP 请求
- **主要方法**:
  - `prepare()`: 准备请求，返回 `PreparedRequest` 对象

#### `PreparedRequest` 类
- **文件**: `src/requests/models.py:313`
- **作用**: 表示一个准备好的 HTTP 请求，包含发送所需的所有信息
- **主要方法**:
  - `prepare()`: 准备请求的各个部分
  - `prepare_method()`: 准备 HTTP 方法
  - `prepare_url()`: 准备 URL
  - `prepare_headers()`: 准备头部
  - `prepare_body()`: 准备请求体

#### `Response` 类
- **文件**: `src/requests/models.py:640`
- **作用**: 表示一个 HTTP 响应
- **主要属性**:
  - `status_code`: 状态码
  - `headers`: 响应头部
  - `content`: 响应内容（字节）
  - `text`: 响应内容（字符串）
  - `json()`: 解析 JSON 响应

### 2.4 传输适配器

#### `HTTPAdapter` 类
- **文件**: `src/requests/adapters.py:143`
- **作用**: 处理 HTTP 请求的发送，与 urllib3 交互
- **主要方法**:
  - `send()`: 发送请求
  - `build_response()`: 构建 `Response` 对象

## 3. requests.get() 调用链

从 `requests.get()` 调用到真正发送 HTTP 请求的完整调用链如下：

1. **`requests.get(url, params=None, **kwargs)`** (`src/requests/api.py:62`)
   - 调用 `request("get", url, params=params, **kwargs)`

2. **`request(method, url, **kwargs)`** (`src/requests/api.py:14`)
   - 创建 `Session` 实例
   - 调用 `session.request(method=method, url=url, **kwargs)`

3. **`session.request(method, url, **kwargs)`** (`src/requests/sessions.py:500`)
   - 创建 `Request` 对象
   - 调用 `self.prepare_request(req)` 准备请求
   - 调用 `self.send(prep, **send_kwargs)` 发送请求

4. **`session.prepare_request(request)`** (`src/requests/sessions.py:457`)
   - 合并会话和请求的配置
   - 创建 `PreparedRequest` 对象
   - 调用 `p.prepare()` 准备请求

5. **`prepared_request.prepare()`** (`src/requests/models.py:351`)
   - 调用 `prepare_method()` 准备 HTTP 方法
   - 调用 `prepare_url()` 准备 URL
   - 调用 `prepare_headers()` 准备头部
   - 调用 `prepare_cookies()` 准备 cookies
   - 调用 `prepare_body()` 准备请求体
   - 调用 `prepare_auth()` 准备认证

6. **`session.send(request, **kwargs)`** (`src/requests/sessions.py:673`)
   - 获取 URL 对应的适配器
   - 调用 `adapter.send(request, **kwargs)` 发送请求

7. **`adapter.send(request, **kwargs)`** (`src/requests/adapters.py:590`)
   - 获取连接池
   - 验证证书
   - 构建请求 URL
   - 调用 `conn.urlopen()` 发送请求
   - 构建并返回 `Response` 对象

## 4. 数据流示意图

```
用户代码
  │
  ▼
requests.get()  # api.py
  │
  ▼
request()  # api.py
  │
  ▼
Session()  # sessions.py
  │
  ▼
session.request()  # sessions.py
  │
  ▼
Request()  # models.py
  │
  ▼
session.prepare_request()  # sessions.py
  │
  ▼
PreparedRequest.prepare()  # models.py
  │
  ├───► prepare_method()
  │
  ├───► prepare_url()
  │
  ├───► prepare_headers()
  │
  ├───► prepare_cookies()
  │
  ├───► prepare_body()
  │
  └───► prepare_auth()
  │
  ▼
session.send()  # sessions.py
  │
  ▼
adapter.send()  # adapters.py
  │
  ▼
urllib3.urlopen()  # 底层库
  │
  ▼
HTTP 服务器
  │
  ▼
urllib3 响应
  │
  ▼
adapter.build_response()  # adapters.py
  │
  ▼
Response()  # models.py
  │
  ▼
用户代码
```

## 5. 核心流程说明

1. **请求初始化**: 用户调用 `requests.get()` 等方法，传入 URL 和参数
2. **会话创建**: 创建 `Session` 实例，管理请求上下文
3. **请求准备**: 
   - 创建 `Request` 对象
   - 转换为 `PreparedRequest` 对象
   - 准备请求的各个部分（方法、URL、头部、请求体等）
4. **请求发送**: 
   - 获取合适的 `HTTPAdapter`
   - 通过 urllib3 发送请求
5. **响应处理**: 
   - 接收服务器响应
   - 构建 `Response` 对象
   - 处理重定向（如果需要）
   - 返回 `Response` 对象给用户

## 6. 设计特点

1. **简洁的 API**: 提供直观的高层接口，隐藏底层复杂性
2. **会话管理**: 通过 `Session` 类管理连接池和 cookies，提高性能
3. **灵活的适配器**: 使用适配器模式与底层库交互，便于扩展
4. **全面的功能**: 支持各种 HTTP 特性，如认证、代理、SSL 验证等
5. **优雅的响应处理**: 提供丰富的响应对象方法，如 `json()`、`text` 等

## 7. 代码优化建议

1. **连接池管理**: 对于频繁请求同一主机的场景，建议使用 `Session` 对象以利用连接池
2. **超时设置**: 始终设置合理的超时值，避免请求无限期等待
3. **异常处理**: 捕获并适当处理可能的异常，如 `ConnectionError`、`Timeout` 等
4. **流式处理**: 对于大文件下载，使用 `stream=True` 以减少内存使用
5. **会话重用**: 对于多个相关请求，重用 `Session` 对象以保持状态

通过理解 Requests 库的架构和工作原理，开发者可以更有效地使用和扩展这个强大的 HTTP 客户端库。