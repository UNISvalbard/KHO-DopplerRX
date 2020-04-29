# University Centre in Svalbard - Polar Research Ionospheric Doppler Experiment

## Background

The project uses a simple radio system to measure waves in the upper atmopshere (ionosphere) above Svalbard. The simplest configuration uses one transmitter and one receiver that are in different locations with an optimal distance being roughly 100km. The transmitter sends a constant carrier wave at a fixed frequency. The wave is reflected back from the ionosphere to the receiver. Plasma motions in the ionosphere cause small shifts in the frequency of the reflected wave. Comparisons of the received frequency, or frequencies, to the known transmit frequency can be used to study plasma motion and waves in the upper atmosphere.

## Technical description

The transmitter is a simple analog radio transmitter that sends a continuous CW at a fixed frequency in the HF band. The antenna is a tuned half-wave dipole in an inverted-V configuration.

The receiver uses a custom RF front-end and an USRP N200 with an LFRX daughterboard. A single active loop is used in testing. The plan is to eventually use two separate orthogonal dipoles to obtain two received channels for analysing O and X propagation modes.

## Software

The development of the software is work in progress... The platform is a linux computer (Ubuntu LTS 18.04.4) with GnuRadio and UHD API.
