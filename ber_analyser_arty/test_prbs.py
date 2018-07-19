from migen import *

from prbs import PRBSTX, PRBSRX

class DUT(Module):
    def __init__(self, width, delay=16):
        self.submodules.tx = PRBSTX(width)
        self.submodules.rx = PRBSRX(width)

        self.flip_bits = Signal(32)

        # connect tx to rx
        data = self.tx.o
        for i in range(delay):
            new_data = Signal(32)
            self.sync += new_data.eq(data)
            data = new_data
        self.comb += self.rx.i.eq(data ^ self.flip_bits)


def tb(dut):
    print("Start TX generator/RX Checker and wait synchronization")
    yield dut.tx.config.eq(0b01)
    yield dut.rx.config.eq(0b01)
    for i in range(128):
        yield

    print("Verify we don't have errors when synchronized")
    for i in range(64):
        yield
        print("cycle:{}, errors: {}".format(i, (yield dut.rx.bit_wise_errors)))

    print("Flip a bit in TX/RX loopback, verify we have errors")
    for i in range(64):
        if i == 0:
            yield dut.flip_bits.eq(0x00000001)
        else:
            yield dut.flip_bits.eq(0x00000000)
        yield
        print("cycle:{}, errors: {}".format(i, (yield dut.rx.bit_wise_errors)))

    print("Change TX mode and verify we have errors on RX")
    yield dut.tx.config.eq(0b11)
    yield dut.rx.config.eq(0b00)
    for i in range(16):
        yield
    yield dut.tx.config.eq(0b11)
    yield dut.rx.config.eq(0b01)
    for i in range(64):
        yield
        print("cycle:{}, errors: {}".format(i, (yield dut.rx.bit_wise_errors)))

if __name__ == "__main__":
    dut = DUT(32)
    run_simulation(dut, tb(dut), vcd_name="test_prbs.vcd")
