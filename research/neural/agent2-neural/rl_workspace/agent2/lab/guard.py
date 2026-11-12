"""RAM watchdog for long jobs (same rule as run_guarded.ps1, without PowerShell scripts): runs the command, kills it
if free physical memory falls under 2 GB, and reports the lowest free RAM seen.
usage: python -P agent2/lab/guard.py LOGFILE -- command args...   (environment passes through)
"""
import ctypes, subprocess, sys, time


class MEM(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def free_gb():
    m = MEM()
    m.dwLength = ctypes.sizeof(MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2 ** 30


log, cmd = sys.argv[1], sys.argv[sys.argv.index("--") + 1:]
low = 99.0
with open(log, "a") as fh:
    p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
    while p.poll() is None:
        time.sleep(3)
        f = free_gb()
        low = min(low, f)
        if f < 2.0:
            p.kill()
            fh.write(f"KILLED by watchdog: free RAM {f:.2f} GB\n")
            print("KILLED: free RAM under 2 GB", flush=True)
            break
print(f"exit {p.returncode}; lowest free RAM {low:.1f} GB", flush=True)
