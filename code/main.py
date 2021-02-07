# -*- coding: utf-8 -*-
import sys
import os
#公共库
libpath = os.path.abspath("./lib")
sys.path.append(libpath)


import spider_beike
import log
import global_obj


def init_log(filename = None):
    obj = log.CFileLog(filename)
    global_obj.set_obj("logger", obj)

def init_config(config_file):
    data = config_api.load_config(config_file)
    global_obj.set_obj("config", data)




def main(config_file):
    init_log()

    spider_beike.init()
    spider_beike.test()

    log.Sys("start ok")




if __name__ == "__main__":

    conf_file = None
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main(conf_file)
