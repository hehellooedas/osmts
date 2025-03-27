import shutil
import subprocess
import sys,os,tarfile
from pathlib import Path
from openpyxl import Workbook


"""
使用 Jtreg 对 OpenJDK 执行测试回归测试
分别要测试OpenJDK 8,11,17
"""

def install_rpm(package_name):
    subprocess.run(
        f"dnf install -y {package_name}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def remove_rpm(package_name):
    subprocess.run(
        f"dnf remove -y {package_name}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class Jtreg:
    def __init__(self, **kwargs):
        self.rpms = { 'subversion','screen','samba','samba-client','gdb','automake','lrzsz','expect','libX11*','libxt*','libXtst*','libXt*','libXrender*','cache*' 'cups*','freetype*','mercurial','numactl','vim','tar','dejavu-fonts','unix2dos','dos2unix','bc','lsof','net-tool'}
        self.path = Path('/root/osmts_tmp/jtreg')
        self.directory: Path = kwargs.get('saved_directory') / 'jtreg'


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)

    
    def run_test(self):
        # OpenJDK8 测试
        print('开始进行OpenJDK 8测试')
        install_rpm('java-1.8.0-openjdk*')

        remove_rpm('java-1.8.0-openjdk*')
        print('OpenJDK 8测试结束')


        # OpenJDK11 测试
        print('开始进行OpenJDK 11测试')
        install_rpm('java-11-openjdk*')

        remove_rpm('java-11-openjdk*')
        print('OpenJDK 11测试结束')


        # OpenJDK17 测试
        print('开始进行OpenJDK 17测试')
        install_rpm('java-17-openjdk*')
        
        remove_rpm('java-17-openjdk*')
        print('OpenJDK 17测试结束')


    def run(self):
        self.pre_test()
        self.run_test()