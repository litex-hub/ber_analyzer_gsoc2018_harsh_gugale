from migen import *
from gtp_7series import *
from litex.soc.interconnect.csr import *

class Top_gtp(Module, AutoCSR):
    def __init__ (self, refclk, refclk_freq, linerate, platform):
        self.seldata = CSRStorage()
        self.en8b10b = CSRStorage()
        self.enable_err_count = CSRStorage(2)
        self.tx_prbs_config = CSRStorage(2)
        self.rx_prbs_config = CSRStorage(2)
        self.global_error = CSRStatus(32)
        self.total_bit_count = CSRStatus(32)
        self.input = CSRStorage(20)
        self.mask = CSRStorage(20)
        self.k = CSRStorage(2)
        self.plllock = CSRStatus()

        self.tx_reset_host = CSRStorage()
        self.rx_reset_host = CSRStorage()
        self.tx_reset_ack = CSRStatus()
        self.rx_reset_ack = CSRStatus()
        self.rx_restart_phaseAlign = CSRStorage()
        self.rx_phaseAlign_ack = CSRStatus()

        qpll = GTPQuadPLL(refclk, 100e6, 2e9)
        print(qpll)
        self.submodules += qpll

        tx_pads = platform.request("gtp_tx")
        rx_pads = platform.request("gtp_rx")

        gtp = GTP(qpll, tx_pads, rx_pads, refclk_freq,
            clock_aligner=True, internal_loopback=True)

        self.submodules += gtp

        inp1 = BusSynchronizer(20,"sys","tx")
        self.comb += inp1.i.eq(self.input.storage), gtp.tx_input.eq(inp1.o)

        inp2 = BusSynchronizer(20,"sys","tx")
        self.comb += inp2.i.eq(self.mask.storage), gtp.tx_mask.eq(inp2.o)

        inp3 = BusSynchronizer(20,"sys","rx")
        self.comb += inp3.i.eq(self.mask.storage), gtp.rx_mask.eq(inp3.o)

        inp4 = BusSynchronizer(32,"rx","sys")
        self.comb += inp4.i.eq(gtp.global_error), self.global_error.status.eq(inp4.o)

        inp5 = BusSynchronizer(32,"rx","sys")
        self.comb += inp5.i.eq(gtp.total_bit_count), self.total_bit_count.status.eq(inp5.o)

        self.submodules += inp1,inp2,inp3,inp4,inp5

        pul1 = PulseSynchronizer("sys","tx")
        pul2 = PulseSynchronizer("sys","tx")
        pul3 = PulseSynchronizer("sys","tx")

        self.submodules += pul1,pul2,pul3

        self.comb += [
        pul1.i.eq(self.tx_reset_host.storage),
        pul1.o.eq(gtp.tx_reset_host),
        pul2.i.eq(self.rx_reset_host.storage),
        pul2.o.eq(gtp.rx_reset_host),
        pul3.i.eq(self.rx_restart_phaseAlign.storage),
        pul3.o.eq(gtp.rx_restart_phaseAlign)
        ]

        self.specials += [
            MultiReg(self.seldata.storage, gtp.tx_seldata, "tx"),
            MultiReg(self.en8b10b.storage, gtp.tx_en8b10b, "tx"),
            MultiReg(self.k.storage, gtp.k, "tx"),
            MultiReg(self.tx_prbs_config.storage, gtp.tx_prbs_config, "tx"),
            MultiReg(gtp.tx_reset_ack,self.tx_reset_ack.status,"sys"),
            MultiReg(gtp.plllock,self.plllock.status,"sys")
        ]

        self.specials += [
        	MultiReg(self.seldata.storage,gtp.rx_seldata,"rx"),
            MultiReg(self.en8b10b.storage,gtp.rx_en8b10b,"rx"),
            MultiReg(self.rx_prbs_config.storage, gtp.rx_prbs_config, "rx"),
            MultiReg(self.enable_err_count.storage,gtp.enable_err_count,"rx"),
            MultiReg(gtp.rx_phaseAlign_ack,self.rx_phaseAlign_ack.status,"sys"),
            MultiReg(gtp.rx_reset_ack,self.rx_reset_ack.status,"sys")
        ]

        sys_clk = Signal()
        self.comb += sys_clk.eq(ClockSignal("sys"))
        sys_clk.attr.add("keep")
        gtp.cd_tx.clk.attr.add("keep")
        gtp.cd_rx.clk.attr.add("keep")
        platform.add_period_constraint(gtp.cd_tx.clk, 1e9/gtp.tx_clk_freq)
        platform.add_period_constraint(gtp.cd_rx.clk, 1e9/gtp.tx_clk_freq)
        platform.add_false_path_constraints(
            sys_clk,
            gtp.cd_tx.clk,
            gtp.cd_rx.clk)






