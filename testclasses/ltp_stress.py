from multiprocessing import Process
from pathlib import Path
import sys,subprocess,shutil


class Ltp_stress(Process):
    def __init__(self, **kwargs):
        super().__init__()
        self.path = Path('/root/osmts_tmp/ltp_stress')
        self.directory: Path = kwargs.get('saved_directory')
        self.compiler: str = kwargs.get('compiler')


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        # 安装rpm包
        install_rpm = subprocess.run(
            "yum install -y git make automake gcc clang pkgconf autoconf bison flex m4 kernel-headers glibc-headers clang findutils libtirpc libtirpc-devel pkg-config sysstat",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if install_rpm.returncode != 0:
            print(f"ltp_stress测试出错:安装rpm包失败.报错信息:{install_rpm.stderr.decode('utf-8')}")
            sys.exit(1)

        # 拉取源码
        git_clone = subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitee.com/April_Zhao/ltp_stress.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"ltp_stress测试出错:git clone拉取源码失败.报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        # 编译
        if self.compiler == "gcc":
            build = subprocess.run(
                "cd /root/osmts_tmp/ltp_stress && make autotools && ./configure && make -j $(nproc) && make install",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        elif self.compiler == "clang":
            build = subprocess.run(
                'cd /root/osmts_tmp/ltp_stress && export CFLAGS="-Wno-error=implicit-function-declaration" && make autotools && CC=clang ./configure ./configure && make -j $(nproc) && make install',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

        if build.returncode != 0:
            print(f"ltp_stress测试出错:ltp_stress源码编译不通过.报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        ltpstress_sh = subprocess.run(
            "cd /opt/ltp/testscripts && mkdir -p /opt/ltp/output && ./ltpstress.sh -i 3600 -d /opt/ltp/output/ltpstress.data -I /opt/ltp/output/ltpstress.iodata -l /opt/ltp/output/ltpstress.log -n -p -S -m 512 -t 168",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if ltpstress_sh.returncode != 0:
            print(f"ltp_stress测试出错:ltpstress.sh进程运行失败.报错信息:{ltpstress_sh.stderr.decode('utf-8')}")
            sys.exit(1)


    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)


    def run(self):
        print("开始进行ltp_stress")
        self.pre_test()
        self.run_test()
        self.post_test()
        print("ltp_stress测试结束")