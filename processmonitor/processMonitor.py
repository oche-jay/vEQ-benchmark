import os
import platform
import re
from subprocess import PIPE
import subprocess

import psutil


# from __main__ import name
def get_processor():
    if platform.system() == "Windows":
        family = platform.processor()
        name = subprocess.check_output(["wmic","cpu","get", "name"]).strip().split("\n")[1]
        return ' '.join([name, family])
    elif platform.system() == "Darwin":
        import os
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + "/usr/sbin"
        return subprocess.check_output(["sysctl","-n","machdep.cpu.brand_string"]).strip()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(command, shell=True).strip()
        for line in all_info.split("\n"):
            if "model name" in line:
                return re.sub( ".*model name.*:", "", line,1)
    return "N/A"

def get_gpu():
    import os
    if platform.system() == "Windows":
        return subprocess.check_output(["wmic","path",  "win32_VideoController", "get", "name"]).strip().split("\n")[1]
    elif platform.system() == "Darwin":
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + "/usr/sbin"
        return subprocess.check_output(["system_profiler","SPDisplaysDataType"]).strip()
    elif platform.system() == "Linux":
        return "Not implemented"
    else:
        return "Not Available"

def get_os():
    system = platform.system()
    release = platform.release()
    operatingsys = ' '.join([system, release])
    return operatingsys
#p = psutil.Popen(["stress","-t","10","-c","1"], stdout=PIPE)

# for proc in psutil.process_iter():
#     try:
#         if 'Google' in  (proc.name() ):
#             print "Google"
#         pinfo = proc.as_dict(attrs=['pid', 'name', 'cpu_percent'])
#     except psutil.NoSuchProcess:
#         pass
#     else:
#         print(pinfo)

if __name__ == '__main__':
    import time
    t = time.time()
    print platform.system()
    print get_processor()
    print get_os()
    print get_gpu()
    print time.time() - t