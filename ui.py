from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, \
    QLabel, QDateEdit, QPlainTextEdit, QComboBox, QCheckBox, QAction, QTreeWidget, QTextEdit, \
    QToolButton, QStackedLayout, QGraphicsDropShadowEffect, QFormLayout, QDialog, QMessageBox, QSplitter, QProgressBar


# class MyTreeWidget(QTreeWidget):
#
#     def __init__(self):
#         super(MyTreeWidget, self).__init__()
#         self.setMouseTracking(True)
#
#     def mouseMoveEvent(self, event):
#         pass
#         # for i in range(9):
#         #     button = self.itemWidget(self.topLevelItem(i),1)
#         #     if button is None:
#         #         continue
#         #     if self.topLevelItem(i) == self.itemAt(event.pos()):
#         #         button.setVisible(True)
#         #     else:
#         #         button.setVisible(False)
#         # print(event.pos(), event.globalPos())  # 返回值分别为控件的整数坐标值 和 屏幕的整数坐标值
#         # print(event.windowPos(), event.screenPos())  # 返回值分别为控件的浮点坐标值 和


class MyWin(QWidget):
    def __init__(self):
        super(MyWin, self).__init__()
        self.main_layout = QHBoxLayout(self)
        self.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.setWindowTitle("律师助手")

        self.vbox1 = QVBoxLayout()
        self.user_layout = QHBoxLayout()
        self.user = QToolButton()
        self.user_name = QLabel()
        self.task_button = QPushButton("日志")
        self.law_button = QPushButton("法律")
        self.progress = QProgressBar(self.law_button)
        self.allcase_button = QPushButton("案件")
        self.collect_button = QPushButton("收藏")
        self.files_button = QPushButton("文件")
        self.newlaw_button = QToolButton()
        self.newlaw_label = QLabel(self.newlaw_button)

        self.setting_win = QDialog()
        self.setting_layout = QFormLayout(self.setting_win)

        #splitter
        self.splitter2 = QSplitter(QtCore.Qt.Horizontal)

        # show win
        self.show_win = QWidget()
        self.vbox2 = QVBoxLayout(self.show_win)
        self.search = QLineEdit()
        self.search_which = QHBoxLayout()
        self.main_tree = QTreeWidget()
        self.newlaw_tree = QTreeWidget()
        self.many = QLabel()

        #stacklayout
        self.stack_win = QWidget()
        self.stack = QStackedLayout(self.stack_win)
        self.label = QLabel()
        self.show_law_txt = QTextEdit()

        self.record = QToolButton()

        #case inf
        self.case_inf = QWidget()
        self.gbox = QGridLayout(self.case_inf)
        self.hbox2 = QHBoxLayout()
        self.label_start = QLabel("收案日期")
        self.case_start = QDateEdit()
        self.label_end = QLabel("结案日期")
        self.case_end = QDateEdit()
        self.case_end_ok = QCheckBox("结案")
        self.make_paper = QToolButton()
        self.tree_case = QTreeWidget()
        self.splitter1 = QSplitter(QtCore.Qt.Vertical)
        self.reson_txt = QPlainTextEdit()
        self.law_txt = QPlainTextEdit()

        # write win
        self.log_win = QWidget()
        self.log_gbox1 = QGridLayout(self.log_win)
        self.log_case_label = QLabel("案件")
        self.log_case = QComboBox()
        self.log_name_label = QLabel("主题")
        self.log_name = QLineEdit()
        self.log_start_label = QLabel("开始日期")
        self.log_start = QDateEdit()
        self.log_end_label = QLabel("结束日期")
        self.log_end = QDateEdit()
        self.log_end_ok = QCheckBox("完成")
        self.log_record_layout = QVBoxLayout()
        self.log_what = QPlainTextEdit()
        # self.log_how_label = QLabel("措施")
        # self.log_how = QPlainTextEdit()
        # self.log_why_label = QLabel("依据")
        # self.log_why = QPlainTextEdit()

        # collect win
        self.collect_win = QWidget()
        self.collect_gbox1 = QVBoxLayout(self.collect_win)
        self.collect_hbox = QHBoxLayout()
        self.collect_name_label = QLabel("主题")
        self.collect_name = QLineEdit()
        self.collect_content = QTextEdit()

        #more inf win
        self.more_inf_win = QWidget()
        self.more_inf_gbox = QGridLayout(self.more_inf_win)
        self.more_inf_txt = QPlainTextEdit()

        self.msgbox = QMessageBox(self)

        self.setup_Ui()

    def add_shadow(self,button):
        # 添加阴影
        self.effect_shadow = QGraphicsDropShadowEffect(self)
        self.effect_shadow.setOffset(0, 0)  # 偏移
        self.effect_shadow.setBlurRadius(30)  # 阴影半径
        self.effect_shadow.setColor(QtCore.Qt.darkGray)  # 阴影颜色
        button.setGraphicsEffect(self.effect_shadow)  # 将设置套用到button窗口中

    def setup_Ui(self):
        self.resize(900,720)
        self.main_layout.addLayout(self.vbox1)
        self.main_layout.addWidget(self.splitter2,1)
        self.splitter2.addWidget(self.show_win)
        self.splitter2.addWidget(self.stack_win)

        self.setting_win.setWindowTitle("设置")
        self.setting_win.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.setting_win.setFixedSize(400,160)
        self.setting_layout.addRow("用户名:",QLineEdit())
        self.setting_layout.addRow("头  像:",QLineEdit())
        self.setting_layout.addRow("案件库:",QLineEdit())
        self.setting_layout.addRow("座右铭:",QLineEdit())
        self.setting_layout.addRow(QHBoxLayout())
        self.setting_layout.itemAt(0, 1).widget().setMaxLength(5)
        self.setting_layout.itemAt(1,1).widget().addAction(QAction(QIcon("icons\\more.png"),"",self),QLineEdit.TrailingPosition)
        self.setting_layout.itemAt(2,1).widget().addAction(QAction(QIcon("icons\\more.png"),"",self),QLineEdit.TrailingPosition)
        # self.setting_layout.itemAt(3,1).widget().addAction(QAction(QIcon("add.png"),"",self),QLineEdit.TrailingPosition)
        self.setting_layout.itemAt(4,1).layout().addStretch(1)
        self.setting_layout.itemAt(4, 1).layout().addWidget(QPushButton("默认"))
        self.setting_layout.itemAt(4, 1).layout().addWidget(QPushButton("确定"))
        self.setting_layout.itemAt(4,1).layout().addWidget(QPushButton("取消"))

        #foun win
        self.vbox1.setContentsMargins(0, 0, 0, 0)
        self.user_layout.setContentsMargins(0, 0, 0, 0)
        self.user_layout.addStretch(1)
        self.user_layout.addWidget(self.user)
        self.user_layout.addStretch(1)
        self.vbox1.addLayout(self.user_layout)
        self.vbox1.addWidget(self.user_name)
        self.vbox1.addWidget(self.task_button)
        self.vbox1.addWidget(self.law_button)
        self.vbox1.addWidget(self.allcase_button)
        self.vbox1.addWidget(self.collect_button)
        self.vbox1.addSpacing(30)
        self.vbox1.addWidget(self.files_button)
        self.vbox1.addStretch(1)
        self.vbox1.addWidget(self.newlaw_button)

        self.user.setFixedSize(69,69)
        self.user.setIconSize(QSize(69,69))
        self.user.setStyleSheet("background-color:transparent;border-radius:45px;border:none;")
        # self.add_shadow(self.user)
        self.user_name.setAlignment(QtCore.Qt.AlignCenter)

        self.task_button.setIcon(QIcon("icons\\tasks.png"))
        self.law_button.setIcon(QIcon("icons\\book.png"))
        self.allcase_button.setIcon(QIcon("icons\\paper.png"))
        self.collect_button.setIcon(QIcon("icons\\star.png"))
        self.files_button.setIcon(QIcon("icons\\folder.png"))
        self.newlaw_button.setIcon(QIcon("icons\\book_new.png"))

        self.task_button.setIconSize(QSize(35,35))
        self.law_button.setIconSize(QSize(35,35))
        self.allcase_button.setIconSize(QSize(35,35))
        self.collect_button.setIconSize(QSize(35,35))
        self.files_button.setIconSize(QSize(35,35))
        self.newlaw_button.setIconSize(QSize(35,35))

        self.task_button.setFixedSize(85,40)
        self.law_button.setFixedSize(85,40)
        self.allcase_button.setFixedSize(85,40)
        self.collect_button.setFixedSize(85,40)
        self.files_button.setFixedSize(85,40)
        self.newlaw_button.setFixedSize(40,40)
        self.newlaw_label.setFixedSize(12,12)
        self.newlaw_label.move(28,0)

        self.progress.setFixedSize(75,6)
        self.progress.setTextVisible(False)
        self.progress.move(5,34)
        self.newlaw_button.setStyleSheet("background-color:transparent;")
        self.newlaw_label.setStyleSheet("background-color:red;border-radius:6px;")
        self.newlaw_label.setVisible(False)

        #splitter2
        self.splitter2.setContentsMargins(0,0,0,0)

        # show_win
        self.vbox2.setContentsMargins(0, 0, 0, 0)
        self.vbox2.addWidget(self.search)
        self.search_which.setContentsMargins(0, 0, 0, 0)
        for i in ["日志","案件","收藏","法律"]:
            check = QCheckBox(i)
            if i == "法律":
                check.setCheckState(QtCore.Qt.Checked)
            self.search_which.addWidget(check)
        self.search_which.addStretch(1)
        # last_page = QToolButton()
        # last_page.setIcon(QIcon("icons\\last.png"))
        # last_page.setIconSize(QSize(10,10))
        # last_page.setObjectName("上一页")
        # last_page.setStyleSheet("background-color:transparent;")
        # next_page = QToolButton()
        # next_page.setIcon(QIcon("icons\\next.png"))
        # next_page.setIconSize(QSize(10,10))
        # next_page.setObjectName("下一页")
        # next_page.setStyleSheet("background-color:transparent;")
        # self.search_which.addWidget(last_page)
        # self.search_which.addWidget(next_page)
        self.vbox2.addLayout(self.search_which)
        self.vbox2.addWidget(self.main_tree, 1)
        self.vbox2.addWidget(self.many)
        self.vbox2.addWidget(self.newlaw_tree)

        action = QAction(self)
        action.setIcon(QIcon("icons\\add_ok.png"))
        self.search.addAction(action,QLineEdit.TrailingPosition)

        action = QAction(self)
        action.setIcon(QIcon("icons\\search.png"))
        self.search.addAction(action,QLineEdit.TrailingPosition)
        self.search.setPlaceholderText("任意关键字（空格分开）")
        self.search.setObjectName("搜索")

        self.main_tree.setHeaderHidden(True)
        self.main_tree.setSortingEnabled(False)
        self.main_tree.setMinimumWidth(360)
        self.main_tree.setObjectName("main_tree")
        self.many.setAlignment(QtCore.Qt.AlignRight)
        self.main_tree.setStyleSheet('''QTreeWidget {
            color:black;
            background-color:transparent;
            font-size:16px;
            border:none;}''')
        self.newlaw_tree.setSortingEnabled(False)
        self.newlaw_tree.setRootIsDecorated(False)
        self.newlaw_tree.setFixedHeight(260)
        self.newlaw_tree.setColumnCount(2)
        self.newlaw_tree.setColumnWidth(0,255)
        self.newlaw_tree.setColumnWidth(1,5)
        # self.newlaw_tree.se
        # self.newlaw_tree.
        self.newlaw_tree.setHeaderLabels(["新法速递","发布时间"])
        self.many.setAlignment(QtCore.Qt.AlignRight)
        self.newlaw_tree.setStyleSheet('''QTreeWidget {
                    color:black;
                    background-color:transparent;
                    font-size:16px;
                    border:none;
                    }
                    QHeaderView::section {
                    background-color: transparent;
                    color: gray;
                    padding: 0px;
                    border-top:0px solid;
                    border-bottom:1px solid;
                    border-left:0px solid;
                    border-right:0px solid;
                }''')
        self.newlaw_tree.header().setDefaultAlignment(QtCore.Qt.AlignCenter)

        self.stack.addWidget(self.case_inf)
        self.stack.addWidget(self.log_win)
        self.stack.addWidget(self.collect_win)
        self.stack.addWidget(self.show_law_txt)
        self.stack.addWidget(self.label)
        self.stack.setCurrentIndex(4)

        #label
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.show_law_txt.setReadOnly(True)
        self.show_law_txt.setObjectName("法条")

        self.record.setIcon(QIcon("icons\\add_case_ok.png"))
        self.record.setIconSize(QSize(25,25))
        self.record.setStyleSheet("background-color:transparent;border:0px;border-radius:12px")
        self.record.setObjectName("记录完成")
        self.add_shadow(self.record)

        #case_inf
        self.gbox.setContentsMargins(0, 0, 0, 0)
        self.gbox.setColumnStretch(2,1)
        self.gbox.setRowStretch(2,1)
        self.gbox.setRowStretch(5,1)
        self.gbox.addLayout(self.hbox2,0,0,1,4)#共5列
        self.hbox2.setContentsMargins(0, 0, 0, 0)
        self.hbox2.addWidget(self.label_start)
        self.hbox2.addWidget(self.case_start)
        self.hbox2.addWidget(self.label_end)
        self.hbox2.addWidget(self.case_end)
        self.hbox2.addWidget(self.case_end_ok)
        self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.make_paper)

        self.case_start.setCalendarPopup(True)
        self.case_end.setCalendarPopup(True)
        self.case_end.setEnabled(False)
        self.make_paper.setIcon(QIcon("icons\\notes.png"))
        self.make_paper.setIconSize(QSize(25, 25))
        self.make_paper.setStyleSheet("background-color:transparent;")
        self.add_shadow(self.make_paper)

        # self.gbox.addWidget(,0,4)
        self.gbox.addWidget(self.tree_case,1,0,6,2)#共9行
        self.splitter1.setContentsMargins(0,0,0,0)
        self.splitter1.addWidget(self.reson_txt)
        self.splitter1.addWidget(self.law_txt)
        self.gbox.addWidget(self.splitter1,1,2,6,2)
        self.tree_case.setMinimumWidth(360)
        self.tree_case.setHeaderHidden(True)
        self.tree_case.setColumnCount(2)
        self.tree_case.setColumnWidth(0,320)
        self.tree_case.setColumnWidth(1,5)
        self.tree_case.setSortingEnabled(False)
        self.tree_case.setStyleSheet('''QTreeWidget {
                    }''')
        self.tree_case.setStyleSheet('''QTreeWidget {
                    color:gray;
                    background-color:rgba(255,255,255,160);
                    font-size:16px;
                    border:none;}
                    QTreeWidget::item:hover {
                    background-color: transparent}
                    QTreeWidget::item::selected{
                    color:gray;background-color:transparent;}
                    QTreeWidget::branch::selected{background-color:transparent;}''')
        self.tree_case.setRootIsDecorated(False)

        self.reson_txt.setObjectName("事实理由")
        self.reson_txt.setPlaceholderText("事实理由/答辩意见：")
        self.law_txt.setObjectName("法律法规")
        self.law_txt.setPlaceholderText("法律法规：")

        # log_win
        self.log_gbox1.setContentsMargins(0, 0, 0, 0)
        self.log_gbox1.setColumnStretch(1,1)
        self.log_gbox1.setRowStretch(3,1)
        self.log_gbox1.addWidget(self.log_case_label,0,0)
        self.log_gbox1.addWidget(self.log_case, 0,1,1,2)
        self.log_gbox1.addWidget(self.log_name_label,1,0)
        self.log_gbox1.addWidget(self.log_name, 1,1,1,2)
        self.log_gbox1.addWidget(self.log_start_label,0,3)
        self.log_gbox1.addWidget(self.log_start,0,4)
        self.log_gbox1.addWidget(self.log_end_label,1,3)
        self.log_gbox1.addWidget(self.log_end,1,4)
        self.log_gbox1.addWidget(self.log_end_ok,1,5)
        self.log_record_layout.setContentsMargins(0,0,0,0)
        self.log_record_layout.addStretch(1)
        self.log_gbox1.addLayout(self.log_record_layout,0,7,2,1)
        self.log_gbox1.addWidget(self.log_what,2,0,3,8)
        self.log_what.setPlaceholderText("内容：")

        self.log_case.setEditable(True)
        self.log_start.setCalendarPopup(True)
        self.log_end.setCalendarPopup(True)
        self.log_end.setEnabled(False)

        # collect_win
        self.collect_hbox.setContentsMargins(0, 0, 0, 0)
        self.collect_gbox1.setContentsMargins(0, 0, 0, 0)
        self.collect_hbox.addWidget(self.collect_name_label)
        self.collect_hbox.addWidget(self.collect_name, 1)
        # self.collect_hbox.addStretch()
        self.collect_gbox1.addLayout(self.collect_hbox)
        self.collect_content.setPlaceholderText("内容：")
        self.collect_gbox1.addWidget(self.collect_content)

        #more inf win
        self.more_inf_win.resize(300,400)
        self.more_inf_win.setWindowTitle("详细信息")
        self.more_inf_win.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.more_inf_gbox.setColumnStretch(1,1)
        self.more_inf_gbox.setRowStretch(1,1)
        self.more_inf_txt.setObjectName("更多")
        self.more_inf_gbox.addWidget(self.more_inf_txt,0,0,3,3)

        self.msgbox.setWindowTitle("提示")
        self.msgbox.setIcon(QMessageBox.Warning)
        self.msgbox.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
        self.msgbox.button(QMessageBox.Ok).setText("确认")
        self.msgbox.button(QMessageBox.No).setText("取消")