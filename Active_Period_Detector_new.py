import time
import matplotlib.pyplot as plt
import statistics as st
import DWT_compress as DWT
from threading import Thread
from utils import *
import numpy as np
import math

"""
Active_Period_Detector pipeline:
[consumer]: A constantly running process (after configuration) that will maintain input buffer reconstruction, 
            active period fragmentation, and other necessary functions for active period detection

in_queue[] -> consumer -> out_queue[]
"""


class Active_Period_Detector_new:

    def __init__(self, channel, in_queue, out_queue):
        #####################################################################
        self.minSF = 7
        self.win_jump_factor = 2
        self.num_accum = 32
        self.lst_flag_left = 0
        self.lst_flag_right = 0
        self.nfl_flag = 0
        self.nfl = 7.5  # 4.7e-5#7.5#0.4

        self.cur_flag_left = 0
        self.cur_flag_right = 0
        self.lst_chunk = np.ndarray((0,), dtype=np.complex64)
        self.lst_wind = []
        self.tail_sz = (2 ** self.minSF) * UPSAMPLE_FACTOR * 48

        self.num_chunk = 0
        self.ind_arr = []

        #####################################################################
        # interface queues
        self.in_q = in_queue
        self.out_q = out_queue
        self.apd_num = 0

        # active period detection constants
        # self.win_jump_factor = 3
        self.num_keep = 3
        self.front_buf = 2 * self.win_jump_factor
        self.rear_buf = 4 * self.win_jump_factor

        # active period detection constants after initialization
        self.ASD_small_thresh_high = 0
        self.ASD_small_thresh_low = 0
        self.ASD_small_superDC = build_super_DC(9)
        self.ASD_big_thresh_high = 0
        self.ASD_big_thresh_low = 0
        self.ASD_big_superDC = build_super_DC(12)
        self.Noise_Avg = 0

        # internal state values
        self.curr_state = 0
        self.low_buffer = 0
        self.frag_store = None
        self.frag_buff = np.ndarray((0,), dtype=np.complex64)

        self.last_buff = np.ndarray((0,), dtype=np.complex64)

        np.random.seed(1234)

        # internal data to save
        print(f"Hey I am channel: {channel}")
        self.channel = channel
        self.center_freq = CENTER_FREQ + channel * FREQ_OFF
        overlap = 10 * RAW_FS / BW

        # self.static_config(0.00007797103913, 9.14960812776426, 0.269693977605989, 2, 'low')
        self.config_flag = False

        # consumer and sender thread
        self.sender = Thread(target=self.consumer2, args=[])

    def start_consuming(self):
        self.sender.start()

    def send_packet(self, info, chunk):
        self.apd_num += 1
        # if self.out_q.qsize() / QUEUE_SIZE < 1:
        # self.out_q.append((info, chunk, time.time(), self.channel))
        self.out_q.put((info, chunk, time.time(), self.channel))
        # print(f'Length of out_q = {self.out_q.qsize()}')
        # else:
        #     self.out_q.put((info, None, len(chunk), self.channel))
        time.sleep(0.5 * (info[1] - info[0]) / FS)

    def consumer2(self):
        startt = time.time()
        while True:
            if not self.in_q.empty():
                # print(f'Length of Out_Q = {len(self.out_q)}\n')
                # print(f'Length of Out_Q = {self.out_q.qsize()}\n')
                print(f'APD detected so far = {self.apd_num}\n')
                startt = time.time()
                buff = self.in_q.get()
                very_start = buff[1]
                # buff = channelize(buff[0], self.phaser, self.filt)
                buff = buff[0].astype(np.complex64)
                ##########################################################################
                buff = buff[10 * UPSAMPLE_FACTOR:-10 * UPSAMPLE_FACTOR]
                print(len(buff))
                ##########################################################################
                if not self.config_flag:
                    # self.configNF(buff, 'low')
                    self.config_flag = True

                uplink_wind = self.Active_Sess_SFAgn2(buff)
                print(f'Found {len(uplink_wind)} active Periods')

                # if len(uplink_wind) > 0:
                #
                self.lst_chunk = buff

            else:
                if time.time() - startt > 25:
                    return
                else:
                    time.sleep(0.25)

    def Active_Sess_SFAgn2(self, x_1):
        upsampling_factor = UPSAMPLE_FACTOR
        windsz = 2 ** self.minSF
        win_jump = int(np.floor(windsz * upsampling_factor / self.win_jump_factor))

        uplink_wind = []

        idx = np.concatenate([np.array(range(0, int(windsz / 2))), np.array(
            range(int(windsz / 2 + (upsampling_factor - 1) * windsz), int((upsampling_factor) * windsz)))])
        x_1_len = len(x_1)

        ind_arr_len = int(np.floor(x_1_len / win_jump) - (self.win_jump_factor * (self.win_jump_factor - 1)))

        for i in range(1, int(np.floor(x_1_len / win_jump) - (self.win_jump_factor * (self.win_jump_factor - 1)))):
            if self.num_chunk > 0:
                x_1 = np.append(self.lst_chunk[len(self.lst_chunk) - int((1 + (1 - (1/self.win_jump_factor))) * windsz * upsampling_factor): len(self.lst_chunk)],x_1)
            wind_fft = np.abs(np.fft.fft(np.multiply(x_1[(i - 1) * win_jump: (i - 1) * win_jump + (windsz * upsampling_factor)], np.conj(x_1[(i - 1) * win_jump + (windsz * upsampling_factor): (i - 1) * win_jump + (2 * windsz * upsampling_factor)]))))
            w_f = wind_fft[idx]
            ind = np.argmax(w_f)

            self.ind_arr.append(ind)


            if len(self.ind_arr) > ind_arr_len:
                self.ind_arr.pop(0)

            if len(self.ind_arr) == ind_arr_len:
                D_1 = 0
                D_65 = 0
                D_97 = 0
                D_113 = 0
                D_121 = 0
                D_125 = 0
                for o in self.ind_arr:
                    if o == 0 or o == 1:
                        D_1 += 1
                    elif o == 64 or o == 63 or o == 65:
                        D_65 += 1
                    elif o == 96 or o == 95 or o == 97:
                        D_97 += 1
                    elif o == 112 or o == 111 or o == 113:
                        D_113 += 1
                    elif o == 120 or o == 119 or o == 121:
                        D_121 += 1
                    elif o == 124 or o == 123 or o == 125:
                        D_125 += 1
                f1 = open('Data_log.txt', 'a')
                f1.write(f"{D_1}, \t{D_65}, \t{D_97}, \t{D_113}, \t{D_121}, \t{D_125},\n")
                f1.close()

        self.num_chunk += 1
        return uplink_wind

