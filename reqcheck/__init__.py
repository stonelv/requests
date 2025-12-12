# reqcheck - 批量URL检查工具
# 版本: 1.0.0
# 作者: Your Name
# 邮箱: your.email@example.com

from .__version__ import __version__, __author__, __author_email__ as __email__
from .cli import main

__all__ = ["main", "__version__", "__author__", "__email__"]

if __name__ == "__main__":
    main()