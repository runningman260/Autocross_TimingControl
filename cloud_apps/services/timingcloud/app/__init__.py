import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, lazy_gettext as _l
import rq
from config import Config
import sqlalchemy as sa
from werkzeug.middleware.proxy_fix import ProxyFix

def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


db = SQLAlchemy()

babel = Babel()



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    if not app.debug and not app.testing:

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.makedirs('logs', exist_ok=True)
            file_handler = RotatingFileHandler('logs/timingctrl.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('timingctrl startup')


    return app


from app import models
