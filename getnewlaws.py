import os
import pickle
import re
import sqlite3
import time
from datetime import datetime

import requests
from PyQt5.QtNetwork import QUdpSocket, QHostAddress

with open("agent.txt","r",encoding="utf-8") as t:
    agent = t.readlines()
if int(agent[0][0:-1]) == len(agent)-1:
    index = str(1)+"\n"
else:
    index = str(int(agent[0][0:-1])+1)+"\n"
with open("agent.txt","w",encoding="utf-8") as t:
    t.write(index+"".join(agent[1:]))

headers = dict()
headers["user-agent"] = agent[int(agent[0][0:-1])][0:-1]

ids1 = {"国家法律法规数据库": [], "最高法": [], "国务院行政法规库": [], "最高检": []}
ids2 = {"国务院最新政策": [], "四川省政府公报": [], "绵阳市政府公报": []}

for db,idw in zip(["newlaw.db","gongbao.db"],[ids1,ids2]):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    for i in idw.keys():
        cur.execute('''create table if not exists {} (
                                    name TEXT,
                                    date TEXT,
                                    url TEXT,
                                    id INTEGER PRIMARY KEY
                                    )'''.format(i))
        idw[i] = [k[0]+k[1] for k in cur.execute("select name,date from {}".format(i)).fetchall()]
    conn.commit()

def convertdate(txt):
    return datetime.strptime(txt,"%Y-%m-%d").strftime("%Y-%m-%d")

def getnewdata(i,x,y,z):#获取单条数据的函数
    if i[y] !="" and re.search('[0-9]+-[0-9]+-[0-9]+',i[y]) is None:#判断日期格式是否符合规范
        i[y] = convertdate(re.sub('-*$','',re.sub("[年月\\\.日/]","-",i[2])))

    return {"title": i[x], "publish": i[y], "url": i[z]}

def gethtml(url):
    try:
        html = requests.get(url=url,headers=headers).content
        with open("ttt.html", "wb") as t:
            t.write(html)
        with open("ttt.html", "r", encoding="utf-8") as t:
            html = t.read()
        os.remove("ttt.html")
        return html
    except:
        return "啥也没有"

def getnewdict(urls,compiles,ids,order):#主函数
    dicts = dict()
    for url,com,key,o in zip(urls,compiles,ids.keys(),order):
        if com == "":#不用正则截取的链接
            try:
                jsons = requests.get(url=url,headers=headers).json()
                dicts[key] = jsons["result"]["data"][0:10]
            except:
                dicts[key] = []
        else:
            try:
                if re.search("^dao\s",url) is None:
                    jsons = re.findall(com, gethtml(url), re.S)[0: 10]#找最开始还是最后
                else:
                    url = re.sub("^dao\s","",url)
                    jsons = re.findall(com, gethtml(url), re.S)[-10:]
                dicts[key] = [getnewdata(list(i),*o) for i in jsons]
            except:
                dicts[key] = []
    return dicts

a = ["https://flk.npc.gov.cn/api/?sortTr=f_bbrq_s;desc&sort=true&last=true&page=1","https://www.court.gov.cn/fabu/gengduo/16.html",
    "http://xzfg.moj.gov.cn/search2.html","https://www.spp.gov.cn/spp/flfg/sfjs/index.shtml"]#显示在程序左侧的页面链接，按ids字典的key顺序放
b = ['',
     '<li>.*?<a title="(.*?)".*?target.*?href="(.*?)".*?class="date">(.*?)</i>',
     '<a target="_blank" href="(.*?)">(.*?)</a>.*?([0-9].*?)公布',
     '				<li><a href="(.*?)" target="_blank"  >(.*?)</a><span>(.*?)</span></li>']#截取标题时间链接的规则
c = ids1
d = [[0,0,0],[0,2,1],[1,2,0],[1,2,0]]#标题时间链接的位置
newlaws = getnewdict(a,b,c,d)

a = ["https://www.gov.cn/zhengce/zuixin","","dao http://www.my.gov.cn/zwgk/gongbao/2023nzfgb/"]#显示在程序右侧的网站主链接，按ids字典的key顺序放
b = ['<li>.*?<h4>.*?<a href="(.*?)" target="_blank">(.*?)</a>.*?<span class="date">(.*?)</span>',
     '"left">\s*<a href="(.*?)"[\n\s]*target="_blank"[\n\s]*class="yh_14heix">(.*?)</a>()\s',
    '<li class=.*?>[.\s]*<a href="(.*?)" target="_blank" title="(.*?)>[\s\n.\t\W\S]*?<span class="date">(.*?)</span>']#截取标题时间链接的规则
c = ids2
d = [[1,2,0],[1,2,0],[1,2,0]]#标题时间链接的位置
findnew = re.findall('<li>\s+<a href="(.*?)" target="', gethtml("https://www.sc.gov.cn/10462/c103109/zwgklist00.shtml"))#进一步获取链接
if len(findnew) == 0:
    findnew = [""]
a[1] = findnew[0]
gongbao = getnewdict(a,b,c,d)

pre1 = ["https://flk.npc.gov.cn/","https://www.court.gov.cn/","",""]#newlaws前面要加的链接
pre2 = ["https://www.gov.cn/zhengce/","https://www.sc.gov.cn/",""]#gongbao前面要加的链接
#写新标题
newlawSend = QUdpSocket()
new = []
title = ""
for db,idw,data,pres in zip(["newlaw.db","gongbao.db"],[ids1,ids2],[newlaws,gongbao],[pre1,pre2]):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    for table,pre in zip(idw.keys(),pres):#table代表每个网站名称，与主链接和前面要加的链接对应
        n = 0
        if len(data[table]) == 0:
            title = title + table+"<br>"
            continue
        for i in data[table]:#i代表每一组title,publish,url字典
            if n == 10:
                break
            i["title"] = re.sub("[\W\s\n\t]", "", i["title"])
            if re.search('^[\\\./]+', i["url"]) is not None:  # 判断开头是否符合url规范
                i["url"] = re.sub('^[\\\./]+', "", i["url"])
                i["url"] = pre + i["url"]
            cur.execute("insert or replace into {} values(?,?,?,?)".format(table),
                        [i["title"], i["publish"][0:10], i["url"], n])
            if i["publish"] == "":
                date = ""
            else:
                date = i["publish"][0:10]
            if i["title"] + date not in idw[table]:
                new.append(i["title"])
            n = n + 1
        conn.commit()
    conn.close()
if len(title) != 0:
    title = "无法获取最新数据：<br><font color='#DB3022'>{}</font>".format(title) + "请检查网络或更新组件！"
    newlawSend.writeDatagram(pickle.dumps(title), QHostAddress.LocalHost, 8849)
    time.sleep(0.5)
newlawSend.writeDatagram(pickle.dumps(new),QHostAddress.LocalHost, 8849)