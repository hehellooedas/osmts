from pathlib import Path
import sys,subprocess,shutil,os,fnmatch,time,tarfile,threading
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor


class AnghaBench:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/AnghaBench')
        self.directory: Path = kwargs.get('saved_directory') / 'anghabench'
        self.log_files:Path = self.directory / 'log_files'
        self.failed = 0
        self.total = 0
        self.lock = threading.Lock()
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = 'AnghaBench'

        self.ws.cell(1,1,"AnghaBench测试中编译未通过项目汇总")
        self.ws.merge_cells("A1:C1")
        self.ws.cell(2,1,"c文件名")
        self.ws.cell(2,2,"编译耗时")
        self.ws.cell(2,3,"日志文件")


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


    def match2result(self,match):
        start_time = time.time()
        compile = subprocess.run(
            f"gcc {match[1]} -c -o {match[1]}.o",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        # 记录编译时间
        time_consuming = time.time() - start_time
        if compile.returncode != 0:
            with self.lock:
                self.failed += 1
                if (result := compile.stdout.decode('utf-8')) != '':
                    log_name = match[0] + '.log'
                    self.ws.append([match[0],f"{time_consuming:.4f}s",log_name])
                    with open(self.log_files / log_name, 'w') as log:
                        log.write(result)
                else:
                    self.ws.append([match[0],f"{time_consuming:.4f}s","日志为空,不生成日志文件"])



    def run_test(self):
        matches = []
        for root,dirnames,filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, '*.c'):
                matches.append((filename,os.path.join(root,filename)))
        self.total = len(matches)

        with ThreadPoolExecutor() as pool:
            pool.map(self.match2result,matches)

        # 汇总结果
        self.ws.append([f"总共编译文件数{self.total}",f"通过编译数{self.total - self.failed}",f"失败编译数{self.failed}"])

        self.wb.save(self.directory / 'AnghaBench.xlsx')

        with tarfile.open(self.directory / 'AnghaBench.tar.xz',"w:xz") as tar:
            tar.add(self.log_files)


    def run(self):
        print('开始进行AnghaBench测试')
        self.pre_test()
        self.run_test()
        print('AnghaBench测试结束')