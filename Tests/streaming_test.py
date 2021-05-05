#!/usr/bin/env python3
#
"""
Testing of UHD streaming straight to disk

TODO
- there are occasionaly drops between individual record files. This may
  be due to tests running in a virtual machine. But do we need a realtime-OS
  to guarantee all samples will be capturered? Or does it matter in practice
  as long as the time for each sample is known (which it is)?
- error handling completely missing as of now :-)
"""

import argparse
import numpy as np
import uhd
import scipy.signal as ss
from datetime import datetime
import time
import logging
import threading


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument("-f", "--freq", type=float, default=4.45e6-25,
                        help="Tuning frequency in Hz (default 4.45MHz)")
    parser.add_argument("-r", "--rate", default=250e3, type=float,
                        help="Sample rate in Hz (default 250kHz)")
    parser.add_argument("-g", "--gain", type=int, default=10)
    parser.add_argument("-c", "--channel", type=int, default=0)
    parser.add_argument("-d", "--duration", type=int, default=60,
                        help="Duration for individual record files (s)")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--fs500", action="store_true",
                        help="Decimate to 500Hz sampling instead of 100Hz")
    return parser.parse_args()


def decimate_100Hz_to_file(mytime, samples, fs):
    """Reduce the sample rate before saving to file"""
    x1 = ss.decimate(samples, 50)
    x2 = ss.decimate(x1, 50)
    fs_new = (fs//50)//50
    mydt = datetime.utcfromtimestamp(mytime)
    filename = "/dev/shm/doppler"+mydt.strftime("%Y-%m-%dT%H:%M:%S")
    logging.info("Fs=" + str(fs_new) + "Hz " + filename)
    np.savez(filename, timestamp=mytime, fs=fs_new, samples=x2)


def decimate_500Hz_to_file(mytime, samples, fs):
    """Reduce the sample rate before saving to file"""
    x1 = ss.decimate(samples, 50)
    x2 = ss.decimate(x1, 10)
    fs_new = (fs//50)//10
    mydt = datetime.utcfromtimestamp(mytime)
    filename = "/dev/shm/doppler"+mydt.strftime("%Y-%m-%dT%H:%M:%S")
    logging.info("Fs=" + str(fs_new) + "Hz " + filename)
    np.savez(filename, timestamp=mytime, fs=fs_new, samples=x2)


def main():
    args = parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    usrp = uhd.usrp.MultiUSRP(args.args)

    # Use 10MHz reference and PPS signals from an external GPS
    usrp.set_clock_source("external")
    usrp.set_time_source("external")

    # Add here a routine to wait for the system to lock
    ref_status=usrp.get_mboard_sensor("ref_locked",0)
    if ref_status.value:
        logging.info("Reference clock locked")
    else:
        logging.info("** Reference clock not locked?")


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

    prev_sample_count = 0
    try:
        while True:
            # Receive the samples into the receive buffer
            # and copy to the actual sample buffer when available
            logging.info("Receiving new buffer...")
            mytime = time.time()    # Always start from UTC time!
            mydt = datetime.utcfromtimestamp(mytime)
            logging.info(mydt.strftime("%Y-%m-%d %H:%M:%S"))
            recv_samps = 0
            while recv_samps < num_samps:
                samps = streamer.recv(recv_buffer, metadata)

                sample_count = int(metadata.time_spec.get_full_secs())*int(args.rate)+int(metadata.time_spec.get_frac_secs()*args.rate)
                input_step = sample_count - prev_sample_count
                if input_step != 363:
                    print("Dropped packet %d!"%(input_step))
                prev_sample_count=sample_count

                if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                    print(metadata.strerror())
                if samps:
                    real_samps = min(num_samps - recv_samps, samps)
                    samples[:, recv_samps:recv_samps +
                            real_samps] = recv_buffer[:, 0:real_samps]
                    recv_samps += real_samps
            logging.info("...done")
            if args.fs500:
                x = threading.Thread(target=decimate_500Hz_to_file,
                                     args=(mytime, samples, args.rate))
            else:
                x = threading.Thread(target=decimate_100Hz_to_file,
                                     args=(mytime, samples, args.rate))
            x.start()

    except KeyboardInterrupt:
        pass

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    streamer.issue_stream_cmd(stream_cmd)


if __name__ == "__main__":
    main()
