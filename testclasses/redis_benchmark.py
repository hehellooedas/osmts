from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from pathlib import Path
import re
import sys,subprocess,shutil


class sysBench: # redis-benchmark 是 Redis 自带的基准测试工具
    def __init__(self, **kwargs):
        self.rpms = {'redis'}
        self.directory: Path = kwargs.get('saved_directory') / 'redis-benchmark'

