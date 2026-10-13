# On a PC, laptop or mini PC

Lauschkiste is not tied to the Raspberry Pi. It runs on any 64 bit PC (x64) with Linux. That makes a box out of
things you may already have:

- an **old laptop**, which brings its own screen, keyboard, speakers and battery,
- a **mini PC** (new or used), small, quiet and often cheap second-hand,
- your **work computer**, to try Lauschkiste out before you buy or build anything.

## What works

Everything that does not need Pi hardware: the web page, the library, radio, podcasts, audiobooks, time limits, Bluetooth,
and RFID readers that plug in over USB. What is missing are the parts tied to the Pi's pins and boot configuration:
readers and sound cards that you wire to the GPIO header, the pHAT BEAT, the OnOff SHIM and the like. `lauschctl setup`
asks first *What kind of machine is this?* and leaves out the questions that do not fit the answer.

Sound comes out of whatever the computer has: its speakers, a headphone jack, a USB speaker or Bluetooth.

## Install

You need a Linux with Debian or Ubuntu underneath (Debian, Ubuntu, Linux Mint and similar). Then the steps are the
ones from [Install](install.md), without the SD card:

1. Install the Linux on the computer as usual (a server or minimal install is enough, a desktop is fine too).
2. Open a terminal there, or log in with `ssh`, and paste the install line from [Install](install.md#3-install).
3. Run `lauschctl setup`. The first question is *What kind of machine is this?*. For a computer there are two answers:
   - *PC or laptop, just trying it out*: nothing is changed on the system outside Lauschkiste, no port 80, no Samba, no
     login or boot changes, no kiosk, no system upgrade. Preselected on a computer that is not a Pi. This is the one for
     your work computer.
   - *PC, laptop or mini PC as a box of its own*: for a computer that is a Lauschkiste box. The setup may then offer
     port 80, Samba, a login message, a system upgrade, the WiFi hotspot and the kiosk screen (it sets up the console
     login for it).

   The other answers on a computer:
   - *Start Lauschkiste at boot* is a *no* by default for a test; answer *yes* for a box that starts by itself.
   - Then come the questions about what is attached (a USB reader needs nothing, answer *Configure an RFID reader now*
     with *yes*).
4. Open `http://<name>.local` or `http://<ip address>:5556` from a phone or from the same computer.

On another Linux (Fedora, Arch, ...) the installer only warns: install Python 3 with headers, a C compiler, `curl`, the
PortAudio library and `alsa-utils` yourself first.

## Windows and macOS

There is no installer for them yet. To try Lauschkiste on a work computer with Windows or macOS, use a Linux in a virtual
machine; sound from a virtual machine needs a little care, so do not judge the sound quality by it.

## What has been tested

The development happens on a x64 Linux, and every change installs the packages into a fresh environment on x64 and starts
them. Running a computer like this as an everyday box for children, with an RFID reader and all, is less tested than the
Pi: tell us what you find.

Next: [Install](install.md).
