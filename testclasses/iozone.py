from pathlib import Path
import sys,subprocess,shutil
from testclasses.excel2csv import excel2csv


class Iozone:
    def __init__(self,**kwargs ):
        self.path = Path('/root/osmts_tmp/iozone')
        self.saved_method:str = kwargs.get('saved_method')
        self.directory:Path = kwargs.get('saved_directory')
        self.compiler:str = kwargs.get('compiler')

    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        # 获取iozone的源码
        git_clone = subprocess.run("cd /root/osmts_tmp/iozone && wget https://www.iozone.org/src/current/iozone3_506.tar && tar -xvf iozone3_506.tar",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if git_clone.returncode != 0:
            print(f"iozone测试出错:下载/解压iozone源码压缩包失败.报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        #编译iozone
        compile = subprocess.run(f"cd /root/osmts_tmp/iozone/iozone3_506/src/current && make clean && make CC={self.compiler} CFLAGS=-fcommon linux",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if compile.returncode != 0:
            print(f"iozone测试出错:编译iozone失败.报错信息:{compile.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        iozone = subprocess.run(f"cd /root/osmts_tmp/iozone/iozone3_506/src/current && ./iozone -Rab {self.directory}/iozone.xls",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if iozone.returncode != 0:
            print(f"iozone测试出错:iozone运行报错.报错信息:{iozone.stderr.decode('utf-8')}")
            sys.exit(1)

    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)


    def run(self):
        print("开始进行iozone测试")
        self.pre_test()
        self.run_test()
        self.post_test()
        print("iozone测试结束")
