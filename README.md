# EmojiBoard
Emojiboard documentation &amp; build kit assets &amp; instructions

    LUX
    Emojiboard
    v2.0
    Luukkonen Timo
    1-22-2025


Device and Program Documentation

OVERVIEW

The hardware setup includes a Raspberry Pi (version 3 B v1.2) connected to:
    
        •	A 3x7 + 2x2 button matrix.
        •	NeoPixel LEDs (26 units).
        •	A buzzer (connected to GPIO pin 16).
        •	The program logs keypresses into a CSV file.

The program is implemented in Python and uses libraries such as RPi.GPIO, rpi_ws281x, and datetime. It starts automatically when the device boots using a cron job and saves keypresses to the file keypress_log.csv         located in the /home/emojikeyboard folder.
 

PROGRAM FUNCTIONALITY


NEOPIXEL LED CONTROL


Each button in the matrix is linked to a specific NeoPixel LED. When a button is pressed, its corresponding NeoPixel lights up green and returns to its default state once the button is released. NeoPixel 10 is programmatically set to remain off at all times and is not used in the program.


BUTTON MATRIX

The matrix is divided into two sections:

    1.	A 3x7 matrix.
    2.	A 2x2 matrix.

The buttons are assigned the following functions:

    •	BACKSPACE: Clears the keypresses in the current session.
    •	RETURN: Saves the current session data and starts a new session.
    •	Other buttons: Add the pressed key to the current session.
    •	Key to Emojis conversion table attached to this document.


KEYPRESS LOGGING

The program logs each session in the following format:

    •	A username (randomly generated combination of an adjective, animal, and unique code).
    •	Keypresses.
    •	A timestamp of when the session is saved.

The data is stored in the file keypress_log.csv.


AUTOMATIC PROGRAM STARTUP

The program is configured to run automatically on device boot using a cron job. Add the following line to the user’s crontab file by running crontab -e:

        @reboot python3 /home/emojikeyboard/keyboard-140.py

 
INSTRUCTIONS FOR COPYING KEYPRESS_LOG.CSV TO A USB STICK

    1.    Connect HDMI display and a regular keyboard to the Emojiboard.
  	2.    Connect power cable.
    3.    Insert the USB stick into the Raspberry Pi.
    4.    Identify the USB stick’s mount point using the command: 
            lsblk
          
          The stick is typically listed as /dev/sda1.
    
    5.    Mount the USB stick using the command (assuming it is /dev/sda1): 
            sudo mount /dev/sda1 /mnt

    6.    Copy the log file to the USB stick:     
        cp /home/emojikeyboard/keypress_log.csv /mnt

    7.    Safely unmount the USB stick: 
            sudo umount /mnt

    8.    Remove the USB stick from the device.

TROUBLESHOOTING

If the program does not start or the NeoPixel LEDs do not function correctly:

    1.	Verify that all hardware connections are correct.
    2.	Ensure the required libraries are installed: 
        pip3 install rpi_ws281x RPi.GPIO
    3.	Check /home/emojiboard/keyboard_debug.log
    4.	Check /var/log/syslog for error messages.

