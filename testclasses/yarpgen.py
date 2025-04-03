import os
from pathlib import Path
import sys,subprocess,shutil
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor,as_completed


class Yarpgen:
    def __init__(self, **kwargs):
        self.rpms = {'gcc-g++'}
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/yarpgen')
        self.directory: Path = kwargs.get('saved_directory') / 'yarpgen'
        self.yarpgen_count = kwargs.get('yarpgen_count')


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path)
            git_clone = subprocess.run(
                "cd /root/osmts_tmp && git clone https://gitcode.com/gh_mirrors/ya/yarpgen.git",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if git_clone.returncode != 0:
                print(f"yarpgen测试出错.git clone失败,报错信息:{git_clone.stderr.decode('utf-8')}")
                sys.exit(1)

        build = subprocess.run(
            "cd /root/osmts_tmp/yarpgen && mkdir build && cd build && cmake .. && make",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"yarpgen测试出错.cmake和make失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)



    def run_test(self):
        with ThreadPoolExecutor() as pool:
            pass


    def run(self):
        print("开始运行yarpgen测试")
        self.pre_test()
        self.run_test()
        print("yarpgen测试结束")
