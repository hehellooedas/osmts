import shutil
import subprocess
from pathlib import Path
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


class OpenSCAP:
    def __init__(self, **kwargs):
        self.rpms = {'penscap-scanner','scap-security-guide'}
        self.scap_directory = Path("/usr/share/xml/scap/ssg/content/")
        self.scap_files = (
            ""
        )
        self.directory: Path = kwargs.get('saved_directory') / 'OpenSCAP'


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True)


    def run_test(self):
        pass


    def run(self):
        print('开始进行OpenSCAP测试')
        self.pre_test()
        self.run_test()
        print('OpenSCAP测试结束')
