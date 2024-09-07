import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.flaskenv'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    if( os.environ.get('DATABASE_DOCKER_URL') is not None):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_DOCKER_URL')
    else:
       SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
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