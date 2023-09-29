from PyQt5.QtCore import QSize, Qt, QFileInfo
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, \
    QLabel, QDateEdit, QPlainTextEdit, QComboBox, QCheckBox, QAction, QTreeWidget, QTextEdit, \
    QToolButton, QStackedLayout, QFormLayout, QDialog, QMessageBox, QSplitter, QSpinBox, QTableWidget, QHeaderView, \
    QRadioButton, QButtonGroup, QAbstractItemView, QListWidget, QListWidgetItem, QFileIconProvider, QScrollArea, \
    QListView, QTimeEdit


class ComboBox(QComboBox):

    def __init__(self):
        super(ComboBox,self).__init__()
        self.view = QListView()
        self.setView(self.view)

class Calendar(QWidget):
    def __init__(self):
        super(Calendar, self).__init__()
        self.grid = QVBoxLayout(self)
        self.grid.setContentsMargins(0,0,0,0)
        self.navition = QHBoxLayout()
        self.lm = QToolButton()
        self.lm.setObjectName("-1")
        self.lm.setIcon(QIcon("icons\\last.png"))
        self.lm.setIconSize(QSize(15,15))
        self.ys = QSpinBox()
        self.ys.setMinimumWidth(80)
        self.ys.setMaximum(9999)
        self.ys.setSuffix("年")
        self.mc = ComboBox()
        self.mc.setMinimumWidth(60)
        self.nm = QToolButton()
        self.nm.setObjectName("1")
        self.nm.setIcon(QIcon("icons\\next.png"))
        self.nm.setIconSize(QSize(15,15))

        self.alllog = QRadioButton("全部")
        self.alllog.setChecked(True)
        self.caselog = QRadioButton("案件")
        self.clientlog = QRadioButton("法务")

        self.bg = QButtonGroup()
        self.bg.addButton(self.alllog,1)
        self.bg.addButton(self.caselog,2)
        self.bg.addButton(self.clientlog,3)


        self.navition.addStretch(1)
        self.navition.addWidget(self.lm)
        self.navition.addWidget(self.ys)
        self.navition.addWidget(self.mc)
        self.navition.addWidget(self.nm)
        self.navition.addStretch(1)
        self.navition.addWidget(self.alllog)
        self.navition.addWidget(self.caselog)
        self.navition.addWidget(self.clientlog)

        for i in range(1,13):
            self.mc.addItem(str(i)+"月",("" if len(str(i)) == 2 else "0") + str(i))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setRowCount(6)
        self.table.setHorizontalHeaderLabels(["周一","周二","周三","周四","周五","周六","周日"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("border:none;")

        self.table.horizontalHeader().setStyleSheet("QHeaderView::section{background-color:gray;border:0px solid;font:13pt '宋体';color: white;}")

        self.grid.addLayout(self.navition)
        self.grid.addWidget(self.table)


class MsgBox(QMessageBox):

    def __init__(self):
        super(MsgBox, self).__init__()
        self.setWindowTitle("提示")
        self.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
        self.button(QMessageBox.Ok).setText("确认")
        self.button(QMessageBox.No).setText("取消")
        self.setStyleSheet("QMessageBox{color:black;font-size:18px;}")


class ListWidget(QListWidget):
    def __init__(self):
        super(ListWidget,self).__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.paths = []
        self.hb = QHBoxLayout(self)
        self.file_draghere = QLabel("拖动文件到此处")
        self.hb.addStretch(1)
        self.hb.addWidget(self.file_draghere)
        self.hb.addStretch(1)
        self.file_draghere.setAlignment(Qt.AlignCenter)
        self.file_draghere.setStyleSheet("background-color:transparent;color:gray;font-size:30px;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QListWidget{background-color:transparent;}")

    def deleteItem(self,file=None):
        if file in [None,False]:
            file = self.sender().objectName()
        if file not in self.paths:
            return
        index = self.paths.index(file)
        self.takeItem(index)
        del self.paths[index]
        if len(self.paths) == 0:
            self.file_draghere.setVisible(True)

    def createwidget(self,txt=None,foun=None,icon=None):
        widget = QWidget()
        hb = QHBoxLayout(widget)
        hb.setContentsMargins(0, 0, 0, 0)
        delete = QToolButton()
        delete.setIcon(QIcon("icons\\"+icon))
        delete.setFixedSize(15, 15)
        delete.setIconSize(QSize(15, 15))
        delete.clicked.connect(foun)
        delete.setObjectName(txt[0])
        if len(txt) == 2:
            text = QLabel(txt[1].split("/")[-1])
            text.setStyleSheet("color:black;font-size:18px;")
            text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            hb.addWidget(text)
        hb.addStretch(1)
        hb.addWidget(delete)
        hb.addSpacing(7)
        return widget

    def dragEnterEvent(self,event):
        urls = event.mimeData().urls()
        if len(urls) != 0:
            self.file_draghere.setVisible(False)
        for i in urls:
            file = i.toLocalFile()
            if file in self.paths:
                continue
            fileInfo = QFileInfo(file)
            fileIcon = QFileIconProvider()
            icon = QIcon(fileIcon.icon(fileInfo))
            item = QListWidgetItem()
            item.setIcon(icon)
            self.paths.append(file)
            self.addItem(item)
            self.setItemWidget(item,self.createwidget([file,file],self.deleteItem,"delete.png"))
    def hideEvent(self, event):
        if self.count() > 0:
            self.clear()
            self.file_draghere.setVisible(True)


class MyWin(QWidget):

    def __init__(self):
        super(MyWin, self).__init__()
        self.main_layout = QHBoxLayout(self)
        self.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.setWindowIconText("大律师")
        self.setWindowTitle("大律师")

        self.vbox1 = QVBoxLayout()
        self.user_layout = QHBoxLayout()
        self.user = QToolButton()
        self.user_name = QLabel()
        self.log_button = QPushButton("日志")
        self.law_button = QPushButton("法律")
        self.case_button = QPushButton("案件")
        self.client_button = QPushButton("法务")
        self.collect_button = QPushButton("收藏")
        self.files_button = QPushButton("文件")
        # self.GPT_button = QPushButton("GPT")
        self.newlaw_button = QPushButton("新法")
        self.newlaw_label = QLabel(self.newlaw_button)

        self.setting_win = QDialog()
        self.setting_layout = QFormLayout(self.setting_win)

        #splitter
        self.splitter_main = QSplitter(Qt.Horizontal)

        # show win
        self.show_win = QWidget()
        self.vbox2 = QVBoxLayout(self.show_win)
        self.search = QLineEdit()
        self.search_win = QWidget()
        self.search_which = QHBoxLayout(self.search_win)
        self.main_tree = QTreeWidget()

        self.sai_layout = QHBoxLayout()
        self.paper = QSpinBox()
        self.saixuanwin = QWidget()
        self.inf_layout = QHBoxLayout(self.saixuanwin)
        self.finished = QCheckBox()
        self.rb1 = QRadioButton('我的')
        self.rb1.setChecked(True)
        self.rb2 = QRadioButton('部门')
        self.bg1 = QButtonGroup()
        self.bg1.addButton(self.rb1,1)
        self.bg1.addButton(self.rb2,2)

        #stacklayout
        self.stack_win = QWidget()
        self.stack = QStackedLayout(self.stack_win)
        self.show_law_txt = QTextEdit()
        # self.vb = QVBoxLayout(self.show_law_txt)
        # self.hb = QHBoxLayout()
        # self.law_keys = QLineEdit()

        #links_win
        self.links_win = QWidget()
        self.links_layout = QVBoxLayout(self.links_win)

        self.addlink_win = QWidget()
        self.addlink_layout = QHBoxLayout(self.addlink_win)
        self.link_title = QLineEdit()
        self.link_link = QLineEdit()

        self.link_box_win = QWidget()
        self.link_box = QGridLayout(self.link_box_win)
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidget(self.link_box_win)
        self.scrollarea.setWidgetResizable(True)
        self.paper_box = QHBoxLayout()
        self.guojia = QTreeWidget()
        self.sheng = QTreeWidget()
        self.shi = QTreeWidget()

        #公用
        self.record = QToolButton()
        self.label_as = QLabel("办理人")
        self.assitant = ComboBox()
        self.assitant.setObjectName("办理人")
        self.assitant.setMinimumWidth(80)
        self.make_paper = QToolButton()
        self.have_done = QTreeWidget()
        self.show_log = QPlainTextEdit()

        #case inf
        self.case_inf = QWidget()
        self.show_box = QVBoxLayout(self.case_inf)
        self.hbox2 = QHBoxLayout()
        self.label_start = QLabel("收案")
        self.case_start = QDateEdit()
        self.case_end_ok = QCheckBox("结案")
        self.case_end = QDateEdit()
        self.logs = QToolButton()
        self.write_paper = QToolButton()
        self.tree_case = QTreeWidget()
        self.splitter_havedone_and_log = QSplitter(Qt.Vertical)
        self.splitter_case = QSplitter(Qt.Horizontal)
        self.reson_txt = QPlainTextEdit()

        # client inf
        self.client_inf = QWidget()
        self.client_box = QVBoxLayout(self.client_inf)
        self.client_hbox2 = QHBoxLayout()
        self.client_label_start = QLabel("签约")
        self.client_case_start = QDateEdit()
        self.client_label_end = QLabel("到期")
        self.client_case_end = QDateEdit()
        self.client_tree_case = QTreeWidget()
        self.client_splitter_havedone_and_log = QSplitter(Qt.Vertical)
        self.client_splitter_case = QSplitter(Qt.Horizontal)

        # write win
        self.log_win = QSplitter(Qt.Horizontal)
        self.log_show = QWidget()
        self.calendar = Calendar()

        self.log_vbox = QVBoxLayout(self.log_show)

        self.log_hbox1 = QHBoxLayout()
        self.log_start_label = QLabel("计划日期")
        self.log_start = QDateEdit()
        self.log_start_time = QTimeEdit()

        self.log_hbox2 = QHBoxLayout()
        self.log_end_ok = QCheckBox("完成日")
        self.log_end = QDateEdit()

        self.log_hbox3 = QHBoxLayout()
        self.log_case_label = QLabel("属于")
        self.log_case = ComboBox()

        self.log_hbox4 = QHBoxLayout()
        self.log_name_label = QLabel("主题")
        self.log_name = ComboBox()
        self.log_count_label = QLabel("数量")
        self.log_count = QSpinBox()

        self.log_what = QTextEdit()
        self.log_files = ListWidget()

        # collect win
        self.collect_win = QWidget()
        self.collect_gbox1 = QVBoxLayout(self.collect_win)
        self.collect_hbox = QHBoxLayout()
        self.collect_name_label = QLabel("主题")
        self.collect_name = QLineEdit()
        self.collect_content = QTextEdit()

        #more inf win
        self.more_inf_txt = QPlainTextEdit()

        self.setup_ui()

    def setup_ui(self):
        self.resize(1280,720)

        self.main_layout.addLayout(self.vbox1)
        self.main_layout.addWidget(self.splitter_main,1)
        self.splitter_main.addWidget(self.show_win)
        self.splitter_main.addWidget(self.stack_win)

        # self.splitter_main.setStyleSheet("background-color:transparent;")

        self.setting_win.setWindowTitle("设置")
        self.setting_win.setWindowFlags(Qt.WindowMinimizeButtonHint)
        self.setting_win.setWindowIcon(QIcon("icons\\lawyer.png"))

        for i in ["执业证号:","用 户 名:","头    像:","主 目 录:"]:
            w = QLineEdit()
            if i == "用 户 名:":
                layout = QHBoxLayout()
                zhuji = QCheckBox("管理员")
                layout.addWidget(w,1)
                layout.addWidget(zhuji)
                w = layout
            self.setting_layout.addRow(i,w)
        self.setting_layout.addRow("打开显示:", ComboBox())

        self.setting_layout.addRow(QHBoxLayout())
        self.setting_layout.itemAt(1, 1).layout().itemAt(0).widget().setMaxLength(5)
        # action = QWidgetAction(self)
        # check = QPushButton("主机")
        # action.setDefaultWidget(check)
        # action.setCheckable(True)
        # self.setting_layout.itemAt(1,1).widget().addAction(action,QLineEdit.TrailingPosition)
        self.setting_layout.itemAt(2,1).widget().addAction(QAction(QIcon("icons\\more.png"),"",self),QLineEdit.TrailingPosition)
        self.setting_layout.itemAt(3,1).widget().addAction(QAction(QIcon("icons\\more.png"),"",self),QLineEdit.TrailingPosition)

        self.setting_layout.itemAt(4,1).widget().addItems(["日志","法律","案件","法务","收藏","日志（部门）","案件（部门）","法务（部门）"])

        self.setting_layout.itemAt(5,1).layout().addStretch(1)
        for i in ["默认","确定","取消","更新","退出"]:
            b = QPushButton(i)
            b.setMaximumWidth(60)
            self.setting_layout.itemAt(5, 1).layout().addWidget(b)


        #foun win
        self.vbox1.setContentsMargins(0, 0, 0, 0)
        self.user_layout.setContentsMargins(0, 0, 0, 0)
        self.user_layout.addStretch(1)
        self.user_layout.addWidget(self.user)
        self.user_layout.addStretch(1)
        self.vbox1.addLayout(self.user_layout)
        self.vbox1.addWidget(self.user_name)
        self.vbox1.addWidget(self.log_button)
        self.vbox1.addWidget(self.law_button)
        self.vbox1.addWidget(self.case_button)
        self.vbox1.addWidget(self.client_button)
        self.vbox1.addWidget(self.collect_button)
        self.vbox1.addSpacing(30)
        self.vbox1.addWidget(self.files_button)
        self.vbox1.addStretch(1)
        # self.vbox1.addWidget(self.GPT_button)
        self.vbox1.addWidget(self.newlaw_button)

        self.user.setFixedSize(60,60)
        self.user.setIconSize(QSize(60,60))
        self.user.setStyleSheet("background-color:transparent;border-radius:30px;border:none;")
        self.user_name.setAlignment(Qt.AlignCenter)

        self.log_button.setIcon(QIcon("icons\\tasks.png"))
        self.law_button.setEnabled(False)
        self.law_button.setIcon(QIcon("icons\\book.png"))
        self.case_button.setIcon(QIcon("icons\\case.png"))
        self.client_button.setIcon(QIcon("icons\\paper.png"))
        self.collect_button.setIcon(QIcon("icons\\star.png"))
        self.files_button.setIcon(QIcon("icons\\folder.png"))
        # self.GPT_button.setIcon(QIcon("icons\\GPT.png"))
        self.newlaw_button.setIcon(QIcon("icons\\newlaw.png"))

        self.log_button.setIconSize(QSize(22,22))
        self.law_button.setIconSize(QSize(22,22))
        self.case_button.setIconSize(QSize(22,22))
        self.client_button.setIconSize(QSize(22,22))
        self.collect_button.setIconSize(QSize(22,22))
        self.files_button.setIconSize(QSize(22,22))
        # self.GPT_button.setIconSize(QSize(22,22))
        self.newlaw_button.setIconSize(QSize(22,22))

        self.log_button.setFixedSize(85,40)
        self.law_button.setFixedSize(85,40)
        self.case_button.setFixedSize(85,40)
        self.client_button.setFixedSize(85,40)
        self.collect_button.setFixedSize(85,40)
        self.files_button.setFixedSize(85,40)
        # self.GPT_button.setFixedSize(85,40)
        self.newlaw_button.setFixedSize(85,40)
        self.newlaw_label.setFixedSize(12,12)
        self.newlaw_label.move(73,0)

        self.newlaw_label.setStyleSheet("background-color:red;border-radius:6px;")
        self.newlaw_label.setVisible(False)

        #splitter2
        self.splitter_main.setContentsMargins(0,0,0,0)
        self.splitter_main.setStretchFactor(1,1)

        # show_win
        self.vbox2.setContentsMargins(0, 0, 0, 0)
        self.vbox2.addWidget(self.search)
        self.search_which.setContentsMargins(0, 0, 0, 0)
        for i in ["日志","案件","法务","收藏","法律","文件"]:
            check = QCheckBox(i)
            if i in ["法律","文件"]:
                check.setCheckState(Qt.Checked)
            self.search_which.addWidget(check)
        self.search_which.addStretch(1)
        self.vbox2.addWidget(self.search_win)
        self.vbox2.addWidget(self.main_tree, 1)

        self.sai_layout.setContentsMargins(0,0,0,0)
        self.sai_layout.addStretch(1)
        self.paper.setPrefix("第 ")
        self.paper.setMinimum(1)
        self.paper.setContentsMargins(0,0,0,0)
        self.sai_layout.addWidget(self.paper)
        self.inf_layout.setContentsMargins(0,0,0,0)
        self.inf_layout.addWidget(self.finished)
        self.inf_layout.addWidget(self.rb1)
        self.inf_layout.addWidget(self.rb2)
        self.sai_layout.addWidget(self.saixuanwin)
        self.vbox2.addLayout(self.sai_layout)

        action = QAction(self)
        action.setIcon(QIcon("icons\\add_ok.png"))
        self.search.addAction(action,QLineEdit.TrailingPosition)

        action = QAction(self)
        action.setIcon(QIcon("icons\\search.png"))
        self.search.addAction(action, QLineEdit.TrailingPosition)

        action = QAction(self)
        action.setIcon(QIcon("icons\\earth.png"))
        self.search.addAction(action,QLineEdit.TrailingPosition)

        self.search.setToolTip("空格分开多个关键词，按回车键开始搜索")
        self.search.setPlaceholderText("搜索")
        self.search.setObjectName("搜索")

        self.main_tree.setHeaderHidden(True)
        self.main_tree.setSortingEnabled(False)
        self.main_tree.setMinimumWidth(360)
        self.main_tree.setObjectName("main_tree")
        self.main_tree.setStyleSheet('''QTreeWidget {
            color:black;
            background-color:transparent;
            font-size:16px;
            border:none;}''')
        self.main_tree.setRootIsDecorated(False)

        # self.stack.addWidget(self.calendar)
        self.stack.addWidget(self.log_win)
        self.stack.addWidget(self.show_law_txt)
        self.stack.addWidget(self.case_inf)
        self.stack.addWidget(self.client_inf)
        self.stack.addWidget(self.collect_win)
        self.stack.addWidget(self.links_win)

        self.links_layout.setContentsMargins(0,0,0,0)
        self.addlink_layout.setContentsMargins(0,0,0,0)
        self.link_box.setContentsMargins(0,0,0,0)
        self.paper_box.setContentsMargins(0,0,0,0)
        self.addlink_layout.addWidget(self.link_title)
        self.addlink_layout.addWidget(self.link_link,1)
        self.links_layout.addWidget(self.addlink_win)

        self.links_layout.addWidget(self.scrollarea)
        self.links_layout.addLayout(self.paper_box)
        self.paper_box.addWidget(self.guojia)
        self.paper_box.addWidget(self.sheng)
        self.paper_box.addWidget(self.shi)

        self.addlink_win.setVisible(False)

        self.guojia.setMinimumHeight(360)
        style = "QHeaderView::section{font:15px;height:18px;text-align:center;color:white;border:0px solid; background-color:gray;}"
        self.guojia.setStyleSheet(style)
        self.sheng.setStyleSheet(style)
        # self.label_start.setAlignment()
        self.shi.setStyleSheet(style)
        self.guojia.setRootIsDecorated(False)
        self.sheng.setRootIsDecorated(False)
        self.shi.setRootIsDecorated(False)

        self.link_title.setPlaceholderText("标题")
        self.link_link.setPlaceholderText("链接")

        self.scrollarea.setStyleSheet("QScrollArea{background-color:transparent;border:none;}")
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.link_box.setStyleSheet('''QTableWidget {
        #             color:gray;
        #             background-color:transparent;
        #             border:none;}''')
        # self.link_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.link_box.setColumnCount(1)
        # self.link_box.horizontalHeader().setHidden(True)
        # self.link_box.verticalHeader().setHidden(True)
        # self.link_box.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # # self.link_box.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.link_box.
        # self.link_box.setShowGrid(False)

        #show_law_txt
        self.show_law_txt.setReadOnly(True)
        self.show_law_txt.setObjectName("法条")
        # self.show_law_txt.setStyleSheet("background-color:rgba(255,255,255,80);")
        #
        # self.hb.addStretch(1)
        # self.hb.addWidget(self.law_keys)
        # self.hb.setContentsMargins(0,0,0,0)
        # self.vb.setContentsMargins(0,0,0,0)
        # self.vb.addLayout(self.hb)
        # self.vb.addStretch(1)
        #
        # action = QAction(self)
        # action.setIcon(QIcon("icons\\search.png"))
        # self.law_keys.addAction(action, QLineEdit.TrailingPosition)
        # self.law_keys.setMinimumWidth(180)
        # self.law_keys.setStyleSheet("color:#DB3022")

        self.record.setIcon(QIcon("icons\\add_case_ok.png"))
        self.record.setIconSize(QSize(20, 20))
        self.record.setObjectName("记录完成")

        #case_inf
        self.show_box.setContentsMargins(0, 0, 0, 0)
        self.show_box.addLayout(self.hbox2)
        self.show_box.addWidget(self.splitter_case,1)

        self.hbox2.setContentsMargins(0, 0, 0, 0)
        self.hbox2.addWidget(self.label_start)
        self.hbox2.addWidget(self.case_start)
        self.hbox2.addWidget(self.case_end_ok)
        self.hbox2.addWidget(self.case_end)
        self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.write_paper)

        self.case_start.setCalendarPopup(True)
        self.case_end.setCalendarPopup(True)
        self.case_end.setEnabled(False)

        self.logs.setIcon(QIcon("icons\\tasks.png"))
        self.logs.setIconSize(QSize(20, 20))
        self.logs.setObjectName("添加日志")
        self.write_paper.setIcon(QIcon("icons\\write.png"))
        self.write_paper.setIconSize(QSize(20, 20))
        self.write_paper.setObjectName("事实理由")
        self.make_paper.setIcon(QIcon("icons\\output.png"))
        self.make_paper.setIconSize(QSize(20, 20))

        self.splitter_havedone_and_log.setContentsMargins(0,0,0,0)
        self.splitter_havedone_and_log.setMinimumWidth(360)
        self.splitter_case.setContentsMargins(0,0,0,0)
        self.splitter_case.addWidget(self.tree_case)
        self.splitter_case.addWidget(self.splitter_havedone_and_log)
        self.splitter_case.setStretchFactor(0,1)

        self.have_done.setStyleSheet('''QTreeWidget {
                    background-color:rgba(255,255,255,80);
                    font-size:16px;
                    border:none;}''')
        self.have_done.setHeaderHidden(True)
        self.have_done.setRootIsDecorated(False)

        self.tree_case.setMinimumWidth(360)
        self.tree_case.setHeaderHidden(True)
        self.tree_case.setSortingEnabled(False)
        self.tree_case.setStyleSheet('''QTreeWidget {
                    color:gray;
                    background-color:rgba(255,255,255,80);
                    font-size:16px;
                    border:none;}
                    QTreeWidget::item:hover {
                    background-color: transparent}
                    QTreeWidget::item::selected{
                    color:gray;background-color:transparent;}
                    QTreeWidget::branch::selected{background-color:transparent;}''')
        self.tree_case.setRootIsDecorated(False)

        self.reson_txt.setObjectName("案件")
        self.reson_txt.setWindowTitle("事实理由/答辩意见：")
        self.reson_txt.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.reson_txt.resize(600,800)
        self.reson_txt.setWindowFlags(Qt.WindowStaysOnTopHint)

        #client_inf
        self.client_box.setContentsMargins(0, 0, 0, 0)
        self.client_box.addLayout(self.client_hbox2)
        self.client_box.addWidget(self.client_splitter_case, 1)

        self.client_hbox2.setContentsMargins(0, 0, 0, 0)
        self.client_hbox2.addWidget(self.client_label_start)
        self.client_hbox2.addWidget(self.client_case_start)
        self.client_hbox2.addWidget(self.client_label_end)
        self.client_hbox2.addWidget(self.client_case_end)
        self.client_hbox2.addStretch(1)

        self.client_case_start.setCalendarPopup(True)
        self.client_case_end.setCalendarPopup(True)

        self.client_splitter_havedone_and_log.setContentsMargins(0, 0, 0, 0)
        self.client_splitter_havedone_and_log.setMinimumWidth(360)
        self.client_splitter_case.setContentsMargins(0, 0, 0, 0)
        self.client_splitter_case.addWidget(self.client_tree_case)
        self.client_splitter_case.addWidget(self.client_splitter_havedone_and_log)
        self.client_splitter_case.setStretchFactor(0, 1)

        self.client_tree_case.setMinimumWidth(360)
        self.client_tree_case.setHeaderHidden(True)
        # self.client_tree_case.setColumnCount(2)
        # self.client_tree_case.setColumnWidth(0, 320)
        # self.client_tree_case.setColumnWidth(1, 5)
        self.client_tree_case.setSortingEnabled(False)
        self.client_tree_case.setStyleSheet('''QTreeWidget {
                            color:gray;
                            background-color:rgba(255,255,255,80);
                            font-size:16px;
                            border:none;}
                            QTreeWidget::item:hover {
                            background-color: transparent}
                            QTreeWidget::item::selected{
                            color:gray;background-color:transparent;}
                            QTreeWidget::branch::selected{background-color:transparent;}''')
        self.client_tree_case.setRootIsDecorated(False)

        self.show_log.setObjectName("日志内容")
        self.show_log.setVisible(False)
        self.show_log.setMinimumHeight(250)

        # log_win
        self.log_vbox.setContentsMargins(0, 0, 0, 0)

        self.log_hbox1.addWidget(self.log_start_label)
        self.log_hbox1.addWidget(self.log_start)
        self.log_hbox1.addWidget(self.log_start_time)
        self.log_hbox1.addStretch(1)
        self.log_vbox.addLayout(self.log_hbox1)

        self.log_hbox2.addWidget(self.log_end_ok)
        self.log_hbox2.addWidget(self.log_end)
        self.log_hbox2.addStretch(1)
        self.log_vbox.addLayout(self.log_hbox2)

        self.log_hbox3.addWidget(self.log_case_label)
        self.log_hbox3.addWidget(self.log_case,1)
        self.log_vbox.addLayout(self.log_hbox3)

        self.log_hbox4.addWidget(self.log_name_label)
        self.log_hbox4.addWidget(self.log_name,1)
        self.log_hbox4.addWidget(self.log_count_label)
        self.log_hbox4.addWidget(self.log_count)
        self.log_vbox.addLayout(self.log_hbox4)

        self.log_vbox.addWidget(self.log_what,1)
        self.log_vbox.addWidget(self.log_files)

        self.log_win.setContentsMargins(0,0,0,0)
        self.log_win.addWidget(self.calendar)
        self.log_win.addWidget(self.log_show)
        self.log_win.setStretchFactor(0,1)
        self.log_show.setVisible(False)
        # self.log_show.setStyleSheet("QWidget{background-color:white;}")

        self.log_start.setCalendarPopup(True)
        self.log_start_time.setDisplayFormat('HH:mm')
        self.log_end_ok.setStyleSheet("color:gray;font-size:16px;")
        self.log_end.setCalendarPopup(True)
        self.log_end.setEnabled(False)
        self.log_case.setEditable(True)
        self.log_case.setToolTip("输入后按回车键开始搜索")
        self.log_name.setEditable(True)
        self.log_what.setObjectName("日志")
        self.log_what.setPlaceholderText("内容：")

        # collect_win
        self.collect_hbox.setContentsMargins(0, 0, 0, 0)
        self.collect_gbox1.setContentsMargins(0, 0, 0, 0)
        self.collect_hbox.addWidget(self.collect_name_label)
        self.collect_hbox.addWidget(self.collect_name, 1)
        # self.collect_hbox.addStretch()
        self.collect_gbox1.addLayout(self.collect_hbox)
        self.collect_content.setObjectName("收藏")
        # self.collect_content.setStyleSheet("background-color:rgba(255,255,255,80);")
        self.collect_content.setPlaceholderText("内容：")
        self.collect_gbox1.addWidget(self.collect_content)

        #more inf win
        self.more_inf_txt.resize(300,400)
        self.more_inf_txt.setWindowTitle("详细信息")
        self.more_inf_txt.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.more_inf_txt.setWindowFlags(Qt.WindowStaysOnTopHint)