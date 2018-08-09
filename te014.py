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

from math import *
from top_gtp import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

_io = [
    ("clk_in", 0, Pins("T14"), IOStandard("LVCMOS33")),

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


class _CRG(Module):
    def __init__(self, platform,pll):
        self.clock_domains.cd_sys = ClockDomain()

        clk_in = platform.request("clk_in")
        clk_in.attr.add("keep")
        platform.add_period_constraint(clk_in,pll["fin_period"])

        pll_locked = Signal()
        pll_fb = Signal()
        pll_sys = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=pll_locked,

                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=pll["fin_period"],
                     p_CLKFBOUT_MULT=pll["m"], p_DIVCLK_DIVIDE=pll["d"],
                     i_CLKIN1=clk_in, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 100 MHz
                     p_CLKOUT0_DIVIDE=pll["o"], p_CLKOUT0_PHASE=0.0,
                     o_CLKOUT0=pll_sys,
            ),
            Instance("BUFG", i_I=pll_sys, o_O=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_sys, ~pll_locked),
        ]

        platform.add_platform_command("set_property SEVERITY {{Warning}} [get_drc_checks REQP-49]")

def csr_map_update(csr_map, csr_peripherals):
    csr_map.update(dict((n, v)
        for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


class TE014SoC(SoCCore):
    csr_peripherals = {
        "dna",
        "top_gtp"
    }
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    def __init__(self,pll):
        platform = Platform()
        sys_clk_freq = int(pll["refclk_freq"])

        SoCCore.__init__(self, platform,
            cpu_type=None,
            clk_freq=sys_clk_freq,
            csr_data_width=32,
            with_uart=False,
            with_timer=False,
            ident="Bit Error Ratio Analyzer", ident_version=True)

        # crg
        self.submodules.crg = _CRG(platform,pll)

        # No CPU, use Serial to control Wishbone bus
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # dna
        self.submodules.dna = dna.DNA()

        self.submodules.top_gtp = Top_gtp(self.crg.cd_sys.clk,pll["refclk_freq"], pll["linerate"], platform)

def pllSettings(linerate,fin):
	allowed_linerates = [i*5e8 for i in range(2,13)]
	if linerate not in allowed_linerates:
		raise ValueError("Allowed linerates : 1GHz - 6GHz in increments of 0.5GHz")

	required_refclk = linerate/20

	fvcomax = 1600e6
	fvcomin = 800e6
	fpfdmin = 19e6
	fpfdmax = 500e6

	dmin = ceil(fin/fpfdmax)

	assert dmin<=106 and dmin>=1

	mideal = round(((dmin*fvcomax)/fin),3)
	assert mideal<=64 and mideal>=2

	o = round(((fin*mideal)/(dmin*required_refclk)),3)
	assert o<=128 and o>=1

	fin_period = round((1e9/fin),3)

	print("D : {0:8.5f} \nM : {1:8.5f} \nO : {2:8.5f}".format(dmin,mideal,o))

	return {"d":dmin,"m":mideal,"o":o,"fin":fin,"fin_period":fin_period,"refclk_freq":required_refclk,"linerate":linerate}


def main():
	linerate = 3e9
	fin = 25e6
	args = sys.argv[1:]
	no_compile = "no_compile" in args
	pll = pllSettings(linerate,fin)
	soc = TE014SoC(pll)
	builder = Builder(soc, output_dir="build", csr_csv="./csr.csv")
	vns = builder.build()

if __name__ == "__main__":
	main()
