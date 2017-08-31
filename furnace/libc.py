#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

import ctypes
import os

from bake.logger import Logger

logger = Logger(__name__)

libc = ctypes.CDLL("libc.so.6", use_errno=True)


MS_RDONLY = 0x00000001
MS_NOSUID = 0x00000002
MS_NODEV = 0x00000004
MS_NOEXEC = 0x00000008
MS_REMOUNT = 0x00000020
MS_NOATIME = 0x00000400
MS_NODIRATIME = 0x00000800
MS_BIND = 0x00001000
MS_MOVE = 0x00002000
MS_REC = 0x00004000
MS_PRIVATE = 0x00040000
MS_SLAVE = 0x00080000
MS_SHARED = 0x00100000
MS_STRICTATIME = 0x01000000

CLONE_NEWCGROUP = 0x02000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWNS = 0x00020000
CLONE_NEWPID = 0x20000000
CLONE_NEWUTS = 0x04000000

SYSCALL_NUM_CLONE = 56
SYSCALL_NUM_GETPID = 39


def mount(source, target, fstype, flags, data):
    if fstype is not None:
        fstype = fstype.encode('utf-8')
    if data is not None:
        data = data.encode('utf-8')
    if libc.mount(source.encode('utf-8'), target.encode('utf-8'), fstype, flags, data) != 0:
        raise OSError(ctypes.get_errno(), "Mount failed")


def umount(target):
    if libc.umount(target.encode('utf-8')) != 0:
        raise OSError(ctypes.get_errno(), "Unmount failed for directory {}".format(target))


def get_all_mounts():
    with open("/proc/self/mounts") as f:
        mounts = []
        for l in f:
            mp = l.split(' ')[1]
            # unicode_escape is necessary because moutns with special characters are
            # represented with octal escape codes in 'mounts'
            mounts.append(mp.encode('utf-8').decode('unicode_escape'))
    return mounts


def is_mount_point(path):
    # os.path.ismount does not properly detect bind mounts
    return os.path.abspath(path) in get_all_mounts()


def unshare(flags):
    if libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), "unshare failed")


def setns(fd, flags):
    if libc.setns(fd, flags) != 0:
        raise OSError(ctypes.get_errno(), "sqtns failed")


def pivot_root(new_root, old_root):
    if libc.pivot_root(new_root.encode('utf-8'), old_root.encode('utf-8')) != 0:
        raise OSError(ctypes.get_errno(), "pivot_root failed")


def clone(flags, stack=0):
    syscall = libc.syscall
    syscall.restype = ctypes.c_int
    syscall.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int)
    result = syscall(SYSCALL_NUM_CLONE, flags, stack)
    if result < 0:
        raise OSError(abs(result), "clone failed")
    return result


def non_caching_getpid():
    # libc caches the return value of getpid, and does not refresh this
    # cache, if we call syscalls (e.g. clone) by hand.
    syscall = libc.syscall
    syscall.restype = ctypes.c_int
    syscall.argtypes = (ctypes.c_int,)
    result = syscall(SYSCALL_NUM_GETPID)
    if result < 0:
        raise OSError(abs(result), "getpid failed")
    return result