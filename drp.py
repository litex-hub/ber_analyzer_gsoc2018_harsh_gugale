from migen import *

class drp(Module):
	def __init__(self):
		self.drpaddr = Signal(9)
		self.drpdi = Signal(16)
		self.drpdo = Signal(16)
		self.drpvalue = Signal(16)
		self.drpen = Signal()
		self.drprdy = Signal()
		self.drpwe = Signal()
		self.oprenable = Signal()
		self.wren = Signal()
		self.ack = Signal()

		drp_fsm = ResetInserter()(FSM(reset_state="IDLE"))
		self.submodules += drp_fsm

		drp_fsm.act("IDLE",
			If(self.oprenable,
				If(self.wren,
				NextState("WRITE")    
				).Else(
				NextState("READ")
				)				
			)
		)

		drp_fsm.act("WRITE",
			self.drpen.eq(1),
			self.drpwe.eq(1),
			NextState("WRITE_WAIT")
			)

		drp_fsm.act("WRITE_WAIT",
			If(self.drprdy,
				self.ack.eq(1),
				NextState("OPRENABLE_DEASSERT")
				)
			)

		drp_fsm.act("READ",
			self.drpen.eq(1),
			self.drpwe.eq(0),
			NextState("READ_WAIT")
			)

		drp_fsm.act("READ_WAIT",
			If(self.drprdy,
				self.ack.eq(1),
				NextValue(self.drpvalue, self.drpdo),
				NextState("OPRENABLE_DEASSERT")
				)
			)

		drp_fsm.act("OPRENABLE_DEASSERT",
			self.ack.eq(1),
			If(~self.oprenable,
				NextState("IDLE")
				)
			)

