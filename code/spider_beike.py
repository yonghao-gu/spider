# -*- coding: utf-8 -*-
'''
抓取贝壳网的信息
'''


from lxml import etree


import tools
import log
import codecs
import re
import global_obj
import csv

import thread_tool
import beike_db

from spider import get_url,new_session,url_encode,js2py_val,is_not_ok

from mailtool import mail
from mailtool import html


g_session = None

def trim_str(s):
    return s.replace("\n", "").replace(" ", "")

def __get_community_info_desc(cityName, keyword, filter_word = None):
    return "获取小区信息:<%s-%s>完成"%(cityName,keyword)

#获取小区信息
@tools.check_use_time(5, tools.global_log, __get_community_info_desc)
def get_community_info(cityName, keyword, filter_word = None):
    '''
    cityName: 城市
    keyword: 小区名
    filter_word 过滤关键字， 对region进行匹配
    @return
        返回小区列表
    '''
    global g_session

    data = {
        "cityName":cityName,
        "channel":"xiaoqu",
        "keyword": keyword,
        "query": keyword,
    }

    url = url_encode("https://ajax.api.ke.com/sug/headerSearch", data)
    result,_ = get_url(url, session = g_session)
    result_list = {}
    if is_not_ok(result) :
        log.Error("get_community_info url false", cityName, keyword, result.status_code)
        return
    result_data = js2py_val(result.content)
    if result_data["errno"] != 0:
        log.Error("get_community_info not ok", cityName, keyword)
        return result_list
    if len(result_data["data"]) == 0:
        log.Waring("get_community_info data is nil")
        return result_list
    for data in result_data["data"]["result"]:
        if filter_word and not filter_word in data["region"]:
            log.Info("get_community_info ingore by filter_word", cityName, keyword, data)
            continue
        new_data = {
            "city":cityName,
            "name" : data["text"],
            "id" : data["id"],
            "region":data["region"],
            "house_url_list" : [],
            "house_data":{},
        }
        new_data["house_url_list"] = get_house_list(data["id"])
        result_list[new_data["id"]] = new_data
    

    return result_list

__pHouseID = re.compile(".*?(\d+)\.html")




#通过小区ID找到房子
@tools.check_use_time(2, tools.global_log, "小区二手房数据用时")
def get_house_list(cid):
    url = "https://gz.ke.com/ershoufang/c%s/"%(cid)
    global g_session
    result,_ = get_url(url, session = g_session)
    if result.status_code != 200 :
        log.Waring("get_house_list url false", cid)
        return False
    
    #获取房子列表
    tree = etree.HTML(result.text)
    url_ls = tree.xpath('//div[@class="leftContent"]//ul[@class="sellListContent"]//li[@class="clear"]/a/@href')

    return url_ls


@tools.check_use_time(5, tools.global_log, "爬取房子信息超时")
def get_house_info(url, house_data):
    def get_total(data, htree):
        ls  = htree.xpath('.//div[@class="overview"]//span[@class="total"]/text()')
        if len(ls) == 0 or not tools.is_float(ls[0]):
            log.Waring("get_house_info -> get_total false")
            return
        data["价格"] = tools.tofloat(ls[0])
    
    def get_info(data, htree):
        #基本属性

        def get_info2(key):
            parttern = './div[@data-component="baseinfo"]//div[@class="introContent"]//div[@class="%s"]//ul//li'%(key)
            ls = htree.xpath(parttern)
            if len(ls) == 0:
                log.Waring("get_house_info -> get_info -> get_info2 false", key)
                return
            d = {}
            for li in ls:
                ls1 = li.xpath('./span/text()')
                if len(ls1) > 1 and trim_str(ls1[0]) == "抵押信息": #特殊处理该处信息
                    ls2 = ls1[1:]
                else:
                    ls2 = li.xpath('./text()')
                if len(ls1) == 0 or len(ls2) == 0:
                    log.Waring("get_house_info -> get_info base false", ls1, ls2)
                    continue
                k = trim_str(ls1[0])
                v = trim_str(ls2[0])
                if k == "建筑面积" or k == "套内面积":
                    v = tools.tofloat(v.replace("㎡", ""),5)
                
                data[k] = v
            #data[key] = d

        get_info2("base")
        get_info2("transaction")
        if "价格" in data and "建筑面积" in data:
            data["均价"] = tools.tofloat(float(data["价格"])/float(data["建筑面积"]),5)

    r = re.match(__pHouseID, url)
    if not r:
        log.Error("get_house_info no hid", url)
        return None
    house_info = {
        "id": r.groups()[0],
    }
    result,_ = get_url(url, session = g_session)
    if result.status_code != 200 :
        log.Waring("request house url false", url)
        return None
    htree = etree.HTML(result.text)
    
    ls = htree.xpath('//div[@class="sellDetailPage"]//div[@data-component="overviewIntro"]')
    if len(ls) > 0:
        get_total(house_info, ls[0])
    ls = htree.xpath('//div[@class="sellDetailPage"]//div[@class="m-content"]//div[@class="box-l"]')
    if len(ls) > 0:
        get_info(house_info, ls[0])
    house_data[house_info["id"]] = house_info



def send_diff_mail(diff_list):
    if len(diff_list) == 0:
        log.Info("no beike diff")
        return
    htmobj = html.CHtml("房奴调研:")
    for data in diff_list:
        htmobj.AddLine("="*30) 
        htmobj.AddLine("小区<%s>信息发生变化"%(data["name"]))
        if len(data["new"]) > 0:
            htmobj.AddLine("新增房源:")
            htmobj.AddDict2Table(data["new"])
        if len(data["del"]) > 0:
            htmobj.AddLine("有房源被删除:")
            htmobj.AddDict2Table(data["del"])
        if len(data["diff"]) > 0 :
            htmobj.AddLine("房源信息发生变化:")
            for v in data["diff"]:
                v1 = v[0]
                v2 = v[1]
                htmobj.AddLine("-"*30)
                htmobj.AddDict2Table(v)
                htmobj.AddLine("+"*30) 
        htmobj.AddLine("*"*30) 
    html_text = htmobj.GetHtml()
    mailobj = global_obj.get("mail")
    message  = mailobj.HtmlMailMessage()
    if message.SendMessage("房奴调研", html_text):
        log.Info("send beike mail done")



def check_diff(now, old):
    now_house_data = now["house_data"]
    old_house_data = old["house_data"]
    now_set = set(now_house_data.keys())
    old_set = set(old_house_data.keys())
    diff_flag = False
    result = {
        "id":now["id"],
        "name":now["name"],
        "new":[],
        "del":[],
        "diff":[],
    }
    #找出新增和删除的
    if len(now_set^old_set) != 0:
        new_list = list(now_set - old_set)
        del_list = list(old_set - now_set)
        result["new"] = [ now_house_data[hid] for hid in new_list]
        result["del"] = [ old_house_data[hid] for hid in del_list ]
        diff_flag = True
    
    def is_diff(now_data, old_data):
        for k,v in old_data.items():
            v1 = now_data.get(k, "")
            if  type(v) != type(v1) or v != v1:
                return True
        return False


    for hid, data in old_house_data.items():
        if hid in now_house_data:
            now_data = now_house_data[hid]
            if is_diff(now_data, data):
                diff_flag = True
                result["diff"].append([now_data, data])
    result["is_diff"] = diff_flag
    return result


def get_all_community(cityName):
    return []




###################### 对外接口 ######################

DATA_PATH = "./tmp/"


##将数据保存CSV
def save_community_csv(data):
    #print("data", data)
    file = DATA_PATH + "%s_%s.csv"%(data["name"], data["region"])
    f = open(file,'w', encoding="utf-8", newline='')
    writer = csv.writer(f)
    format_list = None
    for hid, house in data["house_data"].items():
        if not format_list:
            format_list = house.keys()
            writer.writerow(format_list)
        row = [ house.get(s,"") for s in format_list]
        writer.writerow(row)
    
    f.close()

@tools.check_use_time(0, tools.global_log, "保存结果用时")
def save_excel(data_list, collect = True):
    import excel_tool

    obj_list = []
    head_list = [
    "小区","id","价格","均价","建筑面积","套内面积",
    "配备电梯","挂牌时间","房屋户型","所在楼层",
    "户型结构","建筑类型","房屋朝向","建筑结构",
    "装修情况","梯户比例","交易权属","上次交易",
    "房屋用途","房屋年限","产权所属","抵押信息",
    "房本备件"
    ]
    file = DATA_PATH + "结果"
    all_list = []
    for data in data_list:
        save_data = []
        for _, house in data["house_data"].items():

            l = [ data["name"] if s == "小区" else house.get(s,"") for s in head_list]
            save_data.append(l)
            if collect:
                all_list.append(l)
            
        obj_list.append(excel_tool.CSheetObject(data["name"], head_list, save_data))
    if collect:
        obj = excel_tool.CSheetObject("汇总", head_list, all_list)
        obj_list.insert(0, obj)
    excel_tool.save_excel(file, obj_list)

@tools.check_use_time(0, tools.global_log, "所有小区新爬取完成，用时")
def start_community():
    '''
    使用多线程爬取小区
    '''
    beike_conf = global_obj.get("config")["beike"]
    task_list = []
    for data in beike_conf["spider_list"]:
        cityName = data["city"]
        if "all" in data:
            community_list = get_all_community(cityName)
        else:
            community_list = data["community"]
        filterWord = None
        if "filter" in data:
            filterWord = data["filter"]
        for cName in community_list:
            task_list.append((cityName, cName, filterWord,))
    
    task2_list = []
    data_list = []
    def _get_community_info(threadobj, cityName, cName, filterWord):
        result_list = get_community_info(cityName, cName, filterWord)
        data_list.extend(result_list.values())
        for cid, data in result_list.items():
            for url in data["house_url_list"]:
                task2_list.append((url, data["house_data"]))
            del data["house_url_list"]



    thread_tool.start_thread(_get_community_info, task_list, 5)
    log.Info("爬取小区信息完毕", len(task_list), len(task2_list))
    global g_count
    g_count = 0
    def _get_house_info(tobj, url, house_data):
        get_house_info(url, house_data)

        
    log.Info("开始爬取所有信息", len(task2_list))
    thread_tool.start_thread(_get_house_info, task2_list, 10)
    log.Info("爬取所有信息完成")
    return data_list

@tools.check_use_time(0, tools.global_log, "beike_task完成")
def beike_task():
    data_list = start_community()
    save_excel(data_list)
    log.Info("保存excel完成")

    diff_list = []
    for data in data_list:
        ret = beike_db.load_xiaoqu(data["id"])
        if ret:
            ret = check_diff(data, ret)
            if ret["is_diff"]:
                diff_list.append(ret)
        beike_db.save_xiaoqu(data["id"],data)
    log.Info("数据保存完毕")
    send_diff_mail(diff_list)



def init():
    #需要先获得cookies后再执行其他请求
    global g_session
    g_session = new_session()
    url = "https://gz.ke.com/?utm_source=baidu&utm_medium=pinzhuan&utm_term=biaoti&utm_content=biaotimiaoshu&utm_campaign=wyguangzhou"
    result,g_session = get_url(url, session = g_session)


################ 测试 ###########################

@tools.check_use_time(1, tools.global_log)
def test():
    #result = get_community_info("广州", "新天美地")
    
    file = "./tmp/新天美地花园_ 荔城富鹏_增城.csv"
    writer = csv.writer(open(file,'w', encoding="utf-8", newline=''))
    writer.writerow(("a","b","c"))
    writer.writerow(("a","b","c"))
    writer.writerow(("sssa","ddb","cff"))















