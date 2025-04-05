import os
from pathlib import Path
import sys,subprocess,shutil
import tarfile,requests
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


class MMTests:
    def __init__(self, **kwargs):
        self.rpms = {'expect','pcre-devel','bzip2-devel','xz-devel','libcurl-devel','libcurl','texinfo','gcc-gfortran','java-1.8.0-openjdk-devel','wget','libXt-devel','readline-devel','glibc-headers','gcc-c++','zlib','zlib-devel','bc','httpd','net-tools','m4','flex','bison','byacc','keyutils-libs-devel','lksctp-tools-devel','xfsprogs-devel','libacl-devel','openssl','openssl-devel','numactl-devel','libaio-devel','glibc-devel','libcap-devel','patch','findutils','libtirpc','libtirpc-devel','kernel-headers','glibc-headers','hwloc-devel','numactl','automake','fio','sysstat','time','psmisc','popt-devel','libstdc++','libstdc++-static','elfutils-libelf-devel','slang-devel','libbabeltrace-devel','zstd-devel','gtk2-devel','systemtap','libtool','rpcgen','vim'}
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/mmtests')
        self.directory: Path = kwargs.get('saved_directory') / 'mmtests'


    # 下载/编译/安装R包
    def prepare_R(self):
        pass


    # 下载/编译/安装List-BinarySearch
    def prepare_L(self):
        pass


    # 下载/编译/安装File-Slurp
    def prepare_F(self):
        pass


    # 准备mmtests
    def prepare_M(self):
        # 获取mmtests的源码
        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path, ignore_errors=True)
            git_clone =  subprocess.run(
                "cd /osmts_tmp/ && git clone https://gitcode.com/gh_mirrors/mm/mmtests.git",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if git_clone.returncode != 0:
                print(f"MMTtests测试出错.git clone运行失败,报错信息:{git_clone.stderr.decode('utf-8')}")
                sys.exit(1)


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)

        with ThreadPoolExecutor(max_workers=4) as pool:
            pool.submit(self.prepare_R)
            pool.submit(self.prepare_L)
            pool.submit(self.prepare_F)
            pool.submit(self.prepare_M)



    def run_test(self):
        pass


    def run(self):
        print("开始进行MMTests测试")
        self.pre_test()
        self.run_test()
        print("MMTests测试结束")
