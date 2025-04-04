import re
import shutil
import subprocess
import sys
from pathlib import Path
from openpyxl import Workbook


class SecureGuardian:
    def __init__(self, **kwargs):
        self.rpms = {'jq'}
        self.path = kwargs.get('/root/osmts_tmp/secureguardian')
        self.directory: Path = kwargs.get('saved_directory') / 'secureguardian'
        self.test_result = ''


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        install_secureguardian = subprocess.run(
            "dnf install -y https://eulermaker.compass-ci.openeuler.openatom.cn/api/ems5/repositories/openEuler-24.09:epol/openEuler:24.09/x86_64/history/223fa6b8-65fc-11ef-9cf1-324c421ef8df/steps/upload/cbs.6161130/secureguardian-1.0.0-1.oe2409.noarch.rpm",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if install_secureguardian.returncode != 0:
            print(f"secureguardian测试出错.安装rpm包失败,报错信息:{install_secureguardian.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        run_checks = subprocess.run(
            "run_checks",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if run_checks.returncode != 0:
            print(f"secureguardian测试出错.run_checks命令运行失败,报错信息:{run_checks.stderr.decode('utf-8')}")
            return
        self.test_result = run_checks.stdout.decode('utf-8')
        shutil.copy2("/usr/local/secureguardian/reports/all_checks.results.html", self.directory)
        shutil.copy2("/usr/local/secureguardian/reports/all_checks.results.json", self.directory)


    def result2summary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'secureguardian'

        for version,status in re.findall(r"检查 (\d+\.\d+\.\d+) 执行完成：(成功|失败)", self.test_result):
            ws.append([version,status])


    def run(self):
        print('开始进行secureguardian测试')
        self.pre_test()
        self.run_test()
        self.result2summary()
        print('secureguardian测试结束')