from pathlib import Path
import sys,subprocess,shutil


class Llvmcase():
    def __init__(self, **kwargs):
        self.rpms = {'gcc-g++', 'gcc-gfortran', 'cmake', 'ninja-build'}
        self.path = Path('/root/osmts_tmp/llvm-project')
        self.directory: Path = kwargs.get('saved_directory') / 'llvmcase'


    def pre_test(self):
        if not self.directory.exists():
            self.directory.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            shutil.rmtree(self.path)
        # 拉取源码
        git_clone = subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitcode.com/pollyduan/llvm-project.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"llvmcase测试出错.git clone执行失败,报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        # 编译llvm
        build_llvm = subprocess.run(
            f'cd {self.path} && mkdir build && cd build && cmake -DLLVM_PARALLEL_LINK_JOBS=3 -DLLVM_ENABLE_PROJECTS="clang" -DLLVM_TARGETS_TO_BUILD="RISCV" -DCMAKE_BUILD_TYPE="Release" -G Ninja ../llvm && ninja',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build_llvm.returncode != 0:
            print(f"llvmcase测试出错.编译llvm失败,报错信息:{build_llvm.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        run_clang = subprocess.run(
            "cd /root/osmts_tmp/llvm-project/build/bin && clang -v",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if run_clang.returncode != 0:
            print(f"llvmcase测试出错.clang -v运行报错,报错信息:{run_clang.stderr.decode('utf-8')}")
            print('不过osmts仍会继续运行')

        with open(self.directory / 'llvmcase.log', 'w') as file:
            file.write(run_clang.stdout.decode('utf-8'))


    def run(self):
        print('开始进行llvmcase测试')
        self.pre_test()
        self.run_test()
        print('llvm测试结束')