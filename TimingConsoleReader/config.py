#/bin/python3

##################################################################
#                                                                #
#  Configuration class to represent the Farmtek Timing Console.  #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

class Config:
    FARMTEK_CONSOLE_PATH = '/dev/ttyUSB98'
    FARMTEK_CONSOLE_BAUD = 9600
    # FARMTEK_CONSOLE_SYMLINK = ""
    # ^^- requires udev rule