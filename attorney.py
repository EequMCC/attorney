import calendar
import cgitb
import imghdr
import os
import pickle
import re
import shutil
import socket
import sqlite3
import struct
import sys
import time
import winreg
import datetime
from functools import partial
from itertools import chain
from subprocess import run

import requests
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QRect, QRunnable, QThreadPool
from PyQt5.QtGui import QTextCursor, QFont, QColor, QCursor, QPixmap
from PyQt5.QtNetwork import QUdpSocket, QHostAddress, QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QMenu, QApplication, QTreeWidgetItem, QFileDialog, QInputDialog, QWidgetAction

from ui import *


class TcpSocket(QThread):
    ip = ""
    sql = []

    def __init__(self):
        super(TcpSocket, self).__init__()
        self.receiv_finished = False
        self.datas = b''
        self.socketT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            if self.socketT.connect_ex((self.ip, 6666)) != 0:
                return
            datas = pickle.dumps(self.sql)
            leng = len(datas)
            head = struct.pack('512sq', b'', leng)
            self.socketT.send(head)
            for start in range(0, leng, 2048):
                self.socketT.send(datas[start:start + 2048])
        except:
            return

        while True:
            try:
                size = struct.calcsize('512sq')
                leng = self.socketT.recv(size)
                if leng:
                    n, leng = struct.unpack('512sq', leng)
                    while leng != len(self.datas):
                        if leng - len(self.datas) > 2048:
                            self.datas = self.datas + self.socketT.recv(2048)
                        else:
                            self.datas = self.datas + self.socketT.recv(leng - len(self.datas))
                    self.receiv_finished = True
                    self.socketT.close()
                    break
            except:
                break
            time.sleep(0.01)


class Thread(QRunnable):

    def __init__(self, fun, *arg):
        super(Thread, self).__init__()
        self.fun = fun
        self.arg = arg

    def run(self):
        self.fun(*self.arg)


class MyThread(QThread):
    mysig1 = pyqtSignal()

    def __init__(self, *fun):
        super(MyThread, self).__init__()
        self.fun = fun

    def run(self):
        if len(self.fun) == 1:
            self.fun[0]()
        else:
            self.fun[0](*self.fun[1:])
        self.mysig1.emit()


class Attorney(MyWin):
    do_something_sig = pyqtSignal(list)

    def __init__(self):
        super(Attorney, self).__init__()
        self.fetchall = []
        self.all_laws = dict()
        self.me = {"id": "", "姓名": "\n0", "头像": b'', "workspace": "", "show": "法律"}
        self.allmeals = dict()
        self.current_log = [""] * 8
        self.current_case = [""] * 9 + [[["", "", ""]] for _ in range(6)]
        self.current_client = [""] * 7 + [pickle.dumps(["", dict()])] + [""] * 4
        self.working_data = [""] * 6
        self.current_collect = []
        self.alllaw_items = dict()
        self.law_items = []
        self.find_lawitems = []
        self.newlaw = []
        self.current_lawitem = None
        self.lastlogitem = None
        self.lastfoun = None
        self.abort = False
        self.current_items = dict()
        self.clipboard = QApplication.clipboard()
        self.lineedit_menu = None
        self.mutex = QMutex()
        self.these = []
        self.serverip = None

        self.thread_pool = QThreadPool()
        self.thread_pool.globalInstance()

        self.add_law_thread = MyThread(self.add_law)
        self.showlaw_thread = MyThread(self.append_law)
        self.find_thread = MyThread(self.find_in_all)

        self.flash_law_thread = MyThread(self.load_alllaws)

        self.anyhost_udp = QUdpSocket(self)
        self.anyhost_udp.bind(QHostAddress.Any, 8848)
        self.anyhost_udp.readyRead.connect(self.anyhost_func)

        self.localhost_udp = QUdpSocket(self)
        self.localhost_udp.bind(QHostAddress.LocalHost, 8849)
        self.localhost_udp.readyRead.connect(self.localhost_func)

        with open("style.qss", "r") as t:
            self.stylesheet = t.read()
        self.main_button_style = '''
            QPushButton {
                background-color:transparent;
                border:none;
                border-radius:12px;
                font-size:18px;
            }
            QPushButton:hover {
                background-color:rgb(193, 233, 242);
                border:none;
            }
            QPushButton:pressed {
                background-color:rgb(148, 216, 233);
                border:none;
            }'''

    def initialite(self):
        self.setStyleSheet(self.stylesheet)
        # self.paper.setStyleSheet("QSpinBox::up-button {subcontrol-position:bottom right;}QSpinBox::down-button {subcontrol-position:top right;}")
        self.setting_win.setStyleSheet(self.stylesheet)
        self.more_inf_txt.setStyleSheet(self.stylesheet)
        self.reson_txt.setStyleSheet(self.stylesheet)

        def selectfile(t):
            if t == 2:
                file = \
                QFileDialog.getOpenFileName(self, "选择图片", os.path.expanduser('~'), '图片文件 (*.png *.jpg *.jpeg)')[
                    0]
            else:
                file = QFileDialog.getExistingDirectory(self, "选择文件夹", os.path.expanduser('~'))
            if file != "":
                self.setting_layout.itemAt(t, 1).widget().setText(file.replace("/", "\\"))

        self.setting_layout.itemAt(2, 1).widget().actions()[0].triggered.connect(lambda: selectfile(2))
        self.setting_layout.itemAt(3, 1).widget().actions()[0].triggered.connect(lambda: selectfile(3))

        self.setting_layout.itemAt(5, 1).layout().itemAt(1).widget().clicked.connect(lambda: self.setting(1))
        self.setting_layout.itemAt(5, 1).layout().itemAt(2).widget().clicked.connect(lambda: self.setting(2))
        self.setting_layout.itemAt(5, 1).layout().itemAt(3).widget().clicked.connect(lambda: self.setting(3))
        self.setting_layout.itemAt(5, 1).layout().itemAt(4).widget().clicked.connect(self.anyhost_func)
        self.setting_layout.itemAt(5, 1).layout().itemAt(5).widget().clicked.connect(app.quit)

        self.do_something_sig.connect(self.do_something)
        if os.path.exists("profile.bt"):
            with open("profile.bt", "rb") as t:
                self.me = pickle.loads(t.read())
            if len(self.me["姓名"].split("\n")) < 2:
                self.me["姓名"] = self.me["姓名"] + "\n0"
                with open("profile.bt", "wb") as t:
                    t.write(pickle.dumps(self.me))
            self.set_me()
        else:
            self.setting_show()

        self.setfounstyle(self.me["show"][0:2])
        if sys.argv[-1] != "no":  # 快捷图标启动时带的参数no表示不显示界面
            self.show()
        if os.path.exists(self.me["workspace"] + "\\meals"):
            with open(self.me["workspace"] + "\\meals", "rb") as t:
                self.allmeals = pickle.loads(t.read())
        l = [list(i.keys()) for i in self.allmeals.values()]
        l = list(chain.from_iterable(l))
        self.log_name.addItems(set(l))
        self.log_name.addItems(["提供模板", "法律咨询", "电话回访", "单项服务"])

        self.user.clicked.connect(self.setting_show)
        self.files_button.setStyleSheet(self.main_button_style)
        for i in [2, 3, 4, 5, 6, 8, 10]:
            widget = self.vbox1.itemAt(i).widget()
            widget.clicked.connect(partial(self.which_founction, widget.text()))
            if i == 8:
                continue
        self.flash_law_thread.start()

        def theses():
            these = re.sub("(^\s*)|(\s*$)", "", self.search.text()).split(" ")
            for i in these:
                if i == "":
                    these.remove(i)
            self.these = these

        self.search.textChanged.connect(theses)
        self.search.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search.returnPressed.connect(self.find_prepare)
        self.search.actions()[0].triggered.connect(self.add_new)
        self.search.actions()[1].triggered.connect(self.find_prepare)
        self.search.actions()[2].triggered.connect(
            lambda: os.startfile("https://cn.bing.com/search?q=" + self.search.text()))
        for i in range(6):
            checkbox = self.search_which.itemAt(i).widget()
            if checkbox.text() in self.me["show"]:
                checkbox.setCheckState(Qt.Checked)
            checkbox.clicked.connect(self.find_prepare)

        self.main_tree.itemClicked.connect(self.show_one)
        self.main_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_tree.customContextMenuRequested.connect(self.tree_menu)
        self.main_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.tree_case.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        def starturl():
            os.startfile(self.sender().currentItem().data(0, Qt.UserRole))
            self.sender().currentItem().setForeground(0, QColor(Qt.black))
            name = re.sub("^.*?\s", "", self.sender().currentItem().text(0))
            if name in self.newlaw:
                self.newlaw.remove(name)
            if len(self.newlaw) == 0:
                self.newlaw_label.setVisible(False)

        self.guojia.clicked.connect(starturl)
        self.sheng.clicked.connect(starturl)
        self.shi.clicked.connect(starturl)

        def showlog():
            log = self.have_done.currentItem().data(0, Qt.UserRole)[1]
            if log == 0:
                return
            if log is None:
                return
            self.show_log.setVisible(True)
            if log[-1] is None:
                assi = log[6]
            else:
                assi = re.sub("\n[0,1]*", "", log[-1])
            self.show_log.setPlainText(
                "计划日：" + str(log[1]) + "\n结束日：" + str(log[5]) + "\n办理人：" + str(assi) + "\n主题：" + str(
                    log[3]) + "\n内容：" + str(log[4]))

        self.have_done.itemClicked.connect(showlog)
        self.have_done.doubleClicked.connect(self.show_one)

        self.case_end_ok.stateChanged.connect(lambda: self.case_end.setEnabled(not self.case_end.isEnabled()))

        self.logs.clicked.connect(self.add_new)
        self.write_paper.clicked.connect(self.reson_txt.show)
        self.make_paper.clicked.connect(self.output_paper)
        self.record.clicked.connect(self.start_write_thread)

        self.log_case.lineEdit().returnPressed.connect(self.fill_case_name)
        self.log_case.currentIndexChanged.connect(self.log_case_change)
        self.log_case.editTextChanged.connect(self.change_workdata)
        self.log_end_ok.stateChanged.connect(lambda: self.log_end.setEnabled(not self.log_end.isEnabled()))

        who = [self.show_law_txt, self.search, self.log_name.lineEdit(), self.collect_name, self.log_case.lineEdit(),
               self.link_title, self.link_link, self.show_log,
               self.collect_content, self.log_what, self.reson_txt, self.more_inf_txt]
        for i in who:
            i.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            i.customContextMenuRequested.connect(self.txt_menu)
            if who.index(i) in [8, 9]:
                i.textChanged.connect(self.start_write_thread)
            if who.index(i) >= 10:
                i.textChanged.connect(self.cach_case_inf)

        try:
            os.startfile("getnewlaws.exe")
        except:
            pass

        def movetofirst():
            textCursor = self.show_law_txt.textCursor()
            textCursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            self.show_law_txt.setTextCursor(textCursor)

        self.showlaw_thread.mysig1.connect(movetofirst)

        self.calendar.lm.clicked.connect(self.changem)
        self.calendar.nm.clicked.connect(self.changem)
        self.calendar.mc.setCurrentIndex(datetime.datetime.today().month - 1)
        self.calendar.mc.currentIndexChanged.connect(self.setdates)
        self.calendar.ys.setValue(datetime.datetime.today().year)
        self.calendar.ys.valueChanged.connect(self.setdates)

        self.calendar.bg.buttonClicked.connect(self.setdates)

        self.finished.stateChanged.connect(lambda: self.which_founction(self.search.actions()[0].objectName()))
        self.bg1.buttonClicked.connect(lambda: self.which_founction(self.search.actions()[0].objectName()))
        self.paper.valueChanged.connect(lambda: self.which_founction(self.search.actions()[0].objectName()))

    def do_something(self, arg):
        try:
            if len(arg) == 1:
                arg[0]()
            else:
                arg[0](*arg[1:])
        except:
            pass

    def changem(self):
        self.calendar.ys.blockSignals(True)
        m = int(self.sender().objectName())
        index = self.calendar.mc.currentIndex() + m
        if index in (-1, 12):
            self.calendar.ys.setValue(self.calendar.ys.value() + m)
        if index == -1:
            index = 11
        if index == 12:
            index = 0
        self.calendar.mc.setCurrentIndex(index)
        self.calendar.ys.blockSignals(False)

    def setdates(self):
        self.calendar.table.clearContents()
        thread = Thread(self.creatcalendar)
        thread.setAutoDelete(True)
        self.thread_pool.start(thread)

    def creatcalendar(self):
        def addloglist(logs, r, c, day):
            loglist = QTreeWidget()
            loglist.setContentsMargins(0, 0, 0, 0)
            loglist.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            loglist.setSortingEnabled(False)
            loglist.setRootIsDecorated(False)
            # loglist.setIconSize(QSize(15,15))
            loglist.itemClicked.connect(self.show_one)
            loglist.setStyleSheet('QTreeWidget {background-color:rgba(255,255,255,80);font-size:14px;border:none;}')
            if c in [5, 6]:
                color = "#ff0000"
            else:
                color = "#000000"
            loglist.headerItem().setText(0, logs[0])
            loglist.headerItem().setForeground(0, QColor(color))
            ft = QFont()
            ft.setBold(True)
            loglist.headerItem().setFont(0, ft)
            del logs[0]
            for log in logs:
                item = QTreeWidgetItem()
                if log[1][-1] is not None:
                    item.setIcon(0, QIcon('icons\\case.png'))
                if len(log[1][1]) == 16:
                    t = log[1][1][11:] + " "
                else:
                    t = ""
                item.setText(0, t + re.sub("\.[0-9]+$", "", log[1][3]))
                item.setData(0, Qt.UserRole, ["日志", log[1][0:-1]])
                item.setForeground(0, QColor(log[0]))
                loglist.addTopLevelItem(item)
            if datetime.date(self.calendar.ys.value(), self.calendar.mc.currentIndex() + 1,
                             day) == datetime.datetime.today().date():
                loglist.setStyleSheet(loglist.styleSheet().replace("border:none", "border:1px solid"))  # 今日
            else:
                loglist.setStyleSheet(loglist.styleSheet().replace("border:1px solid", "border:none"))
            self.calendar.table.setCellWidget(r, c, loglist)

        self.lastlogitem = None
        wl = calendar.monthrange(self.calendar.ys.value(), self.calendar.mc.currentIndex() + 1)
        c = wl[0]
        r = 0

        sql = ""
        if self.bg1.checkedId() == 1:
            sql = " and 日志.assistant='{}'".format(self.me["id"])
        fetchall = self.sendsql([
                                    "select 日志.*,案件.id from 日志 left outer join 案件 on 日志.caseid=案件.id where 日志.startdate like '%{}%'{} group by 日志.id order by 日志.startdate asc".format(
                                        str(self.calendar.ys.value()) + "-" + self.calendar.mc.currentData(), sql)])
        if fetchall == 0:
            fetchall = ()
        for day in range(1, wl[1] + 1):
            if self.abort:
                return
            logs = [str(day)]
            logsa_ok = []
            logsa_no = []
            logsf_ok = []
            logsf_no = []
            for data in fetchall:
                if self.abort:
                    return
                if (self.calendar.bg.checkedId() == 2 and data[-1] is None) or (
                    self.calendar.bg.checkedId() == 3 and data[-1] is not None):
                    continue
                if int(data[1][8:10]) == day:
                    if data[5] == "":
                        if data[-1] is None:
                            logsf_no.append(('#000000', data))
                        else:
                            logsa_no.append(('#000000', data))
                    else:
                        if data[-1] is None:
                            logsf_ok.append(('#808080', data))
                        else:
                            logsa_ok.append(('#808080', data))

            if c == 7:
                c = 0
                r = r + 1
            logs = logs + logsa_no + logsf_no + logsa_ok + logsf_ok
            self.do_something_sig.emit([addloglist, logs, r, c, day])
            time.sleep(0.01)
            c = c + 1

    def anyhost_func(self):
        datagram, host = b'update', QHostAddress.LocalHost
        while self.anyhost_udp.hasPendingDatagrams():
            datagram, host, port = self.anyhost_udp.readDatagram(
                self.anyhost_udp.pendingDatagramSize()
            )
        if datagram == b'ip':
            ip = self.serverip
            self.serverip = re.sub(".*:", "", host.toString())
            if ip != self.serverip:
                for i in [2, 4, 5, 6]:
                    widget = self.vbox1.itemAt(i).widget()
                    if "transparent" not in widget.styleSheet():
                        self.which_founction(widget.text())
                        break
        elif datagram == b'server':
            try:
                if self.me["姓名"].split("\n")[1] == "0":
                    return
                os.system("start /B attorney_server.exe {}".format(re.sub(".*:", "", host.toString())))
            except:
                pass
        elif datagram == b'update':
            self.anyhost_udp.blockSignals(True)
            os.startfile("update.exe")
            app.quit()

    def msg(self, arg):
        msgbox = MsgBox()
        if len(arg) == 1:
            msgbox.setIcon(QMessageBox.Warning)
        else:
            pixmap = self.circleImage(arg[1])
            msgbox.setIconPixmap(pixmap.scaled(50, 50))
        msgbox.setText(arg[0])
        return msgbox.exec_()

    def setting_show(self):
        for i, j in zip(range(5), list(self.me.keys())):
            if i == 2:
                n = ""
            else:
                n = self.me[j]
            if i == 4:
                self.setting_layout.itemAt(i, 1).widget().setCurrentText(n)
            elif i == 1:
                n = n.split("\n")
                self.setting_layout.itemAt(i, 1).layout().itemAt(0).widget().setText(n[0])
                self.setting_layout.itemAt(i, 1).layout().itemAt(1).widget().setChecked(int(n[1]))
            else:
                self.setting_layout.itemAt(i, 1).widget().setText(n)
        self.setting_win.exec_()

    def setting(self, result):
        if result == 3:
            self.finishsetting(3)
        else:
            thread = Thread(self.finishsetting, result)
            thread.setAutoDelete(True)
            self.thread_pool.start(thread)

    def finishsetting(self, result):
        w = 0
        if result == 1:
            self.me["姓名"] = "用户\n0"
            with open("icons\\userdefault.png", "rb") as t:
                self.me["头像"] = t.read()
            self.me["workspace"] = os.getcwd() + "\\workspace"
            self.me["show"] = "日志"
            if not os.path.exists("workspace"):
                os.mkdir("workspace")
            w = 1
        if result == 2:
            img = self.setting_layout.itemAt(2, 1).widget().text()
            if not os.path.exists(img) and self.me["头像"] == b'':
                self.do_something_sig.emit([self.msg, ["头像不存在！"]])
                return
            try:
                with open(img, "rb") as t:
                    self.me["头像"] = t.read()
            except:
                pass
            dir = self.setting_layout.itemAt(3, 1).widget().text()
            if not os.path.exists(dir):
                self.do_something_sig.emit([self.msg, ["主目录不存在！"]])
                return
            self.me["id"] = self.setting_layout.itemAt(0, 1).widget().text()
            admin = str(int(self.setting_layout.itemAt(1, 1).layout().itemAt(1).widget().isChecked()))
            if admin == "1":
                name = self.sendsql(["select id,name from 用户 where name like '%\n1%'"])
                if name == 0:
                    self.do_something_sig.emit([self.msg, ["无法设置为管理员！"]])
                    admin = "0"
                    name = ()
                if len(name) > 0 and name[0][0] != self.me["id"]:
                    self.do_something_sig.emit([self.msg, [
                        "<font color='#DB3022'><b>{}</font><br>".format(name[0][1].split("\n")[0]) + "已经是管理员！"]])
                    admin = "0"
            self.me["姓名"] = self.setting_layout.itemAt(1, 1).layout().itemAt(0).widget().text() + "\n" + admin
            self.me["workspace"] = dir
            self.me["show"] = self.setting_layout.itemAt(4, 1).widget().currentText()
            w = 1
        if w == 1:
            if self.me["id"] == "":
                self.me["id"] = str(time.strftime("%Y%m%d%H%M%S"))
            self.me["workspace"] = re.sub("\\$", "", self.me["workspace"])
            self.sendsql(["insert or replace into 用户 values(?,?,?)"],
                         (self.me["id"], self.me["姓名"], self.me["头像"]))
            with open("profile.bt", "wb") as t:
                t.write(pickle.dumps(self.me))
            try:
                os.startfile("getnewlaws.exe")
            except:
                pass
            self.do_something_sig.emit([self.set_me])
        self.do_something_sig.emit([self.setting_win.close])
        if w == 0 and self.isHidden():
            exit(0)

    def set_me(self):
        pixmap = self.circleImage(self.me["头像"])
        self.user.setIcon(QIcon(pixmap))
        self.user_name.setText(self.me["姓名"].split("\n")[0])
        if "（部门）" in self.me["show"]:
            self.rb1.setChecked(False)
            self.rb2.setChecked(True)
        for file in ("update.exe", "attorney_server.exe", "getnewlaws.exe", "convert_law.exe", "output_docx.exe"):
            if os.path.exists(file + "-update"):
                n = 0
                while True:
                    if n == 30:
                        break
                    try:
                        if os.path.exists(file):
                            os.remove(file)
                        os.rename(file + "-update", file)
                        break
                    except:
                        if file == "attorney_server.exe":
                            self.anyhost_udp.writeDatagram(b'quit', QHostAddress.Broadcast, 6665)
                        time.sleep(0.1)
                        n += 1
        if self.me["姓名"].split("\n")[1] == "0":
            self.anyhost_udp.writeDatagram(b'ip', QHostAddress.Broadcast, 6665)
        else:
            self.anyhost_udp.writeDatagram(b'server', QHostAddress.Broadcast, 8848)

    def output_paper(self):
        def getsql(table):
            sql = ""
            if self.bg1.checkedId() == 1:
                sql = " where {}.assistant='{}'".format(table, self.me["id"])
            if table in ["案件"]:
                order = "startdate"
                if not self.finished.isChecked():
                    t = "=''"
                else:
                    t = "!=''"
            else:
                order = "enddate"
                guoqi = str(datetime.datetime.today().date())
                if not self.finished.isChecked():
                    t = ">'{}'".format(guoqi)
                else:
                    t = "<='{}'".format(guoqi)
            sql = sql + (" and " if "where" in sql else " where ") + "{}.enddate".format(table) + t
            return "select {}.*,用户.name from {} left outer join 用户 on {}.assistant=用户.id{} group by {}.id order by {} desc".format(
                table, table, table, sql, table, table + "." + order)

        def get_paper(what):
            if "客户清单" in what:
                table = self.search.actions()[0].objectName()
                data = self.sendsql([getsql(table)])
                dirs = self.me["workspace"]
            else:
                if len(self.working_data) == 12:
                    dirs = "\\法务客户库\\"
                else:
                    dirs = "\\案件库\\"
                dirs = self.me["workspace"] + dirs + re.sub("[\\\/:*?|\"'<>]", "", self.working_data[1])
                if "日志" in what:
                    data = self.sendsql(["select * from 日志 where caseid='{}'".format(self.working_data[0])])
                else:
                    data = self.current_case
            if data == 0:
                return
            with open("data_out.bt", "wb") as t:
                t.write(pickle.dumps([dirs, data, what]))
            try:
                os.startfile("output_docx.exe")
            except:
                pass

        def start_getpaper():
            thread = Thread(get_paper, self.sender().text())
            thread.setAutoDelete(True)
            self.thread_pool.start(thread)

        groupBox_menu = QMenu(self)
        if len(self.working_data) == 15:
            if re.search("劳动.*?仲裁", self.current_case[13][0][0]) is not None:
                txt = u'劳动仲裁申请书'
            elif re.search("仲裁", self.current_case[13][0][0]) is not None:
                txt = u"仲裁申请书"
            else:
                txt = u"民事起诉状"
            actionA = QAction(QIcon('icons\\case.png'), txt, self)
            actionA.triggered.connect(start_getpaper)
            groupBox_menu.addAction(actionA)

            actionB = QAction(QIcon('icons\\defence.png'), u'答辩状', self)
            actionB.triggered.connect(start_getpaper)
            groupBox_menu.addAction(actionB)

        actionE = QAction(QIcon('icons\\tasks.png'), u'工作日志', self)
        actionE.triggered.connect(start_getpaper)
        groupBox_menu.addAction(actionE)

        actionF = QAction(QIcon('icons\\tasks.png'), u'客户清单', self)
        actionF.triggered.connect(start_getpaper)
        groupBox_menu.addAction(actionF)

        groupBox_menu.exec(QCursor.pos())

    def circleImage(self, imagePath, circle=True):
        if type(imagePath) == type(""):
            source = QPixmap(imagePath)
        else:
            with open("img.png", "wb") as t:
                t.write(imagePath)
            source = QPixmap("img.png")
            os.remove("img.png")
        if circle:
            size = min(source.width(), source.height())

            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            qp = QtGui.QPainter(pixmap)
            qp.setRenderHints(qp.Antialiasing)
            path = QtGui.QPainterPath()
            path.addEllipse(0, 0, size, size)
            qp.setClipPath(path)
            sourceRect = QRect(0, 0, size, size)
            sourceRect.moveCenter(source.rect().center())
            qp.drawPixmap(pixmap.rect(), source, sourceRect)
            qp.end()
        else:
            pixmap = source

        return pixmap

    def sendsql(self, words, *args):
        socketT = TcpSocket()
        n = 0
        if self.serverip is not None:
            socketT.ip = self.serverip
            socketT.sql = [words, *args]
            socketT.start()
            n = 0
            while n < 400 and not socketT.receiv_finished:
                if self.abort:
                    break
                time.sleep(0.01)
                n += 1
        if self.serverip is None or (n == 400 and not self.abort):
            self.anyhost_udp.writeDatagram(b'server', QHostAddress.Broadcast, 8848)
            self.do_something_sig.emit([self.msg, ["主机断开！"]])
        if not socketT.receiv_finished:
            r = 0
        else:
            r = pickle.loads(socketT.datas)
        if r == -1:
            r = 0
            self.do_something_sig.emit([self.msg, ["主机太菜，等等！"]])
        return r

    def record_database(self, words, *args, db="", hebing=True):
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        datas = []
        args = list(args)
        for i in range(len(words) - len(args)):
            args.append(tuple())
        for sql, arg in zip(words, args):  # sql和数据按顺序对应
            try:
                cur.execute(sql, arg)
            except:
                datas = 0
                break
            if "select" in sql:
                if hebing:
                    datas = datas + cur.fetchall()
                else:
                    datas.append(cur.fetchall())
            else:
                conn.commit()
                time.sleep(0.01)
        conn.close()
        return datas

    def change_workdata(self):
        self.working_data = [self.log_case.currentText()] + [""] * 5
        self.setWindowTitle("大律师")

    def log_case_change(self):
        self.working_data = self.log_case.currentData()
        if self.working_data is not None:
            self.do_something_sig.emit([self.setWindowTitle, self.working_data[1]])

    def fill_case_name(self):
        def fill():
            self.log_case.blockSignals(True)
            if self.log_case.currentText() == "":
                self.log_case.blockSignals(False)
                return
            fetchall = self.sendsql(
                ["select * from 案件 where casename like '%{}%'".format(self.log_case.currentText()),
                 "select * from 法务 where name like '%{}%'".format(self.log_case.currentText())])
            if fetchall == 0:
                fetchall = ()
            many = len(fetchall)
            if many > 0:
                self.do_something_sig.emit([self.log_case.clear])
                while self.log_case.count() > 0:
                    time.sleep(0.01)
                for i in fetchall:
                    self.do_something_sig.emit(
                        [self.log_case.addItem, i[6 if len(i) != 12 else 5] + " " + i[1], list(i)])

                while self.log_case.count() < many:
                    time.sleep(0.01)
                self.log_case_change()
                if len(self.log_case.currentData()) == 12:  # 法务列数
                    self.current_client = self.log_case.currentData()
                else:
                    self.current_case = self.log_case.currentData()
            if many > 1:
                while self.log_case.count() < many:
                    time.sleep(0.01)
                self.do_something_sig.emit([self.log_case.showPopup])
            self.log_case.blockSignals(False)

        thread = Thread(fill)
        thread.setAutoDelete(True)
        self.thread_pool.start(thread)

    def copyfiles(self, what):
        no = []
        for i in what[2]:
            name = re.split('[\\\/]', i)[-1]
            date = what[1][5]
            if date == "":
                date = what[1][1]
            date = date[0:10]
            if not re.search('^' + date, name):
                name = date + " " + name
            try:
                if os.path.isdir(i):
                    shutil.copytree(i, what[0] + "\\" + name)
                else:
                    shutil.copyfile(i, what[0] + "\\" + name)
            except:
                no.append(name)
        if len(no) != 0:
            self.do_something_sig.emit(
                [self.msg, ["<font color='#DB3022'>下列文件提交失败：</font><br>" + "<br>".join(no)]])

    def writelinks(self, title, link):
        ico = re.sub("http[s]?://", "", link).split("/")[0]
        ico = requests.get(url="https://api.iowen.cn/favicon/" + ico + ".png").content
        if imghdr.what(None, ico) is None:
            ico = b''
        self.record_database(["create table if not exists links (ico BLOB,title TEXT,link TEXT)"], db="links.db")
        self.record_database(["insert into links values(?,?,?)"], (ico, title, link), db="links.db")
        self.do_something_sig.emit([self.show_linkwin])

    def write_log_case_client_collect(self, table=None, record=False):
        self.mutex.lock()
        if table == "新法":
            if "" not in [self.link_link.text()]:
                thread = Thread(partial(self.writelinks, self.link_title.text(), self.link_link.text()))
                thread.setAutoDelete(True)
                self.thread_pool.start(thread)
                self.do_something_sig.emit([self.link_title.clear])
                self.do_something_sig.emit([self.link_link.clear])
            else:
                self.do_something_sig.emit([self.msg, ["请输入链接！"]])
            self.mutex.unlock()
            return
        if table != "收藏":
            assitant = self.assitant.itemData(self.assitant.currentIndex(), Qt.UserRole)[0]
        if table == "案件":
            if record:
                self.do_something_sig.emit([self.reson_txt.hide])
                n = []
                for i in range(2):
                    for j in range(self.tree_case.topLevelItem(i).childCount()):
                        txt = self.tree_case.itemWidget(self.tree_case.topLevelItem(i).child(j), 0).text()
                        if len(txt) != 0:
                            n.append(txt)
                            break
                newname = self.casename(n)
                dirs = self.me["workspace"] + "\\案件库\\"
                oldname = self.current_case[1]
                if oldname != "" and newname != oldname and os.path.exists(dirs + oldname):
                    thread = Thread(shutil.move, dirs + oldname, dirs + newname)
                    thread.setAutoDelete(True)
                    self.thread_pool.start(thread)
                if not os.path.exists(dirs + newname):
                    try:
                        os.mkdir(dirs + newname)
                    except:
                        pass
                self.current_case[1] = newname
            self.current_case[6:9] = [self.case_start.date().toString("yyyy-MM-dd"),
                                      self.case_end.date().toString("yyyy-MM-dd") if self.case_end.isEnabled() else "",
                                      assitant]
            data = self.current_case[0:9] + [pickle.dumps(i) for i in self.current_case[9:]]
        if table == "日志":
            self.current_log = [self.current_log[0],
                                self.log_start.date().toString("yyyy-MM-dd") + self.log_start_time.time().toString(
                                    " HH:mm"), self.working_data[0],
                                self.log_name.currentText() + "." + str(self.log_count.value()),
                                self.log_what.toPlainText(),
                                self.log_end.date().toString("yyyy-MM-dd") if self.log_end.isEnabled() else "",
                                assitant, self.current_log[-1]]
            if record:
                if len(self.log_files.paths) > 0:
                    dir = self.show_file_all("1")
                    if dir != 0:
                        copyfiles_threads = Thread(self.copyfiles, [dir, self.current_log, self.log_files.paths.copy()])
                        copyfiles_threads.setAutoDelete(True)
                        self.thread_pool.start(copyfiles_threads)
                        self.log_files.paths = []
                if self.current_log[-3] != "":
                    self.current_log[-1] = "#808080"
                elif self.current_log[-1] in ["#808080", None]:
                    self.current_log[-1] = "#000000"
            data = self.current_log
        if table == "收藏":
            if record != "右键收藏":
                self.current_collect = [self.current_collect[0], str(time.strftime("%Y-%m-%d %H%M%S")),
                                        self.collect_name.text(), self.collect_content.toPlainText()]
            data = self.current_collect
        if table == "法务":
            if record:
                txt = self.client_tree_case.itemWidget(self.client_tree_case.topLevelItem(0).child(0), 0).text()
                dirs = self.me["workspace"] + "\\法务客户库\\"
                if self.current_client[1] != "" and self.current_client[1] != txt and os.path.exists(
                    dirs + self.current_client[1]):
                    thread = Thread(shutil.move, dirs + self.current_client[1], dirs + txt)
                    thread.setAutoDelete(True)
                    self.thread_pool.start(thread)
                if not os.path.exists(dirs + txt):
                    try:
                        os.mkdir(dirs + txt)
                    except:
                        pass
                self.current_client[1] = txt
            self.current_client = [self.current_client[0], *self.current_client[1:5],
                                   self.client_case_start.date().toString("yyyy-MM-dd"),
                                   self.client_case_end.date().toString("yyyy-MM-dd"), *self.current_client[7:9],
                                   assitant, *self.current_client[-2:]]
            data = self.current_client
        edit_dir = self.me["workspace"] + "\\editting\\"
        my_edit_dir = os.getcwd() + "\\workspace\\editting\\"
        edit_item = table + str(data[0]) + ".editting"
        if os.path.exists(edit_dir + edit_item):
            with open(edit_dir + edit_item, "rb") as t:
                item = pickle.loads(t.read())
        else:
            item = [None]

        if not record or record == "右键收藏":
            with open(my_edit_dir + edit_item, "wb") as t:
                t.write(pickle.dumps([self.me["id"], self.me["姓名"].split("\n")[0], table, data, self.me["头像"]]))
            if edit_dir != my_edit_dir and os.path.exists(self.me["workspace"]):
                if not os.path.exists(edit_dir):
                    os.mkdir(edit_dir)
                if item[0] in [None, self.me["id"]]:
                    shutil.copyfile(my_edit_dir + edit_item, edit_dir + edit_item)
        else:
            if item[0] is not None:
                if item[0] != self.me["id"]:
                    msg = ["<font color='#DB3022'><b>" + item[1] + "</font><br>正在编辑该条，无法保存！", item[4]]
                else:
                    msg = ""
            else:
                msg = ""
            if msg != "":
                self.do_something_sig.emit([self.msg, msg])
            else:
                r = self.sendsql(["insert or replace into {} values (?{})".format(table, ",?" * (len(data) - 1))], data)
                if r == 0:
                    self.mutex.unlock()
                    return
                if os.path.exists(edit_dir + edit_item):
                    os.remove(edit_dir + edit_item)
                if os.path.exists(my_edit_dir + edit_item):
                    os.remove(my_edit_dir + edit_item)
                index = int(self.log_win.objectName())
                self.log_win.setObjectName("-1")
                if index == -1:
                    index = 0
                    self.set_item(data, table, 0)

                def ok(table, index, date):
                    self.log_show.setVisible(False)
                    self.prepare(index)
                    if table == "日志" and self.stack.currentIndex() == 0 and str(
                        self.calendar.ys.value()) + "-" + self.calendar.mc.currentData() in date:
                        self.setdates()

                self.do_something_sig.emit([ok, table, index, data[1]])
        self.mutex.unlock()

    def casename(self, arg):
        try:
            with open("place", "rb") as t:
                p = pickle.loads(t.read())
        except:
            p = ""
        arg = arg + ["", ""]
        yuan = re.sub(p, "", arg[0])
        bei = re.sub(p, "", arg[1])
        return re.sub("[\\\/:*?|\"'<>]", "", yuan + " VS " + bei)

    def tree_menu(self):
        def up_law():
            if self.sender().text() == u'删除':
                yn = self.msg(["确定删除？"])
                if yn == QMessageBox.Ok:
                    if self.main_tree.currentItem() in self.law_items[0] + self.law_items[1:]:
                        title = self.all_laws[table_data[0]][table_data[1]][0]
                        self.record_database(["delete from {} where title='{}'".format(table_data[0], title)],
                                             db="LawData.db")
                        self.record_database(["delete from {} where title='{}'".format("常用法律", title)],
                                             db="LawData.db")
                        self.main_tree.currentItem().parent().removeChild(self.main_tree.currentItem())
                        del self.all_laws[table_data[0]][table_data[1]]
                        return
                    if self.main_tree.currentItem() in self.current_items.values():
                        def delitem(table_data):
                            fetchall = self.sendsql(
                                ["delete from {} where id='{}'".format(table_data[0], table_data[1][0])])
                            if fetchall == 0:
                                return
                            self.do_something_sig.emit(
                                [self.main_tree.takeTopLevelItem, self.main_tree.currentIndex().row()])
                            del self.current_items[table_data[1][0]]
                            if table_data[0] == "日志" and self.stack.currentIndex() == 0 and str(
                                self.calendar.ys.value()) + "-" + self.calendar.mc.currentData() in table_data[1][1]:
                                self.do_something_sig.emit([self.setdates])

                        thread = Thread(delitem, table_data)
                        thread.setAutoDelete(True)
                        self.thread_pool.start(thread)
                return
            elif self.sender().text() == u'加入常用':
                if self.main_tree.currentItem() in self.law_items[1:]:
                    index = self.main_tree.currentIndex().row()
                else:
                    index = -1
                    for i in self.law_items[1:]:
                        if i.data(0, Qt.UserRole)[1] == table_data[1]:
                            index = self.alllaw_items[table_data[0]].indexOfChild(i)
                            break
                if index == -1:
                    return
                self.record_database(["insert or replace into 常用法律 (title,name) values(?,?)"],
                                     (self.all_laws[table_data[0]][table_data[1]][0], table_data[1]), db="LawData.db")
                add = self.alllaw_items[table_data[0]].takeChild(index)
                # add = self.alllaw_items["法律"][table_data[0]].takeChild(self.main_tree.currentIndex().row())
                self.alllaw_items["常用法律"].insertChild(0, add)
                self.law_items.remove(add)
                self.law_items[0].append(add)
            elif self.sender().text() == u'移出常用':
                self.record_database(["delete from {} where title='{}'".format("常用法律", self.all_laws[table_data[0]][
                    table_data[1]][0])], db="LawData.db")
                rem = self.alllaw_items["常用法律"].takeChild(self.main_tree.currentIndex().row())
                self.alllaw_items[table_data[0]].insertChild(0, rem)
                self.law_items[0].remove(rem)
                self.law_items.append(rem)
            elif self.sender().text() == u'复制':
                if table_data[0] == "案件":
                    data = table_data[1][0:10] + [pickle.dumps(i) for i in table_data[1][10:]]
                    data[1] = ""
                else:
                    data = table_data[1]
                data = ["复制项目", str(time.strftime("%Y%m%d%H%M%S")), *(data[1:])]
                self.set_item(data, table_data[0], 0)
            elif self.sender().text() == u'打开文件位置':
                try:
                    run(f'explorer /select, {table_data[1]}', shell=True)
                except:
                    pass
            elif "#" in self.sender().objectName():
                color = self.sender().objectName()
                self.main_tree.currentItem().setForeground(0, QColor(color))
                thread = Thread(self.sendsql,
                                ["update 日志 set color= '{}' where id='{}'".format(color, table_data[1][0])])
                thread.setAutoDelete(True)
                self.thread_pool.start(thread)

        if self.main_tree.currentItem() is None:
            return
        txt = ""
        table_data = self.main_tree.currentItem().data(0, Qt.UserRole)

        icon = 'upload.png'

        if self.main_tree.currentItem() in self.law_items[1:] + self.find_lawitems:
            txt = u'加入常用'
        elif self.main_tree.currentItem() in self.law_items[0]:
            txt = u'移出常用'

        groupBox_menu = QMenu(self)
        if txt != "":
            actionA = QAction(QIcon("icons\\" + icon), txt, self)
            actionA.triggered.connect(up_law)
            groupBox_menu.addAction(actionA)
        if self.main_tree.currentItem() in self.current_items.values() or self.main_tree.currentItem() in \
            self.law_items[0] + self.law_items[1:]:
            actionB = QAction(QIcon("icons\\delete.png"), u"删除", self)
            actionB.triggered.connect(up_law)
            groupBox_menu.addAction(actionB)
        if self.main_tree.currentItem() in self.current_items.values():
            actionC = QAction(QIcon("icons\\clone.png"), u"复制", self)
            actionC.triggered.connect(up_law)
            groupBox_menu.addAction(actionC)
        if table_data[0] == "文件":
            actionD = QAction(QIcon("icons\\folder.png"), u"打开文件位置", self)
            actionD.triggered.connect(up_law)
            groupBox_menu.addAction(actionD)
        if type(table_data[1]) is not int and len(table_data[1]) == 8:
            menu = QMenu(u"标注", self)
            menu.setIcon(QIcon("icons\\color.png"))
            menu.setStyleSheet("QMenu::right-arrow{color: red;}")
            for i in ["#000000", "#FF0000", "#FF7D00", "#FFC90E", "#4DB030", "#0000FF", "#FF00FF"]:
                action = QWidgetAction(self)
                lable = QLabel()
                lable.setStyleSheet("background-color:{};".format(i))
                lable.setMinimumWidth(80)
                action.setDefaultWidget(lable)
                action.setObjectName(i)
                action.triggered.connect(up_law)
                menu.addAction(action)
                menu.addSeparator()
            groupBox_menu.addMenu(menu)
        if len(groupBox_menu.actions()) > 0:
            groupBox_menu.exec(QCursor.pos())
            groupBox_menu.close()
        groupBox_menu.deleteLater()

    def txt_menu(self):
        groupBox_menu = QMenu(self)
        # self.windowEffect.setAcrylicEffect(int(groupBox_menu.winId()))
        sender = self.sender()
        if type(sender) == type(self.search):
            selectedText = sender.selectedText()
        else:
            selectedText = sender.textCursor().selectedText()

        def add_to_collect():
            sender.copy()
            if self.clipboard.text() == "":
                return
            self.current_collect = list(self.sender().data())
            self.current_collect[-1] = self.current_collect[-1] + self.clipboard.text() + "\n"
            self.write_log_case_client_collect("收藏", "右键收藏")

        if sender.objectName() != "法条":
            actionE = QAction(QIcon('icons\\paste.png'), u'粘贴', self)
            actionE.triggered.connect(lambda: sender.paste())
            groupBox_menu.addAction(actionE)

        if selectedText != "":
            actionA = QAction(QIcon('icons\\clipboard.png'), u'复制', self)
            actionA.triggered.connect(lambda: sender.copy())  # textCursor().selectedText()
            groupBox_menu.addAction(actionA)

            menu = QMenu(u'收藏', self)
            # self.windowEffect.setAcrylicEffect(int(menu.winId()))
            menu.setIcon(QIcon("icons\\star.png"))
            actionB = QAction(u'新建', self)
            actionB.setData((str(time.strftime("%Y%m%d%H%M%S")), "", "", ""))
            actionB.triggered.connect(add_to_collect)
            menu.addAction(actionB)
            for i in self.find_editting("收藏"):
                with open(i, "rb") as t:
                    data = pickle.loads(t.read())[3]
                action = QAction(data[2] if data[2] != "" else data[0], self)
                action.setData(data)
                action.triggered.connect(add_to_collect)
                menu.addAction(action)
            groupBox_menu.addMenu(menu)

        groupBox_menu.exec(QCursor.pos())

    def prepare(self, w=0):
        self.stack.setCurrentIndex(w)
        if w == 0:
            self.log_hbox1.addWidget(self.record)
            self.log_hbox2.addWidget(self.label_as)
            self.log_hbox2.addWidget(self.assitant)
            self.record.setObjectName("日志")
        if w == 2:
            self.hbox2.insertWidget(4, self.label_as)
            self.hbox2.insertWidget(5, self.assitant)
            self.hbox2.insertWidget(7, self.logs)
            self.hbox2.addWidget(self.make_paper)
            self.hbox2.addWidget(self.record)
            self.splitter_havedone_and_log.addWidget(self.have_done)
            self.splitter_havedone_and_log.addWidget(self.show_log)
            self.record.setObjectName("案件")
        if w == 3:
            self.client_hbox2.insertWidget(4, self.label_as)
            self.client_hbox2.insertWidget(5, self.assitant)
            self.client_hbox2.insertWidget(7, self.logs)
            self.client_hbox2.addWidget(self.make_paper)
            self.client_hbox2.addWidget(self.record)
            self.client_splitter_havedone_and_log.addWidget(self.have_done)
            self.client_splitter_havedone_and_log.addWidget(self.show_log)
            self.record.setObjectName("法务")
        if w == 4:
            self.collect_hbox.addWidget(self.record)
            self.record.setObjectName("收藏")
        if w == 5:
            self.addlink_layout.insertWidget(2, self.record)
            self.record.setObjectName("新法")

    def set_item(self, data, table="", w=-1):
        data = list(data)
        if data[0] == "复制项目":
            id = data[1]
            txt = "复制项目"
            data = data[1:]
        else:
            id = data[0]
            txt = None
        color = Qt.black
        if table == "法务":
            if len(data) > 12:
                if data[-1] is not None:
                    recent = datetime.datetime.strptime(data[-1][:10], "%Y-%m-%d").date()
                else:
                    recent = None
                data = data[0:-1]
            else:
                recent = datetime.datetime.today().date()
            icon = "icons\\paper.png"
            txt = txt if txt else data[6] + " " + data[1]
            # fetchall = self.sendsql(["select max(startdate) from 日志 where caseid='{}'".format(data[0])])
            # if fetchall != 0:
            if recent is None or (datetime.datetime.today().date() - recent).days >= 30:
                color = QColor(77, 176, 48)
            if (datetime.datetime.strptime(data[6], "%Y-%m-%d").date() - datetime.datetime.today().date()).days <= 30:
                color = Qt.gray
                icon = "icons\\paper_ok.png"
        elif table == "收藏":
            icon = "icons\\star.png"
            txt = txt if txt else data[1][:10] + " " + data[2] if data[2] != "" else data[0]
        elif table == "案件":
            if data[7] == "":
                icon = "icons\\case.png"
            else:
                icon = "icons\\case_ok.png"
                color = Qt.gray
            data = data[0:9] + [pickle.loads(j) if type(j) is bytes else j for j in data[9:]]
            txt = txt if txt else data[6] + " " + data[1]
        else:
            # if len(data) > 8:
            #     who = data[-1] if data[-1] is not None else data[-2]
            #     data = data[0:-2]
            # else:
            #     who = None
            color = data[-1]
            if data[-3] == "":
                icon = "icons\\tasks.png"
            else:
                icon = "icons\\tasks_ok.png"
                color = Qt.gray
            if not txt:
                txt = data[1] + " " + re.sub("\.[0-9]+$", "", data[3])  # +((" OF "+who) if who is not None else "")

        if id in self.current_items.keys():
            root = self.current_items[id]
        else:
            root = self.make_item(txtc=False)
            self.current_items[id] = root
        root.setData(0, Qt.UserRole, [table, data])

        def setroot(root, icon, txt, color,w):
            root.setIcon(0, QIcon(icon))
            root.setText(0, txt)
            root.setForeground(0, QColor(color))
            if w == 0:
                self.main_tree.insertTopLevelItem(0, root)
            else:
                self.main_tree.addTopLevelItem(root)
        self.do_something_sig.emit([partial(setroot, root, icon, txt, color,w)])
        time.sleep(0.01)

    def make_item(self, txt="", parent=None, data=None, bold=False, icon=None, txtc=True, tip=None):
        if txtc:
            l = ""
            ll = re.findall("^([a-zA-Z]).*?[0-9]([a-zA-Z])", txt)
            if len(ll) != 0:
                l = "".join(ll[0]).upper() + " "
            txt = l + re.sub("^[a-z0-9_]*", "", txt)
        item = QTreeWidgetItem()
        item.setText(0, txt)
        if tip is None:
            tip = txt
        item.setToolTip(0, tip)
        item.setFirstColumnSpanned(True)
        if data is not None:
            item.setData(0, Qt.UserRole, data)
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
        if parent is not None:
            parent.addChild(item)
        if icon is not None:
            item.setIcon(0, QIcon(icon))
        return item

    def load_alllaws(self):
        tables = self.record_database(["select name from sqlite_master where type='table'"], db="LawData.db")
        all_laws_title = dict()

        def sss(x):
            try:
                fl = re.split("[0-9]+", re.findall("^[0-9a-zA-Z]+", x[1])[0])
                st = "".join([t[0] if len(t) > 0 else t for t in fl])
            except:
                st = "a"
            return st

        for table in tables:
            all_laws_title[table[0]] = self.record_database(["select title,name from {}".format(table[0])],
                                                            db="LawData.db")
            all_laws_title[table[0]].sort(key=lambda x: sss(x))
        if len(all_laws_title) == 0:
            return

        self.alllaw_items = dict()
        self.current_lawitem = None
        usual_law = ()
        usual_law_items = []
        for table in all_laws_title.keys():
            kindparent = self.make_item(table, bold=True, data=["", table], txtc=False)
            kindparent.setIcon(0, QIcon("icons\\book.png"))
            kindparent.setForeground(0, QColor(0, 0, 255))
            self.alllaw_items[table] = kindparent
            if table == "常用法律":
                self.law_items.append([])
                usual_law = all_laws_title[table]
                continue
            self.all_laws[table] = dict()
            for title_name in all_laws_title[table]:
                if title_name in usual_law:
                    root = self.make_item(title_name[1], data=[table, title_name[1]], bold=True)
                    self.law_items[0].append(root)
                    usual_law_items.append(root)
                else:
                    root = self.make_item(title_name[1], kindparent, data=[table, title_name[1]], bold=True)
                    self.law_items.append(root)
                index = 0
                parent = root
                self.all_laws[table][title_name[1]] = (title_name[0], pickle.loads(
                    self.record_database(["select * from {} where name='{}'".format(table, title_name[1])],
                                         db="LawData.db")[0][2]))
                for j in self.all_laws[table][title_name[1]][1]:
                    if j is None:
                        continue
                    if re.search("(^第.+?编\s+)", j) is not None:
                        if re.search("^第.+?[章编]\s+", parent.text(0)) is not None:
                            parent = root
                        parent = self.make_item(j.replace("\n", ""), parent, [title_name[1], index])
                    elif re.search("^第.+?章\s+", j) is not None:
                        if re.search("^第.+?章\s+", parent.text(0)) is not None:
                            parent = parent.parent()
                        parent = self.make_item(j.replace("\n", ""), parent, [title_name[1], index])
                    elif re.search("(^第.+?节\s+)|(^[一二三四五六七八九十]+[\W\s]+)", j) is not None:
                        self.make_item(j.replace("\n", ""), parent, [title_name[1], index])
                    index = index + 1

        def sortme(x):
            w = re.findall("^[0-9a-zA-Z]+", x.data(0, Qt.UserRole)[1])[0]
            return w

        usual_law_items.sort(key=lambda x: sortme(x))
        self.alllaw_items["常用法律"].addChildren(usual_law_items)

        def loadlaw_ok():
            self.law_button.setEnabled(True)
            if "transparent" not in self.law_button.styleSheet():
                self.which_founction("法律")

        self.do_something_sig.emit([loadlaw_ok])

    def localhost_func(self):
        while self.localhost_udp.hasPendingDatagrams():
            datagram, host, port = self.localhost_udp.readDatagram(
                self.localhost_udp.pendingDatagramSize()
            )
            if datagram == b'show':
                self.showNormal()
                return
            data = pickle.loads(datagram)

            def msg(title):
                self.do_something_sig.emit([self.msg, [title]])

            if type(data) is str:
                thread = Thread(partial(msg, data))
                thread.setAutoDelete(True)
                self.thread_pool.start(thread)
                return
            self.newlaw = data
            if len(data) != 0:
                self.newlaw_label.setVisible(True)
            if os.path.exists("gongbao.db"):
                treew = [self.guojia, self.sheng, self.shi]
                index = 0
                for table in self.record_database(["select name from sqlite_master where type='table'"],
                                                  db="gongbao.db"):
                    table = table[0]
                    laws = self.record_database(["select * from {}".format(table)], db="gongbao.db")
                    treew[index].setHeaderLabel(table)
                    treew[index].clear()
                    for i in laws:
                        root = self.make_item(i[1] + " " + i[0], data=i[2], txtc=False)
                        if i[0] in data:
                            root.setForeground(0, QColor(Qt.red))
                        self.do_something_sig.emit([partial(treew[index].addTopLevelItem, root)])
                    index = index + 1

    def show_datas_all(self, table, start=0):
        if start == 0:
            sql = ""
            if table != "收藏" and self.bg1.checkedId() == 1:
                sql = " where {}.assistant='{}'".format(table, self.me["id"])
            if not self.finished.isChecked() and self.finished.isVisible():
                if table in ["日志", "案件"]:
                    t = "=''"
                elif table in ["法务"]:
                    guoqi = str(datetime.datetime.today().date() - datetime.timedelta(days=30))
                    t = ">'{}'".format(guoqi)
                sql = sql + (" and " if "where" in sql else " where ") + "{}.enddate".format(table) + t
            if table == "法务":
                order = "enddate"
            elif table == "收藏":
                order = "editdate"
            else:
                order = "startdate"
            if table == "法务":
                word = "select 法务.* ,max(日志.startdate) from 法务 left outer join 日志 on 法务.id=日志.caseid{} group by 法务.id order by {} desc".format(
                    sql, table + "." + order)
            # elif table == "日志":
            #     word = "select 日志.*,案件.casename,法务.name from 日志 left outer join 案件 on 案件.id=日志.caseid left outer join 法务 on 法务.id=日志.caseid{} group by 日志.id order by {} desc".format(sql, table+"."+order)
            else:
                word = "select * from {}{} order by {} desc".format(table, sql, order)
            fetchall = self.sendsql([word])
            if fetchall == 0:
                return
            self.fetchall = fetchall
            paper = len(fetchall) // 50
            yu = len(fetchall) % 50
            if yu > 0:
                paper += 1

            def setpaper(paper):
                self.paper.blockSignals(True)
                self.paper.setMaximum(paper)
                self.paper.setSuffix("/" + str(paper) + " 页")
                self.paper.blockSignals(False)

            self.do_something_sig.emit([setpaper, paper])
            start = 1

        for data in self.fetchall[(start - 1) * 50:start * 50]:
            if self.abort:
                return
            self.set_item(data, table)
            # a = self.sendsql(["select name from 案件 where id='{}'".format(data[2]),
            #                          "select name from 法务 where id='{}'".format(data[2])])
            # if a == 0:
            #     a = ()
            # if len(a) != 0:
            #     name =  " OF " + re.sub("^[0-9\s-]*", "",a[0][0])
            # else:
            #     name = ""
            # txt = data[1] + " " + re.sub("\.[0-9]+$", "", data[3]) + name
            # self.do_something_sig.emit([self.current_items[data[0]].setText(0,txt)])

    def show_law_all(self, table):
        if self.flash_law_thread.isRunning() or self.add_law_thread.isRunning():
            return
        for i in self.alllaw_items.keys():
            if self.abort:
                return
            self.do_something_sig.emit([partial(self.main_tree.addTopLevelItem, self.alllaw_items[i])])

        def currentlawitem():
            self.main_tree.expandItem(self.alllaw_items["常用法律"])
            if self.current_lawitem is not None:
                self.main_tree.setCurrentItem(self.current_lawitem)
                self.main_tree.scrollToItem(self.current_lawitem, QAbstractItemView.PositionAtCenter)

        while not self.abort:
            if len(self.alllaw_items) == self.main_tree.topLevelItemCount():
                self.do_something_sig.emit([currentlawitem])
                break
            time.sleep(0.01)

    def show_file_all(self, arg="click"):
        if not os.path.exists(self.me["workspace"]):
            self.msg(["主机已断开"])
            return 0
        workdir = re.sub("[\\\/:*?|\"'<>]", "", self.working_data[1])
        if len(self.working_data) == 12:
            dir = "\\法务客户库\\" + workdir
        elif len(self.working_data) == 15:
            dir = "\\案件库\\" + workdir
        else:
            dir = ""
        if os.path.exists(self.me["workspace"] + dir):
            if arg == "click":
                os.startfile(self.me["workspace"] + dir)
            else:
                return self.me["workspace"] + dir
        else:
            mk = False
            if arg == "click":
                yn = self.msg(["无此文件夹\n重新创建？"])
                if yn == QMessageBox.Ok:
                    mk = True
            else:
                mk = True
            if mk:
                run('mkdir "{}"'.format(self.me["workspace"] + dir), shell=True)
                return self.show_file_all(arg)
            else:
                return 0

    def show_newlaws(self, table):
        if not os.path.exists("newlaw.db"):
            return
        tables = self.record_database(["select name from sqlite_master where type='table'"], db='newlaw.db')
        for table in tables:
            if self.abort:
                return
            table = table[0]
            parent = self.make_item(table, data=["", table], icon="icons\\newlaw.png", bold=True, txtc=False)
            self.do_something_sig.emit([partial(self.main_tree.addTopLevelItem, parent)])
            laws = self.record_database(["select * from {}".format(table)], db="newlaw.db")
            for i in laws:
                if self.abort:
                    return
                root = self.make_item(i[1] + " " + i[0], data=["新法", i[2]], txtc=False)
                if i[0] in self.newlaw:
                    root.setForeground(0, QColor(Qt.red))
                self.do_something_sig.emit([partial(parent.addChild, root)])
        self.do_something_sig.emit([self.show_linkwin])
        while not self.abort:
            if len(tables) == self.main_tree.topLevelItemCount():
                self.do_something_sig.emit([self.main_tree.expandAll])
                break
            time.sleep(0.01)

    def setfounstyle(self, text):
        self.search.actions()[0].setObjectName(text[0:2])
        self.search_win.setVisible(False)
        for j in [2, 3, 4, 5, 6, 10]:
            widget = self.vbox1.itemAt(j).widget()
            if widget.text() == text:
                widget.setStyleSheet(self.main_button_style.replace("transparent", "rgb(148, 216, 233)"))
            else:
                widget.setStyleSheet(self.main_button_style)

    def clearmaintree(self):
        while self.main_tree.topLevelItemCount() != 0:
            if self.lastfoun == 1 and not self.search_win.isVisible():
                self.do_something_sig.emit([self.main_tree.takeTopLevelItem, 0])
            else:
                self.main_tree.clear()
                time.sleep(0.05)

    def which_founction(self, text):
        w = ["日志", "法律", "案件", "法务", "收藏", "文件", "新法"]
        if text[0:2] not in w:
            return
        index = w.index(text[0:2])
        if self.sender() is self.anyhost_udp or type(self.sender()) == QPushButton:
            if index != 5:
                self.log_win.setObjectName("-1")
                self.setfounstyle(text[0:2])
            if index in [0, 2, 3]:
                self.finished.setText("过期超30日" if index == 3 else "已完成")
                self.saixuanwin.setVisible(True)
            elif index in [1, 4, 6]:
                self.saixuanwin.setVisible(False)
            if index in [0, 2, 3, 4]:
                self.paper.setVisible(True)
            elif index in [1, 6]:
                self.paper.setVisible(False)
        func = self.show_datas_all
        if index == 5:
            self.show_file_all()
        else:
            if index == 6:
                func = self.show_newlaws
                self.prepare(5)
            elif index == 0 or self.sender() is None:
                if self.sender() is self.log_button:
                    self.log_show.setVisible(False)
                self.prepare(0)
            else:
                self.prepare(index)
            if index == 1:
                func = self.show_law_all
            self.current_items = dict()
            while self.thread_pool.activeThreadCount() > 0:
                self.abort = True
                time.sleep(0.01)
            self.abort = False
            self.clearmaintree()
            self.lastfoun = index
            if self.sender() is self.paper:
                thread = Thread(func, text[0:2], self.paper.value())
            else:
                self.paper.blockSignals(True)
                self.paper.setValue(1)
                self.paper.blockSignals(False)
                self.fetchall = []
                thread = Thread(func, text[0:2])
            thread.setAutoDelete(True)
            self.thread_pool.start(thread)
            if self.sender() in [self.anyhost_udp, self.log_button, self.bg1]:
                self.do_something_sig.emit([self.setdates])

    def append_law(self):
        self.mutex.lock()
        p = lawitem = self.main_tree.currentItem()
        if lawitem in self.alllaw_items.values():
            self.mutex.unlock()
            return
        while True:
            if p.parent() is None:
                break
            lawitem = p
            p = p.parent()
        table_name = lawitem.data(0, Qt.UserRole)
        law_name = self.all_laws[table_name[0]][table_name[1]][0]
        self.do_something_sig.emit([self.show_law_txt.append, "<font><b>" + law_name + "<br></font>"])
        if self.main_tree.currentItem() is not lawitem:
            txt = re.sub("●", "", self.main_tree.currentItem().text(0))
            zjb = re.findall("^第.+?([条章节编])\s*?", txt)
            if len(zjb) == 0:
                zjb = re.findall("^([一二三四五六七八九十0-9])+[\W\s]+?", txt)
            zjb = "" if len(zjb) == 0 else zjb[0]
            if zjb == "条":
                zjb = "[条节章编]"
            if zjb == "节":
                zjb = "[节章编]"
            if zjb == "章":
                zjb = "[章编]"
            if zjb in "一二三四五六七八九十":
                zjb = "[一二三四五六七八九十章节编]"
            if zjb in "0123456789":
                zjb = "[0-9一二三四五六七八九十]"
        else:
            zjb = ""
        index = self.main_tree.currentItem().data(0, Qt.UserRole)[1]
        if type(index) is str:
            index = 0
        current_law = self.all_laws[table_name[0]][table_name[1]][1]
        start = next = index
        for code in current_law[index:]:
            if code is None:
                continue
            if zjb != "" and (re.search("^第.+?" + zjb + "\s+", code) is not None or re.search("^" + zjb + "+[\W\s]*?",
                                                                                               code) is not None):  # 找到下一个zjb
                if zjb == "编":  # zjb != ""的意义在于保证点的item一定是子节点
                    start = start + 1  # 意义在于跳过第一分编
                if next > start:  # next>start的意义在于防止在第一条就终止
                    break
            codetxt = code
            for j in self.these:
                if j in code:
                    codetxt = codetxt.replace(j, "<font color='#DB3022'><b>" + j + "</font>")
            # if re.search("(^第.+?条\s*)|(^[0-9]+[\W\s]+?)", re.sub("<.*?>","",i)) is not None:
            if re.search("(^第.+?[编章节]\s+?)|(^[一二三四五六七八九十]+[\W\s]+?)", code) is not None:
                codetxt = "<font><b>{}</font>".format(codetxt.replace("\n", "<br>"))
            else:
                codetxt = "<font color='#DB3022' size=1>●</font>" + codetxt.replace("\n", "<br>")
            self.do_something_sig.emit([self.show_law_txt.append, codetxt])
            next = next + 1
        self.mutex.unlock()

    def add_law(self):
        while True:
            time.sleep(1)
            if os.path.exists("nolaw.bt"):
                with open("nolaw.bt", "rb") as t:
                    law_txts = pickle.loads(t.read())
                self.do_something_sig.emit([self.msg, ["下列文件无法条：\n" + law_txts]])
                os.remove("nolaw.bt")
            if not os.path.exists("newlaw.bt"):
                self.flash_law_thread.start()
                break

    def show_log_a(self):
        self.log_start.setDate(datetime.datetime.strptime(self.current_log[1][:10], "%Y-%m-%d"))
        if len(self.current_log[1]) == 16:
            t = datetime.datetime.strptime(self.current_log[1][11:], "%H:%M").time()
        else:
            t = datetime.datetime.today().time()
        self.log_start_time.setTime(t)
        if self.current_log[-3] == "":
            self.log_end_ok.setChecked(False)
            self.log_end.setDate(datetime.datetime.today())
        else:
            self.log_end_ok.setChecked(True)
            self.log_end.setDate(datetime.datetime.strptime(self.current_log[-3], "%Y-%m-%d"))
        name = re.sub("\.[0-9]+$", "", self.current_log[3])
        try:
            count = int(re.sub("^" + name + "\.", "", self.current_log[3]))
        except:
            count = 1
        self.log_name.setCurrentText(name)
        self.log_count.setValue(count)
        self.log_what.blockSignals(True)
        txt = self.current_log[4]
        for i in self.these:
            txt = txt.replace(i, "<font color='#DB3022'><b>" + i + "</font>").replace("\n", "<br>")
        self.log_what.setText(txt)
        self.log_what.blockSignals(False)

        if self.sender() in [self.have_done, self.logs]:
            self.log_win.setObjectName(str(self.stack.currentIndex()))

        self.prepare()

        def log_case(current_log):
            self.setassitant(current_log[-2])
            fetchall = self.sendsql(["select * from 案件 where id='{}'".format(current_log[2]),
                                     "select * from 法务 where id='{}'".format(current_log[2])])
            if fetchall == 0:
                return
            self.do_something_sig.emit([self.log_case.clear])
            while self.log_case.count() > 0:
                time.sleep(0.01)
            if len(fetchall) == 0:
                self.do_something_sig.emit([self.log_case.setCurrentText, current_log[2]])
                self.do_something_sig.emit([self.change_workdata])
            elif len(fetchall[0]) == 12:
                self.current_client = list(fetchall[0])
                self.do_something_sig.emit(
                    [self.log_case.addItem, self.current_client[5] + " " + self.current_client[1], self.current_client])
            else:
                self.current_case = list(fetchall[0])
                self.do_something_sig.emit(
                    [self.log_case.addItem, self.current_case[6] + " " + self.current_case[1], self.current_case])

        thread = Thread(log_case, self.current_log)
        thread.setAutoDelete(True)
        self.thread_pool.start(thread)

    def show_collect_a(self):
        self.prepare(4)
        self.collect_content.blockSignals(True)
        txt = self.current_collect[3]
        for i in self.these:
            txt = txt.replace(i, "<font color='#DB3022'><b>" + i + "</font>").replace("\n", "<br>")
        self.collect_name.setText(self.current_collect[2])
        self.collect_content.setText(txt)
        self.collect_content.blockSignals(False)

    def show_linkwin(self):
        self.prepare(5)
        for r in range(self.link_box.rowCount()):
            for c in range(5):
                item = self.link_box.itemAtPosition(r, c)
                if item is None:
                    continue
                self.link_box.removeItem(item)
                item.widget().deleteLater()
        if not os.path.exists("links.db"):
            return
        fetchall = self.record_database(["select * from links"], db="links.db")
        if fetchall == 0:
            return

        def dellink(r, c):
            item = self.link_box.itemAtPosition(r, c)
            self.link_box.removeItem(item)
            item.widget().deleteLater()
            self.record_database(["delete from links where title='{}' and link='{}'".format(self.sender().data()[0],
                                                                                            self.sender().data()[1])],
                                 db="links.db")

        def del_menu(r, c, data):
            groupBox_menu = QMenu(self)
            actionA = QAction(QIcon('icons\\delete.png'), u'删除', self)
            actionA.triggered.connect(partial(dellink, r, c))
            actionA.setData(data)
            groupBox_menu.addAction(actionA)
            groupBox_menu.exec(QCursor.pos())

        def openlink(file):
            try:
                os.startfile(file)
            except:
                pass

        r, c = 0, 0
        for i in fetchall:
            if c == 5:
                c = 0
                r = r + 1
            if i[0] == b'':
                ico = "icons\\earth.png"
            else:
                ico = i[0]
            link_button = QToolButton()
            link_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            link_button.setText(i[1])
            link_button.setIcon(QIcon(self.circleImage(ico, False)))
            link_button.setIconSize(QSize(30, 30))
            link_button.setFixedWidth(150)
            link_button.setFixedHeight(36)
            link_button.setStyleSheet(
                "QToolButton:hover {background-color:rgba(72, 175, 255,100);border:0px;border-radius:6px;} QToolButton {background-color:transparent;border:0px;}")
            link_button.clicked.connect(partial(openlink, i[2]))
            link_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            link_button.customContextMenuRequested.connect(partial(del_menu, r, c, i[1:]))
            self.link_box.addWidget(link_button, r, c)
            c = c + 1
        self.link_box.setRowStretch(r + 1, 1)
        self.link_box.setColumnStretch(5, 1)

    def find_editting(self, table):
        e = []
        my_edit_dir = "workspace\\editting\\"
        if not os.path.exists("workspace"):
            os.mkdir("workspace")
        if not os.path.exists(my_edit_dir):
            os.mkdir(my_edit_dir)
        for i in os.listdir(my_edit_dir):
            if table in i and i.endswith(".editting"):
                e.append(my_edit_dir + i)
        return e

    def add_new(self, table=""):

        def add_log():
            self.log_show.setVisible(True)
            if len(editting) != 0:
                with open(editting[0], "rb") as t:
                    self.current_log = pickle.loads(t.read())[3]
            else:
                self.current_log = [str(time.strftime("%Y%m%d%H%M%S")), str(time.strftime("%Y-%m-%d")),
                                    "" if len(self.working_data) == 6 else self.working_data[0], "", "", "", "#000000"]
            self.show_log_a()

        def add_case():
            if len(editting) != 0:
                with open(editting[0], "rb") as t:
                    d = pickle.loads(t.read())[3]
                    self.current_case = d[0:9] + [pickle.loads(i) for i in d[9:]]
            else:
                self.current_case = [""] * 9 + [[["", "", ""]] for _ in range(6)]
            self.setWindowTitle("大律师" if self.current_case[1] == "" else self.current_case[1])
            self.show_case_a()

        def add_client():
            if len(editting) != 0:
                with open(editting[0], "rb") as t:
                    self.current_client = pickle.loads(t.read())[3]
            else:
                self.current_client = [""] * 7 + [pickle.dumps(["", dict()])] + [""] * 4
            self.setWindowTitle("大律师" if self.current_client[1] == "" else self.current_client[1])
            self.show_client_a()

        def add_law():
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
            dir = winreg.QueryValueEx(key, "Desktop")[0]
            lawfiles = QFileDialog.getOpenFileNames(self, '导入法律', dir, '纯文本 (*.txt)')[0]
            if len(lawfiles) != 0:
                tbl = QInputDialog(self)
                tbl.setCancelButtonText("取消")
                tbl.setOkButtonText("确定")
                tbl.setWindowTitle("类型")
                tbl.setLabelText("请选择")
                tbl.setComboBoxItems(
                    ["法律", "宪法", "司法解释", "行政法规", "地方性法规", "部门规章", "地方政府规章", "规范性文件"])
                if tbl.exec_() == 1:
                    table = tbl.textValue()
                else:
                    return
                newlaw = {table: lawfiles}
                with open("newlaw.bt", "wb") as t:
                    t.write(pickle.dumps(newlaw))
                try:
                    os.startfile("create_law.exe")
                except:
                    return
                self.law_button.setEnabled(False)
                self.add_law_thread.start()

        def add_collect():
            if len(editting) != 0:
                with open(editting[0], "rb") as t:
                    self.current_collect = pickle.loads(t.read())[3]
            else:
                self.current_collect = (str(time.strftime("%Y%m%d%H%M%S")), "", "", "")
            self.show_collect_a()

        if self.sender().objectName() not in ["法律", "新法"]:
            if self.sender().objectName() not in ["添加日志"]:
                editting = self.find_editting(self.search.actions()[0].objectName())
                if self.search_win.isVisible():
                    self.which_founction(self.search.actions()[0].objectName())
            else:
                editting = []

        self.log_win.setObjectName("-1")

        if table in ["", False]:
            table = self.sender().objectName()
        if table == "案件":
            add_case()
        elif table in ["日志", "添加日志"]:
            add_log()
        elif table == "法务":
            add_client()
        elif table == "收藏":
            add_collect()
        elif table == "法律":
            add_law()
        elif table == "新法":
            self.addlink_win.setVisible(True)

    def show_one(self):

        def show_log():
            self.current_log = item.data(0, Qt.UserRole)[1][0:8]
            self.log_show.setVisible(True)
            init = self.sender() in (self.main_tree, self.have_done)
            if not init:
                if self.lastlogitem is not None:
                    self.lastlogitem.setSelected(False)
                self.lastlogitem = item
                if self.current_log[0] in self.current_items:
                    self.main_tree.setCurrentItem(self.current_items[self.current_log[0]])
                    self.main_tree.scrollToItem(self.main_tree.currentItem(), QAbstractItemView.PositionAtCenter)
            editting = "workspace\\editting\\" + "日志" + str(self.current_log[0]) + ".editting"
            if os.path.exists(editting):
                with open(editting, "rb") as t:
                    self.current_log = pickle.loads(t.read())[3]
            self.show_log_a()

        def show_law():
            self.current_lawitem = item
            self.prepare(1)
            self.show_law_txt.clear()
            self.showlaw_thread.start()

        def show_case():
            self.current_case = item.data(0, Qt.UserRole)[1]
            editting = "workspace\\editting\\" + "案件" + str(self.current_case[0]) + ".editting"
            if os.path.exists(editting):
                with open(editting, "rb") as t:
                    d = pickle.loads(t.read())[3]
                    self.current_case = d[0:9] + [pickle.loads(i) for i in d[9:]]
            self.setWindowTitle("大律师" if self.current_case[1] == "" else self.current_case[1])
            self.show_case_a()

        def show_client():
            self.current_client = item.data(0, Qt.UserRole)[1]
            editting = "workspace\\editting\\" + "法务" + str(self.current_client[0]) + ".editting"
            if os.path.exists(editting):
                with open(editting, "rb") as t:
                    self.current_client = pickle.loads(t.read())[3]
            self.setWindowTitle("大律师" if self.current_client[1] == "" else self.current_client[1])
            self.show_client_a()

        def show_collect():
            self.current_collect = item.data(0, Qt.UserRole)[1]
            editting = "workspace\\editting\\" + "收藏" + str(self.current_collect[0]) + ".editting"
            if os.path.exists(editting):
                with open(editting, "rb") as t:
                    self.current_collect = pickle.loads(t.read())[3]
            self.show_collect_a()

        def starturl():
            try:
                os.startfile(item.data(0, Qt.UserRole)[1])
                item.setForeground(0, QColor(Qt.black))
                name = re.sub("^.*?\s", "", item.text(0))
                if name in self.newlaw:
                    self.newlaw.remove(name)
                if len(self.newlaw) == 0:
                    self.newlaw_label.setVisible(False)
            except:
                pass

        def openfile(file):
            try:
                # run(f'explorer /select, {file}',shell=True)
                os.startfile(file)
            except:
                try:
                    run(f'explorer /select, {file}', shell=True)
                except:
                    pass

        my_edit_dir = "workspace\\editting\\"
        if not os.path.exists("workspace"):
            os.mkdir("workspace")
        if not os.path.exists(my_edit_dir):
            os.mkdir(my_edit_dir)

        item = self.sender().currentItem()
        self.log_win.setObjectName("-1")

        if item.data(0, Qt.UserRole)[0] == "文件":
            openfile(item.data(0, Qt.UserRole)[1])
        elif item.data(0, Qt.UserRole)[0] == "案件":
            show_case()
        elif item.data(0, Qt.UserRole)[0] == "法务":
            show_client()
        elif item.data(0, Qt.UserRole)[0] == "日志":
            show_log()
        elif item.data(0, Qt.UserRole)[0] == "收藏":
            show_collect()
        elif item.data(0, Qt.UserRole)[0] == "新法":
            starturl()
        elif item.data(0, Qt.UserRole)[0] != "":
            show_law()

    def setassitant(self, id):
        id = str(id)
        fetchall = self.sendsql(["select id,name from 用户"])
        if fetchall != 0:
            self.do_something_sig.emit([self.assitant.clear])
            while self.assitant.count() > 0:
                time.sleep(0.01)
            for i in fetchall:
                self.do_something_sig.emit([self.assitant.addItem, i[1].split("\n")[0], i])
        else:
            fetchall = []
        if id == "":
            id = self.me["id"]
        while self.assitant.count() < len(fetchall):
            time.sleep(0.01)
        for i in range(self.assitant.count()):
            if self.assitant.itemData(i, Qt.UserRole)[0] == id:
                self.do_something_sig.emit([self.assitant.setCurrentIndex, i])
                break

    def start_write_thread(self, table=False):
        if not table:
            table = self.sender().objectName()
        if self.sender() is self.record:
            record = True
        else:
            record = False
        thread = Thread(self.write_log_case_client_collect, table, record)
        thread.setAutoDelete(True)
        self.thread_pool.start(thread)

    def cach_case_inf(self, *arg):
        if self.sender() is self.reson_txt:
            self.current_case[4] = self.reson_txt.toPlainText()
        elif self.sender() is self.more_inf_txt:
            index = [int(i) for i in self.more_inf_txt.objectName().split("-")]
            if index[0] == 3:
                self.current_case[3] = self.more_inf_txt.toPlainText()
            else:
                self.current_case[index[0]][index[1]][1] = self.more_inf_txt.toPlainText()
        elif len(arg) == 1 and arg[0] == 5:
            self.current_case[5] = self.sender().toPlainText()
        elif len(arg) > 0:
            if arg[0] == 2:
                self.current_case[2] = self.sender().text()
            else:
                self.current_case[arg[0]][arg[1]][0] = self.sender().text()
        self.start_write_thread("案件")

    def cach_client_inf(self, index):
        who = self.sender()
        if who.objectName() == "备注":
            self.current_client[index] = who.toPlainText()
        elif who.objectName() == "套餐":
            self.current_client[index] = pickle.dumps([who.currentText(), who.currentData()])
        else:
            self.current_client[index] = who.text()
        self.start_write_thread("法务")

    def deletelog(self, item):
        yn = self.msg(["确定删除？"])
        if yn == QMessageBox.Ok:
            id = item.data(0, Qt.UserRole)[1][0]
            thread = Thread(self.sendsql, ["delete from 日志 where id='{}'".format(id)])
            thread.setAutoDelete(True)
            self.thread_pool.start(thread)
            self.have_done.takeTopLevelItem(self.have_done.indexOfTopLevelItem(item))

    def show_client_a(self):
        self.prepare(3)
        self.working_data = self.current_client
        if self.current_client[5] == "":
            self.client_case_start.setDate(datetime.datetime.today())
        else:
            self.client_case_start.setDate(datetime.datetime.strptime(self.current_client[5][0:10], "%Y-%m-%d"))
        if self.current_client[0] == "":
            self.current_client[0] = str(self.client_case_start.date().toString("yyyyMMdd")) + str(
                time.strftime("%H%M%S"))
        if self.current_client[6] == "":
            self.client_case_end.setDate(datetime.datetime.today())
        else:
            self.client_case_end.setDate(datetime.datetime.strptime(self.current_client[6], "%Y-%m-%d"))

        self.client_tree_case.clear()
        labels = ["", "名称", "行业", "联系电话", "联系地址", "", "", "套餐", "回款/签约金额", "", "签约顾问", "备注",
                  "服务剩余"]
        for i in labels:
            if i == "":
                continue
            root = QTreeWidgetItem(self.client_tree_case)
            root.setText(0, i)
            self.client_creat_line(root, labels.index(i))
        self.client_tree_case.expandAll()

    def show_havedone(self, current, fetchall=0):
        self.do_something_sig.emit([self.have_done.clear])
        while self.have_done.topLevelItemCount() > 0:
            time.sleep(0.01)
        if fetchall == 0:
            fetchall = self.sendsql([
                                        "select 日志.*,用户.name from 日志 left outer join 用户 on 日志.assistant=用户.id where 日志.caseid='{}' order by 日志.startdate desc".format(
                                            current[0])])
            if fetchall == 0:
                fetchall = ()
        if len(fetchall) == 0:
            root = self.make_item("无日志......", data=["", None], txtc=False)
            self.do_something_sig.emit([partial(self.have_done.addTopLevelItem, root)])

        def addroot(root):
            self.have_done.addTopLevelItem(root)
            self.have_done.setItemWidget(root, 0,
                                         self.log_files.createwidget([""], partial(self.deletelog, root), "delete.png"))

        for i in fetchall:
            task = i[1] + " " + i[3]
            root = self.make_item(task, data=["日志", list(i)], txtc=False, tip=i[4])
            if i[-3] == "":
                root.setIcon(0, QIcon("icons\\tasks.png"))
            else:
                root.setIcon(0, QIcon("icons\\tasks_ok.png"))
            self.do_something_sig.emit([addroot, root])
        self.do_something_sig.emit([self.show_log.setVisible, False])
        if len(current) == 12:
            self.setassitant(current[9])
        else:
            self.setassitant(current[8])

    def show_case_a(self):
        self.prepare(2)
        self.working_data = self.current_case
        if self.current_case[6] == "":
            self.case_start.setDate(datetime.datetime.today())
        else:
            self.case_start.setDate(datetime.datetime.strptime(self.current_case[6], "%Y-%m-%d"))
        if self.current_case[0] == "":
            self.current_case[0] = str(self.case_start.date().toString("yyyyMMdd")) + str(time.strftime("%H%M%S"))
        if self.current_case[7] == "":
            self.case_end_ok.setChecked(False)
            self.case_end.setDate(datetime.datetime.today())
        else:
            self.case_end_ok.setChecked(True)
            self.case_end.setDate(datetime.datetime.strptime(self.current_case[7], "%Y-%m-%d"))

        self.tree_case.clear()
        labels = ["原告", "被告", "第三人", "回款/签约金额", "案由", "管辖法院", "法官", "诉讼请求", "备注"]
        self.case_menu()
        for i in labels:
            root = QTreeWidgetItem(self.tree_case)
            root.setText(0, i)
            self.case_creat_line(root)
            if labels.index(i) in [3, 4, 7, 8]:
                continue
            self.tree_case.setItemWidget(root, 0,
                                         self.log_files.createwidget(["加"], partial(self.case_creat_line, root),
                                                                     "add.png"))
        self.tree_case.expandAll()
        self.reson_txt.blockSignals(True)
        self.reson_txt.setPlainText(self.current_case[4])
        self.reson_txt.blockSignals(False)

        thread = Thread(self.show_havedone, self.current_case)
        thread.setAutoDelete(True)
        self.thread_pool.start(thread)

    def case_menu(self):
        self.lineedit_menu = QMenu(self)

        def setit():
            d = self.sender().data()
            if self.sender().text() == "设置委托人":
                txt = "委托人"
                icon = "icons\\client.png"
            else:
                icon = txt = ""
            self.current_case[d[1]][d[2]][2] = txt
            self.tree_case.topLevelItem(d[0]).child(d[2]).setIcon(0, QIcon(icon))

        actionA = QAction(QIcon('icons\\client.png'), u'设置委托人', self)
        actionA.triggered.connect(setit)
        self.lineedit_menu.addAction(actionA)

        def delit():
            d = self.sender().data()
            self.tree_case.topLevelItem(d[0]).removeChild(self.tree_case.topLevelItem(d[0]).child(d[2]))
            del self.current_case[d[1]][d[2]]

        actionB = QAction(QIcon('icons\\delete.png'), u'删除', self)
        actionB.setObjectName("案件")
        actionB.triggered.connect(delit)
        self.lineedit_menu.addAction(actionB)

    def client_creat_line(self, root, index):
        child = QTreeWidgetItem(root)
        if index == 11:
            root.setIcon(0, QIcon("icons\\flag.png"))
            beizhu = QPlainTextEdit()
            beizhu.setPlainText(self.current_client[index])
            beizhu.setMaximumHeight(80)
            beizhu.setObjectName("备注")
            beizhu.textChanged.connect(partial(self.cach_client_inf, index))
            # beizhu.setStyleSheet("background-color:rgba(239,228,176,100);font-size:20px")
            widget = beizhu
        elif index == 7:
            lineedit = ComboBox()
            lineedit.setObjectName(root.text(0))
            lineedit.setContentsMargins(3, 3, 3, 3)
            lineedit.setEditable(True)
            data = pickle.loads(self.current_client[7])
            lineedit.addItem(data[0], data[1])
            for i in self.allmeals.keys():
                lineedit.addItem(i, self.allmeals[i])
            lineedit.setCurrentText(data[0])
            lineedit.currentTextChanged.connect(partial(self.cach_client_inf, index))
            widget = lineedit
        elif index != 12:
            lineedit = QLineEdit()
            lineedit.setObjectName(root.text(0))
            lineedit.setContentsMargins(3, 3, 3, 3)
            lineedit.setText(self.current_client[index])
            if index != 1:
                lineedit.textChanged.connect(partial(self.cach_client_inf, index))
            widget = lineedit

        def countservice(label, current_client):
            # fetchall = self.sendsql(["select * from 日志 where caseid='{}' order by startdate desc".format(current_client[0])])
            fetchall = self.sendsql([
                                        "select 日志.*,用户.name from 日志 left outer join 用户 on 日志.assistant=用户.id where 日志.caseid='{}' group by 日志.id order by 日志.startdate desc".format(
                                            current_client[0])])
            if type(current_client[7]) == type(""):
                meal = dict()
            else:
                meal = pickle.loads(current_client[7])[1]
            last = meal.copy()
            if fetchall != 0:
                for i in fetchall:
                    for j in meal.keys():
                        if j in i[3]:
                            try:
                                last[j] = last[j] - int(i[3].split(".")[-1])
                            except:
                                pass
            else:
                for j in last.keys():
                    last[j] = "未读到日志"
            txt = ""
            for i in meal.keys():
                if type(last[i]) is int and last[i] <= 1:
                    txt = txt + "<font color = #000000 size=4>{}：</font><font color = #ff0000 size=4>{}/{}</font><br>".format(
                        i, str(last[i]), str(meal[i]))
                else:
                    txt = txt + "<font color = #000000 size=4>{}：{}/{}</font><br>".format(i, str(last[i]), str(meal[i]))
            if txt == "":
                txt = "<font color = #000000 >该套餐未设置数量限制</font><br>"

            def setw(label):
                label.setText(txt[0:-4])
                label.adjustSize()

            self.do_something_sig.emit([setw, label])
            self.show_havedone(self.current_client, fetchall)

        if index == 12:
            label = QLabel()
            self.client_tree_case.setItemWidget(child, 0, label)
            thread = Thread(countservice, label, self.current_client)
            thread.setAutoDelete(True)
            self.thread_pool.start(thread)
        else:
            if type(widget) is ComboBox:
                w = widget.lineEdit()
            else:
                w = widget
            w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            if type(widget) is not QLabel:
                w.customContextMenuRequested.connect(self.txt_menu)
            self.client_tree_case.setItemWidget(child, 0, widget)

    def case_creat_line(self, root):
        rootindex = self.tree_case.indexOfTopLevelItem(root)
        e = {0: 9, 1: 10, 2: 11, 3: 2, 4: 12, 5: 13, 6: 14, 7: 3, 8: 5}
        dataindex = e[rootindex]
        if root.text(0) in ["备注"]:
            child = QTreeWidgetItem(root)
            root.setIcon(0, QIcon("icons\\flag.png"))
            beizhu = QPlainTextEdit()
            beizhu.setPlainText(self.current_case[dataindex])
            beizhu.setMaximumHeight(120)
            beizhu.setObjectName("案件")
            beizhu.textChanged.connect(partial(self.cach_case_inf, dataindex))
            beizhu.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            beizhu.customContextMenuRequested.connect(self.txt_menu)
            # beizhu.setStyleSheet("background-color:rgba(239,228,176,100);font-size:20px;")
            self.tree_case.setItemWidget(child, 0, beizhu)
            return

        def action_enable(line, act, dataindex, n):
            if line.text() != "":
                act.setEnabled(True)
            else:
                act.setEnabled(False)
            self.cach_case_inf(dataindex, n)

        def show_menu(rootindex, dataindex, n):
            if rootindex in [0, 1, 2]:
                self.lineedit_menu.actions()[0].setEnabled(True)
                if self.current_case[dataindex][n][2] == "委托人":
                    text = "取消委托人"
                else:
                    text = "设置委托人"
                self.lineedit_menu.actions()[0].setText(text)
                self.lineedit_menu.actions()[0].setData([rootindex, dataindex, n])
                self.lineedit_menu.actions()[1].setData([rootindex, dataindex, n])
            else:
                self.lineedit_menu.actions()[0].setEnabled(False)

            self.lineedit_menu.exec(QCursor.pos())

        if self.sender().objectName() == "加":
            n = len(self.current_case[dataindex])
            self.current_case[dataindex].append(["", "", ""])
            ran = [["", "", ""]]
        else:
            d = self.current_case[dataindex]
            if type(d) is bytes:
                d = pickle.loads(d)
            ran = [[d, "", ""]] if type(d) is str else d
            n = 0
        for i in ran:
            if len(i) < 3:
                i = i + ["", ""]
            child = QTreeWidgetItem(root)
            if i[2] == "委托人":
                child.setIcon(0, QIcon("icons\\client.png"))
            child.setData(0, Qt.UserRole, i[1])
            lineedit = QLineEdit()
            lineedit.setObjectName("案件")
            lineedit.setText(i[0])
            lineedit.setContentsMargins(3, 3, 3, 3)
            lineedit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            if dataindex not in [13, 2, 3]:
                lineedit.customContextMenuRequested.connect(partial(show_menu, rootindex, dataindex, n))
            if dataindex in [3]:
                lineedit.setReadOnly(True)
            if dataindex not in [2]:
                action = QAction(lineedit)
                action.setIcon(QIcon("icons\\more.png"))
                action.triggered.connect(partial(self.more_inf, dataindex, n))
                if i[0] == "" and dataindex != 3:
                    action.setEnabled(False)
                lineedit.addAction(action, QLineEdit.TrailingPosition)
            if dataindex not in [2, 3]:
                lineedit.textChanged.connect(partial(action_enable, lineedit, action, dataindex, n))
            self.tree_case.setItemWidget(child, 0, lineedit)
            n = n + 1

    def more_inf(self, dataindex, n):
        self.more_inf_txt.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.more_inf_txt.move(self.x() + (self.width() - self.more_inf_txt.width()) // 2,
                               self.y() + (self.height() - self.more_inf_txt.height()) // 2)
        self.more_inf_txt.show()
        self.more_inf_txt.blockSignals(True)
        if dataindex == 3:
            self.more_inf_txt.setPlainText(self.current_case[dataindex])
        else:
            self.more_inf_txt.setPlainText(self.current_case[dataindex][n][1])
        self.more_inf_txt.setObjectName(str(dataindex) + "-" + str(n))
        cursor = self.more_inf_txt.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.more_inf_txt.setTextCursor(cursor)
        self.more_inf_txt.blockSignals(False)

    def find_prepare(self):
        while self.find_thread.isRunning():
            self.abort = True
            time.sleep(0.01)
        self.clearmaintree()
        if not self.search_win.isVisible():
            self.search_win.setVisible(True)
        self.paper.setVisible(False)
        self.saixuanwin.setVisible(False)
        self.abort = False
        self.find_thread.start()

    def find_in_all(self):
        self.current_items = dict()
        scope = []
        for i in range(6):
            checkbox = self.search_which.itemAt(i).widget()
            if checkbox.isChecked():
                scope.append(checkbox.text())
        if len(self.these) == 0 or len(scope) == 0:
            return
        try:
            shutil.copyfile(self.me["workspace"] + "\\database.db", "database.db")
        except:
            scope = []
        for which in scope:
            if self.abort:
                return
            if which in ["法律", "文件"]:
                continue
            datas = self.record_database(["select * from {}".format(which)], db="database.db")
            if datas == 0:
                datas = []
            for data in datas:
                if self.abort:
                    return
                m = 0
                these = []
                for k in data[1:]:
                    if self.abort:
                        return
                    if k is None:
                        continue
                    if which == "案件":
                        if m >= 8:
                            k = "\n".join(list(chain.from_iterable(pickle.loads(k))))
                        if m == 7:
                            a = self.record_database(["select name from 用户 where id='{}'".format(str(k))],
                                                     db="database.db")
                            if a != 0 and len(a) != 0:
                                k = a[0][0]
                            else:
                                k = ""
                    if which == "法务":
                        if m == 6:
                            k = pickle.loads(k)[0]
                        if m == 8:
                            a = self.record_database(["select name from 用户 where id='{}'".format(str(k))],
                                                     db="database.db")
                            if a != 0 and len(a) != 0:
                                k = a[0][0]
                            else:
                                k = ""
                    if which == "日志":
                        if m == 1:
                            name = self.record_database(["select casename from 案件 where id='{}'".format(str(k)),
                                                         "select name from 法务 where id='{}'".format(str(k))],
                                                        db="database.db")
                            if name == 0:
                                name = ()
                            if len(name) != 0:
                                k = name[0][0]
                        if m == 5:
                            a = self.record_database(["select name from 用户 where id='{}'".format(str(k))],
                                                     db="database.db")
                            if a != 0 and len(a) != 0:
                                k = a[0][0]
                            else:
                                k = ""
                    m = m + 1
                    for txt in self.these:
                        if txt in k and txt not in these:
                            these.append(txt)
                    if len(these) == len(self.these):
                        self.set_item(data, which)
                        break

        if "文件" in scope:
            for home, dirs, files in os.walk(self.me["workspace"]):
                if self.abort:
                    return
                for i in files:
                    if self.abort:
                        return
                    file = os.path.join(home, i)
                    n = 0
                    for j in self.these:
                        if j in file:
                            n = n + 1
                    if n == len(self.these):
                        fileInfo = QFileInfo(file)
                        fileIcon = QFileIconProvider()
                        icon = QIcon(fileIcon.icon(fileInfo))
                        root = self.make_item(i, icon=icon, data=["文件", file], txtc=False)
                        self.do_something_sig.emit([partial(self.main_tree.addTopLevelItem, root)])

        if "法律" in scope and not self.flash_law_thread.isRunning():
            self.find_lawitems = []

            def add_ex(kindparent, root):
                kindparent.addChild(root)
                if kindparent.data(0, Qt.UserRole)[0] == "" and not kindparent.isExpanded():
                    self.main_tree.expandItem(kindparent)

            for kind in self.all_laws.keys():
                if self.abort:
                    return
                kindparent = self.make_item(kind, data=["", kind], bold=True, icon="icons\\book.png", txtc=False)
                kindparent.setForeground(0, QColor(0, 0, 255))
                havetable = [self.main_tree.topLevelItem(i).text(0) for i in range(self.main_tree.topLevelItemCount())]
                for name in self.all_laws[kind].keys():
                    if self.abort:
                        return
                    txt = self.all_laws[kind][name][0] + "\n" + "".join(self.all_laws[kind][name][1])
                    n = 0
                    for i in self.these:
                        if i in txt:
                            n = n + 1
                    if n != len(self.these):
                        continue
                    else:
                        root = self.make_item(name, bold=True, data=[kind, name])
                        self.find_lawitems.append(root)
                        if kindparent not in havetable:
                            self.do_something_sig.emit([partial(self.main_tree.addTopLevelItem, kindparent)])
                        self.do_something_sig.emit([partial(add_ex, kindparent, root)])
                    index = 0
                    for code in self.all_laws[kind][name][1]:
                        if self.abort:
                            return
                        if re.search("(" + ")|(".join(self.these) + ")", code) is not None:
                            child = QTreeWidgetItem()
                            child.setText(0, code)
                            child.setFirstColumnSpanned(True)
                            child.setData(0, Qt.UserRole, [name, index])
                            if re.search("^第.+?[编章节][\W\s]+?", code) is not None:
                                child.setForeground(0, QColor(219, 48, 34))
                            self.do_something_sig.emit([partial(add_ex, root, child)])
                        index = index + 1

        time.sleep(0.5)
        if self.main_tree.topLevelItemCount() == 0:
            root = self.make_item("什么也没找到！", data=["", "什么也没找到"])
            root.setForeground(0, QColor(Qt.red))
            self.do_something_sig.emit([partial(self.main_tree.addTopLevelItem, root)])


if __name__ == '__main__':
    serverName = 'AppServer'
    socketT = QLocalSocket()
    sockShow = QUdpSocket()
    socketT.connectToServer(serverName)
    # 判定应用服务是否正常链接，如正常则证明程序实例已经在运行
    if socketT.waitForConnected(500):
        sockShow.writeDatagram(b'show', QHostAddress.LocalHost, 8849)
    else:
        log_dir = os.path.join(os.getcwd(), 'log')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        cgitb.enable(format='text', logdir=log_dir)
        app = QApplication(sys.argv)
        QApplication.setQuitOnLastWindowClosed(False)
        localServer = QLocalServer()
        localServer.listen(serverName)
        win = Attorney()
        win.initialite()
        sys.exit(app.exec_())

    # # 如果没有实例运行，则创建应用服务器并监听服务
    # else:
    #     localServer = QLocalServer()
    #     localServer.listen(serverName)
    #     # 原始处理逻辑
    #     win = Attorney()
    #     # win.show()
    #     win.initialite()
    #     sys.exit(app.exec_())
