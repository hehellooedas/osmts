from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from pathlib import Path
import re,os,time
import requests,tarfile
import pymysql,psycopg2
import sys,subprocess,shutil


class BenchMarkSQL:
    def __init__(self, **kwargs):
        self.rpms = {'postgresql-server','mysql-server','java'}
        self.directory: Path = kwargs.get('saved_directory') / 'benchmarksql'
        self.test_result:str = ''


    def pre_test(self):
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

        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)


    def run_test(self):
        pass


    def run(self):
        print('开始进行benchmarksql测试')
        self.pre_test()
        self.run_test()
        print('benchmarksql测试结束')