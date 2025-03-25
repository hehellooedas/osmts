import shutil
import subprocess
import sys,os,threading
from pathlib import Path
from openpyxl import Workbook

class Jtreg:
    def __init__(self, **kwargs):
        self.rpms = {}
        self.path = Path('/root/osmts_tmp/jtreg')
        self.directory: Path = kwargs.get('saved_directory') / 'jtreg'
