import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.flaskenv'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if( os.environ.get('DATABASE_DOCKER_URL') is not None):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_DOCKER_URL')
    else:
       SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    POSTS_PER_PAGE = 25
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = 'username'
    MQTT_PASSWORD = 'password'
    if( os.environ.get('DOCKER_HOST_IP') is not None ):
        MQTT_BROKER_URL = os.environ.get('DOCKER_HOST_IP')
    else:
        MQTT_BROKER_URL = 'localhost'
    MQTT_CLIENTID = 'TimingControlWebUI'
    MQTT_KEEPALIVE = 5
    MQTT_TLS_ENABLED = False
    MQTT_CLEAN_SESSION = True