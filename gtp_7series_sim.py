#!/usr/bin/env python3

import os
import sys
sys.path.append("../")

from migen import *
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from migen.genlib.io import CRG

from transceiver.gtp_7series import GTPQuadPLL, GTP


_io = [
    ("gtp_refclk", 0,
        Subsignal("p", Pins("X")),
        Subsignal("n", Pins("X"))
    ),
    ("gtp_tx", 0,
        Subsignal("p", Pins("X")),
        Subsignal("n", Pins("X"))
    ),
    ("gtp_rx", 0,
        Subsignal("p", Pins("X")),
        Subsignal("n", Pins("X"))
    ),
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "", _io)


class GTPSim(Module):
    def __init__(self, platform):
        sys_clk = Signal()
        sys_clk_freq = 100e6
        self.submodules.crg = CRG(sys_clk)

        refclk100 = Signal()
        refclk100_pads = platform.request("gtp_refclk")
        self.specials += [
            Instance("IBUFDS_GTE2",
                i_CEB=0,
                i_I=refclk100_pads.p,
                i_IB=refclk100_pads.n,
                o_O=refclk100),
            Instance("BUFG", i_I=refclk100, o_O=sys_clk)
        ]

        refclk125 = Signal()
        pll_fb = Signal()
        self.specials += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", #o_LOCKED=,

                     # VCO @ 1GHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=10.0,
                     p_CLKFBOUT_MULT=10, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=sys_clk, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 125MHz
                     p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=refclk125
            ),
        ]

        qpll = GTPQuadPLL(refclk125, 125e6, 2.5e9)
        print(qpll)
        self.submodules += qpll


        tx_pads = platform.request("gtp_tx")
        rx_pads = platform.request("gtp_rx")
        gtp = GTP(qpll, tx_pads, rx_pads, sys_clk_freq,
            clock_aligner=False, internal_loopback=False)
        self.submodules += gtp

        # counter = Signal(8)
        # self.sync.tx += counter.eq(counter + 1)

        # self.comb += [
        #     gtp.encoder.k[0].eq(1),
        #     gtp.encoder.d[0].eq((5 << 5) | 28),
        #     gtp.encoder.k[1].eq(0),
        #     gtp.encoder.d[1].eq(counter),
        # ]


def generate_top():
    platform = Platform()
    soc = GTPSim(platform)
    platform.build(soc, build_dir="./", run=False)

def generate_top_tb():
    f = open("top_tb.v", "w")
    f.write("""
`timescale 1ns/1ps

module top_tb();

reg gtp_refclk;
initial gtp_refclk = 1'b1;
always #5 gtp_refclk = ~gtp_refclk;

wire gtp_p;
wire gtp_n;

top dut (
    .gtp_refclk_p(gtp_refclk),
    .gtp_refclk_n(~gtp_refclk),
    .gtp_tx_p(gtp_p),
    .gtp_tx_n(gtp_n),
    .gtp_rx_p(gtp_p),
    .gtp_rx_n(gtp_n)
);

endmodule""")
    f.close()

def run_sim():
    os.system("rm -rf xsim.dir")
    os.system("xvlog glbl.v")
    os.system("xvlog top.v")
    os.system("xvlog top_tb.v")
    os.system("xelab -debug typical top_tb glbl -s top_tb_sim -L unisims_ver -L unimacro_ver -L SIMPRIM_VER -L secureip -L $xsimdir/xil_defaultlib -timescale 1ns/1ps")
    os.system("xsim top_tb_sim -gui")

def main():
    generate_top()
    generate_top_tb()
    run_sim()

if __name__ == "__main__":
    main()
