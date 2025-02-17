#! /usr/bin/env python3
# encoding: utf-8

import sys
import tomllib,ipaddress
import subprocess,argparse
from pathlib import Path
from testclasses import osmts_tests


def from_tests_to_tasks(run_tests:list) -> set:
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

    # netperf需要server支持
    if "netperf" in tasks:
        if netperf_server_ip is None:
            print(f"用户选择测试netperf,但输入的服务端ip有误,请检查netperf_server_ip字段.")
            sys.exit(1)
        try:
            ipaddress.IPv4Address(netperf_server_ip)
        except ipaddress.AddressValueError:
            print(f"输入的netperf服务端ip不符合ipv4规范,请检查netperf_server_ip字段.")
            sys.exit(1)
        print("友情提示:请确保指定ip机器上已经执行了netserver -p 10000命令,否则osmts会报错.")
    return tasks



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

    # 所有检查都通过,则正式开始测试
    for task in tasks:
        # 构造测试类
        osmts_tests[task](saved_directory=saved_directory,saved_method=saved_method,compiler=compiler,netperf_server_ip=netperf_server_ip).run()

    print("osmts运行结束")