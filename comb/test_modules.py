# -*- coding: utf-8 -*-

from myhdl import *
from .comb_modules import *
import telemetry


def test_exe1():
    @instance
    def stimulus():
        for i in range(4):
            t = bin(i, 2)
            a.next = bool(int(t[0]))
            b.next = bool(int(t[1]))
            yield delay(1)
            assert q == (a or (not b))

    q = Signal(bool(0))
    a = Signal(bool(0))
    b = Signal(bool(0))
    dut = exe1(q, a, b)
    sim = Simulation(dut, stimulus)
    sim.run()


vec = [
    "0001",
    "0010",
    "0100",
    "0111",
    "1001",
    "1010",
    "1100",
    "1111",
]


def test_exe2():
    @instance
    def stimulus():
        for t in vec:
            a.next = bool(int(t[0]))
            b.next = bool(int(t[1]))
            c.next = bool(int(t[2]))
            yield delay(1)
            assert q == bool(
                int(t[3])
            ), f"Entrada: {t[0:3]}\tSaída esperada: {t[3]}\tObtido: {int(q)}"

    q = Signal(bool(0))
    a = Signal(bool(0))
    b = Signal(bool(0))
    c = Signal(bool(0))
    dut = exe2(q, a, b, c)
    sim = Simulation(dut, stimulus)
    sim.run()


def test_exe3():
    @instance
    def stimulus():
        for i in range(2**5 - 1):
            t = bin(i, 5)
            a.next = bool(int(t[0]))
            b.next = bool(int(t[1]))
            c.next = bool(int(t[2]))
            d.next = bool(int(t[3]))
            e.next = bool(int(t[4]))
            yield delay(1)
            assert q.val == ((a or b) and c and d and e).val

    q = Signal(bool(0))
    a = Signal(bool(0))
    b = Signal(bool(0))
    c = Signal(bool(0))
    d = Signal(bool(0))
    e = Signal(bool(0))
    dut = exe3(q, a, b, c, d, e)
    sim = Simulation(dut, stimulus)
    sim.run()

    
def test_bin2bcd():
    @instance
    def stimulus():
        b.next = 12
        yield delay(1)
        assert dig0 == 2
        assert dig1 == 1

    b = Signal(modbv(0))
    dig0 = Signal(modbv(0))
    dig1 = Signal(modbv(0))
    dut = bin2bcd(b, dig1, dig0)
    sim = Simulation(dut, stimulus)
    sim.run()


def test_somador():
    @instance
    def stimulus():
        xi.next = 1
        yi.next = 1

        yield delay(1)
        assert int(soma) == 1
        

    xi = Signal(modbv(0))
    yi = Signal(modbv(0))
    carry = Signal(modbv(0))
    soma = Signal(modbv(0))

    dut = somador_completo(xi, yi,soma, carry)
    sim = Simulation(dut, stimulus)
    sim.run()
