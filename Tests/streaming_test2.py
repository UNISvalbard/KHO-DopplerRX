#!/usr/bin/env python3
#
"""
Testing of UHD streaming straight to disk

TODO
- the sample stream from the Ettus N200 is implemented as UDP packets, which does not
  quarantee that every packet will always be received. In fact, there are regularly a couple
  of missed packets. However, as we normally use a sample rate of 250kHz with a decimation down
  to 100Hz, a few lost packets should not be an issue in practice.
- error handling somewhat missing as of now :-)
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
    logging.debug("Fs=" + str(fs_new) + "Hz " + filename)
    np.savez(filename, timestamp=mytime, fs=fs_new, samples=x2.flatten())


def decimate_500Hz_to_file(mytime, samples, fs):
    """Reduce the sample rate before saving to file"""
    x1 = ss.decimate(samples, 50)
    x2 = ss.decimate(x1, 10)
    fs_new = (fs//50)//10
    mydt = datetime.utcfromtimestamp(mytime)
    filename = "/dev/shm/doppler"+mydt.strftime("%Y-%m-%dT%H:%M:%S")
    logging.debug("Fs=" + str(fs_new) + "Hz " + filename)
    np.savez(filename, timestamp=mytime, fs=fs_new, samples=x2)

def main():
    args = parse_args()

    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s',filename='/home/aurora/UNIS-DopplerRX/Tests/errorlog.txt')
    #if args.verbose:
    #    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s',filename='/home/aurora/UNIS-DopplerRX/Tests/errorlog.txt')
    #else:
    #    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s',filename='/home/aurora/UNIS-DopplerRX/Tests/errorlog.txt')

    usrp = uhd.usrp.MultiUSRP(args.args)

    # Use the internal GPSDO
    usrp.set_clock_source("gpsdo")
    usrp.set_time_source("gpsdo")

    # Add here a routine to wait for the system to lock
    ref_status=usrp.get_mboard_sensor("gps_locked",0)
    if ref_status.value:
        logging.info("GPSDO clock locked")
    else:
        logging.error("** GPDSO clock not locked?")

    # Set the USRP clock date and time from the GPSDO
    lastt=usrp.get_time_last_pps()
    nextt=usrp.get_time_last_pps()
    while nextt==lastt:
        time.sleep(0.05)
        lastt=nextt
        nextt=usrp.get_time_last_pps()
    time.sleep(0.2)
    usrp.set_time_next_pps(uhd.libpyuhd.types.time_spec(usrp.get_mboard_sensor("gps_time").to_int()+1))

    logging.info("USRP clock set to GPSDO time")
    logging.debug(str(usrp.get_mboard_sensor("gps_gpgga")))
    logging.debug(str(usrp.get_mboard_sensor("gps_gprmc")))

    # Checking the date&time across devices (for debugging)
    if args.verbose:
        t_now=time.time()
        t_usrp=(usrp.get_time_now().get_full_secs()+usrp.get_time_now().get_frac_secs())
        t_gpsdo=usrp.get_mboard_sensor("gps_time")
        logging.debug("pc clock %1.2f usrp clock %1.2f gpsdo %1.2f" % (t_now, t_usrp, t_gpsdo.to_int()))


    # Set the USRP rate, freq, and gain
    usrp.set_rx_rate(args.rate, args.channel)
    usrp.set_rx_freq(uhd.types.TuneRequest(args.freq), args.channel)
    usrp.set_rx_gain(args.gain, args.channel)

    # Create the buffer for received samples
    num_samps = int(args.duration*args.rate)
    logging.debug("One buffer records " + str(num_samps) + " samples")
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

    mytime = time.time()    # Always start from UTC time!
    mydt = datetime.utcfromtimestamp(mytime)
    logging.debug("Starting the receiver...")


    prev_sample_count = 0
    try:
        while True:
            # Receive the samples into the receive buffer
            # and copy to the actual sample buffer when available
            logging.debug("Receiving new buffer...")
            recv_samps = 0
            while recv_samps < num_samps:
                samps = streamer.recv(recv_buffer, metadata)

                sample_count = int(metadata.time_spec.get_full_secs())*int(args.rate)+int(metadata.time_spec.get_frac_secs()*args.rate)
                input_step = sample_count - prev_sample_count
                if input_step != 363:
                    logging.error("Dropped a packet!!")
                prev_sample_count=sample_count

                if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                    logging.error(metadata.strerror())
                if samps:
                    real_samps = min(num_samps - recv_samps, samps)
                    samples[:, recv_samps:recv_samps +
                            real_samps] = recv_buffer[:, 0:real_samps]
                    recv_samps += real_samps

            if args.fs500:
                mytime = time.time();
                x = threading.Thread(target=decimate_500Hz_to_file,
                                     args=(mytime, samples, args.rate))
            else:
                mytime = time.time();
                x = threading.Thread(target=decimate_100Hz_to_file,
                                     args=(mytime, samples, args.rate))
            x.start()
    except KeyboardInterrupt:
        pass

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    streamer.issue_stream_cmd(stream_cmd)
    logging.info("Stopping the reception")

if __name__ == "__main__":
    main()
