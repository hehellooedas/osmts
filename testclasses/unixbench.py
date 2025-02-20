import subprocess,fileinput,shutil,re
import sys
from pathlib import Path
from openpyxl import Workbook
from testclasses.excel2csv import excel2csv


class Unixbench:
    def __init__(self,**kwargs ):
        self.path = Path('/root/osmts_tmp/unixbench')
        self.saved_method:str = kwargs.get('saved_method')
        self.directory:Path = kwargs.get('saved_directory')
        self.compiler:str = kwargs.get('compiler')
        self.test_result = ''


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)
        install_rpm = subprocess.run(f"dnf install make {self.compiler} perl perl-CPAN -y",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if install_rpm.returncode != 0:
            print(f"unixbench测试出错:rpm包安装失败.报错信息:{install_rpm.stderr.decode()}")
            sys.exit(1)
        clone = subprocess.run("cd /root/osmts_tmp/unixbench && git clone https://gitcode.com/gh_mirrors/by/byte-unixbench.git",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if clone.returncode != 0:
            print(f"unixbench测试出错:git clone执行失败.报错信息:{clone.stderr.decode('utf-8')}")
            sys.exit(1)
        if self.compiler == 'clang':
            for line in fileinput.input('/root/osmts_tmp/unixbench/byte-unixbench/UnixBench/Makefile', inplace=True):
                if 'CC=gcc' in line:  # 仅在包含'CC=gcc'的行进行替换
                    line = line.replace('CC=gcc', 'CC=clang')
                print(line, end='') #inplace=True会把stdout重定向到文件中
        make = subprocess.run("cd /root/osmts_tmp/unixbench/byte-unixbench/UnixBench && make",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if make.returncode != 0:
            print(f"unixbench测试出错:make执行失败.报错信息:{make.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        run = subprocess.run("cd /root/osmts_tmp/unixbench/byte-unixbench/UnixBench/ && ./Run -c 1 -c $(nproc)",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if run.returncode != 0:
            print(f"unixbench测试出错:Run程序运行失败.报错信息:{run.stderr.decode('utf-8')}")
            sys.exit(1)
        self.test_result = run.stdout.decode('utf-8')


    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True, exist_ok=True)

    def result2summary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "unixbench"
        ws['a1'] = "unixbench"
        ws['b1'] = "测试项目"
        ws['c1'] = "数据"

        ws['a2'] = "64 CPUs & 1 parallel"
        ws['a15'] = "64 CPUs & 64 parallel"
        ws.merge_cells("a2:a13")
        ws.merge_cells("a15:a26")

        ws['b2'] = ws['b15'] = "Dhrystone 2 using register variables(lps)"
        ws['b3'] = ws['b16'] = "Double-Precision Whetstone(MWIPS)"
        ws['b4'] = ws['b17'] = "Execl Throughput(lps)"
        ws['b5'] = ws['b18'] = "File Copy 1024 bufsize 2000 maxblocks(KBps)"
        ws['b6'] = ws['b19'] = "File Copy 256 bufsize 500 maxblocks(KBps)"
        ws['b7'] = ws['b20'] = "File Copy 4096 bufsize 8000 maxblocks(KBps)"
        ws['b8'] = ws['b21'] = "Pipe Throughput(lps)"
        ws['b9'] = ws['b22'] = "Pipe-based Context Switching(lps)"
        ws['b10'] = ws['b23'] = "Process Creation(lps)"
        ws['b11'] = ws['b24'] = "Shell Scripts (1 concurrent)(lpm)"
        ws['b12'] = ws['b25'] = "Shell Scripts (8 concurrent)(lpm)"
        ws['b13'] = ws['b26'] = "System Call Overhead(lps)"

        match_list = [
            re.compile(r"Dhrystone 2 using register variables\s+([\d.]+\d)\slps"),
            re.compile(r"Double-Precision Whetstone\s+([\d.]+\d)\sMWIPS"),
            re.compile(r"Execl Throughput\s+([\d.]+\d)\slps"),
            re.compile(r"File Copy 1024 bufsize 2000 maxblocks\s+([\d.]+\d)\sKBps"),
            re.compile(r"File Copy 256 bufsize 500 maxblocks\s+([\d.]+\d)\sKBps"),
            re.compile(r"File Copy 4096 bufsize 8000 maxblocks\s+([\d.]+\d)\sKBps"),
            re.compile(r"Pipe Throughput\s+([\d.]+\d)\slps"),
            re.compile(r"Pipe-based Context Switching\s+([\d.]+\d)\slps"),
            re.compile(r"Process Creation\s+([\d.]+\d)\slps"),
            re.compile(r"Shell Scripts \(1 concurrent\)\s+([\d.]+\d)\slpm"),
            re.compile(r"Shell Scripts \(8 concurrent\)\s+([\d.]+\d)\slpm"),
            re.compile(r"System Call Overhead\s+([\d.]+\d)\slps"),
        ]
        line = 2
        for one in match_list:
            match_result = one.findall(self.test_result)
            ws[f'c{line}'] = match_result[0]
            ws[f'c{line + 13}'] = match_result[1]
            line += 1

        if self.saved_method == "excel":
            wb.save(self.directory / 'unixbench.xlsx')
        elif self.saved_method == "csv":
            excel2csv(ws, self.directory)


    def run(self):
        print("开始进行unixbench测试")
        self.pre_test()
        self.run_test()
        self.post_test()
        self.result2summary()
        print("unixbench测试结束")