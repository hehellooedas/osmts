from pathlib import Path
import sys,shutil,os,fnmatch,tarfile,subprocess
from openpyxl import Workbook
import asyncio,aiofiles



class AnghaBench:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/AnghaBench')
        self.directory: Path = kwargs.get('saved_directory') / 'anghabench'
        self.log_files:Path = self.directory / 'log_files'

        self.failed = 0
        self.total = 0

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = 'AnghaBench'

        self.ws.cell(1,1,"AnghaBench测试中编译未通过项目汇总")
        self.ws.merge_cells("A1:B1")
        self.ws.cell(2,1,"c文件名")
        self.ws.cell(2,2,"日志文件")


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


    async def match2result(self):
        while True:
            match:list = await self.queue.get()
            log_name = match[0] + '.log'
            compile = await asyncio.create_subprocess_shell(
                f"gcc {match[1]} -c -o {match[1]}.o",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            await asyncio.sleep(0.5)
            stdout, stderr = await compile.communicate()
            self.queue.task_done()

            if compile.returncode != 0:
                self.failed += 1
                if (result := stdout.decode('utf-8')) != '':
                    self.ws.append([match[0],log_name])
                    async with aiofiles.open(self.log_files / log_name, 'w') as log:
                        await log.write(result)
                else:
                    self.ws.append([match[0],"日志为空,不生成日志文件"])


    async def run_test(self):
        matches = []
        for root,dirnames,filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, '*.c'):
                matches.append((filename,os.path.join(root,filename)))
        self.total = len(matches)

        self.queue = asyncio.Queue(maxsize=os.cpu_count() * 4)
        workers = [asyncio.create_task(self.match2result()) for _ in range(os.cpu_count() * 2)]
        for match in matches:
            await self.queue.put(match)
        await self.queue.join()
        for worker in workers:
            worker.cancel()

        # 汇总结果
        self.ws.append([f"总共编译文件数{self.total}",f"通过编译数{self.total - self.failed}",f"失败编译数{self.failed}"])

        self.wb.save(self.directory / 'AnghaBench.xlsx')

        with tarfile.open(self.directory / 'AnghaBench.tar.xz',"w:xz") as tar:
            tar.add(self.log_files)


    def run(self):
        print('开始进行AnghaBench测试')
        self.pre_test()
        asyncio.run(self.run_test())
        print('AnghaBench测试结束')