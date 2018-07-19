from litex.soc.tools.remote import RemoteClient
from control_prbs import *

wb = RemoteClient()
wb.open()
prcon = PRBSControl(wb.regs,"top")
prcon.setErrMask(0,40)
prcon.setPRBSConfig(7,7)
print(prcon.calcBER(5,40))
prcon.enable8b10b()
prcon.setErrMask(0.5,40)
print(prcon.calcBER(5,40))
