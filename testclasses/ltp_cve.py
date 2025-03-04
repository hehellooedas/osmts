from pathlib import Path
import sys,subprocess

"""
ltp cve测试在ltp测试的基础上运行
"""

class Ltp_cve:
    def __init__(self, **kwargs):
        self.path = Path('/root/osmts_tmp/ltp_cve')
        self.directory: Path = kwargs.get('saved_directory')
        self.remove_osmts_tmp_dir:bool = kwargs.get('remove_osmts_tmp_dir')
        self.test_result = ''


    def run_test(self):
        runltp = subprocess.run(
            "cd /opt/ltp && ./runltp -f cve",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if runltp.returncode != 0:
            print(f"ltp_cve测试出错.runltp进程报错:报错信息:{runltp.stderr.decode('utf-8')}")
            sys.exit(1)
        self.test_result = runltp.stdout.decode('utf-8')
        print(self.test_result)


    def run(self):
        print("开始进行ltp_cve测试")
        self.run_test()
        print("ltp_cve测试结束")