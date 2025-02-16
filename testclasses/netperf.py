from pathlib import Path
import re,sys,subprocess
from openpyxl import Workbook
from testclasses.excel2csv import excel2csv


class Netperf(object):
    def __init__(self,**kwargs):
        self.saved_method:str = kwargs.get('saved_method')
        self.directory:Path = kwargs.get('saved_directory')
        self.server_ip:str = kwargs.get('netperf_server_ip')


    def pre_test(self):
        install_netperf = subprocess.run("dnf install netperf -y",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        if install_netperf.returncode != 0:
            print(f"netperf测试出错:rpm包安装失败.报错信息:{install_netperf.stderr.decode('utf-8')}")
            sys.exit(1)


    def run_test(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "netperf"

        ws.cell(1,1,"TCP STREAM TEST")
        ws.merge_cells("a1:a5")

        ws.cell(6,1,"UDP STREAM TEST")
        ws.merge_cells("a6:a20")

        ws.cell(21,1,"TCP REQUEST/RESPONSE TEST")
        ws.merge_cells("a21:a23")

        ws.cell(24,1,"TCP Connect/Request/Response TEST")
        ws.merge_cells("a24:a26")

        ws.cell(27,1,"UDP REQUEST/RESPONSE TEST")
        ws.merge_cells("a27:a29")

        # TCP_STREAM表头
        ws.cell(1,2,"Recv Socket Size bytes")
        ws.cell(1,3,"Send Socket Size Bytes")
        ws.cell(1,4,"Send Message Size Bytes")
        ws.cell(1,5,"Elapsed Time secs.")
        ws.cell(1,6,"Throughput(10^6bits/sec)")

        # UDP_STREAM表头
        ws.cell(7,2,"Socket Size bytes")
        ws.cell(7,3,"Message Size bytes")
        ws.cell(7,4,"Elapsed Time secs")
        ws.cell(7,5,"Messages Okay")
        ws.cell(7, 6, "Messages Errors")
        ws.cell(7,7,"Throughput(10^6bits/sec)")

        # 剩余三个测试的表头
        ws.cell(21,2,"Local Socket Send bytes")
        ws.cell(21, 3, "Remote Size Recv Bytes")
        ws.cell(21, 4, "Request Size bytes")
        ws.cell(21, 5, "Resp. Size bytes")
        ws.cell(21, 6, "Elapsed Time secs.")
        ws.cell(21,7,"Trans. Rate per sec")




        # TCP_STREAM测试
        line = 2
        for message_size_bytes in (1,64,512,65536):
            TCP_STREAM = subprocess.run(f"netperf -t TCP_STREAM -H {self.server_ip} -p 10000 -l 60 -- -m {message_size_bytes}",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if TCP_STREAM.returncode != 0:
                print(f"netperf测试出错:TCP_STREAM测试运行失败.报错信息:{TCP_STREAM.stderr}")
            result = re.findall(r'\d+\.\d+|\d+', TCP_STREAM.stdout.decode('utf-8').split('\n')[6])
            for col,value in enumerate(result):
                ws.cell(line,col+2,value)
            line += 1


        # UDP_STREAM测试
        line = 7
        for message_size_bytes in (1,64,128,256,512,32768):
            UDP_STREAM = subprocess.run(f"netperf -t UDP_STREAM -H {self.server_ip} -p 10000 -l 60 -- -m {message_size_bytes}",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if UDP_STREAM.returncode != 0:
                print(f"netperf测试出错:UDP_STREAM测试运行失败.报错信息:{UDP_STREAM.stderr.decode('utf-8')}")
                sys.exit(1)
            result1 = re.findall(r'\d+\.\d+|\d+', UDP_STREAM.stdout.decode('utf-8').split('\n')[5])
            result2 = re.findall(r'\d+\.\d+|\d+', UDP_STREAM.stdout.decode('utf-8').split('\n')[6])
            for col,value in enumerate(result1):
                ws.cell(line,col+2,value)
            line += 1
            ws.cell(line,2,result2[0])
            ws.cell(line, 4, result2[1])
            ws.cell(line, 5, result2[2])
            ws.cell(line, 7, result2[3])
            line += 1


        # TCP REQUEST/RESPONSE测试
        TCP_RR = subprocess.run(f"netperf -t TCP_RR -H ${self.server_ip} -p 10000",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if TCP_RR.returncode != 0:
            print(f"netperf测试出错:TCP_RR测试运行失败.报错信息:{TCP_RR.stderr.decode('utf-8')}")
            sys.exit(1)
        result1 = re.findall(r'\d+\.\d+|\d+', TCP_RR.stdout.decode('utf-8').split('\n')[6])
        result2 = re.findall(r'\d+\.\d+|\d+', TCP_RR.stdout.decode('utf-8').split('\n')[7])
        for col, value in enumerate(result1):
            ws.cell(22, col + 2, value)
        ws.cell(23, 2, result2[0])
        ws.cell(23, 3, result2[1])


        # TCP Connect/Request/Response测试
        TCP_CRR = subprocess.run(f"netperf -t TCP_CRR -H ${self.server_ip} -p 10000",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if TCP_CRR.returncode != 0:
            print(f"netperf测试出错:TCP_CRR测试运行失败.报错信息:{TCP_CRR.stderr.decode('utf-8')}")
            sys.exit(1)
        result1 = re.findall(r'\d+\.\d+|\d+', TCP_CRR.stdout.decode('utf-8').split('\n')[6])
        result2 = re.findall(r'\d+\.\d+|\d+', TCP_CRR.stdout.decode('utf-8').split('\n')[7])
        for col, value in enumerate(result1):
            ws.cell(25, col + 2, value)
        ws.cell(26, 2, result2[0])
        ws.cell(26, 3, result2[1])


        # UDP REQUEST/RESPONSE测试
        UDP_RR = subprocess.run(f"netperf -t UDP_RR -H ${self.server_ip} -p 10000",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if UDP_RR.returncode != 0:
            print(f"netperf测试出错:TCP_CRR测试运行失败.报错信息:{TCP_CRR.stderr.decode('utf-8')}")
            sys.exit(1)
        result1 = re.findall(r'\d+\.\d+|\d+', UDP_RR.stdout.decode('utf-8').split('\n')[6])
        result2 = re.findall(r'\d+\.\d+|\d+', UDP_RR.stdout.decode('utf-8').split('\n')[7])
        for col, value in enumerate(result1):
            ws.cell(28, col + 2, value)
        ws.cell(29, 2, result2[0])
        ws.cell(29, 3, result2[1])

        if self.saved_method == "excel":
            wb.save(self.directory / 'netperf.xlsx')
        elif self.saved_method == "csv":
            excel2csv(ws, self.directory)


    def run(self):
        print("开始进行netperf测试")
        self.pre_test()
        self.run_test()
        print("netperf测试结束")