from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from pathlib import Path
from io import StringIO
import csv,time
import sys,subprocess,shutil


TEST_COMMANDS = (
    'PING_INLINE','PING_MBULK','SET','GET','INCR','LPUSH','RPUSH','LPOP','RPOP','SADD','HSET','SPOP','ZADD',
    'ZPOPMIN','LPUSH','LRANGE_100','LRANGE_300','LRANGE_500','LRANGE_600','MSET','XADD'
)


class redisBenchMark: # redis-benchmark 是 Redis 自带的基准测试工具
    def __init__(self, **kwargs):
        self.rpms = {'redis'}
        self.directory: Path = kwargs.get('saved_directory') / 'redis-benchmark'
        self.test_result:str = ''


    def pre_test(self):
        self.redis:Unit = Unit(b'redis.service',_autoload=True)
        try:
            self.redis.Unit.Start(b'replace')
        except:
            self.redis.Unit.Start(b'replace')
        time.sleep(5)
        if self.redis.Unit.ActiveState != b'active':
            time.sleep(5)
            if self.redis.Unit.ActiveState != b'active':
                print("redis_benchmark测试出错.redis.service开启失败,退出测试.")
                sys.exit(1)

        redis_benchmark_check = subprocess.run(
            "type redis-benchmark",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )
        if redis_benchmark_check.returncode != 0:
            print(f"redis_benchmark测试出错.找不到redis-benchmark命令.")
            sys.exit(1)

        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)


    def run_test(self):
        redis_bench_mark = subprocess.run(
            "redis-benchmark -h 127.0.0.1 -c 100 -n 100000 --csv "
            f"-t {','.join(TEST_COMMANDS)}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if redis_bench_mark.returncode != 0:
            print(f"redis_benchmark测试出错.测试时报错,报错信息:{redis_bench_mark.stderr.decode('utf-8')}")
            return
        self.test_result = redis_bench_mark.stdout.decode('utf-8')


    def result2symmary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'redisBenchmark'
        ws.append(['测试项目名称','rps(每秒请求数)','平均延迟(ms)','最小延迟(ms)','50% 延迟(ms)[中位数]','90% 延迟(ms)','99% 延迟(ms)','最大延迟(ms)'])

        csv_reader = list(csv.reader(StringIO(self.test_result), delimiter=','))
        for result in csv_reader[1:]:
            ws.append(result)

        wb.save(self.directory / 'redisBenchmark.xlsx')


    def post_test(self):
        self.redis.Unit.Stop(b'replace')
        time.sleep(5)
        subprocess.run(
            "dnf remove -y redis",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )


    def run(self):
        print('开始进行redis_benchmark测试')
        self.pre_test()
        self.run_test()
        self.result2symmary()
        self.post_test()
        print('redis_benchmark测试结束')