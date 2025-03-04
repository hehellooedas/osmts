# osmts means "One-stop management of test scripts".

osmts是一个一站式管理和运行测试脚本并完成总结数据的工具。为基于rpm包管理器的linux发行版设计，一般用于openEuler新镜像的测试。

testclasses目录用于存放测试类,用于描述测试脚本执行过程以及数据分析与总结。



## 如何使用？

* 获取osmts

```
git clone https://gitee.com/April_Zhao/osmts.git
cd osmts
```



* 运行前安装环境

```
dnf install gcc python python3-devel python3-pip
pip install --upgrade pip setuptools
pip install -r requirements.txt

# 如果遇到SSL问题
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt

# 仍然提示SSL错误
dnf install ntp
ntpdate cn.pool.ntp.org
```



* 直接运行脚本

```commandline
# main.py应当直接以root身份运行
chmod +x main.py
./main.py
```

在运行脚本时可以使用--config或者-c选项指定配置文件的位置（默认是osmts_config.toml）.

比如：

```Python
./main.py --config your_config.toml

# 或者
./main.py -c your_config.toml

# 也可以不配置,用默认的文件名
./main.py
```



* toml文件配置

```
run_tests = ['netperf','unixbench','nmap','stream']
saved_directory = "/root/osmts_result"
merge = 0
compiler = "gcc"
netperf_server_ip = "127.0.0.1"
remove_osmts_tmp_dir = 1
```

1. run_tests是一个列表，里面是需要测试的项目;
2. saved_directory填写测试结果存放的目录，main.py运行结束后会在这个目录产生excel文件，默认为'/root/osmts_result';
3. merge是最终生成的excel是否要合并，如果为1则产物只有一个，如果为0则每个测试各生成一个;
4. compiler是待测试的编译环境，应当填写gcc或者clang ,默认是gcc;
5. netperf_server_ip是netserver运行的机器的ip地址，如果不测试netperf则无需填写，netserver机器可以是自己，这时候就填写127.0.0.1;指定机器上提前运行netserver -p 10000。
6. 如果run_tests里存在“performance-test”，则osmts会自动把[性能测试文档](https://gitee.com/jean9823/openEuler_riscv_test/blob/master/%E5%9C%A8openEuler%20RISC-V%2024.03%20LTS%20%E4%B8%8A%E6%89%8B%E5%8A%A8%E6%89%A7%E8%A1%8C%E6%80%A7%E8%83%BD%E6%B5%8B%E8%AF%95.md)这里面的项目添加进去;
7. remove_osmts_tmp_dir = 1表示在测试结束后删除存放测试文件的临时目录/root/osmts_tmp/,为0表示保留.



有的测试项目会运行很长一段时间，把main.py一直挂着就好，推荐在screen/tmux这样的终端复用器里运行，防止意外终止运行。

---

## 开发进度

| 项目       | 支持程度 |
| ---------- |------|
| unixbench  | 完成   |
| nmap       | 完成   |
| lmbench    | 完成   |
| stream     | 完成   |
| ltp stress | 完成   |
| iozone     | 完成   |
| libmicro   | 完成   |
| fio        | 完成   |
| netperf    | 完成   |
| trinity    | 完成   |
| ltp cve    | 未完成  |
| ltp posix  | 未完成  |
| ltp        | 待分析  |


## 注意事项
1. 请不要在run_tests里添加“未完成”的项目.
2. fio测试要下载iso文件、ltp stress测试很费时,单独开进程并行执行.main.py若被用户强制终止,则子进程也会dead.
3. 若待测机器的/分区剩余容量过小,osmts会报错,避免因fio下载文件导致文件系统崩溃.

---
## 未来计划
1. 开发更多测试脚本进行汇总;
2. 对已有的测试结果进行审查看是否有数据遗漏;
3. osmts项目在sg2042 Milk-V Pioneer上检测通过,在其他设备上待测试.


---
## 展示图片
netperf测试类的输出结果如图所示:
![netperf总结为excel的截图](https://github.com/hehellooedas/learn_riscv/blob/main/images/osmts_imgs/netperf_excel.png?raw=true)

fio测试类的输出结果如图所示:
![fio总结为excel的截图](https://github.com/hehellooedas/learn_riscv/blob/main/images/osmts_imgs/fio_excel.png?raw=true)

lmbench测试类的输出结果如图所示:
![netperf总结为excel的截图](https://github.com/hehellooedas/learn_riscv/blob/main/images/osmts_imgs/lmbench_excel.png?raw=true)