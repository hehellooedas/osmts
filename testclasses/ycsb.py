from openpyxl.workbook import Workbook
from pystemd.systemd1 import Unit
from pathlib import Path
import re
import sys,subprocess,shutil



class YCSB: # Yahoo！Cloud Serving Benchmark
    def __init__(self, **kwargs):
        self.rpms = {'redis','java','maven'}
        self.believe_tmp: bool = kwargs.get('believe_tmp')
        self.path = Path('/root/osmts_tmp/YCSB')
        self.directory: Path = kwargs.get('saved_directory') / 'ycsb'
        self.ycsb:Path = self.path / 'bin/ycsb'
        self.workloada:Path = self.path / 'workloads/workloada'
        self.test_result:str = ''


    def pre_test(self):
        self.redis:Unit = Unit(b'redis.service',_autoload=True)
        self.redis.Unit.Start(b'replace')
        if self.redis.Unit.ActiveState != b'active':
            print("ycsb测试出错.redis.service开启失败,退出测试.")
            sys.exit(1)

        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)

        if self.path.exists() and self.believe_tmp:
            pass
        else:
            shutil.rmtree(self.path,ignore_errors=True)
            git_clone = subprocess.run(
                "cd /root/osmts_tmp && git clone https://gitcode.com/gh_mirrors/yc/YCSB.git",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if git_clone.returncode != 0:
                print(f"ycsb测试出错.git clone失败,报错信息:{git_clone.stderr.decode('utf-8')}")
                sys.exit(1)

        mvn = subprocess.run(
            f"cd {self.path} && mvn -pl site.ycsb:redis-binding -am clean package",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if mvn.returncode != 0:
            print(f"ycsb测试出错.mvn命令运行失败,报错信息:{mvn.stderr.decode('utf-8')}")
            sys.exit(1)

        with open(self.workloada,mode='a+') as workloada:
            workloada.writelines(['redis.host=127.0.0.1\n','redis.port=6379\n'])

        # 加载数据
        load = subprocess.run(
            f"cd {self.path} && "
            f"bin/ycsb load redis -threads 100 -P workloads/workloada",
            shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
        )
        if load.returncode != 0:
            print(f"ycsb测试出错.ycsb load redis加载数据失败,报错信息:{load.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        run = subprocess.run(
            f"cd {self.path} && "
            f"bin/ycsb run redis -threads 100 -P workloads/workloada",
            shell=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        )
        if run.returncode != 0:
            print(f"ycsb测试出错.执行测试失败,报错信息:{run.stderr.decode('utf-8')}")
            return
        self.test_result = run.stdout.decode('utf-8')
        with open(self.directory / 'ycsb.log','w') as log:
            log.write(self.test_result)


    def result2summary(self):
        wb = Workbook()
        ws = wb.active
        ws.title = 'ycsb'
        ws.append(['key','value'])

        # 总体指标
        ws.append(['总体指标','---'])
        runtime = re.search(r"\[OVERALL\], RunTime\(ms\), (\d+)",self.test_result)
        ws.append(['测试过程耗时:',runtime.group(1) + 'ms'])

        throughput = re.search(r"\[OVERALL\], Throughput\(ops/sec\), (\d+\.\d+)",self.test_result)
        ws.append(['测试过程中的吞吐量:',throughput.group(1) + 'ops/sec'])

        ws.append(['',''])

        # 垃圾回收(GC机制)指标
        ws.append(['垃圾回收(GC机制)指标','---'])
        gc_count_copy = re.search(r"\[TOTAL_GCS_Copy\], Count, (\d+)",self.test_result)
        ws.append(['发生Copy类型的GC次数:',gc_count_copy.group(1) + '次'])

        gc_time_copy = re.search(r"\[TOTAL_GC_TIME_Copy\], Time\(ms\), (\d+)",self.test_result)
        ws.append(['Copy类型的GC共耗时:',gc_time_copy.group(1) + 'ms'])

        gc_time_copy_percent = re.search(r"\[TOTAL_GC_TIME_%_Copy\], Time\(%\), (\d+\.\d+)",self.test_result)
        ws.append(['Copy类型的GC占程序总耗时的百分比:',gc_time_copy_percent.group(1) + '%'])

        gc_count_marksweepcompact = re.search(r"\[TOTAL_GCS_MarkSweepCompact\], Count, (\d+)",self.test_result)
        ws.append(['发生MarkSweepCompact类型GC次数:',gc_count_marksweepcompact.group(1) + '次'])

        gc_time_marksweepcompact = re.search(r"\[TOTAL_GC_TIME_MarkSweepCompact\], Time\(ms\), (\d+)",self.test_result)
        ws.append(['MarkSweepCompact类型的GC共耗时:',gc_time_marksweepcompact.group(1) + 'ms'])

        gc_time_marksweepcompact_percent = re.search(r"\[TOTAL_GC_TIME_%_MarkSweepCompact]\, Time\(%\), (\d+\.\d+)",self.test_result)
        ws.append(['MarkSweepCompact类型的GC占程序总耗时的百分比:',gc_time_marksweepcompact_percent.group(1) + '%'])

        gc_count = re.search(r"\[TOTAL_GCs\], Count, (\d+)",self.test_result)
        ws.append(['总共发生GC次数:',gc_count.group(1) + '次'])

        gc_time = re.search(r"\[TOTAL_GC_TIME\], Time\(ms\), (\d+)",self.test_result)
        ws.append(['GC总耗时:',gc_time.group(1) + 'ms'])

        gc_percent = re.search(r"\[TOTAL_GC_TIME_%\], Time\(%\), (\d+\.\d+)",self.test_result)
        ws.append(['GC占程序总耗时的百分比:',gc_percent.group(1) + '%'])

        ws.append(['',''])

        # 读(READ)取操作指标
        ws.append(['读取操作(read)指标','---'])

        read_Operations = re.search(r"\[READ\], Operations, (\d+)",self.test_result)
        ws.append(['共执行读操作次数:',read_Operations.group(1) + '次'])

        read_AverageLatency = re.search(r"\[READ\], AverageLatency\(us\), (\d+\.\d+)",self.test_result)
        ws.append(['每次读操作的平均时延:',read_AverageLatency.group(1) + 'us'])

        read_MinLatency = re.search(r"\[READ\], MinLatency\(us\), (\d+)",self.test_result)
        ws.append(['每次读操作的最小时延:',read_MinLatency.group(1) + 'us'])

        read_MaxLatency = re.search(r"\[READ\], MaxLatency\(us\), (\d+)",self.test_result)
        ws.append(['每次读操作的最大时延:',read_MaxLatency.group(1) + 'us'])

        read_PercentileLatency_50 = re.search(r"\[READ\], 50thPercentileLatency\(us\), (\d+)",self.test_result)
        read_PercentileLatency_95 = re.search(r"\[READ\], 95thPercentileLatency\(us\), (\d+)", self.test_result)
        read_PercentileLatency_99 = re.search(r"\[READ\], 99thPercentileLatency\(us\), (\d+)", self.test_result)
        ws.append([f'50% 读操作的时延在{read_PercentileLatency_50.group(1)}us以内',f'95% 读操作的时延在{read_PercentileLatency_95.group(1)}us以内',f'99% 读操作的时延在{read_PercentileLatency_99.group(1)}us以内'])

        read_return_ok = re.search(r"\[READ\], Return=OK, (\d+)",self.test_result)
        ws.append(['read返回成功,操作数:',read_return_ok.group(1)])

        ws.append(['',''])

        # 清理(CLEANUP)操作指标
        ws.append(['清理操作(clean up)指标', '---'])

        cleanup_Operations = re.search(r"\[CLEANUP\], Operations, (\d+)",self.test_result)
        ws.append(['执行了清理操作的次数:',cleanup_Operations.group(1) + '次'])

        cleanup_AverageLatency = re.search(r"\[CLEANUP\], AverageLatency\(us\), (\d+\.\d+)",self.test_result)
        ws.append(['每次清理操作的平均时延:',cleanup_AverageLatency.group(1) + 'us'])

        cleanup_MinLatency = re.search(r"\[CLEANUP\], MinLatency\(us\), (\d+)",self.test_result)
        ws.append(['每次清理操作的最小时延:',cleanup_MinLatency.group(1) + 'us'])

        cleanup_MaxLatency = re.search(r"\[CLEANUP\], MaxLatency\(us\), (\d+)",self.test_result)
        ws.append(['每次清理操作的最小时延:',cleanup_MaxLatency.group(1) + 'us'])

        cleanup_PercentileLatency_50 = re.search(r"\[CLEANUP\], 50thPercentileLatency\(us\), (\d+)",self.test_result)
        cleanup_PercentileLatency_95 = re.search(r"\[CLEANUP\], 95thPercentileLatency\(us\), (\d+)", self.test_result)
        cleanup_PercentileLatency_99 = re.search(r"\[CLEANUP\], 99thPercentileLatency\(us\), (\d+)", self.test_result)
        ws.append([f'50% 清理操作的时延在{cleanup_PercentileLatency_50.group(1)}us以内',f'95% 清理操作的时延在{cleanup_PercentileLatency_95.group(1)}us以内',f'99% 清理操作的时延在{cleanup_PercentileLatency_99.group(1)}us以内'])

        ws.append(['',''])

        # 更新操作指标
        ws.append(['更新操作(update)指标','---'])
        update_Operations = re.search(r"\[UPDATE\], Operations, (\d+)",self.test_result)
        ws.append(['执行了更新操作的次数:',update_Operations.group(1) + '次'])

        update_AverageLatency = re.search(r"\[UPDATE\], AverageLatency\(us\), (\d+\.\d+)",self.test_result)
        ws.append(['每次更新操作的平均时延:',update_AverageLatency.group(1) + 'us'])

        update_MinLatency = re.search(r"\[UPDATE\], MinLatency\(us\), (\d+)",self.test_result)
        ws.append(['每次更新操作的最小时延:',update_MinLatency.group(1) + 'us'])

        update_MaxLatency = re.search(r"\[UPDATE\], MaxLatency\(us\), (\d+)", self.test_result)
        ws.append(['每次更新操作的最小时延:', update_MaxLatency.group(1) + 'us'])

        update_PercentileLatency_50 = re.search(r"\[UPDATE\], 50thPercentileLatency\(us\), (\d+)",self.test_result)
        update_PercentileLatency_95 = re.search(r"\[UPDATE\], 95thPercentileLatency\(us\), (\d+)", self.test_result)
        update_PercentileLatency_99 = re.search(r"\[UPDATE\], 99thPercentileLatency\(us\), (\d+)", self.test_result)
        ws.append([f'50% 更新操作的时延在{update_PercentileLatency_50.group(1)}us以内',f'95% 更新操作的时延在{update_PercentileLatency_95.group(1)}us以内',f'99% 更新操作的时延在{update_PercentileLatency_99.group(1)}us以内'])

        update_return_ok = re.search(r"\[UPDATE\], Return=OK, (\d+)",self.test_result)
        ws.append(['update成功,操作数:',update_return_ok.group(1)])

        wb.save(self.directory / 'ycsb.xlsx')



    def post_test(self):
        self.redis.Unit.Stop(b'replace')
        subprocess.run(
            "dnf remove -y redis",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )


    def run(self):
        print("开始进行ycsb测试")
        self.pre_test()
        self.run_test()
        self.result2summary()
        self.post_test()
        print("ycsb测试结束")