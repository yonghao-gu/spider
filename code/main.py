# -*- coding: utf-8 -*-
import sys
import os
#公共库
libpath = os.path.abspath("./lib")
sys.path.append(libpath)

from mailtool import mail
import spider_beike
import log
import global_obj
import config_op
import beike_db


def init_log(filename = None):
    obj = log.CFileLog(filename)
    global_obj.set("logger", obj)

def init_config(config_file):
    data = config_op.load_config(config_file)
    global_obj.set("config", data)


def init_mail():
    config = global_obj.get("config")
    mail_data = config["mail"]
    obj = mail.CMailBox(mail_data["user"], mail_data["password"], mail_data["host"])
    obj.SetSender(mail_data["user"])
    for name in mail_data["to"]:
        obj.SetReceive(name)
    global_obj.set("mail", obj)



def init_base(config_file):
    init_config(config_file)
    init_log()

def main(config_file):
    init_base(config_file)
    beike_db.init_db()
    init_mail()
    spider_beike.init()

    spider_beike.beike_task()
    #spider_beike.start_community()

    log.Sys("start ok")




if __name__ == "__main__":

    conf_file = "./server_config.json"
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main(conf_file)
