#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: Patron
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
import osmosdr
import time



class Chan4_2M_RTLSDR(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
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

        self.settings = Qt.QSettings("GNU Radio", "Chan4_2M_RTLSDR")

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
        self.samp_rate_0 = samp_rate_0 = 2000e3
        self.samp_rate = samp_rate = 2048e3
        self.dec_factor = dec_factor = 4
        self.M_PI = M_PI = 3.14159265358979323846
        self.FSby2 = FSby2 = samp_rate_0/(2e6)
        self.FFtaps = FFtaps = [8.98440143e-05, 9.54644754e-05, 1.53599431e-04, 9.54644754e-05, 8.98440143e-05]
        self.FBtaps = FBtaps = [1, -3.74412118,  5.30709176, -3.37351017,  0.81112777]

        ##################################################
        # Blocks
        ##################################################

        self.rtlsdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + ""
        )
        self.rtlsdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(903.2e6, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(35, 0)
        self.rtlsdr_source_0.set_if_gain(35, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(samp_rate, 0)
        self.rational_resampler_xxx_0_0_0_4 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=dec_factor,
                taps=[],
                fractional_bw=0)
        self.rational_resampler_xxx_0_0_0_3 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=dec_factor,
                taps=[],
                fractional_bw=0)
        self.rational_resampler_xxx_0_0_0_0 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=dec_factor,
                taps=[],
                fractional_bw=0)
        self.rational_resampler_xxx_0_0_0 = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=dec_factor,
                taps=[],
                fractional_bw=0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=125,
                decimation=128,
                taps=[],
                fractional_bw=0)
        self.network_udp_sink_0_0_1 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 5100, 0, 32768, False)
        self.network_udp_sink_0_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 1998, 0, 32768, False)
        self.network_udp_sink_0_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 2010, 0, 32768, False)
        self.network_udp_sink_0_0 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 5200, 0, 32768, False)
        self.iir_filter_xxx_0_0_3 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_1_2 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_1_0_0 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_1_0 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_1 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_0_0 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0_0 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.iir_filter_xxx_0_0 = filter.iir_filter_ccd(FFtaps, FBtaps, False)
        self.blocks_rotator_cc_0_0_0_0 = blocks.rotator_cc(((-0.3 * M_PI) / FSby2), False)
        self.blocks_rotator_cc_0_0_0 = blocks.rotator_cc(((0.3 * M_PI) / FSby2), False)
        self.blocks_rotator_cc_0_0 = blocks.rotator_cc(((0.1 * M_PI) / FSby2), False)
        self.blocks_rotator_cc_0 = blocks.rotator_cc(((-0.1 * M_PI) / FSby2), False)
        self.blocks_file_sink_0_0_1_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C6', False)
        self.blocks_file_sink_0_0_1_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C7', False)
        self.blocks_file_sink_0_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C4', False)
        self.blocks_file_sink_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'C:\\Users\\Patron\\Downloads\\SF_BW_EST\\C5', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_rotator_cc_0, 0), (self.iir_filter_xxx_0_0_0, 0))
        self.connect((self.blocks_rotator_cc_0_0, 0), (self.iir_filter_xxx_0_0, 0))
        self.connect((self.blocks_rotator_cc_0_0_0, 0), (self.iir_filter_xxx_0_0_1, 0))
        self.connect((self.blocks_rotator_cc_0_0_0_0, 0), (self.iir_filter_xxx_0_0_1_0, 0))
        self.connect((self.iir_filter_xxx_0_0, 0), (self.iir_filter_xxx_0_0_3, 0))
        self.connect((self.iir_filter_xxx_0_0_0, 0), (self.iir_filter_xxx_0_0_0_0, 0))
        self.connect((self.iir_filter_xxx_0_0_0_0, 0), (self.rational_resampler_xxx_0_0_0_0, 0))
        self.connect((self.iir_filter_xxx_0_0_1, 0), (self.iir_filter_xxx_0_0_1_2, 0))
        self.connect((self.iir_filter_xxx_0_0_1_0, 0), (self.iir_filter_xxx_0_0_1_0_0, 0))
        self.connect((self.iir_filter_xxx_0_0_1_0_0, 0), (self.rational_resampler_xxx_0_0_0, 0))
        self.connect((self.iir_filter_xxx_0_0_1_2, 0), (self.rational_resampler_xxx_0_0_0_4, 0))
        self.connect((self.iir_filter_xxx_0_0_3, 0), (self.rational_resampler_xxx_0_0_0_3, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_rotator_cc_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_rotator_cc_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_rotator_cc_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_rotator_cc_0_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0, 0), (self.blocks_file_sink_0_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0, 0), (self.network_udp_sink_0_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_0, 0), (self.blocks_file_sink_0_0_1_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_0, 0), (self.network_udp_sink_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_3, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_3, 0), (self.network_udp_sink_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_4, 0), (self.blocks_file_sink_0_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0_0_4, 0), (self.network_udp_sink_0_0_1, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.rational_resampler_xxx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "Chan4_2M_RTLSDR")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate_0(self):
        return self.samp_rate_0

    def set_samp_rate_0(self, samp_rate_0):
        self.samp_rate_0 = samp_rate_0
        self.set_FSby2(self.samp_rate_0/(2e6))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)
        self.rtlsdr_source_0.set_bandwidth(self.samp_rate, 0)

    def get_dec_factor(self):
        return self.dec_factor

    def set_dec_factor(self, dec_factor):
        self.dec_factor = dec_factor

    def get_M_PI(self):
        return self.M_PI

    def set_M_PI(self, M_PI):
        self.M_PI = M_PI
        self.blocks_rotator_cc_0.set_phase_inc(((-0.1 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0.set_phase_inc(((0.1 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0_0.set_phase_inc(((0.3 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0_0_0.set_phase_inc(((-0.3 * self.M_PI) / self.FSby2))

    def get_FSby2(self):
        return self.FSby2

    def set_FSby2(self, FSby2):
        self.FSby2 = FSby2
        self.blocks_rotator_cc_0.set_phase_inc(((-0.1 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0.set_phase_inc(((0.1 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0_0.set_phase_inc(((0.3 * self.M_PI) / self.FSby2))
        self.blocks_rotator_cc_0_0_0_0.set_phase_inc(((-0.3 * self.M_PI) / self.FSby2))

    def get_FFtaps(self):
        return self.FFtaps

    def set_FFtaps(self, FFtaps):
        self.FFtaps = FFtaps
        self.iir_filter_xxx_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_2.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_3.set_taps(self.FFtaps, self.FBtaps)

    def get_FBtaps(self):
        return self.FBtaps

    def set_FBtaps(self, FBtaps):
        self.FBtaps = FBtaps
        self.iir_filter_xxx_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_0_0.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_1_2.set_taps(self.FFtaps, self.FBtaps)
        self.iir_filter_xxx_0_0_3.set_taps(self.FFtaps, self.FBtaps)




def main(top_block_cls=Chan4_2M_RTLSDR, options=None):

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
