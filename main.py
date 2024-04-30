import math
import multiprocessing
from multiprocessing import Manager
from Demodulators.Standard_LoRa.Std_LoRa import Std_LoRa

import time
from threading import Thread
from queue import Queue

from matplotlib import pyplot as plt

from Active_Session import Active_Session
from Active_Period_Detector_new import Active_Period_Detector_new
from Active_Period_Detector import Active_Period_Detector2
# from State import State
from utils import *

channel_streams = []
# big_q = multiprocessing.Queue()
comp_q = multiprocessing.Queue(maxsize=1)
out_q = multiprocessing.Queue(maxsize=2)

# running average of BW usage and active period false positive rates
C_FP_rate = {}  # store False Positive rates channel-wise
AGG_FP_rate = []  # store false positive rate among all channels

def store_results(fname, info, Chan, SF, pkts, SF_act, pkt_found, sym_found, pkt_dec):
    f1 = open(fname, 'a')
    f1.write(f"{int(Chan)},\t")  # log channel, active period, time, SF, decoded data
    f1.write(f"{int(SF)},\t")
    f1.write(f"{int(SF_act)},\t")
    f1.write(f"{SF == SF_act}\t,")
    f1.write(f"{pkt_found}, ")
    f1.write(f"{sym_found}, ")
    f1.write(f"{pkt_dec}, ")
    f1.write("\t")
    f1.write(f"{int(info[2])},\t")
    f1.write(f"{int(info[3])},\t")
    f1.write(f"{int(info[4])},\t")
    f1.write(f"{int(info[5])},\t")
    f1.write(f"{int(info[6])},\t")
    f1.write(f"{int(info[7])},\t")
    f1.write(f"{int(info[8])},\t")
    # f1.write("\t")
    if len(pkts) != 0:
        f1.write(f"{pkts[0][2].tolist()}")
    else:
        if pkt_found != 0 and sym_found != 0:
            f1.write(f"Decoding Error!")
        else:
            f1.write(f"Not able to Decode packet! Check Reason!")
    f1.write(f"\n")
    f1.close()

def store_results2(fname, info, Chan, SF, pkts, SF_act, pkt_found, sym_found, pkt_dec):
    f1 = open(fname, 'a')
    f1.write(f"{int(Chan)},\t")  # log channel, active period, time, SF, decoded data
    f1.write(f"{int(SF)},\t")
    f1.write(f"{int(SF_act)},\t")
    f1.write(f"{SF == SF_act}\t,")
    f1.write(f"{pkt_found}, ")
    f1.write(f"{sym_found}, ")
    f1.write(f"{pkt_dec}, ")
    f1.write("\t")
    f1.write(f"{int(info[2])},\t")
    f1.write(f"{int(info[3])},\t")
    f1.write(f"{int(info[4])},\t")
    f1.write(f"{int(info[5])},\t")
    f1.write(f"{int(info[6])},\t")
    f1.write(f"{int(info[7])},\t")
    f1.write(f"{int(info[8])},\t")
    # f1.write("\t")
    f1.write(f"Not able to Decode packet! Packet Detection Error!")
    f1.write(f"\n")
    f1.close()


# create a method that will basically just spawn a Channel_Worker object and pass a multiprocessing queue
def spawn_a_worker(my_channel, input_queue, output_queue):
    # worker = Active_Period_Detector_new(my_channel, input_queue, output_queue)
    worker = Active_Period_Detector2(my_channel, input_queue, output_queue)
    worker.start_consuming()

def worker(in_queue):
    while True:
        # if len(in_queue) != 0:
        if in_queue.qsize() != 0:
            # process_data(in_queue.get())
            # info, chunk, t, ch = in_queue[0]
            info, chunk, t, ch = in_queue.get()
            # print(f"Indexing from {info[0]} to {info[1]}\n")
            arr = [0, 64, 96, 112, 120, 124]
            # for i in uplink_wind:
            ind = np.argmin(abs(info[2] - np.array(arr)))
            sf_est = ind + 7
            # c1 = 0
            # c2 = 0
            # # for i in range(3,9):
            # for i in range(0, 6):
            #     if info[i + 3] < 5:
            #         c1 += 1
            #     if info[2] != arr[i]:
            #         c2 += 1
            # if c2 == 6:
            #     if c1 == 6:
            #         sf_est = 7

            c1 = 0
            c2 = 0
            for i in range(0, 6):
                if info[i + 3] < 5:
                    c1 += 1
                if info[2] != arr[i]:
                    c2 += 1
            if c2 == 6 and c1 != 6:
                ind = np.argmax(info[3:])
                sf_est = ind + 7
            elif c2 != 6 and c1 == 6:
                ind = np.argmin(abs(info[2] - np.array(arr)))
                sf_est = ind + 7
            elif c2 == 6 and c1 == 6:
                ind = np.argmax(info[3:4])
                sf_est = ind + 7


                # if c1 == 6:
                #     sf_est = 7

                # print(f'{ind + 7}')
            while True:
                try:
                    [SF_act, pkts, pkt_found, sym_found, pkt_dec] = process_data(chunk, sf_est)
                    store_results(LOGGER_LOC, info, ch, sf_est, pkts, SF_act, pkt_found, sym_found, pkt_dec)
                    break
                except ValueError:
                    store_results2(LOGGER_LOC, info, ch, sf_est, pkts, SF_act, 0, 0, 0)
                    break
            # in_queue.pop(0)
            # print(f"info: {info}, time: {t}, Channel: {ch}\n")
        # else:
        #     time.sleep(0.1)

def process_data(buff, SF_est):
    # First extract file information
    # info, chunk, t, ch = file_from
    #
    num_dec = [0, 0, 0, 0, 0, 0]
    SF_act = SF_est

    logging = list()
    # (pkt.channel, pkt.pkt_num, pkt.start_time, SNR, decoded_Symbols)

    demoder = Std_LoRa(NUM_PREAMBLE, NUM_SYNC, NUM_DC, MAX_DATA_SYM, HAS_CRC)

    pkt_found = 0
    sym_found = 0
    pkt_dec = 0

    # for SF in LORA_SF:
    # print(SF)
    if SF_est == 13:
        print('****************** Hogaya ***********************')
        return [SF_act, []]
    else:
        print(f'SF = {SF_est}\n')
        [pkt_start, demod_sym, pkts] = demoder.Evaluate(buff, SF_est, LORA_BW, FS, True)
        num_dec[SF_est - 7] += len(pkts)
        if len(pkt_start) == 0:
            print('Had to try other SFs\n')
            for sf in range(7,13):
                [pkt_start, demod_sym, pkts] = demoder.Evaluate(buff, sf, LORA_BW, FS, True)
                if len(pkts) != 0:
                    SF_act = sf
                    break
        if len(pkt_start) != 0:
            pkt_found = 1
        if len(demod_sym) != 0:
            sym_found = 1
        if len(pkts) != 0:
            pkt_dec = 1
        return [SF_act, pkts, pkt_found, sym_found, pkt_dec]



big_q = multiprocessing.Queue()

if __name__ == "__main__":
    manager = Manager()

    # big_q = manager.list()


    for i in LORA_CHANNELS:
        in_queue = multiprocessing.Queue()
        channel_streams.append(in_queue)
        C_FP_rate[i] = []
        multiprocessing.Process(target=spawn_a_worker, args=(i, in_queue, big_q)).start()
    # multiprocessing.Process(target=worker, args=(big_q,)).start()

    myPool = multiprocessing.Pool(6, worker, (big_q,))
    # for i in range(25):
    #     # multiprocessing.Process(target=worker, args= (big_q,)).start()
    #     Thread(target=worker, args=[big_q]).start()

    # t1 = Thread(target=worker, args=[big_q])
    # t2 = Thread(target=worker, args=[big_q])
    # t3 = Thread(target=worker, args=[big_q])
    # t4 = Thread(target=worker, args=[big_q])
    # t5 = Thread(target=worker, args=[big_q])
    # t6 = Thread(target=worker, args=[big_q])
    # t7 = Thread(target=worker, args=[big_q])
    # t8 = Thread(target=worker, args=[big_q])
    # t1.setDaemon(True)
    # t2.setDaemon(True)
    # t3.setDaemon(True)
    # t4.setDaemon(True)
    # t5.setDaemon(True)
    # t6.setDaemon(True)
    # t7.setDaemon(True)
    # t8.setDaemon(True)
    # t1.start()
    # t2.start()
    # t3.start()
    # t4.start()
    # t5.start()
    # t6.start()
    # t7.start()
    # t8.start()

    time.sleep(2.0)
    for i in range(len(LORA_CHANNELS)):
        print(LORA_CHANNELS[i])
        multiprocessing.Process(target=IQ_SOURCE, args=(channel_streams[i], LORA_CHANNELS[i])).start()
        # Thread(target=IQ_SOURCE, args=[channel_streams[i], LORA_CHANNELS[i]]).start()
    #while True:
    #    cc = 1
    time.sleep(7260)

    # myPool.terminate()
    # myPool.join()
    # flow.close()
