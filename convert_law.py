import os.path
import re
import sqlite3
import time
from itertools import chain

from pypinyin import pinyin, Style

conn = sqlite3.connect("LawData.db")
cur = conn.cursor()
# cur.execute('''create table if not exists 行政法规 (title TEXT PRIMARY KEY)''')
# conn.commit()
# conn.close()
# exit()

def sss(x):
    w = ""
    x = re.sub("[《》（）]")
    for i in chain.from_iterable(pinyin(x, style=Style.TONE3)):
        w = w + i[0:-1]
    return w

for i in os.listdir("行政法规"):
    title = sss(i[0:-4])+i[0:-4]
    cur.execute("insert into 行政法规 (title) values(?)",(title,))
# print(cur.execute('select id,title from 行政法规 where "0"=').fetchall())
# for i in cur.execute('select id,title from 行政法规 where "0"=""').fetchall():
    with open("行政法规\\"+i,"r",encoding="utf-8-sig") as t:
        codes = t.readlines()
    law = [""]
    for code in codes:
        if code == "\n":
            continue
        if re.search("(^第.+?[条节章编][、.\s]*)|(^[0-9一二三四五六七八九十]+[、.\s]+)", code) is not None:
            law.append(code)
        else:
            law[-1] = law[-1] + code
    index = 0
    law = law[1:]
    for j in law:
        if len(cur.execute("pragma table_info(行政法规)").fetchall()) - 1 == index:
            cur.execute("alter table 行政法规 add column '{}' TEXT".format(str(index)))
        cur.execute("update 行政法规 set '{}'='{}' where title='{}'".format(str(index),j,title))
        index = index + 1
    conn.commit()
conn.close()
# for i in cur.fetchall():
#     file = re.sub("[\s\n<>]*","",i[0])+".docx"
#     if os.path.exists(os.getcwd()+"\\234\\"+file):
#         shutil.move(os.getcwd()+"\\234\\"+file,os.getcwd()+"\\345\\"+i[1]+"\\"+file)
# word = wc.Dispatch("Word.Application")
# for i in os.listdir("123\\"):
#     name = i.replace(" ", "")
#     if " " in i:
#         shutil.move(os.getcwd()+"\\123\\"+i, os.getcwd()+"\\123\\"+name)
#     i = name# os.remove(i)
#     if i.endswith(".docx"):
#         continue
#     f_e = os.path.splitext(i)
#     if f_e[0] in rep:
#         continue
#     file = os.getcwd()+"\\234\\" + f_e[0].split("\\")[-1] + ".docx"
#     if os.path.exists(file):
#         continue
#     try:
#         doc = word.Documents.Open(os.getcwd()+"\\123\\"+i)
#         doc.SaveAs(file, 12)
#         doc.Close()
#         i = file
#     except Exception as e:
#         print(e,i)
#         continue
# word.Quit()


