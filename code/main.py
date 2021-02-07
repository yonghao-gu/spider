# -*- coding: utf-8 -*-
import sys
import os
#公共库
libpath = os.path.abspath("./lib")
sys.path.append(libpath)


import spider_beike
import log
import global_obj
import config_op

def init_log(filename = None):
    obj = log.CFileLog(filename)
    global_obj.set("logger", obj)

def init_config(config_file):
    data = config_op.load_config(config_file)
    global_obj.set("config", data)




def main(config_file):
    init_config(config_file)
    init_log()

    spider_beike.init()

    spider_beike.start_community()
    #spider_beike.test()
    log.Sys("start ok")




if __name__ == "__main__":

    conf_file = "./server_config.json"
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main(conf_file)
