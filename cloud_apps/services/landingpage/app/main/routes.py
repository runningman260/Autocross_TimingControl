from datetime import datetime, timezone, timedelta
import os
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import News
from app.main import bp
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from io import StringIO


@bp.route('/', methods=['GET', 'POST']) #fix for form not working without explicit path specified - needs post method allowed for root path 
def landingpage():
    latest_news = db.session.scalars(sa.select(News).order_by(News.created_at.desc()).limit(1)).first()
    return render_template('landingpage.html', latest_news=latest_news, timezone=timezone, timedelta=timedelta)

@bp.route('/news', methods=['GET'])
def news():
    news_items = db.session.scalars(sa.select(News).order_by(News.created_at.desc())).all()
    return render_template('news.html', title='News', news_items=news_items, timezone=timezone, timedelta=timedelta)
