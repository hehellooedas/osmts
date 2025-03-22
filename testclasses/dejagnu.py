from pathlib import Path
import sys,subprocess,shutil



class DejaGnu:
    def __init__(self, **kwargs):
        self.rpms = {'gcc-g++', 'gcc-gfortran', 'dejagnu'}
        self.path = Path('/root/osmts_tmp/dejagnu')
        self.directory: Path = kwargs.get('saved_directory') / 'dejagnu'


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)
        # 拉取源码
        git_clone = subprocess.run(
            f"cd {self.path} && git clone https://gitee.com/openeuler/gcc.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"dejagnu测试出错.拉取源码失败,报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        gcc = subprocess.run(
            f"cd /root/osmts_tmp/dejagnu/gcc/gcc/testsuite/ && runtest --tool gcc && cp gcc.log gcc.sum {self.directory}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if gcc.returncode != 0:
            print(f"dejagnu测试出错.runtest --tool gcc命令运行失败,报错信息:{gcc.stderr.decode('utf-8')}")
            sys.exit(1)


        cpp = subprocess.run(
            f"cd /root/osmts_tmp/dejagnu/gcc/gcc/testsuite/ && runtest --tool g++ && cp cpp.log cpp.sum {self.directory}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if cpp.returncode != 0:
            print(f"dejagnu测试出错.runtest --tool g++命令运行失败,报错信息:{cpp.stderr.decode('utf-8')}")
            sys.exit(1)


        gfortran = subprocess.run(
            f"cd /root/osmts_tmp/dejagnu/gcc/gcc/testsuite/ && runtest --tool gfortran && cp gfortran.log gfortran.sum {self.directory}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if gfortran.returncode != 0:
            print(f"dejagnu测试出错.runtest --tool gfortran命令运行失败,报错信息:{gfortran.stderr.decode('utf-8')}")
            sys.exit(1)


    def run(self):
        print('开始进行dejagnu测试')
        self.pre_test()
        self.run_test()
        print('dejagnu测试结束')