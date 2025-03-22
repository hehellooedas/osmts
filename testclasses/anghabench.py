from pathlib import Path
import sys,subprocess,shutil,os,fnmatch,time
from openpyxl import Workbook


class AnghaBench:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/AnghaBench')
        self.directory: Path = kwargs.get('saved_directory') / 'anghabench'
        self.log_files:Path = self.directory / 'log_files'
        self.passed = 0
        self.failed = 0
        self.total = 0


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True,exist_ok=True)
            self.log_files.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir(parents=True)

        # 拉取AnghaBench的源码
        git_clone = subprocess.run(
            f"cd /root/osmts_tmp/ && git clone https://gitcode.com/qq_61653333/AnghaBench.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"AnghaBench测试出错.git clone运行失败,报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'AnghaBench'

        ws.cell(1,1,"c文件名")
        ws.cell(1,2,"编译结果")
        ws.cell(1,3,"编译耗时")

        line = 2

        matches = []
        for root,dirnames,filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, '*.c'):
                matches.append((filename,os.path.join(root,filename)))
        for match in matches:
            ws.cell(line, 1, match[0])
            start_time = time.time()
            compile = subprocess.run(
                f"gcc {match[1]} -c -o {match[1]}.o",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            time_consuming = time.time() - start_time
            ws.cell(line, 3, f"{time_consuming}秒")
            if compile.returncode != 0: #编译失败
                self.failed += 1
                ws.cell(line,2,"failed")
            else:
                self.passed += 1
                ws.cell(line,2,"passed")
            self.total += 1
            with open(self.log_files / f'{match[0]}.txt','w') as log:
                log.write(compile.stdout.decode('utf-8'))
            line += 1
        ws.cell(line,1,f"总共编译文件数{self.total}")
        ws.cell(line, 2, f"通过编译数{self.passed}")
        ws.cell(line, 3, f"失败编译数{self.failed}")



    def run(self):
        print('开始进行AnghaBench测试')
        self.pre_test()
        self.run_test()
        print('AnghaBench测试结束')