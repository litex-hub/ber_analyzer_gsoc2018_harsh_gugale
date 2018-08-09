from migen import *
from litex.soc.cores.code_8b10b import *
#from prbs import *
from prbs_files.prbs import *


class _TX(Module):
	def __init__ (self,data_width=20,reverse=False):
		self.tx_prbs_config = tx_prbs_config = Signal(2)
		self.input = Signal(data_width)
		self.txdata = txdata = Signal(data_width)
		self.seldata = Signal()
		self.en8b10b = Signal()
		self.mask = Signal(data_width)
		self.k = Signal(2)

		prbs_tx = PRBSTX(data_width,reverse)
		enc = Encoder(2,True)
		self.submodules += prbs_tx,enc

		#seldata 0 - PRBS output
		#seldata 1 - input to module

		self.comb += [
			prbs_tx.mask.eq(self.mask),
			If(self.seldata == 0,
			prbs_tx.config.eq(tx_prbs_config),
			txdata.eq(prbs_tx.o)
			).Elif(
			self.en8b10b == 1,
			enc.k[0].eq(self.k[0]),
			enc.k[1].eq(self.k[1]),
			enc.d[0].eq(self.input[:8]),
			enc.d[1].eq(self.input[8:16]),
			txdata.eq(Cat(enc.output[0],enc.output[1]))
			).Else(
			txdata.eq(self.input)
			)
		]

