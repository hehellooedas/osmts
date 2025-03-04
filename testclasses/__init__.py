from testclasses.libmicro import Libmicro
from testclasses.unixbench import Unixbench
from testclasses.stream import Stream
from testclasses.iozone import Iozone
from testclasses.fio import Fio
from testclasses.nmap import Nmap
from testclasses.ltp import Ltp
from testclasses.ltp_cve import Ltp_cve
from testclasses.netperf import Netperf
from testclasses.lmbench import Lmbench
from testclasses.trinity import Trinity
from testclasses.ltp_stress import Ltp_stress


osmts_tests = {
    "iozone":(
        Iozone
    ),
    "libmicro":(
        Libmicro
    ),
    "fio":(
        Fio
    ),
    "stream":(
        Stream
    ),
    "nmap":(
        Nmap
    ),
    "unixbench":(
        Unixbench
    ),
    "ltp":(
        Ltp
    ),
    "ltp_cve":(
        Ltp_cve
    ),
    "netperf":(
        Netperf
    ),
    "lmbench":(
        Lmbench
    ),
    "trinity":(
        Trinity
    ),
    "ltp_stress":(
        Ltp_stress
    )
}
