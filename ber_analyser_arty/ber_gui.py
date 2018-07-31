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

        self.prcon = PRBSControl(self.wb.regs,"top_gtp")
        self.setupUi(MainWindow)
        self.attachHandlers()
        self.prcon.BERinit()
        self.pllStatusCheck()
        self.checklinkstatus()
        self.updateBER()                    

    def attachHandlers(self):
        self.comboBox_4.activated.connect(self.handleActivatedTx)
        self.comboBox_5.activated.connect(self.handleActivatedRx)
        self.comboBox_6.activated.connect(self.handleActivatedErr)
        self.txpolcheckbox.stateChanged.connect(self.txpolchange)
        self.rxpolcheckbox.stateChanged.connect(self.rxpolchange)
        self.loopbackcheck.stateChanged.connect(self.loopbackmode)
        self.txrst.clicked.connect(self.TxReset)
        self.rxrst.clicked.connect(self.RxReset)
        self.submitbutton.clicked.connect(self.drpReadWrite)
        self.swingcombo.activated.connect(self.changeSwing)
        self.precombo.activated.connect(self.changePrecursor)
        self.postcombo.activated.connect(self.changePostcursor)

    def drpReadWrite(self):
        drp_addr = int(self.drpaddr.text(),16)
        drp_value = int(self.drpval.text(),16)

        if drpreadradio.isChecked == True:
            self.prcon.drpWrite(drp_addr,drp_value)

        if drpwriteradio.isChecked == True:
            drp_value = self.prcon.drpRead(drp_addr)
            self.drpval.setText(hex(drp_value))

    def loopbackmode(self,state):
        if state == QtCore.Qt.Checked:
            self.enableLoopback()
        else:
            self.disableLoopback()

    def txpolchange(self,state):
        if state == QtCore.Qt.Checked:
            self.txPolarity(True)
        else:
            self.txPolarity(False)

    def rxpolchange(self,state):
        if state == QtCore.Qt.Checked:
            self.rxPolarity(True)
        else:
            self.rxPolarity(False)

    def changeSwing(self,index):
        if index == 0:
            self.prcon.changeOutputSwing(0b0001)
        if index == 1:
            self.prcon.changeOutputSwing(0b0100)
        if index == 2:
            self.prcon.changeOutputSwing(0b1000)
        if index == 3:
            self.prcon.changeOutputSwing(0b1011)
        if index == 4:
            self.prcon.changeOutputSwing(0b1111)

    def changePrecursor(self,index):
        if index == 0:
            self.prcon.changetxPrecursor(0b00000)
        if index == 1:
            self.prcon.changetxPrecursor(0b00010)
        if index == 2:
            self.prcon.changetxPrecursor(0b00101)
        if index == 3:
            self.prcon.changetxPrecursor(0b01000)
        if index == 4:
            self.prcon.changetxPrecursor(0b01111)
        if index == 5:
            self.prcon.changetxPrecursor(0b10100)

    def changePostcursor(self,index):
        if index == 0:
            self.prcon.changetxPostcursor(0b00000)
        if index == 1:
            self.prcon.changetxPostcursor(0b00010)
        if index == 2:
            self.prcon.changetxPostcursor(0b00100)
        if index == 3:
            self.prcon.changetxPostcursor(0b01000)
        if index == 4:
            self.prcon.changetxPostcursor(0b01111)
        if index == 5:
            self.prcon.changetxPostcursor(0b10100)
        if index == 6:
            self.prcon.changetxPostcursor(0b11000)
        if index == 7:
            self.prcon.changetxPostcursor(0b11110)

    def pllStatusCheck(self):
        self.plllabel.setText(prcon.PLLlockStatus())
        QtCore.QTimer.singleShot(5000,self.updateBER)

    def updateBER(self):
        self.label_4.setText(str(round(self.prcon.calcBER(),3)))
        QtCore.QTimer.singleShot(1000,self.updateBER)

    def checklinkstatus(self):
        self.linklabel.setText(prcon.checkMGTLink())
        QtCore.QTimer.singleShot(5000,self.checklinkstatus)

    def TxReset(self):
        self.prcon.resetTx()

    def RxReset(self):
        self.prcon.resetRx()

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
    
