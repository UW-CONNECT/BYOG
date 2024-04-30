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

    # ch = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # rn = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


    # Channels = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']
    Channels = ['C4', 'C5', 'C6', 'C7']
    runs = ['RUN1', 'RUN2', 'RUN3', 'RUN4', 'RUN5', 'RUN6', 'RUN7', 'RUN8', 'RUN9', 'RUN10']
    SDR = 'RTL_SDR'

    sf_map = np.zeros((len(runs), 6, len(Channels)), int)
    sf_map_global = np.zeros((6, len(Channels)), int)

    for c in range(len(Channels)):
        for r in range(len(runs)):
            print(f'\n\nProcessing {Channels[c]}, {runs[r]} \n')
            # sf_map = np.zeros((6, 10), int)
            str = r'D:/SF_BW_EST_data/Multi Channel/' + SDR + '/' + runs[r] + '/' + Channels[c]
            raw_data = np.fromfile(str, dtype=np.complex64)

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

                print(f'Number of SF {SF} pkts Decoded: {num_dec_SF}')
                sf_map[r-1, SF-7, c-1] += num_dec_SF
                sf_map_global[SF-7, c-1] += num_dec_SF

            fl = SDR + '_' + Channels[c] + '_SNR.txt'
            sourceFile = open(fl, 'a')
            for i in snr_arr:
                print(i, file=sourceFile)
            sourceFile.close()

    fl1 = SDR + 'pkt_dec.txt'
    sourceFile = open(fl1, 'a')
    for j in range(sf_map.shape[0]):
        print('\n', file=sourceFile)
        print(runs[j], file=sourceFile)
        for i in range(sf_map.shape[1]):
            print(sf_map[j, i, :], file=sourceFile)
    print('\n', file=sourceFile)
    print('ALL RUNS', file=sourceFile)
    for i in range(sf_map_global.shape[0]):
        print(sf_map_global[i, :], file=sourceFile)
    sourceFile.close()


if __name__ == '__main__':
    main()
