import sqlite3
import time

import requests

with open("agent.txt","r",encoding="utf-8") as t:
    agent = t.readlines()

headers = {}
conn = sqlite3.connect("newlaw.db")
cur = conn.cursor()
cur.execute('''create table if not exists newlaw (
                            name TEXT,
                            date TEXT,
                            id TEXT PRIMARY KEY
                            )''')
conn.commit()
url = "https://flk.npc.gov.cn/api/?sortTr=f_bbrq_s;desc&sort=true&last=true&page=1"
headers["user-agent"] = agent[0][0:-1]
ids = [i for i in cur.execute("select * from newlaw").fetchall()]
for i in range(10):
    if len(ids) < 10:
        t = str(time.time())
        ids.append(("","",t))
        time.sleep(0.1)
jsons = requests.get(url=url,headers=headers).json()
n = -1
for i in jsons["result"]["data"]:
    n = n + 1
    if i["title"] == ids[n][0] and i["publish"][0:10] == ids[n][1]:
        continue
    try:
        cur.execute("insert or replace into newlaw values(?,?,?)",[i["title"],i["publish"][0:10],ids[n][2]])
        with open("new", "w") as w:
            w.write("")
    except:
        pass
conn.commit()
with open("ok", "w") as w:
    w.write("")