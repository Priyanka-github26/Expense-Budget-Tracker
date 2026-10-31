
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# Application configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'expense-tracker-development-key'
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/expense_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Enable CSRF protection
csrf = CSRFProtect(app)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app import routes

if __name__ == "__main__":
    app.run(debug=True)
