import copy
import json
import os
import pickle
import re
import shutil
import sqlite3
import sys
import time
import winreg
from datetime import datetime
from functools import partial
from itertools import chain

from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QCursor, QTextCursor, QFont, QPixmap, QColor
from PyQt5.QtWidgets import QMenu, QApplication, QTreeWidgetItem, QFileDialog, QAbstractItemView, QInputDialog

import output_docx
from ui import *

class MyThread(QThread):
    mysig = pyqtSignal()
    def __init__(self,fun):
        super(MyThread, self).__init__()
        self.fun = fun
    def run(self):
        for i in self.fun:
            i()
        self.mysig.emit()


class Attorney(MyWin):
    additem_sig = pyqtSignal(list)
    show_law_sig = pyqtSignal(str)
    newlaw_sig = pyqtSignal()
    addlaw_sig = pyqtSignal(str)
    prog_sig = pyqtSignal(int)

    def __init__(self):
        super(Attorney, self).__init__()
        self.all_laws = {}
        self.me = {"name":"","img":"","casedir":""}
        self.current_log = ["","","","","",""]
        self.current_case = self.product_currentcase()
        self.current_collect = []
        self.main_tree_items = {"cases":[],"logs":[],"collects":[],"法律": {}}
        self.find_law_items = {}
        self.law_items = []
        self.current_item = [None,None,None,None,None]
        self.clipboard = QApplication.clipboard()
        self.lineedit_menu = QMenu(self)
        self.additem_sig.connect(self.additem)
        self.show_law_sig.connect(self.show_law_txt.append)
        self.addlaw_sig.connect(self.msg)
        self.prog_sig.connect(self.progress.setValue)
        self.add_law_thread = MyThread
        self.find_thread = MyThread([self.find_in_all])
        self.find_thread.mysig.connect(self.remove_nolaw)
        self.showlaw_thread = MyThread([self.append_law])
        self.newlaw_thread = MyThread([self.get_new_law])
        self.newlaw_sig.connect(lambda :self.newlaw_label.setVisible(True))

        self.log_thread = MyThread([self.load_alllogs])
        self.log_thread.mysig.connect(lambda :self.which_founction("日志"))

        self.law_thread = MyThread([self.load_alllaws])
        self.law_thread.mysig.connect(self.show_law_all)

        self.first_thread = MyThread([self.load_allcases,self.load_allcollects,self.load_alllaws])
        self.first_thread.mysig.connect(lambda :self.law_button.blockSignals(False))

        self.flash_thread = MyThread([self.load_alllogs,self.load_allcases,self.load_allcollects])
        self.flash_thread.mysig.connect(self.show_flash)
        self.start_flash_thread = MyThread([self.flash_all])

        self.write_thread = MyThread([self.write_log_case_collect])

        self.mutex = QMutex()
        with open("style.qss","r") as t:
            self.stylesheet = t.read()
        self.setStyleSheet(self.stylesheet)
        self.setting_win.setStyleSheet(self.stylesheet)
        self.more_inf_win.setStyleSheet(self.stylesheet)
        self.msgbox.setStyleSheet("QLabel {color:black;}")
        self.label.setStyleSheet("color:black;font-size:24px;")
        self.main_button_style = '''
            QPushButton {
                background-color:transparent;
                border:none;
                border-radius:12px;
                font-size:14px;
            }
            QPushButton:hover {
                background-color:rgb(193, 233, 242);
                border:none;
            }
            QPushButton:pressed {
                background-color:rgb(148, 216, 233);
                border:none;
            }'''

    def show_flash(self):
        self.which_founction(self.search.actions()[0].objectName())

    def flash_all(self):
        while True:
            try:
                m = os.path.getmtime(self.me["casedir"]+"\\database.db")
                break
            except:
                time.sleep(3)
        while True:
            try:
                nm = os.path.getmtime(self.me["casedir"]+"\\database.db")
                if nm != m:
                    self.flash_thread.start()
                    m = nm
            except:
                pass
            time.sleep(1)

    def get_new_law(self):
        try:
            os.startfile("getnewlaws.exe")
        except:
            return
        while True:
            if os.path.exists("newlaw.db"):
                break
            else:
                time.sleep(2)
        while True:
            time.sleep(1)
            if os.path.exists("ok"):
                os.remove("ok")
                break
        if os.path.exists("new"):
            self.newlaw_sig.emit()

    def show_newlaws(self):
        if self.newlaw_tree.isVisible():
            self.newlaw_tree.setVisible(False)
            return
        if not os.path.exists("newlaw.db"):
            return
        conn = sqlite3.connect("newlaw.db")
        cur = conn.cursor()
        laws = cur.execute("select * from newlaw").fetchall()
        self.newlaw_tree.clear()
        for i in laws:
            root = QTreeWidgetItem(self.newlaw_tree)
            root.setText(0,i[0])
            root.setText(1,i[1])
            root.setToolTip(0,i[0])
        self.newlaw_tree.setVisible(True)
        if os.path.exists("new"):
            self.newlaw_label.setVisible(False)
            os.remove("new")

    def msg(self,txt):
        self.msgbox.setText(txt)
        return self.msgbox.exec_()

    def setting_show(self):
        for i, j in zip(range(4),self.me.keys()):
            self.setting_layout.itemAt(i, 1).widget().setText(self.me[j])
        self.setting_win.exec_()

    def setting(self,result):
        w = 0
        if (result == 3 and not os.path.exists("profile")) or result == 1:
                self.me["name"] = "用户1"
                self.me["img"] = "icons\\userdefault.png"
                self.me["casedir"] = "案件库"
                self.me["words"] = "心诚所至，金石为开"
                if not os.path.exists("案件库"):
                    os.mkdir("案件库")
                w = 1
        if w == 0:
            self.me["name"] = self.setting_layout.itemAt(0, 1).widget().text()
            self.me["img"] = self.setting_layout.itemAt(1, 1).widget().text()
            self.me["casedir"] = self.setting_layout.itemAt(2, 1).widget().text()
            self.me["words"] = self.setting_layout.itemAt(3, 1).widget().text()
            w = 1
        if w == 1 and result != 3:
            with open("profile", "w", encoding="utf-8") as t:
                t.write(json.dumps(self.me,ensure_ascii=False))
            self.set_me()
        self.setting_win.close()

    def set_me(self):
        pixmap = self.circleImage(self.me["img"])
        self.user.setIcon(QIcon(pixmap))
        self.user_name.setText(self.me["name"])
        self.label.setText(self.me["words"])

    def output_paper(self):
        def get_alllog():
            fetchall = self.record_database("select * from logs where caseid like '"+self.current_case["id"]+"'")
            output_docx.output_paper(self.me["casedir"]+"\\"+self.current_case["案件名"],fetchall,'工作日志')

        def get_paper(what):
            output_docx.output_paper(self.me["casedir"] + "\\" + self.current_case["案件名"], self.current_case, what)

        groupBox_menu = QMenu(self)
        actionA = QAction(QIcon('icons\\paper.png'), u'生成起诉状', self)
        actionA.triggered.connect(lambda :get_paper("民事起诉状"))
        groupBox_menu.addAction(actionA)

        actionB = QAction(QIcon('icons\\defence.png'), u'生成答辩状', self)
        actionB.triggered.connect(lambda :get_paper("答辩状"))
        groupBox_menu.addAction(actionB)

        actionE = QAction(QIcon('icons\\tasks.png'), u'导出日志', self)
        actionE.triggered.connect(get_alllog)
        groupBox_menu.addAction(actionE)
        groupBox_menu.popup(QCursor.pos())

    def circleImage(self,imagePath):
        source = QPixmap(imagePath)
        size = min(source.width(), source.height())

        target = QPixmap(size, size)
        target.fill(QtCore.Qt.transparent)

        qp = QtGui.QPainter(target)
        qp.setRenderHints(qp.Antialiasing)
        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        qp.setClipPath(path)

        sourceRect = QtCore.QRect(0, 0, size, size)
        sourceRect.moveCenter(source.rect().center())
        qp.drawPixmap(target.rect(), source, sourceRect)
        qp.end()

        return target

    def initialite(self):
        def selectfile(t):
            if t == 1:
                file = QFileDialog.getOpenFileName(self,"选择图片",os.path.expanduser('~'),'图片文件 (*.png *.jpg *.jpeg)')[0]
            else:
                file = QFileDialog.getExistingDirectory(self,"选择文件夹",os.path.expanduser('~'))
            if file != "":
                self.setting_layout.itemAt(t, 1).widget().setText(file.replace("/","\\"))
        self.setting_layout.itemAt(1, 1).widget().actions()[0].triggered.connect(lambda :selectfile(1))
        self.setting_layout.itemAt(2, 1).widget().actions()[0].triggered.connect(lambda :selectfile(2))

        self.setting_layout.itemAt(4, 1).layout().itemAt(1).widget().clicked.connect(lambda :self.setting(1))
        self.setting_layout.itemAt(4, 1).layout().itemAt(2).widget().clicked.connect(lambda :self.setting(2))
        self.setting_layout.itemAt(4, 1).layout().itemAt(3).widget().clicked.connect(lambda :self.setting(3))

        if os.path.exists("profile"):
            with open("profile","r",encoding="utf-8") as t:
                self.me = json.loads(t.read())
        else:
            self.setting_show()
        self.set_me()
        self.show()
        self.user.clicked.connect(self.setting_show)
        self.files_button.setStyleSheet(self.main_button_style)
        self.make_paper.clicked.connect(self.output_paper)
        for i in [2,3,4,5,7]:
            widget = self.vbox1.itemAt(i).widget()
            widget.clicked.connect(partial(self.which_founction,widget.text()))
        self.newlaw_button.clicked.connect(self.show_newlaws)
        self.law_button.blockSignals(True)
        for i in [0,1,2,3]:
            self.search_which.itemAt(i).widget().clicked.connect(self.find_prepare)

        def movetofirst():
            textCursor = self.show_law_txt.textCursor()
            textCursor.movePosition(QTextCursor.Start,QTextCursor.MoveAnchor)
            self.show_law_txt.setTextCursor(textCursor)
        self.showlaw_thread.mysig.connect(movetofirst)

        self.search.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.search.returnPressed.connect(self.find_prepare)
        self.search.actions()[0].triggered.connect(self.add_new)
        self.search.actions()[1].triggered.connect(self.find_prepare)

        self.main_tree.clicked.connect(self.show_one)
        self.main_tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_tree.customContextMenuRequested.connect(self.tree_menu)
        self.main_tree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.tree_case.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.record.clicked.connect(self.write_log_case_collect)
        self.collect_content.textChanged.connect(self.write_thread.start)

        self.more_inf_txt.textChanged.connect(self.cach_case_inf)
        self.reson_txt.textChanged.connect(self.cach_case_inf)

        self.law_txt.textChanged.connect(self.cach_case_inf)
        self.case_end_ok.stateChanged.connect(lambda :self.case_end.setEnabled(not self.case_end.isEnabled()))

        self.log_case.currentTextChanged.connect(self.fill_case_name)
        self.log_end_ok.stateChanged.connect(lambda :self.log_end.setEnabled(not self.log_end.isEnabled()))

        who = [self.show_law_txt, self.reson_txt, self.law_txt,self.collect_content, self.search,self.log_what]
        for i in who:
            i.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            i.customContextMenuRequested.connect(self.txt_menu)
            if who.index(i) >= 5:
                i.textChanged.connect(self.write_thread.start)
        self.log_thread.start()
        self.first_thread.start()
        self.start_flash_thread.start()
        self.newlaw_tree.setVisible(False)
        self.newlaw_thread.start()

    def record_database(self,word,arg=""):
        if not os.path.exists(self.me["casedir"]):
            return 0
        conn = sqlite3.connect(self.me["casedir"]+"\\database.db")
        cur = conn.cursor()
        try:
            cur.execute(word,arg)
        except:
            return 0
        if "select" in word:
            return cur.fetchall()
        if re.search("(insert)|(delete)|(create)|(update)",word) is not None:
            conn.commit()
            conn.close()
        return 1

    def fill_case_name(self):
        self.mutex.lock()
        self.log_case.blockSignals(True)
        if self.log_case.currentText() == "":
            fetchall = []
        else:
            fetchall = self.record_database("select * from cases where casename like '%"+self.log_case.currentText()+"%'")
            if fetchall == 0:
                fetchall = []
        if len(fetchall) > 0:
            self.log_case.clear()
            for i in fetchall:
                self.log_case.addItem(i[1],i)
            self.current_case = self.product_currentcase(self.log_case.currentData())
            self.setWindowTitle(self.current_case["案件名"])
        else:
            self.current_case = self.product_currentcase()
            no = self.log_case.currentText()
            self.log_case.clear()
            self.log_case.setCurrentText(no)
            self.setWindowTitle("律师助手")
        if len(fetchall) > 1:
            self.log_case.showPopup()
        self.log_case.blockSignals(False)
        self.mutex.unlock()

    def write_log_case_collect(self):
        self.mutex.lock()
        what = self.stack.currentIndex()
        if what == 0:
            key = self.get_case()
            if key == 0:
                self.mutex.unlock()
                return
            if self.case_end.isEnabled():
                self.current_case["结案日期"] = self.case_end.date().toString("yyyy-MM-dd")
            else:
                self.current_case["结案日期"] = ""
            many = 14
            data = [self.current_case[i] for i in key[0:6]]+[pickle.dumps(self.current_case[j]) for j in key[6:]]
        if what == 1:
            self.current_log = [self.current_log[0],self.log_start.date().toString("yyyy-MM-dd"),self.current_case["id"] if self.current_case["id"] != "" else self.log_case.currentText(), self.log_name.text(), self.log_what.toPlainText(),
                               self.log_end.date().toString("yyyy-MM-dd") if self.log_end.isEnabled() else ""]
            many = 6
            data = self.current_log
        if what == 2:
            self.current_collect = (self.current_collect[0],str(time.strftime("%Y-%m-%d %H%M%S")),self.collect_name.text(), self.collect_content.toPlainText())
            many = 4
            data = self.current_collect
        cachtxt = ["case.json","log.json","collect.json"][what]
        if not self.sender():
            with open(cachtxt,"w",encoding="utf-8") as l:
                l.write(json.dumps(data,ensure_ascii=False))
            self.mutex.unlock()
        else:
            table = ["cases","logs","collects"][what]
            result = self.record_database("insert or replace into "+table+" values (?"+",?"*(many-1)+")",data)
            if result == 0:
                self.msg("案件库已断开")
                self.mutex.unlock()
                return
            if os.path.exists(cachtxt):
                os.remove(cachtxt)
            self.search.actions()[0].setIcon(QIcon("icons\\add_ok.png"))
            # txt = [re.sub("\s[0-9]{6}\s", " ", data[1]),data[1]+ " " + data[3] + "▶" + re.sub("^[0-9\s-]*?","",self.current_case["案件名"] if self.current_case["案件名"] != "" else self.log_case.currentText()),
            # data[1][0:10] + " " + data[2]][what]
            # root = None
            # index = ["日志", "法律", "案件", "收藏"].index(self.search.actions()[0].objectName())
            # if self.add_show == "main_tree":
            #     root = self.current_item[index]
            # else:
            #     for i in range(self.main_tree.topLevelItemCount()):
            #         if data[0] == self.main_tree.topLevelItem(i).data(0,QtCore.Qt.UserRole)[0]:
            #             root = self.main_tree.topLevelItem(i)
            #             break
            #     if root is None:
            #         root = QTreeWidgetItem()
            #         root.setFirstColumnSpanned(True)
            #         self.main_tree_items[table].insert(0,root)
            #         self.main_tree.insertTopLevelItem(0,root)
            # icon = ["paper.png" if self.current_case["结案日期"] == "" else "paper_ok.png",
            #         "tasks.png" if self.current_log[-1] == "" else "tasks_ok.png", "star.png"]
            # if "ok" in icon[what]:
            #     root.setForeground(0, QColor(100, 100, 100))
            # else:
            #     root.setForeground(0, QColor(0, 0, 0))
            # root.setIcon(0, QIcon(icon[what]))
            # root.setText(0, txt)
            # root.setData(0, QtCore.Qt.UserRole, data)
            # self.add_show = "main_tree"
            # self.main_tree.setCurrentItem(root)
            # self.current_item[index] = root
            self.mutex.unlock()

    def get_case(self):
        client = 0
        for i in ["原告","被告","第三人"]:
            for j in self.current_case[i]:
                if i in ["原告","被告"] and (j[0] == "" or re.search("[\\\/:\*\?\|<>\"]", j[0]) is not None):
                    self.msg("请输入"+i+"名称\n且不能包含\\ / : * ? | \" < >")
                    return 0
                if j[2] == "委托人":
                    client = 1
        if client == 0:
            self.msg("请右键点击当事人设置委托人")
            return 0
        if self.current_case["案件名"] == "":
            self.cach_case_inf()
        elif re.sub("\s[0-9]{6}\s"," ",self.current_case["案件名"]) != re.sub("\s[0-9]{6}\s"," ",self.casename()):
            self.cach_case_inf("rename")
        self.setWindowTitle(self.current_case["案件名"])
        return ["id","案件名", "事实理由", "法律法规", "备注", "结案日期","原告", "被告", "第三人", "案由", "诉讼请求",
                   "管辖法院", "法官", "诉讼阶段"]

    def casename(self):
        yuan = self.current_case["原告"][0][0]
        bei = self.current_case["被告"][0][0]
        name = str(self.case_start.date().toString("yyyy-MM-dd"))+str(time.strftime(" %H%M%S ")) + yuan +"VS"+bei
        return name

    def product_currentcase(self,arg=""):
        case = {"id": "", "案件名": "", "事实理由": "", "法律法规": "", "备注": "","结案日期":"", "原告": [["", "", ""]],
                             "被告": [["", "", ""]], "第三人": [["", "", ""]], "案由": [["", ""]],
                             "诉讼请求": [["", ""]], "管辖法院": [["", ""]], "法官": [["", ""]], "诉讼阶段": [["", ""]]}
        if arg != "":
            for i, j in zip(list(case.keys()), list(arg)):
                if list(case.keys()).index(i) >= 6:
                    j = pickle.loads(j)
                case[i] = j
        return case

    def cach_case_inf(self,arg=""):
        who = self.sender().objectName()
        if who == "事实理由":
            self.current_case["事实理由"] = self.reson_txt.toPlainText()
        if who == "法律法规":
            self.current_case["法律法规"] = self.law_txt.toPlainText()
        if who == "备注":
            self.current_case[self.tree_case.currentItem().parent().text(0)] = self.tree_case.itemWidget(self.tree_case.currentItem(), 0).toPlainText()
        if who == "LineEdit":
            parent = self.current_case[self.tree_case.currentItem().parent().text(0)]
            parent[self.tree_case.currentIndex().row()][0] = self.tree_case.itemWidget(self.tree_case.currentItem(),0).text()
        if who == "更多":
            if self.tree_case.currentItem().parent().text(0) == "诉讼请求":
                self.tree_case.itemWidget(self.tree_case.currentItem(), 0).setText(self.more_inf_txt.toPlainText())
            parent = self.current_case[self.tree_case.currentItem().parent().text(0)]
            parent[self.tree_case.currentIndex().row()][1] = self.more_inf_txt.toPlainText()
        if who in ["设置委托人","取消委托人"]:
            parent = self.current_case[self.tree_case.currentItem().parent().text(0)]
            if who == "设置委托人":
                txt = "委托人"
                icon = "icons\\client.png"
            else:
                icon = txt = ""
            parent[self.tree_case.currentIndex().row()][2] = txt
            self.tree_case.currentItem().setIcon(1, QIcon(icon))
        if who == "记录完成":
            name = self.casename()
            if arg == "":
                self.current_case["id"] = str(self.case_start.date().toString("yyyyMMdd"))+str(time.strftime("%H%M%S"))
                os.mkdir(self.me["casedir"]+"\\"+name)
            else:
                if os.path.exists(self.me["casedir"]+"\\"+self.current_case["案件名"]):
                    shutil.move(self.me["casedir"]+"\\"+self.current_case["案件名"],self.me["casedir"]+"\\"+name)
                else:
                    os.mkdir(self.me["casedir"]+"\\" + name)
            self.current_case["案件名"] = name
        with open("case.json", "w", encoding="utf-8") as tt:
            tt.write(json.dumps(self.current_case,ensure_ascii=False))

    def tree_menu(self):
        def up_law():
            if self.sender().text() == u'删除':
                yn = self.msg("确定删除？")
                if yn == QMessageBox.Ok:
                    if self.main_tree.currentItem() in self.law_items[0]+self.law_items[1:]:
                        self.search_law("del",*table_data)
                        self.search_law("del","常用法律",table_data[1])
                        self.main_tree.currentItem().parent().removeChild(self.main_tree.currentItem())
                        del self.all_laws[table_data[0]][table_data[1]]
                        return
                    if self.main_tree.currentItem() in other:
                        fetchall = self.record_database("delete from {} where id='{}'".format(table_data[0],table_data[1][0]))
                        if fetchall == 0:
                            self.msg("案件库已断开")
                            return
                return
            if self.sender().text() == u'加入常用':
                current_law = self.search_law("select title from {} where title='{}'".format(*table_data))[0]
                self.search_law("add",current_law[0])
                add = self.main_tree_items["法律"][table_data[0]].takeChild(self.main_tree.currentIndex().row())
                self.main_tree_items["法律"]["常用法律"].insertChild(0,add)

                self.law_items.remove(add)
                self.law_items[0].append(add)
            else:
                self.search_law("del","常用法律",table_data[1])
                rem = self.main_tree_items["法律"]["常用法律"].takeChild(self.main_tree.currentIndex().row())
                self.main_tree_items["法律"][table_data[0]].insertChild(0,rem)
                self.law_items[0].remove(rem)
                self.law_items.append(rem)


        if self.main_tree.currentItem() is None:
            return
        txt = ""
        table_data = self.main_tree.currentItem().data(0,QtCore.Qt.UserRole)
        icon = 'upload.png'
        if self.main_tree.currentItem() in self.law_items[1:]:
            txt = u'加入常用'
        elif self.main_tree.currentItem() in self.law_items[0]:
            txt = u'移出常用'
        other = self.main_tree_items["logs"] + self.main_tree_items["cases"] + self.main_tree_items["collects"]
        groupBox_menu = QMenu(self)
        if txt != "":
            actionA = QAction(QIcon("icons\\"+icon), txt, self)
            actionA.triggered.connect(up_law)
            groupBox_menu.addAction(actionA)
        if self.main_tree.currentItem() in other or self.main_tree.currentItem() in self.law_items[0] + self.law_items[1:]:
            actionB = QAction(QIcon("icons\\delete.png"), u"删除", self)
            actionB.triggered.connect(up_law)
            groupBox_menu.addAction(actionB)
        groupBox_menu.popup(QCursor.pos())

    def txt_menu(self):
        groupBox_menu = QMenu(self)
        sender = self.sender()
        if self.sender().objectName() == "搜索":
            selectedText = sender.selectedText()
        else:
            selectedText = sender.textCursor().selectedText()
        if selectedText != "":
            actionA = QAction(QIcon('icons\\clipboard.png'), u'复制', self)
            actionA.triggered.connect(lambda :sender.copy())#textCursor().selectedText()
            groupBox_menu.addAction(actionA)
        if sender.objectName() != "法条":
            actionE = QAction(QIcon('icons\\paste.png'), u'粘贴', self)
            actionE.triggered.connect(lambda :sender.paste())
            groupBox_menu.addAction(actionE)

        def collect():
            sender.copy()
            if self.clipboard.text() == "":
                return
            if os.path.exists("collect.json"):
                with open("collect.json", "r", encoding="utf-8") as t:
                    self.current_collect = json.loads(t.read())
            else:
                self.current_collect = [str(time.strftime("%Y%m%d%H%M%S")), "", "", ""]
            self.current_collect[-1] = self.current_collect[-1] + self.clipboard.text()+"\n"
            with open("collect.json", "w", encoding="utf-8") as t:
                t.write(json.dumps(self.current_collect,ensure_ascii=False))

        if selectedText != "":
            actionB = QAction(QIcon('icons\\star.png'), u'收藏', self)
            actionB.setObjectName("收藏")
            actionB.triggered.connect(collect)
            groupBox_menu.addAction(actionB)

        def add_to_case():
            case = list(self.sender().data())
            sender.copy()
            case[3] = case[3] + "\n"+self.clipboard.text()
            fetchall = self.record_database("update cases set laws='{}' where id='{}'".format(case[3],case[0]))
            if fetchall == 0:
                self.msg("案件库已断开")
                return
            for i in self.main_tree_items["cases"]:
                if i.data(0,QtCore.Qt.UserRole)[1][0] == case[0]:
                    i.setData(0,QtCore.Qt.UserRole,case)

        if selectedText != "":
            menu = QMenu(u'加入到', self)
            menu.setIcon(QIcon("icons\\paper.png"))
            for i in self.main_tree_items["cases"]:
                case = i.data(0,QtCore.Qt.UserRole)[1]
                if case[5] == "" or case[0] == self.current_case["id"]:
                    action = QAction(re.sub("\s[0-9]{6}\s", " ", case[1]),self)
                    action.setData(case)
                    action.triggered.connect(add_to_case)
                    menu.addAction(action)
            groupBox_menu.addMenu(menu)

        groupBox_menu.popup(QCursor.pos())

    def prepare(self,w=4):
        self.stack.setCurrentIndex(w)
        if w == 0:
            self.hbox2.addWidget(self.record)
        if w == 1:
            self.log_record_layout.addWidget(self.record)
        if w == 2:
            self.collect_hbox.addWidget(self.record)

    def load_alllogs(self):
        self.mutex.lock()
        fetchall = self.record_database('''create table if not exists logs (
                            id TEXT PRIMARY KEY,
                            startdate TEXT,
                            caseid TEXT,
                            logname TEXT,
                            what TEXT,
                            enddate TEXT
                            )''')
        if fetchall == 0:
            self.mutex.unlock()
            return
        fetchall = self.record_database("select * from logs order by id desc")
        self.main_tree_items["logs"] = []
        for i in fetchall:
            casename = self.record_database("select casename from cases where id like '"+i[2]+"'")
            if len(casename) == 0:
                name = i[2]
            else:
                name = re.sub("^[0-9\s-]*","",casename[0][0])
            task = i[1] + " " + i[3] + "▶" + name
            root = QTreeWidgetItem()
            root.setText(0, task)
            root.setFirstColumnSpanned(True)
            root.setData(0, QtCore.Qt.UserRole, ["logs",i])
            root.setToolTip(0,task)
            if i[-1] == "":
                root.setIcon(0,QIcon("icons\\tasks.png"))
            else:
                root.setIcon(0, QIcon("icons\\tasks_ok.png"))
                root.setForeground(0, QColor(100, 100, 100))
            self.main_tree_items["logs"].append(root)
        self.mutex.unlock()

    def search_law(self,sql,*arg):
        conn = sqlite3.connect("LawData.db")
        cur = conn.cursor()
        if "select" in sql or "pragma" in sql:
            return cur.execute(sql).fetchall()
        if "add" in sql:
            cur.execute("insert or replace into 常用法律 (title) values(?)", (arg[0],))
        if "del" in sql:
            cur.execute("delete from {} where title='{}'".format(arg[0],arg[1]))
        # if
        conn.commit()

    def make_item(self,txt,parent=None,data=None,bold=False,icon=None):
        l = ""
        ll = re.findall("(^[a-zA-Z])",txt)
        if len(ll) != 0:
            l=ll[0].upper()+" "
        txt = l+re.sub("^[a-z0-9_]*","",txt)
        item = QTreeWidgetItem()
        item.setText(0, txt)
        item.setToolTip(0, txt)
        item.setFirstColumnSpanned(True)
        if data is not None:
            item.setData(0, QtCore.Qt.UserRole, data)
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)
        if parent is not None:
            parent.addChild(item)
        if icon is not None:
            item.setIcon(0,QIcon(icon))
        return item

    def load_alllaws(self):
        table = self.search_law("select name from sqlite_master where type='table'")
        all_laws_title = {}
        many = 0
        for i in table:
            all_laws_title[i[0]] = self.search_law("select title from {} order by title asc".format(i[0]))
            if i[0] != table[0][0]:
                many = many + len(all_laws_title[i[0]])
        self.progress.setRange(0,many)
        if all_laws_title == {}:
            return
        self.main_tree_items["法律"] = {}
        usual_law = ()
        many = 0
        for tbl in all_laws_title.keys():
            kindparent = self.make_item(tbl, bold=True, data=tbl)
            kindparent.setIcon(0, QIcon("icons\\book.png"))
            self.main_tree_items["法律"][tbl] = kindparent
            if tbl == "常用法律":
                self.law_items.append([])
                usual_law = all_laws_title[tbl]
                continue
            self.all_laws[tbl] = {}
            for i in all_laws_title[tbl]:
                if (i[0],) in usual_law:
                    root = self.make_item(i[0], self.main_tree_items["法律"]["常用法律"], [tbl, i[0]], True)
                    self.law_items[0].append(root)
                else:
                    root = self.make_item(i[0], kindparent, [tbl, i[0]], True)
                    self.law_items.append(root)
                root.setForeground(0, QColor(90, 90, 90))
                index = 0
                parent = root
                self.all_laws[tbl][i[0]] = pickle.loads(self.search_law("select * from {} where title='{}'".format(tbl,i[0]))[0][1])
                for j in self.all_laws[tbl][i[0]]:
                    if j is None:
                        continue
                    if re.search("(^第.+?编\s+)", j) is not None:
                        if re.search("^第.+?[章编]\s+",parent.text(0)) is not None:
                            parent = root
                        parent = self.make_item(j.replace("\n", ""), parent, index)
                    elif re.search("^第.+?章\s+", j) is not None:
                        if re.search("^第.+?章\s+",parent.text(0)) is not None:
                            parent = parent.parent()
                        parent = self.make_item(j.replace("\n", ""), parent, index)
                    elif re.search("(^第.+?节\s+)|(^[一二三四五六七八九十]+[、.\s]+)", j) is not None:
                        self.make_item(j.replace("\n", ""), parent, index)
                    index = index + 1
                many = many + 1
                self.prog_sig.emit(many)

    def load_allcases(self):
        self.mutex.lock()
        fetchall = self.record_database('''create table if not exists cases (
                                            id TEXT PRIMARY KEY,
                                            casename TEXT,
                                            reasons TEXT,
                                            laws TEXT,
                                            mark TEXT,
                                            enddate TEXT,
                                            plaintiff BLOB,
                                            defendant BLOB,
                                            third BLOB,
                                            cause BLOB,
                                            claims BLOB,
                                            court BLOB,
                                            judge BLOB,
                                            stage BLOB
                                            )''')
        if fetchall == 0:
            self.mutex.unlock()
            return
        fetchall = self.record_database("select * from cases order by id desc")
        self.main_tree_items["cases"] = []
        for i in fetchall:
            root = QTreeWidgetItem()
            root.setText(0, re.sub("\s[0-9]{6}\s", " ", i[1]))
            root.setFirstColumnSpanned(True)
            root.setData(0, QtCore.Qt.UserRole, ["cases",i])
            root.setToolTip(0, re.sub("\s[0-9]{6}\s", " ", i[1]))
            if i[5] == "":
                root.setIcon(0,QIcon("icons\\paper.png"))
            else:
                root.setIcon(0, QIcon("icons\\paper_ok.png"))
                root.setForeground(0,QColor(100,100,100))
            self.main_tree_items["cases"].append(root)
        self.mutex.unlock()

    def load_allcollects(self):
        self.mutex.lock()
        fetchall = self.record_database('''create table if not exists collects (
                                                            id TEXT PRIMARY KEY,
                                                            editdate TEXT,
                                                            theme TEXT,
                                                            content TEXT
                                                            )''')
        if fetchall == 0:
            self.mutex.unlock()
            return
        fetchall = self.record_database("select * from collects order by editdate desc")
        self.main_tree_items["collects"] = []
        for i in fetchall:
            root = QTreeWidgetItem()
            root.setText(0, i[1][0:10] + " " + i[2])
            root.setIcon(0,QIcon("icons\\star.png"))
            root.setFirstColumnSpanned(True)
            root.setData(0, QtCore.Qt.UserRole, ["collects",i])
            root.setToolTip(0, i[1][0:10] + " " + i[2])
            self.main_tree_items["collects"].append(root)
        self.mutex.unlock()

    def show_log_all(self):
        self.main_tree.setRootIsDecorated(False)
        for i in range(self.main_tree.topLevelItemCount()):
            self.main_tree.takeTopLevelItem(0)
        doing = 0
        for i in self.main_tree_items["logs"]:
            if i.data(0, QtCore.Qt.UserRole)[1][-1] == "":
                self.main_tree.addTopLevelItem(i)
                doing = doing + 1
        self.many.setText("待办：" + str(doing))
        self.many.setVisible(True)

    def show_law_all(self):
        self.main_tree.setRootIsDecorated(True)
        for i in range(self.main_tree.topLevelItemCount()):
            self.main_tree.takeTopLevelItem(0)
        self.progress.setVisible(False)
        self.main_tree.addTopLevelItems(list(self.main_tree_items["法律"].values()))
        self.main_tree.expandItem(self.main_tree_items["法律"]["常用法律"])#setExpanded(self.main_tree_items["法律"]["常用法律"].index(),True)#self.main_tree_items["法律"]["常用法律"].setExpanded(True)

    def show_case_all(self):
        for i in range(self.main_tree.topLevelItemCount()):
            self.main_tree.takeTopLevelItem(0)
        self.main_tree.setRootIsDecorated(False)
        done = 0
        doing = 0
        for i in self.main_tree_items["cases"]:
            if i.data(0,QtCore.Qt.UserRole)[1][5] != "":
                done = done + 1
            else:
                doing = doing + 1
                self.main_tree.addTopLevelItem(i)
        self.many.setText("未结案件："+str(doing)+"  已结案件："+str(done))
        self.many.setVisible(True)

    def show_collect_all(self):
        for i in range(self.main_tree.topLevelItemCount()):
            self.main_tree.takeTopLevelItem(0)
        self.main_tree.setRootIsDecorated(False)
        self.main_tree.addTopLevelItems(self.main_tree_items["collects"])

    def open_filedir(self):
        if not os.path.exists(self.me["casedir"]):
            self.msg("案件库已断开")
            return
        if os.path.exists(self.me["casedir"]+"\\" + self.current_case["案件名"]):
            os.startfile(self.me["casedir"]+"\\" + self.current_case["案件名"])
        else:
            yn = self.msg("文件夹已被删除\n重新创建？")
            if yn == QMessageBox.Ok:
                os.mkdir(self.me["casedir"]+"\\" + self.current_case["案件名"])
                self.open_filedir()

    def which_founction(self,default="日志"):
        fun = [self.show_log_all,self.show_law_all,self.show_case_all,self.show_collect_all,self.open_filedir]
        index = ["日志","法律","案件","收藏","文件"].index(default)
        if index != 4:
            self.search.actions()[0].setObjectName(default)
            self.prepare()
            for i in [0,1,2,3]:
                self.search_which.itemAt(i).widget().setVisible(False)
            self.many.setVisible(False)
            for j in range(4):
                widget = self.vbox1.itemAt(j+2).widget()
                if j == index:
                    widget.setStyleSheet("background-color:rgb(148, 216, 233);border:none;border-radius:12px;font-size:14px;")
                else:
                    widget.setStyleSheet(self.main_button_style)
        fun[index]()
        if self.current_item[index] is not None:
            self.main_tree.setCurrentItem(self.current_item[index])
            self.main_tree.scrollToItem(self.current_item[index],QAbstractItemView.PositionAtCenter)

    def append_law(self):
        self.mutex.lock()
        txt = re.sub("●", "", self.main_tree.currentItem().text(0))
        if txt[-1] != "\n":
            txt = txt + "\n"
        zjb = re.findall("^第.+?([条章节编])[、.\s]*?", txt)
        if len(zjb) == 0:
            zjb = re.findall("^([一二三四五六七八九十0-9])+[、.\s]*?", txt)
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
        p = lawitem = self.main_tree.currentItem()
        if lawitem in self.main_tree_items["法律"].values():
            self.mutex.unlock()
            return
        while True:
            if p.parent() is None:
                break
            lawitem = p
            p = p.parent()
        law_name = lawitem.text(0)
        self.show_law_sig.emit("<font><b>" + law_name + "<br></font>")
        if law_name == txt[0:-1]:
            index = 0
        else:
            index = self.main_tree.currentItem().data(0, QtCore.Qt.UserRole)
        these = re.sub("(^\s+)|(\s+$)", "", self.search.text()).split(" ")
        table_title = lawitem.data(0,QtCore.Qt.UserRole)
        current_law = self.all_laws[table_title[0]][table_title[1]]
        for i in these:
            if i == "":
                these.remove(i)
        start = next = index
        for i in current_law[index:]:
            if i is None:
                continue
            if re.search("^第.+?" + zjb + "\s+", i) is not None or re.search("^" + zjb + "+[、.\s]*?", i) is not None:
                if zjb == "编":
                    start = start + 1
                if next > start and law_name != txt[0:-1]:
                    break
            for j in these:
                if j in i:
                    i = i.replace(j, "<font color='#DB3022'><b>" + j + "</font>")
            if re.search("(^第.+?条\s*)|(^[0-9]+[、.\s]*?)", i) is not None:
                self.show_law_sig.emit("<font color='#DB3022'>●</font>" + i.replace("\n", "<br>"))
            else:
                self.show_law_sig.emit("<font><b>" + i.replace("\n", "<br>") + "</font>")
            next = next + 1
        self.mutex.unlock()

    def add_law(self):
        while True:
            time.sleep(1)
            if os.path.exists("nolaw"):
                with open("nolaw", "rb") as t:
                    law_txts = pickle.loads(t.read())
                self.addlaw_sig.emit("下列文件无法条：\n" + law_txts)
                os.remove("nolaw")
            if not os.path.exists("newlaw"):
                self.law_thread.start()
                break


    def show_log_a(self):
        self.log_start.setDate(datetime.strptime(self.current_log[1], "%Y-%m-%d"))
        if self.current_log[-1] == "":
            self.log_end_ok.setChecked(False)
            self.log_end.setDate(datetime.today())
        else:
            self.log_end_ok.setChecked(True)
            self.log_end.setDate(datetime.strptime(self.current_log[-1], "%Y-%m-%d"))
        fetchall = self.record_database("select * from cases where id like '" + self.current_log[2] + "'")
        self.log_case.blockSignals(True)
        self.log_case.clear()
        if fetchall != 0 and len(fetchall) != 0:
            self.current_case = self.product_currentcase(fetchall[0])
            self.log_case.addItem(self.current_case["案件名"], self.current_case)
        else:
            self.current_case = self.product_currentcase()
            self.log_case.setCurrentText(self.current_log[2])
        self.log_case.blockSignals(False)
        self.setWindowTitle("律师助手" if self.current_case["案件名"] == "" else self.current_case["案件名"])
        self.log_name.setText(self.current_log[3])
        self.log_what.blockSignals(True)
        self.log_what.setPlainText(self.current_log[4])
        self.log_what.blockSignals(False)
        self.prepare(1)

    def show_collect_a(self):
        self.collect_content.blockSignals(True)
        txt = self.current_collect[3]
        these = re.sub("(^\s*)|(\s*$)", "", self.search.text()).split(" ")
        for i in these:
            txt = txt.replace(i, "<font color='#DB3022'><b>" + i + "</font>").replace("\n", "<br>")
        self.collect_name.setText(self.current_collect[2])
        self.collect_content.setText(txt)
        self.collect_content.blockSignals(False)
        self.prepare(2)

    def add_new(self):
        if self.search.actions()[0].objectName() != "法律":
            self.search.actions()[0].setIcon(QIcon("icons\\add.png"))
            if self.search_which.itemAt(0).widget().isVisible():
                self.which_founction(self.search.actions()[0].objectName())

        def add_log():
            if os.path.exists("log.json"):
                with open("log.json","r",encoding="utf-8") as t:
                    self.current_log = json.loads(t.read())
            else:
                self.current_log = [str(time.strftime("%Y%m%d%H%M%S")),str(time.strftime("%Y-%m-%d")),self.current_case["id"],"","",""]
            self.show_log_a()

        def add_case():
            if os.path.exists("case.json"):
                with open("case.json", "r", encoding="utf-8") as txt:
                    self.current_case = json.loads(txt.read())
            else:
                self.current_case = self.product_currentcase()
            self.setWindowTitle("律师助手" if self.current_case["案件名"] == "" else self.current_case["案件名"])
            self.prepare(0)
            self.case_inf_initalize()

        def add_law():
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
            dir = winreg.QueryValueEx(key, "Desktop")[0]
            lawfiles = QFileDialog.getOpenFileNames(self, '导入法律', dir, '纯文本 (*.txt)')[0]
            if len(lawfiles) != 0:
                self.current_item[1] = None
                tbl = QInputDialog(self)
                tbl.setCancelButtonText("取消")
                tbl.setOkButtonText("确定")
                tbl.setWindowTitle("类型")
                tbl.setLabelText("请选择")
                tbl.setComboBoxItems(["法律","宪法","司法解释","行政法规","地方性法规","部门规章","规范性文件"])
                if tbl.exec_() == 1:
                    table = tbl.textValue()
                else:
                    return
                self.progress.setValue(0)
                self.progress.setVisible(True)
                newlaw = {table: lawfiles}
                with open("newlaw", "wb") as t:
                    t.write(pickle.dumps(newlaw))
                try:
                    os.system("create_law.exe")
                except:
                    return
                self.add_law_thread = MyThread([self.add_law])
                self.add_law_thread.start()

        def add_collect():
            if os.path.exists("collect.json"):
                with open("collect.json","r",encoding="utf-8") as t:
                    self.current_collect = json.loads(t.read())
            else:
                self.current_collect = (str(time.strftime("%Y%m%d%H%M%S")),"","","")
            self.show_collect_a()

        if self.search.actions()[0].objectName() == "案件":
            add_case()
        elif self.search.actions()[0].objectName() == "日志":
            add_log()
        elif self.search.actions()[0].objectName() == "收藏":
            add_collect()
        elif self.search.actions()[0].objectName() == "法律":
            add_law()

    def show_one(self):
        def show_log():
            self.current_item[0] = self.main_tree.currentItem()
            self.current_log = self.main_tree.currentItem().data(0,QtCore.Qt.UserRole)[1]
            self.show_log_a()

        def show_law():
            if not self.search_which.itemAt(0).widget().isVisible():
                self.current_item[1] = self.main_tree.currentItem()
            self.show_law_txt.clear()
            self.prepare(3)
            self.showlaw_thread.start()

        def show_case():
            self.current_item[2] = self.main_tree.currentItem()
            self.current_case = self.product_currentcase(self.main_tree.currentItem().data(0, QtCore.Qt.UserRole)[1])
            self.setWindowTitle("律师助手" if self.current_case["案件名"] == "" else self.current_case["案件名"])
            self.prepare(0)
            self.case_inf_initalize()

        def show_collect():
            self.current_item[3] = self.main_tree.currentItem()
            self.current_collect = self.main_tree.currentItem().data(0,QtCore.Qt.UserRole)[1]
            self.show_collect_a()

        item = self.main_tree.currentItem()
        if item in self.main_tree_items["cases"]:
            show_case()
        elif item in self.main_tree_items["logs"]:
            show_log()
        elif item in self.main_tree_items["collects"]:
            show_collect()
        elif item not in list(self.main_tree_items["法律"].values())+list(self.find_law_items.values()):
            show_law()

    def case_inf_initalize(self):
        if self.current_case["案件名"] == "":
            self.case_start.setDate(datetime.today())
        else:
            self.case_start.setDate(datetime.strptime(self.current_case["案件名"][0:10],"%Y-%m-%d"))

        if self.current_case["结案日期"] == "":
            self.case_end_ok.setChecked(False)
            self.case_end.setDate(datetime.today())
        else:
            self.case_end_ok.setChecked(True)
            self.case_end.setDate(datetime.strptime(self.current_case["结案日期"],"%Y-%m-%d"))

        self.tree_case.clear()
        labels = ["原告", "被告", "第三人", "案由", "诉讼请求", "管辖法院", "法官", "诉讼阶段","备注"]
        icon = ["fight.png","defence.png","binoculars.png","paper.png","notepad.png","court.png","judge.png","progress.png","flag.png"]
        self.case_menu()
        for i,j in zip(labels,icon):
            root = QTreeWidgetItem(self.tree_case)
            root.setIcon(0,QIcon("icons\\"+j))
            root.setText(0, i)
            self.creat_line(root)
            if labels.index(i) in [3,8]:
                continue
            add = QToolButton()
            add.setObjectName("加")
            add.setStyleSheet("background-color:transparent;border:none;")
            add.setIcon(QIcon("icons\\add.png"))
            add.setIconSize(QSize(15, 15))
            add.setMaximumSize(25, 25)
            add.clicked.connect(partial(self.creat_line,root))
            self.tree_case.setItemWidget(root, 1, add)
        self.tree_case.expandAll()
        self.reson_txt.blockSignals(True)
        self.reson_txt.setPlainText(self.current_case["事实理由"])
        self.reson_txt.blockSignals(False)
        self.law_txt.blockSignals(True)
        self.law_txt.setPlainText(self.current_case["法律法规"])
        self.law_txt.blockSignals(False)

    def case_menu(self):
        self.lineedit_menu = QMenu(self)
        actionA = QAction(QIcon('icons\\client.png'), u'设置委托人', self)
        actionA.triggered.connect(self.cach_case_inf)
        actionA.setObjectName("设置委托人")
        self.lineedit_menu.addAction(actionA)

        actionB = QAction(QIcon('icons\\delete.png'), u'删除', self)
        actionB.setObjectName("删除")
        self.lineedit_menu.addAction(actionB)

        def delit():
            del self.current_case[self.tree_case.currentItem().parent().text(0)][
                self.tree_case.currentIndex().row()]
            self.tree_case.currentItem().parent().removeChild(self.tree_case.currentItem())
            self.cach_case_inf()

        actionB.triggered.connect(delit)

    def creat_line(self,root):
        if root.text(0) == "备注":
            child = QTreeWidgetItem(root)
            beizhu = QPlainTextEdit()
            beizhu.setPlainText(self.current_case["备注"])
            beizhu.setObjectName("备注")
            beizhu.textChanged.connect(self.cach_case_inf)
            beizhu.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            beizhu.customContextMenuRequested.connect(self.txt_menu)
            self.tree_case.setItemWidget(child, 0, beizhu)
            return

        def action_enable(line, act):
            if line.text() != "":
                act.setEnabled(True)
            else:
                act.setEnabled(False)
            self.cach_case_inf()

        if self.sender().objectName() == "加":
            self.current_case[root.text(0)].append(["","",""] if root.text(0) in ["原告","被告","第三人"] else ["",""])
            ran = [["","",""]]
        else:
            ran = self.current_case[root.text(0)]
        for i in ran:
            child = QTreeWidgetItem(root)
            if root.text(0) in ["原告","被告","第三人"] and i[2] == "委托人":
                child.setIcon(1, QIcon("icons\\client.png"))
            lineedit = QLineEdit()
            lineedit.setText(i[0])
            lineedit.setStyleSheet("color:black;font-weight:bold;font-size:14px;border-top:0px solid;border-bottom:1px solid;border-left:0px solid;border-right:0px solid;")
            # lineedit.setStyleSheet("color:black;font-size:16px;border:none;background-color:transparent;")
            lineedit.setContentsMargins(3, 3, 3, 3)
            lineedit.setMaxLength(35)
            lineedit.setObjectName("LineEdit")
            self.tree_case.setItemWidget(child, 0, lineedit)
            lineedit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

            def show_menu():
                parent = self.tree_case.currentItem().parent().text(0)
                if parent in ["原告", "被告", "第三人"]:
                    self.lineedit_menu.actions()[0].setEnabled(True)
                    if self.current_case[parent][self.tree_case.currentIndex().row()][2] == "委托人":
                        text = "取消委托人"
                    else:
                        text = "设置委托人"
                    self.lineedit_menu.actions()[0].setText(text)
                    self.lineedit_menu.actions()[0].setObjectName(text)
                else:
                    self.lineedit_menu.actions()[0].setEnabled(False)

                self.lineedit_menu.popup(QCursor.pos())

            if root.text(0) not in ["案由"]:
                lineedit.customContextMenuRequested.connect(show_menu)
            action = QAction(self)
            action.setIcon(QIcon("icons\\more.png"))
            action.triggered.connect(self.more_inf)
            if i[0] == "" and root.text(0) != "诉讼请求":
                action.setEnabled(False)
            if root.text(0) == "诉讼请求":
                # lineedit.setStyleSheet("padding-right: 20px;")
                lineedit.setPlaceholderText("点击编辑👉")
                lineedit.setReadOnly(True)
                lineedit.textChanged.connect(self.cach_case_inf)
            lineedit.addAction(action, QLineEdit.TrailingPosition)
            if root.text(0) != "诉讼请求":
                lineedit.textChanged.connect(partial(action_enable, lineedit, action))

    def more_inf(self):
        self.more_inf_win.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.more_inf_win.move(self.x()+(self.width()-self.more_inf_win.width())//2,self.y()+(self.height()-self.more_inf_win.height())//2)
        self.more_inf_win.show()
        txt = self.current_case[self.tree_case.currentItem().parent().text(0)][self.tree_case.currentIndex().row()][1]
        self.more_inf_txt.blockSignals(True)
        self.more_inf_txt.setPlainText(txt)
        cursor = self.more_inf_txt.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.more_inf_txt.setTextCursor(cursor)
        self.more_inf_txt.blockSignals(False)

    def find_prepare(self):
        for i in range(self.main_tree.topLevelItemCount()):
            self.main_tree.takeTopLevelItem(0)
        for i in [0,1,2,3]:
            self.search_which.itemAt(i).widget().setVisible(True)
        self.main_tree.setRootIsDecorated(True)
        self.find_thread.start()

    def remove_nolaw(self):
        for i in self.find_law_items.values():
            if i.childCount() == 0:
                self.main_tree.takeTopLevelItem(self.main_tree.indexOfTopLevelItem(i))


    def additem(self,arg=None):
        if arg[0] == self.main_tree:
            arg[0].addTopLevelItem(arg[1])
        else:
            arg[0].addChild(arg[1])
            if arg[0].parent() is None:
                self.main_tree.expandItem(arg[0])

    def find_in_all(self):
        self.mutex.lock()
        scope = []
        for i in range(4):
            if self.search_which.itemAt(i).widget().isChecked():
                scope.append(["logs","cases","collects","laws"][i])
        these = re.sub("(^\s*)|(\s*$)","",self.search.text()).split(" ")
        for i in these:
            if i == "":
                these.remove(i)
        if len(these) == 0:
            self.mutex.unlock()
            return
        for which in scope:
            if which == "laws":
                continue
            for i in self.main_tree_items[which]:
                n = 0
                for txt in these:
                    m = 0
                    for k in i.data(0,QtCore.Qt.UserRole)[1][1:]:
                        if which == "cases" and m >= 5:
                            k = "\n".join(list(chain.from_iterable(pickle.loads(k))))
                        m = m + 1
                        if txt in k:
                            n = n + 1
                            break
                if n == len(these):
                    self.additem_sig.emit([self.main_tree,i])

        if "laws" not in scope:
            self.mutex.unlock()
            return

        find_law = []
        self.find_law_items = {}
        for kind in self.all_laws.keys():
            kindparent = self.make_item(kind,bold=True,icon="icons\\book.png")
            kindparent.setForeground(0, QColor(0, 0, 255))
            self.find_law_items[kind] = kindparent
            self.additem_sig.emit([self.main_tree,kindparent])
            for title in self.all_laws[kind].keys():
                if re.search("(" + ")|(".join(these) + ")", title) is not None:
                    root = self.make_item(title,bold=True,data=[kind,title])
                    find_law.append(title)
                    # root.setForeground(0, QColor(90, 90, 90))
                    self.additem_sig.emit([kindparent, root])
                txt = "".join(self.all_laws[kind][title])
                n = 0
                for i in these:
                    if i in txt:
                        n = n + 1
                if n != len(these):
                    continue
                index = 0
                for j in self.all_laws[kind][title]:
                    if re.search("(" + ")|(".join(these) + ")", j) is not None:
                        if title not in find_law:
                            root = self.make_item(title, bold=True, data=[kind, title])
                            find_law.append(title)
                            # root.setForeground(0, QColor(90, 90, 90))
                            self.additem_sig.emit([kindparent, root])
                        child = QTreeWidgetItem()
                        child.setText(0, "●" + j)
                        child.setFirstColumnSpanned(True)
                        child.setData(0, QtCore.Qt.UserRole, index)
                        self.additem_sig.emit([root, child])
                    index = index + 1

        self.mutex.unlock()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Attorney()
    # win.show()
    win.initialite()
    sys.exit(app.exec_())