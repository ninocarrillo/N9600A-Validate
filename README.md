# N9600A-Validate
Scripts for automatic validation of N9600A firmware. The purpose of this project is to reduce the human time required in validating new firmware versions for the N9600A NinoTNC. Using two slightly-modified TNCs, a Raspberry Pi, and a USB sound card, most validation tasks can performed without oversight. 

![image](images/IMG_0371.jpeg)
## Software Requirements
* Python3
* pyserial module
* local copy of repository found at https://github.com/ninocarrillo/modem-test-audio (big, 1GB+!)

## Hardware Requirements
* Two NinoTNCs... I'm using an A4r1 and an A4r2 that I had laying around
* Raspberry Pi with 40-pin header... I'm using a Pi4B
* Pi-Hat prototyping board... I used [this one from Adafruit](https://www.adafruit.com/product/2310)
* USB sound card... mine is a [Soundblaster Play! 3](https://www.amazon.com/Creative-Labs-70SB173000000-Sound-Blaster/dp/B06XBZ38ZJ/ref=sr_1_1?crid=2YAW4WUG3B18K&keywords=soundblaster+play+3&qid=1705937031&sprefix=soundblaster+play+3%2Caps%2C57&sr=8-1)
* Insulated copper wire for connections... I used solid core from old ethernet cables
* TRRS plug for the sound card, wired to a DE-9 male connector to the TNC
* Optional LEDs and resistors for flashing lights on the Pi-Hat
* Two alligator clip leads to connect TXA and RXA between the TNCs
* Some sort of mounting base and appropriate M2.5 or M3 hardware
* Soldering iron and basic tools
* Optionally, you can use a ZIF socket on the TEST TNC to make it easier to swap dsPICs. I don't recommend the one I used - the pins were too thick for the TNC PCB and it was a real pain to install it. The ZIF socket is not required for this test setup.

## TNC Switch Connections
All four MODE switch signal lines from both TNCs are connected to individual Raspberry Pi GPIO pins via the Pi-Hat. I refer to the TNCs as "TEST" device (the TNC with firmware under validation) and "STANDARD" device (the TNC with an already-validated firmware version). The MODE switch pins closest to the edge of the PCB are the signal pins. When the MODE switches are all in the off position, these pins are only connected to the respective sampling pins on the dsPIC. The Raspberry Pi can drive these signal lines with its GPIO pins, allowing scripted MODE changes on each TNC. The Raspberry Pi GPIO lines are mapped to the TNC switches as follows:
### TEST Device Dignals to Raspberry Pi GPIO:
   * MODE3 <--> GPIO 17
   * MODE2 <--> GPIO 18
   * MODE1 <--> GPIO 27
   * MODE0 <--> GPIO 22
   * TESTTX <--> GPIO 23\
     Image of under side of TEST TNC. Connections on STANDARD TNC similar, but omit TESTTX:
    ![image](images/IMG_0378.jpeg)
### STANDARD Device Signals to Raspberry Pi GPIO:
  * MODE3 <--> GPIO 24
  * MODE2 <--> GPIO 25
  * MODE1 <--> GPIO 5
  * MODE0 <--> GPIO 6  

Don't forget to make a common ground connection between the two TNCs and the Pi. Optionally, you can use some sort of connector to make the wire bundle detachable from the Pi-Hat. I used DE-9 male and female connectors for this purpose, Since there are 9 signals in this scheme, I soldered the ground wires to both of the DE-9 metal shields.

### Audio Connection to TEST TNC DE-9:
I use a USB sound card to provide an audio interface to the Raspberry Pi. Mine uses a Tip-Ring-Ring-Sleeve (TRRS) connector for audio signals in and out. I think the TRRS pinout is fairly standard for these types of devices. 
  * TIP (Left Audio Channel from DAC) <--> TNC pin 5 (RXA)
  * RING (Right Audio Channel from DAC) <--> No Connection
  * RING (Ground) <--> TNC pin 6 (Ground)
  * SLEEVE (Microphone) <--> TNC pin 1 (TXA)  

### Alligator Clip Leads
The TNC audio test loops are connected to provide a loopback on the TEST TNC and allow the STANDARD TNC to decode packets sent by the TEST TNC. I use two alligator clip leads to make these connections.
  * TEST TNC TXA <--> TEST TNC RXA
  * TEST TNC TXA <--> STANDARD TNC RXA  
  ![image](images/IMG_0374.jpeg)  
  ![image](images/IMG_0375.jpeg)

### GPIO Connections on the Pi-Hat
There are plenty of ways you can make connections to the Raspberry Pi GPIO pins, so use the method you prefer. I used the socket inserts of a machine-pin DIP socket to create removable points where I could insert test leads. I also added some LEDs and bias resistors to show which GPIO pins are active during the validation script. This is mostly for script debugging, but it's also interesting to watch.
![image](images/IMG_0373.jpeg)
![image](images/IMG_0382.jpeg)

### Path to modem-test-audio Repository
The validate.py script needs to know where to look for the audio files found in [modem-test-audio](https://github.com/ninocarrillo/modem-test-audio). By default, the script expects this repository to be "/home/pi/github/modem-test-audio/". This can be changed on line 28 of the script.

### TNC Serial Port Enumeration
The validate.py script also assumes the TEST TNC is /dev/ttyACM0 and the STANDARD TNC is /dev/ttyACM1. I place the USB cable for the TEST TNC in the top USB 2.0 port on the pi, and the STANDARD cable in the bottom port. USB 2.0 ports are black colored, USB 3.0 ports are blue. Putting the respective cables in these slots has consistently caused the TNCs to enumerate where I expect them to.
![image](images/IMG_0376.jpeg)

### TNC Control Connections
Set both potentiometers on both TNCs to about midrange. This is not critical. Also set the SIGNALS DIP switch on both TNCs to 1100.

### Running the Script
Just type:
```
python3 validate.py
```
And watch the results start to develop. Takes about an hour for the script to run right now, which might change as I add more tests. Take a look at [example_output.txt](example_output.txt) to see a test run.
