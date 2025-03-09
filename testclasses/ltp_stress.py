from pathlib import Path
import sys,subprocess,shutil,tarfile,signal,os,psutil,traceback
from openpyxl import Workbook


class Ltp_stress():
    def __init__(self, **kwargs):
        self.rpms = {'automake','pkgconf','autoconf','bison','flex','m4','kernel-headers','glibc-headers','findutils','libtirpc','libtirpc-devel','pkg-config','sysstat'}
        self.path = Path('/root/osmts_tmp/ltp_stress')
        self.directory: Path = kwargs.get('saved_directory')
        self.compiler: str = kwargs.get('compiler')
        self.remove_osmts_tmp_dir = kwargs.get('remove_osmts_tmp_dir')


    def pre_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)

        # 拉取源码
        git_clone = subprocess.run(
            "cd /root/osmts_tmp/ && git clone https://gitee.com/April_Zhao/ltp_stress.git",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if git_clone.returncode != 0:
            print(f"ltp_stress测试出错:git clone拉取源码失败.报错信息:{git_clone.stderr.decode('utf-8')}")
            sys.exit(1)

        # 编译
        if self.compiler == "gcc":
            build = subprocess.run(
                "cd /root/osmts_tmp/ltp_stress && make autotools && ./configure --prefix=/opt/ltp_stress && make -j $(nproc) && make install",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        elif self.compiler == "clang":
            build = subprocess.run(
                'cd /root/osmts_tmp/ltp_stress && export CFLAGS="-Wno-error=implicit-function-declaration" && make autotools && CC=clang ./configure ./configure && make -j $(nproc) && make install',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

        if build.returncode != 0:
            print(f"ltp_stress测试出错:ltp_stress源码编译不通过.报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)



    def run_test(self):
        print('ltp_stress测试需要7x24小时,期间请勿中断osmts.')
        ltpstress_sh = subprocess.Popen(
            "cd /opt/ltp_stress/testscripts && mkdir -p /opt/ltp_stress/output && ./ltpstress.sh -i 3600 -d /opt/ltp_stress/output/ltpstress.data -I /opt/ltp_stress/output/ltpstress.iodata -l /opt/ltp_stress/output/ltpstress.log -n -p -S -m 512 -t 168",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # 定义Ctrl+C信号处理函数
        def signal_handler(sig, frame):
            print('osmts检测到Ctrl+C键盘中断信号,正在终止ltp_stress压力测试...')
            try:
                # 尝试终止进程组内所有进程
                os.killpg(os.getpgid(ltpstress_sh.pid), signal.SIGTERM)
            except Exception as e:
                print(f'终止进程组失败,报错信息{e}',file=sys.stderr)

            try:
                parent = psutil.Process(ltpstress_sh.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            print(f'osmts创建的所有子进程均已终止\n当前完整堆栈信息:{traceback.print_stack(frame)}')
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        ltpstress_sh.wait()

        # /opt/ltp/output/里有运行结果
        # ltpstress.log：记录相关日志信息，主要是测试是否通过(pass or fail)
        # ltpstress.data：sar工具记录的日志文件，包括cpu,memory,i/o等
        with tarfile.open(self.directory / 'ltpstress.tar.xz','w:xz') as tar:
            tar.add('/opt/ltp_stress/output/ltpstress.data')
            tar.add('/opt/ltp_stress/output/ltpstress.iodata')
            tar.add('/opt/ltp_stress/output/ltpstress.log')
        # ---------------------------------------------------------------

        # 分析ltpstress.log文件,找到其中fail的项目并统计
        with open('/opt/ltp_stress/output/ltpstress.log','r') as ltpstress_log:
            fail_testcases = sorted(set(line.strip() for line in ltpstress_log.readlines() if 'FAIL'in line))
            wb = Workbook()
            ws = wb.active
            ws.title = 'ltp stress fail testcases'
            ws.append(['Testcase','Result','Exit Value'])
            for fail_testcase in fail_testcases:
                ws.append([item for item in fail_testcase.split(' ') if item != ''])
            wb.save(self.directory / 'fail_testcases.xlsx')

        # 分析ltpstress.iodata



    def run(self):
        print("开始进行ltp_stress测试")
        self.pre_test()
        self.run_test()
        print("ltp_stress测试结束")