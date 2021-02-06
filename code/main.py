# -*- coding: utf-8 -*-
import sys
import os
#公共库
libpath = os.path.abspath("./lib")
sys.path.append(libpath)


import log
import global_obj

def init_log(filename = None):
    obj = log.CFileLog(filename)
    global_obj.set_obj("logger", obj)


def main(config_file):
    init_log()

    log.Sys("start ok")




if __name__ == "__main__":

    conf_file = None
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main(conf_file)
