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


class Active_Period_Detector2:

    def __init__(self, channel, in_queue, out_queue):
        #####################################################################
        self.minSF = 7
        self.win_jump_factor = 2
        self.num_accum = 32
        self.lst_flag_left = 0
        self.lst_flag_right = 0
        self.nfl_flag = 0
        self.chunk_num = 0
        self.nfl = 7.5#4.7e-5#7.5#0.4

        self.cur_flag_left = 0
        self.cur_flag_right = 0
        self.lst_chunk = np.ndarray((0,), dtype=np.complex64)
        self.lst_wind = []
        self.tail_sz = (2 ** self.minSF) * UPSAMPLE_FACTOR * 88


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
        print(f"Hey I am channel: {channel}\n")
        self.channel = channel
        self.center_freq = CENTER_FREQ + channel * FREQ_OFF
        overlap = 10 * RAW_FS / BW
        # phaser = 1j * 2 * np.pi * self.channel * (FREQ_OFF / RAW_FS)
        # self.phaser = np.exp(np.arange(1, RAW_FS + (overlap * 2) + 1) * phaser)
        # del phaser
        # b, a = signal.ellip(4, 1, 100, FC / (RAW_FS / 2), 'low', analog=False)
        # self.filt = signal.dlti(b, a)
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

                # print(f'APD detected so far = {self.apd_num}\n')
                startt = time.time()
                buff = self.in_q.get()
                very_start = buff[1]
                # buff = channelize(buff[0], self.phaser, self.filt)
                buff = buff[0].astype(np.complex64)
                ##########################################################################
                buff = buff[10 * UPSAMPLE_FACTOR:-10 * UPSAMPLE_FACTOR]
                # print(len(buff))
                ##########################################################################
                if not self.config_flag:
                    # self.configNF(buff, 'low')
                    self.config_flag = True

                uplink_wind = self.Active_Sess_SFAgn(buff)
                print(f'\nFound {len(uplink_wind)} active Periods')

                if len(uplink_wind) > 0:
                    for i in range(0,len(uplink_wind)):
                        wind = uplink_wind[i]
                        print(wind)
                        print(f'{self.lst_flag_left}\t\t{self.lst_flag_right}\t{self.cur_flag_left}\t\t{self.cur_flag_right}')
                        if i == 0:
                            if i == len(uplink_wind)-1:
                                print('only 1 APD, i = 0 and i = end')
                                if ~self.cur_flag_left and self.cur_flag_right:
                                    print('do nothing')
                                    # a = 1
                                    if self.lst_flag_right and ~self.cur_flag_left and self.cur_flag_right:
                                        if len(self.lst_chunk) > 0:
                                            print('but take care of last Tail-Gaiting 21')
                                            temp_buff = np.append(self.lst_chunk[self.lst_wind[0]: len(self.lst_chunk)],
                                                                  buff[0:self.tail_sz])
                                            self.send_packet(self.lst_wind, temp_buff)
                                else:
                                    # self.send_packet(wind, buff[wind[0]:wind[1]])
                                    if self.lst_flag_right and self.cur_flag_left:
                                        if len(self.lst_chunk) > 0:
                                            print('Stitched')

                                            temp_buff = np.append(self.lst_chunk[self.lst_wind[0]:len(self.lst_chunk)],
                                                                  buff[0:wind[1]])
                                            wind[3] = wind[3] + self.lst_wind[3]
                                            wind[4] = wind[4] + self.lst_wind[4]
                                            wind[5] = wind[5] + self.lst_wind[5]
                                            wind[6] = wind[6] + self.lst_wind[6]
                                            wind[7] = wind[7] + self.lst_wind[7]
                                            wind[8] = wind[8] + self.lst_wind[8]

                                            wind[2] = (wind[2] + self.lst_wind[2]) /2
                                            # new_wind = self.lst_wind
                                            # new_wind[2] = (self.lst_wind[2] + wind[2])/2
                                            self.send_packet(wind, temp_buff)
                                    elif ~self.lst_flag_right and self.cur_flag_left:
                                        if len(self.lst_chunk) > 0:
                                            print('Tail-Gaiting 1')
                                            temp_buff = np.append(
                                                self.lst_chunk[len(self.lst_chunk) - self.tail_sz: len(self.lst_chunk)],
                                                buff[0:wind[1]])
                                            self.send_packet(wind, temp_buff)
                                    elif self.lst_flag_right and ~self.cur_flag_left:
                                        if len(self.lst_chunk) > 0:
                                            print('Tail-Gaiting 2')
                                            temp_buff = np.append(self.lst_chunk[self.lst_wind[0]: len(self.lst_chunk)],
                                                                  buff[0:self.tail_sz])
                                            self.send_packet(self.lst_wind, temp_buff)
                                            if self.cur_flag_right:
                                                print('Do nothing')
                                            else:
                                                print(' +++++  Packet Sent normally, i = 0 and i = end')
                                                self.send_packet(wind, buff[wind[0]:wind[1]])
                                    elif ~self.lst_flag_right and ~self.cur_flag_left:
                                        print('Packet Sent normally, i = 0 and i = end')
                                        self.send_packet(wind, buff[wind[0]:wind[1]])
                            else:
                                print('more than 1 APD, i = 0 and i ~= end')
                                if self.lst_flag_right and self.cur_flag_left:
                                    if len(self.lst_chunk) > 0:
                                        print('Stitched')
                                        temp_buff = np.append(self.lst_chunk[self.lst_wind[0]:len(self.lst_chunk)], buff[0:wind[1]])
                                        wind[3] = wind[3] + self.lst_wind[3]
                                        wind[4] = wind[4] + self.lst_wind[4]
                                        wind[5] = wind[5] + self.lst_wind[5]
                                        wind[6] = wind[6] + self.lst_wind[6]
                                        wind[7] = wind[7] + self.lst_wind[7]
                                        wind[8] = wind[8] + self.lst_wind[8]

                                        wind[2] = (wind[2] + self.lst_wind[2]) / 2
                                        self.send_packet(wind, temp_buff)
                                elif ~self.lst_flag_right and self.cur_flag_left:
                                    if len(self.lst_chunk) > 0:
                                        print('Tail-Gaiting 1')
                                        temp_buff = np.append(self.lst_chunk[len(self.lst_chunk) - self.tail_sz : len(self.lst_chunk)], buff[0:wind[1]])
                                        self.send_packet(wind, temp_buff)
                                elif self.lst_flag_right and ~self.cur_flag_left:
                                    if len(self.lst_chunk) > 0:
                                        print('Tail-Gaiting 2')
                                        temp_buff = np.append(self.lst_chunk[self.lst_wind[0] : len(self.lst_chunk)], buff[0:self.tail_sz])
                                        self.send_packet(self.lst_wind, temp_buff)
                                        print(' Encountered For the Very First Time, Check If it is Correct ++++  Packet Sent normally, i = 0 and i = end')
                                        self.send_packet(wind, buff[wind[0]:wind[1]])
                                elif ~self.lst_flag_right and ~self.cur_flag_left:
                                    print('Packet Sent normally, i = 0 and i ~= end')
                                    self.send_packet(wind, buff[wind[0]:wind[1]])
                        else:
                            if i == len(uplink_wind)-1:
                                print('more than 1 APD, i ~= 0 and i = end')
                                if self.cur_flag_right:
                                    print('do nothing')
                                    a = 1
                                else:
                                    print('Packet Sent normally, i ~= 0 and i = end')
                                    self.send_packet(wind, buff[wind[0]:wind[1]])
                            else:
                                print('more than 1 APD, i ~= 0 and i ~= end')
                                print('Packet Sent normally, i ~= 0 and i ~= end')
                                self.send_packet(wind, buff[wind[0]:wind[1]])

                        # elif (i == len(uplink_wind) - 1):
                        #     if ~self.cur_flag_right:
                        #         self.send_packet(wind, buff[wind[0]:wind[1]])
                        #     else:
                        #         print('****************** Buffer retained for next session ******************')
                        # else:
                        #     print('Packet Sent normally, i in middle')
                        #     self.send_packet(wind, buff[wind[0]:wind[1]])
                    self.lst_wind = wind
                else:
                    if self.lst_flag_right:
                        print(f'This APD was empty but take care of last Tail-Gaiting 2 --- {self.lst_flag_right}')
                        temp_buff = np.append(self.lst_chunk[self.lst_wind[0]: len(self.lst_chunk)],
                                              buff[0:self.tail_sz])
                        self.send_packet(self.lst_wind, temp_buff)
                    self.lst_flag_left = 0
                    self.lst_flag_right = 0
                    self.cur_flag_right = 0
                    self.cur_flag_left = 0
                self.lst_chunk = buff
            else:
                if time.time() - startt > 25:
                    return
                else:
                    time.sleep(0.25)


    def Active_Sess_SFAgn(self, x_1):
        upsampling_factor = UPSAMPLE_FACTOR
        windsz = 2 ** self.minSF
        win_jump = int(np.floor(windsz * upsampling_factor / self.win_jump_factor))

        peak_gain = []
        uplink_wind = []
        n = []
        p = []
        last_wind = 0
        num_accum = 32
        # front_buf = 58 * self.win_jump_factor
        # back_buf = 78 * self.win_jump_factor
        front_buf = 100 * self.win_jump_factor
        back_buf = 100 * self.win_jump_factor
        mov_thresh_wind = int(np.floor((1000 * self.win_jump_factor) / 32))
        mov_thresh_rec = []
        # print(f"nfl Val = {self.nfl}")
        upLim = self.nfl  # db
        # print(upLim)
        # upLim = 0.4  # db
        c = 1
        t_n = 0
        t_p = 0
        x = []
        lst_ind = 0
        ctr = 0
        dis = 0
        ind_arr = []
        big_ind_arr = []
        t_u = 4.5  # 1.06
        t_v = 4.5  # 1.2
        idx = np.concatenate([np.array(range(0, int(windsz / 2))), np.array(
            range(int(windsz / 2 + (upsampling_factor - 1) * windsz), int((upsampling_factor) * windsz)))])

        if len(self.lst_chunk) != 0:
            x_1 = np.append(self.lst_chunk[len(self.lst_chunk) - 16384: len(self.lst_chunk)],
                            x_1)

        x_1_len = len(x_1)

        # for i in range(1, int(np.floor(x_1_len / win_jump) - (win_jump_factor * (win_jump_factor - 1)))):
        # print(f"Heyyyyyyyyyyyyyyyyyy!! : {x_1_len / win_jump}")
        # for i in range(1, int(np.floor(x_1_len / win_jump))):
        for i in range(1, int(np.floor(x_1_len / win_jump) - (self.win_jump_factor * (self.win_jump_factor - 1)))):
            wind_fft = np.abs(np.fft.fft(np.multiply(x_1[(i - 1) * win_jump: (i - 1) * win_jump + (windsz * upsampling_factor)], np.conj(x_1[(i - 1) * win_jump + (windsz * upsampling_factor): (i - 1) * win_jump + (2 * windsz * upsampling_factor)]))))
            w_f = wind_fft[idx]
            ind = np.argmax(w_f)
            id = np.setdiff1d(range(0, len(w_f)), ind)
            n_f = np.mean(w_f[id])

            noise_floor = np.mean(wind_fft)
            fft_peak = max(wind_fft)

            # if len(peak_gain) < 200:
            #     upLim = t_u * np.mean(peak_gain)

            if np.mod(c, num_accum) == 0:
                n.append(t_n)
                p.append(t_p)
                peak_gain.append(t_p)
                x.append(i)

######################################################################################################################################
                # if ((i + 1) / num_accum) > mov_thresh_wind:
                #     mov_thresh = t_v * np.mean(peak_gain[len(peak_gain) - mov_thresh_wind:len(peak_gain)])
                #     if mov_thresh > upLim:
                #         mov_thresh = upLim
                # else:
                #     mov_thresh = t_v * np.mean(peak_gain)
                #     if mov_thresh > upLim:
                #         mov_thresh = upLim
######################################################################################################################################
                mov_thresh = upLim
######################################################################################################################################
                mov_thresh_rec.append(mov_thresh)

                ## Add alternative to energy thresholding
                # if len(ind_arr) > 0:
                #     D_1 = 0
                #     D_65 = 0
                #     D_97 = 0
                #     D_113 = 0
                #     D_121 = 0
                #     D_125 = 0
                #     # temp = np.array(big_ind_arr).reshape(1, -1)
                #     for o in ind_arr:
                #         if o == 0:
                #             D_1 += 1
                #         elif o == 64:
                #             D_65 += 1
                #         elif o == 96:
                #             D_97 += 1
                #         elif o == 112:
                #             D_113 += 1
                #         elif o == 120:
                #             D_121 += 1
                #         elif o == 124:
                #             D_125 += 1
                # num = 10
                # if D_1 >= num or D_65 >= num or D_97 >= num or D_113 >= num or D_121 >= num or D_125 >= num:
                #########################################

                if peak_gain[-1] >= mov_thresh:
                    big_ind_arr.append(ind_arr)
                    if i - num_accum >= last_wind:
                        if i - back_buf < 1:
                            # print('Touched this Corner Case\n')
                            uplink_wind.append([1, i + front_buf, 0, 0, 0, 0, 0, 0, 0])
                            # uplink_wind.append([i - back_buf, i + front_buf, 0, 0, 0, 0, 0, 0, 0])
                            big_ind_arr = []
                            big_ind_arr.append(ind_arr)
                        else:
                            uplink_wind.append([i - back_buf, i + front_buf, 0, 0, 0, 0, 0, 0, 0])
                            big_ind_arr = []
                            big_ind_arr.append(ind_arr)
                        last_wind = uplink_wind[-1][1]
                        if len(big_ind_arr) > 0:
                            D_1 = 0
                            D_65 = 0
                            D_97 = 0
                            D_113 = 0
                            D_121 = 0
                            D_125 = 0
                            temp = np.array(big_ind_arr).reshape(1, -1)
                            for o in temp[0]:
                                if o == 0:
                                    D_1 += 1
                                elif o == 64:
                                    D_65 += 1
                                elif o == 96:
                                    D_97 += 1
                                elif o == 112:
                                    D_113 += 1
                                elif o == 120:
                                    D_121 += 1
                                elif o == 124:
                                    D_125 += 1
                            uplink_wind[-1][2:len(uplink_wind[-1])] = (st.mode(temp[0]), D_1, D_65, D_97, D_113, D_121, D_125)
                    elif i - num_accum < last_wind:
                        uplink_wind[-1][1] = i + front_buf
                        last_wind = uplink_wind[-1][1]
                        if len(big_ind_arr) > 0:
                            D_1 = 0
                            D_65 = 0
                            D_97 = 0
                            D_113 = 0
                            D_121 = 0
                            D_125 = 0
                            temp = np.array(big_ind_arr).reshape(1, -1)
                            for o in temp[0]:
                                if o == 0:
                                    D_1 += 1
                                elif o == 64:
                                    D_65 += 1
                                elif o == 96:
                                    D_97 += 1
                                elif o == 112:
                                    D_113 += 1
                                elif o == 120:
                                    D_121 += 1
                                elif o == 124:
                                    D_125 += 1
                            uplink_wind[-1][2:len(uplink_wind[-1])] = (st.mode(temp[0]), D_1, D_65, D_97, D_113, D_121, D_125)
                t_n = 0
                t_p = 0
            if np.mod(c, num_accum) == 0:
                ind_arr = []
            else:
                ind_arr.append(ind)
            c += 1
            t_n = t_n + noise_floor
            t_p = t_p + fft_peak

            lst_ind = ind
        if len(uplink_wind) > 0:
            for i in range(0, len(uplink_wind)):
                uplink_wind[i][0:2] = np.multiply(uplink_wind[i][0:2], [win_jump, win_jump])
            temp = []
            for i in range(0, len(uplink_wind)):
                if ((uplink_wind[i][1] - uplink_wind[i][0]) / (windsz * upsampling_factor)) > 30:
                    temp.append(uplink_wind[i])
            uplink_wind = temp

        if not self.nfl_flag:
            self.chunk_num += 1

        if not self.nfl_flag and self.chunk_num == 2:
            # print(f"{max(peak_gain)}\t{self.nfl_flag}")
            self.nfl = max(peak_gain) * 1.09
            # self.nfl = max(peak_gain) * 6
            # self.nfl = np.mean(peak_gain)
            print(f"Your threshold is : {self.nfl}\n")
            # self.nfl = max(peak_gain) * 1
            self.nfl_flag = 1

        self.lst_flag_right = self.cur_flag_right
        self.lst_flag_left = self.cur_flag_left
        if len(uplink_wind) > 0:
            if uplink_wind[0][0] == win_jump:
                self.cur_flag_left = 1
            else:
                self.cur_flag_left = 0

            if (x_1_len - uplink_wind[-1][1]) < 0:
                self.cur_flag_right = 1
            else:
                self.cur_flag_right = 0
                # self.chunk = x_1[uplink_wind[-1][0] : x_1_len]
        # print(f"Maximum of current peak gain is = {max(peak_gain)}")
        return uplink_wind

