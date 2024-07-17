'''
    this the the package for the thoughts_guru web app. 
'''
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail


app = Flask(__name__)
app.config['SECRET_KEY'] = '36e792fa1feb235a2ebd2c5724eaf51b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # this is showing where the login is located
login_manager.login_message_category = 'info' #bootstrap stuff to beautify the message
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('G_EMAIL')
app.config['MAIL_PASSWORD'] = os.environ.get('G_PASSWORD')
mail = Mail(app)

from thoughts_guru import route
