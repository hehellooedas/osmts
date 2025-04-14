from pathlib import Path
import subprocess,shutil

from .errors import GitCloneError,RunError


class DejaGnu:
    def __init__(self, **kwargs):
        self.rpms = {'gcc-g++', 'gcc-gfortran', 'dejagnu'}
        self.path = Path('/root/osmts_tmp/dejagnu')
        self.directory: Path = kwargs.get('saved_directory') / 'dejagnu'
        self.testsuite = Path("/root/osmts_tmp/dejagnu/gcc/gcc/testsuite/")


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)
        # 拉取源码
        try:
            subprocess.run(
                f"git clone https://gitee.com/openeuler/gcc.git",
                cwd=self.path,
                shell=True,check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise GitCloneError(e.returncode,'https://gitee.com/openeuler/gcc.git',e.stderr.decode())


    def run_test(self):
        try:
            subprocess.run(
                f"runtest --tool gcc && cp gcc.log gcc.sum {self.directory}",
                cwd=self.testsuite,
                shell=True,check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise RunError(e.returncode,f"dejagnu测试出错.runtest --tool gcc命令运行失败,报错信息:{e.stderr.decode('utf-8')}")

        try:
            subprocess.run(
                f"runtest --tool g++ && cp cpp.log cpp.sum {self.directory}",
                cwd=self.testsuite,
                shell=True,check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise RunError(e.returncode,f"dejagnu测试出错.runtest --tool g++命令运行失败,报错信息:{e.stderr.decode('utf-8')}")


        try:
            # gfortran
             subprocess.run(
                f"runtest --tool gfortran && cp gfortran.log gfortran.sum {self.directory}",
                cwd=self.testsuite,
                shell=True,check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise RunError(e.returncode,f"dejagnu测试出错.runtest --tool gfortran命令运行失败,报错信息:{e.stderr.decode('utf-8')}")


    def run(self):
        print('开始进行dejagnu测试')
        self.pre_test()
        self.run_test()
        print('dejagnu测试结束')