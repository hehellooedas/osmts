from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from pathlib import Path
import re
import pymysql
import sys,subprocess,shutil


class sysBench:
    def __init__(self, **kwargs):
        self.rpms = {'sysbench'}
        self.directory: Path = kwargs.get('saved_directory') / 'sysbench'
        self.test_result:str = ''


    def pre_test(self):
        self.mysqld:Unit = Unit('mysqld.service',_autoload=True)
        self.mysqld.Unit.Start(b'replace')
        if self.mysqld.Unit.ActiveState != b'active':
            print(f"sysbench测试出错.开始mysqld.service失败,退出测试.")
            sys.exit(1)

        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)

        try:
            self.conn = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                passwd='',
            )
        except Exception as e:
            self.conn = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                passwd='123456',
            )
        cursor = self.conn.cursor()
        cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';")
        cursor.execute("DROP DATABASE IF EXISTS sysbench;")
        cursor.execute("CREATE DATABASE IF NOT EXISTS sysbench;")
        cursor.close()

        # 准备测试数据和表
        sysbench_prepare = subprocess.run(
            "sysbench --db-driver=mysql --mysql-host=127.0.0.1 "
            "--mysql-port=3306 --mysql-user=root --mysql-password=123456 "
            "--mysql-db=sysbench --table_size=10000000 --tables=64 "
            "--time=180 --threads=6 --report-interval=1 oltp_read_write prepare",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if sysbench_prepare.returncode != 0:
            print(f"sysbench测试出错.准备测试数据和表失败,报错信息:{sysbench_prepare.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        sysbench_run = subprocess.run(
            "sysbench --db-driver=mysql --mysql-host=127.0.0.1 "
            "--mysql-port=3306 --mysql-user=root --mysql-password=123456 "
            "--mysql-db=sysbench --table_size=10000000 --tables=64 "
            "--time=180 --threads=6 --report-interval=1 oltp_read_write run",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if sysbench_run.returncode != 0:
            print(f"sysbench测试出错.运行sysbench run返回值不为0,报错信息:{sysbench_run.stderr.decode('utf-8')}")
        self.test_result = sysbench_run.stdout.decode('utf-8')
        with open(Path(self.directory) / 'sysbench.log', 'a') as log:
            log.write(self.test_result)
        print(self.test_result)


    def result2summary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'sysbench'
        


    def post_test(self):
        # 清理测试数据
        sysbench_clean = subprocess.run(
            "sysbench --db-driver=mysql --mysql-host=127.0.0.1 "
            "--mysql-port=3306 --mysql-user=root --mysql-password=123456 "
            "--mysql-db=sysbench --table_size=10000000 --tables=64 "
            "--time=180 --threads=6 --report-interval=1 oltp_read_write cleanup",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if sysbench_clean.returncode != 0:
            print(f"sysbench测试.清理测试数据失败,报错信息:{sysbench_clean.stderr.decode('utf-8')}")

        self.mysqld.Unit.Stop(b'replace')
        subprocess.run(
            "dnf remove -y mysql-server",
            shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )


    def run(self):
        print('开始进行sysbench测试')
        self.pre_test()
        self.run_test()
        self.result2summary()
        self.post_test()
        print('sysbench测试结束')