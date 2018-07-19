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
        self.rx_global_error = CSRStatus(32)
        self.input = CSRStorage(20)
        self.mask = CSRStorage(20)
        self.k = CSRStorage(2)
        self.rx_ready_sys = CSRStatus()

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

        inp4 =BusSynchronizer(20,"rx","sys")
        self.comb += inp4.i.eq(gtp.rx_global_error), self.rx_global_error.status.eq(inp4.o)

        self.submodules += inp1,inp2,inp3,inp4

        self.specials += [
            MultiReg(self.seldata.storage, gtp.tx_seldata, "tx"),
            MultiReg(self.en8b10b.storage, gtp.tx_en8b10b, "tx"),
            MultiReg(self.k.storage, gtp.k, "tx"),
            MultiReg(self.tx_prbs_config.storage, gtp.tx_prbs_config, "tx")
        ]

        self.specials += [
        	MultiReg(self.seldata.storage,gtp.rx_seldata,"rx"),
            MultiReg(self.en8b10b.storage,gtp.rx_en8b10b,"rx"),
            MultiReg(self.rx_prbs_config.storage, gtp.rx_prbs_config, "rx"),
            MultiReg(self.enable_err_count.storage,gtp.enable_err_count,"rx"),
            MultiReg(gtp.rx_ready,self.rx_ready_sys.status,"sys"),
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






