from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from io import BytesIO
from pathlib import Path
import pexpect
import time
import requests,tarfile
import pymysql
import subprocess,shutil
from tqdm import trange,tqdm

from .errors import DefaultError


class TPC_H:
    def __init__(self, **kwargs):
        self.rpms = {'sysbench','mysql-server'}
        self.directory: Path = kwargs.get('saved_directory') / 'TPC-H'
        self.path = Path('/root/osmts_tmp/TPC-H')
        self.dbgen = self.path / 'dbgen'
        self.saveSQL = self.dbgen / 'saveSQL'
        self.test_result:str = ''


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        if self.path.exists():
            shutil.rmtree(self.path)

        self.mysqld:Unit = Unit('mysqld.service',_autoload=True)
        try:
            self.mysqld.Unit.Start(b'replace')
        except:
            self.mysqld.Unit.Start(b'replace')
        time.sleep(5)
        if self.mysqld.Unit.ActiveState != b'active':
            time.sleep(5)
            if self.mysqld.Unit.ActiveState != b'active':
                raise DefaultError("sysbench测试出错.开启mysqld.service失败,退出测试.")

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

        # 获取TPC-H
        response = requests.get(
            url="https://gitee.com/April_Zhao/osmts/releases/download/v1.0/TPC-H.tar.xz",
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0',
                'referer': 'https://gitee.com/April_Zhao/osmts',
            }
        )
        response.raise_for_status()
        with tarfile.open(fileobj=BytesIO(response.content), mode="r:xz") as tar:
            tar.extractall(Path('/root/osmts_tmp/'))

        # build dbgen
        # 这个过程会有交互
        try:
            subprocess.run(
                f"make -j 4 && ./dbgen -s 1",
                cwd=self.path / "dbgen",
                shell=True,check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise DefaultError(f"TPC-H测试出错.构建或运行dbgen失败,报错信息:{e.stdout.decode('utf-8')}")



        cursor.execute("DROP DATABASE IF EXISTS tpch;")
        cursor.execute("CREATE DATABASE IF NOT EXISTS tpch;")
        cursor.execute("USE tpch;")
        cursor.close()

        # SOURCE是MySQL客户端特有的工具(pymysql无法执行SOURCE)
        # cursor.execute(f"SOURCE {self.path}/dss.ddl;")
        # cursor.execute(f"SOURCE {self.path}/dss.ri;")


        mysql = pexpect.spawn(
            command="/bin/bash",
            args=["-c", "mysql -uroot -p123456"],
            encoding='utf-8',
            logfile=open(self.directory / 'osmts_tpch_loadData.log', 'w'),
        )
        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline(f"USE tpch;")

        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline("SET GLOBAL max_allowed_packet = 1024*1024*1024;")

        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline("SET GLOBAL innodb_buffer_pool_size = 4*1024*1024*1024;")

        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline(f"SOURCE {self.dbgen}/dss.ddl;")
        mysql.expect_exact("mysql>", timeout=600)
        mysql.sendline(f"SOURCE {self.dbgen}/dss.ri;")

        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline("SET FOREIGN_KEY_CHECKS=0;")
        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline("SET GLOBAL local_infile=1;")

        for table in tqdm(('customer','lineitem','nation','orders','partsupp','part','region','supplier'),desc="load data进度"):
            mysql.expect_exact("mysql>",timeout=3600)
            mysql.sendline(
                f"LOAD DATA LOCAL INFILE '{self.dbgen}/{table}.tbl' INTO TABLE {table} FIELDS TERMINATED BY '|' LINES TERMINATED BY '|\n';"
            )

        mysql.expect_exact("mysql>")
        mysql.sendline("SET FOREIGN_KEY_CHECKS=1;")
        mysql.expect_exact("mysql>")
        mysql.terminate(force=True)



    def run_test(self):
        mysql = pexpect.spawn(
            command="/bin/bash",
            args=["-c", "mysql -uroot -p123456"],
            encoding='utf-8',
            logfile=open(self.directory / 'osmts_tpch_query.log', 'w'),
        )
        mysql.expect_exact("mysql>", timeout=60)
        mysql.sendline(f"USE tpch;")

        for i in trange(1,23,desc="SQL查询进度"):
            mysql.expect_exact("mysql>")
            mysql.sendline(f"\. {self.saveSQL}/{i}.sql")
        time.sleep(5)
        mysql.terminate(force=True)


    def result2summary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'TPC-H'
        ws.append(['SQL文件','查询所耗时间'])

        index = 1
        log = open(self.directory / 'osmts_tpch_query.log').readlines()
        for line in log:
            if "rows in set" in line:
                print(line)
                ws.append([index, line.split('(')[-1][:-1]])
                index += 1
        wb.save(self.directory / 'tpch.xlsx')


    def post_test(self):
        self.mysqld.Unit.Stop(b'replace')
        subprocess.run(
            "dnf remove -y mysql-server",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )


    def run(self):
        print('开始进行tpch测试')
        self.pre_test()
        self.run_test()
        self.result2summary()
        self.post_test()
        print('tpch测试结束')