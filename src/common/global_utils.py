#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import configparser
import logging
import logging.handlers
import json
from threading import Lock
import sys
import traceback
import platform
import threading
import src.common.constant as constant
from getpass import getuser
import time
import datetime
from decimal import Decimal

# if "Linux" in platform.system():
#     import fcntl


EMPTY_RETURN = ""

#global dict to read json files
JSON_DICT = {}

#a lock to protect json conf file read and write
JSON_LOCK = Lock()

TERM_RED   = '\033[1;31m'
TERM_NFMT  = '\033[0;0m'
TERM_BLUE  = '\033[1;34m'
TERM_GREEN = '\033[1;32m'


# return true if current system is Windows
def is_windows_system():
    return "Windows" in platform.system()

# return true if current system is Linux
def is_linux_system():
    return "Linux" in platform.system()

# return true if current system is MacOS
def is_macos_system():
    return "Darwin" in platform.system()

def get_transfer_addr(ip):
    """get target address based on types: tcp, udp, ipc
    
    Arguments:
        ip {str} -- [string get from the json conf file]
    
    Returns:
        [str] -- [address string]
    """
    mark = "://"
    mark_index = ip.index(mark) if mark in ip else 0
    type = ip[: mark_index]
    if not type:
        return None
    if type.lower() == "tcp" or type.lower() == "udp":
        return ip
    elif type.lower() == "ipc":
        cur_dir = os.path.dirname(os.path.dirname(__file__))
        file_name = ip[mark_index + len("://"):]  # the len("://") is 3 
        path = os.path.join(cur_dir, "ipc")
        if not os.path.exists(path):
            os.makedirs(path)
        path = "ipc://" + os.path.join(path, file_name)
        return path

def get_current_func_name():
    return (sys._getframe().f_code.co_filename + " : " + sys._getframe().f_code.co_name + "()")            
    

#TODO 测一下
def get_common_parent_path(file=None):
    """
    return to upper level of common
    当前文件在common文件夹, 返回到上一层目录的路径

    file {string} -- "file name if you need to add after parent path/要组装的文件名"
    """
    parent = os.path.dirname(os.path.dirname(__file__))
    if file:
        result = os.path.join(parent, file)
        return result
    else:
        return parent

def get_json_config(file, section , key=None, default = EMPTY_RETURN):
    """get json file
    
    Arguments:
        file {string} -- absolute file path
        section {string} -- level1 key
    
    Keyword Arguments:
        key {string} -- level2 key (default: {None})
    
    Returns:
        dict -- json dict
    """
    try:
        global JSON_LOCK
        with JSON_LOCK:
            global JSON_DICT
            if file not in JSON_DICT:
                if os.path.exists(file):
                    if os.path.getsize(file):
                        with open(file, mode="r", encoding="utf-8") as json_file:
                            # if is_linux_system():
                            #     fcntl.flock(json_file, fcntl.LOCK_EX)
                            global_dict = json.load(json_file)
                            JSON_DICT[file] = global_dict
                    else:
                        JSON_DICT[file] = {}
                else:
                    JSON_DICT[file] = {}

            if section in JSON_DICT[file]:
                if key and key in JSON_DICT[file][section]:
                    data = JSON_DICT[file][section][key]
                elif key and key not in JSON_DICT[file][section]:
                    data = default
                else:
                    data = JSON_DICT[file][section]
            else:
                data = JSON_DICT[file]
        
            return data
    except:
        traceback.print_exc()
        return {}
        

def set_json_config(file, section, value, key=None):
    """set json file
        
    Arguments:
        file {string} -- absolute file path
        section {string} -- level1 key
    
    Keyword Arguments:
        key {string} -- level2 key (default: {None})
    
    Returns:
        dict -- json dict
    """
    try:
        global JSON_DICT
        global JSON_LOCK
        with JSON_LOCK:
            if file not in JSON_DICT:
                if os.path.exists(file):
                    if os.path.getsize(file):
                        with open(file, mode="r", encoding="utf-8") as json_file:
                            # if is_linux_system():
                            #     fcntl.flock(json_file, fcntl.LOCK_EX)
                            global_dict = json.load(json_file)
                            JSON_DICT[file] = global_dict
                    else:
                        JSON_DICT[file] = {}
                else:
                    JSON_DICT[file] = {}

            if section not in JSON_DICT[file]:
                JSON_DICT[file][section] = {}

            if key:
                JSON_DICT[file][section][key] = value
            else:
                JSON_DICT[file][section] = value

            with open(file, mode="w", encoding="utf-8") as json_file:
                # if is_linux_system():
                #     fcntl.flock(json_file, fcntl.LOCK_EX)
                data = json.dumps(JSON_DICT[file], ensure_ascii=False, indent=4)
                json_file.write(data)
    except:
        traceback.print_exc()

def get_ini_config(file, section, key):
    try:
        config = configparser.ConfigParser()
        config.read(file)
        return config.get(section, key)
    except:
        traceback.print_exc()
        return EMPTY_RETURN


def set_ini_config(file, section, key, value):
    try:
        config = configparser.ConfigParser()
        config.read(file)
        config.set(section, key, value)
        config.write(open(file, "w"))
    except:
        traceback.print_exc()

def setup_logger(log_file_name, log_level=logging.INFO, print_level=logging.INFO, log_path=None, file_size=None):
    """
        Init LOG module here
    """
    #1.读属于哪个文件夹
    LOG_DIR = './logs'

    #2.拼一个文件夹路径

    if is_windows_system():
        #windows下 如果没有配置, 则使用文件夹下log文件夹
        if not log_path:
            LOG_DIR = os.path.join(get_common_parent_path(), "log")
            LOG_FILE = os.path.join(LOG_DIR, log_file_name + ".log")

        else:
            LOG_DIR = log_path
            LOG_FILE = os.path.join(LOG_DIR, log_file_name+".log")

    elif is_linux_system() or is_macos_system():
        # linux下 如果没有配置, 则使用/tmp文件夹
        if not log_path:
            LOG_DIR = "/tmp/coin_trade/log/" + getuser() + "/default_log"   #配置到统一 /tmp文件夹
            LOG_FILE = LOG_DIR + "/" + log_file_name + ".log"
        else:
            LOG_DIR = log_path
            LOG_FILE = os.path.join(LOG_DIR, log_file_name + ".log")


    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    #加入不同的文件存储方式: size  time
    if file_size:
        handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=file_size, backupCount=60)
    else:
        handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', interval=1)
        handler.suffix = '%Y-%m-%d.log'
    fmt = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s ---- %(message)s'

    formatter = logging.Formatter(fmt)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter


    logger = logging.getLogger(log_file_name)  # 获取名为tst的logger
    logger.addHandler(handler)  # 为logger添加handler
    #DEBUG 20180418
    logger.setLevel(log_level)

    # Prints logger info to terminal
    ch = logging.StreamHandler()
    #DEBUG 20180418
    ch.setLevel(print_level)
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 添加日志文件权限
    os.chmod(LOG_FILE, 0o777) #0o标志, 777全读写运行权限
    os.chmod(LOG_DIR, 0o777)
    return logger

def setup_save_data_logger(file_name, level=logging.INFO, isPrint=False, path=None, file_size=None):
    """
        Init LOG module here
    """
    #1.读属于哪个文件夹

    #2.拼一个文件夹路径

    if is_windows_system():
        #windows下 如果没有配置, 则使用文件夹下log文件夹
        if not path:
            LOG_DIR = os.path.join(get_common_parent_path(), "log")
            LOG_FILE = os.path.join(LOG_DIR, file_name + ".dict")

        else:
            LOG_DIR = path
            LOG_FILE = os.path.join(LOG_DIR, file_name + ".dict")

    elif is_linux_system():
        # linux下 如果没有配置, 则使用/tmp文件夹
        if not path:
            json_dir = os.path.join(get_common_parent_path(), "global.json")
            folder_name = get_json_config(file=json_dir, section="path", key="folder_name")
            LOG_DIR = "/tmp/coin_trade/log/" + getuser() + "/" + folder_name  #配置到统一 /tmp文件夹
            LOG_FILE = LOG_DIR + "/" + file_name + ".dict"
        else:
            LOG_DIR = path
            LOG_FILE = os.path.join(LOG_DIR, file_name + ".dict")


    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    #加入不同的文件存储方式: size  time
    if file_size:
        handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=file_size, backupCount=60)
    else:
        handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', interval=1)
        handler.suffix = '%Y-%m-%d.dict'
    fmt = '%(message)s'

    formatter = logging.Formatter(fmt)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter


    logger = logging.getLogger(file_name)  # 获取名为tst的logger
    logger.addHandler(handler)  # 为logger添加handler
    logger.setLevel(level)

    # Prints logger info to terminal
    if isPrint:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # add formatter to ch
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # 添加日志文件权限
    os.chmod(LOG_FILE, 0o777)  # 0o标志, 777全读写运行权限
    os.chmod(LOG_DIR, 0o777)

    return logger

def print_error(actual_func):
    """decorator to print exception
    打印错误的装饰器糖
    """
    def my_decorate(*args, **keyargs):
        try:
            return actual_func(*args, **keyargs)
        except:
            print("Error execute: {}".format(actual_func.__name__))
            traceback.print_exc()
    return my_decorate
    
    
def call_timer(execute_method=None, args=[]):
    """
    通过timer执行指定函数
    :param execute_method:
    :param args:
    :return:
    """
    if execute_method:
        try:
            timer = threading.Timer(constant.TIMER_INTERVAL_NOW, execute_method, args)
            timer.start()
        except:
            print("Error: call_timer error.")
            traceback.print_exc()
    else:
        print("Error: call_timer error,execute_method is None.")


def get_current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


def format_timestamp_to_date(timestamp):
    """
    时间戳（毫秒级、微秒级）转换成日期
    :param timestamp:
    :return:
    """
    ts_str = str(timestamp)
    return time.strftime("%Y-%m-%d", time.localtime(int(ts_str[:10])))


def get_yestoday(mytime, format="%Y-%m-%d"):
    """
    获取当前日期的前一天
    :param mytime:
    :param format:
    :return:
    """
    myday = datetime.datetime.strptime(mytime, format)
    my_yestoday = myday - datetime.timedelta(days=1)
    return my_yestoday.strftime(format)

def get_current_trade_day():
    return get_current_time()[:len("2000-01-01")]

def get_port_from_address(address):
    """
    find the port(str) in a ip address
    :param address:
    :return:
    """
    try:
        index1 = address.find("://")+1
        index2 = address.find(":", index1)+1
        port = address[index2:]
        return port
    except:
        traceback.print_exc()
        return None


def get_availabel_ip( is_tcp=False):
    """读取json得到所有默认可用的ip
    
    Arguments:
        is_tcp {bool} -- 是否是tcp模式, 默认是False(ipc模式)
    """
    json_path = get_common_parent_path("global.json")
    ip_section = "ip_section"
    ip_dict = get_json_config(file=json_path, section=ip_section)
    ip = "" #TODO
    tcp_ips = ip_dict["tcp"]
    ipc_ips = ip_dict["ipc"]
    
    if is_tcp:
        return tcp_ips
    else:
        return ipc_ips

def set_default_address(address, is_tcp=False):
    """设置json的ip配置项
    
    Arguments:
        address_list {list} -- 可用列表
        is_tcp {bool} -- 是否是tcp模式 (default: {False})
    """
    ip_section = 'ip_section'
    key = "tcp" if is_tcp else "ipc"

    json_path = get_common_parent_path("global.json")

    colon_index_1 = address.find(":")
    colon_index_2 = address.find(":",colon_index_1 + 1) + 1
    port = int(address[colon_index_2: ])
    set_json_config(file=json_path, section=ip_section, key=key, value=port)
# 时区转换 utc转换本地时间
def utc_local(utc_st):
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st

# def main():
#     # mfile = get_common_parent_path("global.json")
#     m = setup_logger(log_file_name="testname")
#     # print(get_json_config(file=mfile, section="data_proxy",key="proxy_bind_server_request"))

#     # set_json_config(file=mfile, section="te2st",key="test_key1",value="ddd")
#     # print(JSON_DICT)

def current_milli_ts() -> str:
    return str(int(time.time() * 1000))

def current_time_string() -> str:
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def add(a, b) -> str:
    return str(Decimal(a) + Decimal(b))

def sub(a, b) -> str:
    return str(Decimal(a) - Decimal(b))

def mul(a, b) -> str:
    return str(Decimal(a) * Decimal(b))

def div(a, b) -> str:
    return str(Decimal(a) / Decimal(b))


if __name__ == '__main__':
    # get_one_availabel_addr()
    pass