import pickle
import re
import sqlite3
import webbrowser
from itertools import chain

import requests


def record_database(word, *arg, db="workspace\\database.db"):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        cur.execute(word, arg)
    except Exception as e:
        print(e)
        return 0
    if "select" in word:
        return cur.fetchall()
    if re.search("(insert)|(delete)|(create)|(update)", word) is not None:
        conn.commit()
        conn.close()
    return 1

# ii = [1]
# ii.insert(1,2)
# print(ii)
html = requests.get(url="http://xzfg.moj.gov.cn/search2.html").content
with open("txt.html", "wb") as t:
    t.write(html)
# record_database("alter table aa rename to 案件 ")
exit(0)
fetchall = record_database("select 法务.*,max(日志.startdate) from 法务 join 日志 on 法务.id=日志.caseid group by 法务.id order by 法务.enddate desc")
for i in fetchall:
    print(len(i),i[1],i[-1])
exit(0)
fetchall = record_database("select id,casename,paid,claims,reasons,mark,startdate,enddate,assistant,plaintiff,defendant,third,cause,court,judge from 案件")
for i in fetchall:
    i = list(i)
    # i.insert(2,"")
    # i.insert(7,re.findall("^[0-9-]+",i[1])[0][0:10])
    # i[1] = re.sub("^[\s0-9-]+","",i[1])
    # i[3] = "\n".join([i[1] for i in pickle.loads(i[3])])
    record_database("insert or replace into aa (id,casename,paid,claims,reasons,mark,startdate,enddate,assistant,plaintiff,defendant,third,cause,court,judge) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",*i)