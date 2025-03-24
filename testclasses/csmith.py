from pathlib import Path
import sys,subprocess,shutil
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


class Csmith:
    def __init__(self, **kwargs):
        self.rpms = {'g++','m4','gcc','clang'}
        self.path = Path('/root/osmts_tmp/csmith')
        self.directory: Path = kwargs.get('saved_directory') / 'csmith'
        self.source:Path = self.directory / 'source'
        self.bin: Path = self.directory / 'bin'


    def create_source_and_bin(self,number):
        # 创建随机c文件
        csmith = subprocess.run(
            "/root/osmts_tmp/csmith/install/bin/csmith",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if csmith.returncode != 0:
            print(f"csmith测试出错.生成c代码失败,报错信息:{csmith.stderr.decode('utf-8')}")
            sys.exit(1)
        with open(f"{self.source}/csmith{number}.c", "w") as file:
            file.write(csmith.stdout.decode('utf-8'))

        # 分别用gcc和clang编译c文件
        compile = subprocess.run(
            f"gcc {self.source}/csmith{number}.c -I {self.path}/install/include -o {self.bin}/csmith{number}_gcc && "
            f"clang {self.source}/csmith{number}.c -I {self.path}/install/include -o {self.bin}/csmith{number}_clang",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if compile.returncode != 0:
            print(f"csmith测试出错.编译c代码失败,报错信息:{compile.stderr.decode('utf-8')}")
            sys.exit(1)


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        if not self.source.exists():
            self.source.mkdir()
        if not self.bin.exists():
            self.bin.mkdir()

        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True,exist_ok=True)

        git_clone =subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitcode.com/qq_61653333/csmith.git -b master",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"Csmith测试出错.git clone失败,报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        build = subprocess.run(
            f"cd {self.path} && mkdir install && cmake -DCMAKE_INSTALL_PREFIX=/root/osmts_tmp/csmith/install . && make && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"Csmith测试出错.构建csmith项目失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)

        # 批量生成c代码
        with ThreadPoolExecutor() as pool:
            pool.map(self.create_source_and_bin, [i for i in range(1,1001)])



    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'Csmith'




    def run(self):
        print('开始进行Csmith测试')
        self.pre_test()
        self.run_test()
        print('Csmith测试结束')
