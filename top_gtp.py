from migen import *
from gtp_7series import *
from litex.soc.interconnect.csr import *
from drp import *

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
        self.loopback = CSRStorage(3,reset=0b010)
        self.tx_polarity = CSRStorage()
        self.rx_polarity = CSRStorage()
        self.diffctrl = CSRStorage(4,reset=0b1000)
        self.txprecursor = CSRStorage(5)
        self.txpostcursor = CSRStorage(5)
        self.linkstatus = CSRStatus()
        self.checklink = CSRStorage()

        linerate_resetval = ((linerate*2)/1e9)

        print("yo "+str(int(linerate_resetval)))

        self.mgt_linerate = CSRStorage(4,reset=int(linerate_resetval))

        self.tx_reset_host = CSRStorage()
        self.rx_reset_host = CSRStorage()
        self.tx_reset_ack = CSRStatus()
        self.rx_reset_ack = CSRStatus()
        self.rx_restart_phaseAlign = CSRStorage()
        self.rx_phaseAlign_ack = CSRStatus()

        # DRP Host Signals

        self.drp_oprenable = CSRStorage()
        self.drp_addr = CSRStorage(9)
        self.drp_di = CSRStorage(16)
        self.drp_value = CSRStatus(16)
        self.drp_wren = CSRStorage()
        self.drp_ack = CSRStatus()

        # # #

        qpll = GTPQuadPLL(refclk, refclk_freq, linerate)
        print(qpll)

        tx_pads = platform.request("gtp_tx")
        rx_pads = platform.request("gtp_rx")

        drp_host = (ClockDomainsRenamer("tx"))(drp())

        gtp = GTP(qpll,drp_host,tx_pads, rx_pads, refclk_freq, clock_aligner=True)

        self.submodules += gtp,qpll,drp_host

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

        inp6 = BusSynchronizer(16,"sys","tx")
        self.comb += inp6.i.eq(self.drp_di.storage), drp_host.drpdi.eq(inp6.o)

        inp7 = BusSynchronizer(16,"tx","sys")
        self.comb += inp7.i.eq(drp_host.drpvalue), self.drp_value.status.eq(inp7.o)

        inp8 = BusSynchronizer(9,"sys","tx")
        self.comb += inp8.i.eq(self.drp_addr.storage), drp_host.drpaddr.eq(inp8.o)

        inp9 = BusSynchronizer(3,"sys","tx")
        self.comb += inp9.i.eq(self.loopback.storage), gtp.loopback.eq(inp9.o)

        inp10 = BusSynchronizer(4,"sys","tx")
        self.comb += inp10.i.eq(self.diffctrl.storage), gtp.diffctrl.eq(inp10.o)

        inp11 = BusSynchronizer(5,"sys","tx")
        self.comb += inp11.i.eq(self.txpostcursor.storage), gtp.txpostcursor.eq(inp11.o)

        inp12 = BusSynchronizer(5,"sys","tx")
        self.comb += inp12.i.eq(self.txprecursor.storage), gtp.txprecursor.eq(inp12.o)

        self.submodules += inp1,inp2,inp3,inp4,inp5,inp6,inp7,inp8,inp9,inp10,inp11,inp12

        pul1 = PulseSynchronizer("sys","tx")
        pul2 = PulseSynchronizer("sys","tx")
        pul3 = PulseSynchronizer("sys","tx")
        pul4 = PulseSynchronizer("sys","tx")

        self.submodules += pul1,pul2,pul3,pul4

        self.comb += [
        pul1.i.eq(self.tx_reset_host.storage),
        pul1.o.eq(gtp.tx_reset_host),
        pul2.i.eq(self.rx_reset_host.storage),
        pul2.o.eq(gtp.rx_reset_host),
        pul3.i.eq(self.rx_restart_phaseAlign.storage),
        pul3.o.eq(gtp.rx_restart_phaseAlign),
        pul4.i.eq(self.checklink.storage),
        pul4.o.eq(gtp.checklink)
        ]

        self.specials += [
            MultiReg(self.seldata.storage, gtp.tx_seldata, "tx"),
            MultiReg(self.en8b10b.storage, gtp.tx_en8b10b, "tx"),
            MultiReg(self.k.storage, gtp.k, "tx"),
            MultiReg(self.tx_prbs_config.storage, gtp.tx_prbs_config, "tx"),
            MultiReg(gtp.tx_reset_ack,self.tx_reset_ack.status,"sys"),
            MultiReg(gtp.plllock,self.plllock.status,"sys"),
            MultiReg(self.drp_oprenable.storage,drp_host.oprenable,"tx"),
            MultiReg(self.drp_wren.storage,drp_host.wren,"tx"),
            MultiReg(drp_host.ack,self.drp_ack.status,"sys"),
            MultiReg(self.tx_polarity.storage,gtp.tx_polarity,"tx")
        ]

        self.specials += [
            MultiReg(self.seldata.storage,gtp.rx_seldata,"rx"),
            MultiReg(self.en8b10b.storage,gtp.rx_en8b10b,"rx"),
            MultiReg(self.rx_prbs_config.storage, gtp.rx_prbs_config, "rx"),
            MultiReg(self.enable_err_count.storage,gtp.enable_err_count,"rx"),
            MultiReg(gtp.rx_phaseAlign_ack,self.rx_phaseAlign_ack.status,"sys"),
            MultiReg(gtp.rx_reset_ack,self.rx_reset_ack.status,"sys"),
            MultiReg(self.rx_polarity.storage,gtp.rx_polarity,"rx"),
            MultiReg(gtp.linkstatus,self.linkstatus.status,"sys"),
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






