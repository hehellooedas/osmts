from pySmartDL import SmartDL
import requests,shutil,pySmartDL
from pathlib import Path

from .errors import DefaultError

class Sha256sum():
    def __init__(self, **kwargs):
        self.rpms = set()
        self.path = Path('/root/osmts_tmp/sha256sumISO')
        self.directory: Path = kwargs.get('saved_directory') / 'sha256sumISO'
        self.sha256sumISO:str = kwargs.get('sha256sumISO')


    def pre_test(self):
        response = requests.get(self.sha256sumISO + '.sha256sum')
        if not response.ok:
            raise DefaultError("sha256sumISO测试sha256sum文件下载失败")
        self.hash = response.text.split(' ')[0]
        if self.path.exists():
            shutil.rmtree(self.path)
        self.path.mkdir()

        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir()


    def run_test(self):
        result = open(self.directory / 'sha256sumISO.result','w')
        try:
            ISO = SmartDL(
                urls=self.sha256sumISO,
                dest=str(self.path),
                threads=16,
                progress_bar=True,
                request_args={
                    "headers": {
                        'Connection': 'keep-alive',
                        # User-Agent会自动生成
                        'Referer': 'https://gitee.com/April_Zhao/osmts'
                    }},

            )
            ISO.add_hash_verification(algorithm='sha256',hash=self.hash)
            ISO.start(blocking=True)
        except pySmartDL.pySmartDL.HashFailedException:
            result.write("哈希值校验失败")
        else:
            result.write("哈希值校验成功")
        finally:
            result.close()

    def post_test(self):
        shutil.rmtree(self.path)

    def run(self):
        self.pre_test()
        self.run_test()
        self.post_test()