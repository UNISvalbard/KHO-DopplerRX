#!/usr/bin/env python3
#
"""
Testing of UHD streaming straight to disk

TODO
- one file each second may be good for testing, but the data file
  should be e.g. one file for each minute (or for each hour). This should
  definitely be run in a separate thread...
- error handling completely missing as of now :-)
"""

import argparse
import numpy as np
import uhd
import scipy.signal as ss
from datetime import datetime
import logging
import threading


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument("-f", "--freq", type=float, default=4.45e6)
    parser.add_argument("-r", "--rate", default=250e3, type=float)
    parser.add_argument("-g", "--gain", type=int, default=10)
    parser.add_argument("-c", "--channel", type=int, default=0)
    parser.add_argument("-d", "--duration", type=int, default=1)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def decimate_to_file(mydt, samples, fs):
    """Reduce the sample rate before saving to file"""
    x1 = ss.decimate(samples, 50)
    x2 = ss.decimate(x1, 50)
    fs_new = (fs//50)//50
    filename = "/dev/shm/doppler"+mydt.strftime("%Y-%m-%dT%H:%M:%S")
    logging.info(str(x2.shape)+" "+str(fs_new) + " " + filename)
    np.savez(filename, timestamp=mydt.timestamp(), fs=fs_new, samples=x2)


def main():
    args = parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    usrp = uhd.usrp.MultiUSRP(args.args)

    # Set the USRP rate, freq, and gain
    usrp.set_rx_rate(args.rate, args.channel)
    usrp.set_rx_freq(uhd.types.TuneRequest(args.freq), args.channel)
    usrp.set_rx_gain(args.gain, args.channel)

    # Create the buffer for received samples
    num_samps = int(args.duration*args.rate)
    logging.info("One buffer records " + str(num_samps) + " samples")
    samples = np.empty((1, num_samps), dtype=np.complex64)

    # Configure RX streaming, create a receive buffer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = [args.channel]

    metadata = uhd.types.RXMetadata()
    streamer = usrp.get_rx_stream(st_args)
    buffer_samps = streamer.get_max_num_samps()
    recv_buffer = np.zeros((1, buffer_samps), dtype=np.complex64)

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)
    try:
        while True:
            # Receive the samples into the receive buffer
            # and copy to the actual sample buffer when available
            logging.info("Receiving new buffer...")
            mydt = datetime.now()
            logging.info(mydt.strftime("%Y-%m-%d %H:%M:%S"))
            recv_samps = 0
            while recv_samps < num_samps:
                samps = streamer.recv(recv_buffer, metadata)

                if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                    print(metadata.strerror())
                if samps:
                    real_samps = min(num_samps - recv_samps, samps)
                    samples[:, recv_samps:recv_samps +
                            real_samps] = recv_buffer[:, 0:real_samps]
                    recv_samps += real_samps
            print("...done")
            x = threading.Thread(target=decimate_to_file,
                                 args=(mydt, samples, args.rate))
            x.start()

    except KeyboardInterrupt:
        pass

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    streamer.issue_stream_cmd(stream_cmd)


if __name__ == "__main__":
    main()
