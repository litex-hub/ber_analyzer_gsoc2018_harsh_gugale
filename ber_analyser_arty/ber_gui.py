from PyQt5 import QtCore, QtGui, QtWidgets
from litex.soc.tools.remote import RemoteClient
import sys
from designer import Ui_MainWindow
from control_prbs import *

class Ui(Ui_MainWindow):
    def __init__(self,MainWindow):
        super().__init__()
        self.wb = RemoteClient()
        self.wb.open()

        self.prcon = PRBSControl(self.wb.regs,"top")
        self.setupUi(MainWindow)
        self.attachHandlers()
        self.prcon.BERinit()
        self.encodingEnabled = False
        self.updateBER()                    

    def attachHandlers(self):
        self.comboBox.activated.connect(self.handleActivatedTx)
        self.comboBox_3.activated.connect(self.handleActivatedRx)
        self.comboBox_2.activated.connect(self.handleActivatedErr)
        self.pushButton.clicked.connect(self.button_pressed)

    def updateBER(self):
        self.label_4.setText(str(round(self.prcon.calcBER(40),3)))
        QtCore.QTimer.singleShot(1000,self.updateBER)

    def button_pressed(self):
        if self.encodingEnabled is True:
            self.prcon.disable8b10b()
            self.pushButton.setText("Enable")
            self.encodingEnabled = False

        else:
            self.prcon.enable8b10b()
            self.pushButton.setText("Disable")
            self.encodingEnabled = True

    def handleActivatedTx(self,index):
        if index == 0:
            self.prcon.setPRBSConfig(7,None)
        if index == 1:
            self.prcon.setPRBSConfig(15,None)
        if index == 2:
            self.prcon.setPRBSConfig(23,None)
        if index == 3:
            self.prcon.setPRBSConfig(31,None)

    def handleActivatedRx(self,index):
        if index == 0:
            self.prcon.setPRBSConfig(None,7)
        if index == 1:
            self.prcon.setPRBSConfig(None,15)
        if index == 2:
            self.prcon.setPRBSConfig(None,23)
        if index == 3:
            self.prcon.setPRBSConfig(None,31)

    def handleActivatedErr(self,index):
        if index == 0:
            self.prcon.setErrMask(0,40)
        if index == 1:
            self.prcon.setErrMask(0.25,40)
        if index == 2:
            self.prcon.setErrMask(0.5,40)
        if index == 3:
            self.prcon.setErrMask(0.75,40)
        if index == 4:
            self.prcon.setErrMask(1,40)

def main():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    
