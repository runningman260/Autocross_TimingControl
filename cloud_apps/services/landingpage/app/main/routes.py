from datetime import datetime, timezone
import os
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.main import bp
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from io import StringIO


@bp.route('/', methods=['GET', 'POST']) #fix for form not working without explicit path specified - needs post method allowed for root path 
def landingpage():
    return render_template('landingpage.html')
