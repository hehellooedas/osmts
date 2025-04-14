from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from io import BytesIO
from pathlib import Path
import re,os,time
import requests,tarfile
import pymysql
import sys,subprocess,shutil

from errors import DefaultError


class TPC_H:
    def __init__(self, **kwargs):
        self.rpms = {'sysbench','mysql-server'}
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.directory: Path = kwargs.get('saved_directory') / 'TPC-H'
        self.path = Path('/root/osmts_tmp/TPC-H')
        self.saveSQL = self.path / 'saveSQL'
        self.test_result:str = ''


    def pre_test(self):
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)

        self.mysqld:Unit = Unit('mysqld.service',_autoload=True)
        try:
            self.mysqld.Unit.Start(b'replace')
        except:
            self.mysqld.Unit.Start(b'replace')
        time.sleep(5)
        if self.mysqld.Unit.ActiveState != b'active':
            time.sleep(5)
            if self.mysqld.Unit.ActiveState != b'active':
                print(f"sysbench测试出错.开启mysqld.service失败,退出测试.")
                sys.exit(1)
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

        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path,ignore_errors=True)
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
        cursor.execute(f"SOURCE {self.path}/dbgen/dss.ddl")
        cursor.execute(f"SOURCE {self.path}/dbgen/dss.ri")

        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        for table in ('customer','lineitem','nation','orders','partsupp','part','region','supplier'):
            cursor.execute(f"LOAD DATA LOCAL INFILE {self.path}/dbgen/{table}.tbl INTO TABLE {table};")
            cursor.execute(f"FIELDS TERMINATED BY '|' LINES TERMINATED BY '|\n';")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
        cursor.close()


    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'TPC-H'
        ws.append(['执行查询的编号','查询时间'])

        for i in range(1,23):
            with self.conn.cursor() as cursor:
                start_time = time.perf_counter()
                cursor.execute(f"SOURCE {self.path}/dbgen/saveSQL/{i}.sql")
                stop_time = time.perf_counter()
                cursor.execute(f"show profile")
                profile = cursor.fetchall()
                print(profile)
                print(f"Python处记录的时间{stop_time - start_time}")



    def post_test(self):
        self.mysqld.Unit.Stop(b'replace')
        subprocess.run(
            "dnf remove -y mysql-server",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )


    def run(self):
        print('开始进行tpch测试')
        self.pre_test()
        self.run_test()
        self.post_test()
        print('tpch测试结束')