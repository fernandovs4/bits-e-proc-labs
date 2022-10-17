# -*- coding: utf-8 -*-
# Eduardo Marossi & Rafael Corsi @ insper.edu.br
# Dez/2017
# Disciplina Elementos de Sistemas
import os, sys, file_utils, argparse, shutil
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from bits import proc_run
from bits.hw.hw_util import rom_init_from_hack

PATH_APP       = os.path.dirname(os.path.abspath(__file__))
TEMP_PATH      = PATH_APP + "/temp"


class RamAddr:
    def __init__(self, val):
        self.val = val

class SimulatorTask(QObject):
    finished = pyqtSignal()

    def __init__(self, temp_path="", verbose=False, debug=False, rtl_dir=None):
        super().__init__()
        self.verbose = verbose
        self.file_ram_out =  os.path.abspath(temp_path + "ram_out.mif")
        self.file_lcd_out =  os.path.abspath(temp_path + "lcd.pgm")
        self.lst_vsim   = 'temp/rom_in.nasm' # TODO: tosco, melhorar isso !
        self.temp_path = temp_path
        self.debug = debug
        self.ram_contents = {}
        self.rtl_dir = rtl_dir

    def setup(self, stream_rom_in, stream_ram_in, stream_lst_out, simulation_time):
        self.file_rom_in  = self._setup_file(stream_rom_in, self.temp_path + "/rom_out.hack")
        self.lst_stream   = stream_lst_out
        self.simulation_time = simulation_time

        stream_ram_in.seek(0, 0)
        self.ram_contents.clear()
        for i, l in enumerate(stream_ram_in):
            val = int(l, 2)
            if val == 0:
                continue
            self.ram_contents[i] = val

    def _setup_file(self, fsrc, filename):
        fsrc.seek(0, 0)
        ftemp_n = filename + ".tmp"
        ftemp = open(ftemp_n, "w")
        shutil.copyfileobj(fsrc, ftemp)
        ftemp.close()
        os.unlink(ftemp_n)
        return filename

    def run(self):
        if self.verbose:
            print("Starting simulator....")

        rom = rom_init_from_hack(self.file_rom_in)
        proc_run('rom', rom, self.ram_contents, self.simulation_time, dump=True)

        self.lst_vsim = 'rom.lst'

        file_utils.file_to_stream(self.lst_vsim, self.lst_stream)
        if self.verbose:
            print("Ending emulator....")
        self.finished.emit()

if __name__ == "__main__":
    sim = SimulatorTask(TEMP_PATH, True)
    parser = argparse.ArgumentParser(description="Simulate Z01 CPU using ROM, RAM in binary formats. Outputs a LST simulation result file")
    parser.add_argument('rom_in')
    parser.add_argument('ram_in')
    parser.add_argument('simulation_time')
    parser.add_argument('lst_out')
    args = parser.parse_args()
    if(args.ram_in == "0"):
        args.ram_in = file_utils.create_empty_rom("empty_ram.bin")
    sim.setup(open(args.rom_in, "r"), open(args.ram_in, "r"), open(args.lst_out, "w"), args.simulation_time)
    sim.run()
