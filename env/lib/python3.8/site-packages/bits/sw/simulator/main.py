# -*- coding: utf-8 -*-
# Eduardo Marossi & Rafael Corsi @ insper.edu.br
# Dez/2017
# Disciplina Elementos de Sistemas
import sys, os, tempfile
import argparse
sys.path.insert(0, ".")
import asm_utils, file_utils
import config_dialog
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog, QActionGroup, QMessageBox, QProgressDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QTextCursor, QColor, QTextFormat
from PyQt5.QtCore import QThread, QFileSystemWatcher
from main_window import *
from simulator_task import SimulatorTask, TEMP_PATH
from assembler_task import AssemblerTask
from lst_parser import LSTParser


if sys.version_info[0] < 3:
    print ("Precisa ser o Python 3")
    exit()


class TextEditor(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signalMouseDoubleClickEvent = None

    def mouseDoubleClickEvent(self, e: QtGui.QMouseEvent) -> None:
        if self.signalMouseDoubleClickEvent is not None:
            self.signalMouseDoubleClickEvent()


class AppMainWindow(QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

    def resizeEvent(self, event):
        self.resized.emit()
        return QMainWindow.resizeEvent(self, event)


class AppMain(Ui_MainWindow):
    RAM_VIEW_INITIAL_SIZE = 21186
    TEMP_MAX_RAM_USE = 1024*1000
    STEP_TIMER_IN_MS = 1000
    COLOR_NOT_SELECTED = QColor(0, 0, 0, 0)
    COLOR_BREAKPOINT = QColor(209, 220, 236)
    COLOR_CURRENT_LINE = QColor(0, 0, 0, 127)

    def __init__(self):
        Ui_MainWindow.__init__(self)

        ## class Variables
        self.config_dialog = None
        self.rom_stream = None
        self.rom_path = None
        self.rom_type_sel = None
        self.rom_watcher = None
        self.ram_model = None
        self.data_changed = None
        self.lst_parser = None
        self.last_step = None
        self.editor_converting = False
        self.pixmap_ALU = None
        self.asm_thread = None
        self.sim_thread = None
        self.config_dialog_ui = None
        self.actionROMGroup = None
        self.actionRAMGroup = None
        self.actionREGGroup = None
        self.step_timer = None
        self.romViewSelections = None
        self.breakpointsSelection = None
        self.romCurrentLineSelection = None
        self.romView = None
        self.window = AppMainWindow()

        # Setup Dialog, Editor, Actions, Threads, Img Resizing
        self.setup_dialog()
        self.setupUi(self.window)
        self.setup_editor()
        self.setup_actions()
        self.setup_threads()

        self.SW = [self.SW9, self.SW8, self.SW7, self.SW6, self.SW5, self.SW4, self.SW3, self.SW2, self.SW1, self.SW0]
        self.LEDR = [self.LEDR9, self.LEDR8, self.LEDR7, self.LEDR6, self.LEDR5, self.LEDR4, self.LEDR3, self.LEDR2,
                     self.LEDR1, self.LEDR0]

    def load_icon(self):
        app_icon = QtGui.QIcon()
        app_icon.addFile('theme/icon/16x16.png', QtCore.QSize(16, 16))
        app_icon.addFile('theme/icon/24x24.png', QtCore.QSize(24, 24))
        app_icon.addFile('theme/icon/32x32.png', QtCore.QSize(32, 32))
        app_icon.addFile('theme/icon/48x48.png', QtCore.QSize(48, 48))
        app_icon.addFile('theme/icon/256x256.png', QtCore.QSize(256, 256))
        return app_icon

    def setup_editor(self):
        self.verticalLayout_Rom.removeWidget(self.romView)
        self.romView = TextEditor(self.romView.parent())
        self.romView.setFontPointSize(16)
        self.romCurrentLineSelection = QtWidgets.QTextEdit.ExtraSelection()
        self.romCurrentLineSelection.cursor = QTextCursor(self.romView.textCursor())
        self.romCurrentLineSelection.format.setBackground(AppMain.COLOR_NOT_SELECTED)
        self.romCurrentLineSelection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.romViewSelections = [self.romCurrentLineSelection]
        self.breakpointsSelection = []
        self.romView.setExtraSelections(self.romViewSelections)
        self.verticalLayout_Rom.addWidget(self.romView)

        self.rom_stream = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
        self.rom_path = None
        self.rom_type_sel = self.actionROMAssembly
        self.lst_parser = None
        self.rom_watcher = QFileSystemWatcher()
        self.rom_watcher.fileChanged.connect(self.reload_rom)
        self.editor_converting = False
        self.label_S.hide()
        self.lineEdit_S.hide()
        self.label_A.setStyleSheet('QLabel { font-size: 12pt; }')
        self.label_D.setStyleSheet('QLabel { font-size: 12pt; }')
        self.label_S.setStyleSheet('QLabel { font-size: 12pt; }')
        self.label_inM.setStyleSheet('QLabel { font-size: 12pt; }')
        self.label_outM.setStyleSheet('QLabel { font-size: 12pt; }')
        self.toolBar.addSeparator()
        self.lineEdit_A.setStyleSheet(self.style_register())
        self.lineEdit_D.setStyleSheet(self.style_register())
        self.lineEdit_inM.setStyleSheet(self.style_register())
        self.lineEdit_outM.setStyleSheet(self.style_register())
        self.on_new()
        self.window.setWindowIcon(self.load_icon())

    def style_register(self):
        return 'QLineEdit { border: none; background-color: transparent; font-size:12pt; color:black; }'

    def style_register_active(self):
        return 'QLineEdit { border: none; background-color: yellow; font-size:12pt; color:black; }'

    def setup_threads(self):
        self.asm_thread = QThread()
        self.sim_thread = QThread()

    def setup_dialog(self):
        self.config_dialog = QDialog()
        self.config_dialog_ui = config_dialog.Ui_Dialog()
        self.config_dialog_ui.setupUi(self.config_dialog)

    def reload_lcd(self):
        if os.path.exists(os.path.join(TEMP_PATH, 'lcd.pgm')):
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(os.path.join(TEMP_PATH, 'lcd.pgm')), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.LCDButton.setIcon(icon)
            self.LCDButton.setIconSize(QtCore.QSize(320, 240))
        else:
            icon = QtGui.QIcon()
            self.LCDButton.setIcon(icon)

    def clean_lcd(self):
        if os.path.exists(os.path.join(TEMP_PATH, 'lcd.pgm')):
            os.unlink(os.path.join(TEMP_PATH, 'lcd.pgm'))

    def setup_clean_views(self, table, rows=100, caption="Dados", line_header=None):
        model = QStandardItemModel(rows, 1, self.window)
        model.setHorizontalHeaderItem(0, QStandardItem(caption))
        table.setModel(model)

        for l in range(0, rows):
            if line_header is None:
                model.setHeaderData(l, QtCore.Qt.Vertical, l)
            else:
                model.setHeaderData(l, QtCore.Qt.Vertical, line_header(l))

        return model

    def setup_actions(self):
        self.step_timer = QtCore.QTimer()
        self.step_timer.timeout.connect(self.on_proximo)
        self.actionNovo.triggered.connect(self.on_new)
        self.actionSalvar_ROM.triggered.connect(self.on_save)
        self.actionAbrir.triggered.connect(self.on_load)
        self.actionProximo.triggered.connect(self.on_proximo)
        self.actionExecutarFim.triggered.connect(self.on_executar_fim)
        self.actionIrFim.triggered.connect(self.on_ir_fim)
        self.actionParar.triggered.connect(self.on_parar)
        self.actionEraseRAM.triggered.connect(self.on_clear_ram)
        self.actionVoltarInicio.triggered.connect(self.on_voltar_inicio)
        self.actionROMAssembly.triggered.connect(self.on_rom_assembly)
        self.actionROMBinario.triggered.connect(self.on_rom_binary)
        self.actionROMGroup = QActionGroup(self.window)
        self.actionROMGroup.addAction(self.actionROMAssembly)
        self.actionROMGroup.addAction(self.actionROMBinario)
        self.actionROMAssembly.setChecked(True)
        self.actionConfiguracoes.triggered.connect(self.config_dialog.show)
        self.romView.signalMouseDoubleClickEvent = self.set_breakpoint

    def set_breakpoint(self):
        cursor = self.romView.textCursor()
        remove = None
        for sel in self.romViewSelections:
            if cursor.blockNumber() == sel.cursor.blockNumber():
                remove = sel
                break

        if remove is not None:
            self.romViewSelections.remove(remove)
            self.romView.setExtraSelections(self.romViewSelections)
            return

        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(AppMain.COLOR_BREAKPOINT)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = QTextCursor(cursor)
        selection.cursor.clearSelection()
        self.romViewSelections.append(selection)
        self.romView.setExtraSelections(self.romViewSelections)
        self.breakpointsSelection.append(selection)

    def check_breakpoint_exists(self, index):
        for sel in self.breakpointsSelection:
            if sel.cursor.blockNumber() == index:
                return True
        return False

    def on_rom_assembly(self):
        self.editor_converting = True
        self.on_clear_rom()
        file_utils.copy_file_to_textedit(self.rom_stream, self.romView)
        self.rom_type_sel = self.actionROMAssembly
        self.editor_converting = False

    def on_rom_binary(self):
        self.editor_converting = True
        if self.rom_type_sel == self.actionROMAssembly:
            file_utils.copy_textedit_to_file(self.romView, self.rom_stream)
            self.assemble(self.load_converted_asm_bin)

        self.rom_type_sel = self.actionROMBinario

    def on_ram_tooltip(self, item):
        text = item.text().strip()

        try:
            val = int(text, 2)
        except ValueError:
            return

        item.setToolTip("{0:d} dec - {1:x} hex".format(val, val))

    def on_clear_rom(self):
        self.romView.clear()

    def on_clear_ram(self):
        self.ram_model = self.setup_clean_views(self.ramView, rows=self.RAM_VIEW_INITIAL_SIZE, caption="RAM", line_header=asm_utils.z01_ram_name)
        for i in range(0, self.RAM_VIEW_INITIAL_SIZE):
            item = QStandardItem("0000000000000000")
            self.on_ram_tooltip(item)
            self.ram_model.setItem(i, item)

    def on_new(self):
        self.rom_path = None
        self.on_clear_ram()
        self.on_clear_rom()
        self.ram_model.itemChanged.connect(self.valid_ram)
        self.actionROMAssembly.setEnabled(True)
        self.clear_simulation()

    def on_voltar_inicio(self):
        self.clean_lcd()
        self.reload_lcd()
        self.keys_set_enable(True)
        self.data_changed = True
        self.clear_simulation()

    def on_parar(self):
        self.keys_to_ram()
        self.step_timer.stop()

    def on_executar_fim(self):
        self.step_timer.start(self.STEP_TIMER_IN_MS)

    def on_ir_fim(self):
        self.step_timer.start(0) 

    def show(self):
        self.window.show()

    def on_save(self):
        filename = self.rom_path

        if self.rom_path is not None:
            self.rom_watcher.removePath(self.rom_path)

        if filename is None:
            filename = QFileDialog.getSaveFileName(self.window, "Salve o arquivo", os.getcwd(), "Arquivos (*.hack *.nasm)")
            if len(filename) == 0 or len(filename[0]) == 0:
                return None
            filename = filename[0]
            self.rom_path = filename

        if self.actionROMAssembly.isChecked():
            file_utils.copy_textedit_to_file(self.romView, self.rom_stream)

        file_utils.stream_to_file(self.rom_stream, filename)
        self.rom_watcher.addPath(self.rom_path)

    def on_load(self):
        filename = QFileDialog.getOpenFileName(self.window, "Escolha arquivo", os.getcwd(), "Arquivos (*)")
        if len(filename) == 0 or len(filename[0]) == 0:
            return None

        if self.rom_path is not None:
            self.rom_watcher.removePath(self.rom_path)

        self.on_new()
        self.rom_path = filename[0]
        self.rom_watcher.addPath(self.rom_path)
        self.reload_rom()

    def reload_rom(self):
        return self.load_rom(self.rom_path)

    def load_rom(self, filename):
        if not os.path.exists(filename):
            return

        if filename.endswith(".asm") or filename.endswith(".nasm"):
            self.load_asm(filename, self.romView)
        elif filename.endswith(".bin") or filename.endswith(".hack"):
            self.load_bin(filename, self.romView)

    def on_proximo(self):
        if self.data_changed:
            self.clean_lcd()
            if self.lst_parser is not None:
                self.lst_parser.close()

            self.keys_set_enable(False)
            self.keys_to_ram()

            if self.actionROMAssembly.isChecked():
                file_utils.copy_textedit_to_file(self.romView, self.rom_stream)
                self.assemble(self.assemble_end)
            else:
                tmp_rom = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
                file_utils.copy_textedit_to_file(self.romView, tmp_rom)
                tmp_ram = self.get_updated_ram()
                self.simulate(tmp_rom, tmp_ram)

            return False
        step = self.lst_parser.advance()

        if "s_regAout" not in step:
            self.step_timer.stop()
            QMessageBox.warning(self.window, "Simulador", "Fim de simulação")
            return

        self.update_line_edit(self.lineEdit_A, step["s_regAout"])
        self.update_line_edit(self.lineEdit_D, step["s_regDout"])
        self.update_line_edit(self.lineEdit_inM, step["inM"])
        self.update_line_edit(self.lineEdit_outM, step["outM"])

        if self.last_step is not None:
            addr = int(step["s_regAout"], 2)
            index = self.ram_model.index(addr, 0)
            if int(step["writeM"]) == 0 and int(step["c_muxALUI_A"]) == 1 and int(self.last_step["c_muxALUI_A"]) == 0:
               self.ramView.setCurrentIndex(index)

            if int(step["writeM"]) == 1:
               self.ramView.setCurrentIndex(index)
               self.ram_model.itemFromIndex(index).setText(step["outM"])

        ## update ROM line
        pc_counter = int(step["pcout"], 2)

        if pc_counter < 0:
            pc_counter = 0

        if self.actionROMAssembly.isChecked():
            rom_line = asm_utils.z01_real_line(self.assembler_task.labels_pos, pc_counter) - 1
        else:
            rom_line = pc_counter - 1

        if rom_line < 0:
            rom_line = 0

        if self.check_breakpoint_exists(rom_line):
            print('Breakpoint')
            self.step_timer.stop()

        document = self.romView.document()
        block = document.findBlockByLineNumber(rom_line)
        self.romCurrentLineSelection.cursor = QTextCursor(block)
        self.romCurrentLineSelection.format.setBackground(AppMain.COLOR_CURRENT_LINE)
        self.romView.setExtraSelections(self.romViewSelections)
        self.ram_to_leds()
        print("Próximo")
        self.reload_lcd()
        self.last_step = step

    def update_line_edit(self, line_edit, new_value, ignore=False):
        if line_edit.text() != new_value:
            line_edit.setText(new_value)
            if not ignore:
                line_edit.setStyleSheet(self.style_register_active())
            valid = self.valid_binary(line_edit)
            if valid:
                self.on_ram_tooltip(line_edit)
        else:
            line_edit.setStyleSheet(self.style_register())

    def valid_ram(self, item):
        if not item.text():
            return None
        text = item.text()
        index = item.index()

        while index.row() + 100 >= self.ram_model.rowCount():
            self.ram_model.appendRow(QStandardItem("{0:0>16b}".format(0)))

        if text.startswith("d"):
            text = text[1:]
            if text.isdigit():
                item.setText("{0:0>16b}".format(int(text)))

        valid = self.valid_binary(item)

        if valid:
            self.data_changed = True
            self.on_ram_tooltip(item)
        else:
            item.setText("{0:0>16b}".format(0))

    def assemble(self, callback):
        if self.asm_thread.isRunning() or self.sim_thread.isRunning():
            print("Assembler está sendo executado...")
            return False

        assembler = 'myassembler'
        self.assembler_task = AssemblerTask(assembler, "temp/")
        rom_in = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
        rom_out = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
        file_utils.copy_file_to_file(self.rom_stream, rom_in)
        self.assembler_task.setup(rom_in, rom_out)
        self.assembler_task.finished.connect(callback)
        self.assembler_task.moveToThread(self.asm_thread)
        self.asm_thread.started.connect(self.assembler_task.run)
        self.asm_thread.start()

    def simulate(self, rom_file, ram_file):
        if self.asm_thread.isRunning() or self.sim_thread.isRunning():
            print("Simulador está sendo executado...")
            return False

        self.simulator_task = SimulatorTask("temp/", False, False, '')
        lst_out = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
        self.simulator_task.setup(rom_file, ram_file, lst_out, int(self.config_dialog_ui.simTime.text()))
        self.simulator_task.finished.connect(self.simulation_end)
        self.simulator_task.moveToThread(self.sim_thread)
        self.sim_thread.started.connect(self.simulator_task.run)
        self.sim_thread.start()
        self.lock_and_show_dialog()
        self.lst_parser.advance()

    def lock_and_show_dialog(self):
        ## waits for ASM thread and SIM thread to end
        self.progress_dialog = QProgressDialog("Simulando...", "Cancelar", 0, 0, self.window)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setWindowTitle("RESimulatorGUI")
        self.progress_dialog.setWindowFlags(self.progress_dialog.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

        while self.asm_thread.isRunning() or self.sim_thread.isRunning():
            QApplication.processEvents()

        self.progress_dialog.reset()

    def read_keys(self):
        data = 0
        for k in self.SW:
            data = data << 1
            if k.isChecked():
                data = data | 1
        return data

    def keys_set_enable(self, enable=True):
        for k in self.SW:
            k.setEnabled(enable)

    def keys_to_ram(self):
        data = '{0:0>16b}'.format(self.read_keys())
        self.ram_model.setItem(21185, QStandardItem(data))

    def ram_to_leds(self):
        index = self.ram_model.index(21184, 0)
        data = self.ram_model.itemFromIndex(index).text().strip()
        for c in range(0, 10):
            if data[6+c] == '1':
                self.LEDR[c].setChecked(True)
            elif data[6+c] == '0':
                self.LEDR[c].setChecked(False)

    def get_updated_ram(self):
        ram = tempfile.SpooledTemporaryFile(max_size=self.TEMP_MAX_RAM_USE, mode="w+")
        file_utils.copy_model_to_file(self.ram_model, ram)
        return ram

    def check_assembler_sucess(self):
        if self.assembler_task is not None and self.assembler_task.success is True:
            return True
        QMessageBox.critical(self.window, "Assembler", "Erro ao traduzir assembly.")
        self.step_timer.stop()
        return False

    def assemble_end(self):
        self.asm_thread.quit() # ensure end of thread
        self.asm_thread.wait()
        ram = self.get_updated_ram()
        if not self.check_assembler_sucess():
            return
        print("ASM done!")
        self.simulate(self.assembler_task.stream_out, ram)

    def simulation_end(self):
        self.sim_thread.quit() #ensure end of thread
        self.sim_thread.wait()
        print("SIM done!")
        self.data_changed = False
        self.lst_parser = LSTParser(self.simulator_task.lst_stream)

        if self.actionROMAssembly.isChecked():
            rom_line = asm_utils.z01_real_line(self.assembler_task.labels_pos, 0)
        else:
            rom_line = 0

        document = self.romView.document()
        self.romCurrentLineSelection.cursor = QTextCursor(document.findBlockByLineNumber(rom_line))
        self.romView.setExtraSelections(self.romViewSelections)

    def load_converted_asm_bin(self):
        self.asm_thread.quit()
        self.asm_thread.wait()
        if not self.check_assembler_sucess():
            return
        self.on_clear_rom()
        file_utils.copy_file_to_textedit(self.assembler_task.stream_out, self.romView)
        self.editor_converting = False

    def load_converted_asm_hex(self):
        self.asm_thread.quit()
        self.asm_thread.wait()
        if not self.check_assembler_sucess():
            return
        self.on_clear_rom()
        file_utils.copy_file_to_textedit(self.assembler_task.stream_out, self.romView, asm_utils.bin_str_to_hex)
        self.editor_converting = False

    def valid_binary(self, item):
        valid = True
        text = item.text().strip()

        try:
            val = int(text, 2)
        except ValueError:
            valid = False

        if not valid:
           print("Invalid BIN Instruction: {}".format(item.text()))

        return valid

    def clear_simulation(self):
        self.last_step = None
        self.update_line_edit(self.lineEdit_A, "0000000000000000", True)
        #self.update_line_edit(self.lineEdit_S, "0000000000000000", True)
        self.update_line_edit(self.lineEdit_D, "0000000000000000", True)
        self.update_line_edit(self.lineEdit_inM, "0000000000000000", True)
        self.update_line_edit(self.lineEdit_outM, "0000000000000000", True)
        self.data_changed = True
        index = self.ram_model.index(0, 0)
        self.ramView.setCurrentIndex(index)
        document = self.romView.document()
        self.romCurrentLineSelection.cursor = QTextCursor(document.findBlockByLineNumber(0))
        self.romCurrentLineSelection.format.setBackground(AppMain.COLOR_NOT_SELECTED)
        self.romCurrentLineSelection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.romView.setExtraSelections(self.romViewSelections)

    def load_file(self, filename, model):
        fp = open(filename, "r")
        self.on_clear_rom()
        file_utils.copy_file_to_textedit(fp, model)
        fp.close()

    def load_asm(self, filename, model):
        self.actionROMAssembly.setChecked(True)
        self.load_file(filename, model)

    def load_bin(self, filename, model):
        self.actionROMBinario.setChecked(True)
        self.actionROMAssembly.setEnabled(False)
        self.load_file(filename, model)


def init_simulator_gui(rtl_dir):
    qapp = QApplication(sys.argv)
    app = AppMain()
    app.show()
    sys.exit(qapp.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Z01 Simulator command line options")
    parser.add_argument("--rtl_dir", default=None)
    args = parser.parse_args()
    init_simulator_gui(args.rtl_dir)