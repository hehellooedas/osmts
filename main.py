#! /usr/bin/env python3
# encoding: utf-8

import sys,psutil,shutil
import tomllib,ipaddress
import subprocess,argparse
from pathlib import Path
from testclasses import osmts_tests


osmts_path = Path('/root/osmts_tmp/')
fio_status = False


def fio_judge():
    # 避免下载大文件导致系统崩溃
    if psutil.disk_usage('/').free < 20 * 1024 * 1024 * 1024:
        print("当前机器的/分区剩余容量过低,无法进行fio测试,请参考 https://github.com/openeuler-riscv/oerv-team/blob/main/cases/2024.10.19-OERV-UEFI%E5%90%AF%E5%8A%A8%E7%A3%81%E7%9B%98%E5%88%B6%E4%BD%9C-%E8%B5%B5%E9%A3%9E%E6%89%AC.md#%E9%99%84%E5%BD%95%E4%BA%8C 扩展/分区容量.")
        sys.exit(1)
    nonlocal fio_status
    fio_status = True



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
    print("友情提示:请确保指定ip机器上已经执行了netserver -p 10000命令,否则osmts会报错.")



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
    return list(tasks)



if __name__ == '__main__':
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
    saved_method = config.get("saved_method",None)
    compiler = config.get("compiler",None)
    netperf_server_ip = config.get("netperf_server_ip", None)

    if saved_directory is None:
        print("请输入本次测试结果保存的目录,检查saved_directory字段")
        sys.exit(1)
    saved_directory = Path(saved_directory)
    saved_directory.mkdir(parents=True,exist_ok=True)

    if saved_method not in ("excel","csv"):
        print("保存方式只能为excel或csv,请检查saved_method字段")
        sys.exit(1)
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
    print(f"本次osmts脚本执行将进行的测试:{tasks}")
    if not osmts_path.exists():
        osmts_path.mkdir()

    if fio_status:
        # 提前下载iso文件
        fio = osmts_tests['fio'](saved_directory=saved_directory, saved_method=saved_method)
        tasks.remove('fio')


    # 所有检查都通过,则正式开始测试
    for task in tasks:
        # 构造测试类
        osmts_tests[task](saved_directory=saved_directory,saved_method=saved_method,compiler=compiler,netperf_server_ip=netperf_server_ip).run()

    if fio_status:
        fio.run()

    # if osmts_path.exists():
    #     shutil.rmtree(osmts_path)
    print("osmts运行结束")