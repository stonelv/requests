#!/bin/bash

echo "=== 示例1: 基础使用 ==="
python -m reqcheck examples/urls.txt -o results.json

echo -e "\n=== 示例2: 导出为CSV ==="
python -m reqcheck examples/urls.txt -o results.csv -f csv

echo -e "\n=== 示例3: 详细模式 ==="
python -m reqcheck examples/urls.txt -v

echo -e "\n=== 示例4: 自定义请求头 ==="
python -m reqcheck examples/urls.txt -H "User-Agent: CustomAgent/1.0" -H "Accept: application/json"

echo -e "\n=== 示例5: 高并发 ==="
python -m reqcheck examples/urls.txt -C 10

echo -e "\n=== 示例6: 自定义配置文件 ==="
python -m reqcheck --config examples/config.json

echo -e "\n=== 示例7: 下载模式 ==="
python -m reqcheck -d -D ./downloads examples/urls.txt

echo -e "\n所有示例运行完成！"