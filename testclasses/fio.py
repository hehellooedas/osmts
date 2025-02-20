from pathlib import Path
import sys,subprocess,shutil,time,requests
from multiprocessing import Process
from openpyxl.workbook import Workbook




class Fio:
    def __init__(self, **kwargs):
        self.path = Path('/root/osmts_tmp/fio')
        self.saved_method: str = kwargs.get('saved_method')
        self.directory: Path = kwargs.get('saved_directory')
        self.download_iso_process:Process = Process(target=self.download_iso_file,daemon=True)
        self.download_iso_process.start()



    def download_iso_file(self):
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir()
        with requests.get(
                'https://repo.openeuler.org/openEuler-preview/openEuler-24.03-LLVM-Preview/ISO/riscv64/openEuler-24.03-LLVM-riscv64-dvd.iso',
                stream=True
        ) as response:
            response.raise_for_status()
            with open(self.path / 'openEuler-24.03-LLVM-riscv64-dvd.iso', 'wb') as file:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        file.write(chunk)



    def pre_test(self):
        install_fio = subprocess.run("dnf install fio -y", shell=True, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.PIPE)
        if install_fio.returncode != 0:
            print(f"fio运行出错:fio包安装失败.报错信息:{install_fio.stderr.decode('utf-8')}")
            sys.exit(1)



    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "fio"

        self.download_iso_process.join()
        filename = "/root/osmts_tmp/fio/openEuler-24.03-LLVM-riscv64-dvd.iso"
        numjobs = 10
        iodepth = 10
        for rw in ("read","write","rw","randread","randwrite","randrw"):
            for bs in (4,16,32,64,128,256,512,1024):
                if rw == "randrw" or rw == "rw":
                    fio = subprocess.run(f"fio -filename={filename} -direct=1 -iodepth {iodepth} -thread -rw={rw} -rwmixread=70 -ioengine=libaio -bs={bs}k -size=1G -numjobs={numjobs} -runtime=30 -group_reporting -name={rw}-{bs}k",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                else:
                    fio = subprocess.run(f"fio -filename={filename} -direct=1 -iodepth {iodepth} -thread -rw={rw} -ioengine=libaio -bs={bs}k -size=1G -numjobs={numjobs} -runtime=30 -group_reporting -name={rw}-{bs}k",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                if fio.returncode != 0:
                    print(f"fio测试出错:fio进程运行报错,此时rw为{rw}.报错信息:{fio.stderr.decode('utf-8')}")
                    sys.exit(1)
                print('此时fio开始输出')
                print(fio.stdout.decode('utf-8'))
                print('---------------------------------------------------------------')
                time.sleep(3)



    def post_test(self):
        if self.path.exists():
            shutil.rmtree(self.path)



    def run(self):
        print("开始进行fio测试")
        self.pre_test()
        self.run_test()
        self.post_test()
        print("fio测试结束")