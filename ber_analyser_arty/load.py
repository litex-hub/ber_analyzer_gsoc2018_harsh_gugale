from migen.build.xilinx import VivadoProgrammer

prog = VivadoProgrammer()
prog.load_bitstream("./build/gateware/top.bit")
