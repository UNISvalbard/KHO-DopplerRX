#!/bin/bash
RXFREQ='4.6e6'
UHDPATH='/usr/lib/uhd/examples'

echo "Receiving at $RXFREQ Hz..."

$UHDPATH/rx_samples_to_file --freq $RXFREQ --rate 250e3 --duration 10 doppler_samples.sat

