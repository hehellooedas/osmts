#! /usr/bin/env python3
# encoding: utf-8

import multiprocessing
import sys,psutil,shutil,time
import tomllib,ipaddress
import subprocess,argparse,random,humanfriendly
from pathlib import Path
from testclasses import osmts_tests


osmts_tmp_dir = Path('/root/osmts_tmp/')
fio_flag = False
ltp_stress_flag = False
netserver_created_by_osmts = False


def fio_judge():
    # 避免下载大文件导致系统崩溃
    if psutil.disk_usage('/').free < 20 * 1024 * 1024 * 1024:
        print("当前机器的/分区剩余容量过低,无法进行fio测试,请参考 https://github.com/openeuler-riscv/oerv-team/blob/main/cases/2024.10.19-OERV-UEFI%E5%90%AF%E5%8A%A8%E7%A3%81%E7%9B%98%E5%88%B6%E4%BD%9C-%E8%B5%B5%E9%A3%9E%E6%89%AC.md#%E9%99%84%E5%BD%95%E4%BA%8C 扩展/分区容量.")
        sys.exit(1)
    global fio_flag
    fio_flag = True



def netperf_judge():
    # netperf需要server支持
    if netperf_server_ip is None:
        print(f"用户选择测试netperf,但输入的服务端ip有误,请检查netperf_server_ip字段.")
        sys.exit(1)
    try:
        ipaddress.IPv4Address(netperf_server_ip)
    except ipaddress.AddressValueError:
        print(f"输入的netperf服务端ip不符合ipv4规范,请检查netperf_server_ip字段.")
        sys.exit(1)
    if netperf_server_ip in ('127.0.0.1', 'localhost'):
        if 'netserver' not in [process.name() for process in tuple(psutil.process_iter())]:
            choice = input("未检测到netserver,是否在本机启动netserver?(Y/n) [netperf测试结束后会自动关闭netserver] ")
            if choice == 'Y' or choice == 'y':
                install_netperf = subprocess.run(
                    "dnf install netperf -y",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                if install_netperf.returncode != 0:
                    print(f"netperf测试出错:rpm包安装失败.报错信息:{install_netperf.stderr.decode('utf-8')}")
                    sys.exit(1)
                subprocess.run(
                    "netserver -p 10000",
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                global netserver_created_by_osmts
                netserver_created_by_osmts = True
        else:
            print("请手动执行netserver -p 10000以进行netperf的测试")
            sys.exit(1)



def from_tests_to_tasks(run_tests:list) -> list:
    support_tests = list(osmts_tests.keys())
    tasks = set()
    if "performance-test" in run_tests:
        tasks |= {"fio", "stream", "iozone", "unixbench", "libmicro", "nmap", "lmbench", "netperf","ltp_stress"}
        run_tests.remove("performance-test")
    for run_test in run_tests:
        if run_test not in support_tests:
            print(f"osmts当前支持的测试项目:{support_tests}")
            print(f"run_tests中出现了不在osmts支持列表里的测试项目:{run_test},请检查配置文件.")
            sys.exit(1)
        tasks.add(run_test)

    if 'netperf' in tasks:
        netperf_judge()
    if 'fio' in tasks:
        fio_judge()
    tasks = list(tasks)
    random.shuffle(tasks)
    return tasks



if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser(description="get the config file name for osmts.")
    parser.add_argument("--config","-c",type=str,default="osmts_config.toml")
    osmts_config_file = parser.parse_args().config
    try:
        config = tomllib.loads(open(osmts_config_file).read())
    except FileNotFoundError:
        print(f"您指定的文件{osmts_config_file}不存在,请检查文件或目录名是否正确")
        sys.exit(1)

    if config == {}:
        print("您指定的配置文件是空的,请检查输入的toml格式文件")
        sys.exit(1)
    run_tests = config.get("run_tests",None)
    saved_directory = config.get("saved_directory",None)
    compiler = config.get("compiler",None)
    netperf_server_ip = config.get("netperf_server_ip", None)
    remove_osmts_tmp_dir = bool(config.get("remove_osmts_tmp_dir", None))
    merge = bool(config.get("merge", None))


    if saved_directory is None:
        saved_directory = '/root/osmts_result/'
    elif saved_directory in ('/','/etc','/dev','proc','/boot'):
        print(f"{saved_directory}为系统关键目录,不建议把结果存放在该路径")
        choice = input("是否使用osmts推荐的路径?(Y/n)")
        if choice == 'N' or choice == 'n':
            print('本次测试退出.')
            sys.exit(1)
        print("已设定存放结果的目录为/root/osmts_result")
        saved_directory = '/root/osmts_result/'
    saved_directory = Path(saved_directory)
    saved_directory.mkdir(parents=True,exist_ok=True)

    if compiler not in ("gcc","clang"):
        print("编译器必为gcc或者clang之一,否则默认为gcc,请检查compiler字段")
        continue_test = input("是否继续测试?(y/N)")
        if continue_test in ("y","Y"):
            compiler = "gcc"
        else:
            sys.exit(1)

    if run_tests is None:
        print(f"您指定的配置文件{osmts_config_file}中的字段run_tests为空,请检查输入的toml文件")
        sys.exit(1)

    #安装必备的rpm包
    install_git = subprocess.run("dnf install git make -y",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    if install_git.returncode != 0:
        print(f"安装git失败,请检查.报错信息:{install_git.stderr.decode('utf-8')}")
        sys.exit(1)

    tasks = from_tests_to_tasks(run_tests)
    print(f"本次osmts脚本执行将进行的测试:{tasks},运行时请勿删除{osmts_tmp_dir}和{saved_directory}")
    if not osmts_tmp_dir.exists():
        osmts_tmp_dir.mkdir()

    if fio_flag:
        # 提前下载iso文件
        fio = osmts_tests['fio'](saved_directory=saved_directory)
        tasks.remove('fio')

    # ltp stress独立测试
    if 'ltp_stress' in tasks:
        tasks.remove('ltp_stress')
        ltp_stress_flag = True
        ltp_stress:multiprocessing.Process = osmts_tests['ltp_stress'](
            saved_directory=saved_directory,
            compiler=compiler,
            netperf_server_ip=netperf_server_ip
        )
        ltp_stress.daemon = True
        ltp_stress.start()


    # 所有检查都通过,则正式开始测试
    for task in tasks:
        # 构造测试类
        osmts_tests[task](saved_directory=saved_directory,compiler=compiler,netperf_server_ip=netperf_server_ip,netserver_created_by_osmts=netserver_created_by_osmts,remove_osmts_tmp_dir=remove_osmts_tmp_dir,merge=merge).run()


    if fio_flag:
        fio.run()

    if ltp_stress_flag:
        print("osmts等待ltp_stress测试的7x24小时压力测试的结束...|如果osmts被信号强制退出,则ltp_stress测试也会停止.")
        ltp_stress.join()

    if remove_osmts_tmp_dir and osmts_tmp_dir.exists():
        shutil.rmtree(osmts_tmp_dir)

    print(f"osmts运行结束,本次运行总耗时{humanfriendly.format_timespan(time.time() - start_time)}")