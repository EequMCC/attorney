import os.path
import pickle
import re
import sqlite3
import time
from itertools import chain

from pypinyin import pinyin, Style


def convert_to_bytes(table,laws):
    def sss(x):
        w = ""
        for i in chain.from_iterable(pinyin(x, style=Style.TONE3)):
            w = w + i
        return w

    conn = sqlite3.connect("LawData.db")
    cur = conn.cursor()
    cur.execute('''create table if not exists {} (title TEXT PRIMARY KEY,name,codes BLOB)'''.format(table))
    conn.commit()

    for title in laws.keys():
        x = title.replace("人民代表大会","人大").replace("常务委员会","常委")
        x =  re.sub("(中华人民共和国)|(最高人民法院)|(最高人民检察院)|(关于)|(适用)|(办理)|(审理)|(的)","",x)
        x = re.sub("[\W]*", "", x)
        name = sss(x)+x
        codes = laws[title]
        law = [""]
        for code in codes:
            if re.search("(^第.+?[条节章编]\s+?)|(^[0-9一二三四五六七八九十]+[\W\s]+?)", code) is not None:
                law.append(code)
            else:
                law[-1] = law[-1] + code
        law = law[1:]
        cur.execute("insert or replace into {} (title,name,codes) values(?,?,?)".format(table), (title,name,pickle.dumps(law)))
        conn.commit()
        time.sleep(0.1)
    conn.close()


def opentxt(file):
    try:
        with open(file, "r", encoding="utf-8-sig") as t:
            codes = t.readlines()
    except:
        try:
            with open(file, "r", encoding="utf-8") as t:
                codes = t.readlines()
        except:
            try:
                with open(file, "r") as t:
                    codes = t.readlines()
            except:
                codes = []

    return codes


def record_law(table,files):
    no_law = ""
    laws = {}
    for i in files:
        i = i.replace("/","\\")
        f_e = os.path.splitext(i)
        ok = kk = 0
        zjp = []
        txt = f_e[0].split("\\")[-1]
        law_txt = []
        codes = opentxt(i)
        for j in codes:
            if re.search("^\n+$",j) is not None:
                continue
            t = re.sub("\s+"," ",re.sub("^\s+","",j)) + "\n"
            c = re.findall("^第.+?([编章节])\s+?", t)
            if kk == 0 and len(c) > 0:
                if c[0] not in zjp:
                    zjp.append(c[0])
                    law_txt.append(t)
                    continue
                else:
                    kk = 1
            if re.search("(^第.+?条\s+?)|(^[0-9一二三四五六七八九十][\W\s]+?)",t) is not None:
                ok = 1
            if ok == 1:
                law_txt.append(t)
        if len(law_txt) != 0:
            laws[txt] = law_txt
        else:
            no_law = no_law + f_e[0]+"\n"

    if no_law != "":
        with open("nolaw.bt","wb") as t:
            t.write(pickle.dumps(no_law))
    convert_to_bytes(table, laws)

    os.remove("newlaw.bt")

n = 0
while True:
    if n == 60:
        break
    if not os.path.exists("newlaw.bt"):
        time.sleep(1)
        n = n + 1
        continue
    with open("newlaw.bt","rb") as t:
        files = pickle.loads(t.read())
    for i in files.keys():
        record_law(i,files[i])
    break

