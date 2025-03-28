import shutil
import subprocess
import sys,os
import asyncio
from pathlib import Path
from openpyxl import Workbook


max_workers = asyncio.Semaphore(os.cpu_count() * 100) # 限制并发度


async def rpm_check_each(package_name):
    async with max_workers:
        rpm_check = await asyncio.create_subprocess_shell(
            f"rpm -K /root/osmts_tmp/gpgcheck/{package_name}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(1.5)
        _,stderr = await rpm_check.communicate()
        if rpm_check.returncode != 0:
            return True,package_name, stderr.decode('utf-8')
        else:
            return False,None,None



class GpgCheck:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/gpgcheck')
        self.directory: Path = kwargs.get('saved_directory') / 'gpgcheck'
        self.packages = []

        # 创建Excel表格
        self.wb = Workbook()
        self.ws = self.wb.active


    async def rpm_check_all(self):
        # 对每个rpm包创建一个测试任务
        tasks = [asyncio.create_task(rpm_check_each(package)) for package in self.packages]
        futures = await asyncio.gather(*tasks)
        for future in futures:
            failed, package_name, error_log = future
            if failed:
                self.ws.append([package_name, error_log])


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir()
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)

        # 更新缓存以便后面下载
        subprocess.run(
            "dnf clean all && dnf makecache",
            shell=True,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        )

        # 引入openEuler的gpg验证密钥
        import_gpg_key = subprocess.run(
            "rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-openEuler",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if import_gpg_key.returncode != 0:
            print(f"gpgcheck测试出错.import gpg文件失败,报错信息:{import_gpg_key.stderr.decode('utf-8')}")
            sys.exit(1)

        # 获取已安装的所有rpm包名
        dnf_list = subprocess.run(
            "dnf list available | awk '/Available Packages/{flag=1; next} flag' | awk '{print $1}'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if dnf_list.returncode != 0:
            print(f"gpgcheck测试出错.获取所有已安装的rpm包名失败,报错信息:{dnf_list.stderr.decode('utf-8')}")
            sys.exit(1)
        self.rpm_package_list = dnf_list.stdout.decode('utf-8').splitlines()

        self.ws.title = 'gpgcheck'
        self.ws.cell(1,1,f"当前系统已安装rpm包的数量:{len(self.rpm_package_list)}")
        self.ws.merge_cells('A1:B1')
        self.ws.cell(2,1,"gpgcheck失败的rpm包统计")
        self.ws.merge_cells('A2:B2')
        self.ws.cell(3,1,"package name")
        self.ws.cell(3,2,"报错日志")


    def run_test(self):
        # 排除掉不符合测试要求的包名
        for package in self.rpm_package_list:
            if package.endswith('.src') or 'debug' in package:
                continue
            else:
                self.packages.append(package)

        # 根据包名一次性下载所有需要测试的rpm包
        rpm_download = subprocess.run(
            f"dnf download {self.packages} --destdir={self.path}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if rpm_download.returncode != 0:
            print(f"gpgcheck测试出错.下载所有待测的rpm包失败,报错信息:{rpm_download.stderr.decode('utf-8')}")
            sys.exit(1)

        asyncio.run(self.rpm_check_all())
        self.wb.save(self.directory / 'gpgcheck.xlsx')


    def run(self):
        print('开始进行gpgcheck测试')
        self.pre_test()
        self.run_test()
        print('gpgcheck测试结束')