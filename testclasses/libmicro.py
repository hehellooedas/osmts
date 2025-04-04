from pathlib import Path
import sys,subprocess,shutil



class Libmicro:
    def __init__(self, **kwargs):
        self.rpms = set()
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/libmicro')
        self.directory: Path = kwargs.get('saved_directory') / 'libmicro'
        self.compiler: str = kwargs.get('compiler')
        self.test_result = ''


    def pre_test(self):
        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path, ignore_errors=True)
            # 获取源码
            git_clone = subprocess.run("cd /root/osmts_tmp/ && git clone https://gitee.com/April_Zhao/libmicro.git",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            if git_clone.returncode != 0:
                print(f"libmicro测试出错:拉取libmicro源码错误.报错信息:{git_clone.stderr.decode('utf-8')}")
                sys.exit(1)

        # 开始编译
        if self.compiler == "gcc":
            make = subprocess.run("cd /root/osmts_tmp/libmicro && make",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        elif self.compiler == "clang":
            make = subprocess.run('cd /root/osmts_tmp/libmicro && make CC=clang CFLAGS="-Wno-error=implicit-function-declaration"',shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if make.returncode != 0:
            print(f"libmicro测试出错:make编译报错.报错信息:{make.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        bench = subprocess.run(
            "cd /root/osmts_tmp/libmicro && ./bench",
                   shell=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE
        )
        if bench.returncode != 0:
            print(f"libmicro测试出错:bench命令运行失败.报错信息:{bench.stderr.decode('utf-8')}")
            sys.exit(1)
        self.test_result = bench.stdout.decode('utf-8')
        if not self.directory.exists():
            self.directory.mkdir(exist_ok=True,parents=True)
        with open(self.directory / 'libmicro.log','w') as file:
            file.write(self.test_result)


    def result2summary(self):
        pass


    def run(self):
        print("开始进行libmicro测试")
        self.pre_test()
        self.run_test()
        self.result2summary()
        print("libmicro测试结束")