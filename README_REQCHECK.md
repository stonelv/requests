# reqcheck - Bulk URL Checker

A powerful command-line tool for bulk URL checking with concurrent requests, retry logic, and detailed reporting.

## Features

- **Concurrent Requests**: Check multiple URLs at once
- **Retry Logic**: Exponential backoff for failed requests
- **Proxy Support**: Configure HTTP/HTTPS proxies
- **Timeout Configuration**: Set custom request timeouts
- **Download Mode**: Save responses to local files
- **Progress Bar**: Visual progress tracking
- **Detailed Reporting**: Export results to CSV/JSON
- **Custom Headers/Cookies**: Configure request headers and cookies

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
reqcheck --urls examples/urls.txt --output results.csv
```

### Advanced Usage

```bash
reqcheck --urls examples/urls.txt \
    --output results.json \
    --method GET \
    --timeout 10 \
    --max-retries 3 \
    --retry-delay 1 \
    --proxy http://proxy.example.com:8080 \
    --headers examples/headers.json \
    --cookies examples/cookies.json \
    --concurrency 20 \
    --verbose
```

### Download Mode

```bash
reqcheck --urls examples/urls.txt \
    --download \
    --download-dir downloads \
    --concurrency 5
```

## Output Format

### CSV Output

The CSV file includes these fields:
- `url`: Original URL
- `final_url`: Final URL after redirects
- `status_code`: HTTP status code
- `elapsed`: Response time in seconds
- `redirected`: Whether the request was redirected
- `timed_out`: Whether the request timed out
- `content_length`: Content length in bytes
- `error`: Error message if the request failed

### JSON Output

The JSON file includes the same fields as CSV, in a structured format.

## Command-Line Options

```
usage: reqcheck [-h] [--urls URLS] [--output OUTPUT] [--method {GET,HEAD,POST}]
                [--timeout TIMEOUT] [--max-retries MAX_RETRIES]
                [--retry-delay RETRY_DELAY] [--proxy PROXY] [--headers HEADERS]
                [--cookies COOKIES] [--download] [--download-dir DOWNLOAD_DIR]
                [--concurrency CONCURRENCY] [--verbose] [--no-progress]
                [--version]

reqcheck - A bulk URL checker tool

optional arguments:
  -h, --help            show this help message and exit
  --urls URLS           File containing URLs to check (one per line)
  --output OUTPUT       Output file path (supports .csv or .json)
  --method {GET,HEAD,POST}
                        HTTP request method (default: GET)
  --timeout TIMEOUT     Request timeout in seconds (default: 10.0)
  --max-retries MAX_RETRIES
                        Maximum number of retries per URL (default: 3)
  --retry-delay RETRY_DELAY
                        Initial retry delay in seconds (exponential backoff)
                        (default: 1.0)
  --proxy PROXY         Proxy URL (e.g., http://proxy.example.com:8080)
  --headers HEADERS     Path to JSON file containing custom headers
  --cookies COOKIES     Path to JSON file containing cookies
  --download            Enable download mode to save responses
  --download-dir DOWNLOAD_DIR
                        Directory to save downloaded files (default: downloads)
  --concurrency CONCURRENCY
                        Number of concurrent requests (default: 10)
  --verbose             Enable verbose logging
  --no-progress         Disable progress bar
  --version             show program's version number and exit
```

## Project Structure

```
reqcheck/
├── __init__.py
├── __version__.py
├── cli.py          # Command-line interface
├── config.py       # Configuration management
├── logging_utils.py # Logging utilities
├── requestor.py    # HTTP request handling
├── runner.py       # Main execution flow
├── exporters.py    # Result export to CSV/JSON
└── downloader.py   # File downloading
```

## Development

### Running Tests

```bash
pytest tests/test_reqcheck.py
```

### Running Linter

```bash
flake8 reqcheck/
```

## License

MIT License