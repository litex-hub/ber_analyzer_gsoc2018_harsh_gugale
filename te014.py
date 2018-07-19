#!/usr/bin/env python3

import sys
import struct

from migen import *
from migen.genlib.cdc import MultiReg, PulseSynchronizer
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores import dna

from top_gtp import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

_io = [
    ("clk25", 0, Pins("T14"), IOStandard("LVCMOS33")),

    # serial
    ("serial", 0,
        Subsignal("tx", Pins("U12")), # tp7
        Subsignal("rx", Pins("T12")), # tp8
        IOStandard("LVCMOS33")
    ),

    # gtp
    ("gtp_refclk_en", 0, Pins("V13"), IOStandard("LVCMOS33")),
    ("gtp_refclk", 0,
        Subsignal("p", Pins("D6")),
        Subsignal("n", Pins("D5")),
    ),
    ("gtp_tx", 0,
        Subsignal("p", Pins("F2")),
        Subsignal("n", Pins("F1")),
    ),
    ("gtp_rx", 0,
        Subsignal("p", Pins("A4")),
        Subsignal("n", Pins("A3")),
    ),
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "xc7a50t-csg325-2", _io, toolchain="vivado")
        self.add_platform_command("""
                set_property CFGBVS VCCO [current_design]
                set_property CONFIG_VOLTAGE 3.3 [current_design]
                """)


def period_ns(freq):
    return 1e9/freq


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_clk200 = ClockDomain()

        clk25 = platform.request("clk25")
        clk25.attr.add("keep")
        platform.add_period_constraint(clk25, period_ns(25e6))

        pll_locked = Signal()
        pll_fb = Signal()
        pll_sys = Signal()
        pll_clk200 = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     # VCO @ 1600 MHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=40.0,
                     p_CLKFBOUT_MULT=64, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=clk25, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 100 MHz
                     p_CLKOUT0_DIVIDE=16, p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=pll_sys,

                     # 200 MHz
                     p_CLKOUT1_DIVIDE=8, p_CLKOUT1_PHASE=0.0,
                     o_CLKOUT1=pll_clk200
            ),
            Instance("BUFG", i_I=pll_sys, o_O=self.cd_sys.clk),
            Instance("BUFG", i_I=pll_clk200, o_O=self.cd_clk200.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked),
            AsyncResetSynchronizer(self.cd_clk200, ~pll_locked),
        ]

        platform.add_platform_command("set_property SEVERITY {{Warning}} [get_drc_checks REQP-49]")

        reset_counter = Signal(4, reset=15)
        ic_reset = Signal(reset=1)
        self.sync.clk200 += \
            If(reset_counter != 0,
                reset_counter.eq(reset_counter - 1)
            ).Else(
                ic_reset.eq(0)
            )
        self.specials += Instance("IDELAYCTRL", i_REFCLK=ClockSignal("clk200"), i_RST=ic_reset)

def csr_map_update(csr_map, csr_peripherals):
    csr_map.update(dict((n, v)
        for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


class TE014SoC(SoCCore):
    csr_peripherals = {
        "dna",
        "top_gtp"
    }
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    def __init__(self):
        platform = Platform()
        sys_clk_freq = int(100e6)

        SoCCore.__init__(self, platform,
            cpu_type=None,
            clk_freq=sys_clk_freq,
            csr_data_width=32,
            with_uart=False,
            with_timer=False,
            ident="TE014SoC Example Design", ident_version=True)

        # crg
        self.submodules.crg = _CRG(platform)

        # No CPU, use Serial to control Wishbone bus
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # dna
        self.submodules.dna = dna.DNA()

        self.submodules.top_gtp = Top_gtp(self.crg.cd_sys.clk,100e6, 2e9, platform)


def main():
    args = sys.argv[1:]
    no_compile = "no_compile" in args
    soc = TE014SoC()
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()
