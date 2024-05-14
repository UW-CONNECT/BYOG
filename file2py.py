#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: ID
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network



class file2py(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "ID", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("ID")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "file2py")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 500e3

        ##################################################
        # Blocks
        ##################################################

        self.network_udp_sink_0_0_1_0_0_1 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2070, 0, 32768, False)
        self.network_udp_sink_0_0_1_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2060, 0, 32768, False)
        self.network_udp_sink_0_0_1_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2040, 0, 32768, False)
        self.network_udp_sink_0_0_1_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2050, 0, 32768, False)
        self.network_udp_sink_0_0_1 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 5100, 0, 32768, False)
        self.network_udp_sink_0_0_0_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2030, 0, 32768, False)
        self.network_udp_sink_0_0_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2020, 0, 32768, False)
        self.network_udp_sink_0_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 1998, 0, 32768, False)
        self.network_udp_sink_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2010, 0, 32768, False)
        self.network_udp_sink_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 5200, 0, 32768, False)
        self.blocks_throttle2_0_8 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_7 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_6 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_5 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_4 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_3 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_2 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_1 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_file_source_0_8 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C10', False, 0, 0)
        self.blocks_file_source_0_8.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_7 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C9', False, 0, 0)
        self.blocks_file_source_0_7.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_6 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C8', False, 0, 0)
        self.blocks_file_source_0_6.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_5 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C7', False, 0, 0)
        self.blocks_file_source_0_5.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_4 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C6', False, 0, 0)
        self.blocks_file_source_0_4.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_3 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C5', False, 0, 0)
        self.blocks_file_source_0_3.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_2 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C4', False, 0, 0)
        self.blocks_file_source_0_2.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_1 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C3', False, 0, 0)
        self.blocks_file_source_0_1.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C2', False, 0, 0)
        self.blocks_file_source_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C1', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_file_source_0_0, 0), (self.blocks_throttle2_0_0, 0))
        self.connect((self.blocks_file_source_0_1, 0), (self.blocks_throttle2_0_1, 0))
        self.connect((self.blocks_file_source_0_2, 0), (self.blocks_throttle2_0_2, 0))
        self.connect((self.blocks_file_source_0_3, 0), (self.blocks_throttle2_0_3, 0))
        self.connect((self.blocks_file_source_0_4, 0), (self.blocks_throttle2_0_4, 0))
        self.connect((self.blocks_file_source_0_5, 0), (self.blocks_throttle2_0_5, 0))
        self.connect((self.blocks_file_source_0_6, 0), (self.blocks_throttle2_0_6, 0))
        self.connect((self.blocks_file_source_0_7, 0), (self.blocks_throttle2_0_7, 0))
        self.connect((self.blocks_file_source_0_8, 0), (self.blocks_throttle2_0_8, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.network_udp_sink_0_0_1_0_0_0, 0))
        self.connect((self.blocks_throttle2_0_0, 0), (self.network_udp_sink_0_0_1_0_0, 0))
        self.connect((self.blocks_throttle2_0_1, 0), (self.network_udp_sink_0_0_1_0, 0))
        self.connect((self.blocks_throttle2_0_2, 0), (self.network_udp_sink_0_0_1, 0))
        self.connect((self.blocks_throttle2_0_3, 0), (self.network_udp_sink_0_0, 0))
        self.connect((self.blocks_throttle2_0_4, 0), (self.network_udp_sink_0_0_0, 0))
        self.connect((self.blocks_throttle2_0_5, 0), (self.network_udp_sink_0_0_0_0, 0))
        self.connect((self.blocks_throttle2_0_6, 0), (self.network_udp_sink_0_0_0_0_0, 0))
        self.connect((self.blocks_throttle2_0_7, 0), (self.network_udp_sink_0_0_0_0_0_0, 0))
        self.connect((self.blocks_throttle2_0_8, 0), (self.network_udp_sink_0_0_1_0_0_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "file2py")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_1.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_2.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_3.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_4.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_5.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_6.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_7.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_8.set_sample_rate(self.samp_rate)




def main(top_block_cls=file2py, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
