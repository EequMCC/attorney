import os
import re
import socket
import struct
import sys
import time
from subprocess import run

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
from PyQt5.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout, QApplication


class MyThread(QThread):
    mysig1 = pyqtSignal()

    def __init__(self,fun):
        super(MyThread, self).__init__()
        self.fun = fun

    def run(self):
        self.fun()


class Updateme(QWidget):
    prog_sig = pyqtSignal(int)
    max_sig = pyqtSignal(int)
    fl_sig = pyqtSignal(str)

    def __init__(self):
        super(Updateme,self).__init__()
        try:
            self.socketT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            app.quit()

        self.label = QLabel("正在连接到主机...")
        self.label.setWordWrap(True)
        self.prog = QProgressBar()
        self.prog.setAlignment(Qt.AlignCenter)
        self.setWindowTitle("更新程序")
        self.setWindowIcon(QIcon("icons\\lawyer.png"))
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setFixedSize(300,120)
        v = QVBoxLayout(self)
        v.addStretch(1)
        v.addWidget(self.label)
        v.addWidget(self.prog)
        v.addStretch(1)

        self.prog_sig.connect(self.prog.setValue)
        self.max_sig.connect(self.prog.setMaximum)
        self.fl_sig.connect(self.label.setText)

        self.prog.setValue(0)

        self.getserverip = QUdpSocket(self)
        self.getserverip.bind(QHostAddress.Any, 8848)
        self.getserverip.readyRead.connect(self.get_serverip)

        self.th = MyThread(self.startUpdate)

    def startup(self):
        self.getserverip.blockSignals(False)
        self.getserverip.writeDatagram(b'update', QHostAddress.Broadcast, 6665)

    def get_serverip(self):
        while self.getserverip.hasPendingDatagrams():
            datagram, host, port = self.getserverip.readDatagram(
                self.getserverip.pendingDatagramSize()
            )
            if self.socketT.connect_ex((re.sub(".*:", "", host.toString()),6666)) == 0:
                self.th.start()
            else:
                self.fl_sig.emit("<font size='3'><b>连接主机失败！</font>")

    def startUpdate(self):
        try:
            self.socketT.send(b'update')
        except:
            return

        while True:
            try:
                size = struct.calcsize('512sq')
                head = self.socketT.recv(size)
                if head == b'none':
                    self.fl_sig.emit("<font size='3' color='#DB3022'><b>Nothing Could be updated!</font>")
                    break
                if head == b'ok':
                    self.fl_sig.emit("<font size='3'><b>更新完成！</font>")
                    try:
                        self.getserverip.blockSignals(True)
                    except:
                        pass
                    break
                if head:
                    name, leng = struct.unpack('512sq',head)
                    name = str(name.strip(b'\00').decode())
                    self.fl_sig.emit("<font size='3' color='#DB3022'><b>进度：</font>"+name)
                    receiv_leng = 0
                    max = leng//204800
                    yu = leng%204800
                    if yu != 0:
                        max += 1
                    if max == 0:
                        max = 1
                    self.max_sig.emit(max)
                    self.prog_sig.emit(0)
                    while self.prog.value() != 0 or self.prog.maximum() != max:
                        time.sleep(0.01)
                    try:
                        dirs = os.path.dirname(name)
                        if dirs != "" and not os.path.exists("./"+dirs):
                            run('mkdir "{}"'.format(dirs), shell=True)
                        with open('./' + str(name)+"-update", 'wb') as t:
                            while leng != receiv_leng:
                                if leng - receiv_leng > 2048:
                                    data = self.socketT.recv(2048)
                                else:
                                    data = self.socketT.recv(leng - receiv_leng)
                                receiv_leng += len(data)
                                t.write(data)
                                if receiv_leng//204800 > self.prog.value():
                                    value = self.prog.value()+1
                                    self.prog_sig.emit(value)
                                    while self.prog.value() != value:
                                        time.sleep(0.001)
                        if leng == receiv_leng:
                            self.prog_sig.emit(self.prog.value() + 1)
                        if os.path.exists('./' + str(name)):
                            os.remove('./' + str(name))
                        os.rename('./' + str(name)+"-update",'./' + str(name))
                        if str(name) == "大律师Attorney.exe":
                            os.startfile("大律师Attorney.exe")
                            app.quit()
                    except:
                        self.fl_sig.emit("<font size='3'><b>更新失败！</font>")
            except:
                break
            time.sleep(0.01)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Updateme()
    win.show()
    win.startup()
    sys.exit(app.exec_())