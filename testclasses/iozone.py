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
        get_iozone = subprocess.run("cd /root/osmts_tmp/iozone && wget https://www.iozone.org/src/current/iozone3_506.tar && tar -xvf iozone3_506.tar",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if get_iozone.returncode != 0:
            print(f"iozone测试出错:获取iozone源码失败.报错信息:{get_iozone.stderr.decode('utf-8')}")
            sys.exit(1)

