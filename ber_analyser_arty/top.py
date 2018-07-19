from migen import *
from litex.soc.interconnect.csr import *
from tx_top import _TX
from rx_top import _RX

class _Top(Module):
	def __init__(self,data_width=20):
		self.tx_config = Signal(2)
		self.rx_config = Signal(2)
		self.input = Signal(data_width)
		self.global_error = Signal(32)
		self.txdata = Signal(data_width)
		self.rxdata = Signal(data_width)
		self.bit_wise_errors = Signal(data_width)
		self.en8b10b = Signal()
		self.bit_error = Signal(8)
		self.mask = Signal(data_width)
		self.enable_err_count = Signal(2)
		self.total_bit_count = Signal(32)
		self.seldata = Signal()
		self.k_tx = Signal(2)

		tx = _TX(data_width)
		rx = _RX(data_width)
		self.submodules += tx, rx

		self.comb += [
			tx.tx_prbs_config.eq(self.tx_config),
			rx.rx_prbs_config.eq(self.rx_config),
			rx.rxdata.eq(self.rxdata),
			self.txdata.eq(tx.txdata),
			self.bit_error.eq(rx.bit_error),
			self.global_error.eq(rx.global_error),
			self.total_bit_count.eq(rx.total_bit_count),
			rx.enable_err_count.eq(self.enable_err_count),
			self.rxdata.eq(self.txdata),   #Enable loopback only to verify PRBS and encoding module
			tx.mask.eq(self.mask),
			rx.mask.eq(self.mask),
			rx.en8b10b.eq(self.en8b10b),
			tx.en8b10b.eq(self.en8b10b),
			tx.input.eq(self.input),
			tx.seldata.eq(self.seldata),
			rx.seldata.eq(self.seldata),
			tx.k.eq(self.k_tx),
			self.bit_wise_errors.eq(rx.bit_wise_errors)
		]


class Top(Module, AutoCSR):
	def __init__ (self, data_width = 40):
		self.tx_config = CSRStorage(2)
		self.rx_config = CSRStorage(2)
		self.mask = CSRStorage(data_width)
		self.global_error = CSRStatus(32)
		self.total_bit_count = CSRStatus(32)
		self.enable_err_count = CSRStorage(2)
		self.en8b10b = CSRStorage()

		_top = _Top()
		self.submodules += _top

		self.comb += [
		_top.tx_config.eq(self.tx_config.storage),
		_top.rx_config.eq(self.rx_config.storage),
		_top.mask.eq(self.mask.storage),
		_top.enable_err_count.eq(self.enable_err_count.storage),
		self.global_error.status.eq(_top.global_error),
		self.total_bit_count.status.eq(_top.total_bit_count),
		_top.en8b10b.eq(self.en8b10b.storage)
		]


def tb(dut):
	yield dut.tx_config.eq(0b10)
	yield dut.rx_config.eq(0b10)
	for i in range(16):
		yield
    
	yield dut.mask.eq(0x0)
	yield dut.tx_config.eq(0b10)
	yield dut.rx_config.eq(0b10)

	for i in range(32):
		yield

	yield dut.mask.eq(0x55500)
	yield dut.tx_config.eq(0b10)
	yield dut.rx_config.eq(0b10)

	for i in range(32):
		yield

	yield dut.seldata.eq(1)

	counter = 0

	for i in range(64):
		yield dut.k_tx.eq(0b01)
		yield dut.input[:8].eq((5 << 5) | 28)
		counter = counter + 1
		yield dut.input[8:16].eq(counter)
		yield

	yield dut.seldata.eq(1)
	yield dut.en8b10b.eq(1)

	counter = 0

	for i in range(64):
		yield dut.k_tx.eq(0b01)
		yield dut.input[:8].eq((5 << 5) | 28)
		counter = counter + 1
		yield dut.input[8:16].eq(counter)
		yield
	

if __name__ == "__main__":
	data_width = 20
	dut = _Top(data_width)
	run_simulation(dut,tb(dut),vcd_name="top_prbs.vcd")

