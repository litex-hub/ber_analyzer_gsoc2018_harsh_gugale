import sys
sys.path.insert("./")
from litex.soc.tools.remote import RemoteClient
from control_prbs import *

wb = RemoteClient()
wb.open()
prcon = PRBSControl(wb.regs,"top_gtp")
prcon.phaseAlign()
prcon.setErrMask(0,20)
prcon.setPRBSConfig(7,7)
print(prcon.calcBERabs(5,20))
prcon.setErrMask(0.5,20)
print(prcon.calcBERabs(5,20))
prcon.resetTx()
prcon.resetRx()
prcon.phaseAlign()

prcon.setPRBSConfig(15,15)
prcon.setErrMask(0,20)
print(prcon.calcBERabs(5,20))
prcon.setErrMask(0.5,20)
print(prcon.calcBERabs(5,20))

print("{0:0x}".format(prcon.drpRead(0x0040)))

prcon.PLLlockStatus()

