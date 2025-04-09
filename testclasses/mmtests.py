import os
from pathlib import Path
import sys,subprocess,shutil
import tarfile,requests
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


headers = {
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
}

MMTESTS_CONFIGS = (
'config-buildtest-hpc-blas',
'config-buildtest-hpc-cmake',
'config-buildtest-hpc-fftw',
'config-buildtest-hpc-gmp',
'config-buildtest-hpc-metis',
'config-buildtest-hpc-mpfr',
'config-buildtest-hpc-revocap',
'config-db-sqlite-insert-small',
'config-example-tuning-sysctl',
'config-functional-ltp-containers',
'config-hpc-graph500-omp-infant',
'config-hpc-scimarkc-small',
'config-io-dbench4-async',
'config-io-fio-randread-sync-heavywrite',
'config-io-fio-randread-sync-randwrite',
'config-io-fio-scaling',
'config-io-fio-ssd',
'config-io-sparsetruncate-small',
'config-io-trunc',
'config-memdb-redis-benchmark',
'config-multi-tbench__netperf-tcp-rr',
'config-network-iperf-s14-r10000-tcp-unbound',
'config-network-netperf-cross-socket',
'config-network-netperf-rr-unbound',
'config-network-netperf-unix-unbound',
'config-network-netpipe',
'config-network-obsolete-netperf-rr-cstate',
'config-network-obsolete-netperf-unbound',
'config-pagereclaim-stutter',
'config-scheduler-adrestia-single-unbound',
'config-scheduler-lat_proc',
'config-scheduler-saladfork',
'config-scheduler-sysbench-cpu',
'config-scheduler-sysbench-mutex',
'config-scheduler-sysbench-thread',
'config-workload-aim9-pagealloc',
'config-workload-ebizzy',
'config-workload-freqmine',
'config-workload-poundsyscall',
'config-workload-spinplace-long',
'config-workload-spinplace-short',
'config-multi-tbench__netperf-tcp-rr',
'config-workload-stream-omp-llcs',
'config-workload-stream-omp-nodes',
'config-workload-stream-single',
'config-workload-stressng-class-io-parallel',
'config-workload-stressng-context',
'config-workload-stressng-get',
'config-workload-stressng-mmap',
'config-workload-thotdata',
'config-workload-thpscale',
'config-workload-thpscale-madvhugepage',
'config-workload-unixbench',
'config-workload-unixbenchd-syscall-context1',
'config-workload-unixbenchd-syscall-getpid',
'config-workload-unixbench-io-fsbuffer',
'config-workload-unixbench-io-fsdisk',
'config-workload-unixbench-io-fstime',
'config-workload-usemem',
'config-workload-will-it-scale-io-processes',
'config-workload-will-it-scale-io-threads',
'config-workload-will-it-scale-pf-processes',
'config-workload-will-it-scale-sys-processes',
#longtime
'config-db-pgbench-timed-ro-scale1',
'config-functional-ltp-cve',
'config-functional-ltp-lite',
'config-functional-ltp-mm',
'config-functional-ltp-netstress',
'config-functional-ltp-realtime',
'config-io-blogbench',
'config-io-fio-randread-direct-multi',
'config-io-fio-sync-maxrandwrite',
'config-io-paralleldd-read-small',
'config-io-pgioperf',
'config-io-xfsio',
'config-ipc-scale-short',
'config-network-netperf-cross-node',
'config-network-netperf-cstate',
'config-network-netperf-rr-cstate',
'config-network-netperf-stream-unbound',
'config-network-netperf-unbound',
'config-network-obsolete-netperf-cross-node',
'config-network-obsolete-netperf-cross-socket',
'config-network-obsolete-netperf-cstate',
'config-workload-coremark',
'config-workload-futexbench',
'config-workload-pft-process',
'config-workload-pft-threads',
'config-workload-sembench-futex',
'config-workload-shellscripts',
'config-workload-stockfish',
'config-workload-usemem-stress-numa-compact',
#long long time
'config-network-sockperf-unbound',
'config-scheduler-adrestia-periodic-unbound',
'config-workload-johnripper',
'config-workload-usemem-swap-ramdisk',
'config-workload-wp-tlbflush',
'config-workload-will-it-scale-pf-threads',
'config-workload-will-it-scale-sys-threads',
'config-monitor',
)


class MMTests:
    def __init__(self, **kwargs):
        self.rpms = {
            'expect','expect-devel','pcre-devel','bzip2-devel','xz-devel','libcurl-devel',
            'libcurl','texinfo','gcc-gfortran','java-1.8.0-openjdk-devel',
            'wget','libXt-devel','readline-devel','glibc-headers','gcc-c++',
            'zlib','zlib-devel','bc','httpd','net-tools','m4','flex','bison',
            'byacc','keyutils-libs-devel','lksctp-tools-devel','xfsprogs-devel',
            'libacl-devel','openssl','openssl-devel','numactl-devel','libaio-devel',
            'glibc-devel','libcap-devel','patch','findutils','libtirpc','libtirpc-devel',
            'kernel-headers','glibc-headers','hwloc-devel','numactl','automake','fio',
            'sysstat','time','psmisc','popt-devel','libstdc++','libstdc++-static',
            'elfutils-libelf-devel','slang-devel','libbabeltrace-devel','zstd-devel',
            'gtk2-devel','systemtap','libtool','rpcgen','vim','autoconf','automake',
            'python3-rpm-macros','binutils-devel','coreutils','kernel-tools','e2fsprogs',
            'gawk','hdparm','hostname','iproute','nmap','perl-File-Slurp','perl-Time-HiRes',
            'tcl','util-linux','xfsprogs','btrfs-progs','numad','tuned','perl-Try-Tiny',
            'perl-JSON','perl-GD','perl-List-BinarySearch','perl-Math-Gradient','R'
        }
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/mmtests')
        self.directory: Path = kwargs.get('saved_directory') / 'mmtests'
        self.logs:Path = self.directory / 'logs'

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = 'MMTests'
        self.ws.append(['config','返回值'])



    # 下载/编译/安装R包
    def prepare_R(self):
        R_Dir = Path('/usr/local/R')
        R_Src_Path,R_Dst_Path = R_Dir / 'bin/R',Path('/usr/bin/R')
        Rscript_Src_Path,Rscript_Dst_Path = R_Dir / 'bin/Rscript',Path('/usr/bin/Rscript')

        if self.believe_tmp:
            if R_Dir.exists():
                return
        else:
            if R_Dir.exists():
                shutil.rmtree(R_Dir)
            if R_Dst_Path.exists():
                shutil.rmtree(R_Dst_Path)
            if Rscript_Dst_Path.exists():
                shutil.rmtree(Rscript_Dst_Path)
        R_Dir.mkdir(parents=True)
        response = requests.get(
            url="https://mirror.lzu.edu.cn/CRAN/src/base/R-4/R-4.4.0.tar.gz",
            headers=headers,
            stream=True
        )
        response.raise_for_status()
        with tarfile.open(fileobj=response.raw, mode="r:gz") as tar:
            tar.extractall('/opt/')
        build = subprocess.run(
            f"cd /opt/R-4.4.0 && "
            f"./configure --enable-R-shlib=yes --with-tcltk --prefix={R_Dir} && "
            f"make -j {os.cpu_count()} && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"mmtests测试出错.R-4.4.0构建失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)
        # 创建软链接
        shutil.copyfile(R_Src_Path,R_Dst_Path,follow_symlinks=True)
        shutil.copyfile(Rscript_Src_Path,Rscript_Dst_Path)



    # 下载/编译/安装List-BinarySearch
    def prepare_L(self):
        response = requests.get(
            url="https://gitee.com/April_Zhao/osmts/releases/download/v1.0/List-BinarySearch.tar.xz",
            headers=headers,
            stream=True
        )
        with tarfile.open(fileobj=response.raw, mode="r:xz") as tar:
            tar.extractall('/opt/')
        build = subprocess.run(
            f"cd /opt/List-BinarySearch && "
            f"echo y|perl Makefile.PL && make && make test && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"mmtests测试出错.List-BinarySearch构建失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)



    # 下载/编译/安装File-Slurp
    def prepare_F(self):
        response = requests.get(
            url="https://cpan.metacpan.org/authors/id/C/CA/CAPOEIRAB/File-Slurp-9999.32.tar.gz",
            headers=headers,
            stream=True
        )
        response.raise_for_status()
        with tarfile.open(fileobj=response.raw, mode="r:gz") as tar:
            tar.extractall('/opt/')
        build = subprocess.run(
            f"cd /opt/File-Slurp-9999.32 && "
            f"perl Makefile.PL -y && "
            f"make -j {os.cpu_count()} && make test && make install",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if build.returncode != 0:
            print(f"mmtests测试出错.File-Slurp构建失败,报错信息:{build.stderr.decode('utf-8')}")
            sys.exit(1)


    # 准备mmtests
    def prepare_M(self):
        # 获取mmtests的源码
        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path, ignore_errors=True)
            git_clone =  subprocess.run(
                "cd /root/osmts_tmp/ && git clone https://gitcode.com/gh_mirrors/mm/mmtests.git",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if git_clone.returncode != 0:
                print(f"MMTtests测试出错.git clone运行失败,报错信息:{git_clone.stderr.decode('utf-8')}")
                sys.exit(1)


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        self.logs.mkdir(parents=True)

        with ThreadPoolExecutor(max_workers=4) as pool:
            #pool.submit(self.prepare_R)
            pool.submit(self.prepare_L)
            pool.submit(self.prepare_F)
            pool.submit(self.prepare_M)


    def mmtests_each_test(self,config):
        run_mmtests = subprocess.run(
            f"cd /root/osmts_tmp/mmtests && ./run-mmtests.sh --no-monitor "
            f"--config configs/{config} {config}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        with open(self.logs / f"{config}.log", "w") as log:
            log.write(run_mmtests.stdout.decode('utf-8'))
        return (config,run_mmtests.returncode)


    def run_test(self):
        with ThreadPoolExecutor() as pool:
            results = list(tqdm(pool.map(self.mmtests_each_test,MMTESTS_CONFIGS),total=len(MMTESTS_CONFIGS)))
            for result in results:
                self.ws.append(result)
        self.wb.save(self.directory / 'mmtests.xlsx')


    def run(self):
        print("开始进行MMTests测试")
        self.pre_test()
        self.run_test()
        print("MMTests测试结束")
