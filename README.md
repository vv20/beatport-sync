# Beatport Synchronisation Utility
This is a handy script that checks the list of music tracks in the pre-configured local directory, the list of tracks in the user's Beatport library and downloads all the tracks from the Beatport library that are missing locally.

## Installation

Running the following script will install the command under ./local.bin

```shell
./install.sh
```

## Usage

To synchronise your Beatport library with your local library, run the command "beatport-sync" (from any directory). On first use, you will be asked to define the local directory for storing the music library and the number of simultaneous downloads the script may perform (recommended to be the same as the number of CPU cores for optimal use)- these parameters will be stored in the local config file in your home directory. Once the command is running, enter your Beatport username and password to login- these are not stored, so you will have to enter them with every use. Once you have logged in, simply wait- the command will sync up your local library with the remote one!
