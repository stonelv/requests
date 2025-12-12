from setuptools import setup, find_packages
import re

# 读取版本号
with open('reqcheck/__version__.py', 'r') as f:
    version_content = f.read()
    version_match = re.search(r'__version__ = "(.*?)"', version_content)
    version = version_match.group(1) if version_match else '0.0.1'

# 读取README
with open('README_REQCHECK.md', 'r') as f:
    readme = f.read()

# 读取依赖
with open('requirements_reqcheck.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='reqcheck',
    version=version,
    description='批量URL检查工具',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your@email.com',
    url='https://github.com/your/repo',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'reqcheck = reqcheck.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
)