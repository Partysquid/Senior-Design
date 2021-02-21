# Trainlib
# A library for controlling model train setups - written for ECE 485
# Written by Michael Kersting

import serial
import time

####################
# Serial Functions #
####################

# Get a list of all open COM ports
def getCOMPorts():
    results = list()
    
    for i in range(0, 256):
        try:
            s = serial.Serial("COM%d" % i)
            s.close()
            results.append("COM%d" % i)
        except (OSError, serial.SerialException):
            pass
    results = ['/dev/tty.usbserial-1410']
    return results


####################
# Controller Class #
####################

class Controller(object):

    # Sends a packet, taking care of any overhead
    # Packet must be of length 6
    def __sendPacket__(self, data):
        # Check the packet length
        if len(data) != 6:
            raise ValueError("Packet length must be exactly 6 bytes (got %d)" % len(data))
            
        # Add the header/footer and send the packet
        self.conn.write(b'\x00' + data + b'\xFF')
        
        # Wait for the confirmation packet, then return it (stripping the header and footer)
        self.conn.reset_input_buffer()
        response = self.conn.read(8)
        if len(response) != 8:
            raise ValueError("Response length was %d (should be 8); maybe the request timed out?" % len(response))
        if (response[0] != 0) or (response[len(response)-1] != 255) or (len(response) != 8):
            raise ValueError("Received a corrupt response from the main controller: %s" % response)
        return response[1:len(response)-1]
        
        
    # Sends a test packet - FOR DEVELOPMENT PURPOSED ONLY!!!
    def test(self):
        # Send a test packet and get the response
        return self.__sendPacket__(b'\x00\x00\x00\x00\x00\x00')
        
        
    # Sends a ping packet; returns true if a main controller responded, false otherwise
    def ping(self):
        # Send a ping packet and get the response
        response = self.__sendPacket__(b'\x01\x00\x00\x00\x00\x00')
        if (response == b'\x00\xa1\xb2\xc3\xd4\xe5'): return True
        else: return False
        
        
    # Sends a speed packet; returns true if successful, false otherwise
    # Address -> int specifying the loco's address
    # Speed -> int between 0 and 127
    # Direction -> int, 0 for reverse and 1 for forward
    def sendSpeed(self, addr, speed, direction):
        # Set up the bytes (192 is 0xC0)
        #direction = (direction==0) ? 1 : 0
        direction = not(direction)
        addr_bytes = bytes([192 | (addr >> 8)]) + bytes([addr & 255])
        speed_byte = bytes([(direction << 7) | speed])
        
        # Send the packet and read the response back
        response = self.__sendPacket__(b'\x02'+addr_bytes+speed_byte+b'\x00\x00')
        if (response[0] == 0): return True
        else: return False
        
    # Sends a function group 1 packet; returns true if successful, false otherwise
    # Address -> int specifying the loco's address
    # fl -> Headlight setting (0 for off, 1 for on)
    # f1-f4 -> Function settings (0 for off, 1 for on)
    def sendFuncG1(self, addr, fl, f1, f2, f3, f4):
        # Set up the bytes
        addr_bytes = bytes([192 | (addr >> 8)]) + bytes([addr & 255])
        func_byte = bytes([(fl<<4) | (f4<<3) | (f3<<2) | (f2<<1) | f1])
        
        # Send the packet and read the response back
        response = self.__sendPacket__(b'\x03'+addr_bytes+func_byte+b'\x00\x00')
        if (response[0] == 0): return True
        else: return False
        
    # Sends a pin write command; returns true if successful, false otherwise
    # Address -> I2C address of the target local controller
    # Pin -> The pin you want to write a value to (between 0 and 13, inclusive)
    # State -> The state you want to write to the pin (0->LOW, 1->HIGH)
    def sendPinWrite(self, lc_addr, pin, state):
        # Set up the bytes
        cmd_bytes = bytes([lc_addr, pin, state])
        
        # Send the packet and read the response back
        response = self.__sendPacket__(b'\x04'+cmd_bytes+b'\x00\x00')
        if (response[0] == 0): return True
        else: return False
        
    # Sends a pin read command; returns the state of the pin (0->LOW, 1->HIGH) or None, if an error ocurred
    # Address -> I2C address of the target local controller
    # Pin -> The pin you want to write a value to (between 0 and 13, inclusive)
    def sendPinRead(self, lc_addr, pin):
        # Set up the bytes
        cmd_bytes = bytes([lc_addr, pin])
        
        # Send the packet and read the response back
        response = self.__sendPacket__(b'\x05'+cmd_bytes+b'\x00\x00\x00')
        if (response[0] == 0): return response[1]
        else: return None
        
    # Switches a turnout; returns true if successful, false otherwise
    # Address -> I2C address of the target local controller
    # Norm Pin -> The pin that switches the turnout to the NORM position
    # Rev Pin -> The pin that switches the turnout to the REV position
    # Pos -> The position to switch the turnout to (0->NORM, 1->REV)
    def switchTurnout(self, lc_addr, norm_pin, rev_pin, pos):
        # Switch the turnout to NORM
        if (pos == 1):
            self.sendPinWrite(lc_addr, rev_pin, 0)
            self.sendPinWrite(lc_addr, norm_pin, 1)
        # Switch the turnout to REV
        else:
            self.sendPinWrite(lc_addr, norm_pin, 0)
            self.sendPinWrite(lc_addr, rev_pin, 1)
        return True
        
    # Reads a sensor; returns true if the sensor is blocked, false if it's not
    # Address -> I2C address of the target local controller
    # Pin -> The pin attached to the sensor
    def readSensor(self, lc_addr, pin):
        # Note: the true/false values might need to be swapped depending on
        # how the sensors work. I can fix that really quickly though.
        if (self.sendPinRead(lc_addr, pin) == 1): return False
        else: return True
        
    # Sets a light to red or green; returns true if successful, false otherwise
    # Address -> I2C address of the target local controller
    # Pin -> The pin the light control board is attached to
    # State -> The state of the light (0->red, 1->green)
    def setLight(self, lc_Addr, pin, state):
        # Note: I still need to standardize the pin locations on the control boards
        self.sendPinWrite(lc_Addr, pin, state)
        return True
            
    # Init Method
    def __init__(self, com_port, baudrate=9600, timeout=1):
        # Create the serial connection
        self.conn = serial.Serial(com_port)
        self.conn.baudrate = baudrate
        self.conn.timeout = timeout
        time.sleep(3)
        
        # Send a test packet
        try:
            self.ping()
        except ValueError:
            raise ValueError("Unable to connect to a controller on %s" % com_port)
