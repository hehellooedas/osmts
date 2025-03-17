from pathlib import Path
import sys,subprocess,shutil,subprocess



class AnghaBench:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/AnghaBench')
        self.directory: Path = kwargs.get('saved_directory') / 'anghabench'
        self.passed = 0
        self.failed = 0
        self.total = 0


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True,exist_ok=True)
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
            print(f'AnghaBench测试出错.git clone运行失败,报错信息:{git_clone.stderr.decode('utf-8')}')
            sys.exit(1)




    def run_test(self):
        pass


    def run(self):
        print('开始进行AnghaBench测试')
        self.pre_test()
        self.run_test()
        print('AnghaBench测试结束')