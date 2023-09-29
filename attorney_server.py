import os
import pickle
import socket
import sqlite3
import struct
import sys
import threading
import time

from PyQt5.QtCore import QObject, QMutex
from PyQt5.QtNetwork import QUdpSocket, QHostAddress, QLocalSocket, QLocalServer
from PyQt5.QtWidgets import QApplication


with open("profile.bt", "rb") as t:
    me = pickle.loads(t.read())
database = me["workspace"] + "\\" +"database.db"

def checktable():
    conn = sqlite3.connect(database)
    cur = conn.cursor()
    tables = [i[0] for i in cur.execute("select name from sqlite_master where type='table'").fetchall()]
    c = 0
    if "日志" not in tables:
        cur.execute('''create table if not exists 日志 (id TEXT PRIMARY KEY,startdate TEXT,
                            caseid TEXT,logname TEXT,what TEXT,enddate TEXT,assitant TEXT)''')
        c = 1
    if "案件" not in tables:
        cur.execute('''create table if not exists 案件 (id TEXT PRIMARY KEY,casename TEXT,paid TEXT,claims TEXT,reasons TEXT,
                            mark TEXT,startdate TEXT,enddate TEXT,assistant TEXT,
                            plaintiff BLOB,defendant BLOB,third BLOB,cause BLOB,court BLOB,judge BLOB)''')
        c = 1
    if "收藏" not in tables:
        cur.execute('''create table if not exists 收藏 (id TEXT PRIMARY KEY,editdate TEXT,theme TEXT,content TEXT)''')
        c = 1
    if "用户" not in tables:
        cur.execute("create table if not exists 用户 (id TEXT PRIMARY KEY,name TEXT,img BLOB)")
        c = 1
    if "法务" not in tables:
        cur.execute('''create table if not exists 法务 (id TEXT PRIMARY KEY,name TEXT,business TEXT,contacts TEXT,
                            address TEXT,startdate TEXT,enddate TEXT,meal BLOB,paid TEXT,assitant TEXT,company TEXT,marks TEXT)''')
        c = 1
    if c == 1:
        conn.commit()
    conn.close()


class Server(QObject):

    def __init__(self):
        super().__init__()
        try:
            self.socketT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socketT.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socketT.bind(("0.0.0.0", 6666))
            self.socketT.listen(10)
        except:
            app.quit()

        self.mutex = QMutex()

        self.sendserverip = QUdpSocket(self)
        self.sendserverip.bind(QHostAddress.Any, 6665)
        self.sendserverip.readyRead.connect(self.send_serverip)

        thread = threading.Thread(target=self.startread, args=())
        thread.start()

    def send_serverip(self):
        while self.sendserverip.hasPendingDatagrams():
            datagram, host, port = self.sendserverip.readDatagram(
                self.sendserverip.pendingDatagramSize()
            )
            self.sendserverip.writeDatagram(datagram,host,8848)

    def record_database(self,words, *args,hebing=True):
        n = 0
        while not self.mutex.tryLock():
            if n == 3000:
                return -1
            time.sleep(0.001)
            n+=1
        datas = []
        args = list(args)
        if "fenkai" in words:
            hebing = False
            words.remove("fenkai")
        for i in range(len(words)-len(args)):
            args.append(tuple())
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        for sql,arg in zip(words,args):#sql和数据按顺序对应
            try:
                if "manysql " in sql:
                    cur.executemany(sql.replace("manysql ",""),arg)
                else:
                    cur.execute(sql, arg)
            except:
                continue
            if "select" in sql:
                data = cur.fetchall()
                if hebing:
                    datas = datas + data
                else:
                    datas.append(data)
            else:
                conn.commit()
                time.sleep(0.01)
        conn.close()
        self.mutex.unlock()
        return datas

    def startread(self):
        while 1:
            # 等待请求并接受(程序会停留在这一旦收到连接请求即开启接受数据的线程)
            socketT, addr = self.socketT.accept()
            # 接收数据
            t = threading.Thread(target=self.read_data_slot, args=(socketT, ))
            t.start()

    def sendnew_app(self,socketT):
        files = os.listdir(me["workspace"] + "\\update")
        if not os.path.exists(me["workspace"] + "\\update") or len(files) == 0:
            socketT.send(b'none')
            return
        def walk(dirs,files):
            for file in files:
                file = dirs + "\\" + file
                if os.path.isdir(file):
                    walk(file,os.listdir(file))
                    continue
                size = os.stat(file).st_size
                # size = os.path.getsize(file)
                head = struct.pack('512sq', file.replace(me["workspace"] + "\\update\\","").encode('utf-8'), size)
                socketT.send(head)
                with open(file,"rb") as d:
                    while 1:
                        data = d.read(2048)
                        if not data:
                            break
                        socketT.send(data)
        walk(me["workspace"] + "\\update",files)
        socketT.send(b'ok')

    def read_data_slot(self,socketT):# 数据格式：[sql命令,散开的数据]
        data = b''
        while True:
            try:
                size = struct.calcsize('512sq')
                head = socketT.recv(size)
                if head == b'update':
                    self.sendnew_app(socketT)
                    break
                if head:
                    n, leng = struct.unpack('512sq', head)
                    while leng != len(data):
                        if leng - len(data) > 2048:
                            data = data + socketT.recv(2048)
                        else:
                            data = data + socketT.recv(leng - len(data))
                    sql = pickle.loads(data)
                    datas = pickle.dumps(self.record_database(*sql))
                    leng = len(datas)
                    head = struct.pack('512sq', b'',leng)
                    socketT.send(head)
                    for start in range(0,leng,2048):
                        socketT.send(datas[start:start + 2048])
                    break
            except:
                break
            time.sleep(0.01)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        ip = QHostAddress(sys.argv[-1])
    else:
        ip = QHostAddress.Broadcast
    QUdpSocket().writeDatagram(b'ip',ip,8848)
    serverName = 'attorneyServer'
    socketT = QLocalSocket()
    socketT.connectToServer(serverName)
    # 判定应用服务是否正常链接，如正常则证明程序实例已经在运行
    if socketT.waitForConnected(500):
        pass
    else:
        checktable()
        app = QApplication(sys.argv)
        localServer = QLocalServer()
        localServer.listen(serverName)
        server = Server()
        sys.exit(app.exec_())

