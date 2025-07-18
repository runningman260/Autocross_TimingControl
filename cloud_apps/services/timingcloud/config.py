import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.flaskenv'))


class Config:
    if( os.environ.get('DATABASE_DOCKER_URL') is not None):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_DOCKER_URL')
    else:
       SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    POSTS_PER_PAGE = 25
    