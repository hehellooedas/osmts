from pathlib import Path
import sys,subprocess,shutil,hashlib,requests,re
from multiprocessing import Process
from openpyxl.workbook import Workbook


class Trinity:
    def __init__(self,**kwargs ):
        self.path = Path('/root/osmts_tmp/trinity')
        self.directory:Path = kwargs.get('saved_directory')
        self.compiler:str = kwargs.get('compiler')
        self.remove_osmts_tmp_dir:bool = kwargs.get('remove_osmts_tmp_dir')
        self.test_result:str = ''


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir()
        install_rpm = subprocess.run(
            f"dnf install {self.compiler} make -y",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        if install_rpm.returncode != 0:
            print(f"trinity测试出错:编译器安装失败.报错信息:{install_rpm.stderr.decode('utf-8')}")
            sys.exit(1)

        git_clone = subprocess.run(
            f"cd /root/osmts_tmp/ && git clone https://gitee.com/April_Zhao/trinity_{self.compiler}.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        if git_clone.returncode != 0:
            print(f"trinity测试出错:git clone失败.报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        config_make = subprocess.run(
            f"cd /root/osmts_tmp/trinity_{self.compiler} && ./configure && make && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        if config_make.returncode != 0:
            print(f"trinity测试出错:configure和make失败.报错信息:{config_make.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        trinity = subprocess.run(
            "cd /root/osmts_tmp/trinity_{self.compiler} && ./trinity -N 10000 | tee output.log",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if trinity.returncode != 0:
            print(f"trinity测试出错:configure和make失败.报错信息:{trinity.stderr.decode('utf-8')}")
            sys.exit(1)
        self.test_result = trinity.stdout.decode('utf-8')
        with open(self.path / 'trinity.log','w') as file:
            file.write(self.test_result)


    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)


    def result2summary(self):
        pass


    def run(self):
        print("开始进行libmicro测试")
        self.pre_test()
        self.run_test()
        self.result2summary()
        if self.remove_osmts_tmp_dir:
            self.post_test()
        print("libmicro测试结束")