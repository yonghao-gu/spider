# -*- coding: utf-8 -*-
'''
抓取贝壳网的信息
'''


from lxml import etree

import spiker
import tools
import log
import codecs
import re

from spiker import get_url,new_session,url_encode,js2py_val

g_session = None




#获取小区信息
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
    result_data = js2py_val(result.content)
    result_list = []
    if result_data["errno"] != 0:
        log.Error("get_community_info not ok", cityName, keyword)
        return result_list

    for data in result_data["data"]["result"]:
        if filter_word and not filter_word in data["region"]:
            log.Info("get_community_info ingore by filter_word", cityName, keyword, data)
            continue
        new_data = {
            "name" : data["text"],
            "id" : data["id"],
            "house_data" : {},
        }
        get_house_list(data["id"])
        result_list.append(new_data)
    

    return result_list

__pHouseID = re.compile(".*?(\d+)\.html")


def trim_str(s):
    return s.replace("\n", "").replace(" ", "")

#通过小区ID找到房子
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

    #摘取房子信息
    house = {}

    def get_total(data, htree):
        ls  = htree.xpath('.//div[@class="overview"]//span[@class="total"]/text()')
        if len(ls) == 0 or not tools.is_float(ls[0]):
            log.Waring("get_house_list -> get_total false")
            return
        data["total"] = tools.tofloat(ls[0])
    
    def get_info(data, htree):
        #基本属性

        def get_info2(key):
            parttern = './div[@data-component="baseinfo"]//div[@class="introContent"]//div[@class="%s"]//ul//li'%(key)
            ls = htree.xpath(parttern)
            if len(ls) == 0:
                log.Waring("get_house_list -> get_info -> get_info2 false", key)
                return
            d = {}
            for li in ls:
                ls1 = li.xpath('./span/text()')
                if len(ls1) > 0 and trim_str(ls1[0]) == "抵押信息": #特殊处理该处信息
                    ls2 = li.xpath('./span/span/text()')
                else:
                    ls2 = li.xpath('./text()')
                if len(ls1) == 0 or len(ls2) == 0:
                    log.Waring("get_house_list -> get_info base false")
                    continue
                k = trim_str(ls1[0])
                v = trim_str(ls2[0])
                d[k] = v
            data[key] = d

        get_info2("base")
        get_info2("transaction")


    result_map = {}
    for url in url_ls:
        r = re.match(__pHouseID, url)
        if not r:
            log.Error("get_house_list no hid", url)
            continue
        data = {
            "id": r.groups()[0],
        }
        result,_ = get_url(url, session = g_session)
        if result.status_code != 200 :
            log.Waring("request house url false", url)
            continue
        htree = etree.HTML(result.text)
        
        ls = htree.xpath('//div[@class="sellDetailPage"]//div[@data-component="overviewIntro"]')
        if len(ls) > 0:
            get_total(data, ls[0])
        ls = htree.xpath('//div[@class="sellDetailPage"]//div[@class="m-content"]//div[@class="box-l"]')
        if len(ls) > 0:
            get_info(data, ls[0])
        result_map[data["id"]] = data
    
    return result_map



###################### 对外接口 ######################





@tools.check_use_time(30, tools.global_log, "start")
def start():
    pass



@tools.check_use_time(30, tools.global_log, "start_community")
def start_community():
    pass



def init():
    #需要先获得cookies后再执行其他请求
    global g_session
    g_session = new_session()
    url = "https://gz.ke.com/?utm_source=baidu&utm_medium=pinzhuan&utm_term=biaoti&utm_content=biaotimiaoshu&utm_campaign=wyguangzhou"
    result,g_session = get_url(url, session = g_session)


################ 测试 ###########################

@tools.check_use_time(1, tools.global_log)
def test():
    get_community_info("广州", "新天美地")

















