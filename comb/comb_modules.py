# -*- coding: utf-8 -*-
"""Exercice 1

Implemente a equacão:

q = a or !b
"""


from myhdl import *


@block
def exe1(q, a, b):
    """
    q = a or !b
    """

    @always_comb
    def comb():
        q.next = a

    return instances()


@block
def exe2(q, a, b, c):
    """
    Implemente a tabela verdade a seguir:

    A B C | Q
    ------|--
    0 0 0 | 1
    0 0 1 | 0
    0 1 0 | 0
    0 1 1 | 1
    1 0 0 | 1
    1 0 1 | 0
    1 1 0 | 0
    1 1 1 | 1

    Não utilize IF!
    """

    @always_comb
    def comb():
        q.next = a

    return instances()


@block
def exe3(q, a, b, c, d, e):
    """
    Exercice 3

    Implemente o circuito lógico a seguir:

                __
    a---------\  \
                |  |-  __
    b---------/__/  -|  \
                    |   )-
    c----------------|__/  -  __
                            -|  \
                            |   )-
    d------------------------|__/  -  __
                                    -|  \
                                    |   )-----
    e--------------------------------|__/
    """

    @always_comb
    def comb():
        q.next = a

    return instances()


@block
def exe4(led, sw):
    @always_comb
    def comb():
        led[0].next = sw[0] and (not sw[1])

    return instances()


@block
def exe5(leds, sw):
    """
    led0 é uma copia da chave sw0
    led1 é sw0 & sw1
    led2 é o led1 invertido
    led3 é xor entre sw0 e sw1
    todos os outros leds acesos
    """

    @always_comb
    def comb():
        pass

    return instances()


@block
def sw2hex(hex0, sw):
    @always_comb
    def comb():
        pass

    return instances()


@block
def bin2hex(hex0, sw):
    @always_comb
    def comb():
        if sw[4:0] == 0:
            hex0.next = "1000000"
        elif sw[4:0] == 1:
            hex0.next = "1000000"
        elif sw[4:0] == 2:
            hex0.next = "1000000"
        elif sw[4:0] == 3:
            hex0.next = "1000000"
        elif sw[4:0] == 4:
            hex0.next = "1000000"
        elif sw[4:0] == 5:
            hex0.next = "1000000"
        elif sw[4:0] == 6:
            hex0.next = "1000000"
        elif sw[4:0] == 7:
            hex0.next = "1000000"
        elif sw[4:0] == 8:
            hex0.next = "1000000"
        elif sw[4:0] == 9:
            hex0.next = "1000000"
        elif sw[4:0] == 10:
            hex0.next = "1000000"
        elif sw[4:0] == 11:
            hex0.next = "1000000"
        elif sw[4:0] == 12:
            hex0.next = "1000000"
        elif sw[4:0] == 13:
            hex0.next = "1000000"
        elif sw[4:0] == 14:
            hex0.next = "1000000"
        else:
            hex0.next = "1000000"

    return instances()

@block
def bin2bcd(b, dig1, dig0):
    @always_comb
    def comb():
       pass

    return instances()

# @block
# def somador_completo(xi, yi, soma, carry):

#     @always_comb
   
#     def comb():
        
#         soma.next = (xi(not(yi)) or yi(not(xi)))(not(carry) or carry(not((xi(not(yi)) or yi(not(xi)))))
#         carry.next = xi and yi or xi and carr or yi and carr

#     return instances()


# @block
# def somador(x, y, carry, soma):
#     n = len(x)

#     @always_comb
#     def comb():
#         for i in range(n):
#             somador_completo(xi[i], yi[i], soma[i], carry)
#     return instances()



