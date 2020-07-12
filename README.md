# University Centre in Svalbard - Polar Research Ionospheric Doppler Experiment

## Background

The experiment uses a simple radio system to measure waves in the upper atmosphere (ionosphere) above Svalbard. The simplest configuration uses only one transmitter and one receiver that are in different locations with an optimal distance being roughly 100km. The transmitter sends a constant carrier wave at a fixed frequency. The wave is reflected back from the ionosphere to the receiver. Plasma motions in the ionosphere cause small shifts in the frequency of the reflected wave. Comparisons of the received frequency, or frequencies, to the known transmit frequency can be used to study plasma motion and waves in the upper atmosphere.

## Technical description

The transmitter is an analog radio transmitter that sends a continuous CW at a fixed frequency in the HF band. The transmission power is roughly 20W. The antenna is a tuned half-wave dipole in an inverted-V configuration. The transmitter is located at the [Polish Polar Station Hornsund]([https://hornsund.igf.edu.pl/en/) in the southern part of Spitsbergen (77N, 15.5E).

The receiver uses a custom RF front-end and an USRP N200 with an LFRX daughterboard. A single active loop is used in testing. The plan is to eventually use two separate orthogonal dipoles to obtain two received channels for analysing O and X propagation modes. The receiver is located near Longyearbyen at the [Kjell Henriksen Observatory]([http://kho.unis.no) (N78, 16.0E).

## Software

The development of the software is work in progress... The platform is a linux computer (Ubuntu LTS 18.04.4) where mainly the python API for [USRP Hardware Driver (UHD)](https://github.com/EttusResearch/uhd) is used.
