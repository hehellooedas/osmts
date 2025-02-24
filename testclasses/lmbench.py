from pathlib import Path
import re,sys,subprocess,shutil,pexpect
from openpyxl import Workbook
from testclasses.excel2csv import excel2csv


class Lmbench:
    def __init__(self, **kwargs):
        self.path = Path('/root/osmts_tmp/lmbench')
        self.saved_method: str = kwargs.get('saved_method')
        self.directory: Path = kwargs.get('saved_directory')
        self.compiler: str = kwargs.get('compiler')
        self.remove_osmts_tmp_dir:bool = kwargs.get('remove_osmts_tmp_dir')
        self.test_result = ''


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        # 获取lmbench源码
        git_clone = subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitee.com/April_Zhao/lmbench.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"lmbench测试出错:拉取源码失败.报错信息:{git_clone.stderr.decode('utf-8')})")
            sys.exit(1)
        # 安装rpm包
        install_rpm = subprocess.run(
            f"yum install -y libtirpc-devel {self.compiler} make -y",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if install_rpm.returncode != 0:
            print(f"lmbench测试出错:安装rpm包失败.报错信息:{install_rpm.stderr.decode('utf-8')}")
            sys.exit(1)



    def run_test(self):
        # make后直接就运行了
        make = pexpect.spawn(
            '/bin/bash',['-c',f"cd /root/osmts_tmp/lmbench && make CC={self.compiler} results"]
        )

        # 同时运行lmbench的份数
        make.expect("MULTIPLE COPIES [default 1]:",timeout=1800)
        make.sendline("1")

        # 允许作业调度
        make.expect("Job placement selection [default 1]:",timeout=1800)
        make.sendline("1")

        # 设置测试内存大小
        make.expect("MB [default",timeout=1800)
        make.sendline("4096")

        # 选择要运行的测试集
        make.expect("SUBSET (ALL|HARWARE|OS|DEVELOPMENT) [default all]:",timeout=1800)
        make.sendline("ALL")

        # 不跳过内存latency测试
        make.expect('FASTMEM [default no]:',timeout=1800)
        make.sendline("no")

        # 不跳过文件系统latency测试
        make.expect('SLOWFS [default no]:',timeout=1800)
        make.sendline("no")

        # 不测试硬盘
        make.expect('DISKS [default none]:',timeout=1800)
        make.sendline()

        # 不测试网络
        make.expect("REMOTE [default none]:",timeout=1800)
        make.sendline("")

        # 测试CPU与设定频率
        make.expect('Processor mhz',timeout=1800)
        make.sendline()

        # 设定临时目录存放测试文件
        make.expect('FSDIR [default /usr/tmp]:',timeout=1800)
        make.sendline('/usr/tmp')

        # 设置测试输出信息文件存放目录
        make.expect('Status output file [default /dev/tty]:',timeout=1800)
        make.sendline('/dev/tty')

        # 设置不发邮件
        make.expect('Mail results [default yes]:',timeout=1800)
        make.sendline('no')

        # 等待lmbench测试运行结束
        make.expect(pexpect.EOF)
        print(make.before)


        # 获取运行结果
        make_see = subprocess.run(
            "cd /root/osmts_tmp/lmbench && make see",
            shell=True,
            stdout=subprocess.DEVNULL,
            stdin=subprocess.PIPE,
        )
        if make_see.returncode != 0:
            print(f"lmbench测试:make see执行出错.报错信息:{make_see.stderr.decode('utf-8')}")
            sys.exit(1)



    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)


    def result2summary(self):
        pass


    def run(self):
        print("开始进行lmbench测试")
        self.pre_test()
        self.run_test()
        self.result2summary()
        if self.remove_osmts_tmp_dir:
            self.post_test()
        print("lmbench测试结束")