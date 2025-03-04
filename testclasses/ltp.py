from pathlib import Path
import sys,subprocess,shutil
from openpyxl import Workbook


class Ltp:
    def __init__(self, **kwargs):
        self.path = Path('/root/osmts_tmp/ltp')
        self.directory: Path = kwargs.get('saved_directory')
        self.compiler: str = kwargs.get('compiler')
        self.remove_osmts_tmp_dir:bool = kwargs.get('remove_osmts_tmp_dir')
        self.test_result = ''


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        install_rpm = subprocess.run(
            "yum install -y --skip-broken --nobest automake gcc clang pkgconf autoconf bison flex m4 kernel-headers glibc-headers clang findutils libtirpc libtirpc-devel pkg-config",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if install_rpm.returncode != 0:
            print(f"ltp测试出错:安装rpm包失败.报错信息:{install_rpm.stderr.decode('utf-8')}")
            sys.exit(1)

        git_clone = subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitcode.com/gh_mirrors/ltp/ltp.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"ltp测试出错.git clone拉取ltp源码失败:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        make = subprocess.run(
            "cd /root/osmts_tmp/ltp/ && make autotools && ./configure && make -j $(nproc) && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if make.returncode != 0:
            print(f"ltp测试出错.configure和make出错:报错信息:{make.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        runltp = subprocess.run(
            "cd /opt/ltp && ./runltp",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if runltp.returncode != 0:
            print(f"ltp测试出错.runltp进程报错:报错信息:{runltp.stderr.decode('utf-8')}")
            sys.exit(1)
        self.test_result = runltp.stdout.decode('utf-8')


    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)


    def run(self):
        print("开始进行ltp测试")
        self.pre_test()
        self.run_test()
        if self.remove_osmts_tmp_dir:
            self.post_test()
        print("ltp测试结束")
