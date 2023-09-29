import os.path
import re
import sqlite3
from itertools import chain

from pypinyin import pinyin, Style


def record_law(table):
    conn = sqlite3.connect("LawData.db")
    cur = conn.cursor()
    cur.execute('''create table if not exists {} (title TEXT PRIMARY KEY,name TEXT,codes BLOB)'''.format(table))
    conn.commit()
    def sss(x):
        w = ""
        for i in chain.from_iterable(pinyin(x, style=Style.TONE3)):
            w = w + i
        return w

    for i in os.listdir("laws"):
        x = re.sub("[《》()（）]", "", i)
        title = sss(x[0:-4])+x[0:-4]
        cur.execute("insert into {} (title) values(?)".format(table),(title,))
        with open("laws\\"+i,"r",encoding="utf-8") as t:
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
            if len(cur.execute("pragma table_info({})".format(table)).fetchall()) - 1 == index:
                cur.execute("alter table {} add column '{}' TEXT".format(table,str(index)))
            cur.execute("update {} set '{}'='{}' where title='{}'".format(table,str(index),j,title))
            index = index + 1
        conn.commit()
        os.remove("laws\\"+i)
    conn.close()
record_law("常用法律")
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


