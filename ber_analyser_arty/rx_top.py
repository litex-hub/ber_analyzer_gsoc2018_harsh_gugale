from migen import *
from litex.soc.cores.code_8b10b import *
#from prbs import *
from ber_analyser_arty.prbs import *

class _RX(Module):
	def __init__(self, data_width = 20):
		self.rx_prbs_config = rx_prbs_config = Signal(2)
		self.en8b10b = Signal()
		self.mask = Signal(data_width,reset=0)
		self.rxdata = rxdata = Signal(data_width)
		self.bit_wise_errors = Signal(data_width)
		self.enable_err_count = Signal(2)
		self.total_bit_count = Signal(32)
		self.bit_error = Signal(8)
		self.global_error = Signal(32)
		self.k = Signal(2)
		self.seldata = Signal()
		self.output = Signal(data_width)

		#seldata 0 - PRBS output
		#seldata 1 - input to module

		prbs_rx = PRBSRX(data_width)
		dec0 = Decoder()
		dec1 = Decoder()
		self.submodules += prbs_rx, dec0, dec1

		self.comb += [
			prbs_rx.config.eq(rx_prbs_config),
			prbs_rx.mask.eq(self.mask),
			If(self.seldata == 0,
			prbs_rx.i.eq(rxdata),
			self.bit_wise_errors.eq(prbs_rx.bit_wise_errors)
			).Elif( self.en8b10b == 1,
			dec0.input.eq(rxdata[:10]),
			dec1.input.eq(rxdata[10:20]),
			self.k[0].eq(dec0.k),
			self.k[1].eq(dec1.k),
			self.output.eq(Cat(dec0.d,dec1.d)),
			).Else(
			self.output.eq(rxdata)
			)
		]

		valadd = Signal(32)

		for i in range(data_width):
			valadd = valadd + self.bit_wise_errors[i]

		self.sync += self.bit_error.eq(valadd)
		self.sync += [
			If(self.enable_err_count == 0b01,
			self.global_error.eq(self.global_error + self.bit_error),
			self.total_bit_count.eq(self.total_bit_count + 1)
			).Elif(self.enable_err_count == 0b11,
			self.global_error.eq(self.global_error),
			self.total_bit_count.eq(self.total_bit_count)
			).Elif(self.enable_err_count == 0b00,
			self.global_error.eq(0),
			self.total_bit_count.eq(0)
			)]
