from migen import *

class drp(Module):
	def __init__(self):
		self.drpen = Signal()
		self.drprdy = Signal()
		self.drpwe = Signal()
		self.oprenable = Signal()
		self.wren = Signal()
		self.busy = Signal()
		self.ack = Signal()

		drp_fsm = ResetInserter()(FSM(reset_state="IDLE"))

		drp_fsm.act("IDLE",
			If(self.oprenable,
			self.busy.eq(1),
				If(self.wren,
					NextState("WRITE")    
				).Else(
					NextState("READ")
				)
			)
		)

		drp_fsm.act("WRITE",
			self.busy.eq(1),
			self.drpen.eq(1),
			self.drpwe.eq(1),
			NextState("WRITE_WAIT")
			)

		drp_fsm.act("WRITE_WAIT",
			self.busy.eq(1)
			If(self.drprdy,
				self.ack.eq(1),
				NextState("OPRENABLE_DEASSERT")
				)
			)

		drp_fsm.act("READ",
			self.busy.eq(1),
			self.drpen.eq(1),
			self.drpwe.eq(0),
			NextState("READ_WAIT")
			)

		drp_fsm.act("READ_WAIT",
			self.busy.eq(1)
			If(self.drprdy,
				self.ack.eq(1),
				NextState("OPRENABLE_DEASSERT")
				)
			)

		drp_fsm.act("OPRENABLE_DEASSERT",
			self.busy.eq(1),
			self.ack.eq(1),
			If(~self.oprenable,
				NextState("IDLE")
				)
			)

