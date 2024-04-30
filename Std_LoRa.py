from Demodulators.Demod_Interface import Demod_Interface
import numpy as np
import math
from .decode import lora_decoder
from .DC_gen import DC_gen
from .sym_to_data_ang import sym_to_data_ang
from .dnsamp_buff import dnsamp_buff
import matplotlib.pyplot as plt
from .stft_v1 import stft_v1


class Std_LoRa(Demod_Interface):
    def __init__(self, num_preamble, num_sync, num_DC, num_data_sym, check_crc):
        self.num_preamble = num_preamble
        self.num_sync = num_sync
        self.num_DC = num_DC
        self.num_data_sym = num_data_sym
        self.check_crc = check_crc

        self.pkt_starts = []
        self.demod_sym = []
        self.cnt = 0

    def Evaluate(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        [pkt_start, demod_sym, fin_data] = self.demodulate(Rx, SF, BW, FS, PRINT)
        # return [pkt_start, demod_sym, self.decode(SF, PRINT)]
        return [pkt_start, demod_sym, fin_data]

    def Evaluate2(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        self.demodulate2(Rx, SF, BW, FS)
        return self.decode(SF, PRINT)


    def EvaluateRLO(self, Rx, SF: int, BW: int, FS: int, PRINT: False):
        self.demodulate(Rx, SF, BW, FS)
        return self.decodeRLO(SF, PRINT)

    def decode(self, SF, PRINT):
        decoded_packets = 0
        final_data = []

        if len(self.demod_sym) > 0 and len(self.demod_sym[0]) > 0:
            for i, syms in enumerate(self.demod_sym):
                if SF <= 10:
                #     # dem = mod(dem - 2, 2 ^ SF)
                    message = lora_decoder(np.mod(np.add(syms, -1), (2 ** SF)), SF, self.check_crc)
                else:
                #     # dem = mod(dem - 1, 2 ^ SF)
                    message = lora_decoder(np.mod(np.add(syms, 0), (2 ** SF)), SF, self.check_crc)
                # message = lora_decoder(np.mod(np.add(syms, -1), (2**SF)), SF, self.check_crc)
                if message is not None:
                    decoded_packets += 1
                    final_data.append((self.pkt_starts[i], self.demod_sym[i], message))
            final_data = self.remove_sim(final_data, 10 * (2 ** SF))

        self.demod_sym = []
        self.pkt_starts = []
        if PRINT:
            for d in final_data:
                print(d[2].tolist())
                #print(''.join([chr(int(c)) for c in d[2][7:]]))

        return final_data

    def demodulate(self, Rx, SF: int, BW: int, FS: int, PRINT: True) -> list:

        pkt_starts = self.pkt_detection2(Rx, SF, BW, FS, self.num_preamble)
        # pkt_starts = self.pkt_detection(Rx, SF, BW, FS, self.num_preamble)
        # print(self.pkt_starts)
        fin_data = []
        shift = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, 6, -6]
        # for i in range(-int(FS/BW) , int(FS/BW) + 1):
        for i in shift:
            pkt_st = pkt_starts + i
            # print("iterate till decoding Successfull\n")
            self.demod_sym = self.lora_demod(Rx, SF, BW, FS, self.num_preamble, self.num_sync, self.num_DC,
                                             self.num_data_sym, pkt_st)
            self.pkt_starts = pkt_starts + i
            fin_data = self.decode(SF, True)
            self.pkt_starts = pkt_starts + i
            if len(fin_data) != 0:
                break
        return [pkt_st, self.demod_sym, fin_data]

    def demodulate2(self, Rx, SF: int, BW: int, FS: int) -> list:
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        self.pkt_starts = self.pkt_detection(Rx, SF, BW, FS, self.num_preamble)
        Rx = Rx[int(self.pkt_starts - (2*N*upsampling_factor) - 1):len(Rx)]
        temp_buff = Rx[:(len(Rx) // upsampling_factor) * upsampling_factor]

        Rx_Buff_dnsamp = []
        for i in range(upsampling_factor):
            Rx_Buff_dnsamp.append(temp_buff[i::upsampling_factor])
        Rx_Buff_dnsamp = np.array(Rx_Buff_dnsamp)
        Upchirp_ind = []
        Upchirp_ind.append(np.arange(2*N, ((self.num_preamble + 1) * N) + 1, N))
        print(Upchirp_ind)
        [Data_freq_off, Peak, Upchirp_ind, FFO] = dnsamp_buff(Rx_Buff_dnsamp, Upchirp_ind, SF)
        # if Upchirp_ind.shape[0] == 0:
        #     print('nothing found\n')
        pkt_starts = []
        for i in range(len(Upchirp_ind)):
            pkt_starts.append(Upchirp_ind[i][0])
        self.demod_sym = self.lora_demod2(Data_freq_off, SF, BW, BW, self.num_preamble, self.num_sync, self.num_DC,
                                         self.num_data_sym, pkt_starts)
        return [0, 0]


    def pkt_detection(self, Rx_Buffer, SF, BW, FS, num_preamble):
        # print(f"Entered Packet Detection Block {self.cnt}\n")
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        # num_preamble -= 1  # need to find n-1 total chirps (later filtered by sync word)

        # DC_upsamp = DC_gen(SF, BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, upsampling_factor))

        # Preamble Detection
        # temp_wind_fft = np.array([])
        ind_buff = np.array([])
        count = 0
        Pream_ind = np.array([], int)
        lim = int(np.floor(len(Rx_Buffer)/(upsampling_factor*N)))
        temp_wind_fft_idx = np.concatenate(
            [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])
        for i in range(1,lim+1):
            temp_wind_fft = abs(
                np.fft.fft(Rx_Buffer[((i-1) * upsampling_factor * N):
                                     ((i) * upsampling_factor * N) ] * DC_upsamp , axis=0))
            temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
            # plt.plot(temp_wind_fft)
            # plt.show()
            b = np.argmax(temp_wind_fft)
            if len(ind_buff) >= num_preamble:
                # ind_buff = ind_buff[-(num_preamble - 2):]
                ind_buff = ind_buff[len(ind_buff) - (num_preamble-1):len(ind_buff)]
                ind_buff = np.append(ind_buff, b)
            else:
                ind_buff = np.append(ind_buff, b)

            # print(f"{ind_buff}\n")
            if ((sum(abs(np.diff(np.mod(ind_buff, N + 1)))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff, N    )))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff, N - 1)))) <= (num_preamble + 4)) and
                    ind_buff.size >= num_preamble):
                # if np.sum(np.abs(Rx_Buffer[(i * upsampling_factor * N) + offset:((i + 1) * upsampling_factor * N) + offset])) != 0:
                    count = count + 1
                    # Pream_ind = np.append(Pream_ind, ((i-1) - (num_preamble - 1)) * (upsampling_factor * N) + 1)
                    Pream_ind = np.append(Pream_ind, ((i-1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 - (upsampling_factor * round(np.mean(ind_buff))))
                    Pream_ind = np.append(Pream_ind, ((i-1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 + ((N*upsampling_factor) - (upsampling_factor * round(np.mean(ind_buff)))))
        # if len(Pream_ind) == 1:
        #     np.append(Pream_ind, Pream_ind[0] + (N*upsampling_factor))
        #     np.append(Pream_ind, Pream_ind[0] - (N * upsampling_factor))
        # if SF == 7:
        #     print('hwere!')
        # print(f'{Pream_ind}\n')

        # Synchronization
        Pream_ind.sort()
        # print(f"Initial # of Preams = {len(Pream_ind)}\n")
        # shifts = np.arange(-N / 2, N / 2, dtype=int) * upsampling_factor
        # shifts = np.arange((-N/2) * upsampling_factor, (N/2) * upsampling_factor, dtype=int)
        # shifts = np.arange(-20 * upsampling_factor, 20 * upsampling_factor, dtype=int)
        shifts = np.arange(-5 * upsampling_factor, 5 * upsampling_factor, dtype=int)
        new_pream = []
        for i in range(len(Pream_ind)):
            ind_arr = np.array([])
            amp_arr = np.array([])
            for j in shifts:
                if Pream_ind[i] + j < 1:
                    ind_arr = np.append(ind_arr, -1)
                    amp_arr = np.append(amp_arr, -1)
                    continue

                temp_wind_fft = abs(
                    np.fft.fft(Rx_Buffer[(Pream_ind[i] + j - 1): (Pream_ind[i] + j + (upsampling_factor * N) - 1)] * DC_upsamp,
                               upsampling_factor * N, axis=0))
                temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
                b = temp_wind_fft.argmax()
                a = max(temp_wind_fft)
                amp_arr = np.append(amp_arr, a)
                ind_arr = np.append(ind_arr, b)

            temp_ind = (ind_arr == 0).nonzero()
            temp_shift = np.array([])
            temp_amp = np.array([])
            if len(temp_ind[0]) != 0:
                for k in temp_ind[0]:
                    temp_shift = np.append(temp_shift, shifts[k])
                    temp_amp = np.append(temp_amp, amp_arr[k])
                c = temp_amp.argmax()
                Pream_ind[i] = Pream_ind[i] + temp_shift[c]

############################################################################################################################
        # temp = np.array([], int)
        # for i in range(len(Pream_ind)):
        #     Pre_fft1 = abs(np.fft.fft(Rx_Buffer[Pream_ind[i]-1:Pream_ind[i]-1+(upsampling_factor*N)] * DC_upsamp, axis=0))
        #     Pre_fft1 = Pre_fft1[temp_wind_fft_idx]
        #
        #     Pre_fft2 = abs(
        #         np.fft.fft(Rx_Buffer[Pream_ind[i] + (upsampling_factor*N)-1:Pream_ind[i] - 1 + (2*upsampling_factor * N)] * DC_upsamp, axis=0))
        #     Pre_fft2 = Pre_fft2[temp_wind_fft_idx]
        #
        #     c1 = np.argmax(Pre_fft1)
        #     c2 = np.argmax(Pre_fft2)
        #     if (c1<=2 or c1 >=N-3) and (c2<=2 or c2>=N-3):
        #         temp = np.append(temp, Pream_ind[i])
        # Pream_ind = temp

############################################################################################################################
        # SYNC WORD DETECTION
        count = 0
        Pream_ind = list(set(Pream_ind))
        Pream_ind.sort()
        Preamble_ind = np.array([], int)
        for i in range(len(Pream_ind)):
            if ((Pream_ind[i] + (9*upsampling_factor * N) - 1 > Rx_Buffer.size) or (
                    Pream_ind[i] + (10*upsampling_factor * N)-1 > Rx_Buffer.size)):
                continue

            sync_wind1 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (8 * upsampling_factor * N)-1): (
                    Pream_ind[i] + (9 * upsampling_factor * N)-1)] * DC_upsamp, axis=0))
            sync_wind2 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (9 * upsampling_factor * N)-1): (
                    Pream_ind[i] + (10 * upsampling_factor * N)-1)] * DC_upsamp, axis=0))
            sync_wind1 = sync_wind1[temp_wind_fft_idx]
            sync_wind2 = sync_wind2[temp_wind_fft_idx]

            s1 = sync_wind1.argmax()
            s2 = sync_wind2.argmax()
            if s1 >= 7 and s1 <= 9 and s2 >= 15 and s2 <= 17:
                count = count + 1
                Preamble_ind = np.append(Preamble_ind, Pream_ind[i])

        return Preamble_ind

    def pkt_detection2(self, Rx_Buffer, SF, BW, FS, num_preamble):
        # print(f"Entered Packet Detection Block {self.cnt}\n")
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        # if N == 512:
        #     print("Pakra gaya\n")
        DC_upsamp = np.conj(sym_to_data_ang([1], N, upsampling_factor))

        # Preamble Detection
        # temp_wind_fft = np.array([])
        ind_buff = np.array([])
        count = 0
        Pream_ind = np.array([], int)
        lim = int(np.floor(len(Rx_Buffer) / (upsampling_factor * N)))
        temp_wind_fft_idx = np.concatenate(
            [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])
        for i in range(1, lim + 1):
            temp_wind_fft = abs(
                np.fft.fft(Rx_Buffer[((i - 1) * upsampling_factor * N):
                                     ((i) * upsampling_factor * N)] * DC_upsamp, axis=0))
            temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
            # plt.plot(temp_wind_fft)
            # plt.show()
            b = np.argmax(temp_wind_fft)
            if len(ind_buff) >= num_preamble:
                # ind_buff = ind_buff[-(num_preamble - 2):]
                ind_buff = ind_buff[len(ind_buff) - (num_preamble - 1):len(ind_buff)]
                ind_buff = np.append(ind_buff, b)
            else:
                ind_buff = np.append(ind_buff, b)

            # print(f"{ind_buff}\n")
            if ((sum(abs(np.diff(np.mod(ind_buff[2:], N + 1)))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff[2:], N)))) <= (num_preamble + 4) or
                 sum(abs(np.diff(np.mod(ind_buff[2:], N - 1)))) <= (num_preamble + 4)) and
                    ind_buff.size >= num_preamble):
            # if ((sum(abs(np.diff(np.mod(ind_buff[1:], N + 1)))) <= num_preamble)  and
            #         ind_buff.size >= num_preamble):
                # if np.sum(np.abs(Rx_Buffer[(i * upsampling_factor * N) + offset:((i + 1) * upsampling_factor * N) + offset])) != 0:
                count = count + 1
                # Pream_ind = np.append(Pream_ind, ((i-1) - (num_preamble - 1)) * (upsampling_factor * N) + 1)
                Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 - (
                            upsampling_factor * (round(np.mean(ind_buff[2:])) )))
                Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 + (
                        (N * upsampling_factor) - (upsampling_factor * (round(np.mean(ind_buff[2:]))))))

                Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble + 1)) * (upsampling_factor * N) + 1 - (
                        upsampling_factor * (round(np.mean(ind_buff[2:])))))
                Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble + 1)) * (upsampling_factor * N) + 1 + (
                            (N * upsampling_factor) - (upsampling_factor * (round(np.mean(ind_buff[2:])) ))))

                # Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 - (
                #         upsampling_factor * (round(np.mean(ind_buff)))))
                # Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble - 1)) * (upsampling_factor * N) + 1 + (
                #         upsampling_factor * (round(np.mean(ind_buff)))))
                #
                # Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble + 1)) * (upsampling_factor * N) + 1 - (
                #         upsampling_factor * (round(np.mean(ind_buff)))))
                # Pream_ind = np.append(Pream_ind, ((i - 1) - (num_preamble + 1)) * (upsampling_factor * N) + 1 + (
                #         upsampling_factor * (round(np.mean(ind_buff)))))
        # if len(Pream_ind) == 1:
        #     np.append(Pream_ind, Pream_ind[0] + (N*upsampling_factor))
        #     np.append(Pream_ind, Pream_ind[0] - (N * upsampling_factor))
        # if SF == 7:
        #     print('hwere!')
        # print(f'Init: {Pream_ind}\n')

        # Synchronization
        Pream_ind.sort()
        # print(f"Initial # of Preams = {len(Pream_ind)}\n")
        # shifts = np.arange(-N / 2, N / 2, dtype=int) * upsampling_factor
        # shifts = np.arange((-N/2) * upsampling_factor, (N/2) * upsampling_factor, dtype=int)
        shifts = np.arange(-20 * upsampling_factor, 20 * upsampling_factor, dtype=int)
        # shifts = np.arange(-5 * upsampling_factor, 5 * upsampling_factor, dtype=int)
        new_pream = []
        for i in range(len(Pream_ind)):
            ind_arr = np.array([])
            amp_arr = np.array([])
            for j in shifts:
                if Pream_ind[i] + j < 1:
                    ind_arr = np.append(ind_arr, -1)
                    amp_arr = np.append(amp_arr, -1)
                    continue

                temp_wind_fft = abs(
                    np.fft.fft(Rx_Buffer[(Pream_ind[i] + ((num_preamble-1)*upsampling_factor*N) + j - 1): (
                                Pream_ind[i] + ((num_preamble-1)*upsampling_factor*N) + j + (upsampling_factor * N) - 1)] * DC_upsamp,
                               upsampling_factor * N, axis=0))
                temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
                b = temp_wind_fft.argmax()
                a = max(temp_wind_fft)
                amp_arr = np.append(amp_arr, a)
                ind_arr = np.append(ind_arr, b)

            temp_ind = (ind_arr == 0).nonzero()
            temp_shift = np.array([])
            temp_amp = np.array([])
            if len(temp_ind[0]) != 0:
                for k in temp_ind[0]:
                    temp_shift = np.append(temp_shift, shifts[k])
                    temp_amp = np.append(temp_amp, amp_arr[k])
                c = temp_amp.argmax()
                Pream_ind[i] = Pream_ind[i] + temp_shift[c]
        # print(f'After Fine Sync: {Pream_ind}\n')
        ############################################################################################################################
        # temp = np.array([], int)
        # for i in range(len(Pream_ind)):
        #     # Pre_fft1 = abs(np.fft.fft(Rx_Buffer[Pream_ind[i]-1:Pream_ind[i]-1+(upsampling_factor*N)] * DC_upsamp, axis=0))
        #     Pre_fft1 = abs(
        #         np.fft.fft(Rx_Buffer[Pream_ind[i] + (6*upsampling_factor * N) - 1:Pream_ind[i] - 1 + (
        #                     7 * upsampling_factor * N)] * DC_upsamp, axis=0))
        #     Pre_fft1 = Pre_fft1[temp_wind_fft_idx]
        #
        #     Pre_fft2 = abs(
        #         np.fft.fft(Rx_Buffer[Pream_ind[i] + (7*upsampling_factor*N)-1:Pream_ind[i] - 1 + (8*upsampling_factor * N)] * DC_upsamp, axis=0))
        #     Pre_fft2 = Pre_fft2[temp_wind_fft_idx]
        #
        #     c1 = np.argmax(Pre_fft1)
        #     c2 = np.argmax(Pre_fft2)
        #     if (c1<=2 or c1 >=N-3) and (c2<=2 or c2>=N-3):
        #         temp = np.append(temp, Pream_ind[i])
        # Pream_ind = temp

        ############################################################################################################################
        # SYNC WORD DETECTION
        count = 0
        Pream_ind = list(set(Pream_ind))
        Pream_ind.sort()
        Preamble_ind = np.array([], int)
        for i in range(len(Pream_ind)):
            if ((Pream_ind[i] + (9 * upsampling_factor * N) - 1 > Rx_Buffer.size) or (
                    Pream_ind[i] + (10 * upsampling_factor * N) - 1 > Rx_Buffer.size)):
                continue

            sync_wind1 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (8 * upsampling_factor * N) - 1): (
                    Pream_ind[i] + (9 * upsampling_factor * N) - 1)] * DC_upsamp, axis=0))
            sync_wind2 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + (9 * upsampling_factor * N) - 1): (
                    Pream_ind[i] + (10 * upsampling_factor * N) - 1)] * DC_upsamp, axis=0))
            sync_wind1 = sync_wind1[temp_wind_fft_idx]
            sync_wind2 = sync_wind2[temp_wind_fft_idx]

            s1 = sync_wind1.argmax()
            s2 = sync_wind2.argmax()
            # print(f'SYNC Words: {s1} & {s2}\n')
            if s1 >= 7 and s1 <= 9 and s2 >= 15 and s2 <= 17:
                count = count + 1
                Preamble_ind = np.append(Preamble_ind, Pream_ind[i])
        # print(f'After SYNC Word: {Preamble_ind}\n')
        return Preamble_ind
    # def pkt_detection(self, Rx_Buffer, SF, BW, FS, num_preamble):
    #     upsampling_factor = int(FS / BW)
    #     N = int(2 ** SF)
    #     num_preamble -= 1  # need to find n-1 total chirps (later filtered by sync word)
    #
    #     DC_upsamp = DC_gen(SF, BW, FS)
    #
    #     # Preamble Detection
    #     ind_buff = np.array([])
    #     count = 0
    #     Pream_ind = np.array([], int)
    #
    #     loop = 0
    #     for off in range(3):
    #         offset = off * upsampling_factor * N // 3
    #         loop = Rx_Buffer.size // (upsampling_factor * N) - 1
    #         for i in range(loop):
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(i * upsampling_factor * N) + offset:
    #                                      ((i + 1) * upsampling_factor * N) + offset] * DC_upsamp, axis=0))
    #             temp_wind_fft_idx = np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])
    #             temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
    #             b = np.argmax(temp_wind_fft)
    #             if len(ind_buff) >= num_preamble:
    #                 ind_buff = ind_buff[-(num_preamble - 1):]
    #                 ind_buff = np.append(ind_buff, b)
    #             else:
    #                 ind_buff = np.append(ind_buff, b)
    #
    #             if ((sum(abs(np.diff(np.mod(ind_buff, N + 1)))) <= (num_preamble + 4) or
    #                  sum(abs(np.diff(np.mod(ind_buff, N)))) <= (num_preamble + 4) or
    #                  sum(abs(np.diff(np.mod(ind_buff, N - 1)))) <= (num_preamble + 4)) and
    #                     ind_buff.size >= num_preamble - 1):
    #                 if np.sum(np.abs(Rx_Buffer[(i * upsampling_factor * N)
    #                                            + offset:((i + 1) * upsampling_factor * N) + offset])) != 0:
    #                     count = count + 1
    #                     Pream_ind = np.append(Pream_ind, (i - (num_preamble - 1)) * (upsampling_factor * N) + offset)
    #
    #     # print('Found ', count, ' Preambles')
    #     if count >= (loop * 0.70):
    #         Preamble_ind = np.array([], int)
    #         return Preamble_ind
    #
    #     # Synchronization
    #     Pream_ind.sort()
    #     shifts = np.arange(-N / 2, N / 2, dtype=int) * upsampling_factor
    #     new_pream = []
    #     for i in range(len(Pream_ind)):
    #         ind_arr = np.array([])
    #
    #         for j in shifts:
    #             if Pream_ind[i] + j < 0:
    #                 ind_arr = np.append(ind_arr, -1)
    #                 continue
    #
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(Pream_ind[i] + j): (Pream_ind[i] + j + upsampling_factor * N)] * DC_upsamp,
    #                            upsampling_factor * N, axis=0))
    #             temp_wind_fft = temp_wind_fft[np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #             b = temp_wind_fft.argmax()
    #             ind_arr = np.append(ind_arr, b)
    #
    #         nz_arr = (ind_arr == 0).nonzero()
    #         if len(nz_arr) != 0:
    #             new_pream = new_pream + (shifts[nz_arr] + Pream_ind[i]).tolist()
    #
    #     # sub-sample sync
    #     Pream_ind = new_pream
    #     shifts = np.arange(-upsampling_factor, upsampling_factor + 1, dtype=int)
    #     for i in range(len(Pream_ind)):
    #         amp_arr = []
    #
    #         for j in shifts:
    #             if Pream_ind[i] + j < 0:
    #                 amp_arr.append([-1, j])
    #                 continue
    #
    #             temp_wind_fft = abs(
    #                 np.fft.fft(Rx_Buffer[(Pream_ind[i] + j): (Pream_ind[i] + j + upsampling_factor * N)] * DC_upsamp,
    #                            upsampling_factor * N, axis=0))
    #             temp_wind_fft = temp_wind_fft[np.concatenate(
    #                 [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #
    #             b = temp_wind_fft.argmax()
    #             if b == 0:
    #                 a = temp_wind_fft[0]
    #                 amp_arr.append([a, j])
    #
    #         if len(amp_arr) != 0:
    #             Pream_ind[i] = Pream_ind[i] + max(amp_arr)[1]
    #
    #     # SYNC WORD DETECTION
    #     count = 0
    #     Pream_ind = list(set(Pream_ind))
    #     Pream_ind.sort()
    #     Preamble_ind = np.array([], int)
    #     for i in range(len(Pream_ind)):
    #         if ((Pream_ind[i] + 9 * (upsampling_factor * N) > Rx_Buffer.size) or (
    #                 Pream_ind[i] + 10 * (upsampling_factor * N) > Rx_Buffer.size)):
    #             continue
    #
    #         sync_wind1 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + 8 * upsampling_factor * N): (
    #                 Pream_ind[i] + 9 * upsampling_factor * N)] * DC_upsamp, axis=0))
    #         sync_wind2 = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + 9 * upsampling_factor * N): (
    #                 Pream_ind[i] + 10 * upsampling_factor * N)] * DC_upsamp, axis=0))
    #         sync_wind1 = sync_wind1[np.concatenate(
    #             [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #         sync_wind2 = sync_wind2[np.concatenate(
    #             [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
    #
    #         s1 = sync_wind1.argmax()
    #         s2 = sync_wind2.argmax()
    #         if s1 >= 7 and s1 <= 9 and s2 >= 15 and s2 <= 17:
    #             count = count + 1
    #             Preamble_ind = np.append(Preamble_ind, Pream_ind[i])
    #
    #     return Preamble_ind

    def lora_demod(self, Rx_Buffer, SF, BW, FS, num_preamble, num_sync, num_DC, num_data_sym, Preamble_ind):
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        fact = 1
        demod_sym = np.array([], int, ndmin=2)

        # DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, upsampling_factor))
        Data_frame_st = Preamble_ind + int((num_preamble + num_sync + num_DC) * N * upsampling_factor)

        for j in range(Preamble_ind.shape[0]):
            demod = np.empty((1, num_data_sym), int)
            for i in range(num_data_sym):
                if Data_frame_st[j] + (i + 1) * upsampling_factor * N > Rx_Buffer.size:
                    demod[:, i] = -1
                    continue

                temp_fft = abs(np.fft.fft(Rx_Buffer[(Data_frame_st[j] + (i * upsampling_factor * N)-1): (
                        Data_frame_st[j] + ((i + 1) * upsampling_factor * N))-1] * DC_upsamp, n=fact*upsampling_factor*N , axis=0))
                # temp_fft = temp_fft[np.concatenate(
                #     [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
                temp_fft = temp_fft[np.concatenate(
                    [np.arange(0,fact * (N // 2)), np.arange((fact*(N // 2)) + (upsampling_factor - 1) * fact * N, fact * upsampling_factor * N)])]

                # plt.plot(temp_fft)
                # plt.show()

                b = temp_fft.argmax()
                demod[:, i] = round(b/fact)

            if j == 0:
                demod_sym = demod
            else:
                demod_sym = np.vstack((demod_sym, demod))

        demod_sym = demod_sym % N
        # print(f'{demod_sym}\n')
        return demod_sym

    def lora_demod2(self, Rx_Buffer, SF, BW, FS, num_preamble, num_sync, num_DC, num_data_sym, Preamble_ind):
        Rx_Buffer = Rx_Buffer[0]
        upsampling_factor = int(FS / BW)
        N = int(2 ** SF)
        fact = 1
        demod_sym = np.array([], int, ndmin=2)

        # DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
        DC_upsamp = np.conj(sym_to_data_ang([1], N, 0))
        DC_upsamp = np.reshape(DC_upsamp, (1, N))
        Data_frame_st = Preamble_ind[0] + int((num_preamble + num_sync + num_DC) * N * upsampling_factor)

        for j in range(len(Preamble_ind)):
            demod = np.empty((1, num_data_sym), int)
            for i in range(num_data_sym):
                if Data_frame_st + (i + 1) * upsampling_factor * N > Rx_Buffer.size:
                    demod[:, i] = -1
                    continue

                temp_fft = abs(np.fft.fft(Rx_Buffer[(Data_frame_st + (i * upsampling_factor * N)-1): (
                        Data_frame_st + ((i + 1) * upsampling_factor * N))-1] * DC_upsamp, n=fact*upsampling_factor*N , axis=0))
                # temp_fft = temp_fft[np.concatenate(
                #     [np.arange(0, N // 2), np.arange(N // 2 + (upsampling_factor - 1) * N, upsampling_factor * N)])]
                temp_fft = temp_fft[np.concatenate(
                    [np.arange(0,fact * (N // 2)), np.arange((fact*(N // 2)) + (upsampling_factor - 1) * fact * N, fact * upsampling_factor * N)])]

                b = temp_fft.argmax()
                demod[:, i] = round(b/fact)

            if j == 0:
                demod_sym = demod
            else:
                demod_sym = np.vstack((demod_sym, demod))

        demod_sym = demod_sym % N
        return demod_sym

    def remove_sim(self, vals, dist):
        if len(vals) <= 1:
            return vals
        ret = []
        curr_index = vals[0][0]
        ret.append(vals[0])
        for i, _ in enumerate(vals):
            if i == 0:
                continue
            else:
                if vals[i][0] - curr_index > dist:
                    ret.append(vals[i])
                    curr_index = vals[i][0]
        return ret

    def decodeRLO(self, SF, PRINT):
        decoded_packets = 0
        final_data = []
        message = []
        if len(self.demod_sym) > 0 and len(self.demod_sym[0]) > 0:
            for i, syms in enumerate(self.demod_sym):
                # print(f'syms = {i}, {syms}')
                message = lora_decoder(np.mod(syms, (2**SF)), SF, self.check_crc)
                if message is not None:
                    decoded_packets += 1
                    # final_data.append((self.pkt_starts[i], self.demod_sym[i], message))
                    final_data.append((self.pkt_starts[0], self.demod_sym[0], message))

            # print(f'Before = {final_data}')
            # final_data = self.remove_sim(final_data, 10 * (2 ** SF))
            # print(f'After = {final_data}')
        self.demod_sym = []
        self.pkt_starts = []
        if PRINT:
            for d in final_data:
                print(d[2].tolist())
                #print(''.join([chr(int(c)) for c in d[2][7:]]))

        return message    # def correlate(self, Rx, SF: int, BW: int, FS: int):
    #     upsampling_factor = int(FS / BW)
    #     N = int(2 ** SF)
    #     # demod_sym = np.array([], int, ndmin=2)
    #
    #     DC_upsamp = DC_gen(int(math.log2(N)), BW, FS)
    #
    #     np.correlate(Rx, "full")
    #     self.demodulate(Rx, SF, BW, FS)
    #     return self.decode(SF, PRINT)

    def dnsamp_buff(self, Data_stack, Upchirp_ind, SF):
        # load Parameters
        N = int(2 ** SF)
        num_preamble = 8
        # DC = np.conj(sym_to_data_ang([1], N))
        DC = np.conj(sym_to_data_ang([1], N, 0))

        ####################################
        ##  Compute and Correct Frequency Offsets for each Preamble Detected in each Data_stack and Find the Peak Statistics needed for demodulation

        Up_ind = []
        peak_amp = []
        Data_buff = []
        ffo = []
        FFO = []
        # n_pnt is the fft Factor - fft(Signal, n_pnt * length(Signal))
        n_pnt = 16
        peak_stats = []
        # iterate over all Upchirps that qualified 8 consecutive Peak condition
        # for k in range(Upchirp_ind.shape[0]):
        for k in range(len(Upchirp_ind)):
            if (Upchirp_ind[k] - N <= 0):
                peak_stats.append([])
                continue
            inn = []
            k_peak_stats = []
            Data_freq_off = []
            # iterate overall downsampled buffers
            for m in range(Data_stack.shape[0]):
                data_fft = []
                freq_off = []
                # ind_temp contains the Frequency Bins around bin 1 where a
                # Preamble Peak can lie
                ind_temp = np.concatenate([np.arange(5 * n_pnt), np.arange((N * n_pnt) - (4 * n_pnt) - 1, (N * n_pnt))])
                # iterate over all Preambles
                c = []
                for j in range(num_preamble):
                    data_wind = Data_stack[m,
                                int(Upchirp_ind[k]) - 1: int(Upchirp_ind[k] + (num_preamble * N) - 1)]
                    data_fft.append(abs(np.fft.fft(data_wind[((j) * N):((j + 1) * N)] * DC[:N], n_pnt * N)))

                    c.append(data_fft[j][ind_temp].argmax(0))
                    c[j] = ind_temp[c[j]] + 1
                    # Handle -ve and +ve Frequency Offsets Accordingly
                    if (c[j] > (n_pnt * N) / 2):
                        freq_off.append(((N * n_pnt) - c[j]) / n_pnt)
                    else:
                        freq_off.append(-1 * (c[j] - 1) / n_pnt)
                # average the frequency offset of 6 middle Preambles
                freq_off = np.sum(freq_off[1:7]) / (num_preamble - 2)
                ffo.append(freq_off)
                # Correct for the Frequency Offset in corresponding Data_Stack
                Data_freq_off.append(Data_stack[m, :] * np.exp(
                    (1j * 2 * math.pi * (freq_off / N)) * np.arange(1, self.length(Data_stack[m, :]) + 1)))
                # ind_temp contains the Frequency Bins around bin 1 where a
                # Preamble Peak can lie, assumption (-5*BW/2^SF <= Freq_off <= 5*BW/2^SF)
                ind_temp = np.concatenate([range(5), range(N - 4, N)])
                a = []
                c = []
                data_wind = []
                data_fft = []
                # for the frequency offset corrected Data Stack, find FFT of Preamble to get Peak Statistics
                for j in range(num_preamble):
                    data_wind = Data_freq_off[m][
                                int(Upchirp_ind[k]) - 1: int(Upchirp_ind[k] + (num_preamble * N)) - 1]
                    data_fft.append(abs(np.fft.fft(data_wind[(j) * N: (j + 1) * N] * DC[:N], N)))
                    [aj, cj] = data_fft[j][ind_temp].max(0), data_fft[j][ind_temp].argmax(0)
                    a.append(aj);
                    c.append(cj)

                    c[j] = ind_temp[c[j]]
                k_peak_stats.append([np.mean(a), np.var(a, ddof=1), np.std(a, ddof=1)])

                ##  Find the Right Data_stack to work with
                # first find the stft of given stack at the Preamble Region,
                # Spec is a 2D Matrix, rows - Freq. Bins & Col. - Time Samples
                Spec = stft_v1(Data_freq_off[m][int(Upchirp_ind[k] - N) - 1:int(Upchirp_ind[k] + 11*N - 1 - N)], N,
                               DC[:N], 0, 0)
                temp = []
                freq_track_qual = []
                pream_peak_ind = []
                adj_ind = []
                # row_ind contains the Frequency Rows around bin 1 where a
                # Preamble Peak can lie
                row_ind = np.concatenate([range(N - 6, N), range(0, 6)])
                count = 1
                for i in np.nditer(row_ind):
                    temp.append(np.sum(np.abs(Spec[i, :])))
                    count = count + 1
                temp = np.array(temp)
                # Frequency Track in row containing Preamble should have
                # maximum energy
                ind = temp.argmax(0)
                pream_peak_ind = row_ind[ind]
                # Find row indices for Preamble row + 1 & - 1
                adj_ind = np.array([np.mod(pream_peak_ind - 1 + 1, N),
                                    np.mod(pream_peak_ind + 1 + 1, N)])  # plus 1 for index conversion
                if (np.sum(adj_ind == 0) == 1):
                    adj_ind[(adj_ind == 0).nonzero()] = N
                # A good quality frequency track for a preamble is one that has
                # least energy leakage in adjacent rows (this promises very sharp FFT peaks)
                adj_ind -= 1  # subtract 1 to convert back to Python indices
                freq_track_qual = (np.sum(np.abs(Spec[pream_peak_ind, :])) - np.sum(np.abs(Spec[adj_ind[0], :]))) + (
                            np.sum(np.abs(Spec[pream_peak_ind, :])) - np.sum(np.abs(Spec[adj_ind[1], :])))
                inn.append(freq_track_qual)
            inn = np.array(inn)
            peak_stats.append(k_peak_stats)
            Data_freq_off = np.array(Data_freq_off)
            # choosing the best Data_stack based on maximum energy difference from
            # adjacent bins
            b = inn.argmax(0)
            # output frequency offset corrected buffer with relevant, Peak
            # statistics and frequency offsets
            Data_buff.append(Data_freq_off[b, :])
            FFO.append(ffo[b])
            peak_amp.append(peak_stats[k][b])
            Up_ind.append(Upchirp_ind[k])

        Data_buff = np.array(Data_buff)
        Up_ind = np.array(Up_ind)
        peak_amp = np.array(peak_amp)
        return [Data_buff, peak_amp, Up_ind, FFO]

    def length(self, arr):
        return max(arr.shape)
