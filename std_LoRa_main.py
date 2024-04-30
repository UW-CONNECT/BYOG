import numpy as np
from Demodulators.Standard_LoRa import Std_LoRa #.Standard_LoRa.Std_LoRa import Std_LoRa
from Demodulators.Standard_LoRa import *
import multiprocessing
# from Client import *
from Client.utils import *
# from Client.Active_Period_Detector import Active_Period_Detector
import time


In_Q = multiprocessing.Queue()
Out_Q = multiprocessing.Queue()

def main():

    payload_num = 50  # config.Max_Payload_Num
    check_crc = 1
    num_preamble = 8
    num_sync = 2
    preamble_sym = 1
    num_data_sym = payload_num
    num_DC = 2.25
    pkt_len = num_preamble + num_DC + num_data_sym + 2
    Fs = 500e3  # config.RX_Sampl_Rate
    BW = 125e3  # config.LORA_BW
    upsampling_factor = int(Fs // BW)

    # Load raw signal
    # raw_data = np.fromfile(r'C:\Users\Patron\Downloads\SF_BW_EST/C4', dtype=np.complex64)
    raw_data = np.fromfile(r'D:\SF_BW_EST_data\Single Channel\USRP\RUN1/all_SF1', dtype=np.complex64)
    rx_pkt_num = list()


    # APD = Active_Period_Detector(In_Q, Out_Q)
    # SF = 7
    # N = int(2 ** SF)
    # chunk = raw_data[0 : 10 * upsampling_factor * N]
    # APD.configNF(chunk, 'low')
    # uplink_wind = APD.Active_Sess_Detect2(raw_data, 'low')
    # print(len(uplink_wind))

    shift = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, 6, -6]
    num_dec = 0
    SF = 7
    N = int(2**SF)
    snr_arr = []
    # n_p = sum(np.power(abs(raw_data[0: 20 * N * upsampling_factor - 1]), 2)) / (20 * N * upsampling_factor)
    n_p = sum(np.power(abs(raw_data[2752020 + 0:2752020 +  20 * N * upsampling_factor - 1]), 2)) / (20 * N * upsampling_factor)
    for SF in [7, 8, 9, 10, 11, 12]:
        num_dec_SF = 0
        N = int(2 ** SF)

        print(f'Data Samples: {raw_data.size}; SF = {SF}; BW = {BW}Hz')


        std = Std_LoRa.Std_LoRa(num_preamble, num_sync, num_DC, num_data_sym, check_crc)
        # std.Evaluate(raw_data, SF, BW, Fs, True)
        # [pkt_starts, demod_sym, final_data] = std.Evaluate(raw_data, SF, BW, Fs, True)

        pkt_starts = std.pkt_detection2(raw_data, SF, BW, Fs, num_preamble)
        print(f'Number of SF {SF} pkts Detected: {len(pkt_starts)}')
        for k in pkt_starts:
            s_p = sum(np.power(abs(raw_data[k: k + (num_preamble * upsampling_factor * N)]), 2)) / ((num_preamble * upsampling_factor * N) + 1)
            # print(s_p)
            snr = 10 * np.log10((s_p - n_p) / n_p)
            # print(snr)
            # np.append(snr_arr, snr)

            for i in shift:
                pkt_st = np.array([], int)
                pkt_st = np.append(pkt_st, k+i)
                # print(pkt_st)
                demod_sym = std.lora_demod(raw_data, SF, BW, Fs, num_preamble, num_sync, num_DC,
                                           num_data_sym, pkt_st)
                std.demod_sym = np.mod(demod_sym, N)
                std.pkt_starts = pkt_st

                final_data = std.decode(SF, True)
                if len(final_data) != 0:
                    snr_arr.append(snr)
                    num_dec_SF += 1
                    num_dec += 1
                    break

        # print(f'Number of SF {SF} pkts Demodulated: {len(demod_sym)}')
        print(f'Number of SF {SF} pkts Decoded: {num_dec_SF}')
    print(f'Total pkts Decoded: {num_dec}')
        # print(snr_arr)
        # for k in pkt_starts:
        #     print(k)
        #     buff = raw_data[k - 2*N*upsampling_factor : k + round((52.25 *N*upsampling_factor))]
        #     buff = buff[:(len(buff) // upsampling_factor) * upsampling_factor]
        #     Rx_Buff_dnsamp = []
        #     for i in range(upsampling_factor):
        #         Rx_Buff_dnsamp.append(buff[i::upsampling_factor])
        #     Rx_Buff_dnsamp = np.array(Rx_Buff_dnsamp)
        #     [Data_freq_off, Peak, Upchirp_ind, FFO] = std.dnsamp_buff(Rx_Buff_dnsamp, [2*N*upsampling_factor], SF)





            # for i in final_data:
            #     rx_pkt_num.append(i[2][10])
    #
    # print(rx_pkt_num)
    # rx_pkt_num.sort()
    # print(rx_pkt_num)
    sourceFile = open('demo.txt', 'w')
    for i in snr_arr:
        print(i, file=sourceFile)
    # sourceFile.close()

if __name__ == '__main__':
    main()
