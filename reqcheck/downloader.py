import os
import hashlib
import shutil
from typing import Optional
from tqdm import tqdm

class Downloader:
    def __init__(self, config):
        self.config = config
        self.download_dir = config.download_dir
        
        # 创建下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def get_filename(self, url: str, content_type: Optional[str] = None) -> str:
        # 从URL提取文件名，处理以'/'结尾的情况
        parts = url.split('/')
        # 过滤掉由末尾斜杠导致的空字符串
        parts = [p for p in parts if p]
        filename = parts[-1] if parts else ''
        if not filename or '.' not in filename:
            # 如果没有扩展名，使用内容类型或默认名
            if content_type and ';' in content_type:
                content_type = content_type.split(';')[0]
            if content_type and '/' in content_type:
                ext = content_type.split('/')[-1]
                filename = f'unknown.{ext}'
            else:
                filename = 'unknown.bin'
        
        # 处理重复文件名
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(self.download_dir, filename)):
            filename = f'{base_name}_{counter}{ext}'
            counter += 1
        
        return filename

    def save_content(self, url: str, content: bytes, headers: dict = None) -> str:
        if not content:
            return None
        
        # 获取文件名
        content_type = headers.get('Content-Type') if headers else None
        filename = self.get_filename(url, content_type)
        file_path = os.path.join(self.download_dir, filename)
        
        try:
            # 显示进度条
            with tqdm(
                total=len(content),
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc=f'Downloading {filename}',
                leave=False
            ) as pbar:
                with open(file_path, 'wb') as f:
                    f.write(content)
                    pbar.update(len(content))
            
            return file_path
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

    def get_file_hash(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return None
        
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()

    def cleanup(self):
        # 清空下载目录
        if os.path.exists(self.download_dir):
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'清理文件失败: {e}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
