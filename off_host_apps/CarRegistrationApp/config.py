#/bin/python3

##################################################################
#                                                                #
#  CarRegistrationApp Configuration class                        #
#                                                                #
####################################### Pittsburgh Shootout LLC ##

class Config:
    class MQTT:
        PORT = 1883
        USERNAME = 'username'
        PASSWORD = 'password'
        BROKER = '192.168.88.200'
        CLIENTID = 'CarRegistrationApp'