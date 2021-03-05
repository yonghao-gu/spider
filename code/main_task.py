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
from timer_task import init_task,CTimeTrigger,CTask

import main

def init_mail():
    config = global_obj.get("config")
    mail_data = config["mail"]
    obj = mail.CMailBox(mail_data["user"], mail_data["password"], mail_data["host"])
    obj.SetSender(mail_data["user"])
    for name in mail_data["to"]:
        obj.SetReceive(name)
    global_obj.set("mail", obj)


def add_task():
    def start_task(tobj):
        spider_beike.beike_task()
    task_timer = global_obj.get("task_timer")
    time1 = CTimeTrigger(CTimeTrigger.TDay, "21:00:00")
    taskobj1 = CTask("spider_beike", time1, start_task, run_type = CTask.TForever)
    task_timer.AddTask(taskobj1)



def main_task(config_file):
    main.init_base(config_file)
    beike_db.init_db()
    init_mail()
    init_task()
    spider_beike.init()
    log.Sys("初始化完成")
    add_task()
    taskobj = global_obj.get("task_timer")
    taskobj.RunForever()

if __name__ == "__main__":

    conf_file = "./server_config.json"
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main_task(conf_file)













