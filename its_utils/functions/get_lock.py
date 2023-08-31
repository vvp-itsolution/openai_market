# coding=utf8

# http://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running
import socket
import sys


def get_lock(process_name):
    global lock_socket

    if not getattr(socket, 'AF_UNIX', 0):
        print('Windows launch?')
        return

    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        lock_socket.bind('\0' + process_name)
    except socket.error:
        print('%s lock exists' % process_name)
        sys.exit()
