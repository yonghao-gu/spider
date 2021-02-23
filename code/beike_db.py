# -*- coding: utf-8 -*-

import global_obj
import mongo

colname = "beike_data"

def init_db():
    config = global_obj.get("config")
    db_data = config["db"]
    obj = mongo.CMongodbManager("jiucai", db_data["addr"], db_data["port"], db_data["user"], db_data["password"])
    global_obj.set("dbobj", obj)
    init_db_index()

def init_db_index():
    dbobj = global_obj.get("dbobj")
    dbobj.CreateIndex(colname, "id")


def load_xiaoqu(cid):
    dbobj = global_obj.get("dbobj")
    col = dbobj.Collection(colname)
    ret = col.find_one({"id": cid}, {"_id":0})
    return ret


def save_xiaoqu(cid, data):
    dbobj = global_obj.get("dbobj")
    col = dbobj.Collection(colname)
    col.update({"id":cid}, data, upsert = True )















