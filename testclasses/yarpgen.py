import os
from pathlib import Path
import sys,subprocess,shutil
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


class Yarpgen:
    def __init__(self, **kwargs):
        self.rpms = {'gcc-g++'}
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/yarpgen')
        self.directory: Path = kwargs.get('saved_directory') / 'yarpgen'
        self.yarpgen = Path('/root/osmts_tmp/yarpgen/build/yarpgen')
        self.testdir = Path('/root/osmts_tmp/yarpgen/testdir')
        self.yarpgen_count = kwargs.get('yarpgen_count')

        self.passed = 0
        self.failed = 0


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

        if self.testdir.exists():
            shutil.rmtree(self.testdir)
        self.testdir.mkdir(parents=True)

        # 构建yarpgen命令
        build = subprocess.run(
            f"cd /root/osmts_tmp/yarpgen && mkdir build && cd build && cmake .. && make -j {os.cpu_count()}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"yarpgen测试出错.cmake和make失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)


    def create_source_code_and_run(self,id) -> dict:
        directory = self.testdir / str(id)

        # 生成随机c++代码
        create_source_code = subprocess.run(
            f"cd {directory} && {self.yarpgen} && cat init.h func.cpp driver.cpp > random.cpp",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if create_source_code.returncode != 0:
            print(f"yarpgen测试{id}出错.创建随机c++源代码文件失败,报错信息:{create_source_code.stderr.decode('utf-8')}")
            sys.exit(1)

        # 编译c++代码
        compile = subprocess.run(
            f"g++ {directory}/random.cpp -O0 -o {directory}/g++_O0.out &&" # 不开优化编译
            f"g++ {directory}/random.cpp -O3 -o {directory}/g++_O3.out",         # O3优化编译
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if compile.returncode != 0:
            print(f"yarpgen测试{id}出错.编译c++源代码失败,报错信息:{compile.stderr.decode('utf-8')}")
            sys.exit(1)

        # 执行并判断
        O1_result = subprocess.run(
            f"{directory}/g++_O1.out",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode('utf-8')
        O3_result = subprocess.run(
            f"{directory}/g++_O3.out",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.decode('utf-8')
        return {
            "id":id,
            "same":(O1_result == O3_result)
        }


    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'yarpgen'
        ws.append(['请进入/root/osmts_tmp/yarpgen/testdir查看所有结果'])
        ws.append(['出错项目id'])

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
            results = pool.map(self.create_source_code_and_run, range(1, self.yarpgen_count + 1))
            for result in results:
                if result.get('same'):
                    self.passed += 1
                else:
                    self.failed += 1
                    ws.append([result.get('id',"获取id失败")])
        wb.save(self.directory / 'yarpgen.xlsx')


    def run(self):
        print("开始运行yarpgen测试")
        self.pre_test()
        self.run_test()
        print("yarpgen测试结束")