#!/usr/bin/env python3

from myhdl import *
from .cpu import *
from .sequencial import *
from .hw_util import *

import os.path


@block
def z01_sim(ram, rom, lst_data):
    instruction = Signal(intbv(0)[18:])
    inMem, outMem = [Signal(modbv(0)[16:]) for i in range(2)]
    pcount, addressM = [Signal(intbv(0)[15:]) for i in range(2)]
    writeM, clk = [Signal(bool(0)) for i in range(2)]
    clkMem = Signal(bool(0))
    rst = ResetSignal(0, active=1, isasync=True)

    cpu_1 = cpu(
        inMem, instruction, outMem, addressM, writeM, pcount, rst, clk, lst_data
    )
    ram_1 = ram_sim(ram, inMem, outMem, addressM, writeM, clkMem, depth=2**15 - 1)
    rom_1 = rom_sim(instruction, pcount, clk, rom)

    @always(delay(2))
    def clkgen():
        clk.next = not clk

    @always(delay(1))
    def clkgenMem():
        clkMem.next = not clkMem

    @instance
    def rst():
        rst.next = 1
        yield delay(5)
        rst.next = 0

    return instances()


class test_z01:
    def __init__(self, name, rom, ram, time):
        self.name = name
        self.rom = rom
        self.ram = ram
        self.runTime = time
        self.lst_data = []

    def run(self):
        print("--- %s ---" % self.name)
        tb = z01_sim(self.ram, self.rom, self.lst_data)
        tb.config_sim(trace=True, name=self.name, tracebackup=False)
        tb.run_sim(self.runTime)
        tb.quit_sim()
        return {"ram": self.ram, "tst": self.lst_data}

    def dump(self):
        lstWrite(self.lst_data, self.name + ".lst")
        mem_dump_file(self.ram, self.name + "_ram_end.txt")
