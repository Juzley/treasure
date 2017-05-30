import flask
import flask_peewee.db
import jinja2
from flask_api import FlaskAPI


app = FlaskAPI(__name__)

# TODO: Move this to config.py
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = '''
                            naAiVrNOWLrPu9qeIeZD0wgBLFjV/JsuhJsn/YC8V7U'''
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.config['SECURITY_SEND_PASSORD_RESET_NOTICE_EMAIL'] = False
app.config['DATABASE'] = {
    'name': 'treasure.db',
    'engine': 'peewee.SqliteDatabase'
}

# Load templates from the questions dir as well as the default path.
app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(['questions'])])


# Connect to the database
db = flask_peewee.db.Database(app)
