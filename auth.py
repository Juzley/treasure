from flask_security import Security, PeeweeUserDatastore
from flask import render_template

from model import User, Role, UserRoles
from app import app, db

# Set up flask-security
user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
security = Security(app, user_datastore)


@app.route('/register')
def register_user():
    return render_template('security/register_user.html')
