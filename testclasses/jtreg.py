import shutil
import subprocess
import sys
import tarfile
import requests
from pathlib import Path
from io import BytesIO
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


"""
使用 Jtreg 对 OpenJDK 执行测试回归测试
分别要测试OpenJDK 8,11,17
"""

headers = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0',
    'Referer': 'https://gitee.com/April_Zhao/osmts'
}


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
        self.rpms = { 'subversion','screen','samba','samba-client','gdb','automake','lrzsz','expect','libX11*','libxt*','libXtst*','libXt*','libXrender*','cache*','cups*','freetype*','mercurial','numactl','vim','tar','dejavu-fonts','unix2dos','dos2unix','bc','lsof','net-tool'}
        self.path = Path('/root/osmts_tmp/jtreg')
        self.directory: Path = kwargs.get('saved_directory') / 'jtreg'


    def get_tar(self,package_name):
        response = requests.get(
            url=f"https://gitee.com/April_Zhao/osmts/releases/download/v1.0/{package_name}.tar.xz",
            headers=headers
        )
        response.raise_for_status()
        with tarfile.open(fileobj=BytesIO(response.content), mode="r:xz") as tar:
            tar.extractall(path=self.path)


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)

        # 获取tar包
        with ThreadPoolExecutor(max_workers=4) as pool:
            pool.map(self.get_tar, ('jtreg','OpenJDK8-test','OpenJDK11-test','OpenJDK17-test'))
        sys.exit(1)


    def run_test(self):
        # OpenJDK8 测试
        print('  开始进行OpenJDK 8测试')
        install_rpm('java-1.8.0-openjdk*')
        jtreg = subprocess.run(
            "export JT_HOME=",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        remove_rpm('java-1.8.0-openjdk*')
        print('  OpenJDK 8测试结束')


        # OpenJDK11 测试
        print('  开始进行OpenJDK 11测试')
        install_rpm('java-11-openjdk*')

        remove_rpm('java-11-openjdk*')
        print('  OpenJDK 11测试结束')


        # OpenJDK17 测试
        print('  开始进行OpenJDK 17测试')
        install_rpm('java-17-openjdk*')
        
        remove_rpm('java-17-openjdk*')
        print('  OpenJDK 17测试结束')


    def run(self):
        print('开始进行jtreg测试')
        self.pre_test()
        self.run_test()
        print('jtreg测试结束')